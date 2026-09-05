/* ==========================================================================
   app.js — ตรรกะหลักของ KYC Dashboard (SPA)
   --------------------------------------------------------------------------
   สารบัญ
     0) State & Utilities        — ตัวแปรกลาง, ฟังก์ชันช่วยเหลือ
     1) Bootstrap                — โหลดข้อมูล + ผูก event
     2) Filtering / Sorting      — ค้นหา, กรอง, เรียงลำดับ
     3) KPI Cards
     4) Charts (Chart.js)        — Bar / Pie / Line / Stacked
     5) Data Table (DataTables)  — ตาราง Interactive + Drill Down
     6) Insight & Anomaly        — วิเคราะห์เชิงธุรกิจอัตโนมัติ
     7) Data Dictionary
     8) Export                   — Excel / CSV / PDF / PNG
     9) Navigation & UI          — เมนู, modal, toast, responsive
   ========================================================================== */
(function () {
  'use strict';

  /* =========================================================================
     0) STATE & UTILITIES
     ========================================================================= */

  var STATE = {
    all: [],        // ข้อมูลดิบทั้งหมด
    view: [],       // ข้อมูลหลังผ่านตัวกรอง (ใช้ render ทุกส่วน)
    charts: {},     // เก็บ instance ของ Chart.js เพื่อ destroy ก่อน re-render
    dt: null,       // instance ของ DataTables
    grain: 'day',   // ความละเอียดของกราฟแนวโน้ม: day | month | year
    mode: 'snapshot'
  };

  // จานสีตาม Microsoft Fluent
  var PALETTE = ['#0F6CBD', '#107C10', '#F7630C', '#C50F1F', '#8764B8', '#038387',
                 '#CA5010', '#498205', '#005B70', '#986F0B', '#8E562E', '#4F6BED'];

  // แผนที่สีของสถานะ เพื่อให้สีคงที่ทุกกราฟ
  var STATUS_COLOR = {
    'อนุมัติ-KYC': '#107C10',
    'ผ่านการพิจารณาเบื้องต้น': '#0F6CBD',
    'รอการพิจารณาเบื้องต้น': '#F7630C',
    'รอดำเนินการ': '#986F0B',
    'รอผู้จัดการ D3 อนุมัติ': '#8764B8',
    'ไม่ผ่านการพิจารณาเบื้องต้น': '#C50F1F',
    'Draft': '#8A8886'
  };

  var $ = function (id) { return document.getElementById(id); };

  /** จัดรูปแบบตัวเลขแบบมี comma */
  function fmtNum(n) {
    if (n === null || n === undefined || isNaN(n)) return '-';
    return Number(n).toLocaleString('th-TH', { maximumFractionDigits: 0 });
  }

  /** ย่อจำนวนเงินให้อ่านง่าย เช่น 45,000,000 -> 45.0 ล้าน */
  function fmtShortTHB(n) {
    if (!n && n !== 0) return '-';
    if (n >= 1e9) return (n / 1e9).toFixed(2) + ' พันล้าน';
    if (n >= 1e6) return (n / 1e6).toFixed(1) + ' ล้าน';
    if (n >= 1e3) return (n / 1e3).toFixed(0) + 'K';
    return fmtNum(n);
  }

  /** แปลงค่าใด ๆ ให้เป็น Date (รองรับ ISO ของ SharePoint) */
  function toDate(v) {
    if (!v) return null;
    var d = new Date(v);
    return isNaN(d.getTime()) ? null : d;
  }

  /** คืนคีย์ช่วงเวลาตาม grain: 2026-09-05 / 2026-09 / 2026 */
  function periodKey(d, grain) {
    if (!d) return '(ไม่ระบุ)';
    var y = d.getUTCFullYear();
    var m = String(d.getUTCMonth() + 1).padStart(2, '0');
    var day = String(d.getUTCDate()).padStart(2, '0');
    if (grain === 'year') return String(y);
    if (grain === 'month') return y + '-' + m;
    return y + '-' + m + '-' + day;
  }

  /** วันที่แบบสั้นสำหรับแสดงในตาราง */
  function fmtDate(v) {
    var d = toDate(v);
    if (!d) return '-';
    return d.toISOString().slice(0, 10);
  }

  /** นับความถี่ของค่าในฟิลด์หนึ่ง -> [{key, count, sum}] เรียงมาก->น้อย */
  function groupBy(rows, field, sumField) {
    var map = {};
    rows.forEach(function (r) {
      var k = (r[field] === null || r[field] === undefined || String(r[field]).trim() === '')
              ? '(ไม่ระบุ)' : String(r[field]).trim();
      if (!map[k]) map[k] = { key: k, count: 0, sum: 0 };
      map[k].count++;
      if (sumField) map[k].sum += (Number(r[sumField]) || 0);
    });
    return Object.keys(map).map(function (k) { return map[k]; })
                 .sort(function (a, b) { return b.count - a.count; });
  }

  /** escape HTML ป้องกัน XSS เวลา render ค่าเข้า DOM */
  function esc(s) {
    if (s === null || s === undefined) return '';
    return String(s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  /** เลือก class ของ pill ตามข้อความสถานะ */
  function statusPill(s) {
    var v = String(s || '').trim();
    var cls = 'pill-draft';
    if (v.indexOf('อนุมัติ') === 0) cls = 'pill-approved';
    else if (v.indexOf('ไม่ผ่าน') > -1) cls = 'pill-rejected';
    else if (v.indexOf('ผ่านการ') === 0) cls = 'pill-passed';
    else if (v.indexOf('รอ') === 0) cls = 'pill-pending';
    return '<span class="pill ' + cls + '">' + esc(v || '-') + '</span>';
  }

  function toast(msg) {
    var t = $('toast');
    t.textContent = msg;
    t.classList.remove('hidden');
    clearTimeout(t._timer);
    t._timer = setTimeout(function () { t.classList.add('hidden'); }, 2600);
  }

  /* =========================================================================
     1) BOOTSTRAP — โหลดข้อมูลแล้วเริ่มระบบ
     ========================================================================= */

  async function boot() {
    var meta = window.DEMOAPP_META || {};
    $('lnkList').href = meta.listUrl || '#';

    // SPConnector จะพยายามดึงสดก่อน แล้ว fallback เป็น snapshot
    var res = await window.SPConnector.load();
    STATE.all = res.items || [];
    STATE.mode = res.mode;

    $('srcBadge').textContent = (res.mode === 'live') ? 'Live SharePoint' : 'Snapshot ' + (meta.snapshotDate || '');
    $('footMeta').textContent = 'ข้อมูลจาก SharePoint List "' + (meta.listTitle || 'DemoApp') +
                                '" • ' + STATE.all.length + ' รายการ • โหมด: ' + res.mode;

    buildFilterOptions();   // เติมตัวเลือกใน dropdown จากข้อมูลจริง
    bindEvents();
    applyFilters();         // render ครั้งแรก
  }

  /** สร้าง <option> ของ dropdown ทั้งหมดจากค่าที่พบจริงในข้อมูล */
  function buildFilterOptions() {
    var map = [
      ['fStatus', 'Status'],
      ['fType', 'Type_Request'],
      ['fTeam', 'type_teams'],
      ['fProv', 'province']
    ];
    map.forEach(function (pair) {
      var sel = $(pair[0]);
      groupBy(STATE.all, pair[1]).forEach(function (g) {
        var o = document.createElement('option');
        o.value = g.key;
        o.textContent = g.key + ' (' + g.count + ')';
        sel.appendChild(o);
      });
    });
  }

  function bindEvents() {
    // ตัวกรอง: ค้นหาแบบพิมพ์แล้วกรองทันที (debounce 250ms)
    var timer;
    $('q').addEventListener('input', function () {
      clearTimeout(timer); timer = setTimeout(applyFilters, 250);
    });
    ['fStatus', 'fType', 'fTeam', 'fProv', 'dFrom', 'dTo', 'sortBy', 'sortDir'].forEach(function (id) {
      $(id).addEventListener('change', applyFilters);
    });
    $('btnApply').addEventListener('click', applyFilters);
    $('btnReset').addEventListener('click', resetFilters);
    $('btnRefresh').addEventListener('click', function () { location.reload(); });

    // เมนูซ้าย
    document.querySelectorAll('.nav-item').forEach(function (a) {
      a.addEventListener('click', function (e) {
        e.preventDefault();
        switchView(a.dataset.view);
      });
    });
    $('btnNav').addEventListener('click', function () { $('sidebar').classList.toggle('open'); });

    // ปุ่มเลือกความละเอียดของกราฟแนวโน้ม
    document.querySelectorAll('#grainSeg .seg-btn').forEach(function (b) {
      b.addEventListener('click', function () {
        document.querySelectorAll('#grainSeg .seg-btn').forEach(function (x) { x.classList.remove('active'); });
        b.classList.add('active');
        STATE.grain = b.dataset.grain;
        renderTrendCharts();
      });
    });

    // Export
    $('expExcel').addEventListener('click', exportExcel);
    $('expCsv').addEventListener('click', exportCsv);
    $('expPdf').addEventListener('click', exportPdf);
    $('expPng').addEventListener('click', exportPng);

    // Modal
    $('modalClose').addEventListener('click', closeModal);
    $('modal').addEventListener('click', function (e) { if (e.target.id === 'modal') closeModal(); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') closeModal(); });
  }

  /* =========================================================================
     2) FILTERING / SORTING
     ========================================================================= */

  function applyFilters() {
    var q = $('q').value.trim().toLowerCase();
    var fStatus = $('fStatus').value, fType = $('fType').value;
    var fTeam = $('fTeam').value, fProv = $('fProv').value;
    var dFrom = $('dFrom').value ? new Date($('dFrom').value + 'T00:00:00Z') : null;
    var dTo = $('dTo').value ? new Date($('dTo').value + 'T23:59:59Z') : null;

    STATE.view = STATE.all.filter(function (r) {
      // 2.1 ค้นหาข้ามทุกคอลัมน์ (full-text)
      if (q) {
        var hay = Object.keys(r).map(function (k) { return r[k]; }).join(' ').toLowerCase();
        if (hay.indexOf(q) === -1) return false;
      }
      // 2.2 ตัวกรองแบบ exact match
      if (fStatus && String(r.Status || '') !== fStatus) return false;
      if (fType && String(r.Type_Request || '') !== fType) return false;
      if (fTeam && String(r.type_teams || '') !== fTeam) return false;
      if (fProv && String(r.province || '') !== fProv) return false;
      // 2.3 ตัวกรองช่วงวันที่ (อิง Request TimeStamp)
      if (dFrom || dTo) {
        var d = toDate(r['Request TimeStamp']);
        if (!d) return false;
        if (dFrom && d < dFrom) return false;
        if (dTo && d > dTo) return false;
      }
      return true;
    });

    sortView();
    renderAll();
    renderFilterSummary(q, fStatus, fType, fTeam, fProv);
  }

  /** เรียงลำดับตามฟิลด์และทิศทางที่เลือก (รองรับตัวเลข/วันที่/ข้อความไทย) */
  function sortView() {
    var by = $('sortBy').value, dir = $('sortDir').value === 'asc' ? 1 : -1;
    STATE.view.sort(function (a, b) {
      var x = a[by], y = b[by];
      if (by === 'Request TimeStamp') { x = toDate(x) || 0; y = toDate(y) || 0; }
      if (by === 'limit_num' || by === '_ID') { x = Number(x) || 0; y = Number(y) || 0; }
      if (typeof x === 'string' || typeof y === 'string') {
        return String(x || '').localeCompare(String(y || ''), 'th') * dir;
      }
      return (x > y ? 1 : x < y ? -1 : 0) * dir;
    });
  }

  function resetFilters() {
    ['q', 'dFrom', 'dTo'].forEach(function (id) { $(id).value = ''; });
    ['fStatus', 'fType', 'fTeam', 'fProv'].forEach(function (id) { $(id).value = ''; });
    $('sortBy').value = 'Request TimeStamp';
    $('sortDir').value = 'desc';
    applyFilters();
    toast('ล้างตัวกรองแล้ว');
  }

  function renderFilterSummary(q, s, t, tm, p) {
    var parts = [];
    if (q) parts.push('คำค้น "' + esc(q) + '"');
    if (s) parts.push('สถานะ: ' + esc(s));
    if (t) parts.push('ประเภทคำขอ: ' + esc(t));
    if (tm) parts.push('ทีม: ' + esc(tm));
    if (p) parts.push('จังหวัด: ' + esc(p));
    if ($('dFrom').value || $('dTo').value) parts.push('ช่วงวันที่ ' + ($('dFrom').value || '...') + ' ถึง ' + ($('dTo').value || '...'));
    $('filterSummary').innerHTML = 'แสดง <b>' + STATE.view.length + '</b> จาก <b>' + STATE.all.length +
      '</b> รายการ' + (parts.length ? ' — เงื่อนไข: ' + parts.join(' | ') : ' (ไม่มีตัวกรอง)');
  }

  /** สั่ง render ทุกส่วนของ Dashboard */
  function renderAll() {
    renderKpis();
    renderOverviewCharts();
    renderTrendCharts();
    renderTop10();
    renderTable();
    renderInsights();
    renderAnomalies();
    renderDictionary();
  }

  /* =========================================================================
     3) KPI CARDS
     ========================================================================= */

  function renderKpis() {
    var rows = STATE.view;
    var totalLimit = rows.reduce(function (s, r) { return s + (Number(r.limit_num) || 0); }, 0);
    var approved = rows.filter(function (r) { return String(r.Status || '').indexOf('อนุมัติ') === 0; }).length;
    var passed = rows.filter(function (r) { return String(r.Status || '').indexOf('ผ่านการ') === 0; }).length;
    var rejected = rows.filter(function (r) { return String(r.Status || '').indexOf('ไม่ผ่าน') > -1; }).length;
    var pending = rows.filter(function (r) { return String(r.Status || '').indexOf('รอ') === 0; }).length;
    var customers = new Set(rows.map(function (r) { return r.Customer_id || r['Customer Name']; })).size;
    var avg = rows.length ? totalLimit / rows.length : 0;

    var cards = [
      { label: 'คำขอทั้งหมด', value: fmtNum(rows.length), sub: 'จากทั้งหมด ' + STATE.all.length + ' รายการ', cls: '' },
      { label: 'วงเงินรวมที่ขอ', value: fmtShortTHB(totalLimit), sub: fmtNum(totalLimit) + ' บาท', cls: 'k-purple' },
      { label: 'วงเงินเฉลี่ย/คำขอ', value: fmtShortTHB(avg), sub: fmtNum(Math.round(avg)) + ' บาท', cls: 'k-teal' },
      { label: 'ลูกค้าไม่ซ้ำ', value: fmtNum(customers), sub: 'อิง Customer_id', cls: '' },
      { label: 'อนุมัติ-KYC', value: fmtNum(approved), sub: pct(approved, rows.length) + ' ของคำขอ', cls: 'k-success' },
      { label: 'ผ่านพิจารณาเบื้องต้น', value: fmtNum(passed), sub: pct(passed, rows.length), cls: '' },
      { label: 'รอดำเนินการ/รอพิจารณา', value: fmtNum(pending), sub: pct(pending, rows.length) + ' — คอขวด', cls: 'k-warning' },
      { label: 'ไม่ผ่านพิจารณา', value: fmtNum(rejected), sub: pct(rejected, rows.length) + ' Rejection Rate', cls: 'k-danger' }
    ];

    $('kpiGrid').innerHTML = cards.map(function (c) {
      return '<div class="kpi ' + c.cls + '">' +
             '<div class="k-label">' + c.label + '</div>' +
             '<div class="k-value">' + c.value + '</div>' +
             '<div class="k-sub">' + c.sub + '</div></div>';
    }).join('');
  }

  function pct(a, b) { return b ? (a * 100 / b).toFixed(1) + '%' : '0%'; }

  /* =========================================================================
     4) CHARTS
     ========================================================================= */

  /** helper: สร้าง/แทนที่ chart ตาม id ของ canvas */
  function makeChart(id, config) {
    if (STATE.charts[id]) STATE.charts[id].destroy();   // ป้องกัน memory leak
    var ctx = document.getElementById(id);
    if (!ctx) return;
    STATE.charts[id] = new Chart(ctx, config);
  }

  var COMMON = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { labels: { font: { family: 'Segoe UI, Noto Sans Thai', size: 11 }, boxWidth: 12 } },
      tooltip: { titleFont: { family: 'Noto Sans Thai' }, bodyFont: { family: 'Noto Sans Thai' } }
    },
    scales: {
      x: { ticks: { font: { family: 'Noto Sans Thai', size: 10 } }, grid: { display: false } },
      y: { beginAtZero: true, ticks: { font: { family: 'Noto Sans Thai', size: 10 }, precision: 0 } }
    }
  };

  function renderOverviewCharts() {
    var rows = STATE.view;

    // 4.1 Bar: จำนวนตามสถานะ — คลิกเพื่อกรอง (Drill Down ระดับกลุ่ม)
    var st = groupBy(rows, 'Status');
    makeChart('chStatus', {
      type: 'bar',
      data: {
        labels: st.map(function (g) { return g.key; }),
        datasets: [{
          label: 'จำนวนคำขอ',
          data: st.map(function (g) { return g.count; }),
          backgroundColor: st.map(function (g) { return STATUS_COLOR[g.key] || '#0F6CBD'; }),
          borderRadius: 4
        }]
      },
      options: Object.assign({}, COMMON, {
        indexAxis: 'y',
        plugins: { legend: { display: false } },
        onClick: function (e, els) {
          if (!els.length) return;
          $('fStatus').value = st[els[0].index].key;
          applyFilters();
          toast('กรองสถานะ: ' + st[els[0].index].key);
        }
      })
    });

    // 4.2 Pie: สัดส่วนประเภทคำขอ
    var ty = groupBy(rows, 'Type_Request');
    makeChart('chType', {
      type: 'pie',
      data: {
        labels: ty.map(function (g) { return g.key; }),
        datasets: [{ data: ty.map(function (g) { return g.count; }), backgroundColor: PALETTE }]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: {
          legend: { position: 'bottom', labels: { font: { family: 'Noto Sans Thai', size: 11 }, boxWidth: 12 } }
        },
        onClick: function (e, els) {
          if (!els.length) return;
          $('fType').value = ty[els[0].index].key;
          applyFilters();
        }
      }
    });

    // 4.3 Doughnut: ทีมขาย
    var tm = groupBy(rows, 'type_teams');
    makeChart('chTeam', {
      type: 'doughnut',
      data: {
        labels: tm.map(function (g) { return g.key; }),
        datasets: [{ data: tm.map(function (g) { return g.count; }), backgroundColor: PALETTE }]
      },
      options: {
        responsive: true, maintainAspectRatio: false, cutout: '55%',
        plugins: { legend: { position: 'bottom', labels: { font: { family: 'Noto Sans Thai', size: 11 }, boxWidth: 12 } } }
      }
    });

    // 4.4 Bar: ประเภทธุรกิจ 8 อันดับ
    var bz = groupBy(rows, 'business_type').slice(0, 8);
    makeChart('chBiz', {
      type: 'bar',
      data: {
        labels: bz.map(function (g) { return g.key.length > 28 ? g.key.slice(0, 28) + '…' : g.key; }),
        datasets: [{ label: 'จำนวนคำขอ', data: bz.map(function (g) { return g.count; }), backgroundColor: '#038387', borderRadius: 4 }]
      },
      options: Object.assign({}, COMMON, { indexAxis: 'y', plugins: { legend: { display: false } } })
    });

    // 4.5 Bar: วงเงินรวมตามจังหวัด (Top 10)
    var pv = groupBy(rows, 'province', 'limit_num')
              .sort(function (a, b) { return b.sum - a.sum; }).slice(0, 10);
    makeChart('chProv', {
      type: 'bar',
      data: {
        labels: pv.map(function (g) { return g.key; }),
        datasets: [{ label: 'วงเงินรวม (บาท)', data: pv.map(function (g) { return g.sum; }), backgroundColor: '#8764B8', borderRadius: 4 }]
      },
      options: Object.assign({}, COMMON, {
        plugins: {
          legend: { display: false },
          tooltip: { callbacks: { label: function (c) { return fmtNum(c.raw) + ' บาท'; } } }
        },
        scales: { x: COMMON.scales.x, y: { beginAtZero: true, ticks: { callback: function (v) { return fmtShortTHB(v); }, font: { size: 10 } } } }
      })
    });

    // 4.6 Pie: ประเภทลูกค้า Type1
    var t1 = groupBy(rows, 'Type1');
    makeChart('chType1', {
      type: 'polarArea',
      data: {
        labels: t1.map(function (g) { return g.key; }),
        datasets: [{ data: t1.map(function (g) { return g.count; }), backgroundColor: PALETTE }]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: { legend: { position: 'bottom', labels: { font: { family: 'Noto Sans Thai', size: 11 }, boxWidth: 12 } } }
      }
    });
  }

  /** สร้างชุดข้อมูลแนวโน้มตาม grain ปัจจุบัน */
  function trendSeries() {
    var map = {};
    STATE.view.forEach(function (r) {
      var k = periodKey(toDate(r['Request TimeStamp']), STATE.grain);
      if (!map[k]) map[k] = { count: 0, sum: 0 };
      map[k].count++;
      map[k].sum += (Number(r.limit_num) || 0);
    });
    var keys = Object.keys(map).sort();
    return {
      labels: keys,
      counts: keys.map(function (k) { return map[k].count; }),
      sums: keys.map(function (k) { return map[k].sum; })
    };
  }

  function renderTrendCharts() {
    var s = trendSeries();

    // 4.7 Line + Bar ผสม: จำนวนคำขอ (เส้น) และวงเงินรวม (แท่ง)
    makeChart('chTrend', {
      data: {
        labels: s.labels,
        datasets: [
          { type: 'bar', label: 'วงเงินรวม (บาท)', data: s.sums, backgroundColor: 'rgba(135,100,184,.45)', yAxisID: 'y1', borderRadius: 4 },
          { type: 'line', label: 'จำนวนคำขอ', data: s.counts, borderColor: '#0F6CBD', backgroundColor: 'rgba(15,108,189,.15)',
            fill: true, tension: .35, pointRadius: 4, yAxisID: 'y' }
        ]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        interaction: { mode: 'index', intersect: false },
        plugins: {
          legend: { labels: { font: { family: 'Noto Sans Thai', size: 11 }, boxWidth: 12 } },
          tooltip: { callbacks: { label: function (c) {
            return c.dataset.label + ': ' + (c.dataset.yAxisID === 'y1' ? fmtNum(c.raw) + ' บาท' : fmtNum(c.raw) + ' รายการ');
          } } }
        },
        scales: {
          x: { grid: { display: false }, ticks: { font: { size: 10 } } },
          y: { beginAtZero: true, position: 'left', title: { display: true, text: 'จำนวนคำขอ' }, ticks: { precision: 0 } },
          y1: { beginAtZero: true, position: 'right', grid: { drawOnChartArea: false },
                title: { display: true, text: 'วงเงิน' }, ticks: { callback: function (v) { return fmtShortTHB(v); } } }
        }
      }
    });

    // 4.8 Line: ยอดสะสม
    var cum = [], run = 0;
    s.counts.forEach(function (c) { run += c; cum.push(run); });
    makeChart('chCum', {
      type: 'line',
      data: { labels: s.labels, datasets: [{ label: 'คำขอสะสม', data: cum, borderColor: '#107C10',
              backgroundColor: 'rgba(16,124,16,.12)', fill: true, tension: .3, pointRadius: 3 }] },
      options: COMMON
    });

    // 4.9 Stacked bar: สถานะแยกตามช่วงเวลา
    var statuses = groupBy(STATE.view, 'Status').map(function (g) { return g.key; });
    var byPeriod = {};
    STATE.view.forEach(function (r) {
      var k = periodKey(toDate(r['Request TimeStamp']), STATE.grain);
      var st = String(r.Status || '(ไม่ระบุ)');
      byPeriod[k] = byPeriod[k] || {};
      byPeriod[k][st] = (byPeriod[k][st] || 0) + 1;
    });
    var pkeys = Object.keys(byPeriod).sort();
    makeChart('chStack', {
      type: 'bar',
      data: {
        labels: pkeys,
        datasets: statuses.map(function (st, i) {
          return {
            label: st,
            data: pkeys.map(function (k) { return byPeriod[k][st] || 0; }),
            backgroundColor: STATUS_COLOR[st] || PALETTE[i % PALETTE.length]
          };
        })
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: { legend: { position: 'bottom', labels: { font: { family: 'Noto Sans Thai', size: 10 }, boxWidth: 10 } } },
        scales: { x: { stacked: true, grid: { display: false }, ticks: { font: { size: 10 } } },
                  y: { stacked: true, beginAtZero: true, ticks: { precision: 0 } } }
      }
    });
  }

  /* =========================================================================
     5) TOP 10 & DATA TABLE
     ========================================================================= */

  function renderTop10() {
    // 5.1 Top 10 คำขอวงเงินสูงสุด
    var top = STATE.view.slice().sort(function (a, b) {
      return (Number(b.limit_num) || 0) - (Number(a.limit_num) || 0);
    }).slice(0, 10);

    var html = '<thead><tr><th>#</th><th>ลูกค้า</th><th>ประเภทคำขอ</th><th class="num">วงเงินที่ขอ (บาท)</th>' +
               '<th>สถานะ</th><th>ทีม</th><th>จังหวัด</th><th>ผู้ดูแล</th><th>วันที่ยื่น</th></tr></thead><tbody>';
    top.forEach(function (r, i) {
      html += '<tr data-id="' + esc(r._ID) + '">' +
        '<td>' + (i + 1) + '</td>' +
        '<td>' + esc(r['Customer Name'] || r.Registered_Name || ('รายการ ' + r._ID)) + '</td>' +
        '<td>' + esc(r.Type_Request || '-') + '</td>' +
        '<td class="num"><b>' + fmtNum(r.limit_num) + '</b></td>' +
        '<td>' + statusPill(r.Status) + '</td>' +
        '<td>' + esc(r.type_teams || '-') + '</td>' +
        '<td>' + esc(r.province || '-') + '</td>' +
        '<td>' + esc(r.Owner || '-') + '</td>' +
        '<td>' + fmtDate(r['Request TimeStamp']) + '</td></tr>';
    });
    html += '</tbody>';
    var tbl = $('tblTop10');
    tbl.innerHTML = html;
    tbl.querySelectorAll('tbody tr').forEach(function (tr) {
      tr.addEventListener('click', function () { openDrill(tr.dataset.id); });
    });

    // 5.2 Top 10 Owner
    var ow = groupBy(STATE.view, 'Owner').slice(0, 10);
    makeChart('chOwner', {
      type: 'bar',
      data: { labels: ow.map(function (g) { return g.key; }),
              datasets: [{ label: 'จำนวนคำขอ', data: ow.map(function (g) { return g.count; }), backgroundColor: '#0F6CBD', borderRadius: 4 }] },
      options: Object.assign({}, COMMON, { indexAxis: 'y', plugins: { legend: { display: false } } })
    });

    // 5.3 Top 10 ลูกค้าตามวงเงินรวม
    var cu = groupBy(STATE.view, 'Customer Name', 'limit_num')
              .sort(function (a, b) { return b.sum - a.sum; }).slice(0, 10);
    makeChart('chCust', {
      type: 'bar',
      data: { labels: cu.map(function (g) { return g.key.length > 24 ? g.key.slice(0, 24) + '…' : g.key; }),
              datasets: [{ label: 'วงเงินรวม', data: cu.map(function (g) { return g.sum; }), backgroundColor: '#CA5010', borderRadius: 4 }] },
      options: Object.assign({}, COMMON, {
        indexAxis: 'y',
        plugins: { legend: { display: false }, tooltip: { callbacks: { label: function (c) { return fmtNum(c.raw) + ' บาท'; } } } },
        scales: { y: { ticks: { font: { size: 10 } } }, x: { beginAtZero: true, ticks: { callback: function (v) { return fmtShortTHB(v); } } } }
      })
    });
  }

  // คอลัมน์ที่แสดงในตารางหลัก (เลือกเฉพาะที่ใช้บ่อย ส่วนที่เหลือดูใน Drill Down)
  var TABLE_COLS = [
    { data: '_ID', title: 'รหัส' },
    { data: 'Customer Name', title: 'ชื่อลูกค้า' },
    { data: 'Customer_id', title: 'รหัสลูกค้า' },
    { data: 'Title', title: 'รูปแบบนิติบุคคล' },
    { data: 'Type_Request', title: 'ประเภทคำขอ' },
    { data: 'Type1', title: 'ประเภทลูกค้า' },
    { data: 'type_teams', title: 'ทีม' },
    { data: 'limit_num', title: 'วงเงินที่ขอ' },
    { data: 'Status', title: 'สถานะ' },
    { data: 'business_type', title: 'ประเภทธุรกิจ' },
    { data: 'province', title: 'จังหวัด' },
    { data: 'branch', title: 'สาขา' },
    { data: 'Owner', title: 'ผู้ดูแล' },
    { data: 'Request TimeStamp', title: 'วันที่ยื่นคำขอ' }
  ];

  function renderTable() {
    // ถ้ามี instance เดิม ให้ทำลายก่อนสร้างใหม่ (ข้อมูลเปลี่ยนตามตัวกรอง)
    if (STATE.dt) { STATE.dt.destroy(); $('tblMain').innerHTML = ''; }

    STATE.dt = $(('tblMain')) && window.jQuery('#tblMain').DataTable({
      data: STATE.view,
      columns: TABLE_COLS.map(function (c) {
        var col = { data: c.data, title: c.title, defaultContent: '-' };
        if (c.data === 'limit_num') {
          col.className = 'num';
          col.render = function (d, type) { return type === 'display' ? fmtNum(d) : (Number(d) || 0); };
        }
        if (c.data === 'Status') col.render = function (d, type) { return type === 'display' ? statusPill(d) : d; };
        if (c.data === 'Request TimeStamp') col.render = function (d, type) { return type === 'display' ? fmtDate(d) : d; };
        return col;
      }),
      deferRender: true,      // รองรับข้อมูลจำนวนมาก: render เฉพาะแถวที่มองเห็น
      scrollX: true,
      pageLength: 25,
      lengthMenu: [[10, 25, 50, 100, -1], [10, 25, 50, 100, 'ทั้งหมด']],
      order: [[0, 'desc']],
      language: {
        search: 'ค้นหาในตาราง:', lengthMenu: 'แสดง _MENU_ แถว',
        info: 'แสดง _START_ ถึง _END_ จาก _TOTAL_ รายการ',
        infoEmpty: 'ไม่พบข้อมูล', zeroRecords: 'ไม่พบข้อมูลที่ตรงเงื่อนไข',
        paginate: { first: 'หน้าแรก', last: 'หน้าสุดท้าย', next: 'ถัดไป', previous: 'ก่อนหน้า' }
      }
    });

    // Drill Down: คลิกแถวเพื่อดูรายละเอียดครบทุกฟิลด์
    window.jQuery('#tblMain tbody').off('click').on('click', 'tr', function () {
      var d = STATE.dt.row(this).data();
      if (d) openDrill(d._ID);
    });
  }

  /* =========================================================================
     6) INSIGHT & ANOMALY DETECTION
     ========================================================================= */

  /** คำนวณค่าสถิติที่ใช้ซ้ำหลายที่ */
  function stats() {
    var rows = STATE.view;
    var limits = rows.map(function (r) { return Number(r.limit_num) || 0; });
    var total = limits.reduce(function (a, b) { return a + b; }, 0);
    var mean = rows.length ? total / rows.length : 0;
    var sd = rows.length ? Math.sqrt(limits.reduce(function (s, v) { return s + Math.pow(v - mean, 2); }, 0) / rows.length) : 0;
    return { rows: rows, limits: limits, total: total, mean: mean, sd: sd };
  }

  function renderInsights() {
    var s = stats(), rows = s.rows;
    if (!rows.length) { $('insightGrid').innerHTML = '<div class="card">ไม่มีข้อมูลตามเงื่อนไขที่เลือก</div>'; return; }

    var st = groupBy(rows, 'Status');
    var pending = rows.filter(function (r) { return String(r.Status || '').indexOf('รอ') === 0; });
    var rejected = rows.filter(function (r) { return String(r.Status || '').indexOf('ไม่ผ่าน') > -1; });
    var approved = rows.filter(function (r) { return String(r.Status || '').indexOf('อนุมัติ') === 0; });
    var teams = groupBy(rows, 'type_teams');
    var biz = groupBy(rows, 'business_type');
    var prov = groupBy(rows, 'province');
    var mismatch = rows.filter(function (r) { return r.Status_1 && r.Status && r.Status_1 !== r.Status; });
    var dupIds = duplicateGroups(rows);
    var concentration = topShare(rows, s.total);

    var cards = [
      { cls: 'i-ok', title: '&#128200; ภาพรวมกระบวนการ', items: [
        'คำขอที่กำลังวิเคราะห์ <b>' + rows.length + '</b> รายการ วงเงินรวม <b>' + fmtNum(s.total) + ' บาท</b> (เฉลี่ย ' + fmtNum(Math.round(s.mean)) + ' บาท/คำขอ)',
        'สถานะที่พบมากที่สุดคือ <b>' + esc(st[0].key) + '</b> จำนวน ' + st[0].count + ' รายการ (' + pct(st[0].count, rows.length) + ')',
        'อนุมัติ-KYC แล้ว <b>' + approved.length + '</b> รายการ คิดเป็น ' + pct(approved.length, rows.length) + ' ของคำขอทั้งหมด'
      ]},
      { cls: 'i-warn', title: '&#9203; คอขวดของกระบวนการ (Bottleneck)', items: [
        'มีคำขอค้างในสถานะ "รอ..." ถึง <b>' + pending.length + '</b> รายการ (' + pct(pending.length, rows.length) + ') คิดเป็นวงเงินค้างพิจารณา <b>' + fmtNum(pending.reduce(function (a, r) { return a + (Number(r.limit_num) || 0); }, 0)) + ' บาท</b>',
        'อายุคำขอค้างเฉลี่ย <b>' + avgAgeDays(pending) + ' วัน</b> นับจากวันที่ยื่น',
        'ข้อเสนอแนะ: กำหนด SLA เช่น พิจารณาเบื้องต้นภายใน 2 วันทำการ และตั้งการแจ้งเตือนอัตโนมัติเมื่อเกิน SLA'
      ]},
      { cls: 'i-risk', title: '&#9888;&#65039; ความเสี่ยงที่ควรติดตาม', items: [
        'อัตราไม่ผ่านพิจารณาเบื้องต้น <b>' + pct(rejected.length, rows.length) + '</b> (' + rejected.length + ' รายการ) — ควรวิเคราะห์สาเหตุเพื่อลดงานซ้ำ',
        'การกระจุกตัวของวงเงิน: ลูกค้า 3 อันดับแรกคิดเป็น <b>' + concentration + '</b> ของวงเงินที่ขอทั้งหมด (Concentration Risk)',
        'พบคำขอของลูกค้ารายเดิมที่ยื่นซ้ำ <b>' + dupIds.length + '</b> กลุ่ม อาจทำให้นับวงเงินซ้ำซ้อนในรายงาน',
        mismatch.length ? 'พบ <b>' + mismatch.length + '</b> รายการที่ค่า Status และ Status_1 ไม่ตรงกัน → ความเสี่ยงด้านความถูกต้องของรายงาน' : 'ค่า Status และ Status_1 สอดคล้องกันทุกแถว'
      ]},
      { cls: '', title: '&#127970; โครงสร้างพอร์ตคำขอ', items: [
        'ทีมที่ยื่นคำขอมากที่สุด: <b>' + esc(teams[0].key) + '</b> ' + teams[0].count + ' รายการ (' + pct(teams[0].count, rows.length) + ')',
        'ประเภทธุรกิจหลัก: <b>' + esc(biz[0].key) + '</b> ' + biz[0].count + ' รายการ — พอร์ตพึ่งพากลุ่มรับเหมาก่อสร้างสูง จึงอ่อนไหวต่อวัฏจักรงานก่อสร้างและงบประมาณภาครัฐ',
        'จังหวัดที่มีคำขอมากที่สุด: <b>' + esc(prov[0].key) + '</b> ' + prov[0].count + ' รายการ',
        'ข้อเสนอแนะ: กระจายพอร์ตไปยังกลุ่มร้านค้าช่วง/อสังหาริมทรัพย์ เพื่อลดการกระจุกตัวของอุตสาหกรรม'
      ]},
      { cls: 'i-warn', title: '&#128203; คุณภาพข้อมูล (Data Quality)', items: [
        'คอลัมน์ที่ไม่มีข้อมูลเลยและถูกตัดออกจากรายงาน: <b>' + ((window.DEMOAPP_META && window.DEMOAPP_META.droppedEmptyColumns) || []).length + '</b> คอลัมน์ เช่น วงเงิน OD, วงเงินประกัน, ข้อมูลธนาคาร (Bank1-4)',
        'ฟิลด์ที่ควรบังคับกรอก: Estimated_annual_income, branch, Typr_Distribution เพราะยังว่างเป็นจำนวนมาก',
        'ฟิลด์ land / other_property มีการกรอกปะปนทั้งข้อความ ("ปลอดภาระ") และตัวเลข ("1-0-0", "100") ควรแยกเป็น 2 ฟิลด์: สถานะภาระ + ขนาดที่ดิน'
      ]},
      { cls: 'i-ok', title: '&#128161; ข้อเสนอแนะเชิงธุรกิจ', items: [
        'ตั้ง Dashboard นี้เป็นรายงานประจำวันของทีม Credit เพื่อติดตามคิวค้างและ SLA',
        'กำหนด Approval Matrix ตามขนาดวงเงิน (เช่น &gt; 20 ล้านบาท ต้องผ่านคณะกรรมการ) เนื่องจากมีคำขอระดับ 45–50 ล้านบาท',
        'บังคับ Validation ในฟอร์ม Power Apps: วงเงิน, เลขทะเบียนนิติบุคคล 13 หลัก, เบอร์ติดต่อ',
        'เพิ่มฟิลด์วันที่อนุมัติ (Approved Date) เพื่อคำนวณ Cycle Time ได้แม่นยำ'
      ]}
    ];

    $('insightGrid').innerHTML = cards.map(function (c) {
      return '<div class="card insight ' + c.cls + '"><div class="card-head"><h3>' + c.title + '</h3></div><ul><li>' +
             c.items.join('</li><li>') + '</li></ul></div>';
    }).join('');
  }

  /** อายุเฉลี่ย (วัน) ของรายการนับจาก Request TimeStamp ถึงวันนี้ */
  function avgAgeDays(rows) {
    if (!rows.length) return 0;
    var now = Date.now(), sum = 0, n = 0;
    rows.forEach(function (r) {
      var d = toDate(r['Request TimeStamp']);
      if (d) { sum += (now - d.getTime()) / 86400000; n++; }
    });
    return n ? (sum / n).toFixed(1) : 0;
  }

  /** หากลุ่มลูกค้าที่ยื่นคำขอซ้ำ (Customer_id เดียวกัน > 1 รายการ) */
  function duplicateGroups(rows) {
    var m = {};
    rows.forEach(function (r) {
      var k = r.Customer_id || r['Customer Name'];
      if (!k) return;
      (m[k] = m[k] || []).push(r);
    });
    return Object.keys(m).filter(function (k) { return m[k].length > 1; }).map(function (k) { return { key: k, rows: m[k] }; });
  }

  /** สัดส่วนวงเงินของลูกค้า 3 อันดับแรก */
  function topShare(rows, total) {
    if (!total) return '0%';
    var g = groupBy(rows, 'Customer Name', 'limit_num').sort(function (a, b) { return b.sum - a.sum; });
    var top3 = g.slice(0, 3).reduce(function (a, x) { return a + x.sum; }, 0);
    return (top3 * 100 / total).toFixed(1) + '%';
  }

  /**
   * ตรวจจับความผิดปกติ 4 รูปแบบ
   *  A) วงเงินสูงผิดปกติ  : z-score > 2
   *  B) คำขอซ้ำ           : ลูกค้ารายเดียวกันยื่นหลายรายการ
   *  C) ข้อมูลไม่ครบ      : ฟิลด์สำคัญว่าง
   *  D) ค้างนาน           : สถานะ "รอ..." และอายุ > 7 วัน
   *  E) สถานะไม่สอดคล้อง  : Status != Status_1
   */
  function detectAnomalies() {
    var s = stats(), out = [];
    STATE.view.forEach(function (r) {
      var reasons = [];
      var lim = Number(r.limit_num) || 0;
      if (s.sd > 0 && (lim - s.mean) / s.sd > 2) reasons.push('วงเงินสูงผิดปกติ (z=' + ((lim - s.mean) / s.sd).toFixed(2) + ')');
      var missing = ['Customer Name', 'business_type', 'province', 'Owner', 'limit'].filter(function (f) {
        return !r[f] || String(r[f]).trim() === '';
      });
      if (missing.length) reasons.push('ข้อมูลไม่ครบ: ' + missing.join(', '));
      var d = toDate(r['Request TimeStamp']);
      if (d && String(r.Status || '').indexOf('รอ') === 0 && (Date.now() - d.getTime()) / 86400000 > 7) {
        reasons.push('ค้างสถานะรอเกิน 7 วัน (' + Math.round((Date.now() - d.getTime()) / 86400000) + ' วัน)');
      }
      if (r.Status_1 && r.Status && r.Status_1 !== r.Status) reasons.push('Status ไม่ตรงกับ Status_1 ("' + r.Status_1 + '")');
      if (reasons.length) out.push({ row: r, reasons: reasons });
    });

    // เพิ่มเหตุผล "คำขอซ้ำ" ให้กับแถวที่อยู่ในกลุ่มซ้ำ
    var dups = duplicateGroups(STATE.view);
    dups.forEach(function (g) {
      g.rows.forEach(function (r) {
        var found = out.find(function (o) { return o.row._ID === r._ID; });
        var msg = 'คำขอซ้ำของลูกค้าเดียวกัน (' + g.rows.length + ' รายการ)';
        if (found) { found.reasons.push(msg); }
        else { out.push({ row: r, reasons: [msg] }); }
      });
    });

    return out.sort(function (a, b) { return b.reasons.length - a.reasons.length; });
  }

  function renderAnomalies() {
    var list = detectAnomalies();
    var html = '<thead><tr><th>รหัส</th><th>ลูกค้า</th><th class="num">วงเงิน</th><th>สถานะ</th><th>ผู้ดูแล</th><th>สาเหตุที่ตรวจพบ</th></tr></thead><tbody>';
    if (!list.length) {
      html += '<tr><td colspan="6">ไม่พบความผิดปกติตามเกณฑ์ที่กำหนด</td></tr>';
    } else {
      list.forEach(function (a) {
        html += '<tr data-id="' + esc(a.row._ID) + '">' +
          '<td>' + esc(a.row._ID) + '</td>' +
          '<td>' + esc(a.row['Customer Name'] || ('รายการ ' + a.row._ID)) + '</td>' +
          '<td class="num">' + fmtNum(a.row.limit_num) + '</td>' +
          '<td>' + statusPill(a.row.Status) + '</td>' +
          '<td>' + esc(a.row.Owner || '-') + '</td>' +
          '<td>' + a.reasons.map(esc).join('<br>') + '</td></tr>';
      });
    }
    html += '</tbody>';
    var t = $('tblAnomaly');
    t.innerHTML = html;
    t.querySelectorAll('tbody tr[data-id]').forEach(function (tr) {
      tr.addEventListener('click', function () { openDrill(tr.dataset.id); });
    });
  }

  /* =========================================================================
     7) DATA DICTIONARY — สร้างอัตโนมัติจากข้อมูลจริง + คำอธิบายที่กำหนดเอง
     ========================================================================= */

  var FIELD_DESC = {
    '_ID': ['Number', 'รหัสรายการภายในของ SharePoint ใช้เปิดฟอร์ม DispForm.aspx?ID='],
    'Title': ['Text', 'รูปแบบนิติบุคคลของลูกค้า เช่น บริษัท จํากัด / ห้างหุ้นส่วนจำกัด / หน่วยงานราชการ'],
    'Customer_id': ['Text', 'รหัสลูกค้าในระบบหลัก (9 หลัก)'],
    'Type1': ['Text', 'ประเภทลูกค้า: Existing (ลูกค้าเดิม) / Lead (ลูกค้าใหม่)'],
    'type_teams': ['Text', 'ทีมผู้ยื่นคำขอ: Store Operation / Project Sales (PS) / Wholesales (WS) / Retail'],
    'Typr_Distribution': ['Text', 'เขตการขายของทีม PS/WS เช่น WS-NE 2, PS-BMA 1'],
    'Typr_Retail': ['Text', 'เขตการขายฝั่งค้าปลีก'],
    'Customer Name': ['Text', 'ชื่อลูกค้าที่ใช้เรียกทั่วไป'],
    'branch': ['Text', 'รหัสสาขาที่ดูแลลูกค้า เช่น UDOO, SNOO, PKOO'],
    'Request TimeStamp': ['DateTime', 'วันเวลาที่ยื่นคำขอ (UTC) ใช้เป็นแกนเวลาหลักของ Dashboard'],
    'Status': ['Text', 'สถานะปัจจุบันของคำขอในสายอนุมัติ'],
    'Type_Request': ['Text', 'ประเภทคำขอ: เปิดวงเงินลูกค้าใหม่ / เพิ่มวงเงิน / ติดตามชุดเปิดตัวจริง'],
    'limit': ['Text', 'วงเงินที่ขอ (บาท) เก็บเป็นข้อความมี comma — ระบบแปลงเป็น limit_num เพื่อคำนวณ'],
    'limit_num': ['Number (คำนวณ)', 'วงเงินที่ขอในรูปตัวเลข ใช้รวมยอดและจัดอันดับ'],
    'limit_other': ['Text', 'วงเงินที่ขอเพิ่มเติม/วงเงินอื่น'],
    'Owner': ['Text', 'ผู้รับผิดชอบคำขอ (ชื่อเล่น + ชื่อจริง + รหัสหน่วยงาน)'],
    'Data': ['Text', 'วันที่จดทะเบียนจัดตั้งกิจการ'],
    'registration_number': ['Text', 'เลขทะเบียนนิติบุคคล 13 หลัก'],
    'county': ['Text', 'ตำบล/แขวง'],
    'district': ['Text', 'อำเภอ/เขต'],
    'province': ['Text', 'จังหวัด'],
    'telephone': ['Text', 'เบอร์โทรศัพท์ของกิจการ (ถูก mask ในชุดข้อมูลเผยแพร่)'],
    'Registered_Name': ['Text', 'ชื่อจดทะเบียนตามหนังสือรับรอง'],
    'business_type': ['Text', 'ประเภทธุรกิจ เช่น รับเหมาก่อสร้าง, ร้านค้าช่วง, หน่วยงานราชการ'],
    'Estimated_annual_income': ['Text', 'ประมาณการรายได้ต่อปี'],
    'contact_name': ['Text', 'ชื่อผู้ติดต่อ'],
    'position': ['Text', 'ตำแหน่งของผู้ติดต่อ'],
    'contact_number': ['Text', 'เบอร์ผู้ติดต่อ (ถูก mask ในชุดข้อมูลเผยแพร่)'],
    'credit_semester1': ['Number', 'เครดิตเทอมที่ขอ ชุดที่ 1 (วัน)'],
    'credit_semester2': ['Number', 'เครดิตเทอมที่ขอ ชุดที่ 2 (วัน)'],
    'value': ['Text', 'มูลค่า/เงื่อนไขประกอบวงเงินชุดที่ 1'],
    'value2': ['Text', 'มูลค่า/เงื่อนไขประกอบวงเงินชุดที่ 2'],
    'land': ['Text', 'ข้อมูลที่ดินของลูกค้า (สถานะภาระ หรือ ขนาด)'],
    'other_property': ['Text', 'ทรัพย์สินอื่น เช่น บ้าน รถยนต์ หรือสถานะปลอดภาระ'],
    'Status_1': ['Text', 'สถานะสำรอง/สถานะขั้นถัดไปที่ใช้ใน workflow']
  };

  function renderDictionary() {
    var rows = STATE.all;
    var cols = rows.length ? Object.keys(rows[0]) : [];
    var html = '<thead><tr><th>คอลัมน์</th><th>ชนิดข้อมูล</th><th>คำอธิบาย</th><th class="num">มีค่า</th>' +
               '<th class="num">ว่าง</th><th class="num">ค่าไม่ซ้ำ</th><th>ตัวอย่างค่า</th></tr></thead><tbody>';
    cols.forEach(function (c) {
      var vals = rows.map(function (r) { return r[c]; })
                     .filter(function (v) { return v !== null && v !== undefined && String(v).trim() !== ''; });
      var uniq = new Set(vals.map(String));
      var meta = FIELD_DESC[c] || ['Text', '-'];
      var sample = vals.slice(0, 2).map(function (v) { return String(v).slice(0, 30); }).join(' | ');
      html += '<tr><td><b>' + esc(c) + '</b></td><td>' + esc(meta[0]) + '</td><td>' + esc(meta[1]) + '</td>' +
              '<td class="num">' + vals.length + '</td><td class="num">' + (rows.length - vals.length) + '</td>' +
              '<td class="num">' + uniq.size + '</td><td>' + esc(sample) + '</td></tr>';
    });
    html += '</tbody>';
    $('tblDict').innerHTML = html;
  }

  /* =========================================================================
     8) EXPORT — Excel / CSV / PDF / PNG
     ========================================================================= */

  /** เตรียมข้อมูลที่จะ export = ข้อมูลหลังกรอง พร้อมหัวคอลัมน์ภาษาไทย */
  function exportRows() {
    return STATE.view.map(function (r) {
      var o = {};
      TABLE_COLS.forEach(function (c) {
        o[c.title] = (c.data === 'Request TimeStamp') ? fmtDate(r[c.data]) : (r[c.data] === null || r[c.data] === undefined ? '' : r[c.data]);
      });
      return o;
    });
  }

  function stamp() { return new Date().toISOString().slice(0, 10); }

  /** 8.1 Excel: ใช้ SheetJS สร้าง .xlsx 2 ชีต (ข้อมูล + สรุปสถานะ) */
  function exportExcel() {
    var wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, XLSX.utils.json_to_sheet(exportRows()), 'Data');

    var summary = groupBy(STATE.view, 'Status', 'limit_num').map(function (g) {
      return { 'สถานะ': g.key, 'จำนวนคำขอ': g.count, 'วงเงินรวม (บาท)': g.sum };
    });
    XLSX.utils.book_append_sheet(wb, XLSX.utils.json_to_sheet(summary), 'Summary_Status');

    var byTeam = groupBy(STATE.view, 'type_teams', 'limit_num').map(function (g) {
      return { 'ทีม': g.key, 'จำนวนคำขอ': g.count, 'วงเงินรวม (บาท)': g.sum };
    });
    XLSX.utils.book_append_sheet(wb, XLSX.utils.json_to_sheet(byTeam), 'Summary_Team');

    XLSX.writeFile(wb, 'KYC_DemoApp_' + stamp() + '.xlsx');
    toast('ส่งออก Excel เรียบร้อย');
  }

  /** 8.2 CSV: ใส่ BOM เพื่อให้ Excel เปิดภาษาไทยได้ถูกต้อง */
  function exportCsv() {
    var rows = exportRows();
    if (!rows.length) { toast('ไม่มีข้อมูลให้ส่งออก'); return; }
    var head = Object.keys(rows[0]);
    var csv = head.join(',') + '\n' + rows.map(function (r) {
      return head.map(function (h) {
        var v = String(r[h] === null || r[h] === undefined ? '' : r[h]).replace(/"/g, '""');
        return '"' + v + '"';
      }).join(',');
    }).join('\n');
    download(new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8;' }), 'KYC_DemoApp_' + stamp() + '.csv');
    toast('ส่งออก CSV เรียบร้อย');
  }

  /**
   * 8.3 PDF: ใช้ html2canvas จับภาพ KPI+กราฟ แล้วต่อด้วยตารางจาก autoTable
   * หมายเหตุ: jsPDF ไม่มีฟอนต์ไทย จึงพิมพ์ตารางเป็นภาพเช่นกันเพื่อให้อ่านภาษาไทยได้
   */
  async function exportPdf() {
    toast('กำลังสร้าง PDF ...');
    var jsPDF = window.jspdf.jsPDF;
    var pdf = new jsPDF({ orientation: 'landscape', unit: 'pt', format: 'a4' });
    var pw = pdf.internal.pageSize.getWidth();
    var ph = pdf.internal.pageSize.getHeight();

    // ส่วนที่ 1: ภาพ KPI + กราฟของมุมมองที่กำลังเปิดอยู่
    var canvas = await html2canvas($('captureArea'), { scale: 2, backgroundColor: '#F5F5F5', useCORS: true });
    var img = canvas.toDataURL('image/png');
    var w = pw - 40;
    var h = canvas.height * w / canvas.width;
    var y = 20;
    pdf.addImage(img, 'PNG', 20, y, w, Math.min(h, ph - 40));

    // ถ้าภาพสูงเกิน 1 หน้า ให้แบ่งหน้า
    var remaining = h - (ph - 40);
    while (remaining > 0) {
      pdf.addPage();
      y = -(h - remaining) + 20;
      pdf.addImage(img, 'PNG', 20, y, w, h);
      remaining -= (ph - 40);
    }

    pdf.save('KYC_Dashboard_' + stamp() + '.pdf');
    toast('ส่งออก PDF เรียบร้อย');
  }

  /** 8.4 PNG: จับภาพหน้า Dashboard ทั้งหน้า */
  async function exportPng() {
    toast('กำลังจับภาพหน้าจอ ...');
    var canvas = await html2canvas($('captureArea'), { scale: 2, backgroundColor: '#F5F5F5', useCORS: true });
    canvas.toBlob(function (blob) {
      download(blob, 'KYC_Dashboard_' + stamp() + '.png');
      toast('บันทึกรูปภาพเรียบร้อย');
    });
  }

  /** helper สำหรับดาวน์โหลด Blob */
  function download(blob, filename) {
    var url = URL.createObjectURL(blob);
    var a = document.createElement('a');
    a.href = url; a.download = filename;
    document.body.appendChild(a); a.click();
    document.body.removeChild(a);
    setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
  }

  /* =========================================================================
     9) NAVIGATION, DRILL DOWN MODAL
     ========================================================================= */

  function switchView(name) {
    document.querySelectorAll('.nav-item').forEach(function (a) { a.classList.toggle('active', a.dataset.view === name); });
    document.querySelectorAll('.view').forEach(function (v) { v.classList.add('hidden'); });
    var el = $('view-' + name);
    if (el) el.classList.remove('hidden');
    $('sidebar').classList.remove('open');       // ปิดเมนูอัตโนมัติบนมือถือ
    // DataTables ต้อง recalculate ความกว้างเมื่อ container เพิ่งถูกแสดง
    if (name === 'data' && STATE.dt) STATE.dt.columns.adjust();
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  /** เปิด modal แสดงทุกฟิลด์ของรายการที่เลือก */
  function openDrill(id) {
    var r = STATE.all.find(function (x) { return String(x._ID) === String(id); });
    if (!r) return;
    var meta = window.DEMOAPP_META || {};
    $('modalTitle').innerHTML = 'รายละเอียดคำขอ #' + esc(r._ID) + ' — ' + esc(r['Customer Name'] || r.Registered_Name || '');
    $('modalSpLink').href = (meta.itemFormUrl || '#') + r._ID;

    var html = '<div class="kv-grid">';
    Object.keys(r).forEach(function (k) {
      var v = r[k];
      if (v === null || v === undefined || String(v).trim() === '') return;   // ไม่แสดงฟิลด์ว่าง
      var display = (k === 'Request TimeStamp') ? fmtDate(v) : (k === 'limit_num' || k === 'limit_other_num') ? fmtNum(v) : v;
      var label = (FIELD_DESC[k] && FIELD_DESC[k][1]) ? k + ' — ' + FIELD_DESC[k][1] : k;
      html += '<div class="kv"><b>' + esc(label) + '</b><span>' +
              (k === 'Status' ? statusPill(v) : esc(display)) + '</span></div>';
    });
    html += '</div>';
    $('modalBody').innerHTML = html;
    $('modal').classList.remove('hidden');

    $('modalCopy').onclick = function () {
      navigator.clipboard.writeText(JSON.stringify(r, null, 2));
      toast('คัดลอกข้อมูลรายการแล้ว');
    };
  }

  function closeModal() { $('modal').classList.add('hidden'); }

  /* ---------- เริ่มทำงานเมื่อ DOM พร้อม ---------- */
  document.addEventListener('DOMContentLoaded', boot);
})();
