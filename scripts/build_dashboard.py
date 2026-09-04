#!/usr/bin/env python3
"""
=====================================================================
 build_dashboard.py
 แปลง raw JSON (จาก Graph API) -> index.html (Static Dashboard)
=====================================================================
 หน้าที่
   1) Normalize ข้อมูล DemoApp ให้เหลือเฉพาะ field ที่ Dashboard ใช้
   2) สร้าง Security Matrix (RBAC) จาก Admin_KycNew
   3) ฝังข้อมูลเป็น JSON ลงใน template แล้วเขียนเป็น index.html
 หมายเหตุ
   - ถ้าไม่มี raw_*.json (เช่นรัน local โดยไม่มี secret) จะใช้ data/sample_*.json
=====================================================================
"""

import json
import os
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
TPL = ROOT / "templates" / "dashboard.html"
OUT = ROOT / "index.html"

TZ = timezone(timedelta(hours=7))          # Asia/Bangkok
SLA_DAYS = int(os.environ.get("SLA_DAYS", "2"))

# ---- Email ที่ถือเป็น Admin (เห็นข้อมูลทั้งหมด) --------------------
#      แก้ไข/เพิ่มได้ที่นี่ หรือส่งผ่าน env ADMIN_EMAILS="a@x.com,b@x.com"
DEFAULT_ADMINS = [
    "phongsapan.mar@dohome.co.th",
    "piyatida.mali@dohome.co.th",
    "siratip.tha@dohome.co.th",
    "samniang.jai@dohome.co.th",
    "patcharapa.sri@dohome.co.th",
    "siriya.jan@dohome.co.th",
    "yutima.hem@dohome.co.th",
    "nattaya.pho@dohome.co.th",
    "patsachon.put@dohome.co.th",
]

# ---- จัดกลุ่มสถานะ (Status ภาษาไทย -> Status Group มาตรฐาน) --------
STATUS_GROUP = {
    "อนุมัติ-KYC": "Completed",
    "ผ่านการพิจารณาเบื้องต้น": "Completed",
    "รอดำเนินการ": "Pending",
    "รอการพิจารณาเบื้องต้น": "Pending",
    "Draft": "Pending",
    "รอผู้จัดการ D3 อนุมัติ": "In Progress",
    "ไม่ผ่านการพิจารณาเบื้องต้น": "Issue",
}


# --------------------------- UTILITIES -------------------------------
def load(name, fallback):
    """อ่านไฟล์ raw ถ้าไม่มีให้ใช้ sample (สำหรับรัน local/ทดสอบ)"""
    p = DATA / name
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    q = DATA / fallback
    if q.exists():
        print(f"! ไม่พบ {name} -> ใช้ {fallback} แทน")
        return json.loads(q.read_text(encoding="utf-8"))
    return []


def s(v):
    """แปลงค่าใด ๆ เป็น string ที่สะอาด (None/NaN -> '')"""
    if v is None:
        return ""
    t = str(v).strip()
    return "" if t.lower() in ("nan", "none", "null") else t


def num(v):
    """แปลงข้อความจำนวนเงิน '2,000,000' -> 2000000.0"""
    t = s(v).replace(",", "")
    try:
        return float(t)
    except ValueError:
        return 0.0


def iso(v):
    """normalize datetime string -> ISO UTC (หรือ '' ถ้า parse ไม่ได้)"""
    t = s(v)
    if not t:
        return ""
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S.%fZ",
                "%Y-%m-%dT%H:%M:%S%z", "%m/%d/%Y %H:%M:%S", "%Y-%m-%d"):
        try:
            d = datetime.strptime(t, fmt)
            if d.tzinfo is None:
                d = d.replace(tzinfo=timezone.utc)
            return d.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            continue
    return ""


def branch_code(b):
    """CMOO -> CM  (ใช้จับคู่สาขากับอีเมล GM-CM@)"""
    t = s(b).upper().replace(" ", "")
    return t[:-2] if t.endswith("OO") and len(t) > 2 else t


# ----------------------- 1) NORMALIZE MAIN ---------------------------
def normalize_main(rows):
    """แปลง raw DemoApp -> record ที่ Dashboard ใช้งาน"""
    out = []
    for r in rows:
        req = iso(r.get("Request TimeStamp") or r.get("Request_x0020_TimeStamp"))
        mod = iso(r.get("_Modified") or r.get("Modified"))
        status = s(r.get("Status")) or s(r.get("Status_1")) or "ไม่ระบุ"
        # ระยะเวลาดำเนินการ (ชั่วโมง) = Modified - Request
        hours = None
        if req and mod:
            d1 = datetime.strptime(req, "%Y-%m-%dT%H:%M:%SZ")
            d2 = datetime.strptime(mod, "%Y-%m-%dT%H:%M:%SZ")
            if d2 >= d1:
                hours = round((d2 - d1).total_seconds() / 3600, 2)
        out.append({
            "id": r.get("_ID") or r.get("ID") or 0,
            "title": s(r.get("Title")),
            "customerId": s(r.get("Customer_id")),
            "customer": s(r.get("Customer Name") or r.get("Customer_x0020_Name")),
            "branch": s(r.get("branch")).upper() or "ไม่ระบุสาขา",
            "branchCode": branch_code(r.get("branch")) or "N/A",
            "owner": s(r.get("Owner")) or "ไม่ระบุผู้ดูแล",
            "ownerEmail": s(r.get("OwnerEmail") or r.get("Owner_Email")).lower(),
            "status": status,
            "statusGroup": STATUS_GROUP.get(status, "In Progress"),
            "type": s(r.get("Type_Request")) or "ไม่ระบุประเภท",
            "team": s(r.get("type_teams")),
            "segment": s(r.get("Type1")),
            "province": s(r.get("province")),
            "district": s(r.get("district")),
            "business": s(r.get("business_type")),
            "limit": num(r.get("limit")),
            "requestAt": req,
            "modifiedAt": mod,
            "hours": hours,
        })
    return out


