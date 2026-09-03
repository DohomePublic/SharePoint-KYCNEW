#!/usr/bin/env python3
"""
build_dashboard.py — สร้าง KYC Daily Dashboard (HTML ไฟล์เดียว) จาก SharePoint List
แก้ปัญหา: [ERROR] list 'KYCData1' not found  -> resolve ชื่อ list อัตโนมัติ + fail-fast

การใช้งาน
  python scripts/build_dashboard.py
  python scripts/build_dashboard.py --offline data.json     # build จาก snapshot ไม่ต้องต่อ SharePoint

Environment (GitHub Actions secrets)
  TENANT_ID, CLIENT_ID, CLIENT_SECRET     : Azure AD app (Sites.Read.All)
  SP_HOST        default dohomegroup.sharepoint.com
  SP_SITE_PATH   default /sites/AC-Accounting
  SP_LIST_DATA   default KYC_DATA_NEW      (ทับ candidate ตัวแรก)
  SP_LIST_GROUP  default Admin_KycNew
  OUT_FILE       default dist/KYC_Daily_Dashboard.html
"""
import argparse
import difflib
import json
import os
import re
import sys
from pathlib import Path

HOST = os.getenv("SP_HOST", "dohomegroup.sharepoint.com")
SITE_PATH = os.getenv("SP_SITE_PATH", "/sites/AC-Accounting")
OUT_FILE = Path(os.getenv("OUT_FILE", "dist/KYC_Daily_Dashboard.html"))
TEMPLATE = Path(os.getenv("TEMPLATE_FILE", "templates/dashboard_template.html"))

DATA_LIST_CANDIDATES = [os.getenv("SP_LIST_DATA", "").strip(), "KYC_DATA_NEW", "KYCData1", "DemoApp"]
GROUP_LIST_CANDIDATES = [os.getenv("SP_LIST_GROUP", "").strip(), "Admin_KycNew"]

GRAPH = "https://graph.microsoft.com/v1.0"


def log(lvl, msg):
    print(f"[{lvl}] {msg}", flush=True)


# ---------------------------------------------------------------- list resolver
def _norm(s):
    return re.sub(r"[\s_\-.]+", "", (s or "")).lower()


def resolve_list(available, candidates, kind="data"):
    """หา list จริงบนไซต์จาก candidates (ทน _ - . และตัวพิมพ์เล็ก/ใหญ่)"""
    by_norm = {_norm(n): n for n in available}
    # ไล่ทีละ candidate ตามลำดับความสำคัญ: exact -> normalized -> ใกล้เคียง
    for cand in [c for c in candidates if c]:
        if cand in available:
            log("INFO", f"{kind} list = '{cand}'")
            return cand
        hit = by_norm.get(_norm(cand))
        if hit:
            log("WARN", f"list '{cand}' ไม่ตรงตัวอักษร — ใช้ '{hit}' แทน")
            return hit
        core = re.sub(r"\d+$", "", _norm(cand))
        near = [n for k, n in by_norm.items() if len(core) >= 4 and (k.startswith(core) or core in k)]
        if near:
            log("WARN", f"ไม่พบ '{cand}' — ใช้ list ใกล้เคียง '{near[0]}'")
            return near[0]
    first = next((c for c in candidates if c), kind)
    sugg = difflib.get_close_matches(first, available, n=5, cutoff=0.4)
    log("ERROR", f"ไม่พบ {kind} list จาก {[c for c in candidates if c]}")
    log("ERROR", f"ใกล้เคียงที่สุด: {sugg or '(ไม่มี)'}")
    log("ERROR", "ตั้งค่า env SP_LIST_DATA / SP_LIST_GROUP ให้ตรงชื่อจริง")
    sys.exit(1)  # fail-fast — ไม่ทำงานต่อเหมือนเวอร์ชันเดิม


# ---------------------------------------------------------------- graph client
def get_token():
    import requests

    t, c, s = os.getenv("TENANT_ID"), os.getenv("CLIENT_ID"), os.getenv("CLIENT_SECRET")
    if not all([t, c, s]):
        log("ERROR", "ไม่พบ TENANT_ID / CLIENT_ID / CLIENT_SECRET — ใช้ --offline หากต้องการ build จาก snapshot")
        sys.exit(1)
    r = requests.post(
        f"https://login.microsoftonline.com/{t}/oauth2/v2.0/token",
        data={"client_id": c, "client_secret": s,
              "scope": "https://graph.microsoft.com/.default", "grant_type": "client_credentials"},
        timeout=60)
    r.raise_for_status()
    return r.json()["access_token"]


def gget(url, tok):
    import requests
    r = requests.get(url, headers={"Authorization": f"Bearer {tok}"}, timeout=120)
    r.raise_for_status()
    return r.json()


def gall(url, tok):
    out = []
    while url:
        j = gget(url, tok)
        out += j.get("value", [])
        url = j.get("@odata.nextLink")
    return out


def fetch():
    tok = get_token()
    site = gget(f"{GRAPH}/sites/{HOST}:{SITE_PATH}", tok)
    log("INFO", f"site: {site['name']} ({site['id']})")
    lists = gall(f"{GRAPH}/sites/{site['id']}/lists?$select=id,displayName&$top=200", tok)
    names = [l["displayName"] for l in lists]
    log("INFO", f"lists found: {len(names)}")
    dl = resolve_list(names, DATA_LIST_CANDIDATES, "data")
    gl = resolve_list(names, GROUP_LIST_CANDIDATES, "group")
    ids = {l["displayName"]: l["id"] for l in lists}

    def items(name):
        rows = gall(f"{GRAPH}/sites/{site['id']}/lists/{ids[name]}/items?expand=fields&$top=2000", tok)
        out = []
        for r in rows:
            f = dict(r.get("fields", {}))
            f["_ID"] = r.get("id")
            out.append(f)
        return out

    records = items(dl)
    allowed = [r.get("Title") for r in items(gl) if r.get("Title")]
    log("INFO", f"records={len(records)} allowed_viewers={len(allowed)}")
    return {"records": records, "allowed": allowed, "source": dl}


# ---------------------------------------------------------------- build
def build(payload):
    if not TEMPLATE.exists():
        log("ERROR", f"ไม่พบ template: {TEMPLATE}")
        sys.exit(1)
    html = TEMPLATE.read_text(encoding="utf-8")
    if "__DATA__" not in html or "__ALLOWED__" not in html:
        log("ERROR", "template ต้องมี placeholder __DATA__ และ __ALLOWED__")
        sys.exit(1)
    html = html.replace("__ALLOWED__", json.dumps(payload["allowed"], ensure_ascii=False))
    html = html.replace("__DATA__", json.dumps(payload["records"], ensure_ascii=False, default=str))
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(html, encoding="utf-8")
    log("OK", f"wrote {OUT_FILE} ({OUT_FILE.stat().st_size:,} bytes) "
               f"records={len(payload['records'])} viewers={len(payload['allowed'])}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline", metavar="JSON", help="build จากไฟล์ snapshot {records,allowed}")
    a = ap.parse_args()
    log("INFO", f"building dashboard @ {HOST}{SITE_PATH}")
    payload = json.loads(Path(a.offline).read_text(encoding="utf-8")) if a.offline else fetch()
    payload.setdefault("allowed", [])
    build(payload)


if __name__ == "__main__":
    main()
