# คู่มือติดตั้งใช้งานบน GitHub (ทีละขั้นตอน)

ใช้เวลาประมาณ 20–30 นาที ทำครั้งเดียวจบ แล้วระบบจะรันเองทุกวัน 07:00 น.

---

## ขั้นที่ 1 — สร้าง App Registration บน Azure AD (สำหรับดึงข้อมูล SharePoint)

1. เข้า https://portal.azure.com → **Microsoft Entra ID** → **App registrations** → **New registration**
2. ตั้งชื่อ เช่น `KYC-Dashboard-Reader` → Supported account types = **Single tenant** → **Register**
3. หน้า **Overview** คัดลอกเก็บไว้ 2 ค่า
   - `Application (client) ID`  → จะใช้เป็น **CLIENT_ID**
   - `Directory (tenant) ID`    → จะใช้เป็น **TENANT_ID**
4. เมนู **Certificates & secrets** → **New client secret** → ตั้ง Description + Expires (แนะนำ 24 เดือน) → **Add**
   - คัดลอกค่าในคอลัมน์ **Value** ทันที (เห็นครั้งเดียว) → จะใช้เป็น **CLIENT_SECRET**
5. เมนู **API permissions** → **Add a permission** → **Microsoft Graph** → **Application permissions**
   - เลือก **`Sites.Selected`** (แนะนำ — ปลอดภัยสุด ให้สิทธิ์เฉพาะไซต์) หรือ **`Sites.Read.All`** (ง่ายกว่า แต่เห็นทุกไซต์)
   - กด **Add permissions** → แล้วกด **Grant admin consent for <องค์กร>** (ต้องเป็น Global Admin)

### ถ้าเลือก `Sites.Selected` ให้ผูกสิทธิ์กับไซต์ AC-Accounting เพิ่ม
รันใน PowerShell (ต้องมี Graph PowerShell + สิทธิ์ Admin) หรือใช้ Graph Explorer:

```
POST https://graph.microsoft.com/v1.0/sites/dohomegroup.sharepoint.com:/sites/AC-Accounting:/permissions
Content-Type: application/json

{
  "roles": ["read"],
  "grantedToIdentities": [{
    "application": { "id": "<CLIENT_ID>", "displayName": "KYC-Dashboard-Reader" }
  }]
}
```

---

## ขั้นที่ 2 — สร้าง Repository และอัปโหลดไฟล์

**วิธี A: ผ่านหน้าเว็บ (ง่ายสุด)**
1. https://github.com/new → Repository name = `kyc-daily-dashboard`
2. เลือก **Private** (แนะนำ เพราะข้อมูลลูกค้าถูกฝังใน `index.html`) → **Create repository**
3. กด **uploading an existing file** → ลากไฟล์/โฟลเดอร์ทั้งหมดที่ได้รับลงไป → **Commit changes**
   > ถ้าอัปโหลดผ่านเว็บแล้วโฟลเดอร์ `.github` หาย ให้สร้างเองผ่าน **Add file → Create new file**
   > แล้วพิมพ์ path ว่า `.github/workflows/daily-dashboard.yml` จากนั้นวางเนื้อหาไฟล์ลงไป

**วิธี B: ผ่าน Git command line**
```bash
cd kyc-daily-dashboard
git init
git add .
git commit -m "feat: KYC daily dashboard (SharePoint -> GitHub Pages)"
git branch -M main
git remote add origin https://github.com/<ORG-หรือ-USERNAME>/kyc-daily-dashboard.git
git push -u origin main
```

---

## ขั้นที่ 3 — ใส่ Secrets และ Variables

ไปที่ repo → **Settings** → **Secrets and variables** → **Actions**

**แท็บ Secrets** → **New repository secret** (ทำ 3 ครั้ง)

| Name | Value |
|---|---|
| `TENANT_ID` | Directory (tenant) ID จากขั้นที่ 1 |
| `CLIENT_ID` | Application (client) ID จากขั้นที่ 1 |
| `CLIENT_SECRET` | ค่า Value ของ client secret จากขั้นที่ 1 |

