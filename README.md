# SharePoint-KYCNEW — KYC & Credit Limit Dashboard

Dashboard วิเคราะห์ข้อมูล **คำขอเปิด/เพิ่มวงเงินลูกค้า (KYC)** จาก SharePoint List **DemoApp**
(ไซต์ `AC-Accounting`) สร้างเป็น **Single Page Application** ด้วย HTML + CSS + JavaScript ล้วน
เปิดไฟล์ `index.html` ใน Browser ได้ทันที ไม่ต้องติดตั้ง server

> แหล่งข้อมูล: <https://dohomegroup.sharepoint.com/sites/AC-Accounting/Lists/DemoApp>

---

## 1. สรุปโครงสร้างข้อมูล (Data Profile)

| หัวข้อ | ค่า |
|---|---|
| จำนวนรายการทั้งหมด | **39 รายการ** |
| จำนวนคอลัมน์ใน List | **50 คอลัมน์** (ใช้งานจริง 34 คอลัมน์ + 16 คอลัมน์ที่ไม่มีข้อมูลเลย) |
| ช่วงเวลาของข้อมูล | 26 ส.ค. 2026 – 5 ก.ย. 2026 |
| คีย์หลัก | `_ID` (SharePoint Item ID) |
| แกนเวลาหลัก | `Request TimeStamp` |
| ตัวชี้วัดเชิงมูลค่า | `limit` (วงเงินที่ขอ) → แปลงเป็น `limit_num` |
| วงเงินรวมที่ขอ | **321,300,000 บาท** (เฉลี่ย 8,238,462 บาท/คำขอ, สูงสุด 50,000,000 บาท) |

### 1.1 การกระจายตามสถานะ (Status)

| สถานะ | จำนวน | สัดส่วน |
|---|---:|---:|
| รอการพิจารณาเบื้องต้น | 14 | 35.9% |
| รอดำเนินการ | 12 | 30.8% |
| ไม่ผ่านการพิจารณาเบื้องต้น | 6 | 15.4% |
| ผ่านการพิจารณาเบื้องต้น | 2 | 5.1% |
| อนุมัติ-KYC | 2 | 5.1% |
| Draft | 2 | 5.1% |
| รอผู้จัดการ D3 อนุมัติ | 1 | 2.6% |

### 1.2 การกระจายตามประเภทคำขอ (Type_Request)

| ประเภทคำขอ | จำนวน |
|---|---:|
| คำขอเปิดวงเงินลูกค้าใหม่ | 32 |
| คำขอเพิ่มวงเงิน | 6 |
| C.ติดตามชุดเปิดตัวจริง | 1 |

### 1.3 การกระจายตามทีม (type_teams)

| ทีม | จำนวน |
|---|---:|
| Store Operation | 30 |
| Project Sales (PS) | 4 |
| Wholesales (WS) | 3 |
| Retail | 1 |
| (ไม่ระบุ) | 1 |

### 1.4 ประเภทลูกค้า (Type1)

Existing 17 · Lead 12 · ไม่ระบุ 6 · ค้าปลีก 2 · (ค่าผิดพลาดเป็นอีเมล `thossarat.cha@dohome.co.th`) 2

### 1.5 แนวโน้มรายวัน (จำนวนคำขอ)

| วันที่ | จำนวน |
|---|---:|
| 2026-08-26 | 2 |
| 2026-08-27 | 5 |
| 2026-08-28 | 1 |
| 2026-09-01 | 1 |
| 2026-09-02 | 7 |
| 2026-09-03 | 11 |
| 2026-09-04 | 5 |
| 2026-09-05 | 7 |

รายเดือน: ส.ค. 2026 = 8 รายการ, ก.ย. 2026 = 31 รายการ · รายปี: 2026 = 39 รายการ

### 1.6 Top 10 คำขอวงเงินสูงสุด

