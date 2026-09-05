/* ==========================================================================
   sharepoint.js — ตัวเชื่อมต่อ SharePoint REST API (โหมด Live)
   --------------------------------------------------------------------------
   ใช้เมื่อต้องการดึงข้อมูล "สด" จาก SharePoint List DemoApp แทน snapshot
   เงื่อนไขการใช้งาน:
     • ต้อง host ไฟล์ชุดนี้ไว้ใน SharePoint เอง (เช่น /SiteAssets/kyc/index.html)
       หรือใน domain เดียวกัน เพราะ REST API ใช้ cookie-based auth และติด CORS
     • ถ้าเปิดจากไฟล์ในเครื่อง (file://) หรือ GitHub Pages จะดึงสดไม่ได้
       ระบบจะ fallback ไปใช้ snapshot ใน data.js อัตโนมัติ
   ========================================================================== */
window.SPConnector = (function () {
  'use strict';

  // ค่าตั้งต้น — แก้ไขได้ที่นี่ที่เดียว
  var CONFIG = {
    siteUrl: 'https://dohomegroup.sharepoint.com/sites/AC-Accounting',
    listTitle: 'DemoApp',
    pageSize: 2000            // ดึงครั้งละ 2000 แถว แล้ววนตาม __next (รองรับข้อมูลจำนวนมาก)
  };

  /**
   * ตรวจว่าอยู่ใน context ของ SharePoint หรือไม่
   * (ใช้ตัดสินใจว่าจะลองดึง Live หรือใช้ snapshot ทันที)
   */
  function isSharePointContext() {
    try {
      return location.hostname.indexOf('sharepoint.com') > -1;
    } catch (e) {
      return false;
    }
  }

  /**
   * ดึงรายการทั้งหมดจาก List ผ่าน REST API แบบ paging
   * @returns {Promise<Array<Object>>} อาร์เรย์ของ list item (raw)
   */
  async function fetchAll() {
    var url = CONFIG.siteUrl + "/_api/web/lists/getbytitle('" + CONFIG.listTitle +
              "')/items?$top=" + CONFIG.pageSize;
    var all = [];

    while (url) {
      var res = await fetch(url, {
        method: 'GET',
        credentials: 'include',                       // ส่ง cookie เพื่อยืนยันตัวตน
        headers: { 'Accept': 'application/json;odata=nometadata' }
      });
      if (!res.ok) throw new Error('SharePoint REST error ' + res.status);
      var json = await res.json();
      all = all.concat(json.value || []);
      url = json['odata.nextLink'] || json['@odata.nextLink'] || null;   // หน้าถัดไป
    }
    return all;
  }

  /**
   * แปลง field ภายในของ SharePoint ให้เป็นชื่อคอลัมน์เดียวกับ snapshot
   * SharePoint จะแทนที่อักขระพิเศษ เช่น ช่องว่าง -> _x0020_
   */
  function normalize(items) {
    return items.map(function (it) {
      var o = {};
      Object.keys(it).forEach(function (k) {
        var key = k.replace(/_x0020_/g, ' ').replace(/^OData_/, '');
        o[key] = it[k];
      });
      o._ID = it.Id || it.ID;
      // แปลงวงเงินเป็นตัวเลขสำหรับการคำนวณ
      o.limit_num = toNumber(o['limit']);
      o.limit_other_num = toNumber(o['limit_other']);
      return o;
    });
  }

  function toNumber(v) {
    if (v === null || v === undefined || v === '') return null;
    var n = parseFloat(String(v).replace(/[^\d.\-]/g, ''));
    return isNaN(n) ? null : n;
  }

  /**
   * โหลดข้อมูล: พยายามดึงสดก่อน ถ้าไม่ได้ให้ใช้ snapshot
   * @returns {Promise<{items:Array, mode:'live'|'snapshot', error?:string}>}
   */
  async function load() {
    if (isSharePointContext()) {
      try {
        var raw = await fetchAll();
        if (raw && raw.length) {
          return { items: normalize(raw), mode: 'live' };
        }
      } catch (e) {
        console.warn('[SPConnector] ดึงข้อมูลสดไม่สำเร็จ ใช้ snapshot แทน:', e.message);
        return { items: window.DEMOAPP_DATA || [], mode: 'snapshot', error: e.message };
      }
    }
    return { items: window.DEMOAPP_DATA || [], mode: 'snapshot' };
  }

  return { CONFIG: CONFIG, load: load, fetchAll: fetchAll, normalize: normalize, isSharePointContext: isSharePointContext };
})();
