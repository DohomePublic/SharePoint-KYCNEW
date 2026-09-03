# sharepoint-web — KYC Daily Dashboard

Dashboard รายวันงาน KYC ดึงข้อมูลจาก SharePoint List ของไซต์ **AC-Accounting**
สร้างเป็น HTML ไฟล์เดียว (Bootstrap 5 + Chart.js) · Responsive · Dark Mode · จำกัดสิทธิ์ดูด้วย Email Whitelist

---

## 📁 โครงสร้าง

```
sharepoint-web/
├── .github/
│   └── workflows/
│       └── update-dashboard.yml   ← GitHub Actions workflow (รันทุกวัน 08:00 น. ไทย)
├── scripts/
│   └── build_dashboard.py         ← ดึงข้อมูล + สร้าง HTML (ฝัง template ไว้ในตัว)
├── index.html                     ← Dashboard (auto-generated — ห้ามแก้มือ)
└── README.md
```

> `scripts/build_dashboard.py` **ฝังเทมเพลต HTML ไว้ในตัวเอง** (ตัวแปร `TEMPLATE_HTML`)
> จึงไม่มีไฟล์ template ภายนอกให้หายหรือถูกเขียนทับ — แก้หน้าตา Dashboard ได้ที่ตัวแปรนี้โดยตรง
> (ห้ามลบ placeholder `__DATA__` และ `__ALLOWED__`)

---

## ✨ ฟีเจอร์

| กลุ่ม | รายละเอียด |
|---|---|
| **Access Control** | ตรวจอีเมลผู้ใช้อัตโนมัติจาก List `Admin_KycNew` (65 บัญชี) — ไม่อยู่ในรายชื่อ **ไม่เห็นรายงาน** |
| **KPI Cards** | Total / New Today / Closed Today / Pending / ปัญหา / Success Rate / Avg Processing Time / 7-30 วัน |
| **Filter** | Keyword, สาขา, ผู้ดูแล, สถานะ, ช่วงวันที่ |
| **Charts** | Bar สาขา · Doughnut สถานะ · Line รายวัน · Stacked สาขา×สถานะ · Top 10 Owner · วงเงินรายสาขา |
| **Analytics** | Ranking สาขา/ผู้ดูแล, %, งานเปิด-ปิด-ค้าง, Drill Down |
| **Detail Table** | Sort ทุกคอลัมน์, Search, Pagination, Export Excel/CSV (UTF-8 BOM รองรับภาษาไทย) |
| **Auto Insight** | สาขาสูงสุด, ผู้ดูแลงานมากสุด, แนวโน้มเทียบวันก่อน, Anomaly งานค้าง >3 วัน, ข้อเสนอแนะ |
| **Data Binding** | Live จาก SharePoint REST + fallback snapshot ที่ฝังในไฟล์ (offline ก็ไม่พัง) |

---

## 🚀 เริ่มใช้งาน

```bash
git clone https://github.com/<org>/sharepoint-web.git
cd sharepoint-web
pip install requests

# สร้าง index.html จากข้อมูลตัวอย่าง (ไม่ต้องมี credential)
python scripts/build_dashboard.py --sample

# ดึงสดจาก SharePoint
export TENANT_ID=... CLIENT_ID=... CLIENT_SECRET=...
export SP_LIST_DATA=KYC_DATA_NEW SP_LIST_GROUP=Admin_KycNew
python scripts/build_dashboard.py

# เซฟ snapshot ไว้ใช้ offline
python scripts/build_dashboard.py --dump-data data.json
python scripts/build_dashboard.py --offline data.json
```

---

## ⚙️ Environment Variables

| ตัวแปร | ค่าเริ่มต้น | หมายเหตุ |
|---|---|---|
| `TENANT_ID` / `CLIENT_ID` / `CLIENT_SECRET` | — | Azure AD App สิทธิ์ **`Sites.Read.All`** (Application) + Grant admin consent |
| `SP_HOST` | `dohomegroup.sharepoint.com` | |
| `SP_SITE_PATH` | `/sites/AC-Accounting` | |
| `SP_LIST_DATA` | `KYC_DATA_NEW` | ⚠️ ชื่อเดิม `KYCData1` **ไม่มีบนไซต์** |
| `SP_LIST_GROUP` | `Admin_KycNew` | รายชื่ออีเมลผู้มีสิทธิ์ดู |
| `OUT_FILE` | `index.html` | |

