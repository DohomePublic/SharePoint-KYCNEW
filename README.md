# KYC Daily Dashboard — DOHOME BI

Dashboard รายวันสำหรับงาน KYC จาก SharePoint List ของไซต์ **AC-Accounting**
HTML ไฟล์เดียว (Bootstrap 5 + Chart.js) · Responsive · Dark Mode · จำกัดสิทธิ์ดูด้วย Email Whitelist

![build](https://img.shields.io/badge/build-passing-brightgreen)
![license](https://img.shields.io/badge/license-Internal-blue)

---

## ✨ ฟีเจอร์

| กลุ่ม | รายละเอียด |
|---|---|
| **Access Control** | ตรวจอีเมลผู้ใช้อัตโนมัติจาก List `Admin_KycNew` (65 บัญชี) — ไม่อยู่ในรายชื่อ = ไม่เห็นรายงาน |
| **KPI Cards** | Total / New Today / Closed Today / Pending / ปัญหา / Success Rate / Avg Processing Time / 7-30 วัน |
| **Filter** | Keyword, สาขา, ผู้ดูแล, สถานะ, ช่วงวันที่ |
| **Charts** | Bar สาขา · Doughnut สถานะ · Line รายวัน · Stacked สาขา×สถานะ · Top 10 Owner · วงเงินรายสาขา |
| **Branch / Owner Analytics** | Ranking, %, งานเปิด/ปิด/ค้าง, Drill Down รายสาขา-รายผู้ดูแล |
| **Detail Table** | Sort ทุกคอลัมน์, Search, Pagination, Export Excel/CSV (UTF-8 BOM รองรับภาษาไทย) |
| **Auto Insight** | สาขาสูงสุด, ผู้ดูแลงานมากสุด, แนวโน้มเทียบวันก่อน, Anomaly งานค้าง >3 วัน, ข้อเสนอแนะเชิงธุรกิจ |
| **Data Binding** | Live จาก SharePoint REST + fallback snapshot ในไฟล์ (ไม่ crash เมื่อ offline) |

---

## 📁 โครงสร้าง

```
kyc-daily-dashboard/
├─ .github/workflows/build-dashboard.yml   # CI: build + artifact + GitHub Pages
├─ scripts/
│  ├─ build_dashboard.py                   # ตัว build หลัก (fail-fast + list resolver)
│  └─ sp_list_resolver.py                  # โมดูล resolve ชื่อ list
├─ templates/dashboard_template.html       # เทมเพลต (placeholder __DATA__ / __ALLOWED__)
├─ data/sample_data.json                   # snapshot สำหรับ build offline / รัน CI โดยไม่มี secret
├─ dist/KYC_Daily_Dashboard.html           # ผลลัพธ์พร้อมใช้
├─ docs/DEPLOY_README.md                   # คู่มือติดตั้งบน SharePoint
├─ requirements.txt
└─ README.md
```

---

## 🚀 Quick Start

```bash
git clone https://github.com/<org>/kyc-daily-dashboard.git
cd kyc-daily-dashboard
pip install -r requirements.txt

# build จาก snapshot (ไม่ต้องมี credential)
python scripts/build_dashboard.py --offline data/sample_data.json

# build สดจาก SharePoint
export TENANT_ID=... CLIENT_ID=... CLIENT_SECRET=...
export SP_LIST_DATA=KYC_DATA_NEW SP_LIST_GROUP=Admin_KycNew
python scripts/build_dashboard.py
```

ผลลัพธ์: `dist/KYC_Daily_Dashboard.html` → อัปโหลดขึ้น SharePoint แล้ววางด้วย Web Part **File viewer**
(ดูขั้นตอนละเอียดที่ [docs/DEPLOY_README.md](docs/DEPLOY_README.md))

---

## ⚙️ Environment Variables

| ตัวแปร | ค่าเริ่มต้น | หมายเหตุ |
|---|---|---|
| `TENANT_ID` / `CLIENT_ID` / `CLIENT_SECRET` | — | Azure AD App สิทธิ์ `Sites.Read.All` (Application) + admin consent |
| `SP_HOST` | `dohomegroup.sharepoint.com` | |
| `SP_SITE_PATH` | `/sites/AC-Accounting` | |
| `SP_LIST_DATA` | `KYC_DATA_NEW` | **เดิมตั้งเป็น `KYCData1` ทำให้ build พัง** |
| `SP_LIST_GROUP` | `Admin_KycNew` | รายชื่ออีเมลผู้มีสิทธิ์ดู |
| `OUT_FILE` | `dist/KYC_Daily_Dashboard.html` | |
| `TEMPLATE_FILE` | `templates/dashboard_template.html` | |

---

## 🛠️ แก้ปัญหา `[ERROR] list 'KYCData1' not found`

ชื่อ list บนไซต์จริงคือ **`KYC_DATA_NEW`** (ไม่ใช่ `KYCData1`)
เวอร์ชันนี้แก้แล้วด้วย resolver 3 ชั้น:

1. **Exact match** — ตรงตัวอักษร
2. **Normalized match** — ตัด `_ - .` และ ignore case (`admin-kycnew` → `Admin_KycNew`)
3. **Near match** — ตัดเลขท้าย + prefix/contains (`KYCData1` → `KYC_DATA_NEW`)
4. ไม่พบจริง → **exit 1 ทันที** พร้อมรายชื่อ list ใกล้เคียง (เดิม log ERROR แล้วรันต่อจนพังท้าย)

```
[WARN] ไม่พบ 'KYCData1' — ใช้ list ใกล้เคียง 'KYC_DATA_NEW'
[OK] wrote dist/KYC_Daily_Dashboard.html (64,322 bytes) records=23 viewers=65
```

---

## 🔐 ความปลอดภัย

- ห้าม commit `CLIENT_SECRET` ลง repo — ใช้ **GitHub Secrets** เท่านั้น
- `dist/*.html` มีข้อมูลลูกค้า + รายชื่ออีเมล → ตั้ง repo เป็น **Private**
- ถ้าใช้ GitHub Pages ให้เปิดเฉพาะ Pages แบบ private (GitHub Enterprise) มิฉะนั้นให้ปิด job `deploy-pages`

---

## 📄 License
Internal use — DOHOME Group เท่านั้น
