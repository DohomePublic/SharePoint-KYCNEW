# DOHOME | KYC Daily Dashboard (SharePoint ➜ GitHub Actions ➜ GitHub Pages)

Dashboard รายวันจาก SharePoint Online List `DemoApp` + `Admin_KycNew`
สร้างเป็น **static `index.html` ไฟล์เดียว** (HTML + CSS + JS) เผยแพร่ผ่าน GitHub Pages

## 🔄 วิธีทำงาน
1. **GitHub Actions รันทุกวัน 07:00 น. ICT** — `cron: "0 0 * * *"` (00:00 UTC = 07:00 ICT)
2. `scripts/fetch_sharepoint.py` ดึงข้อมูลผ่าน **Microsoft Graph API** (client-credentials, paging รองรับ > 5,000 records)
3. `scripts/build_dashboard.py` normalize ข้อมูล แล้วฝัง JSON ลง `templates/dashboard.html`
4. เขียน `index.html` ใหม่ → **Commit + Push** → **GitHub Pages อัปเดตอัตโนมัติ**

```
.github/workflows/daily-dashboard.yml   ← ตารางเวลา + ขั้นตอน CI/CD
scripts/fetch_sharepoint.py             ← Graph API extractor
scripts/build_dashboard.py              ← transformer + HTML generator
templates/dashboard.html                ← template dashboard (มี placeholder)
data/dataset.json                       ← dataset ที่ normalize แล้ว (ต่อยอด Power BI/Power Apps)
index.html                              ← ผลลัพธ์ที่ GitHub Pages เสิร์ฟ
```

## ⚙️ ตั้งค่าครั้งเดียว
| ที่ตั้ง | ชื่อ | ค่า |
|---|---|---|
| Secrets | `TENANT_ID` | Azure AD Tenant ID |
| Secrets | `CLIENT_ID` | App Registration (Application) ID |
| Secrets | `CLIENT_SECRET` | Client Secret |
| Variables | `ADMIN_EMAILS` | อีเมล Admin คั่นด้วย `,` (ไม่ตั้งก็ใช้ค่าเริ่มต้นในสคริปต์) |

App Registration ต้องได้ **Application permission** `Sites.Selected` (แนะนำ) หรือ `Sites.Read.All` + admin consent
และเปิด Settings → Pages → Source = **GitHub Actions**

## 🌐 โหมดการเข้าถึง : Public (ไม่มีการล็อกอิน)
เปิดลิงก์ปุ๊บเห็นข้อมูลทันที ไม่ต้องกรอกอีเมล ไม่ต้องใส่ `?email=` — ทุกคนเห็นข้อมูลชุดเดียวกันครบทุก record

- ไม่มีหน้า Sign-in / Access Denied อีกต่อไป
- ข้อมูลจาก `Admin_KycNew` ยังถูกดึงและฝังไว้ในตัวแปร `USERS` (เผื่อใช้ต่อยอด) แต่ **ไม่ถูกใช้กรองข้อมูล**
- ถ้าอยากเปิด RBAC กลับมาในอนาคต แก้ที่ฟังก์ชันเดียวคือ `getScopedData()` ใน `templates/dashboard.html`

> ⚠️ เมื่อเป็น public repo + GitHub Pages ข้อมูลใน `index.html` จะเปิดเผยต่อสาธารณะ ถ้าข้อมูลเป็นความลับ ให้ใช้ private repo + Pages แบบ Enterprise หรือ embed บน SharePoint Modern Page แทน

## 🧩 ฟีเจอร์
1. **Executive Summary** — Total / New Today / 7 วัน / 30 วัน / Pending / In Progress / Completed / Issue
2. **Daily KPI** — Total Transaction, Closed Today, Pending, Success Rate, Avg Processing Time, SLA Achievement %, Aging Average, Total Limit
3. **Search & Filter** — keyword, branch/owner/status (multi-select), date range, clear
4. **Branch Analytics** — Top 10, success rate, % share, drill-down modal
5. **Owner Analytics** — Open / Closed / Pending / SLA Breach / Top 10
6. **Charts (Chart.js)** — Bar สาขา, Doughnut สถานะ, Line daily trend, Stacked branch×status, Top 10 owner, SLA performance, Aging analysis
7. **Detail Table** — search, sort ทุกคอลัมน์, pagination, sticky header, Export Excel/CSV (UTF-8 BOM รองรับภาษาไทย)
8. **Auto Insight** — สาขางานสูงสุด, ผู้ดูแลงานมากสุด, เทรนด์เทียบเมื่อวาน, Anomaly (Z-score > 2 + งานค้างนาน), Business Recommendation

UI: Bootstrap 5, Font Awesome 6, DataTables, Corporate Blue `#005BAC`, Responsive, Light/Dark toggle, Loading screen, Error handling

## 🖥️ ทดสอบบนเครื่อง
```bash
pip install requests
python scripts/build_dashboard.py    # ไม่มี raw_*.json จะใช้ data/sample_*.json
python -m http.server 8080           # เปิด http://localhost:8080/index.html  (debug: เติม ?debug=1)
```

## 📌 การจัดกลุ่มสถานะ
| Status (SharePoint) | Status Group |
|---|---|
| อนุมัติ-KYC, ผ่านการพิจารณาเบื้องต้น | Completed |
| รอดำเนินการ, รอการพิจารณาเบื้องต้น, Draft | Pending |
| รอผู้จัดการ D3 อนุมัติ | In Progress |
| ไม่ผ่านการพิจารณาเบื้องต้น | Issue |

SLA ค่าเริ่มต้น = 2 วัน (ปรับที่ env `SLA_DAYS` ใน workflow)
