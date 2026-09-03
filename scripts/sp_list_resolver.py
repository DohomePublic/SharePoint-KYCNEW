"""Drop-in fix for: [ERROR] list 'KYCData1' not found.

ใช้แทนโค้ดเดิมที่ hard-code ชื่อ list ใน scripts/build_dashboard.py
"""
import difflib
import os
import re
import sys

# ---- config: ชื่อ list ที่ถูกต้อง + ชื่อสำรอง (alias) ----
DATA_LIST_CANDIDATES = [
    os.getenv("SP_LIST_DATA", "").strip(),   # override ได้จาก env / GitHub secret
    "KYC_DATA_NEW",                          # << ชื่อจริงบนไซต์
    "KYCData1",                              # ชื่อเดิมที่พังใน log
    "DemoApp",                               # fallback สำหรับ demo
]
GROUP_LIST_CANDIDATES = [
    os.getenv("SP_LIST_GROUP", "").strip(),
    "Admin_KycNew",
]


def _norm(s: str) -> str:
    """ตัดอักขระคั่น + ทำ lowercase เพื่อเทียบชื่อแบบยืดหยุ่น
    (KYCData1 / kyc_data_new / KYC-DATA-NEW -> เทียบกันได้)"""
    return re.sub(r"[\s_\-\.]+", "", (s or "")).lower()


def resolve_list(available, candidates, kind="data"):
    """คืนชื่อ list จริงที่มีอยู่บนไซต์ จาก candidate list
    available : list[str] ชื่อ list ทั้งหมดที่ Graph/REST คืนมา
    """
    by_norm = {_norm(n): n for n in available}

    # 1) exact / normalized match ตามลำดับความสำคัญ
    for cand in candidates:
        if not cand:
            continue
        if cand in available:
            return cand
        hit = by_norm.get(_norm(cand))
        if hit:
            print(f"[WARN] list '{cand}' ไม่ตรงตัวอักษร ใช้ '{hit}' แทน")
            return hit

    # 2) prefix/contains match (KYCData1 -> KYC_DATA_NEW)
    for cand in candidates:
        if not cand:
            continue
        c = _norm(cand)
        core = re.sub(r"\d+$", "", c)  # ตัดเลขท้าย เช่น ...1
        near = [n for k, n in by_norm.items() if core and (k.startswith(core) or core in k)]
        if near:
            print(f"[WARN] ไม่พบ '{cand}' — ใช้ list ใกล้เคียง '{near[0]}'")
            return near[0]

    # 3) fuzzy suggestion แล้ว fail พร้อมคำแนะนำ
    first = next((c for c in candidates if c), kind)
    sugg = difflib.get_close_matches(first, available, n=5, cutoff=0.4)
    raise SystemExit(
        f"[ERROR] ไม่พบ {kind} list จาก candidates {[c for c in candidates if c]}\n"
        f"        ใกล้เคียงที่สุด: {sugg or '(ไม่มี)'}\n"
        f"        ตั้งค่า env SP_LIST_DATA / SP_LIST_GROUP เพื่อระบุชื่อให้ตรง"
    )


if __name__ == "__main__":
    # ชื่อ list ทั้งหมดตาม log จริงของไซต์ AC-Accounting
    available = """3CX_Survey_Template|AC-Data Request for approval of PO|AC-Status  PO|Admin_KycNew|AdvancePayment|AppUsageLog|ApproveAsset|AssetApprove|AssetApproveBranch|AssetClaim1|AssetCostCenter|AssetLocation|AssetProcurement_DB|Bank|BranchEnd|BranchStart|Claim|ClearStock|ClearStock-Asset|ClearStock-Employee|ClearStock-Stock|ClearStock-Vendor|ClearStockMailHR|ClearStockMailPurchase|DB_Asset_Request|DB_Asset_Request_001|Data_Account_Test|Data_Account_Update2025|Data_Purchase_Test|Data_Purchase_Update2025|DemoApp|DetailAssetPicture|DocRunning|DocRunning_01|Download_Name|Email_Master|Follow_KYCDoc|Get_Count_Acc|KYC_DATA_NEW|MailAccountPayment|MailAsignCliam|MailAsignCliamMonney|MailAsset|PattyCash|Purchase Request Data|Purchase Request System|SAPAssetDetail|TaxBillBoard|Update product|Update product Approve|Update product01|การร้องขอการเข้าถึง|ส่วนขยายเทมเพลตเว็บ|เอกสาร""".split("|")

    data = resolve_list(available, DATA_LIST_CANDIDATES, "data")
    group = resolve_list(available, GROUP_LIST_CANDIDATES, "group")
    print(f"[OK] data list  = {data}")
    print(f"[OK] group list = {group}")

    # เทสต์เคสพัง: ชื่อมั่วจริง ๆ ต้อง exit พร้อมคำแนะนำ
    if "--test-fail" in sys.argv:
        resolve_list(available, ["ZZZ_NotExist"], "data")
