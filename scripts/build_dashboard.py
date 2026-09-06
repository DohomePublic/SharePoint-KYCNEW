#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
============================================================================
 build_dashboard.py
----------------------------------------------------------------------------
 ดึงข้อมูลจาก SharePoint List "DemoApp" ผ่าน Microsoft Graph API
 แล้วสร้างไฟล์ index.html (Dashboard SPA) โดยฝังข้อมูลล่าสุดลงในไฟล์

 การใช้งาน
   1) โหมดออนไลน์ (ใช้ใน GitHub Actions)
        python scripts/build_dashboard.py
      ต้องมี environment variables:
        AZURE_CLIENT_ID / AZURE_TENANT_ID / AZURE_CLIENT_SECRET
        (ไม่บังคับ) SP_HOSTNAME, SP_SITE_PATH, SP_LIST_NAME

   2) โหมดออฟไลน์ (ทดสอบ/สำรอง — อ่านจากไฟล์ CSV ที่ export ไว้)
        python scripts/build_dashboard.py --offline data/demoapp.csv

 ผลลัพธ์
   ./index.html          Dashboard พร้อมข้อมูล (GitHub Pages เสิร์ฟไฟล์นี้)
   ./data/demoapp.json   ข้อมูลดิบรูปแบบ JSON (เผื่อระบบอื่นเรียกใช้)
