# 📊 DemoApp Dashboard — คำขอวงเงินลูกค้า / KYC

Dashboard แบบ Single Page Application (HTML + CSS + JavaScript) ที่ดึงข้อมูลจาก
SharePoint List **DemoApp** และอัปเดตอัตโนมัติทุกวันผ่าน GitHub Actions + GitHub Pages

- แหล่งข้อมูล: <https://dohomegroup.sharepoint.com/sites/AC-Accounting/Lists/DemoApp/AllItems.aspx>
- ข้อมูลชุดปัจจุบัน: **67 รายการ • 50 คอลัมน์**

> 🚀 **เพิ่งได้ไฟล์ .zip มา?** อ่าน [`docs/INSTALL_GITHUB.md`](docs/INSTALL_GITHUB.md) —
> คู่มือติดตั้งบน GitHub + GitHub Pages แบบทีละขั้น (6 ขั้นตอน ~15 นาที)

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
| `AZ_CLIENT_ID` | `a37bd62d-e74d-4ea0-9546-1eb5aa96f604` |
| `AZ_TENANT_ID` | `7f8918d9-718a-495b-ac9a-17cba381c4a0` |
| `AZ_CLIENT_SECRET` | (ค่า Client Secret จาก Azure AD — ห้าม commit ลงโค้ดเด็ดขาด) |

> สคริปต์รองรับชื่อ Secret **ทั้งสองแบบ**: `AZ_CLIENT_ID` / `AZ_TENANT_ID` / `AZ_CLIENT_SECRET` (ชื่อที่ใช้จริง)
> และ `AZURE_CLIENT_ID` / `AZURE_TENANT_ID` / `AZURE_CLIENT_SECRET` (ชื่อเดิม) โดยจะเลือกตัวที่มีค่าให้อัตโนมัติ
> และพิมพ์ลง log ว่าอ่านจากตัวแปรชื่อใด (ไม่แสดงค่า Secret จริง)

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
│   ├── build_dashboard.py           ← ดึงข้อมูล Graph API + สร้าง index.html / print.html
│   ├── template.html                ← เทมเพลต Dashboard ต้นฉบับ (HTML/CSS/JS + คอมเมนต์)
│   └── print_template.html          ← เทมเพลตฟอร์มพิมพ์ KYC (A4 2 หน้า)
├── templates/
│   ├── dashboard.html               ← สำเนาเทมเพลต (รองรับสคริปต์รุ่นเดิมที่อ้าง path นี้)
│   └── print.html                   ← สำเนาเทมเพลตฟอร์มพิมพ์
├── data/
│   ├── demoapp.csv                  ← ข้อมูล snapshot (ใช้กับโหมด --offline)
│   └── demoapp.json                 ← ข้อมูลที่แปลงแล้ว (auto-generated)
├── docs/
│   ├── INSTALL_GITHUB.md            ← 🚀 คู่มือติดตั้งบน GitHub + Pages (เริ่มที่นี่)
│   ├── DATA_DICTIONARY.md           ← พจนานุกรมข้อมูลครบทั้ง 50 คอลัมน์
│   ├── BUSINESS_ANALYSIS.md         ← Insight / Anomaly / Risk / ข้อเสนอแนะ
│   ├── USER_GUIDE.md                ← คู่มือใช้งาน + ตัวอย่างการ Export
│   ├── KYC_FORM_MAPPING.md          ← คู่มือหน้าพิมพ์ + Mapping คอลัมน์ → ช่องในฟอร์ม
│   ├── mockup.svg                   ← Mockup / Wireframe ของหน้า Dashboard
│   ├── kyc_form_mockup.svg          ← ตัวอย่างฟอร์ม KYC หน้า 1 (ข้อมูลจริง)
│   └── kyc_form_mockup_p2.svg       ← ตัวอย่างฟอร์ม KYC หน้า 2 (ข้อมูลจริง)
├── index.html                       ← Dashboard (auto-generated) ← GitHub Pages เสิร์ฟไฟล์นี้
├── print.html                       ← ฟอร์มพิมพ์เอกสาร KYC A4 2 หน้า (auto-generated)
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
(ติ๊ก **diagnose** ถ้าต้องการแค่ตรวจการเชื่อมต่อโดยไม่สร้างไฟล์)

