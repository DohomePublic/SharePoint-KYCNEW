# SharePoint-KYCNEW — KYC Daily Dashboard

Dashboard รายวันสำหรับ SharePoint List **KYCData1** (site: `AC-Accounting`)
สร้างเป็น HTML แบบ static ไฟล์เดียว (Bootstrap 5 + Chart.js) เผยแพร่ผ่าน **GitHub Pages**
และอัปเดตข้อมูลอัตโนมัติทุกวันด้วย **GitHub Actions**

> Repo: <https://github.com/DohomePublic/SharePoint-KYCNEW>

---

## 🔄 วิธีทำงาน

1. GitHub Actions รันทุกวัน **07:00 น. (Asia/Bangkok)** — cron `0 0 * * *` (= 00:00 UTC)
2. ดึงข้อมูลจาก SharePoint List **KYCData1** ผ่าน **Microsoft Graph API** (client credentials flow)
3. สร้าง `index.html` ใหม่พร้อมข้อมูลล่าสุด (ฝัง JSON ลงในไฟล์โดยตรง — ไม่ต้องมี backend)
4. Commit + Push → **GitHub Pages** อัปเดตอัตโนมัติ

```
SharePoint (KYCData1)
      │  Microsoft Graph API  (Sites.Read.All)
      ▼
scripts/build_dashboard.py  ──►  templates/dashboard_template.html
      │                                │
      └──────────► index.html ◄────────┘
                       │
                       ▼
               GitHub Pages (public URL)
```

---

## ⚙️ การตั้งค่า GitHub Secrets

ไปที่ **Settings → Secrets and variables → Actions → New repository secret** แล้วเพิ่ม:

| Secret | Value |
|---|---|
| `AZURE_CLIENT_ID` | `012ac5e6-9487-4436-9e0e-246c19ab2a67` |
| `AZURE_TENANT_ID` | `7f8918d9-718a-495b-ac9a-17cba381c4a0` |
| `AZURE_CLIENT_SECRET` | *(ค่า Client Secret จาก Azure AD — ห้าม commit ลงโค้ดเด็ดขาด)* |

---

## 🔑 การตั้งค่า Azure AD (IT Admin ทำครั้งเดียว)

1. เปิด **Azure Portal**
2. ไปที่ **Azure Active Directory → App registrations**
3. เปิด App ID: `012ac5e6-9487-4436-9e0e-246c19ab2a67`
4. **Certificates & secrets → New client secret → Copy value** (คัดลอกทันที ค่าจะแสดงครั้งเดียว)
5. **API permissions → Add a permission → Microsoft Graph → Application permissions**
6. เพิ่ม **`Sites.Read.All`**
7. กด **Grant admin consent**

> หมายเหตุ: หากองค์กรใช้ *Sites.Selected* แทน ให้ผู้ดูแลกำหนดสิทธิ์ `read` เฉพาะไซต์
> `https://dohomegroup.sharepoint.com/sites/AC-Accounting` ให้กับ App นี้

---

## 📁 โครงสร้างไฟล์

```
sharepoint-web/
├── .github/
│   └── workflows/
│       └── update-dashboard.yml     ← GitHub Actions workflow (cron + manual)
├── scripts/
│   └── build_dashboard.py           ← Python script ดึงข้อมูล + สร้าง HTML
├── templates/
│   └── dashboard_template.html      ← Template UI (Bootstrap 5 + Chart.js)
├── index.html                       ← Dashboard (auto-generated) ← GitHub Pages เสิร์ฟไฟล์นี้
├── requirements.txt
├── .nojekyll
└── README.md
```

---

## 🖱️ รันด้วยตนเอง (Manual Run)

**บน GitHub:** ไปที่แท็บ **Actions → เลือก "Update KYC Dashboard" → กด Run workflow**

**บนเครื่องตัวเอง:**

```bash
pip install -r requirements.txt

export AZURE_CLIENT_ID="012ac5e6-9487-4436-9e0e-246c19ab2a67"
export AZURE_TENANT_ID="7f8918d9-718a-495b-ac9a-17cba381c4a0"
export AZURE_CLIENT_SECRET="********"          # อย่า hard-code ในไฟล์

python scripts/build_dashboard.py
# → เขียนทับ index.html แล้วเปิดดูในเบราว์เซอร์ได้เลย
```

---

## 🔧 Environment Variables

