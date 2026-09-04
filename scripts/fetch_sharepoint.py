#!/usr/bin/env python3
"""
=====================================================================
 fetch_sharepoint.py
 ดึงข้อมูลจาก SharePoint Online ผ่าน Microsoft Graph API
 (App-Only / Client Credentials Flow)  ->  data/raw_*.json
=====================================================================
 Lists ที่ดึง
   1) DemoApp        : ข้อมูลหลัก (Main Data)
   2) Admin_KycNew   : ข้อมูลสิทธิ์ผู้ใช้งาน (Security Data)

 Secrets ที่ต้องตั้งใน GitHub  (Settings > Secrets and variables > Actions)
   TENANT_ID       : Azure AD Tenant ID
   CLIENT_ID       : App Registration (Application) ID
   CLIENT_SECRET   : Client Secret ของ App Registration
 Permission ที่ต้องมี (Application permission + Admin consent)
   Sites.Read.All  หรือ Sites.Selected (แนะนำ: Sites.Selected + grant เฉพาะ site)
=====================================================================
"""

import json
import os
import sys
import time
from pathlib import Path
from urllib.parse import quote

import requests

# ----------------------------- CONFIG --------------------------------
def env_any(*names: str) -> str:
    """
    อ่าน environment variable ตัวแรกที่มีค่า
    รองรับชื่อ Secret ได้หลายแบบ เช่น TENANT_ID หรือ AZ_TENANT_ID
    (จะได้ไม่ต้องแก้ชื่อ Secret เดิมใน GitHub)
    """
    for n in names:
        v = os.environ.get(n, "").strip()
        if v:
            return v
    return ""


TENANT_ID = env_any("TENANT_ID", "AZ_TENANT_ID", "AZURE_TENANT_ID")
CLIENT_ID = env_any("CLIENT_ID", "AZ_CLIENT_ID", "AZURE_CLIENT_ID")
CLIENT_SECRET = env_any("CLIENT_SECRET", "AZ_CLIENT_SECRET", "AZURE_CLIENT_SECRET")

SP_HOSTNAME = os.environ.get("SP_HOSTNAME", "dohomegroup.sharepoint.com")
SP_SITE_PATH = os.environ.get("SP_SITE_PATH", "/sites/AC-Accounting")
MAIN_LIST = os.environ.get("MAIN_LIST", "DemoApp")
SEC_LIST = os.environ.get("SEC_LIST", "Admin_KycNew")

GRAPH = "https://graph.microsoft.com/v1.0"
PAGE_SIZE = 999                      # ค่าสูงสุดที่ Graph รองรับต่อหน้า
MAX_RETRY = 5                        # retry เมื่อโดน throttle (429/5xx)
OUT_DIR = Path(__file__).resolve().parents[1] / "data"


# ------------------------- AUTHENTICATION ----------------------------
def get_token() -> str:
    """ขอ access token แบบ client-credentials (app-only)."""
    if not (TENANT_ID and CLIENT_ID and CLIENT_SECRET):
        missing = [n for n, v in (("TENANT_ID", TENANT_ID),
                                  ("CLIENT_ID", CLIENT_ID),
                                  ("CLIENT_SECRET", CLIENT_SECRET)) if not v]
        raise SystemExit(
            "ERROR: ไม่พบค่า " + " / ".join(missing) + "\n"
            "  รองรับชื่อ Secret ได้ทั้ง TENANT_ID / AZ_TENANT_ID / AZURE_TENANT_ID\n"
            "  (และแบบเดียวกันสำหรับ CLIENT_ID, CLIENT_SECRET)\n"
            "  ตรวจสอบว่า workflow ได้ map secrets เข้า env ของ step นี้แล้ว"
        )
    url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
    data = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scope": "https://graph.microsoft.com/.default",
    }
    print(f"  tenant={TENANT_ID[:8]}... client={CLIENT_ID[:8]}... "
          f"secret_len={len(CLIENT_SECRET)}")
    try:
        r = requests.post(url, data=data, timeout=60)
    except (requests.RequestException, OSError) as e:
        raise SystemExit(f"ERROR: เชื่อมต่อ Azure AD ไม่ได้ -> {e}")

    if r.status_code != 200:
        # แสดงสาเหตุจริงจาก Azure AD (เช่น AADSTS7000215 = secret ผิด/หมดอายุ)
        try:
            j = r.json()
            detail = f"{j.get('error')}: {j.get('error_description','')[:300]}"
        except ValueError:
            detail = r.text[:300]
        raise SystemExit(
            f"ERROR: ขอ token ไม่สำเร็จ (HTTP {r.status_code})\n  {detail}\n"
            "  ตรวจสอบ: AZ_TENANT_ID / AZ_CLIENT_ID ถูกต้องหรือไม่, "
            "client secret หมดอายุหรือยัง (ใช้ค่า 'Value' ไม่ใช่ 'Secret ID')"
        )
    print("  ได้ access token แล้ว")
    return r.json()["access_token"]