---

## 🩺 แก้ปัญหา: workflow รันผ่าน แต่ข้อมูลไม่แสดง / ไม่ดึงจาก SharePoint

ขั้นแรกให้รัน **โหมดตรวจสอบ** เพื่อดูว่าติดขั้นไหน

```bash
# บนเครื่อง
export AZ_CLIENT_ID=...  AZ_TENANT_ID=...  AZ_CLIENT_SECRET=...
python scripts/build_dashboard.py --diagnose

# หรือบน GitHub: Actions → Run workflow → ติ๊ก diagnose
```

โหมดนี้จะพิมพ์: access token → site id → List ที่เจอ → **ชื่อคอลัมน์จริง (internal → display)** → ตัวอย่างข้อมูล 1 รายการ

| อาการใน log | สาเหตุ | วิธีแก้ |
|---|---|---|
| `HTTP 401` / `HTTP 403 AccessDenied` | ยังไม่ได้ให้สิทธิ์แอป | Azure AD → App registrations → API permissions → Microsoft Graph → **Application permissions** → `Sites.Read.All` → กด **Grant admin consent** |
| `HTTP 401 invalid_client` ตอนขอ token | Client Secret หมดอายุ/ผิด | สร้าง secret ใหม่แล้วอัปเดต `AZ_CLIENT_SECRET` |
| `ไม่พบ List ชื่อ 'DemoApp'` (พร้อมรายชื่อ List ที่มี) | Display name ไม่ตรงกับชื่อใน URL | ตั้ง `SP_LIST_NAME` ให้ตรง หรือใส่ `SP_LIST_ID` เป็น GUID ของ List |
| `HTTP 404` ตอนหา site | Site path ผิด | ตรวจ `SP_SITE_PATH` (ต้องเป็น `/sites/AC-Accounting`) |
| `fetched 0 items` | ลิสต์ว่าง หรือแอปเห็นเฉพาะบางรายการ | ตรวจข้อมูลใน SharePoint / สิทธิ์ระดับ item |
| `ดึงรายการมาได้ แต่ฟิลด์สำคัญว่างทั้งหมด` | ชื่อคอลัมน์ internal ≠ display | สคริปต์เวอร์ชันนี้แปลงให้อัตโนมัติแล้ว ถ้ายังพลาดให้ดูชื่อจริงจาก `--diagnose` แล้วเพิ่มชื่อใน `pick(...)` |
| workflow เขียว แต่หน้าเว็บเป็นข้อมูลเก่า | GitHub Pages ตั้ง source ผิด | Settings → Pages → Source = **Deploy from a branch** → `main` / `/ (root)` |
| หน้าเว็บ 404 หรือ CSS เพี้ยน | Jekyll กรองไฟล์ | ต้องมีไฟล์ `.nojekyll` ที่ root (มีให้แล้วในแพ็กเกจ) |

**หมายเหตุเชิงเทคนิคที่แก้ไปแล้วในเวอร์ชันนี้**
1. เดิมเรียก `?expand=fields&$top=500` → ผิด 2 จุด: ต้องเป็น `$expand` (มี `$`) และเมื่อใช้ `$expand=fields` ค่า `$top` สูงสุดคือ **200** — ของเดิมทำให้ Graph ตอบ error
2. เดิมเรียก `/lists/DemoApp` ตรง ๆ → 404 ถ้า display name ไม่ตรง — ตอนนี้ไล่หาจากรายการ List ทั้งหมด
3. เดิมไม่แปลง internal name (`Customer_x0020_Name`) เป็น display name (`Customer Name`) → ทุกฟิลด์ว่าง กราฟไม่ขึ้น
4. เดิมไม่มี error handling → เจอ `KeyError: 'id'` แทนข้อความบอกสาเหตุ
5. เพิ่มการตรวจก่อน push: ถ้าข้อมูลว่าง จะ **ไม่** เขียนทับ `index.html` เดิม

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
| **หน้าพิมพ์ KYC** | `print.html` — ฟอร์มกระดาษ A4 2 หน้าตามแบบทางการของดูโฮม ดึงข้อมูลจากลิสต์อัตโนมัติ |

---

## 🖨️ หน้าพิมพ์เอกสาร KYC (`print.html`)

