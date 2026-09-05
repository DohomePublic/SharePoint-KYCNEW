# 📊 DemoApp Dashboard — คำขอวงเงินลูกค้า / KYC

Dashboard แบบ Single Page Application (HTML + CSS + JavaScript) ที่ดึงข้อมูลจาก
SharePoint List **DemoApp** และอัปเดตอัตโนมัติทุกวันผ่าน GitHub Actions + GitHub Pages

- แหล่งข้อมูล: <https://dohomegroup.sharepoint.com/sites/AC-Accounting/Lists/DemoApp/AllItems.aspx>
- ข้อมูลชุดปัจจุบัน: **42 รายการ • 50 คอลัมน์ • ช่วงวันที่ 2026-08-26 ถึง 2026-09-05**

---

## 🔄 วิธีทำงาน

1. GitHub Actions รันทุกวัน **07:00 น. เวลาไทย** (`cron: 0 0 * * *` = 00:00 UTC)
2. `scripts/build_dashboard.py` ดึงข้อมูลจาก SharePoint List `DemoApp` ผ่าน **Microsoft Graph API**
3. สร้าง `index.html` ใหม่ โดยฝังข้อมูลล่าสุดไว้ในตัวแปร `window.DEMOAPP_DATA`
4. Commit + Push → **GitHub Pages อัปเดตอัตโนมัติ**

> ไฟล์ `index.html` เป็นแบบ self-contained — ดาวน์โหลดไปเปิดในเครื่อง (แม้ไม่มีเน็ตองค์กร) ก็ยังใช้งานได้
> (ต้องมีอินเทอร์เน็ตเพื่อโหลด Chart.js / DataTables จาก CDN)

---

## ⚙️ การตั้งค่า GitHub Secrets

ไปที่ **Settings > Secrets and variables > Actions** แล้วเพิ่ม:

| Secret | Value |
|---|---|
| `AZURE_CLIENT_ID` | `a37bd62d-e74d-4ea0-9546-1eb5aa96f604` |
| `AZURE_TENANT_ID` | `7f8918d9-718a-495b-ac9a-17cba381c4a0` |
| `AZURE_CLIENT_SECRET` | (ค่า Client Secret จาก Azure AD — ห้าม commit ลงโค้ดเด็ดขาด) |

ข้อมูล App registration ที่ใช้จริง

| รายการ | ค่า |
|---|---|
| Application (client) ID | `a37bd62d-e74d-4ea0-9546-1eb5aa96f604` |
| Object ID | `f4e84724-e3f8-444b-981b-74ead3130171` |
| Directory (tenant) ID | `7f8918d9-718a-495b-ac9a-17cba381c4a0` |

> Client ID / Tenant ID / Object ID ไม่ใช่ความลับ (เป็นตัวระบุแอป) แต่ **Client Secret เป็นความลับ** ต้องเก็บใน GitHub Secrets เท่านั้น

ตัวแปรเสริม (ตั้งเป็น Variables ได้ ไม่บังคับ — มีค่า default ในสคริปต์แล้ว)

| Variable | Default |
|---|---|
| `SP_HOSTNAME` | `dohomegroup.sharepoint.com` |
| `SP_SITE_PATH` | `/sites/AC-Accounting` |
| `SP_LIST_NAME` | `DemoApp` |

---

## 🔑 การตั้งค่า Azure AD (IT Admin ทำครั้งเดียว)

1. เปิด **Azure Portal**
2. ไปที่ **Azure Active Directory > App registrations**
3. เปิด App ID: `a37bd62d-e74d-4ea0-9546-1eb5aa96f604` (Object ID `f4e84724-e3f8-444b-981b-74ead3130171`)
4. **Certificates & secrets → New client secret → Copy value**
5. **API permissions → Add permission → Microsoft Graph → Application permissions**
6. เพิ่ม **`Sites.Read.All`**
7. กด **Grant admin consent**

---

## 📁 โครงสร้างไฟล์

```
DemoApp-Dashboard/
├── .github/
│   └── workflows/
│       └── update-dashboard.yml     ← GitHub Actions workflow (รันทุกวัน 07:00 น.)
├── scripts/
│   ├── build_dashboard.py           ← ดึงข้อมูล Graph API + สร้าง index.html
│   └── template.html                ← เทมเพลต Dashboard (HTML/CSS/JS ทั้งหมด + คอมเมนต์)
├── data/
│   ├── demoapp.csv                  ← ข้อมูล snapshot (ใช้กับโหมด --offline)
│   └── demoapp.json                 ← ข้อมูลที่แปลงแล้ว (auto-generated)
├── docs/
│   ├── DATA_DICTIONARY.md           ← พจนานุกรมข้อมูลครบทั้ง 50 คอลัมน์
│   ├── BUSINESS_ANALYSIS.md         ← Insight / Anomaly / Risk / ข้อเสนอแนะ
│   ├── USER_GUIDE.md                ← คู่มือใช้งาน + ตัวอย่างการ Export
│   └── mockup.svg                   ← Mockup / Wireframe ของหน้า Dashboard
├── index.html                       ← Dashboard (auto-generated) ← GitHub Pages เสิร์ฟไฟล์นี้
└── README.md
```

---