# --------------------------- HTTP HELPER -----------------------------
def graph_get(url: str, token: str) -> dict:
    """GET พร้อม retry/back-off สำหรับ throttling (429) และ error ชั่วคราว."""
    for attempt in range(1, MAX_RETRY + 1):
        resp = requests.get(
            url,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
                # ปิด metadata ที่ไม่จำเป็น -> payload เล็กลง เร็วขึ้น
                "Prefer": "HonorNonIndexedQueriesWarningMayFailRandomly",
            },
            timeout=120,
        )
        if resp.status_code in (429, 500, 502, 503, 504):
            wait = int(resp.headers.get("Retry-After", attempt * 5))
            print(f"  ! HTTP {resp.status_code} -> retry in {wait}s "
                  f"({attempt}/{MAX_RETRY})", flush=True)
            time.sleep(wait)
            continue
        if resp.status_code >= 400:
            try:
                j = resp.json().get("error", {})
                detail = f"{j.get('code')}: {str(j.get('message'))[:300]}"
            except ValueError:
                detail = resp.text[:300]
            hint = {
                403: "  -> ยังไม่ได้ Grant admin consent หรือยังไม่ได้ผูก Sites.Selected กับไซต์นี้",
                404: "  -> ตรวจสอบ SP_SITE_PATH / ชื่อ List ว่าสะกดถูกต้อง",
                401: "  -> token ไม่ถูกต้องหรือหมดอายุ",
            }.get(resp.status_code, "")
            raise SystemExit(
                f"ERROR: Graph HTTP {resp.status_code}\n  URL: {url}\n  {detail}\n{hint}")
        return resp.json()
    raise RuntimeError(f"Graph GET ล้มเหลวหลัง retry {MAX_RETRY} ครั้ง: {url}")


# --------------------------- CORE LOGIC ------------------------------
def get_site_id(token: str) -> str:
    """แปลง hostname + server-relative path เป็น Graph siteId."""
    url = f"{GRAPH}/sites/{SP_HOSTNAME}:{SP_SITE_PATH}"
    site = graph_get(url, token)
    print(f"  site: {site.get('displayName')} ({site['id']})")
    return site["id"]


def fetch_list_items(token: str, site_id: str, list_name: str) -> list:
    """
    ดึงรายการทั้งหมดของ List (รองรับ >5,000 records ด้วย server-side paging).
    คืนค่าเป็น list ของ dict (fields + id + lastModifiedDateTime)
    """
    url = (
        f"{GRAPH}/sites/{site_id}/lists/{quote(list_name)}/items"
        f"?expand=fields&$top={PAGE_SIZE}"
    )
    items, page = [], 0
    while url:
        page += 1
        payload = graph_get(url, token)
        for it in payload.get("value", []):
            row = dict(it.get("fields", {}))
            row["_ID"] = int(it.get("id", row.get("id", 0)) or 0)
            row["_Modified"] = it.get("lastModifiedDateTime")
            row["_Created"] = it.get("createdDateTime")
            items.append(row)
        url = payload.get("@odata.nextLink")
        print(f"  {list_name}: page {page} -> รวม {len(items)} รายการ", flush=True)
    return items


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print("== 1) ขอ Access Token ==", flush=True)
    token = get_token()

    print("== 2) หา Site ID ==", flush=True)
    site_id = get_site_id(token)

    print(f"== 3) ดึง Main Data: {MAIN_LIST} ==", flush=True)
    main_items = fetch_list_items(token, site_id, MAIN_LIST)

    print(f"== 4) ดึง Security Data: {SEC_LIST} ==", flush=True)
    sec_items = fetch_list_items(token, site_id, SEC_LIST)

    (OUT_DIR / "raw_main.json").write_text(
        json.dumps(main_items, ensure_ascii=False, indent=1), encoding="utf-8")
    (OUT_DIR / "raw_security.json").write_text(
        json.dumps(sec_items, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"OK: main={len(main_items)} rows, security={len(sec_items)} rows")
    return 0


if __name__ == "__main__":
    sys.exit(main())
