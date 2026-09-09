# 🚀 คู่มือติดตั้ง DemoApp Dashboard บน GitHub + GitHub Pages

> เอกสารนี้สอนติดตั้งตั้งแต่แตกไฟล์ `.zip` จนได้เว็บ Dashboard ที่อัปเดตอัตโนมัติทุกวัน 07:00 น. (เวลาไทย)
> ใช้เวลาประมาณ **15–20 นาที** (ไม่รวมเวลารอ IT Admin กด Grant admin consent)

---

## 📋 สรุปภาพรวม 6 ขั้นตอน

| ขั้น | สิ่งที่ทำ | ใครทำ | เวลา |
|---|---|---|---|
| 1 | แตกไฟล์ `.zip` ตรวจโครงสร้าง | คุณ | 2 นาที |
| 2 | สร้าง Repository บน GitHub + อัปโหลดไฟล์ | คุณ | 5 นาที |
| 3 | ตั้งค่า Azure AD (App permissions + Client secret) | **IT Admin** | 5 นาที |
| 4 | ใส่ GitHub Secrets 3 ตัว | คุณ | 3 นาที |
| 5 | เปิด GitHub Pages | คุณ | 2 นาที |
| 6 | กด Run workflow ทดสอบ | คุณ | 3 นาที |

---

## ขั้นที่ 1 — แตกไฟล์ `.zip` และตรวจโครงสร้าง

แตก `DemoApp-Dashboard.zip` จะได้โฟลเดอร์หน้าตาแบบนี้:

```
DemoApp-Dashboard/
├── .github/
│   └── workflows/
│       └── update-dashboard.yml   ← GitHub Actions workflow (ทำงานทุกวัน 07:00 น.)
├── scripts/
│   ├── build_dashboard.py         ← ดึงข้อมูล Graph API + สร้าง HTML
│   ├── template.html              ← เทมเพลต Dashboard
│   └── print_template.html        ← เทมเพลตฟอร์มพิมพ์ KYC (A4 2 หน้า)
├── templates/
│   ├── dashboard.html             ← สำเนา (fallback path)
│   └── print.html                 ← สำเนา (fallback path)
├── data/
│   ├── demoapp.csv                ← ข้อมูลสำรอง 67 รายการ (ใช้เมื่อ Graph ล่ม)
│   └── demoapp.json               ← ข้อมูลที่ build แล้ว
├── docs/
│   ├── DATA_DICTIONARY.md         ← Data Dictionary ทุกคอลัมน์
│   ├── BUSINESS_ANALYSIS.md       ← วิเคราะห์เชิงธุรกิจ + Anomaly + ข้อเสนอแนะ
│   ├── KYC_FORM_MAPPING.md        ← ตาราง mapping คอลัมน์ → ช่องในฟอร์ม
│   ├── USER_GUIDE.md              ← คู่มือผู้ใช้งาน
│   ├── INSTALL_GITHUB.md          ← เอกสารนี้
│   ├── kyc_form_mockup.svg        ← ตัวอย่างหน้าพิมพ์ หน้า 1
│   ├── kyc_form_mockup_p2.svg     ← ตัวอย่างหน้าพิมพ์ หน้า 2
│   └── mockup.svg                 ← ตัวอย่างหน้า Dashboard
├── index.html                     ← Dashboard (auto-generated)
├── print.html                     ← ฟอร์มพิมพ์ KYC (auto-generated)
├── .nojekyll                      ← ⚠️ ห้ามลบ! บอก Pages ไม่ต้องประมวลผล Jekyll
├── .gitignore
└── README.md
```

> ⚠️ **ไฟล์ที่มักหายตอนอัปโหลด**
> โฟลเดอร์ `.github/` และไฟล์ `.nojekyll` / `.gitignore` **ขึ้นต้นด้วยจุด** Windows Explorer และหน้าเว็บ
> "Upload files" ของ GitHub อาจซ่อนหรือข้ามไป → **ให้ใช้ Git command line (วิธี A) จะปลอดภัยที่สุด**
> ถ้า `.github/workflows/update-dashboard.yml` ไม่ขึ้น แท็บ Actions จะว่างเปล่า

