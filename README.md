# SharePoint-KYCNEW — DemoApp Daily Dashboard

Dashboard รายวันสำหรับ SharePoint List **DemoApp** (ไซต์ `AC-Accounting`)
ไฟล์เดียวจบ: HTML + CSS + JavaScript · Bootstrap 5 · Chart.js · Dark Mode · Responsive

🔗 **Live:** https://dohomepublic.github.io/SharePoint-KYCNEW/

---

## 📁 โครงสร้าง repo

```
SharePoint-KYCNEW/
├── index.html                          ← Dashboard ทั้งหมด (ไฟล์เดียว)
├── data.json                           ← ข้อมูลสำรอง (MODE C)
├── .nojekyll                           ← ปิด Jekyll ของ GitHub Pages
├── README.md
└── .github/
    └── workflows/
        └── sync-sharepoint.yml         ← sync อัตโนมัติทุก 15 นาที
```

---

## 🚀 นำขึ้น GitHub (3 ขั้นตอน)

### ขั้นที่ 1 — Push ไฟล์

```bash
git clone https://github.com/DohomePublic/SharePoint-KYCNEW.git
cd SharePoint-KYCNEW

# คัดลอกไฟล์ทั้งหมดจาก zip มาวางทับ (รวมโฟลเดอร์ .github และไฟล์ .nojekyll)

git add -A
git commit -m "feat: DemoApp dashboard v3 พร้อม live connect ผ่าน Microsoft Graph"
git push origin main
```

> ⚠️ ไฟล์ `.nojekyll` และโฟลเดอร์ `.github` ขึ้นต้นด้วยจุด — บางระบบซ่อนไว้
> ตรวจว่า push ขึ้นไปจริงด้วย `git status` ก่อน commit

### ขั้นที่ 2 — เปิด GitHub Pages

**Settings → Pages**
- Source: `Deploy from a branch`
- Branch: `main` · Folder: `/ (root)`
- Save → รอ 1-2 นาที

### ขั้นที่ 3 — ตั้งค่า Entra ID (สำคัญที่สุด ⚠️)

ถ้าข้ามขั้นนี้ Dashboard จะแสดงข้อมูล snapshot อย่างเดียว ไม่ดึงสด

ไปที่ **Entra admin center → App registrations → Sharepoint-web**

**3.1 Authentication**
- คลิก **Add a platform** → เลือก **Single-page application** (ห้ามเลือก "Web")
- ใส่ Redirect URI ให้ครบทั้ง 2 บรรทัด:
  ```
  https://dohomepublic.github.io/SharePoint-KYCNEW/
  https://dohomepublic.github.io/SharePoint-KYCNEW/index.html
  ```
- Save

**3.2 API permissions**
- **Add a permission** → Microsoft Graph → **Delegated permissions** → `Sites.Read.All`
- คลิก **Grant admin consent for Dohome** (ต้องเป็น Global Admin)
- สถานะต้องขึ้นเครื่องหมายถูกเขียวทั้งแถว

**3.3 ทดสอบ**
เปิด https://dohomepublic.github.io/SharePoint-KYCNEW/
→ กดปุ่ม **"เชื่อมต่อ SharePoint"** → login → badge เปลี่ยนเป็นสีเขียว `GRAPH (MSAL)`

---

## 🔌 3 โหมดดึงข้อมูล (เลือกอัตโนมัติ + fallback ต่อกัน)

| โหมด | เงื่อนไข | ต้อง login | ใช้เมื่อไหร่ |
|------|----------|-----------|-------------|
| **A · EMBED** | หน้าอยู่บนโดเมน `sharepoint.com` | ไม่ต้อง | ฝังใน SharePoint Site Page |
| **B · GRAPH** | มี clientId + tenantId | ครั้งแรกครั้งเดียว | GitHub Pages ← **ใช้อันนี้** |
| **C · JSON** | มีไฟล์ `data.json` | ไม่ต้อง | หน้า public / ไม่มีสิทธิ์ Entra |

ระบบไล่ลองตามลำดับ A → B → C → snapshot ในไฟล์
แผง **"0. Data Connection"** บอกทุกครั้งว่าใช้โหมดไหน และโหมดที่ล้มเหลวเพราะอะไร

### ทางเลือก MODE A — ฝังใน SharePoint (ง่ายกว่า ไม่ต้องตั้ง Entra ID)

1. อัปโหลด `index.html` ไปที่ **Site Assets** ของ `/sites/AC-Accounting`
2. สร้าง Site Page → เพิ่ม web part **Embed** → วาง:
   ```html
   <iframe src="https://dohomegroup.sharepoint.com/sites/AC-Accounting/SiteAssets/index.html"
           width="100%" height="2400" frameborder="0"></iframe>
   ```
3. ถ้า Embed ถูกบล็อก ให้ admin เพิ่มโดเมนที่
   **SharePoint admin center → Settings → Embed HTML**

---

## 🤖 เปิด Auto-sync (MODE C)

ให้ GitHub Action ดึงข้อมูลมาเขียน `data.json` ทุก 15 นาที — หน้าเว็บจะสดโดยไม่ต้อง login เลย

