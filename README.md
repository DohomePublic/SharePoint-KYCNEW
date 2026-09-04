# DOHOME | KYC Daily Dashboard (SharePoint ➜ GitHub Actions ➜ GitHub Pages)

Dashboard รายวันจาก SharePoint Online List `DemoApp` + `Admin_KycNew`
สร้างเป็น **static `index.html` ไฟล์เดียว** (HTML + CSS + JS) เผยแพร่ผ่าน GitHub Pages

## 🔄 วิธีทำงาน
1. **GitHub Actions รันทุกวัน 07:00 น. ICT** — `cron: "0 0 * * *"` (00:00 UTC = 07:00 ICT)
2. `scripts/fetch_sharepoint.py` ดึงข้อมูลผ่าน **Microsoft Graph API** (client-credentials, paging รองรับ > 5,000 records)
3. `scripts/build_dashboard.py` normalize + คำนวณ RBAC แล้วฝัง JSON ลง `templates/dashboard.html`
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

## 🔐 Security (RBAC by Email)
ตรวจสิทธิ์จาก List `Admin_KycNew` (คอลัมน์ `Title` = อีเมล) — เปิดหน้าเว็บด้วย `?email=you@dohome.co.th` หรือกรอกในหน้า Sign-in (จำไว้ใน localStorage)

| Role | เงื่อนไขที่ระบบแยกให้อัตโนมัติ | ขอบเขตข้อมูล |
|---|---|---|
| **Admin** | อยู่ใน `ADMIN_EMAILS` | ทุก record |
| **Branch Manager** | `GM-XX@`, `BI-OperationXX_GM@`, `BI-VOperationXX_GM@`, `Dohometogogm-XX@` | เฉพาะสาขา `XX` (จับคู่ `XX` ↔ `XXOO`) |
| **Owner** | อีเมลอื่นที่อยู่ใน list | เฉพาะงานที่ `OwnerEmail`/ชื่อ Owner ตรงกับตน |
| **Access Denied** | ไม่พบอีเมล หรือ `IsActive = No` | ไม่เห็นข้อมูล |

> ถ้าเพิ่มคอลัมน์ `Role`, `Branch`, `IsActive`, `OwnerEmail` ใน SharePoint เมื่อใด สคริปต์จะใช้ค่าจาก List ทันที (override กติกาอัตโนมัติ)
>
> ⚠️ GitHub Pages เป็น static hosting — RBAC ทำงานฝั่ง client จึงเป็นการ *แบ่งมุมมอง* ไม่ใช่การป้องกันระดับเซิร์ฟเวอร์ ถ้าข้อมูลเป็นความลับสูง ให้ใช้ **private repo + GitHub Pages แบบ private (Enterprise)** หรือ embed หน้านี้บน SharePoint Modern Page แล้วดึงข้อมูลด้วย REST API แบบ real-time แทน

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
python -m http.server 8080           # เปิด http://localhost:8080/index.html?email=you@dohome.co.th
```

## 📌 การจัดกลุ่มสถานะ
| Status (SharePoint) | Status Group |
|---|---|
| อนุมัติ-KYC, ผ่านการพิจารณาเบื้องต้น | Completed |
| รอดำเนินการ, รอการพิจารณาเบื้องต้น, Draft | Pending |
| รอผู้จัดการ D3 อนุมัติ | In Progress |
| ไม่ผ่านการพิจารณาเบื้องต้น | Issue |

SLA ค่าเริ่มต้น = 2 วัน (ปรับที่ env `SLA_DAYS` ใน workflow)
