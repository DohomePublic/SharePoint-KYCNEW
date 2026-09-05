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


# -------------------- FIELD NAME RESOLVER ----------------------------
#  Graph API คืนค่าเป็น "internal name" ซึ่งอาจไม่ตรงกับชื่อที่เห็นในหน้าเว็บ
#  เช่น  "Request TimeStamp"  ->  "Request_x0020_TimeStamp" หรือ "RequestTimeStamp"
#        "Customer Name"      ->  "Customer_x0020_Name" หรือ "CustomerName"
#  จึงเทียบชื่อแบบ normalize (ตัดช่องว่าง/_/x0020 + ไม่สนตัวพิมพ์)
def _norm_key(k):
    """
    ทำชื่อคอลัมน์ให้เทียบกันได้ : ตัดช่องว่าง/ขีด/_x0020_ + ไม่สนตัวพิมพ์

    ระวัง : ต้องใช้ \\W (unicode-aware) ไม่ใช่ [^a-z0-9]
    เพราะถ้าตัดอักษรที่ไม่ใช่ ASCII ทิ้ง ชื่อคอลัมน์ภาษาไทยทุกตัว
    จะกลายเป็นสตริงว่างเหมือนกันหมด แล้วจับคู่ผิดคอลัมน์
    (เคยทำให้ "สาขา" ไปตรงกับคอลัมน์ "วันที่ร้องขอ")
    """
    t = str(k).lower().replace("_x0020_", "")
    return re.sub(r"[\W_]+", "", t, flags=re.UNICODE)


def flat(v):
    """
    ทำให้ค่าที่ Graph ส่งมาเป็น "ข้อความที่อ่านออก"

    สำคัญมาก : คอลัมน์ชนิด Person / Lookup / Managed Metadata ของ SharePoint
    จะถูกส่งมาเป็น dict หรือ list ไม่ใช่ string เช่น
        {"LookupId": 12, "LookupValue": "สาขาอุดรธานี"}
        {"DisplayName": "สมชาย ใจดี", "Email": "somchai@..."}
        [{"LookupValue": "A"}, {"LookupValue": "B"}]
    ถ้าไม่แปลงก่อน str() จะได้ข้อความหน้าตาแบบ dict ทำให้ Dashboard
    แสดงเป็น "ไม่ระบุ..." หรือขึ้นข้อความประหลาด
    """
    if isinstance(v, dict):
        for k in ("LookupValue", "lookupValue", "DisplayName", "displayName",
                  "Title", "title", "Label", "label", "Value", "value",
                  "Email", "email"):
            if v.get(k) not in (None, ""):
                return v[k]
        return ""
    if isinstance(v, list):
        parts = [s(flat(x)) for x in v]
        return ", ".join([p for p in parts if p])
    return v


def flat_email(v):
    """ดึงอีเมลออกจากคอลัมน์ Person (dict) เช่น {'DisplayName':.., 'Email':..}"""
    if isinstance(v, dict):
        for k in ("Email", "email", "EMail", "UserName", "userPrincipalName"):
            t = s(v.get(k))
            if "@" in t:
                return t
        return ""
    if isinstance(v, list):
        for x in v:
            t = flat_email(x)
            if t:
                return t
        return ""
    t = s(v)
    return t if "@" in t else ""


def raw_pick(row, *names):
    """เหมือน pick() แต่คืน "ค่าดิบ" (ยังไม่ flatten) เพื่อดึงอีเมลจาก Person"""
    for n in names:
        if n in row and row[n] not in (None, ""):
            return row[n]
    idx = {_norm_key(k): k for k in row}
    for n in names:
        nk = _norm_key(n)
        if nk and idx.get(nk) is not None and row[idx[nk]] not in (None, ""):
            return row[idx[nk]]
    for n in names:
        nk = _norm_key(n)
        real = COLMAP.get(nk) if nk else None
        if real and row.get(real) not in (None, ""):
            return row[real]
    return None


# แผนที่ displayName -> internal name (เติมจาก data/raw_main_columns.json)
COLMAP = {}


