#!/usr/bin/env python3
"""
build_dashboard.py
------------------
ดึงข้อมูลจาก SharePoint List "KYCData1" ผ่าน Microsoft Graph API (client credentials)
แล้ว render เป็น index.html (Dashboard แบบ static ไฟล์เดียว) สำหรับ GitHub Pages

ENV ที่ต้องมี (ตั้งใน GitHub Secrets):
  AZURE_CLIENT_ID
  AZURE_TENANT_ID
  AZURE_CLIENT_SECRET
ENV เสริม (มีค่า default):
  SP_HOSTNAME   default: dohomegroup.sharepoint.com
  SP_SITE_PATH  default: /sites/AC-Accounting
  SP_LIST_NAME  default: KYCData1
  OUTPUT_FILE   default: index.html
  TEMPLATE_FILE default: templates/dashboard_template.html
  TZ_OFFSET_HRS default: 7   (Asia/Bangkok — ใช้แสดง As of และคำนวณ "วันนี้")
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import requests

ROOT = Path(__file__).resolve().parents[1]

HOSTNAME = os.getenv("SP_HOSTNAME", "dohomegroup.sharepoint.com")
SITE_PATH = os.getenv("SP_SITE_PATH", "/sites/AC-Accounting")
LIST_NAME = os.getenv("SP_LIST_NAME", "KYCData1")
OUTPUT_FILE = ROOT / os.getenv("OUTPUT_FILE", "index.html")
TEMPLATE_FILE = ROOT / os.getenv("TEMPLATE_FILE", "templates/dashboard_template.html")
TZ_OFFSET = timedelta(hours=float(os.getenv("TZ_OFFSET_HRS", "7")))

GRAPH = "https://graph.microsoft.com/v1.0"
TIMEOUT = 60

# ---------------------------------------------------------------- field mapping
# ชื่อฟิลด์ที่เป็นไปได้ในลิสต์ (internal name) → คีย์ที่ dashboard ใช้
FIELD_MAP: Dict[str, List[str]] = {
    "customer": ["Customer_x0020_Name", "CustomerName", "Customer_Name", "Customer", "Title"],
    "branch":   ["branch", "Branch", "BranchCode", "Branch_x0020_Code"],
    "owner":    ["Owner", "owner", "AssignedTo", "Responsible"],
    "status":   ["Status", "status", "Status_x0020_1", "Status_1"],
    "type":     ["Type_Request", "TypeRequest", "Type_x0020_Request", "RequestType"],
    "team":     ["type_teams", "TypeTeams", "Team", "type_team"],
    "limit":    ["limit", "Limit", "CreditLimit", "limit_amount"],
    "seg":      ["Type1", "Segment", "CustomerType"],
    "province": ["province", "Province"],
    "ts":       ["Request_x0020_TimeStamp", "RequestTimeStamp", "Request_TimeStamp",
                 "RequestDate", "Created"],
}


def env(name: str) -> str:
    v = os.getenv(name, "").strip()
    if not v:
        sys.exit(f"[ERROR] missing required environment variable: {name}")
    return v


def get_token() -> str:
    tenant = env("AZURE_TENANT_ID")
    resp = requests.post(
        f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token",
        data={
            "client_id": env("AZURE_CLIENT_ID"),
            "client_secret": env("AZURE_CLIENT_SECRET"),
            "scope": "https://graph.microsoft.com/.default",
            "grant_type": "client_credentials",
        },
        timeout=TIMEOUT,
    )
    if resp.status_code != 200:
        sys.exit(f"[ERROR] token request failed ({resp.status_code}): {resp.text[:400]}")
    return resp.json()["access_token"]


def api_get(url: str, token: str, params: Optional[dict] = None) -> dict:
    r = requests.get(
        url,
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
        params=params,
        timeout=TIMEOUT,
    )
    if r.status_code != 200:
        sys.exit(f"[ERROR] GET {url} failed ({r.status_code}): {r.text[:400]}")
    return r.json()


def fetch_items(token: str) -> List[dict]:
    site = api_get(f"{GRAPH}/sites/{HOSTNAME}:{SITE_PATH}", token)
    site_id = site["id"]
    print(f"[INFO] site: {site.get('displayName')} ({site_id})")

    lists = api_get(f"{GRAPH}/sites/{site_id}/lists", token, {"$top": "200"})["value"]
    match = next(
        (l for l in lists if l.get("name") == LIST_NAME or l.get("displayName") == LIST_NAME),
        None,
    )
    if not match:
        names = ", ".join(sorted({l.get("displayName", "") for l in lists}))
        sys.exit(f"[ERROR] list '{LIST_NAME}' not found. Available: {names}")
    list_id = match["id"]
    print(f"[INFO] list: {match.get('displayName')} ({list_id})")

    items: List[dict] = []
    url = f"{GRAPH}/sites/{site_id}/lists/{list_id}/items"
    params = {"$expand": "fields", "$top": "200"}
    while url:
        page = api_get(url, token, params)
        items.extend(page.get("value", []))
        url = page.get("@odata.nextLink")
        params = None  # nextLink already carries query params
        print(f"[INFO] fetched {len(items)} items...")
    return items


# ---------------------------------------------------------------- normalisation
def pick(fields: dict, keys: Iterable[str]) -> Any:
    for k in keys:
        v = fields.get(k)
        if v not in (None, ""):
            return v
    return None


def to_number(v: Any) -> float:
    if v is None:
        return 0.0
    if isinstance(v, (int, float)):
        return float(v)
    s = re.sub(r"[^\d.\-]", "", str(v))
    try:
        return float(s) if s not in ("", "-", ".") else 0.0
    except ValueError:
        return 0.0


def to_ts(v: Any) -> str:
    """คืนค่า 'YYYY-MM-DD HH:MM' (UTC) ให้ frontend"""
    if not v:
        return ""
    s = str(v)
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%S",
                "%m/%d/%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt).strftime("%Y-%m-%d %H:%M")
        except ValueError:
            continue
    return s[:16].replace("T", " ")


def normalise(items: List[dict]) -> List[dict]:
    rows: List[dict] = []
    for it in items:
        f = it.get("fields", {}) or {}
        ts = to_ts(pick(f, FIELD_MAP["ts"]) or it.get("createdDateTime"))
        if not ts:
            continue
        rows.append(
            {
                "id": int(f.get("id") or it.get("id") or 0),
                "customer": str(pick(f, FIELD_MAP["customer"]) or ""),
                "branch": str(pick(f, FIELD_MAP["branch"]) or "(ไม่ระบุสาขา)"),
                "owner": str(pick(f, FIELD_MAP["owner"]) or "(ไม่ระบุผู้ดูแล)"),
                "status": str(pick(f, FIELD_MAP["status"]) or "(ไม่ระบุสถานะ)"),
                "type": str(pick(f, FIELD_MAP["type"]) or ""),
                "team": str(pick(f, FIELD_MAP["team"]) or ""),
                "limit": to_number(pick(f, FIELD_MAP["limit"])),
                "seg": str(pick(f, FIELD_MAP["seg"]) or ""),
                "province": str(pick(f, FIELD_MAP["province"]) or ""),
                "ts": ts,
            }
        )
    rows.sort(key=lambda r: r["ts"], reverse=True)
    return rows


# ---------------------------------------------------------------- render
def render(rows: List[dict]) -> str:
    if not TEMPLATE_FILE.exists():
        sys.exit(f"[ERROR] template not found: {TEMPLATE_FILE}")
    html = TEMPLATE_FILE.read_text(encoding="utf-8")

    now_local = datetime.now(timezone.utc) + TZ_OFFSET
    site_url = f"https://{HOSTNAME}{SITE_PATH}/Lists/{LIST_NAME}"

    payload = json.dumps(rows, ensure_ascii=False)
    if "/*__DATA__*/[]" not in html:
        sys.exit("[ERROR] template missing the /*__DATA__*/[] binding placeholder")
    html = html.replace("/*__DATA__*/[]", payload)
    html = html.replace("__GENERATED_AT__", now_local.strftime("%Y-%m-%d %H:%M") + " (UTC+7)")
    html = html.replace("__LIST_URL__", site_url)
    html = html.replace("__LIST_NAME__", LIST_NAME)
    return html


def main() -> None:
    print(f"[INFO] building dashboard for list '{LIST_NAME}' @ {HOSTNAME}{SITE_PATH}")
    token = get_token()
    items = fetch_items(token)
    rows = normalise(items)
    if not rows:
        sys.exit("[ERROR] no rows returned — refusing to overwrite index.html with empty data")
    OUTPUT_FILE.write_text(render(rows), encoding="utf-8")
    print(f"[OK] wrote {OUTPUT_FILE} ({len(rows)} records, {OUTPUT_FILE.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