| # | ลูกค้า | วงเงินที่ขอ (บาท) | สถานะ | ทีม | จังหวัด |
|---:|---|---:|---|---|---|
| 1 | บริษัท หาดใหญ่เรืองชัยการโยธา จำกัด | 50,000,000 | รอการพิจารณาเบื้องต้น | Project Sales (PS) | สงขลา |
| 2 | UDONTHANADEE ENGINEERING COMPANY LIMITED | 45,000,000 | รอดำเนินการ | Store Operation | อุดรธานี |
| 3 | UDONTHANADEE ENGINEERING COMPANY LIMITED | 45,000,000 | รอดำเนินการ | Store Operation | อุดรธานี |
| 4 | UDONTHANADEE ENGINEERING COMPANY LIMITED | 45,000,000 | รอการพิจารณาเบื้องต้น | Store Operation | อุดรธานี |
| 5 | ปัตตานีสหพันธ์ก่อสร้าง | 20,000,000 | ผ่านการพิจารณาเบื้องต้น | Project Sales (PS) | ปัตตานี |
| 6 | ปัตตานีสหพันธ์ก่อสร้าง | 20,000,000 | ไม่ผ่านการพิจารณาเบื้องต้น | Project Sales (PS) | ปัตตานี |
| 7 | ปัตตานีสหพันธ์ก่อสร้าง | 20,000,000 | รอดำเนินการ | Store Operation | ปัตตานี |
| 8 | ปัตตานีสหพันธ์ก่อสร้าง | 20,000,000 | อนุมัติ-KYC | Store Operation | ปัตตานี |
| 9 | บริษัท ชนะสุ พร็อพเพอร์ตี้ จำกัด | 6,000,000 | ผ่านการพิจารณาเบื้องต้น | Store Operation | นครปฐม |
| 10 | จำลองชัยคอนกรีต | 5,000,000 | รอดำเนินการ | Wholesales (WS) | ขอนแก่น |

Data Dictionary ฉบับเต็มดูที่ [`docs/DATA_DICTIONARY.md`](docs/DATA_DICTIONARY.md)
บทวิเคราะห์เชิงธุรกิจดูที่ [`docs/BUSINESS_INSIGHTS.md`](docs/BUSINESS_INSIGHTS.md)
Mockup หน้าจอดูที่ [`docs/mockup.svg`](docs/mockup.svg)

---

## 2. คุณสมบัติของ Dashboard

**KPI Cards (8 ใบ)** — คำขอทั้งหมด, วงเงินรวม, วงเงินเฉลี่ย, ลูกค้าไม่ซ้ำ, อนุมัติ-KYC, ผ่านพิจารณา, รอดำเนินการ, ไม่ผ่านพิจารณา

**กราฟ 11 ชุด (Chart.js)**
- Bar แนวนอน: จำนวนคำขอตามสถานะ *(คลิกแท่ง = กรองข้อมูลทันที)*
- Pie: สัดส่วนประเภทคำขอ *(คลิกชิ้น = กรอง)*
- Doughnut: ทีมขาย · PolarArea: ประเภทลูกค้า
- Bar: ประเภทธุรกิจ 8 อันดับ · Bar: วงเงินรวมตามจังหวัด
- Line + Bar ผสม: แนวโน้มจำนวนคำขอและวงเงิน (สลับ **รายวัน / รายเดือน / รายปี**)
- Line: คำขอสะสม · Stacked Bar: สถานะตามช่วงเวลา
- Bar: Top 10 Owner · Bar: Top 10 ลูกค้าตามวงเงินรวม

**ระบบค้นหาและกรอง** — Search Box ค้นทุกคอลัมน์ (debounce 250 ms), Filter: Status / Type_Request / type_teams / province, Filter ช่วงวันที่ (จาก–ถึง), Sort 6 ฟิลด์ ทั้ง Ascending และ Descending

**ตาราง Interactive (DataTables)** — 14 คอลัมน์, ค้นหาในตาราง, แบ่งหน้า 10/25/50/100/ทั้งหมด, `deferRender` รองรับข้อมูลจำนวนมาก, **คลิกแถวเพื่อ Drill Down** เห็นครบทุกฟิลด์พร้อมลิงก์เปิดรายการจริงใน SharePoint