============================================================================
"""

import argparse
import json
import os
import re
import sys
from collections import Counter
from datetime import datetime, timezone, timedelta

# ---------------------------------------------------------------------------
# 1) ค่าคงที่ของ SharePoint  (ปรับผ่าน environment variable ได้)
# ---------------------------------------------------------------------------
# ค่า default ของ Azure AD App registration ที่ใช้จริง
# (Client ID / Tenant ID เป็น "ตัวระบุแอป" ไม่ใช่ความลับ — ส่วน Client Secret ต้องมาจาก
#  environment variable / GitHub Secrets เท่านั้น ห้ามใส่ไว้ในโค้ด)
DEFAULT_CLIENT_ID = "a37bd62d-e74d-4ea0-9546-1eb5aa96f604"
DEFAULT_TENANT_ID = "7f8918d9-718a-495b-ac9a-17cba381c4a0"
# Object ID ของ App registration (อ้างอิงเฉย ๆ ไม่ได้ใช้เรียก API): f4e84724-e3f8-444b-981b-74ead3130171

HOSTNAME  = os.getenv("SP_HOSTNAME",  "dohomegroup.sharepoint.com")
SITE_PATH = os.getenv("SP_SITE_PATH", "/sites/AC-Accounting")
LIST_NAME = os.getenv("SP_LIST_NAME", "DemoApp")
LIST_URL  = f"https://{HOSTNAME}{SITE_PATH}/Lists/{LIST_NAME}"

ROOT      = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_HTML  = os.path.join(ROOT, "index.html")
OUT_JSON  = os.path.join(ROOT, "data", "demoapp.json")

# ---------------------------------------------------------------------------
# 1.1) ค้นหาไฟล์เทมเพลต
#      รองรับหลายตำแหน่ง เพื่อให้ย้าย repo / วางไฟล์คนละที่แล้วยังทำงานได้
#      (แก้ปัญหา FileNotFoundError: templates/dashboard.html)
#      กำหนดเองได้ด้วย environment variable: TEMPLATE_PATH
# ---------------------------------------------------------------------------
TEMPLATE_CANDIDATES = [
    os.getenv("TEMPLATE_PATH", ""),                        # 0) ระบุเองผ่าน env
    os.path.join(ROOT, "scripts",   "template.html"),      # 1) โครงสร้างของแพ็กเกจนี้
    os.path.join(ROOT, "templates", "dashboard.html"),     # 2) โครงสร้างแบบ SharePoint-KYCNEW เดิม
    os.path.join(ROOT, "templates", "template.html"),
    os.path.join(ROOT, "scripts",   "dashboard.html"),
    os.path.join(ROOT, "template.html"),
    os.path.join(ROOT, "dashboard.html"),
]


def find_template() -> str:
    """คืน path ของเทมเพลตตัวแรกที่มีอยู่จริง — ถ้าไม่พบเลยให้ error ที่อ่านเข้าใจได้"""
    for p in TEMPLATE_CANDIDATES:
        if p and os.path.isfile(p):
            print(f"[template] ใช้เทมเพลต: {p}")
            return p
    tried = "\n".join("  - " + p for p in TEMPLATE_CANDIDATES if p)
    raise SystemExit(
        "[error] ไม่พบไฟล์เทมเพลต HTML\n"
        f"ค้นหาจากตำแหน่งเหล่านี้แล้ว:\n{tried}\n"
        "วิธีแก้: วางไฟล์เทมเพลตไว้ที่ scripts/template.html หรือ templates/dashboard.html\n"
        "        หรือกำหนด environment variable TEMPLATE_PATH ให้ชี้ไปยังไฟล์เทมเพลตโดยตรง"
    )

# เวลาไทย (UTC+7) สำหรับ timestamp ที่แสดงบน Dashboard
TZ_TH = timezone(timedelta(hours=7))

# ---------------------------------------------------------------------------
# 2) Data Dictionary — คำอธิบายของแต่ละคอลัมน์ (ใช้แสดงในหน้า Data Dictionary)
# ---------------------------------------------------------------------------
FIELD_DESC = {
    "_ID": "รหัสรายการภายในของ SharePoint (ใช้เปิด DispForm.aspx?ID=)",
    "Title": "ประเภทนิติบุคคล/หัวข้อรายการ เช่น บริษัท จํากัด, ห้างหุ้นส่วนจำกัด",
    "Customer_id": "รหัสลูกค้าในระบบหลัก (9 หลัก) — ใช้ตรวจคำขอซ้ำ",
    "Type1": "ประเภทลูกค้า: Existing (ลูกค้าเดิม) / Lead (ลูกค้าใหม่)",
    "type_teams": "ทีมที่ยื่นคำขอ: Store Operation, Wholesales (WS), Project Sales (PS), Retail, Steel Key Account",
    "Typr_Distribution": "เขตขายของทีมค้าส่ง/โครงการ เช่น WS-NE 2, PS-BMA 1",
    "Typr_Retail": "เขตขายของทีมค้าปลีก",
    "Customer Name": "ชื่อลูกค้าที่ใช้เรียกทั่วไป",
    "branch": "รหัสสาขาที่ยื่นคำขอ เช่น UDOO, SNOO, PKOO",
    "Request TimeStamp": "วันเวลาที่ยื่นคำขอ (UTC) — แกนเวลาหลักของทุกกราฟ",
    "Status": "สถานะปัจจุบันของคำขอในกระบวนการอนุมัติ",
    "Type_Request": "ประเภทคำขอ: เปิดวงเงินลูกค้าใหม่ / เพิ่มวงเงิน / ติดตามชุดเปิดตัวจริง",
    "limit": "วงเงินที่ขอ (บาท, เก็บเป็นข้อความมีคอมมา)",
    "CraditApprove": "วงเงินที่ได้รับอนุมัติจริง",
    "1addmonney": "จำนวนเงินที่ขอเพิ่ม (รอบที่ 1)",
    "1CreditApprove": "วงเงินที่อนุมัติในรอบที่ 1",
    "Owner": "ผู้ยื่น/เจ้าของคำขอ (ชื่อเล่น + ชื่อจริง + รหัสหน่วยงาน)",
    "Data": "วันที่จดทะเบียนจัดตั้งกิจการ",
    "registration_number": "เลขทะเบียนนิติบุคคล 13 หลัก",
    "building_road": "อาคาร/ถนน ของที่อยู่จดทะเบียน",
    "county": "ตำบล/แขวง",
    "district": "อำเภอ/เขต",
    "province": "จังหวัด",
    "post_office": "รหัสไปรษณีย์",
    "telephone": "โทรศัพท์ของกิจการ",
    "Registered_Name": "ชื่อนิติบุคคลตามหนังสือรับรอง",
    "business_type": "ประเภทธุรกิจ (เลือกได้หลายค่า คั่นด้วยคอมมา)",
    "Estimated_annual_income": "ประมาณการรายได้ต่อปี (ช่วงค่า)",
    "contact_name": "ชื่อผู้ติดต่อ",
    "position": "ตำแหน่งของผู้ติดต่อ",
    "contact_number": "เบอร์โทรผู้ติดต่อ",
    "Wholesale_retail_stores": "ข้อมูลร้านค้าส่ง/ค้าปลีกในเครือ",
    "credit_semester1": "เครดิตเทอมที่ขอ ชุดที่ 1 (วัน)",
    "Margin_type1": "อัตรากำไรขั้นต้นของชุดที่ 1",
    "value": "คำอธิบายมูลค่าของชุดที่ 1",
    "limit_other": "วงเงินอื่นที่ขอเพิ่มเติม (บาท)",
    "credit_semester2": "เครดิตเทอมที่ขอ ชุดที่ 2 (วัน)",
    "Margin_type2": "อัตรากำไรขั้นต้นของชุดที่ 2",
    "value2": "คำอธิบายมูลค่าของชุดที่ 2",
    "limit_OD": "วงเงิน O/D กับสถาบันการเงิน",
    "Bank1": "ธนาคารของวงเงิน O/D",
    "insurance_limit": "วงเงินค้ำประกัน/ประกัน",
    "Bank2": "ธนาคารของวงเงินค้ำประกัน",
    "leasing_limit": "วงเงินลีสซิ่ง",
    "Bank3": "ธนาคารของวงเงินลีสซิ่ง",
    "Other_limits": "วงเงินอื่น ๆ",
    "Bank4": "ธนาคารของวงเงินอื่น ๆ",
    "land": "หลักประกันประเภทที่ดิน (สถานะภาระผูกพัน/ขนาด)",
    "Status_1": "สถานะสำรอง (ปกติมีค่าเท่ากับ Status)",
    "other_property": "ทรัพย์สินอื่นที่ใช้เป็นหลักประกัน",
}

# ---------------------------------------------------------------------------
# 3) โหมดออนไลน์ — ดึงข้อมูลผ่าน Microsoft Graph API
# ---------------------------------------------------------------------------
def env_any(names, default=None):
    """อ่าน environment variable ตัวแรกที่มีค่า จากรายชื่อที่รองรับ

    รองรับชื่อ Secret ได้หลายแบบ เพื่อไม่ต้องแก้สคริปต์เวลาชื่อ Secret ในองค์กรต่างกัน
    เช่น AZ_CLIENT_ID (ที่ใช้จริง) หรือ AZURE_CLIENT_ID
    """
    for n in names:
        v = os.getenv(n)
        if v and v.strip():
            return v.strip(), n
    return default, None


def graph_token() -> str:
    """ขอ access token ด้วย client-credentials flow (Application permission)"""
    import requests

    # ---- รองรับชื่อ Secret ทั้งแบบ AZ_* (ที่ใช้จริง) และ AZURE_* ----
    tid, tid_src = env_any(["AZ_TENANT_ID", "AZURE_TENANT_ID"], DEFAULT_TENANT_ID)
    cid, cid_src = env_any(["AZ_CLIENT_ID", "AZURE_CLIENT_ID"], DEFAULT_CLIENT_ID)
    secret, sec_src = env_any(["AZ_CLIENT_SECRET", "AZURE_CLIENT_SECRET"])

    if not secret:
        raise SystemExit(
            "[error] ไม่พบ Client Secret ใน environment\n"
            "        รองรับชื่อ: AZ_CLIENT_SECRET หรือ AZURE_CLIENT_SECRET\n"
            "        • GitHub Actions: Settings > Secrets and variables > Actions\n"
            "          แล้ว map ใน workflow เช่น  AZ_CLIENT_SECRET: ${{ secrets.AZ_CLIENT_SECRET }}\n"
            "        • รันในเครื่อง: export AZ_CLIENT_SECRET=...\n"
            "        • หรือใช้โหมดออฟไลน์: python scripts/build_dashboard.py --offline data/demoapp.csv"
        )

    print(f"[auth] tenant={tid} (จาก {tid_src or 'ค่า default ในสคริปต์'})")
    print(f"[auth] client={cid} (จาก {cid_src or 'ค่า default ในสคริปต์'})")
    print(f"[auth] secret  = *** (จาก {sec_src}, ความยาว {len(secret)} อักขระ)")
    r = requests.post(
        f"https://login.microsoftonline.com/{tid}/oauth2/v2.0/token",
        data={
            "client_id":     cid,
            "client_secret": secret,
            "scope":         "https://graph.microsoft.com/.default",
            "grant_type":    "client_credentials",
        },
        timeout=60,
    )
    r.raise_for_status()
    return r.json()["access_token"]


def graph_get(url: str, tok: str, timeout: int = 120) -> dict:
    """เรียก Graph API พร้อมแนบ token และแปล error ให้อ่านรู้เรื่อง

    รวมการเรียก GET ไว้ที่เดียว เพื่อให้ทุก request มี error handling เหมือนกัน
    (ของเดิมเรียก .json()["id"] ตรง ๆ ถ้า API ตอบ error จะได้ KeyError ที่หาสาเหตุไม่ได้)
    """
    import requests
    r = requests.get(
        url,
        headers={"Authorization": "Bearer " + tok, "Accept": "application/json"},
        timeout=timeout,
    )
    try:
        j = r.json()
    except Exception:
        j = {}
    if r.status_code >= 400 or (isinstance(j, dict) and "error" in j):
        err = j.get("error", {}) if isinstance(j, dict) else {}
        code = err.get("code", "")
        msg = err.get("message", r.text[:400])
        hint = ""
        if r.status_code in (401, 403) or code in ("AccessDenied", "unauthenticated"):
            hint = ("\n        แนวทางแก้: Azure AD > App registrations > API permissions\n"
                    "        เพิ่ม Microsoft Graph > Application permissions > Sites.Read.All\n"
                    "        แล้วกด Grant admin consent (ต้องให้ IT Admin เป็นคนกด)")
        elif r.status_code == 404:
            hint = ("\n        แนวทางแก้: ตรวจค่า SP_HOSTNAME / SP_SITE_PATH / SP_LIST_NAME\n"
                    "        หรือรันโหมดตรวจสอบ: python scripts/build_dashboard.py --diagnose")
        raise RuntimeError(
            f"[graph] HTTP {r.status_code} {code}\n        URL: {url}\n        {msg}{hint}")
    return j


def norm_key(s) -> str:
    """ทำชื่อคอลัมน์ให้เทียบกันได้ เช่น Customer_x0020_Name / Customer Name / customername"""
    s = str(s or "")
    s = re.sub(r"_x([0-9a-fA-F]{4})_", lambda m: chr(int(m.group(1), 16)), s)  # ถอด _x0020_
    return re.sub(r"[^0-9a-z]", "", s.lower())


def resolve_site(tok: str) -> str:
    """หา site id จาก hostname + site path"""
    j = graph_get(f"https://graph.microsoft.com/v1.0/sites/{HOSTNAME}:{SITE_PATH}", tok, 60)
    print(f"[graph] site: {j.get('displayName') or j.get('name')}  id={j['id']}")
    return j["id"]


def resolve_list(tok: str, site: str) -> dict:
    """หา List ที่ต้องการ — รองรับทั้ง GUID (SP_LIST_ID), ชื่อใน URL และ Display name

    ปัญหาที่พบบ่อย: ชื่อใน URL (/Lists/DemoApp) ไม่ตรงกับ Display name จริงของ List
    ทำให้เรียก /lists/DemoApp แล้วได้ 404 → ดึงข้อมูลไม่ได้
    ฟังก์ชันนี้จึงไล่ดู List ทั้งหมดในไซต์แล้วจับคู่ชื่อแบบยืดหยุ่น
    """
    list_id = os.getenv("SP_LIST_ID", "").strip()
    if list_id:
        j = graph_get(f"https://graph.microsoft.com/v1.0/sites/{site}/lists/{list_id}", tok, 60)
        print(f"[graph] list (จาก SP_LIST_ID): {j.get('displayName')}  id={j['id']}")
        return j

    all_lists = graph_get(
        f"https://graph.microsoft.com/v1.0/sites/{site}/lists?$top=200", tok, 60).get("value", [])
    print(f"[graph] ไซต์นี้มี List ทั้งหมด {len(all_lists)} รายการ")
    want = norm_key(LIST_NAME)
    for L in all_lists:                       # 1) ชื่อตรงเป๊ะ (display name หรือ internal name)
        if norm_key(L.get("displayName")) == want or norm_key(L.get("name")) == want:
            print(f"[graph] list: {L.get('displayName')}  id={L['id']}")
            return L
    for L in all_lists:                       # 2) ชื่อมีคำที่ต้องการอยู่ข้างใน
        if want and want in norm_key(L.get("displayName", "")):
            print(f"[graph] list (จับคู่บางส่วน): {L.get('displayName')}  id={L['id']}")
            return L
    names = ", ".join(sorted(str(L.get("displayName", "?")) for L in all_lists))
    raise RuntimeError(
        f"[graph] ไม่พบ List ชื่อ '{LIST_NAME}' ในไซต์ {SITE_PATH}\n"
        f"        List ที่มีอยู่: {names}\n"
        f"        แก้โดยตั้ง SP_LIST_NAME ให้ตรง หรือระบุ SP_LIST_ID เป็น GUID ของ List")


def column_map(tok: str, site: str, lid: str) -> dict:
    """สร้างตารางแปลง internal name → display name ของทุกคอลัมน์

    เหตุผลสำคัญ: Graph คืนชื่อฟิลด์เป็น internal name (เช่น Customer_x0020_Name)
    แต่ Dashboard อ้างชื่อคอลัมน์แบบที่เห็นในหน้า SharePoint (เช่น 'Customer Name')
    ถ้าไม่แปลง ทุกฟิลด์จะกลายเป็นค่าว่าง → KPI/กราฟ/ตารางจะไม่มีข้อมูล
    (นี่คือสาเหตุหลักที่ dashboard ขึ้นแต่ข้อมูลว่างเปล่า)
    """
    cols = graph_get(
        f"https://graph.microsoft.com/v1.0/sites/{site}/lists/{lid}/columns?$top=500",
        tok, 60).get("value", [])
    m = {}
    for c in cols:
        internal, display = c.get("name"), c.get("displayName")
        if internal and display:
            m[internal] = display
    print(f"[graph] อ่าน schema คอลัมน์ได้ {len(m)} คอลัมน์")
    return m


def remap_fields(f: dict, cmap: dict) -> dict:
    """แปลงชื่อฟิลด์ของ 1 รายการเป็น display name (และเก็บชื่อ internal ไว้ด้วยเผื่อ map ไม่ครบ)"""
    out = {}
    for k, v in f.items():
        if isinstance(v, (dict, list)):       # ฟิลด์ lookup / multi-value → ทำให้เป็นข้อความ
            v = json.dumps(v, ensure_ascii=False)
        disp = cmap.get(k)
        if disp:
            out[disp] = v
        out.setdefault(k, v)                  # ไม่ทับค่าที่แปลงชื่อแล้ว
    return out


def fetch_graph() -> list:
    """ดึงทุกรายการของ List พร้อม expand fields และวนอ่านจนครบทุกหน้า (paging)"""
    tok  = graph_token()
    site = resolve_site(tok)
    L    = resolve_list(tok, site)
    lid  = L["id"]
    cmap = column_map(tok, site, lid)

    # หมายเหตุสำคัญ 2 ข้อ (ของเดิมผิดทั้งคู่ ทำให้ Graph ตอบ error / ได้ข้อมูลว่าง):
    #   1) ต้องใช้ $expand (มีเครื่องหมาย $) ไม่ใช่ expand
    #   2) เมื่อใช้ $expand=fields ค่า $top สูงสุดคือ 200 (ของเดิมใส่ 500)
    url = (f"https://graph.microsoft.com/v1.0/sites/{site}/lists/{lid}"
           f"/items?$expand=fields&$top=200")
    items, guard = [], 0
    while url and guard < 500:               # guard กัน loop ไม่รู้จบ
        j = graph_get(url, tok)
        for it in j.get("value", []):
            f = remap_fields(dict(it.get("fields", {})), cmap)
            f["_ID"] = int(it.get("id", f.get("id", 0)) or 0)
            items.append(f)
        url = j.get("@odata.nextLink")
        guard += 1
        if url:
            print(f"[graph] ...อ่านแล้ว {len(items)} รายการ กำลังดึงหน้าถัดไป")
    print(f"[graph] fetched {len(items)} items")
    if items:
        keys = [k for k in items[0] if not k.startswith("@")][:12]
        print(f"[graph] ตัวอย่างชื่อคอลัมน์ที่ได้: {keys}")
    return items


def diagnose() -> int:
    """โหมดตรวจสอบการเชื่อมต่อ — ใช้หาสาเหตุเวลาข้อมูลไม่ขึ้น

        python scripts/build_dashboard.py --diagnose
    """
    print("=" * 72)
    print(" โหมดตรวจสอบการเชื่อมต่อ SharePoint / Microsoft Graph")
    print("=" * 72)
    tok = graph_token()
    print(f"[ok] ได้ access token แล้ว (ความยาว {len(tok)} อักขระ)")
    site = resolve_site(tok)
    L    = resolve_list(tok, site)
    cmap = column_map(tok, site, L["id"])
    print("\n--- คอลัมน์ (internal → display) 30 ตัวแรก ---")
    for i, (k, v) in enumerate(cmap.items()):
        if i >= 30:
            break
        print(f"  {k:38s} → {v}")
    j = graph_get(f"https://graph.microsoft.com/v1.0/sites/{site}/lists/{L['id']}"
                  f"/items?$expand=fields&$top=1", tok)
    val = j.get("value", [])
    print(f"\n--- ตัวอย่างรายการแรก (ดึงมา {len(val)} รายการ) ---")
    if val:
        f = remap_fields(dict(val[0].get("fields", {})), cmap)
        for k, v in list(f.items())[:40]:
            print(f"  {k:38s} = {str(v)[:60]}")
    else:
        print("  (List ว่าง — ไม่มีรายการในลิสต์)")
    print("\n[ok] ตรวจสอบเสร็จสมบูรณ์ — การเชื่อมต่อใช้งานได้")
    return 0


# ---------------------------------------------------------------------------
# 4) โหมดออฟไลน์ — อ่านจาก CSV ที่ export จาก SharePoint
# ---------------------------------------------------------------------------
def fetch_csv(path: str) -> list:
    import csv
    with open(path, encoding="utf-8-sig", newline="") as fh:
        rows = [dict(r) for r in csv.DictReader(fh)]
    # แปลง "" → None และตัดช่องว่างหัว/ท้ายชื่อคอลัมน์
    out = []
    for r in rows:
        out.append({k.strip(): (v if v not in ("", None) else None) for k, v in r.items()})
    print(f"[csv] loaded {len(out)} rows from {path}")
    return out


# ---------------------------------------------------------------------------
# 5) แปลงข้อมูลดิบ → โครงสร้างที่ Dashboard ใช้
# ---------------------------------------------------------------------------
def to_number(v):
    """'20,000,000' → 20000000 ; ค่าที่แปลงไม่ได้ → 0"""
    if v is None:
        return 0
    s = re.sub(r"[^\d.\-]", "", str(v))
    try:
        return float(s) if s not in ("", "-", ".") else 0
    except ValueError:
        return 0


def norm_ts(v):
    """ทำให้ timestamp อยู่ในรูป ISO 'YYYY-MM-DDTHH:MM:SSZ'"""
    if not v:
        return ""
    s = str(v).strip()
    if "T" in s:
        return s if s.endswith("Z") else s + "Z"
    for f in ("%m/%d/%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y %H:%M:%S"):
        try:
            return datetime.strptime(s, f).strftime("%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            continue
    return s


def pick(r: dict, *names):
    """ดึงค่าจาก dict โดยเทียบชื่อคอลัมน์แบบยืดหยุ่น

    รองรับความต่างของชื่อคอลัมน์ระหว่าง CSV export กับ Microsoft Graph เช่น
    'Customer Name' / 'Customer_x0020_Name' / 'customer_name' → ถือว่าเป็นคอลัมน์เดียวกัน
    """
    idx = r.get("__norm__")
    if idx is None:
        idx = {norm_key(k): v for k, v in r.items()}
        r["__norm__"] = idx
    for n in names:
        v = r.get(n)                       # 1) ชื่อตรงเป๊ะก่อน
        if v not in (None, ""):
            return v
        v = idx.get(norm_key(n))           # 2) เทียบแบบ normalize
        if v not in (None, ""):
            return v
    return None


def build_payload(raw: list) -> dict:
    """สร้าง dict ที่จะถูกฝังลงใน index.html เป็น window.DEMOAPP_DATA"""
    rows, columns = [], []
    for r in raw:
        for k in r:
            if k not in columns:
                columns.append(k)

    for r in raw:
        clean = {k.strip(): v for k, v in r.items()
                 if v not in (None, "") and not k.startswith("_Has")
                 and k not in ("__norm__",)}
        # ใช้ pick() แทน r.get() เพื่อให้รองรับชื่อคอลัมน์ทั้งจาก CSV และจาก Graph API
        row = {
            "id":           r.get("_ID"),
            "title":        pick(r, "Title"),
            "customerId":   pick(r, "Customer_id", "CustomerId", "Customer ID"),
            "customerName": (pick(r, "Customer Name", "Customer_Name", "CustomerName",
                                  "Registered_Name", "Registered Name")
                             or f"รายการ {r.get('_ID')}"),
            "type1":        pick(r, "Type1", "Type 1"),
            "team":         pick(r, "type_teams", "Type_Teams", "type teams"),
            "distribution": pick(r, "Typr_Distribution", "Type_Distribution",
                                 "Typr_Retail", "Type_Retail"),
            "branch":       pick(r, "branch", "Branch"),
            "ts":           norm_ts(pick(r, "Request TimeStamp", "Request_TimeStamp",
                                         "RequestTimeStamp", "Created")),
            "status":       pick(r, "Status", "Status_1", "Status1"),
            "typeRequest":  pick(r, "Type_Request", "Type Request", "TypeRequest"),
            "limitNum":     to_number(pick(r, "limit", "Limit")),
            "limitOther":   to_number(pick(r, "limit_other", "Limit_Other")),
            "owner":        pick(r, "Owner"),
            "province":     pick(r, "province", "Province"),
            "district":     pick(r, "district", "District"),
            "businessType": pick(r, "business_type", "Business_Type"),
            "income":       pick(r, "Estimated_annual_income", "Estimated Annual Income"),
            "credit1":      pick(r, "credit_semester1", "Credit_Semester1"),
            "credit2":      pick(r, "credit_semester2", "Credit_Semester2"),
            "land":         pick(r, "land", "Land"),
            "contact":      pick(r, "contact_name", "Contact_Name", "Contact Name"),
            "_raw":         clean,   # ใช้ในหน้า Drill Down
        }
        # ฟิลด์รวมข้อความทุกคอลัมน์ (lowercase) สำหรับ global search
        row["_search"] = " ".join(str(v) for v in clean.values()).lower()
        rows.append(row)

    # ---- สถิติคุณภาพข้อมูล ----
    n = max(len(raw), 1)
    null_pct, dictionary = [], []
    for c in columns:
        if c.startswith("_Has"):
            continue
        vals = [r.get(c) for r in raw]
        nonnull = [v for v in vals if v not in (None, "")]
        pct = round((n - len(nonnull)) / n * 100, 1)
        null_pct.append([c, pct])
        sample = str(nonnull[0])[:40] if nonnull else ""
        dictionary.append({
            "name":    c,
            "type":    guess_type(nonnull),
            "desc":    FIELD_DESC.get(c.strip(), "—"),
            "sample":  sample,
            "unique":  len(set(map(str, nonnull))),
            "nullPct": pct,
        })
    null_pct.sort(key=lambda x: -x[1])

    return {
        "generatedAt":  datetime.now(TZ_TH).strftime("%Y-%m-%d %H:%M น. (เวลาไทย)"),
        "listUrl":      LIST_URL,
        "rowCount":     len(rows),
        "columns":      columns,
        "rows":         rows,
        "dictionary":   dictionary,
        "nullPercent":  null_pct,
        "emptyColumns": [c for c, p in null_pct if p >= 100],
    }


def guess_type(vals) -> str:
    """เดาชนิดข้อมูลจากค่าที่มีอยู่จริง"""
    if not vals:
        return "ว่างทั้งหมด"
    s = [str(v) for v in vals[:50]]
    if all(re.fullmatch(r"\d{4}-\d{2}-\d{2}T.*", x) for x in s):
        return "DateTime"
    if all(re.fullmatch(r"[\d,\.]+", x) for x in s):
        return "Number"
    return "Text"


# ---------------------------------------------------------------------------
# 6) เขียนไฟล์ index.html โดยแทนที่ placeholder ใน template
# ---------------------------------------------------------------------------
def render(payload: dict) -> None:
    template = find_template()
    with open(template, encoding="utf-8") as fh:
        html = fh.read()

    # ตรวจว่าเทมเพลตมี placeholder ครบก่อนแทนที่ (กัน ValueError จาก .index())
    if "/*__DATA__*/" not in html or "/*__ENDDATA__*/" not in html:
        raise SystemExit(
            f"[error] เทมเพลต {template} ไม่มี placeholder /*__DATA__*/ ... /*__ENDDATA__*/\n"
            "        กรุณาใช้ไฟล์ scripts/template.html ที่มาพร้อมแพ็กเกจนี้"
        )

    data_js = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    # กัน </script> ในข้อมูลทำให้ HTML พัง
    data_js = data_js.replace("</", "<\\/")

    start, end = "/*__DATA__*/", "/*__ENDDATA__*/"
    i, j = html.index(start), html.index(end)
    html = html[: i + len(start)] + data_js + html[j:]

    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_HTML, "w", encoding="utf-8") as fh:
        fh.write(html)
    with open(OUT_JSON, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=1)

    print(f"[build] wrote {OUT_HTML}  ({len(html):,} bytes, {payload['rowCount']} rows)")
    print(f"[build] wrote {OUT_JSON}")


# ---------------------------------------------------------------------------
# 7) main
# ---------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser(description="Build DemoApp dashboard")
    ap.add_argument("--offline", metavar="CSV",
                    help="สร้าง dashboard จากไฟล์ CSV แทนการเรียก Graph API")
    ap.add_argument("--fallback", metavar="CSV",
                    help="ถ้าดึงจาก Graph ไม่สำเร็จ ให้ใช้ CSV นี้แทน (dashboard จะไม่ว่าง)")
    ap.add_argument("--diagnose", action="store_true",
                    help="ตรวจสอบการเชื่อมต่อ/สิทธิ์/ชื่อคอลัมน์ โดยไม่สร้างไฟล์")
    a = ap.parse_args()

    if a.diagnose:                                   # โหมดตรวจสอบอย่างเดียว
        return diagnose()

    # ---- ดึงข้อมูล ----
    if a.offline:
        raw = fetch_csv(a.offline)
    else:
        try:
            raw = fetch_graph()
        except Exception as e:
            print(f"[error] ดึงข้อมูลจาก SharePoint ไม่สำเร็จ:\n{e}", file=sys.stderr)
            if a.fallback and os.path.exists(a.fallback):
                print(f"[fallback] ใช้ข้อมูลสำรองจาก {a.fallback} แทน", file=sys.stderr)
                raw = fetch_csv(a.fallback)
            else:
                return 1

    if not raw:
        print("[error] ไม่พบข้อมูล — ยกเลิกการสร้างไฟล์ (ไม่เขียนทับ index.html เดิม)",
              file=sys.stderr)
        return 1

    payload = build_payload(raw)

    # ---- ตรวจคุณภาพก่อนเขียนไฟล์ (กันกรณี "ดึงมาได้แต่ทุกช่องว่าง") ----
    rows = payload["rows"]
    filled_status = sum(1 for r in rows if r.get("status"))
    filled_limit  = sum(1 for r in rows if r.get("limitNum"))
    filled_ts     = sum(1 for r in rows if r.get("ts"))
    print(f"[check] มีค่า Status {filled_status}/{len(rows)} | "
          f"วงเงิน {filled_limit}/{len(rows)} | วันที่ {filled_ts}/{len(rows)}")
    if filled_status == 0 and filled_limit == 0:
        print("[error] ดึงรายการมาได้ แต่ฟิลด์สำคัญว่างทั้งหมด — "
              "แปลว่าชื่อคอลัมน์ไม่ตรง (internal name vs display name)\n"
              "        รันคำสั่งนี้เพื่อดูชื่อคอลัมน์จริง: "
              "python scripts/build_dashboard.py --diagnose", file=sys.stderr)
        if not os.getenv("ALLOW_EMPTY"):
            return 1

    render(payload)

    # สรุปสั้น ๆ ลง log ของ GitHub Actions
    print("[summary] status:", dict(Counter(r["status"] for r in payload["rows"])))
    print("[summary] total limit:", f'{sum(r["limitNum"] for r in payload["rows"]):,.0f}')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
