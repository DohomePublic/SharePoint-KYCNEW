# 📊 DemoApp Dashboard — คำขอวงเงินลูกค้า / KYC

Dashboard แบบ Single Page Application (HTML + CSS + JavaScript) ที่ดึงข้อมูลจาก
SharePoint List **DemoApp** และอัปเดตอัตโนมัติทุกวันผ่าน GitHub Actions + GitHub Pages

- แหล่งข้อมูล: <https://dohomegroup.sharepoint.com/sites/AC-Accounting/Lists/DemoApp/AllItems.aspx>
- ข้อมูลชุดปัจจุบัน: **67 รายการ • 50 คอลัมน์**

หน้า Dashboard ใช้โทนส้ม–ขาวสไตล์ DOHOME สำหรับหัวเว็บ เมนู ปุ่ม ตาราง และกราฟ
โดยคงสีสถานะสำเร็จ/รอ/ความเสี่ยงให้แยกแยะได้ และยังสลับโหมดมืดได้
ธีมอยู่ทั้งใน [index.html](./index.html) และ [scripts/template.html](./scripts/template.html)
จึงไม่ย้อนกลับเป็นสีน้ำเงินเมื่อ GitHub Actions สร้างหน้าใหม่

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

## ➕ การสร้างคำขอเพิ่มวงเงินจากหน้าเว็บ

หน้า [request-increase.html](./request-increase.html) ให้ผู้ใช้ลงชื่อเข้าใช้ Microsoft 365
และบันทึกคำขอเพิ่มวงเงินเป็นรายการใหม่ใน SharePoint List **DemoApp** โดยตรง

> ห้ามนำ `AZ_CLIENT_SECRET` ไปใส่ในหน้าเว็บหรือ JavaScript เด็ดขาด หน้าเว็บใช้
> Client ID และ Microsoft 365 sign-in ของผู้ใช้เท่านั้น

ก่อนใช้งาน IT Admin ต้องตั้งค่า App registration `a37bd62d-e74d-4ea0-9546-1eb5aa96f604`:

1. ไปที่ **Authentication → Add a platform → Single-page application (SPA)**
2. เพิ่ม Redirect URI ของหน้าใช้งานจริง เช่น
   `https://<organization>.github.io/<repository>/request-increase.html`
3. ไปที่ **API permissions → Microsoft Graph → Delegated permissions**
4. เพิ่ม `Sites.ReadWrite.All` และกด **Grant admin consent**
5. ให้ผู้ใช้มีสิทธิ์ **Edit** หรือสูงกว่าใน List `DemoApp`

หลังตั้งค่า ให้เปิดหน้า `request-increase.html` จาก Dashboard เมนู
**➕ สร้างคำขอเพิ่มวงเงิน** แล้วกดลงชื่อเข้าใช้ก่อนบันทึก

หน้าเว็บใช้ MSAL Browser 3 และรอ `initialize()` กับ `handleRedirectPromise()`
ให้เสร็จก่อนเปิดปุ่ม Login ปุ่มบันทึกจะเปิดหลังลงชื่อเข้าใช้สำเร็จเท่านั้น
หากพบ `uninitialized_public_client_application` ให้อัปโหลดไฟล์
`request-increase.html` ฉบับล่าสุดทั้งไฟล์ (ไม่ใช่แก้เฉพาะ URL ของ MSAL)
รอ GitHub Pages deploy สำเร็จ แล้วกด Ctrl+F5