# ------------------- 2) SECURITY MATRIX (RBAC) -----------------------
def build_security(rows, branches):
    """
    สร้าง user directory จาก Admin_KycNew (คอลัมน์ Title = Email)
    กติกาแยก Role อัตโนมัติ
      - อยู่ใน ADMIN_EMAILS                       -> Admin        (เห็นทุกสาขา)
      - GM-XX@ / BI-OperationXX_GM@ / BI-VOperationXX_GM@
                                                  -> BranchManager (เห็นสาขา XX)
      - นอกเหนือจากนั้น                            -> Owner        (เห็นเฉพาะงานตนเอง)
    ทุก record มี isActive (ค่าเริ่มต้น Yes; ถ้า List มีคอลัมน์ IsActive จะใช้ค่านั้น)
    """
    admins = {e.strip().lower() for e in
              os.environ.get("ADMIN_EMAILS", ",".join(DEFAULT_ADMINS)).split(",")
              if e.strip()}
    valid_codes = {branch_code(b) for b in branches}
    users = {}

    for r in rows:
        email = s(r.get("Email") or r.get("Title")).lower()
        if "@" not in email:
            continue
        active = s(r.get("IsActive") or r.get("Is_Active") or "Yes")
        role = s(r.get("Role"))
        br = [c.strip().upper() for c in
              re.split(r"[;,]", s(r.get("Branch"))) if c.strip()]

        local = email.split("@")[0].lower()
        if not role:
            if email in admins:
                role = "Admin"
            else:
                m = (re.match(r"^gm-([a-z0-9]+)$", local)
                     or re.match(r"^bi-v?operation([a-z0-9]+)_gm$", local)
                     or re.match(r"^dohometogogm-([a-z0-9]+)$", local))
                if m and m.group(1).upper() in valid_codes | {"TRAINEE"}:
                    role, br = "BranchManager", [m.group(1).upper()]
                elif m:
                    role, br = "BranchManager", [m.group(1).upper()]
                else:
                    role = "Owner"
        users[email] = {
            "email": email,
            "role": role,
            "branches": br,
            "isActive": "No" if active.lower() in ("no", "false", "0") else "Yes",
            "displayName": s(r.get("DisplayName")) or local,
        }
    return users


# ---------------------------- 3) BUILD -------------------------------
def main():
    raw_main = load("raw_main.json", "sample_main.json")
    raw_sec = load("raw_security.json", "sample_security.json")

    records = normalize_main(raw_main)
    branches = sorted({r["branch"] for r in records})
    users = build_security(raw_sec, branches)

    now = datetime.now(TZ)
    meta = {
        "generatedAt": now.strftime("%Y-%m-%d %H:%M:%S"),
        "generatedAtISO": now.astimezone(timezone.utc)
                             .strftime("%Y-%m-%dT%H:%M:%SZ"),
        "totalRecords": len(records),
        "totalUsers": len(users),
        "slaDays": SLA_DAYS,
        "listUrl": "https://dohomegroup.sharepoint.com/sites/AC-Accounting/Lists/DemoApp",
        "secUrl": "https://dohomegroup.sharepoint.com/sites/AC-Accounting/Lists/Admin_KycNew",
    }

    html = TPL.read_text(encoding="utf-8")
    html = (html
            .replace("/*__META__*/null", json.dumps(meta, ensure_ascii=False))
            .replace("/*__DATA__*/[]",
                     json.dumps(records, ensure_ascii=False, separators=(",", ":")))
            .replace("/*__USERS__*/{}",
                     json.dumps(users, ensure_ascii=False, separators=(",", ":")))
            .replace("__BUILD_TIME__", meta["generatedAt"]))
    OUT.write_text(html, encoding="utf-8")

    # เก็บ dataset ที่ normalize แล้วไว้ให้ Power BI / Power Apps ต่อยอด
    (DATA / "dataset.json").write_text(
        json.dumps({"meta": meta, "records": records,
                    "users": list(users.values())},
                   ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"OK: index.html ({OUT.stat().st_size:,} bytes) | "
          f"records={len(records)} | users={len(users)} | "
          f"branches={len(branches)}")


if __name__ == "__main__":
    main()
