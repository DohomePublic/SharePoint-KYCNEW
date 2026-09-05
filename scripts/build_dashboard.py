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


def fetch_graph() -> list:
    """ดึงทุกรายการของ List พร้อม expand fields และวนอ่านจนครบทุกหน้า (paging)"""
    import requests
    tok = graph_token()
    h = {"Authorization": f"Bearer {tok}", "Accept": "application/json"}

    site = requests.get(
        f"https://graph.microsoft.com/v1.0/sites/{HOSTNAME}:{SITE_PATH}",
        headers=h, timeout=60).json()["id"]

    url = (f"https://graph.microsoft.com/v1.0/sites/{site}/lists/{LIST_NAME}"
           f"/items?expand=fields&$top=500")
    items, guard = [], 0
    while url and guard < 200:               # guard กัน loop ไม่รู้จบ
        j = requests.get(url, headers=h, timeout=120).json()
        if "error" in j:
            raise RuntimeError(j["error"])
        for it in j.get("value", []):
            f = dict(it.get("fields", {}))
            f["_ID"] = int(it.get("id", f.get("id", 0)))
            items.append(f)
        url = j.get("@odata.nextLink")
        guard += 1
    print(f"[graph] fetched {len(items)} items")
    return items


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


def build_payload(raw: list) -> dict:
    """สร้าง dict ที่จะถูกฝังลงใน index.html เป็น window.DEMOAPP_DATA"""
    rows, columns = [], []
    for r in raw:
        for k in r:
            if k not in columns:
                columns.append(k)

    for r in raw:
        clean = {k.strip(): v for k, v in r.items()
                 if v not in (None, "") and not k.startswith("_Has")}
        row = {
            "id":           r.get("_ID"),
            "title":        r.get("Title"),
            "customerId":   r.get("Customer_id"),
            "customerName": r.get("Customer Name") or r.get("Registered_Name") or f"รายการ {r.get('_ID')}",
            "type1":        r.get("Type1"),
            "team":         r.get("type_teams"),
            "distribution": r.get("Typr_Distribution") or r.get("Typr_Retail"),
            "branch":       r.get("branch"),
            "ts":           norm_ts(r.get("Request TimeStamp")),
            "status":       r.get("Status") or r.get("Status_1"),
            "typeRequest":  r.get("Type_Request"),
            "limitNum":     to_number(r.get("limit")),
            "limitOther":   to_number(r.get("limit_other")),
            "owner":        r.get("Owner"),
            "province":     r.get("province"),
            "district":     r.get("district"),
            "businessType": r.get("business_type"),
            "income":       r.get("Estimated_annual_income"),
            "credit1":      r.get("credit_semester1"),
            "credit2":      r.get("credit_semester2"),
            "land":         r.get("land"),
            "contact":      r.get("contact_name"),
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
    a = ap.parse_args()

    raw = fetch_csv(a.offline) if a.offline else fetch_graph()
    if not raw:
        print("[error] ไม่พบข้อมูล — ยกเลิกการสร้างไฟล์", file=sys.stderr)
        return 1

    payload = build_payload(raw)
    render(payload)

    # สรุปสั้น ๆ ลง log ของ GitHub Actions
    print("[summary] status:", dict(Counter(r["status"] for r in payload["rows"])))
    print("[summary] total limit:", f'{sum(r["limitNum"] for r in payload["rows"]):,.0f}')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