**Export 4 รูปแบบ** — Excel (.xlsx 3 ชีต), CSV (UTF-8 BOM อ่านภาษาไทยได้), PDF (แนวนอน A4 หลายหน้า), รูปภาพ Dashboard (.png)

**วิเคราะห์อัตโนมัติ** — 6 การ์ด Insight + ตาราง Anomaly Detection 5 เกณฑ์ (วงเงิน z-score > 2, คำขอซ้ำ, ข้อมูลไม่ครบ, ค้างสถานะเกิน 7 วัน, Status ไม่ตรงกับ Status_1)

---

## 3. โครงสร้างโปรเจกต์

```
SharePoint-KYCNEW/
├─ index.html                    # โครงหน้า SPA ทั้งหมด (มี comment อธิบายทุกบล็อก)
├─ assets/
│  ├─ css/style.css              # ธีม Microsoft Fluent Design + responsive
│  └─ js/
│     ├─ data.js                 # ข้อมูล snapshot (สร้างอัตโนมัติจาก tools/gen_data.py)
│     ├─ sharepoint.js           # ตัวเชื่อม SharePoint REST API (โหมด Live)
│     └─ app.js                  # ตรรกะหลัก 9 ส่วน: filter, KPI, chart, table, insight, export
├─ data/demoapp_snapshot.json    # snapshot รูปแบบ JSON
├─ docs/
│  ├─ DATA_DICTIONARY.md         # คำอธิบายทุกคอลัมน์
│  ├─ BUSINESS_INSIGHTS.md       # บทวิเคราะห์เชิงธุรกิจ + ข้อเสนอแนะ + ความเสี่ยง
│  ├─ DEPLOYMENT.md              # วิธีติดตั้ง 3 แบบ
│  └─ mockup.svg                 # Mockup หน้าจอ Dashboard
├─ tools/gen_data.py             # สคริปต์ refresh snapshot จาก CSV ที่ export จาก SharePoint
├─ .github/workflows/pages.yml   # Deploy อัตโนมัติขึ้น GitHub Pages
└─ README.md
```

---

## 4. การติดตั้งและใช้งาน

### 4.1 ใช้งานทันที (ง่ายที่สุด)
ดาวน์โหลดโฟลเดอร์ทั้งหมด → ดับเบิลคลิก `index.html` → ใช้งานได้เลย (ต้องต่ออินเทอร์เน็ตเพื่อโหลด CDN ของ Chart.js/DataTables)

### 4.2 รันเป็น local server (แนะนำ ป้องกันปัญหา CORS)
```bash
cd SharePoint-KYCNEW
python -m http.server 8080
# เปิด http://localhost:8080
```

### 4.3 อัปโหลดขึ้น GitHub และเปิด GitHub Pages
```bash
cd SharePoint-KYCNEW
git init -b main
git add .
git commit -m "feat: KYC dashboard from SharePoint DemoApp"
git remote add origin https://github.com/DohomePublic/SharePoint-KYCNEW.git
git push -u origin main
```
จากนั้นที่ GitHub → **Settings › Pages › Source = GitHub Actions**
ไฟล์ `.github/workflows/pages.yml` จะ deploy ให้อัตโนมัติทุกครั้งที่ push
URL ที่ได้: `https://dohomepublic.github.io/SharePoint-KYCNEW/`

> ⚠️ **ก่อน push ขึ้น repo สาธารณะ** — ชุดข้อมูลนี้มีชื่อลูกค้า เลขทะเบียนนิติบุคคล และผู้ติดต่อ
> ระบบได้ mask เบอร์โทรศัพท์ให้แล้ว (`telephone`, `contact_number`) แต่ฟิลด์อื่นยังเป็นข้อมูลจริง
> หากต้องเผยแพร่สาธารณะ แนะนำใช้ repo แบบ **Private** หรือแทน `assets/js/data.js` ด้วยข้อมูลจำลอง