**แท็บ Variables** → **New repository variable** (ไม่บังคับ)

| Name | Value |
|---|---|
| `ADMIN_EMAILS` | `phongsapan.mar@dohome.co.th,piyatida.mali@dohome.co.th` (คั่นด้วย `,` ไม่มีเว้นวรรค) |

> ถ้าไม่ตั้ง `ADMIN_EMAILS` ระบบจะใช้รายชื่อ default ที่อยู่ในไฟล์ `scripts/build_dashboard.py`

---

## ขั้นที่ 4 — เปิด GitHub Pages

**Settings** → **Pages** → หัวข้อ *Build and deployment* → **Source = GitHub Actions** → บันทึก

> Repo แบบ Private จะเปิด Pages ได้เฉพาะแผน **GitHub Enterprise/Team**
> ถ้าใช้แผนฟรี มี 2 ทางเลือก:
> 1. ทำ repo เป็น Public (ห้ามทำถ้าข้อมูลเป็นความลับ)
> 2. ไม่เปิด Pages — ให้ workflow commit `index.html` ไว้เฉย ๆ แล้วดาวน์โหลดไฟล์ไปวางใน SharePoint Document Library
>    แล้ว embed บน Modern Page ด้วย Web Part **Embed** / **File viewer**

---

## ขั้นที่ 5 — ให้สิทธิ์ workflow เขียนกลับเข้า repo

**Settings** → **Actions** → **General** → *Workflow permissions*
เลือก **Read and write permissions** → **Save**

---

## ขั้นที่ 6 — ทดลองรันครั้งแรก (ไม่ต้องรอ 07:00 น.)

1. แท็บ **Actions** → เลือก workflow **Daily KYC Dashboard Build**
2. กด **Run workflow** → เลือก branch `main` → **Run workflow**
3. รอ ~1–2 นาที แล้วดู log ทีละ step ควรเห็นข้อความประมาณนี้

```
== 1) ขอ Access Token ==
== 2) หา Site ID ==
  site: AC-Accounting (dohomegroup.sharepoint.com,....)
== 3) ดึง Main Data: DemoApp ==
  DemoApp: page 1 -> รวม 30 รายการ
== 4) ดึง Security Data: Admin_KycNew ==
  Admin_KycNew: page 1 -> รวม 65 รายการ
OK: main=30 rows, security=65 rows
OK: index.html (82,388 bytes) | records=30 | users=65 | branches=14
```

4. เสร็จแล้วเปิดลิงก์ได้ที่
   `https://<username>.github.io/<repo>/`  (ไม่ต้องใส่ `?email=` แล้ว)

---

## ขั้นที่ 7 — แจกลิงก์ให้ผู้ใช้งาน

โหมดปัจจุบันคือ **Public View** — ส่งลิงก์เดียวให้ทุกคน เปิดแล้วเห็นข้อมูลครบทันที

| ลิงก์ | ใช้ทำอะไร |
|---|---|
| `https://<username>.github.io/<repo>/` | Dashboard ปกติ |
| `https://<username>.github.io/<repo>/?debug=1` | เปิด Debug Panel ดูจำนวน record / ชื่อสาขา / ตัวอย่าง JSON |

> ไม่มีหน้าล็อกอินและไม่มี Access Denied แล้ว ถ้าเปิดมาแล้วว่าง แปลว่า build ดึงข้อมูลไม่ได้จริง ๆ (ดู log ของ Actions)

---

## ขั้นที่ 8 — Embed บน SharePoint Modern Page (ถ้าต้องการ)

1. เปิดหน้า SharePoint → **Edit** → **+** → เลือก Web Part **Embed**
2. วางโค้ดนี้

```html
<iframe src="https://<username>.github.io/<repo>/index.html"
        width="100%" height="2400" frameborder="0"></iframe>
```

