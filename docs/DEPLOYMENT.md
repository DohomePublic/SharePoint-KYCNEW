# คู่มือการติดตั้งและใช้งาน

## 1. ความต้องการของระบบ

| รายการ | รายละเอียด |
|---|---|
| เบราว์เซอร์ | Microsoft Edge, Google Chrome, Firefox หรือ Safari รุ่นปัจจุบัน |
| อินเทอร์เน็ต | ต้องมี เพื่อโหลดไลบรารีจาก CDN (Chart.js, DataTables, SheetJS, jsPDF, html2canvas) |
| Server | **ไม่จำเป็น** — เป็น static site ล้วน |
| Python | ต้องใช้เฉพาะตอนรีเฟรช snapshot ด้วย `tools/gen_data.py` (ต้องมี pandas) |

---

## 2. วิธีติดตั้ง 4 แบบ

### แบบที่ 1 — เปิดจากเครื่องทันที
```
ดาวน์โหลดโฟลเดอร์ → ดับเบิลคลิก index.html
```
เหมาะกับการดูข้อมูลเร็ว ๆ ข้อจำกัด: ปุ่ม Export PNG/PDF บางเบราว์เซอร์อาจถูกบล็อกเพราะโปรโตคอล `file://`

### แบบที่ 2 — Local web server (แนะนำ)
```bash
cd SharePoint-KYCNEW
python -m http.server 8080
```
เปิด <http://localhost:8080> — ฟีเจอร์ทั้งหมดทำงานครบ

### แบบที่ 3 — GitHub + GitHub Pages
```bash
cd SharePoint-KYCNEW
git init -b main
git add .
git commit -m "feat: KYC dashboard from SharePoint DemoApp"
git remote add origin https://github.com/DohomePublic/SharePoint-KYCNEW.git
git push -u origin main
```
ตั้งค่าที่ GitHub → **Settings › Pages › Source = GitHub Actions**
workflow `.github/workflows/pages.yml` จะ deploy อัตโนมัติ
URL: `https://dohomepublic.github.io/SharePoint-KYCNEW/`

หากยังไม่ได้สร้าง repo และมี GitHub CLI:
```bash
gh repo create DohomePublic/SharePoint-KYCNEW --public --source=. --push
gh api -X POST repos/DohomePublic/SharePoint-KYCNEW/pages -f build_type=workflow
```

> ⚠️ **คำเตือนเรื่องข้อมูลส่วนบุคคล**
> snapshot มีชื่อลูกค้า ชื่อผู้ติดต่อ เลขทะเบียนนิติบุคคล และที่อยู่จริง
> ระบบ mask เฉพาะเบอร์โทร (`telephone`, `contact_number`) ให้แล้ว
> **ก่อน push ขึ้น repo สาธารณะ** ควรเลือกอย่างใดอย่างหนึ่ง:
> 1. ใช้ repo แบบ Private แทน
> 2. แทน `assets/js/data.js` และ `data/demoapp_snapshot.json` ด้วยข้อมูลจำลอง แล้วให้ระบบดึงข้อมูลจริงผ่านโหมด Live เมื่อ host ใน SharePoint
> 3. ขออนุมัติจากผู้ดูแลข้อมูล (Data Owner) ก่อนเผยแพร่

### แบบที่ 4 — ติดตั้งใน SharePoint (ได้ข้อมูลสด)
1. ไปที่ไซต์ `AC-Accounting` → **Site contents › Site Assets** สร้างโฟลเดอร์ `kyc`
2. อัปโหลด `index.html`, `assets/`, `data/` ทั้งหมดเข้าโฟลเดอร์นั้น
3. เปิด URL: `https://dohomegroup.sharepoint.com/sites/AC-Accounting/SiteAssets/kyc/index.html`
4. `sharepoint.js` จะตรวจพบว่าอยู่บนโดเมน `sharepoint.com` และดึงข้อมูลผ่าน REST API
   `_api/web/lists/getbytitle('DemoApp')/items` ทีละ 2,000 แถวจนครบ
5. ป้ายมุมขวาบนจะเปลี่ยนเป็น **Live SharePoint** — หากดึงไม่สำเร็จจะย้อนไปใช้ snapshot อัตโนมัติ

**สิทธิ์ที่ต้องมี:** ผู้ใช้ต้องมีสิทธิ์อย่างน้อย *Read* บน List `DemoApp`

