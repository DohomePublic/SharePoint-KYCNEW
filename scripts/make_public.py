#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=======================================================================
 make_public.py  —  บังคับให้ index.html เป็นโหมด PUBLIC (ไม่มีล็อกอิน)
-----------------------------------------------------------------------
 ทำไมต้องมีไฟล์นี้?
   ถ้า templates/dashboard.html ใน repo ยังเป็นเวอร์ชันเก่า (มีหน้า
   Sign-in / Access Denied) build_dashboard.py ก็จะสร้าง index.html
   ที่มีหน้าล็อกอินออกมาด้วย  ทำให้ deploy ถูกบล็อก

 วิธีทำงาน (Self-healing / ไม่พึ่งพาเวอร์ชันของ template)
   1) ตรวจว่า index.html มีร่องรอยระบบสิทธิ์หรือไม่
   2) ถ้ามี -> ต่อท้ายไฟล์ด้วย "PUBLIC MODE OVERRIDE" (JavaScript สั้น ๆ)
      ที่ override ฟังก์ชันสิทธิ์ทั้งหมดให้ผ่านเสมอ + ซ่อนหน้าล็อกอิน
      + เรียก startApp() ให้แสดงข้อมูลทันที
   3) ใส่ meta กันแคช และป้ายเวอร์ชัน PUBLIC-NO-AUTH
   4) เขียนกลับลง index.html

 ปลอดภัยกับ template ใหม่ด้วย : ถ้าไม่พบร่องรอยสิทธิ์ จะข้ามขั้นตอน
 override และแค่เติม meta กันแคชให้ครบเท่านั้น (idempotent รันซ้ำได้)
=======================================================================
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# ปกติทำงานกับ index.html ที่ root ของ repo
# แต่รับ path จาก argument ได้ด้วย (สะดวกตอนทดสอบ)
TARGET = (sys.argv[1] if len(sys.argv) > 1
          else os.path.join(ROOT, "index.html"))

# ร่องรอยที่บ่งบอกว่ายังมีระบบล็อกอิน/สิทธิ์อยู่ในไฟล์
AUTH_MARKERS = [
    'id="gate"',
    "gateEmail",
    "validateUser",
    "applyRbac",
    "showDenied",
    "resolveEmail",
]

MARK_OVERRIDE = "PUBLIC-MODE-OVERRIDE-V1"
MARK_NOAUTH = "PUBLIC-NO-AUTH"

# ---------------------------------------------------------------------
# สคริปต์ override : ทำงานหลังจากโค้ดเดิมทั้งหมดถูกโหลดแล้ว
# ใช้ได้กับ template ทุกเวอร์ชัน เพราะไป override ฟังก์ชันแทนการลบโค้ด
# ---------------------------------------------------------------------
OVERRIDE_JS = """
<!-- ================================================================
     %s
     ปลดระบบสิทธิ์ทั้งหมด : ใครเปิดลิงก์ก็เห็นข้อมูลครบทุกรายการ
     (สคริปต์นี้ถูกเติมอัตโนมัติโดย scripts/make_public.py)
     ================================================================ -->
<script>
(function(){
  "use strict";

  /* ---------- 1) override ฟังก์ชันตรวจสิทธิ์ให้ "ผ่านเสมอ" ---------- */
  var PUBLIC_USER = {
    email: "public@dohome.co.th",
    role: "Admin",          /* Admin = เห็นทุก record */
    branches: [],
    isActive: "Yes"
  };

  /* ดึงตัวแปร DATA ให้ได้ทุกกรณี
     สำคัญ : ถ้าไฟล์ประกาศด้วย "const DATA = ..." ตัวแปรจะ **ไม่** ผูกกับ window
     จึงต้องอ่านผ่าน lexical scope ด้วย typeof ก่อน แล้วค่อย fallback ไป window */
  function getData(){
    try { if (typeof DATA !== "undefined" && DATA) return DATA; } catch(e){}
    try { if (window.DATA) return window.DATA; } catch(e){}
    return [];
  }

  try { window.resolveEmail = function(){ return PUBLIC_USER.email; }; } catch(e){}
  try { window.validateUser = function(){ return { ok:true, user: PUBLIC_USER }; }; } catch(e){}
  try { window.applyRbac    = function(){ return getData().slice(); }; } catch(e){}
  try { window.getScopedData= function(){ return getData().slice(); }; } catch(e){}
  try { window.showDenied   = function(){ /* ไม่ทำอะไร — ไม่มี Access Denied แล้ว */ }; } catch(e){}
  try { window.signOut      = function(){ location.reload(); }; } catch(e){}

  /* ---------- 2) ซ่อนหน้าล็อกอิน + ล้างค่าที่ค้างไว้ ---------- */
  function unlock(){
    try { localStorage.removeItem("kyc_email"); } catch(e){}

    var gate = document.getElementById("gate");
    if (gate) { gate.style.display = "none"; gate.remove && gate.remove(); }

    /* ซ่อนปุ่ม/ป้ายที่เกี่ยวกับผู้ใช้ในเวอร์ชันเก่า */
    ["hdrRole","hdrUser"].forEach(function(id){
      var el = document.getElementById(id);
      if (el) el.style.display = "none";
    });

    /* ป้าย Public View บนหัวเว็บ (ถ้ายังไม่มี) */
    var bar = document.querySelector(".navbar .d-flex");
    if (bar && !document.getElementById("pubBadge")) {
      var b = document.createElement("span");
      b.id = "pubBadge";
      b.className = "badge bg-light text-dark";
      b.innerHTML = '<i class="fa-solid fa-globe me-1"></i>Public View · ' +
                    getData().length.toLocaleString() + ' รายการ';
      bar.insertBefore(b, bar.firstChild);
    }
  }

  /* ---------- 3) บังคับเปิดหน้า Dashboard ---------- */
  function showApp(){
    unlock();
    var app = document.getElementById("app");
    var ld  = document.getElementById("loader");

    /* ถ้า app ยังไม่ถูก render ให้เรียก startApp เอง */
    if (app && app.style.display !== "block") {
      try {
        if (typeof startApp === "function") {
          /* รองรับทั้งแบบรับ user (เวอร์ชันเก่า) และไม่รับ (เวอร์ชันใหม่) */
          startApp.length > 0 ? startApp(PUBLIC_USER) : startApp();
        }
      } catch(err) {
        console.error("[public-mode] startApp error:", err);
      }
      unlock();
      if (app) app.style.display = "block";
      if (ld)  ld.style.display  = "none";
    }
  }

  /* เรียกทันทีถ้า DOM พร้อมแล้ว, ไม่งั้นรอ DOMContentLoaded */
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function(){ setTimeout(showApp, 0); });
  } else {
    setTimeout(showApp, 0);
  }

  /* กันเหนียว : ตรวจซ้ำอีก 2 รอบ เผื่อโค้ดเดิมไปซ่อน app ทีหลัง */
  setTimeout(showApp, 1200);
  setTimeout(showApp, 4000);

  console.log("[public-mode] เปิดสาธารณะ : ไม่มีการตรวจสอบสิทธิ์");
})();
</script>
""" % MARK_OVERRIDE

