# KYC Daily Dashboard — คู่มือติดตั้ง (พร้อมใช้งาน)

## ไฟล์ในชุดนี้
| ไฟล์ | ใช้ทำอะไร |
|---|---|
| `KYC_Daily_Dashboard.html` | **ใช้ได้ทันที** — เปิดดู/อัปโหลดขึ้น SharePoint ได้เลย (ฝังข้อมูล 23 รายการ + สิทธิ์ 65 อีเมล) |
| `dashboard_template.html` | เทมเพลตสำหรับ CI (มี placeholder `__DATA__`, `__ALLOWED__`) |
| `build_dashboard.py` | สคริปต์ build ที่แก้บั๊ก `list 'KYCData1' not found` แล้ว |
| `sp_list_resolver.py` | โมดูล resolve ชื่อ list (ใช้เดี่ยว ๆ ได้) |

---

## วิธีที่ 1 — ใช้ทันที (ไม่ต้อง build, 3 นาที)

1. อัปโหลด `KYC_Daily_Dashboard.html` ไปที่ Document Library ของไซต์
   `https://dohomegroup.sharepoint.com/sites/AC-Accounting/Shared Documents/Dashboard/`
2. สร้าง Page ใหม่ → เพิ่ม Web Part **“File viewer”** (หรือ **Embed**) → ชี้ไปที่ไฟล์
3. Publish

> ต้องอัปโหลดไว้ในไซต์เดียวกันเท่านั้น เพราะสคริปต์เรียก `_api/web/currentUser` เพื่อตรวจสิทธิ์อัตโนมัติ
> (same-origin) — ถ้าเปิดจากที่อื่นจะตกมาที่หน้ากรอกอีเมลแทน

**พฤติกรรมเมื่อเปิด**
- ตรวจอีเมลผู้ใช้อัตโนมัติ → อยู่ในกลุ่ม `Admin_KycNew` = เข้าได้
- ไม่อยู่ในกลุ่ม = แสดง “ไม่มีสิทธิ์เข้าถึงรายงานนี้” และ **ไม่เรนเดอร์ Dashboard เลย**
- โหลดข้อมูลสดจาก list ตามลำดับ `KYC_DATA_NEW` → `KYCData1` → `DemoApp`
  (badge บน navbar จะขึ้น 🟢 `Live: <ชื่อ list>`) — ถ้าต่อไม่ได้จะใช้ snapshot ในไฟล์ (badge เทา) โดยไม่ error
- รายชื่อสิทธิ์ก็ sync สดจาก `Admin_KycNew` → **เพิ่ม/ลบคนใน List แล้วมีผลทันที ไม่ต้อง build ใหม่**

**ปรับแต่งเร็ว** (แก้ในไฟล์ HTML บรรทัดต้น ๆ ของ `<script>`)
```js
const SP_LIST_DATA_CANDIDATES  = ["KYC_DATA_NEW","KYCData1","DemoApp"];
const SP_LIST_GROUP_CANDIDATES = ["Admin_KycNew"];
const LIVE_MODE = true;   // false = ใช้ snapshot อย่างเดียว
```

---

## วิธีที่ 2 — Build อัตโนมัติผ่าน GitHub Actions

```
repo/
├─ scripts/build_dashboard.py          <- วางไฟล์นี้
├─ templates/dashboard_template.html   <- วาง dashboard_template.html
└─ .github/workflows/dashboard.yml
```

`.github/workflows/dashboard.yml`
```yaml
name: Build KYC Dashboard
on:
  schedule: [{ cron: "0 1 * * *" }]     # 08:00 น. ไทย ทุกวัน
  workflow_dispatch:
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install requests
      - run: python scripts/build_dashboard.py
        env:
          TENANT_ID:     ${{ secrets.TENANT_ID }}
          CLIENT_ID:     ${{ secrets.CLIENT_ID }}
          CLIENT_SECRET: ${{ secrets.CLIENT_SECRET }}
          SP_HOST:       dohomegroup.sharepoint.com
          SP_SITE_PATH:  /sites/AC-Accounting
          SP_LIST_DATA:  KYC_DATA_NEW      # << เดิมตั้งเป็น KYCData1 จึงพัง
          SP_LIST_GROUP: Admin_KycNew
          OUT_FILE:      dist/KYC_Daily_Dashboard.html
      - uses: actions/upload-artifact@v4
        with: { name: dashboard, path: dist/KYC_Daily_Dashboard.html }
```

สิทธิ์ Azure AD App ที่ต้องมี: **Sites.Read.All** (Application) + Grant admin consent

**Build จาก snapshot โดยไม่ต่อ SharePoint**
```bash
python scripts/build_dashboard.py --offline data.json   # {"records":[...], "allowed":[...]}
```

---

## สิ่งที่แก้จากเวอร์ชันที่ error
| เดิม | ใหม่ |
|---|---|
| hard-code `KYCData1` (ไม่มีบนไซต์) | resolver: exact → normalize (`_ - .` / ตัวพิมพ์) → ใกล้เคียง → suggestion |
| log ERROR แล้วรันต่อจนพังท้าย | **fail-fast** `sys.exit(1)` พร้อมรายชื่อ list ใกล้เคียง |
| เปลี่ยนชื่อ list ต้องแก้โค้ด | ตั้งผ่าน env `SP_LIST_DATA` / `SP_LIST_GROUP` |
| ข้อมูลนิ่งตอน build | HTML sync สดจาก SharePoint + fallback snapshot |
| คอลัมน์ต่างชื่อระหว่าง list ทำให้ค่าว่าง | mapping แบบ alias (`Customer Name` / `Customer_Name` / `Registered_Name` ...) |

---

## ผลทดสอบ (รันจริงแล้ว)
- Resolver: `KYCData1` → `KYC_DATA_NEW` ✔ · `admin-kycnew` → `Admin_KycNew` ✔ · ชื่อมั่ว → exit 1 พร้อมคำแนะนำ ✔
- Build offline: `dist/KYC_Daily_Dashboard.html` 64,322 bytes · records=23 · viewers=65 ✔
- ไม่มี credential → exit 1 พร้อมข้อความชัดเจน (ไม่รันต่อ) ✔
- JS syntax OK · Access gate: อีเมลนอกกลุ่ม/ค่าว่าง = ปฏิเสธ, `gm-cm@` และ `PHONGSAPAN.MAR@` = ผ่าน ✔
- Render ครบ: KPI 8, สาขา 10, ผู้ดูแล 18, Insight 7, ตาราง+pagination, drill down ✔
- Live sync ล้มเหลว (offline) → fallback snapshot ไม่ crash ✔