### 4.4 ติดตั้งใน SharePoint เพื่อดึงข้อมูล "สด"
1. อัปโหลดทั้งโฟลเดอร์ไปที่ `Site Assets` ของไซต์ `AC-Accounting`
2. เปิด `index.html` จาก URL ของ SharePoint
3. `sharepoint.js` จะตรวจพบว่าอยู่บนโดเมน `sharepoint.com` แล้วดึงข้อมูลผ่าน REST API อัตโนมัติ (แบ่งหน้า 2,000 แถว/ครั้ง) ป้ายมุมขวาบนจะเปลี่ยนเป็น **Live SharePoint**
4. หากดึงไม่สำเร็จ ระบบจะย้อนไปใช้ snapshot ให้เองโดยไม่ล่ม

### 4.5 อัปเดตข้อมูล snapshot
Export List เป็น CSV จาก SharePoint แล้วรัน:
```bash
python tools/gen_data.py path/to/exported.csv
```
สคริปต์จะ mask เบอร์โทร ตัดคอลัมน์ว่าง และเขียนทับ `assets/js/data.js` + `data/demoapp_snapshot.json`

---

## 5. ตัวอย่างการ Export

| ปุ่ม | ไฟล์ที่ได้ | รายละเอียด |
|---|---|---|
| Excel (.xlsx) | `KYC_DemoApp_2026-09-05.xlsx` | ชีต `Data` (ข้อมูลตามตัวกรอง 14 คอลัมน์), `Summary_Status` (สถานะ/จำนวน/วงเงินรวม), `Summary_Team` (ทีม/จำนวน/วงเงินรวม) |
| CSV | `KYC_DemoApp_2026-09-05.csv` | UTF-8 + BOM เปิดใน Excel ภาษาไทยไม่เพี้ยน |
| PDF | `KYC_Dashboard_2026-09-05.pdf` | A4 แนวนอน จับภาพ KPI + กราฟของมุมมองปัจจุบัน แบ่งหน้าอัตโนมัติ |
| PNG | `KYC_Dashboard_2026-09-05.png` | ภาพ Dashboard ความละเอียด 2x สำหรับแนบในสไลด์ |

ตัวอย่างเนื้อหาชีต `Summary_Status` ที่ได้เมื่อไม่ใส่ตัวกรอง:

| สถานะ | จำนวนคำขอ | วงเงินรวม (บาท) |
|---|---:|---:|
| รอการพิจารณาเบื้องต้น | 14 | 114,400,000 |
| รอดำเนินการ | 12 | 125,200,000 |
| ไม่ผ่านการพิจารณาเบื้องต้น | 6 | 33,000,000 |
| ผ่านการพิจารณาเบื้องต้น | 2 | 26,000,000 |
| อนุมัติ-KYC | 2 | 21,000,000 |
| Draft | 2 | 1,400,000 |
| รอผู้จัดการ D3 อนุมัติ | 1 | 300,000 |

*(ตัวเลขวงเงินรวมคำนวณสดจากข้อมูลขณะกดปุ่ม จึงเปลี่ยนตามตัวกรองที่เลือก)*

---

## 6. ด้านเทคนิค

| หัวข้อ | รายละเอียด |
|---|---|
| สถาปัตยกรรม | SPA แบบ client-side ล้วน ไม่มี build step ไม่มี backend |
| ไลบรารี | Chart.js 4.4.1, DataTables 1.13.8 + Responsive, jQuery 3.7.1, SheetJS 0.18.5, jsPDF 2.5.1, html2canvas 1.4.1 (ทั้งหมดผ่าน CDN) |
| ธีม | Microsoft Fluent 2 tokens — Communication Blue `#0F6CBD`, Success `#107C10`, Warning `#F7630C`, Danger `#C50F1F` |
| Responsive | Breakpoint 1024px และ 820px, สไลด์เมนูด้านข้างบนมือถือ, มี print stylesheet |
| ประสิทธิภาพ | `deferRender` ของ DataTables, destroy chart ก่อน re-render กัน memory leak, debounce การค้นหา, ตัด 16 คอลัมน์ว่างออกจาก payload |
| ความปลอดภัย | escape HTML ทุกค่าที่ render ป้องกัน XSS, mask เบอร์โทรใน snapshot |
| รองรับเบราว์เซอร์ | Edge / Chrome / Firefox / Safari รุ่นปัจจุบัน |