---

## ขั้นที่ 2 — สร้าง Repository และอัปโหลด

### 2.1 สร้าง Repository

1. ไปที่ <https://github.com/new>
2. ตั้งค่า:
   - **Owner:** `DohomePublic` (หรือ organization ที่ใช้จริง)
   - **Repository name:** `DemoApp-Dashboard`
   - **Public** ✅ *(ต้องเป็น Public ถ้าใช้ GitHub Pages แบบฟรี — ถ้า repo เป็น Private ต้องมี GitHub Enterprise)*
   - ❌ **อย่า** ติ๊ก "Add a README file" / "Add .gitignore" / "Choose a license"
     (ไม่งั้นจะชนกับไฟล์ในซิป)
3. กด **Create repository**

### 2.2 อัปโหลด — วิธี A: Git command line ✅ แนะนำ

เปิด Terminal / Git Bash ในโฟลเดอร์ `DemoApp-Dashboard` ที่แตกไว้:

```bash
cd DemoApp-Dashboard

git init
git add -A
git status                # ✅ ตรวจว่ามี .github/workflows/update-dashboard.yml และ .nojekyll
git commit -m "เพิ่ม DemoApp Dashboard + ฟอร์มพิมพ์ KYC"
git branch -M main
git remote add origin https://github.com/DohomePublic/DemoApp-Dashboard.git
git push -u origin main
```

> **ถ้า push แล้วขอ password** → GitHub ยกเลิกรหัสผ่านแล้ว ให้ใช้ **Personal Access Token**
> สร้างที่ Settings → Developer settings → Personal access tokens → Tokens (classic) → Generate new token
> เลือก scope: `repo` + `workflow` แล้วนำ token มาใส่แทนรหัสผ่าน

### 2.3 อัปโหลด — วิธี B: หน้าเว็บ GitHub (ถ้าลง Git ไม่ได้)

1. ในหน้า repo ที่เพิ่งสร้าง กด **uploading an existing file**
2. ลากไฟล์และโฟลเดอร์ทั้งหมด **ยกเว้น `.github/`** เข้าไป → Commit
3. `.github/` ต้องสร้างมือ: กด **Add file → Create new file**
   - ช่องชื่อไฟล์พิมพ์: `.github/workflows/update-dashboard.yml`
     *(พิมพ์ `/` แล้ว GitHub จะสร้างโฟลเดอร์ให้อัตโนมัติ)*
   - เปิดไฟล์ `update-dashboard.yml` จากซิปด้วย Notepad → **คัดลอกทั้งหมด** → วางลงไป → Commit
4. ทำแบบเดียวกันกับไฟล์ `.nojekyll` (สร้างไฟล์เปล่า ชื่อ `.nojekyll` ไม่ต้องมีเนื้อหา)

---

## ขั้นที่ 3 — ตั้งค่า Azure AD *(IT Admin ทำครั้งเดียว)*

**ข้อมูล App ที่ใช้จริง:**

| รายการ | ค่า |
|---|---|
| Application (client) ID | `a37bd62d-e74d-4ea0-9546-1eb5aa96f604` |
| Object ID | `f4e84724-e3f8-444b-981b-74ead3130171` |
| Directory (tenant) ID | `7f8918d9-718a-495b-ac9a-17cba381c4a0` |

**ขั้นตอน:**

1. เปิด <https://portal.azure.com>
2. ไปที่ **Microsoft Entra ID** (ชื่อเดิม Azure Active Directory) → **App registrations**
3. เปิด App ที่ Client ID = `a37bd62d-e74d-4ea0-9546-1eb5aa96f604`
4. **สร้าง Client Secret**
   - เมนูซ้าย → **Certificates & secrets** → แท็บ **Client secrets** → **New client secret**
   - Description: `GitHub Actions - DemoApp Dashboard`
   - Expires: `24 months` (แนะนำ)
   - กด **Add** → **คัดลอกค่าในคอลัมน์ `Value` ทันที**
   - 🔴 **สำคัญมาก:** ค่า Secret จะแสดงแค่ครั้งเดียว ปิดหน้าแล้วดูย้อนหลังไม่ได้ ต้องสร้างใหม่
   - ⚠️ คัดลอกจากคอลัมน์ **Value** ไม่ใช่ **Secret ID** (เป็นคนละค่ากัน — สลับกันบ่อยมาก)
