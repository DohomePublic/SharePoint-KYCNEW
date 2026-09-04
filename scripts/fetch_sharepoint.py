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
TENANT_ID = os.environ.get("TENANT_ID", "")
CLIENT_ID = os.environ.get("CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET", "")

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
        raise SystemExit(
            "ERROR: ไม่พบ TENANT_ID / CLIENT_ID / CLIENT_SECRET "
            "(ตั้งค่าใน GitHub Secrets ก่อนรัน)"
        )
    url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
    data = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scope": "https://graph.microsoft.com/.default",
    }
    r = requests.post(url, data=data, timeout=60)
    r.raise_for_status()
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
        resp.raise_for_status()
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