def load_colmap():
    """
    อ่านแผนที่ชื่อคอลัมน์ที่ fetch_sharepoint.py บันทึกไว้
    ทำให้ pick() ค้นด้วย "ชื่อที่เห็นในหน้าเว็บ" ได้ แม้ internal name
    จะเป็นรหัสอ่านไม่ออก เช่น "_x0e2a__x0e32__x0e02__x0e32_"
    """
    global COLMAP
    p = DATA / "raw_main_columns.json"
    if not p.exists():
        return
    try:
        cols = json.loads(p.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return
    for c in cols:
        dn, nm = c.get("displayName"), c.get("name")
        key = _norm_key(dn) if dn else ""
        if key and nm:                   # กันคีย์ว่างไปทับกันเอง
            COLMAP.setdefault(key, nm)
    print(f"  โหลดแผนที่ชื่อคอลัมน์ {len(COLMAP)} รายการ จาก raw_main_columns.json")


def pick(row, *names, default=""):
    """ดึงค่าจาก row โดยลองชื่อที่เป็นไปได้ทีละตัว (ทนต่อ internal name)"""
    for n in names:                      # 1) ตรงตัวก่อน (เร็วสุด)
        if n in row and row[n] not in (None, ""):
            return flat(row[n])
    idx = {_norm_key(k): k for k in row}  # 2) เทียบแบบ normalize
    for n in names:
        nk = _norm_key(n)
        if not nk:
            continue
        k = idx.get(nk)
        if k is not None and row[k] not in (None, ""):
            return flat(row[k])
    for n in names:                      # 3) เทียบผ่าน displayName -> internal
        nk = _norm_key(n)
        real = COLMAP.get(nk) if nk else None
        if real and row.get(real) not in (None, ""):
            return flat(row[real])
        if real:
            k = idx.get(_norm_key(real))
            if k is not None and row[k] not in (None, ""):
                return flat(row[k])
    return default


# ------------------ AUTO FIELD DETECTION (ตรวจจากค่าในข้อมูล) ---------
#  ใช้เมื่อจับคู่ด้วย "ชื่อคอลัมน์" ไม่สำเร็จ
#  หลักการ : ไล่ดูทุกคอลัมน์แล้วเลือกคอลัมน์ที่ค่าส่วนใหญ่ "หน้าตาตรงกับ
#  สิ่งที่เรามองหา" เช่น สาขาต้องลงท้ายด้วย OO / สถานะต้องอยู่ใน STATUS_GROUP
SKIP_KEYS = {"_id", "id", "_modified", "_created", "modified", "created",
             "contenttype", "attachments", "hasattachments", "guid",
             "odataetag", "modifiedby", "createdby", "authorlookupid",
             "editorlookupid", "filesystemobjecttype", "serverredirected"}


def all_keys(rows):
    keys = []
    seen = set()
    for r in rows[:300]:
        for k in r:
            if k not in seen:
                seen.add(k)
                keys.append(k)
    return keys


def detect_field(rows, test, exclude=()):
    """
    หา key ที่ค่าผ่านเงื่อนไข test มากที่สุด
    คืน (key, จำนวนแถวที่ผ่าน) หรือ (None, 0)
    """
    best, best_n = None, 0
    ex = {_norm_key(e) for e in exclude}
    for k in all_keys(rows):
        nk = _norm_key(k)
        if nk in SKIP_KEYS or nk in ex or nk.endswith("lookupid"):
            continue
        n = 0
        for r in rows:
            try:
                if test(s(flat(r.get(k)))):
                    n += 1
            except Exception:
                pass
        if n > best_n:
            best, best_n = k, n
    return best, best_n


BRANCH_RE = re.compile(r"^[A-Z][A-Z0-9 ]{0,6}OO$")


def resolve_schema(rows):
    """
    ตรวจหาคอลัมน์สำคัญจาก "ค่าในข้อมูลจริง" แล้วรายงานลง log
    ทำงานเสริมจากการจับคู่ด้วยชื่อ — ถ้าชื่อจับคู่ไม่ได้ จะได้ไม่ขึ้น "ไม่ระบุ"
    """
    if not rows:
        return {}

    found = {}
    total = len(rows)

    # ---- สาขา : ค่าลงท้ายด้วย OO เช่น UDOO, CMOO, A YOO
    k, n = detect_field(rows, lambda v: bool(BRANCH_RE.match(v.upper())))
    if k and n >= max(1, total * 0.2):
        found["branch"] = k

    # ---- สถานะ : ค่าตรงกับรายการสถานะที่รู้จัก
    k, n = detect_field(rows, lambda v: v in STATUS_GROUP,
                        exclude=[found.get("branch", "")])
    if k and n >= max(1, total * 0.2):
        found["status"] = k

    # ---- อีเมลผู้ดูแล
    k, n = detect_field(
        rows, lambda v: bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[A-Za-z]{2,}", v)))
    if k and n >= max(1, total * 0.2):
        found["ownerEmail"] = k

    # ---- วันที่ร้องขอ : ค่าที่ parse เป็นวันที่ได้
    k, n = detect_field(rows, lambda v: bool(v) and bool(iso(v)),
                        exclude=["_Modified", "_Created", "Modified", "Created"])
    if k and n >= max(1, total * 0.5):
        found["requestAt"] = k

    if found:
        print("  ตรวจพบคอลัมน์อัตโนมัติจากค่าในข้อมูล:")
        for tgt, key in found.items():
            print(f"     {tgt:12} <- {key!r}")
    return found


def diagnose(rows, label):
    """พิมพ์ชื่อคอลัมน์จริงที่ได้จาก Graph ลง log ของ GitHub Actions"""
    if not rows:
        print(f"  [{label}] ไม่มีข้อมูล (0 rows)")
        return
    keys = all_keys(rows)
    print(f"  [{label}] {len(rows)} rows | {len(keys)} fields")
    print(f"  [{label}] fields: {', '.join(sorted(keys)[:60])}"
          + (" ..." if len(keys) > 60 else ""))
    # แสดงตัวอย่างค่า 1 แถว เพื่อดูว่าคอลัมน์ไหนมีข้อมูลอะไร
    r0 = rows[0]
    sample = []
    for k in sorted(keys)[:25]:
        v = s(flat(r0.get(k)))
        if v:
            sample.append(f"{k}={v[:28]}")
    if sample:
        print(f"  [{label}] ตัวอย่างแถวแรก: " + " | ".join(sample))


# ----------------------- 1) NORMALIZE MAIN ---------------------------
def normalize_main(rows):
    """แปลง raw DemoApp -> record ที่ Dashboard ใช้งาน"""
    out = []
    auto = resolve_schema(rows)          # คอลัมน์ที่ตรวจเจอจากค่าในข้อมูล

    def g(r, target, *names, default=""):
        """จับคู่ด้วยชื่อก่อน ถ้าไม่ได้ค่อยใช้คอลัมน์ที่ auto-detect เจอ"""
        v = pick(r, *names)
        if s(v):
            return v
        k = auto.get(target)
        if k and s(flat(r.get(k))):
            return flat(r[k])
        return default

    for r in rows:
        req = iso(g(r, "requestAt",
                    "Request TimeStamp", "Request_x0020_TimeStamp",
                    "RequestTimeStamp", "วันที่ร้องขอ", "Request Date",
                    "Created", "_Created"))
        mod = iso(pick(r, "_Modified", "Modified"))
        status = (s(g(r, "status", "Status", "สถานะ"))
                  or s(pick(r, "Status_1")) or "ไม่ระบุ")
        # ระยะเวลาดำเนินการ (ชั่วโมง) = Modified - Request
        hours = None
        if req and mod:
            d1 = datetime.strptime(req, "%Y-%m-%dT%H:%M:%SZ")
            d2 = datetime.strptime(mod, "%Y-%m-%dT%H:%M:%SZ")
            if d2 >= d1:
                hours = round((d2 - d1).total_seconds() / 3600, 2)
        branch = g(r, "branch", "branch", "Branch", "สาขา", "Branch Name", "สาขาที่รับผิดชอบ")
        owner_names = ("Owner", "OwnerName", "Owner Name", "ผู้รับผิดชอบ",
                       "ผู้ดูแล", "Responsible", "Responsible Person",
                       "AssignedTo", "Assigned To")
        owner = s(g(r, "owner", *owner_names))
        # อีเมล : ลองคอลัมน์อีเมลโดยตรงก่อน ถ้าไม่มีค่อยดึงจาก Person field
        omail = s(g(r, "ownerEmail", "OwnerEmail", "Owner_Email",
                    "Owner_x0020_Email", "อีเมลผู้ดูแล"))
        if "@" not in omail:
            omail = flat_email(raw_pick(r, *owner_names))
        out.append({
            "id": pick(r, "_ID", "ID", "Id", default=0),
            "title": s(pick(r, "Title")),
            "customerId": s(pick(r, "Customer_id", "CustomerId", "Customer ID",
                                 "รหัสลูกค้า")),
            "customer": s(pick(r, "Customer Name", "Customer_x0020_Name",
                               "CustomerName", "ชื่อลูกค้า", "Registered_Name")),
            "branch": s(branch).upper(),
            "branchCode": branch_code(branch),
            "branchInferred": False,
            "owner": owner or "ไม่ระบุผู้ดูแล",
            "ownerEmail": omail.lower(),
            "status": status,
            "statusGroup": STATUS_GROUP.get(status, "In Progress"),
            "type": s(g(r, "type", "Type_Request", "TypeRequest",
                        "ประเภทคำขอ", "Request Type")) or "ไม่ระบุประเภท",
            "team": s(pick(r, "type_teams", "TypeTeams")),
            "segment": s(pick(r, "Type1")),
            "province": s(pick(r, "province", "Province")),
            "district": s(pick(r, "district", "District")),
            "business": s(pick(r, "business_type", "BusinessType")),
            "limit": num(pick(r, "limit", "Limit")),
            "requestAt": req,
            "modifiedAt": mod,
            "hours": hours,
        })
    infer_branch_from_owner(out)
    for rec in out:
        if not rec["branch"]:
            rec["branch"] = "ไม่ระบุสาขา"
        if not rec["branchCode"]:
            rec["branchCode"] = "N/A"
    return out


# ---- เติม "สาขา" ที่ว่าง โดยอนุมานจากรหัสท้ายชื่อผู้ดูแล -------------
# รูปแบบชื่อจริงใน list : "ชื่อเล่น ชื่อจริง <ทีม> <รหัสสาขา>"
#   เช่น "โจ้ สหสัณห์ SG CM" -> CM,  "แจ๋ว สำเนียง CF HQ" -> HQ
OWNER_SUFFIX_RE = re.compile(r"([A-Za-z]{2,3})\s*$")
# รหัสที่ไม่ใช่สาขาขาย (สำนักงานใหญ่ / ศูนย์กลาง)
CENTRAL_CODES = {"HQ": "HQ (สำนักงานใหญ่)"}


def infer_branch_from_owner(records):
    """
    2-pass :
      pass 1 = เก็บรหัสสาขาที่ 'มีจริง' ในข้อมูล (จากแถวที่กรอกสาขามาแล้ว)
      pass 2 = แถวที่สาขาว่าง -> ดึงโทเคนตัวอักษรท้ายชื่อผู้ดูแลมาเทียบ
    ทำเครื่องหมาย branchInferred = True เพื่อความโปร่งใส
    """
    known = {}                      # "UD" -> "UDOO"
    for rec in records:
        b = s(rec.get("branch"))
        c = s(rec.get("branchCode"))
        if b and c:
            known.setdefault(c.upper(), b.upper())
    filled = 0
    guessed_new = set()
    for rec in records:
        if s(rec.get("branch")):
            continue
        m = OWNER_SUFFIX_RE.search(s(rec.get("owner")))
        if not m:
            continue
        code = m.group(1).upper()
        if code in known:
            rec["branch"] = known[code]
        elif code in CENTRAL_CODES:
            rec["branch"] = CENTRAL_CODES[code]
            guessed_new.add(code)
        elif len(code) == 2:
            # สาขาที่ยังไม่เคยเจอในชุดข้อมูลนี้ (เช่น HY, BP) -> เดารูปแบบ <CODE>OO
            rec["branch"] = code + "OO"
            guessed_new.add(code)
        else:
            continue
        rec["branchCode"] = code
        rec["branchInferred"] = True
        filled += 1
    if filled:
        print(f"  ℹ️  เติมสาขาจากชื่อผู้ดูแลอัตโนมัติ {filled} แถว"
              + (f" | รหัสใหม่ที่ไม่เคยพบ: {', '.join(sorted(guessed_new))}"
                 if guessed_new else ""))
    return records


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
        email = s(pick(r, "Email", "UserEmail", "Title")).lower()
        if "@" not in email:
            # เผื่อ Title ไม่ใช่อีเมล -> ไล่หา field ใดก็ได้ที่หน้าตาเป็นอีเมล
            email = next((s(v).lower() for v in r.values()
                          if isinstance(v, str) and re.fullmatch(
                              r"[^@\s]+@[^@\s]+\.[a-z]{2,}", s(v).lower())), "")
            if not email:
                continue
        active = s(pick(r, "IsActive", "Is_Active", "Active", default="Yes"))
        role = s(pick(r, "Role", "UserRole"))
        br = [c.strip().upper() for c in
              re.split(r"[;,]", s(pick(r, "Branch", "Branches", "สาขา")))
              if c.strip()]

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

    print("== ตรวจสอบข้อมูลดิบที่ได้จาก SharePoint ==")
    load_colmap()                        # แผนที่ displayName -> internal name
    diagnose(raw_main, "DemoApp")
    diagnose(raw_sec, "Admin_KycNew")
    main_raw = raw_main

    records = normalize_main(raw_main)
    branches = sorted({r["branch"] for r in records})
    users = build_security(raw_sec, branches)

    # ---- Validation: เตือนทันทีถ้า field สำคัญว่างทั้งหมด (mapping ผิด) ----
    print("== ตรวจสอบข้อมูลหลัง Normalize ==")
    if not records:
        print("  !! ไม่มี record เลย — dashboard จะว่างเปล่า")
    else:
        checks = {
            "requestAt": sum(1 for r in records if r["requestAt"]),
            "branch (ระบุสาขา)": sum(1 for r in records if r["branch"] != "ไม่ระบุสาขา"),
            "owner (ระบุผู้ดูแล)": sum(1 for r in records if r["owner"] != "ไม่ระบุผู้ดูแล"),
            "status (ไม่ใช่ 'ไม่ระบุ')": sum(1 for r in records if r["status"] != "ไม่ระบุ"),
            "customer": sum(1 for r in records if r["customer"]),
        }
        for k, v in checks.items():
            flag = "  " if v else "!!"
            print(f"  {flag} {k}: {v}/{len(records)}")
        if not checks["requestAt"]:
            print("  !! เตือน: ไม่มี Request TimeStamp เลย -> KPI รายวัน/Trend จะเป็น 0")
        unknown = sorted({r["status"] for r in records
                          if r["status"] not in STATUS_GROUP and r["status"] != "ไม่ระบุ"})
        if unknown:
            print(f"  !! สถานะที่ยังไม่ได้จัดกลุ่ม (จะถูกนับเป็น In Progress): {unknown}")
            print("     -> เพิ่มลงใน STATUS_GROUP ในไฟล์นี้เพื่อให้ KPI ถูกต้อง")

        # ---- ถ้ายังมีช่องที่จับคู่ไม่ได้ ให้โชว์ "คอลัมน์ที่ยังไม่ถูกใช้" ----
        #     เพื่อให้เห็นทันทีว่าควรเพิ่มชื่อคอลัมน์ไหนเข้าไปในตัวจับคู่
        missing = [k for k, v in checks.items() if v < len(records)]
        if missing and main_raw:
            used = set()
            for key in ("branch", "Branch", "สาขา", "Owner", "Status",
                        "Type_Request", "Customer Name", "Customer_id",
                        "Request TimeStamp", "Title"):
                used.add(_norm_key(key))
            spare = []
            for k in all_keys(main_raw):
                nk = _norm_key(k)
                if nk in used or nk in SKIP_KEYS or nk.endswith("lookupid"):
                    continue
                vals = [s(flat(r.get(k))) for r in main_raw[:20]]
                vals = [v for v in vals if v]
                if vals:
                    spare.append(f"{k} (เช่น {vals[0][:24]!r})")
            if spare:
                print(f"  ?? ช่องที่ยังไม่ครบ: {', '.join(missing)}")
                print("     คอลัมน์อื่นที่มีข้อมูลและอาจใช้แทนได้:")
                for line in spare[:25]:
                    print(f"       - {line}")
        print(f"  สาขาที่พบ ({len(branches)}): {', '.join(branches[:20])}")

    if not users:
        print("  ℹ️  ไม่พบผู้ใช้ใน Admin_KycNew (ไม่กระทบการแสดงผล "
              "เพราะ Dashboard เป็นแบบ Public ทุกคนดูได้)")
    else:
        roles = {}
        for u in users.values():
            roles[u["role"]] = roles.get(u["role"], 0) + 1
        print(f"  ผู้ใช้ {len(users)} คน แยกตาม Role: {roles}")

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