**Settings → Secrets and variables → Actions → New repository secret** สร้าง 3 ตัว:

| ชื่อ | ค่า |
|------|-----|
| `AZ_TENANT_ID` | `7f8918d9-718a-495b-ac9a-17cba381c4a0` |
| `AZ_CLIENT_ID` | `a37bd62d-e74d-4ea0-9546-1eb5aa96f604` |
| `AZ_CLIENT_SECRET` | สร้างที่ Entra ID → Sharepoint-web → Certificates & secrets → New client secret |

จากนั้นเพิ่มสิทธิ์แบบ **Application** (คนละอันกับ Delegated ในขั้นที่ 3.2):
Microsoft Graph → **Application permissions** → `Sites.Read.All` → **Grant admin consent**

ทดสอบ: แท็บ **Actions** → `Sync SharePoint DemoApp` → **Run workflow**

---

## 🩺 แก้ปัญหา

| อาการ | สาเหตุ | วิธีแก้ |
|-------|--------|---------|
| badge แดง `SNAPSHOT` | ยังไม่ได้ login | กดปุ่ม "เชื่อมต่อ SharePoint" |
| `AADSTS50011` | Redirect URI ไม่ตรง | คัดลอก URI จากหน้าเว็บไปใส่ใน Entra ID |
| `AADSTS9002326` | เลือกแพลตฟอร์มผิด | ลบทิ้ง แล้วสร้างใหม่เป็น **SPA** |
| `AADSTS65001` / Graph 403 | ยังไม่ได้ consent | Grant admin consent สิทธิ์ `Sites.Read.All` |
| `AADSTS700016` | ไม่พบ Client ID | ตรวจ clientId/tenantId ใน `CONFIG` |
| Graph 404 | ไม่พบ list | ตรวจชื่อ `CONFIG.list` = `DemoApp` |
| หน้าเว็บยังเป็นของเก่า | CDN cache ของ GitHub Pages (~10 นาที) | Ctrl+Shift+R หรือรอสักครู่ |
| CORS error ใน console | เรียก `/_api/` จากนอกโดเมน SharePoint | ปกติ — ระบบจะ fallback ไป Graph เอง |

หมดทางแล้ว: ใช้ปุ่ม **CSV** อัปโหลดไฟล์ export จาก SharePoint โดยตรง (รองรับภาษาไทย)

---

## ⚙️ ปรับแต่ง

แก้ที่ block `CONFIG` บนสุดของ `<script>` ใน `index.html`

```js
const CONFIG = {
  list: "DemoApp",              // ชื่อ list
  autoRefreshSec: 300,          // refresh อัตโนมัติ (วินาที) · 0 = ปิด
  staleHours: 24,               // เกินกี่ชั่วโมงถือว่างานค้าง
  openStatuses:    ["รอดำเนินการ","รอการพิจารณาเบื้องต้น","รอผู้จัดการ D3 อนุมัติ","Draft"],
  closedStatuses:  ["อนุมัติ-KYC","ผ่านการพิจารณาเบื้องต้น"],
  problemStatuses: ["ไม่ผ่านการพิจารณาเบื้องต้น"]
};
```

---

## 📊 ฟีเจอร์

- **KPI 12 การ์ด** — Total, New Today, Closed Today, Pending, Success Rate, Avg Processing, ย้อนหลัง 7/30 วัน, กำลังดำเนินการ, เสร็จสิ้น, มีปัญหา, Pending Age
- **Filter** — keyword, สาขา, ผู้ดูแล, สถานะ, ช่วงวันที่
- **กราฟ 5 แบบ** — Bar (สาขา), Pie (สถานะ), Line (แนวโน้มรายวัน), Stacked Bar (สาขา×สถานะ), Top 10 Owner · คลิกกราฟเพื่อ drill down
- **Branch / Owner Analytics** — ranking, %, งานเปิด/ปิด/ค้าง
- **ตารางรายละเอียด** — sort ทุกคอลัมน์, ค้นหา, pagination, Export Excel/CSV, ลิงก์ไป DispForm
- **Auto Insight** — สาขาสูงสุด, ผู้ดูแลงานมากสุด, growth เทียบวันก่อน, anomaly detection, ข้อเสนอแนะเชิงธุรกิจ

---

## ⚠️ ปัญหาข้อมูลที่ตรวจพบ

คอลัมน์ `Status` และ `Status_1` ไม่ sync กัน **11 รายการ**
(ID 551, 554, 559, 563, 564, 565, 566, 567, 568, 570, 571)

Workflow เขียนค่าใหม่ลง `Status` แต่ `Status_1` ยังค้างค่าเดิม → รายงานที่ผูกกับ `Status_1` จะเห็นข้อมูลเก่า

Dashboard นี้อ่านจาก **`Status`** จึงถูกต้องเสมอ และขึ้นแบนเนอร์เตือนอัตโนมัติ

**แก้ที่ต้นทาง:** ใน Power Automate ให้ action *Update item* เขียนทั้ง `Status` และ `Status_1` พร้อมกัน
หรือเลิกใช้คอลัมน์คู่ แล้วให้ทุกรายงานอ่าน `Status` อย่างเดียว