NO_CACHE_META = (
    '<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">\n'
    '<meta http-equiv="Pragma" content="no-cache">\n'
    '<meta http-equiv="Expires" content="0">\n'
)


def find_auth_markers(html: str):
    """คืน list ของ marker ที่ยังพบในไฟล์"""
    return [m for m in AUTH_MARKERS if m in html]


def ensure_no_cache(html: str) -> str:
    """เติม meta กันแคชถ้ายังไม่มี"""
    if 'http-equiv="Cache-Control"' in html:
        return html
    return re.sub(r"(<meta\s+charset=[^>]*>)", r"\1\n" + NO_CACHE_META, html, count=1)


def ensure_stamp(html: str) -> str:
    """ใส่ป้ายบอกโหมดไว้ในไฟล์ เพื่อให้ตรวจเวอร์ชันจากหน้าเว็บได้"""
    if MARK_NOAUTH in html:
        return html
    return html.replace(
        "<!DOCTYPE html>",
        "<!DOCTYPE html>\n<!-- Access mode : %s (patched by make_public.py) -->" % MARK_NOAUTH,
        1,
    )


def inject_override(html: str) -> str:
    """ต่อท้าย override script ก่อนปิด </body>"""
    if MARK_OVERRIDE in html:
        return html
    if "</body>" in html:
        return html.replace("</body>", OVERRIDE_JS + "\n</body>", 1)
    return html + OVERRIDE_JS


def main() -> int:
    if not os.path.exists(TARGET):
        print("ERROR: ไม่พบ %s (ต้องรัน build_dashboard.py ก่อน)" % TARGET)
        return 1

    html = open(TARGET, encoding="utf-8").read()
    before = os.path.getsize(TARGET)

    markers = find_auth_markers(html)
    if markers:
        print("! พบร่องรอยระบบล็อกอินใน index.html : %s" % ", ".join(markers))
        print("  -> เติม PUBLIC MODE OVERRIDE เพื่อปลดสิทธิ์อัตโนมัติ")
        html = inject_override(html)
    else:
        print("OK: index.html เป็นโหมด PUBLIC อยู่แล้ว (ไม่พบโค้ดล็อกอิน)")

    html = ensure_no_cache(html)
    html = ensure_stamp(html)

    open(TARGET, "w", encoding="utf-8").write(html)
    print("OK: index.html พร้อมเผยแพร่ (%s -> %s bytes)" % (before, os.path.getsize(TARGET)))
    print("    โหมด = PUBLIC (ไม่มีการตรวจสอบสิทธิ์) | override = %s"
          % ("มี" if MARK_OVERRIDE in html else "ไม่ต้องใช้"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
