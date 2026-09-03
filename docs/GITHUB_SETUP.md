# นำขึ้น GitHub — ทีละขั้นตอน

## 0) เตรียมเครื่อง
```bash
git --version          # ต้องมี git
gh --version           # (ไม่บังคับ) GitHub CLI ช่วยสร้าง repo + ตั้ง secret ได้เร็ว
```

---

## 1) แตกไฟล์และเริ่ม repo

```bash
unzip kyc-daily-dashboard.zip
cd kyc-daily-dashboard

git init -b main
git add .
git commit -m "feat: KYC Daily Dashboard + fix list resolver (KYCData1 -> KYC_DATA_NEW)"
```

---

## 2) สร้าง repo บน GitHub

### วิธี A — ใช้ GitHub CLI (แนะนำ)
```bash
gh auth login
gh repo create dohome-bi/kyc-daily-dashboard --private --source=. --remote=origin --push
```

### วิธี B — ผ่านหน้าเว็บ
1. ไปที่ https://github.com/new
2. Owner = องค์กรของคุณ · Repository name = `kyc-daily-dashboard`
3. เลือก **Private** ⚠️ (ในไฟล์มีข้อมูลลูกค้าและรายชื่ออีเมลพนักงาน)
4. **ไม่ต้อง** ติ๊ก Add README / .gitignore (มีอยู่ในชุดแล้ว)
5. Create repository แล้วรัน:

```bash
git remote add origin https://github.com/dohome-bi/kyc-daily-dashboard.git
git push -u origin main
```

---

## 3) ตั้งค่า Secrets (สำหรับ build สดจาก SharePoint)

### ใช้ GitHub CLI
```bash
gh secret set TENANT_ID     --body "<tenant-guid>"
gh secret set CLIENT_ID     --body "<app-client-id>"
gh secret set CLIENT_SECRET --body "<app-secret>"
```

### ผ่านหน้าเว็บ
`Settings` → `Secrets and variables` → `Actions` → `New repository secret`

| Name | Value |
|---|---|
| `TENANT_ID` | Directory (tenant) ID ของ Azure AD |
| `CLIENT_ID` | Application (client) ID |
| `CLIENT_SECRET` | Client secret value |

**สิทธิ์ที่ Azure AD App ต้องมี:** API permissions → Microsoft Graph → Application → **`Sites.Read.All`** → **Grant admin consent**

> ⚠️ ห้ามพิมพ์ค่า secret ลงในไฟล์ใด ๆ ใน repo — ใช้ GitHub Secrets เท่านั้น

---

## 4) รัน Workflow

```bash
gh workflow run "Build KYC Daily Dashboard"                       # build สด
gh workflow run "Build KYC Daily Dashboard" -f offline=true       # build จาก snapshot (ไม่ต้องใช้ secret)
gh run watch
gh run download --name kyc-daily-dashboard                        # ดาวน์โหลดไฟล์ HTML
```

หรือผ่านหน้าเว็บ: แท็บ **Actions** → เลือก workflow → **Run workflow**

workflow จะรันอัตโนมัติทุกวัน **08:00 น. เวลาไทย** (cron `0 1 * * *` UTC)

---

## 5) นำไฟล์ขึ้น SharePoint

ดาวน์โหลด artifact `kyc-daily-dashboard` → ได้ `KYC_Daily_Dashboard.html`
อัปโหลดไปที่ `AC-Accounting / Shared Documents / Dashboard/`
สร้าง Page → เพิ่ม Web Part **File viewer** → ชี้ไปที่ไฟล์ → Publish

รายละเอียดเพิ่มเติม: [DEPLOY_README.md](DEPLOY_README.md)

---

## 6) (ตัวเลือก) เปิด GitHub Pages
`Settings` → `Pages` → Source = **GitHub Actions**

> ถ้า repo เป็น Private และไม่ได้ใช้ GitHub Enterprise ให้ **ลบ job `deploy-pages`** ออกจาก workflow
> เพื่อไม่ให้ข้อมูลลูกค้าถูกเผยแพร่สู่สาธารณะ

---

## 7) เช็กลิสต์ก่อน push
- [ ] repo เป็น **Private**
- [ ] ไม่มีไฟล์ `.env` ใน `git status` (ถูก ignore แล้ว)
- [ ] `grep -ri "client_secret" --exclude-dir=.git .` ไม่พบค่าจริง
- [ ] `python scripts/build_dashboard.py --offline data/sample_data.json` รันผ่าน

---

## คำสั่งรวบยอด (copy-paste ได้เลย)

```bash
unzip kyc-daily-dashboard.zip && cd kyc-daily-dashboard
python -m pip install -r requirements.txt
python scripts/build_dashboard.py --offline data/sample_data.json   # verify
git init -b main && git add . && git commit -m "feat: KYC Daily Dashboard"
gh repo create dohome-bi/kyc-daily-dashboard --private --source=. --remote=origin --push
gh secret set TENANT_ID --body "<tenant>" && gh secret set CLIENT_ID --body "<client>" && gh secret set CLIENT_SECRET --body "<secret>"
gh workflow run "Build KYC Daily Dashboard"
```