หากพบ `AADSTS500111` และ Redirect URI ขึ้นต้นด้วย `file:///` แสดงว่าเปิดไฟล์
ในเครื่องโดยตรง ให้เปิดผ่าน
[หน้าเพิ่มวงเงินบน GitHub Pages](https://dohomepublic.github.io/SharePoint-KYCNEW/request-increase.html)
แทน หน้าเว็บจะปิด Login และบันทึกเมื่อใช้ protocol ที่ไม่รองรับ ห้ามลงทะเบียน
`file:///` เป็น SPA Redirect URI สำหรับทดสอบในเครื่องให้ใช้ HTTP บน localhost
และลงทะเบียน Redirect URI ของ localhost ให้ตรงด้วย

หน้าแบบฟอร์มจะค้นหา Site และ List ตามค่า:

การบันทึกจะจับคู่ชื่อ internal column ก่อน display name และตรวจ `readOnly`
ก่อนส่งข้อมูล หากพบ `Field 'LinkTitleNoMenu' is read-only` ให้อัปโหลดหน้าแบบฟอร์ม
ฉบับล่าสุด ไม่ต้องเพิ่มสิทธิ์เพื่อเขียนคอลัมน์นี้ เพราะเป็นคอลัมน์แสดงผลของ SharePoint
โดยค่าหัวข้อรายการต้องส่งไปที่ `Title` ไม่ใช่ `LinkTitleNoMenu`

รุ่นแบบฟอร์ม `2026-10-05.1720` กำหนด `Title` โดยตรง และตัด `LinkTitle` /
`LinkTitleNoMenu` ก่อนสร้าง JSON สำหรับ POST อีกชั้นหนึ่ง เลขรุ่นแสดงใต้ส่วน Login
เพื่อให้ตรวจได้ว่าแท็บปัจจุบันโหลดไฟล์ที่แก้แล้ว

| ค่า | ค่าเริ่มต้น |
|---|---|
| SharePoint host | `dohomegroup.sharepoint.com` |
| Site path | `/sites/AC-Accounting` |
| List name | `DemoApp` |

หาก Azure App registration เดิมใช้สำหรับ GitHub Actions เท่านั้น แนะนำให้ IT สร้าง
App registration แยกสำหรับ SPA เพื่อจำกัด Redirect URI และ Delegated permissions
เฉพาะการใช้งานของผู้ใช้

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

### แบบฟอร์มเปิดวงเงินลูกค้าใหม่ 5 ขั้นตอน

เปิด [request-new.html](./request-new.html) จากเมนู **ขอเปิดวงเงินลูกค้าใหม่**:

1. หมวดธุรกิจ ข้อมูลนิติบุคคล ผู้ติดต่อ และข้อมูล DBD/TSIC
2. ที่ตั้งสำนักงาน
3. วงเงิน เครดิตเทอม และหลักประกัน
4. โครงการอดีต/ปัจจุบัน/อนาคต และประวัติผู้ขอสินเชื่อ
5. ผู้ทำรายการ Channel สาขา ผู้รับงาน และตรวจทานก่อนบันทึก

รูปแบบสีส้มและสองคอลัมน์อ้างอิงภาพทั้ง 5 หน้า และปรับเป็นหนึ่งคอลัมน์บนมือถือ
ต้องผ่านการตรวจข้อมูลหน้าปัจจุบันก่อนข้ามไปข้างหน้า สามารถย้อนกลับโดยข้อมูลไม่หาย
โครงการอดีตและปัจจุบันมีช่องบังคับเพิ่มเติมเมื่อเลือกผู้รับเหมาก่อสร้าง
รหัสสมาชิกต้องเป็นเลข 9 หลัก เลขทะเบียน 13 หลัก โทรศัพท์ 9–10 หลัก และรหัสไปรษณีย์ 5 หลัก

**ที่ตั้งสำนักงาน:** เลือกจังหวัด → เขต/อำเภอ → แขวง/ตำบลจากชุดข้อมูลที่เก็บในเว็บ
ใช้งานได้ก่อน Login และไม่เรียกบริการข้อมูลที่อยู่ภายนอกขณะกรอกฟอร์ม
เมื่อเปลี่ยนจังหวัด/อำเภอจะล้างรายการที่ขึ้นต่อกันและรหัสไปรษณีย์ เพื่อไม่ให้บันทึกที่อยู่ปะปน
เลือกตำบลแล้วเติมรหัสไปรษณีย์อัตโนมัติ โดยแก้ไขรหัสได้เมื่อพื้นที่จริงใช้รหัสอื่น
บันทึกเป็นชื่อภาษาไทยใน `province`, `district`, `county` และรหัสใน `Postcode` ไม่ใช่ ID
ถ้าโหลดข้อมูลไม่สำเร็จจะแจ้งข้อผิดพลาดและมีปุ่มลองใหม่ ไม่ให้ข้ามขั้นตอนที่อยู่หรือบันทึก
รายชื่อผู้รับงานยังกรอกเอง ไม่เชื่อม Master Thep1, DBD หรือการจัดเส้นทางผู้อนุมัติอัตโนมัติ
ส่วนเอกสารแนบเป็นคำแนะนำตามภาพ ให้เพิ่มไฟล์ใน SharePoint หลังสร้างรายการ
ไม่ได้เขียนผลอนุมัติ วงเงินอนุมัติ หรือสถานะอนุมัติจากแบบฟอร์มนี้
สถานะเริ่มต้นและ workflow ใช้การตั้งค่าของ List เดิม

**การเผยแพร่:** อัปโหลด `request-new.html`, `request-new.css`, `request-new.js`
และ `sharepoint-client.js` ไว้โฟลเดอร์หลักเดียวกัน พร้อม `index.html`
ต้องอัปโหลด [data/thai-addresses.json](./data/thai-addresses.json) และ
[data/thai-addresses.LICENSE.txt](./data/thai-addresses.LICENSE.txt) ในโฟลเดอร์ `data` ด้วย
หน้าเพิ่มวงเงิน `request-increase.html` ใช้ `sharepoint-client.js` ร่วมกันแล้ว
จึงต้องอัปโหลดทั้งสองไฟล์พร้อมกันเมื่ออัปเดตหน้าเพิ่มวงเงินด้วย
ไม่ต้องรันสคริปต์ build เพื่อสร้างไฟล์แบบฟอร์มใหม่

IT ต้องเพิ่ม **SPA Redirect URI** อีกหนึ่งรายการ โดยเก็บ URI หน้าเพิ่มวงเงินเดิมไว้:

```text
https://dohomepublic.github.io/SharePoint-KYCNEW/request-new.html
```

ใช้ Client ID / Tenant เดิมและ delegated `Sites.ReadWrite.All` เช่นเดียวกับหน้าเพิ่มวงเงิน
ห้ามใส่ Client Secret ในหน้าเว็บ กรอกข้อมูลได้ก่อน Login แต่บันทึกได้หลัง Login
และอ่าน schema ของ List สำเร็จเท่านั้น

**การผูกข้อมูล:** `data-column` ใน HTML ระบุชื่อคอลัมน์ของแต่ละช่อง
ตัวเลือก Choice โหลดจาก schema จริง ถ้าเป็น Text และไม่มีตัวเลือกจะให้กรอกเอง
ยกเว้นจังหวัด/อำเภอ/ตำบล ซึ่งใช้ชุดข้อมูลที่อยู่เสมอ ไม่ถูกแทนที่หรือล้างค่าเมื่อ Login
แปลงชนิด Number/Currency/DateTime/Choice ตาม schema และไม่เขียนคอลัมน์ read-only
ฟิลด์ `Type_Request` ถูกกำหนดเป็น `คำขอเปิดวงเงินลูกค้าใหม่` และเวลาทำรายการสร้างเมื่อส่ง
ผู้ทำรายการจากบัญชี Login ถูกเก็บใน `Owner`; ผู้สร้างรายการของ SharePoint กำหนดโดย Graph

บางคอลัมน์ยังไม่ยืนยันจาก snapshot เช่น `Email`, `owner_phone`, `employee_code`
ถ้าไม่พบชื่อที่ระบุ หน้าจะมีส่วน **ตรวจคอลัมน์ SharePoint ก่อนบันทึก** ให้เลือกคอลัมน์จริง
โดยไม่เดาหรือทิ้งค่าที่กรอก หากเป็นช่องไม่บังคับสามารถเว้นข้อมูลว่างได้
Email ไม่ถูกเขียนลง `NotificationSent` โดยอัตโนมัติ เพราะคอลัมน์นั้นอาจเป็น Boolean
คอลัมน์ Person/Lookup ต้องใช้ Lookup ID จึงแจ้งข้อผิดพลาดแทนการส่งข้อความที่ไม่ถูกชนิด
การเลือก mapping นี้อยู่เฉพาะหน้านั้น ไม่เปลี่ยน schema ของ SharePoint

เมื่อสำเร็จจะแสดง Item ID และลิงก์รายการจริง ไม่ส่งซ้ำอัตโนมัติเมื่อเครือข่ายขาด
ถ้าเกิดข้อผิดพลาด ข้อมูลบนหน้ายังอยู่; ให้ตรวจรายการจริงก่อนกดส่งซ้ำในกรณีไม่ทราบผล
ข้อมูล Dashboard/Print เป็น snapshot จึงต้องรอรอบอัปเดต ไม่แสดงรายการใหม่ทันที
ไม่มีการเก็บข้อมูลฟอร์มหรือ access token ลงไฟล์ใน repository

**แหล่งข้อมูลที่อยู่:** [kongvut/thai-province-data](https://github.com/kongvut/thai-province-data)
ภายใต้ MIT License ที่ revision `7d689e478a577a1c9348f2b998c39dd4c2bf153d`
นำเข้า 77 จังหวัด, 928 เขต/อำเภอ และ 7,436 แขวง/ตำบล เก็บเฉพาะชื่อไทย ความสัมพันธ์ และรหัสไปรษณีย์
ตัดรายการเทศบาลรหัส 7074 และ 9077 ที่ไม่มีตำบลออก โดยบันทึกเหตุผลไว้ใน JSON
ชุดข้อมูลนี้ไม่ใช่การตรวจสอบที่อยู่กับทางราชการแบบเรียลไทม์
หากปรับปรุงข้อมูล ให้ตรวจชื่อซ้ำในแต่ละระดับ ความสัมพันธ์ และรหัสไปรษณีย์ 5 หลัก
พร้อมอัปเดต revision และคงประกาศสิทธิ์ของแหล่งข้อมูลไว้

**ทดสอบ mapping แบบไม่เขียนข้อมูลจริง:** เปิด
[tests/sharepoint-client.test.html](./tests/sharepoint-client.test.html)
จะรายงาน PASS/FAIL สำหรับชื่อคอลัมน์ซ้ำ, read-only, Number, Choice และ DateTime
ไม่ต้อง Login และไม่เรียก SharePoint

**ทดสอบตัวเลือกที่อยู่:** เปิด [tests/request-new-address.test.html](./tests/request-new-address.test.html)
ผ่าน HTTP/HTTPS เพื่อทดสอบชุดข้อมูลจริง การเลือกต่อเนื่อง การล้างค่าหลังเปลี่ยนจังหวัด
การคงข้อมูลหลัง Login รูปแบบข้อมูลที่ส่ง และการโหลดผิดพลาด/ลองใหม่
การ Login และบันทึกในชุดทดสอบนี้ใช้ client จำลอง ไม่เรียก Microsoft 365 หรือสร้างรายการจริง

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
├── request-increase.html            ← ฟอร์มสร้างคำขอเพิ่มวงเงิน (Microsoft 365 Login)
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