5. **ให้สิทธิ์ Microsoft Graph**
   - เมนูซ้าย → **API permissions** → **Add a permission**
   - เลือก **Microsoft Graph** → **Application permissions** *(ไม่ใช่ Delegated)*
   - ค้นหาและติ๊ก **`Sites.Read.All`**
   - กด **Add permissions**
6. **Grant admin consent**
   - กดปุ่ม **Grant admin consent for [ชื่อองค์กร]** → Yes
   - ✅ ต้องเห็นเครื่องหมายถูกสีเขียว **Granted for …** ในแถว `Sites.Read.All`
   - ❗ ถ้าข้ามขั้นนี้ workflow จะ error `403 Access denied`

---

## ขั้นที่ 4 — ใส่ GitHub Secrets

ไปที่ repo → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

เพิ่มทีละตัว รวม **3 ตัว**:

| ชื่อ Secret (ต้องตรงเป๊ะ ตัวพิมพ์ใหญ่-เล็ก) | ค่า |
|---|---|
| `AZ_CLIENT_ID` | `a37bd62d-e74d-4ea0-9546-1eb5aa96f604` |
| `AZ_TENANT_ID` | `7f8918d9-718a-495b-ac9a-17cba381c4a0` |
| `AZ_CLIENT_SECRET` | *(ค่า `Value` ที่คัดลอกมาจากขั้นที่ 3.4)* |

> ⚠️ **ชื่อ Secret ต้องเป็น `AZ_` ไม่ใช่ `AZURE_`** — workflow นี้อ่านชื่อ `AZ_CLIENT_ID` / `AZ_TENANT_ID` / `AZ_CLIENT_SECRET`
> ⚠️ เวลาวางค่า **ระวังช่องว่างหรือ Enter ติดท้าย** จะทำให้ authentication ล้มเหลว
> ⚠️ ห้ามใส่ค่า Secret ลงในไฟล์โค้ดหรือ commit ขึ้น repo เด็ดขาด

**ตรวจสอบ:** หลังใส่ครบ หน้า Secrets ต้องแสดง 3 รายการ (ค่าจะถูกซ่อนเป็น `***` เสมอ)

---

## ขั้นที่ 5 — เปิด GitHub Pages

1. repo → **Settings** → เมนูซ้าย **Pages**
2. ตั้งค่า **Build and deployment**
   - **Source:** `Deploy from a branch`
   - **Branch:** `main` · **Folder:** `/ (root)`
   - กด **Save**
3. รอประมาณ 1–2 นาที จะขึ้นแถบเขียว:
   > ✅ Your site is live at `https://dohomepublic.github.io/DemoApp-Dashboard/`

**URL ที่ได้:**

| หน้า | URL |
|---|---|
| Dashboard | `https://dohomepublic.github.io/DemoApp-Dashboard/` |
| ฟอร์มพิมพ์ KYC | `https://dohomepublic.github.io/DemoApp-Dashboard/print.html` |

---

## ขั้นที่ 6 — รัน Workflow ทดสอบ

### 6.1 รันโหมดตรวจสอบก่อน (แนะนำ)

1. repo → แท็บ **Actions**
2. เมนูซ้ายเลือก **Update DemoApp Dashboard**
3. กด **Run workflow** (ปุ่มขวาบน)
4. ติ๊ก ☑ **รันโหมดตรวจสอบการเชื่อมต่อ (diagnose)** → กด **Run workflow**

**ผลที่ควรได้:** log จะพิมพ์ Site ID, List ID, จำนวนรายการ และ **ชื่อ internal name ของทุกคอลัมน์**
👉 ใช้ตรวจว่าคอลัมน์ `Postcode`, `future_project`, `establishment_…` ฯลฯ มีชื่อจริงว่าอะไร

### 6.2 รันจริง