| ตัวแปร | ค่า default | คำอธิบาย |
|---|---|---|
| `AZURE_CLIENT_ID` | *(required)* | Application (client) ID |
| `AZURE_TENANT_ID` | *(required)* | Directory (tenant) ID |
| `AZURE_CLIENT_SECRET` | *(required)* | Client secret |
| `SP_HOSTNAME` | `dohomegroup.sharepoint.com` | SharePoint hostname |
| `SP_SITE_PATH` | `/sites/AC-Accounting` | path ของไซต์ |
| `SP_LIST_NAME` | `KYCData1` | ชื่อลิสต์ |
| `OUTPUT_FILE` | `index.html` | ไฟล์ผลลัพธ์ |
| `TEMPLATE_FILE` | `templates/dashboard_template.html` | ไฟล์ template |
| `TZ_OFFSET_HRS` | `7` | timezone offset สำหรับป้าย "Last updated" |

---

## 📊 ฟีเจอร์ของ Dashboard

- **KPI Cards** — Total Transaction, New Today, ย้อนหลัง 7/30 วัน, Pending, Closed, ต้องติดตาม, Success Rate, Avg Processing Age, วงเงินรวม
- **Charts (Chart.js)** — Bar รายสาขา, Doughnut ตามสถานะ, Line แนวโน้มรายวัน, Stacked Bar สาขา×สถานะ, Top 10 Owner, วงเงินตามประเภทคำขอ
- **Search & Filter** — keyword, สาขา, ผู้ดูแล, สถานะ, ช่วงวันที่
- **Branch / Owner Analytics** — จำนวน, สัดส่วน %, ranking, งานเปิด/ปิด/ค้าง >3 วัน + **Drill Down** (คลิกที่แถวหรือกราฟ)
- **Detail Table** — sort ได้ทุกคอลัมน์, pagination, Export **Excel** และ **CSV**, ลิงก์กลับไปยัง `DispForm.aspx` ของแต่ละรายการ
- **Auto Insight** — สาขา/ผู้ดูแลที่งานสูงสุด, เทียบวันก่อนหน้า, anomaly (คำขอซ้ำ, งานค้างเกิน SLA, ข้อมูลไม่ครบ), ข้อเสนอแนะเชิงธุรกิจ
- **Dark Mode** + Responsive 100% (Desktop / Tablet / Mobile)

---

## 🌐 การเผยแพร่ (GitHub Pages)

**Settings → Pages → Build and deployment → Source: GitHub Actions**
(workflow มี job `deploy` ที่ใช้ `actions/deploy-pages@v4` ให้แล้ว)

หากต้องการใช้โหมด *Deploy from a branch* ให้เลือก branch `main` / folder `/ (root)`
ไฟล์ `.nojekyll` มีอยู่แล้วเพื่อไม่ให้ Jekyll ประมวลผลไฟล์

---

## 🔒 ความปลอดภัย

- Client secret เก็บใน **GitHub Secrets** เท่านั้น ไม่มีการเขียนลงไฟล์หรือ log
- สิทธิ์ที่ขอเป็น **read-only** (`Sites.Read.All`)
- `index.html` เป็น public — **อย่า** ใส่ฟิลด์ที่เป็นข้อมูลส่วนบุคคล/ความลับลงใน `FIELD_MAP`
  ของ `scripts/build_dashboard.py` (ปัจจุบันดึงเฉพาะฟิลด์สรุปที่จำเป็นต่อการวิเคราะห์)
- ควรตั้งรอบหมุนเวียน (rotate) client secret ทุก 6–12 เดือน

---

## 🧯 Troubleshooting

| อาการ | สาเหตุ / วิธีแก้ |
|---|---|
| `token request failed (401)` | client secret หมดอายุ หรือค่าใน Secrets ผิด → สร้าง secret ใหม่ |
| `GET .../sites/... failed (403)` | ยังไม่ได้ **Grant admin consent** ให้ `Sites.Read.All` |
| `list 'KYCData1' not found` | ชื่อลิสต์ไม่ตรง — สคริปต์จะพิมพ์รายชื่อลิสต์ทั้งหมดออกมา ให้ตั้งค่า `SP_LIST_NAME` ใหม่ |
| ข้อมูลขึ้นแต่คอลัมน์ว่าง | internal name ของฟิลด์ต่างจากที่แม็ปไว้ → แก้ `FIELD_MAP` ใน `scripts/build_dashboard.py` |
| Pages ไม่อัปเดต | ตรวจแท็บ Actions ว่ามี run สำเร็จ และ Settings → Pages ตั้ง source เป็น GitHub Actions |
| `no rows returned` | สคริปต์จงใจไม่เขียนทับ `index.html` ด้วยข้อมูลว่าง — ตรวจสิทธิ์/ชื่อลิสต์ก่อน |