3. ถ้าโดนบล็อก ให้ Admin เพิ่ม `github.io` ใน
   **SharePoint admin center → Settings → Pages → HTML field security** (allow domain)

---

## 🔧 การปรับแต่งที่ใช้บ่อย

| ต้องการ | แก้ที่ไหน |
|---|---|
| เปลี่ยนเวลารัน | `.github/workflows/daily-dashboard.yml` → `cron` (เป็น UTC เสมอ; ICT = UTC+7) เช่น 08:00 ICT = `0 1 * * *` |
| รันวันละหลายรอบ | ใส่หลายบรรทัด เช่น `- cron: "0 0 * * *"` และ `- cron: "0 6 * * *"` |
| เปลี่ยนเกณฑ์ SLA | workflow → `env: SLA_DAYS: "3"` |
| เพิ่ม/ลด Admin | Variable `ADMIN_EMAILS` |
| เปลี่ยนการจัดกลุ่มสถานะ | `scripts/build_dashboard.py` → dict `STATUS_GROUP` |
| เปลี่ยนสีธีม | `templates/dashboard.html` → `:root { --brand: #005BAC; }` |
| เปลี่ยน List / Site | workflow → `env: MAIN_LIST`, `SEC_LIST`, `SP_SITE_PATH` |

> แก้ `templates/` หรือ `scripts/` แล้ว push ขึ้น `main` → workflow จะ build ใหม่ให้ทันที (มี trigger `push` ให้แล้ว)

---

## 🩺 แก้ปัญหาที่เจอบ่อย

| อาการใน log | สาเหตุ / วิธีแก้ |
|---|---|
| `ERROR: ไม่พบ TENANT_ID / CLIENT_ID / CLIENT_SECRET` | ยังไม่ได้ใส่ Secrets หรือสะกดชื่อผิด (ต้องตัวพิมพ์ใหญ่ตรงเป๊ะ) |
| `401 Unauthorized` | client secret หมดอายุ → สร้างใหม่แล้วอัปเดต Secret |
| `403 Forbidden` | ยังไม่ได้ **Grant admin consent** หรือยังไม่ได้ผูก `Sites.Selected` กับไซต์ |
| `404 Not Found` ตอนหา site | `SP_SITE_PATH` ผิด — ต้องเป็น `/sites/AC-Accounting` |
| `404` ตอนดึง list | ชื่อ list ไม่ตรง — ลองใช้ GUID ของ list แทนชื่อ |
| `Permission denied to github-actions[bot]` ตอน push | ยังไม่ได้ตั้ง **Read and write permissions** (ขั้นที่ 5) |
| `! ไม่พบ raw_main.json -> ใช้ sample_main.json` | step ดึงข้อมูลล้มเหลว — ดู log ขั้นก่อนหน้า (ตอนนี้กำลังโชว์ข้อมูลตัวอย่าง ไม่ใช่ข้อมูลจริง) |
| Dashboard ว่างเปล่า | เปิดด้วย `?debug=1` ดูจำนวน record; ถ้าเป็น 0 แปลว่า fetch ไม่สำเร็จ; ถ้ามี record แต่ไม่แสดง ให้ดู F12 → Console ว่าโหลด CDN (Bootstrap/Chart.js/DataTables) ได้ไหม |

---

## 🧪 ทดสอบบนเครื่องก่อนขึ้นจริง

```bash
pip install requests
python scripts/build_dashboard.py          # ไม่มี raw_*.json จะใช้ data/sample_*.json
python -m http.server 8080
# เปิด http://localhost:8080/index.html
```

ทดสอบดึงข้อมูลจริงบนเครื่อง (ระวังอย่า commit ค่าเหล่านี้):
```bash
export TENANT_ID=xxx CLIENT_ID=yyy CLIENT_SECRET=zzz
python scripts/fetch_sharepoint.py && python scripts/build_dashboard.py
```

> `.gitignore` กัน `data/raw_*.json` ไม่ให้ถูก commit ไว้ให้แล้ว