1. กด **Run workflow** อีกครั้ง โดย **ไม่ติ๊ก** diagnose
2. รอประมาณ 1–2 นาที จนขึ้นเครื่องหมายถูกสีเขียว ✅
3. เปิด URL ของ Pages → ต้องเห็นข้อมูลล่าสุดจาก SharePoint

**ขั้นตอนที่ workflow ทำ:**

```
Checkout → Setup Python → Install deps → Sync templates
  → Verify secrets (เช็ก 3 ตัวครบไหม)
  → Build จาก SharePoint (Graph API)
  → Verify (ต้องมีข้อมูล > 0 แถว และมีค่า Status)
  → Commit & Push → GitHub Pages อัปเดตเอง
```

---

## ⏰ ตารางการทำงานอัตโนมัติ

| เงื่อนไข | รายละเอียด |
|---|---|
| **ทุกวัน** | `cron: "0 0 * * *"` = **00:00 UTC = 07:00 น. เวลาไทย** |
| **กดเอง** | Actions → Update DemoApp Dashboard → Run workflow |
| **เมื่อแก้โค้ด** | push ที่แตะ `scripts/**` หรือไฟล์ workflow |

> 📌 **หมายเหตุเรื่อง cron ของ GitHub** — GitHub Actions อาจรันช้ากว่าเวลาที่ตั้งไว้ **5–30 นาที** ในช่วงที่ระบบมีงานเยอะ ถือเป็นพฤติกรรมปกติ
> 📌 repo ที่ **ไม่มี activity เกิน 60 วัน** GitHub จะ**ปิด scheduled workflow อัตโนมัติ** — จะมีอีเมลแจ้ง ให้เข้าไปกด Enable workflow ใหม่

---

## 🧪 ทดสอบบนเครื่องก่อน push (ไม่ต้องต่อ SharePoint)

```bash
# ติดตั้ง dependency
pip install requests

# build จากไฟล์ CSV สำรอง 67 รายการ (ไม่ต้องใช้ Secret)
python scripts/build_dashboard.py --offline data/demoapp.csv

# เปิดดูผลลัพธ์
#   Windows : start index.html
#   macOS   : open index.html
#   Linux   : xdg-open index.html
```

**ทดสอบเชื่อม SharePoint จากเครื่องตัวเอง:**

```bash
# macOS / Linux
export AZ_CLIENT_ID="a37bd62d-e74d-4ea0-9546-1eb5aa96f604"
export AZ_TENANT_ID="7f8918d9-718a-495b-ac9a-17cba381c4a0"
export AZ_CLIENT_SECRET="ค่าที่ได้จาก Azure"
python scripts/build_dashboard.py --diagnose     # ตรวจการเชื่อมต่อ + ดูชื่อคอลัมน์
python scripts/build_dashboard.py                # build จริง
```

```powershell
# Windows PowerShell
$env:AZ_CLIENT_ID     = "a37bd62d-e74d-4ea0-9546-1eb5aa96f604"
$env:AZ_TENANT_ID     = "7f8918d9-718a-495b-ac9a-17cba381c4a0"
$env:AZ_CLIENT_SECRET = "ค่าที่ได้จาก Azure"
python scripts/build_dashboard.py --diagnose
```

---

## 🔧 แก้ปัญหาที่พบบ่อย

