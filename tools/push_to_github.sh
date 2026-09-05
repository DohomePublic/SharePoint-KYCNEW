#!/usr/bin/env bash
# ============================================================================
# push_to_github.sh — อัปโหลดโปรเจกต์นี้ขึ้น GitHub repo แล้วเปิด GitHub Pages
#
# วิธีใช้:
#   1) ติดตั้ง git และ (ถ้ามี) GitHub CLI: https://cli.github.com
#   2) ล็อกอิน:  gh auth login
#   3) รัน:      bash tools/push_to_github.sh
#
# หมายเหตุความปลอดภัย: repo ปลายทางเป็น public organization
# ตรวจสอบข้อมูลใน assets/js/data.js ก่อนรันสคริปต์นี้ทุกครั้ง
# ============================================================================
set -euo pipefail

REPO="DohomePublic/SharePoint-KYCNEW"
REMOTE="https://github.com/${REPO}.git"
BRANCH="main"

cd "$(dirname "$0")/.."

echo "==> ตรวจสอบเครื่องมือ"
command -v git >/dev/null || { echo "ไม่พบคำสั่ง git — กรุณาติดตั้งก่อน"; exit 1; }

echo "==> เตรียม git repository"
if [ ! -d .git ]; then
  git init -b "$BRANCH"
fi

git add -A
git commit -m "feat: KYC & Credit Limit dashboard from SharePoint List DemoApp" || echo "ไม่มีการเปลี่ยนแปลงให้ commit"

echo "==> ตั้งค่า remote"
if git remote get-url origin >/dev/null 2>&1; then
  git remote set-url origin "$REMOTE"
else
  git remote add origin "$REMOTE"
fi

echo "==> push ขึ้น GitHub"
git push -u origin "$BRANCH"

echo "==> เปิดใช้งาน GitHub Pages (ต้องมี GitHub CLI)"
if command -v gh >/dev/null 2>&1; then
  gh api -X POST "repos/${REPO}/pages" -f build_type=workflow 2>/dev/null \
    || echo "GitHub Pages อาจถูกเปิดใช้งานอยู่แล้ว หรือให้ตั้งค่าเองที่ Settings › Pages"
else
  echo "ไม่พบ gh — ให้ตั้งค่าเองที่ Settings › Pages › Source = GitHub Actions"
fi

echo
echo "เสร็จสิ้น! URL ที่คาดหมาย: https://dohomepublic.github.io/SharePoint-KYCNEW/"