ฟอร์ม **"เอกสาร KYC สำหรับลูกค้านิติบุคคลและองค์กร"** ขนาด **A4 แนวตั้ง 2 หน้า**
สร้างอัตโนมัติพร้อม `index.html` ทุกครั้งที่ build

**เข้าใช้งานได้ 2 ทาง**
1. กดปุ่ม **🖨️ พิมพ์เอกสาร KYC** บนเมนูหลักของ Dashboard
2. คลิกแถวในตาราง → หน้ารายละเอียด (drill-down) → ปุ่ม **🖨️ พิมพ์เอกสาร KYC**
   (เปิดตรงรายการนั้นทันที ผ่าน `print.html?id=558`)

**ความสามารถ**

| หัวข้อ | รายละเอียด |
|---|---|
| ช่องข้อมูล | **83 ช่อง** แบ่งเป็น **13 ส่วน**<br>**หน้า 1** (ที่อยู่ปทุมธานี): ① ข้อมูลนิติบุคคล → ② ผู้ติดต่อ → ③ ธุรกิจ/ประมาณการรายได้/วงเงิน (แยกเป็น 2 บล็อก: **วงเงินที่ขอกับดูโฮมครั้งนี้ \*** / **วงเงินที่มีกับซัพพลายเออร์อื่น**) → ④ ทรัพย์สินค้ำประกัน (ที่ดิน `land` \| ทรัพย์สินอื่น `Other_limits` + สถานะ 2 ช่อง) → ⑤ **ข้อมูลสถานประกอบการ** (พื้นที่ ตร.ม. / จำนวนพนักงาน / ประเภท / กรรมสิทธิ์) → ⑥ ข้อมูลโครงการ 3 บล็อกตามหน้าจอกรอกข้อมูลจริงของแอป (อดีต 4 ช่อง / ปัจจุบัน 5 ช่อง / อนาคต 5 ช่อง, วันที่แสดงเป็น พ.ศ.) → ⑦ ข้อมูลการขายสินค้า → ⑧ แผนการตลาด<br>**หน้า 2** (ที่อยู่อาคารออรัตนชัย กรุงเทพฯ + สโลแกน "ครบ ถูก ดี"): ⑨ ประวัติผู้บริหาร/กิจการ + บุคคลอ้างอิง → ⑩ ข้อมูลสรุปคำขอ → ⑪ ผู้อนุมัติ 2 ตำแหน่ง (ผู้ทำรายการ ← `Owner`, เจ้าหน้าที่สินเชื่อพิจารณา ← `AppCredit`) พร้อมเบอร์โทร/เวลาอนุมัติ → ⑫ วงเงินที่สินเชื่ออนุมัติ (ดึงจากคอลัมน์ **`CraditApprove`**) + ลายเซ็น 3 ช่อง |
| เลือกรายการ | ค้นหาด้วยชื่อบริษัท / รหัสสมาชิก / เลขทะเบียนนิติบุคคล |
| แก้ไขก่อนพิมพ์ | ปุ่มเปิดโหมด `contenteditable` เติมช่องที่ SharePoint ยังไม่มีคอลัมน์ |
| ช่องที่ไม่มีข้อมูล | แสดงเป็น **เส้นประ** ให้เขียนมือได้ |
| บันทึก PDF | ปุ่ม "พิมพ์ / บันทึก PDF" → ชื่อไฟล์ตั้งอัตโนมัติ `KYC-{รหัสสมาชิก}-{ชื่อบริษัท}` |
| ตัวอย่างหน้าจอ | `docs/kyc_form_mockup.svg` (หน้า 1) · `docs/kyc_form_mockup_p2.svg` (หน้า 2) |
| ผลทดสอบ | JS **282/282** · grid ครบ 12 คอลัมน์ทุกบล็อก · พอดีกระดาษ หน้า 1 = 262.3/281 มม. (93.3%), หน้า 2 = 215.7/281 มม. (76.8%) |
| Mapping คอลัมน์ | ดูตารางเต็มใน [`docs/KYC_FORM_MAPPING.md`](docs/KYC_FORM_MAPPING.md) |

> ⚠️ ตั้งค่าเครื่องพิมพ์: A4 · Portrait · Scale 100% · เปิด **Background graphics**

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