| อาการ / ข้อความ error | สาเหตุ | วิธีแก้ |
|---|---|---|
| แท็บ Actions ว่างเปล่า ไม่มี workflow | ไฟล์ `.github/workflows/update-dashboard.yml` ไม่ได้ถูกอัปโหลด | สร้างไฟล์ด้วย **Add file → Create new file** ตามขั้น 2.3 |
| `ไม่พบ Secret: AZ_CLIENT_SECRET` | ยังไม่ได้ใส่ Secret หรือสะกดชื่อผิด | ตรวจชื่อต้องเป็น `AZ_CLIENT_SECRET` ไม่ใช่ `AZURE_CLIENT_SECRET` |
| `401 Unauthorized` / `invalid_client` | Client Secret ผิด / หมดอายุ / คัดลอก Secret ID มาแทน Value | สร้าง Secret ใหม่ใน Azure แล้วอัปเดต GitHub Secret |
| `403 Access denied` | ยังไม่ได้ **Grant admin consent** หรือให้ permission เป็น Delegated | เพิ่ม `Sites.Read.All` แบบ **Application** แล้วกด Grant admin consent |
| `404 Site not found` | path ของ site ผิด | แก้ `SP_SITE_PATH` ในไฟล์ workflow (ค่าปัจจุบัน `/sites/AC-Accounting`) |
| `404 List not found` | ลิสต์เปลี่ยนชื่อ | ใส่ `SP_LIST_ID` เป็น GUID ของลิสต์ (ดูจาก List settings → URL) แทน `SP_LIST_NAME` |
| `ทุกแถวไม่มีค่า Status` | ชื่อคอลัมน์ในลิสต์เปลี่ยน | รัน workflow โหมด **diagnose** ดูชื่อ internal name จริง |
| `FileNotFoundError: templates/dashboard.html` | โฟลเดอร์ `templates/` ไม่ได้อัปโหลด | อัปโหลด `templates/dashboard.html` และ `templates/print.html` |
| Pages ขึ้น 404 | ยังไม่เปิด Pages / เลือก branch ผิด | Settings → Pages → Branch `main`, Folder `/ (root)` |
| หน้าเว็บโหลดแต่ไม่มีข้อมูล (หน้าขาว) | ไฟล์ `.nojekyll` หาย | สร้างไฟล์ `.nojekyll` (ไฟล์เปล่า) ที่ root แล้ว commit |
| Workflow ขึ้น `Permission denied` ตอน push | สิทธิ์ของ GITHUB_TOKEN | Settings → Actions → General → Workflow permissions → เลือก **Read and write permissions** |
| scheduled workflow หยุดทำงานเอง | repo ไม่มี activity เกิน 60 วัน | Actions → เลือก workflow → กด **Enable workflow** |

---

## 🔐 ข้อควรระวังด้านความปลอดภัย

- ❌ **ห้าม** commit ค่า `AZ_CLIENT_SECRET` ลงในไฟล์ใด ๆ ใน repo — เก็บใน GitHub Secrets เท่านั้น
- ⚠️ repo เป็น **Public** แปลว่าข้อมูลลูกค้าใน `index.html` / `data/demoapp.json` **เปิดให้คนทั่วไปเห็นได้**
  → ถ้าข้อมูลเป็นความลับ ควรใช้ **repo Private + GitHub Enterprise** หรือ deploy บน server ภายในองค์กรแทน
- 🗓️ ตั้งเตือนก่อน Client Secret หมดอายุ (24 เดือน) เพื่อสร้างใหม่ทัน ไม่งั้น dashboard จะหยุดอัปเดต
- 🔄 ระบบมีกลไก `--fallback data/demoapp.csv` — ถ้า Graph API ล่ม จะใช้ข้อมูลสำรองแทน หน้าเว็บไม่กลายเป็นหน้าว่าง

---

## ✅ Checklist ก่อนใช้งานจริง

- [ ] แตกซิปแล้วเห็นโฟลเดอร์ `.github/workflows/` ครบ
- [ ] สร้าง repo และ push ขึ้น GitHub สำเร็จ
- [ ] IT Admin สร้าง Client Secret แล้ว
- [ ] `Sites.Read.All` เป็น **Application permission** และกด **Grant admin consent** แล้ว (มีถูกเขียว)
- [ ] ใส่ GitHub Secrets ครบ 3 ตัว ชื่อขึ้นต้น `AZ_`
- [ ] Settings → Actions → General → Workflow permissions = **Read and write**
- [ ] เปิด GitHub Pages (branch `main`, root)
- [ ] รัน workflow โหมด diagnose ผ่าน
- [ ] รัน workflow จริง ✅ เขียว
- [ ] เปิด URL Pages เห็นข้อมูลจริง
- [ ] เปิด `print.html` เลือกลูกค้า → กด Ctrl+P เห็นฟอร์ม A4 2 หน้า