---

## 3. การใช้งานหน้าจอ

| ต้องการทำ | วิธีทำ |
|---|---|
| ค้นหาข้ามทุกคอลัมน์ | พิมพ์ในช่อง "ค้นหาทุกคอลัมน์" — กรองอัตโนมัติหลังหยุดพิมพ์ 0.25 วินาที |
| กรองตามสถานะ/ประเภท/ทีม/จังหวัด | เลือกจาก dropdown (ตัวเลขในวงเล็บคือจำนวนรายการ) |
| กรองตามช่วงวันที่ | กรอก "ตั้งแต่วันที่" และ/หรือ "ถึงวันที่" |
| เรียงลำดับ | เลือกฟิลด์ที่ "เรียงตาม" + ทิศทาง Asc/Desc หรือคลิกหัวคอลัมน์ในตาราง |
| กรองด้วยกราฟ | คลิกแท่งในกราฟสถานะ หรือคลิกชิ้นใน Pie ประเภทคำขอ |
| สลับรายวัน/รายเดือน/รายปี | ไปเมนู "แนวโน้ม" แล้วกดปุ่มสลับด้านขวาของการ์ด |
| ดูรายละเอียดรายการ (Drill Down) | คลิกแถวในตารางข้อมูล / Top 10 / ตาราง Anomaly |
| เปิดรายการจริงใน SharePoint | ในหน้าต่างรายละเอียด กดปุ่ม "เปิดใน SharePoint" |
| ล้างตัวกรองทั้งหมด | กดปุ่ม "ล้างค่า" |
| ใช้บนมือถือ | กดไอคอน ☰ มุมซ้ายบนเพื่อเปิดเมนู |

> **หมายเหตุ:** ทุกการ Export จะส่งออก **เฉพาะข้อมูลที่ผ่านตัวกรองปัจจุบัน** ไม่ใช่ข้อมูลทั้งหมดเสมอไป

---

## 4. การปรับแต่ง

| ต้องการเปลี่ยน | แก้ที่ไฟล์ |
|---|---|
| ไซต์/ชื่อ List ที่ดึงข้อมูล | `assets/js/sharepoint.js` → `CONFIG.siteUrl`, `CONFIG.listTitle` |
| คอลัมน์ที่แสดงในตารางหลัก | `assets/js/app.js` → ตัวแปร `TABLE_COLS` |
| คำอธิบายคอลัมน์ใน Data Dictionary | `assets/js/app.js` → ตัวแปร `FIELD_DESC` |
| สีของสถานะ | `assets/js/app.js` → ตัวแปร `STATUS_COLOR` |
| เกณฑ์ตรวจจับความผิดปกติ | `assets/js/app.js` → ฟังก์ชัน `detectAnomalies()` (z-score, จำนวนวันค้าง) |
| สีธีม | `assets/css/style.css` → บล็อก `:root` (design tokens) |

---

## 5. การแก้ปัญหาที่พบบ่อย

| อาการ | สาเหตุ | วิธีแก้ |
|---|---|---|
| กราฟและตารางไม่ขึ้น | โหลด CDN ไม่ได้ (เครือข่ายองค์กรบล็อก) | ดาวน์โหลดไลบรารีมาไว้ในโฟลเดอร์ `assets/vendor/` แล้วแก้ path ใน `index.html` |
| ป้ายยังเป็น Snapshot ทั้งที่เปิดจาก SharePoint | ไม่มีสิทธิ์อ่าน List หรือถูก CORS บล็อก | ตรวจสอบสิทธิ์ผู้ใช้บน List `DemoApp` และดู error ใน Console (F12) |
| ภาษาไทยเพี้ยนเมื่อเปิด CSV ใน Excel | Excel ไม่อ่าน UTF-8 | ระบบใส่ BOM ให้แล้ว ถ้ายังเพี้ยนให้ใช้ Data › From Text/CSV แล้วเลือก UTF-8 |
| PDF ตัวหนังสือไทยไม่แสดง | jsPDF ไม่มีฟอนต์ไทยในตัว | ระบบจึง export PDF เป็นภาพหน้าจอความละเอียดสูงแทน จึงอ่านภาษาไทยได้ปกติ |
| กดปุ่ม Export PNG แล้วไม่มีอะไรเกิดขึ้น | เปิดด้วย `file://` | เปิดผ่าน local server (วิธีที่ 2) |