---

## 🔧 นำขึ้น GitHub

```bash
cd sharepoint-web
git init -b main
git add .
git commit -m "feat: KYC daily dashboard"

# สร้าง repo แบบ Private (มีข้อมูลลูกค้า + อีเมลพนักงาน)
gh repo create <org>/sharepoint-web --private --source=. --remote=origin --push

# ตั้ง secrets
gh secret set TENANT_ID     --body "<tenant-guid>"
gh secret set CLIENT_ID     --body "<client-id>"
gh secret set CLIENT_SECRET --body "<secret>"

# ทดสอบรัน (ไม่ต้องใช้ secret)
gh workflow run "Update Dashboard" -f sample=true
gh run watch
```

ไม่มี `gh` → สร้าง repo ที่ https://github.com/new (เลือก **Private**) แล้ว
`git remote add origin https://github.com/<org>/sharepoint-web.git && git push -u origin main`

**Workflow ทำอะไรบ้าง**
1. Self-check — compile สคริปต์ + build ตัวอย่าง + ตรวจ JS syntax
2. Build จาก SharePoint (หรือ `--sample` ถ้าเลือก)
3. **Commit `index.html` กลับเข้า repo อัตโนมัติ** (ข้ามถ้าไม่มีอะไรเปลี่ยน)
4. Upload artifact + (ตัวเลือก) Deploy GitHub Pages

---

## 📤 นำขึ้น SharePoint

1. อัปโหลด `index.html` ไปที่
   `AC-Accounting / Shared Documents / Dashboard/`
2. สร้าง Page → เพิ่ม Web Part **File viewer** → ชี้ไปที่ไฟล์ → Publish

> ต้องวางในไซต์เดียวกันเพื่อให้ตรวจสิทธิ์อัตโนมัติแบบ same-origin ผ่าน `_api/web/currentUser`
> ถ้าเปิดจากที่อื่นจะแสดงหน้ากรอกอีเมลแทน

**พฤติกรรม**
- อยู่ในกลุ่ม `Admin_KycNew` → เข้าได้
- ไม่อยู่ในกลุ่ม → “ไม่มีสิทธิ์เข้าถึงรายงานนี้” และ **ไม่เรนเดอร์ Dashboard เลย**
- รายชื่อสิทธิ์ sync สดจาก List → เพิ่ม/ลบคนแล้วมีผลทันที ไม่ต้อง build ใหม่

---

## 🩺 Troubleshooting

| ปัญหา | วิธีแก้ |
|---|---|
| `[ERROR] list 'KYCData1' not found` | ตั้ง `SP_LIST_DATA=KYC_DATA_NEW` (resolver จะจับชื่อใกล้เคียงให้เองพร้อม `[WARN]`) |
| `[ERROR] ไม่พบ TENANT_ID / CLIENT_ID / CLIENT_SECRET` | ตั้ง GitHub Secrets หรือรัน `--sample` |
| `[ERROR] template ต้องมี placeholder` | **ไม่เกิดแล้ว** — template ฝังอยู่ในสคริปต์ ไม่มีไฟล์ภายนอกให้หาย |
| Workflow commit ไม่ได้ | ตรวจว่า workflow มี `permissions: contents: write` |
| Dashboard ขึ้น badge เทา `Snapshot` | เปิดไฟล์นอกไซต์ SharePoint หรือ REST ถูกบล็อก — ข้อมูลจะใช้ snapshot ที่ฝังไว้ |

---

## 🔐 ความปลอดภัย

- ตั้ง repo เป็น **Private** — `index.html` มีชื่อลูกค้า วงเงิน และอีเมลพนักงาน
- ห้าม commit `CLIENT_SECRET` — ใช้ GitHub Secrets เท่านั้น
- ถ้าไม่ต้องการเผยแพร่สาธารณะ ให้ลบ step `Upload Pages artifact` และ job `deploy` ออกจาก workflow

---

## 📄 License
Internal use — DOHOME Group
