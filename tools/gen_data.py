# -*- coding: utf-8 -*-
"""
gen_data.py — สร้าง/รีเฟรช snapshot ของ SharePoint List "DemoApp"

วิธีใช้
    python tools/gen_data.py <path/to/exported.csv>

สิ่งที่สคริปต์ทำ
    1) อ่าน CSV ที่ export จาก SharePoint List
    2) ตัดคอลัมน์ที่ไม่มีค่าเลยออก เพื่อลดขนาดไฟล์
    3) Mask ข้อมูลส่วนบุคคล (telephone, contact_number) ก่อนนำขึ้น repo
    4) แปลงวงเงิน (limit, limit_other) เป็นตัวเลข -> limit_num, limit_other_num
    5) เขียนไฟล์ assets/js/data.js และ data/demoapp_snapshot.json

ต้องมี: pandas  (pip install pandas)
"""
import datetime
import json
import os
import re
import sys

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_JS = os.path.join(ROOT, "assets", "js", "data.js")
OUT_JSON = os.path.join(ROOT, "data", "demoapp_snapshot.json")

SITE_URL = "https://dohomegroup.sharepoint.com/sites/AC-Accounting"
LIST_URL = SITE_URL + "/Lists/DemoApp"


def mask_phone(v: str) -> str:
    """แทนที่ตัวเลขทั้งหมดยกเว้น 3 หลักสุดท้ายด้วย * (ปกป้องข้อมูลส่วนบุคคล)"""
    d = re.sub(r"\D", "", str(v))
    if len(d) < 4:
        return ""
    return "*" * (len(d) - 3) + d[-3:]


def to_num(v):
    """แปลงข้อความวงเงินที่มี comma ให้เป็น float; คืน None ถ้าแปลงไม่ได้"""
    s = re.sub(r"[^\d.\-]", "", str(v))
    try:
        return float(s) if s not in ("", "-", ".") else None
    except ValueError:
        return None


def main(csv_path: str) -> None:
    df = pd.read_csv(csv_path, dtype=str, keep_default_na=False)

    # 1) ตัดคอลัมน์ว่างทั้งหมด
    empty_cols = [c for c in df.columns if (df[c].str.strip() == "").all()]
    df = df.drop(columns=empty_cols)
    df.columns = [c.strip() for c in df.columns]   # ตัดช่องว่างนำหน้าชื่อคอลัมน์ เช่น " other_property"

    # 2) mask PII
    for col in ("telephone", "contact_number"):
        if col in df.columns:
            df[col] = df[col].map(mask_phone)

    # 3) ฟิลด์คำนวณ
    if "limit" in df.columns:
        df["limit_num"] = df["limit"].map(to_num)
    if "limit_other" in df.columns:
        df["limit_other_num"] = df["limit_other"].map(to_num)

    records = json.loads(df.to_json(orient="records", force_ascii=False))
    records = [
        {k: (None if isinstance(v, str) and v.strip() == "" else v) for k, v in r.items()}
        for r in records
    ]

    meta = {
        "listTitle": "DemoApp",
        "listUrl": LIST_URL,
        "siteUrl": SITE_URL,
        "itemFormUrl": LIST_URL + "/DispForm.aspx?ID=",
        "snapshotDate": datetime.date.today().isoformat(),
        "rowCount": len(records),
        "droppedEmptyColumns": empty_cols,
    }

    js = "/* ไฟล์นี้ถูกสร้างอัตโนมัติโดย tools/gen_data.py - อย่าแก้ไขด้วยมือ */\n"
    js += "window.DEMOAPP_META = " + json.dumps(meta, ensure_ascii=False, indent=2) + ";\n"
    js += "window.DEMOAPP_DATA = " + json.dumps(records, ensure_ascii=False, indent=1) + ";\n"

    os.makedirs(os.path.dirname(OUT_JS), exist_ok=True)
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JS, "w", encoding="utf-8") as f:
        f.write(js)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump({"meta": meta, "items": records}, f, ensure_ascii=False, indent=1)

    print("ตัดคอลัมน์ว่าง :", len(empty_cols), empty_cols)
    print("จำนวนรายการ   :", len(records))
    print("เขียนไฟล์      :", OUT_JS)
    print("เขียนไฟล์      :", OUT_JSON)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    main(sys.argv[1])