## 🚀 การติดตั้ง

### 1) สร้าง repository และอัปโหลดไฟล์
```bash
git init
git add .
git commit -m "feat: DemoApp dashboard"
git branch -M main
git remote add origin https://github.com/<org>/<repo>.git
git push -u origin main
```

### 2) เปิด GitHub Pages
**Settings → Pages → Source: Deploy from a branch → Branch: `main` / root → Save**
จากนั้นเปิด `https://<org>.github.io/<repo>/`

### 3) ใส่ Secrets ตามตารางด้านบน แล้วรัน workflow ครั้งแรก
**Actions → Update DemoApp Dashboard → Run workflow**

### 4) รันในเครื่อง (ทดสอบ)
```bash
pip install requests

# โหมดออนไลน์ (ต้องมี Secrets ใน environment)
export AZURE_CLIENT_ID=... AZURE_TENANT_ID=... AZURE_CLIENT_SECRET=...
python scripts/build_dashboard.py

# โหมดออฟไลน์ (ใช้ไฟล์ CSV snapshot — ไม่ต้องมี credential)
python scripts/build_dashboard.py --offline data/demoapp.csv

# เปิดดู
python -m http.server 8080     # → http://localhost:8080/index.html
```

---

## 🖱️ รันด้วยตนเอง
ไปที่แท็บ **Actions** → เลือก **"Update DemoApp Dashboard"** → กด **Run workflow**

---

## 🧩 ความสามารถของ Dashboard

| หมวด | รายละเอียด |
|---|---|
| **KPI Cards** | คำขอทั้งหมด, วงเงินที่ขอรวม, อนุมัติ/ผ่านเบื้องต้น, อยู่ระหว่างรอ, ไม่ผ่านพิจารณา, Draft |
| **Bar Chart** | สถานะ, ประเภทธุรกิจ, จังหวัด Top 10, Owner Top 10, สาขา, มูลค่าวงเงินรายช่วงเวลา, Stacked สถานะรายช่วงเวลา, คุณภาพข้อมูล |
| **Pie / Doughnut** | ประเภทคำขอ (Type_Request), ทีมผู้ยื่น (type_teams) |
| **Line Chart** | แนวโน้มคำขอ **รายวัน / รายเดือน / รายปี** + เส้นค่าเฉลี่ยเคลื่อนที่ 3 ช่วง |
| **ค้นหา** | Search box ค้นทุกคอลัมน์ (debounce 250ms) |
| **Filter** | Status, ประเภทคำขอ (Category), ทีม, จังหวัด, ช่วงวันที่ (จาก–ถึง) |
| **Sort** | เรียงตามวันที่ / วงเงิน / ชื่อลูกค้า / สถานะ / ผู้ยื่น — Ascending & Descending |
| **Data Table** | DataTables แบ่งหน้า 10–250 แถว, `deferRender` รองรับข้อมูลจำนวนมาก |
| **Drill Down** | คลิกแถวในตาราง หรือคลิกแท่ง/ชิ้นกราฟ → เปิด Panel รายละเอียดทุกฟิลด์ + ลิงก์กลับ SharePoint |
| **Export** | Excel (.xlsx 2 ชีต), CSV (มี BOM อ่านภาษาไทยได้), PDF (A4 แนวนอน), PNG ของ Dashboard |
| **UX/UI** | Fluent Design (Pivot nav, depth shadow, Fluent color ramp), Responsive, Dark mode, รองรับปุ่ม Esc |

---

## 📌 สรุปข้อมูลชุดปัจจุบัน (ณ 2026-09-05)

- **จำนวนรายการทั้งหมด: 42 คำขอ** จากลูกค้าไม่ซ้ำ **30 ราย**
- **วงเงินที่ขอรวม 327,800,000 บาท** — เฉลี่ย 7,804,762 บาท/คำขอ, มัธยฐาน 2,000,000 บาท (ต่ำสุด 200,000 / สูงสุด 50,000,000)
- **สถานะ:** รอการพิจารณาเบื้องต้น 15 • รอดำเนินการ 13 • ไม่ผ่านการพิจารณาเบื้องต้น 6 • Draft 3 • ผ่านการพิจารณาเบื้องต้น 2 • อนุมัติ-KYC 2 • รอผู้จัดการ D3 อนุมัติ 1
- **ประเภทคำขอ:** คำขอเปิดวงเงินลูกค้าใหม่ 35 • คำขอเพิ่มวงเงิน 6 • C.ติดตามชุดเปิดตัวจริง 1
- **ทีม:** Store Operation 31 • Project Sales (PS) 4 • Wholesales (WS) 3 • Steel Key Account 2 • Retail 1 • ไม่ระบุ 1
- **แนวโน้ม:** ส.ค. 2026 = 8 คำขอ, ก.ย. 2026 = 34 คำขอ (สูงสุดวันที่ 2026-09-03 จำนวน 11 คำขอ)

ดูรายละเอียดเชิงลึกที่ [`docs/BUSINESS_ANALYSIS.md`](docs/BUSINESS_ANALYSIS.md)
และคำอธิบายทุกคอลัมน์ที่ [`docs/DATA_DICTIONARY.md`](docs/DATA_DICTIONARY.md)
