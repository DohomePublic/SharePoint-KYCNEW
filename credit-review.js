(function(){
  'use strict';
  const statuses = ['รอการพิจารณาเบื้องต้น','ผ่านการพิจารณาเบื้องต้น','ไม่ผ่านการพิจารณาเบื้องต้น','อนุมัติ-KYC','ไม่อนุมัติ'];
  let selectedStatus = statuses[0];
  let table;
  let detailDialog, detailTrigger;
  let statusDialog, statusRow, statusTrigger, client, account, busy = false;
  const decisions = statuses.slice(1,3);
  const escape = value => String(value ?? '').replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
  const raw = row => row._raw || {};
  const officer = row => raw(row).AppCredit || 'ยังไม่ระบุ';
  const distribution = row => raw(row).Type_Distribution || raw(row).Typr_Distribution || '-';
  const editUrl = row => `${LIST.replace(/\/$/,'')}/EditForm.aspx?ID=${encodeURIComponent(row.id)}`;
  function attachmentLinks(row){
    const prefix = `${LIST.replace(/\/$/,'')}/Attachments/${encodeURIComponent(row.id)}/`;
    return [...new Set(Object.values(raw(row)).filter(value =>
      typeof value === 'string' && value.startsWith(prefix)).map(value=>new URL(value).href))];
  }
  function attachmentLabel(row){
    const links = attachmentLinks(row);
    if(links.length) return `ไฟล์แนบ ${links.length} ลิงก์`;
    if(raw(row).Attachments === true || raw(row).Attachments === 'true') return 'มีไฟล์แนบ';
    if(raw(row).Attachments === false || raw(row).Attachments === 'false') return 'ไม่มีไฟล์แนบ';
    return 'ไฟล์แนบ';
  }
  function displayDate(value){
    const date = dayOf(value);
    if(!date) return 'ไม่ระบุ';
    const parts = date.split('-');
    return `${parts[2]}/${parts[1]}/${parts[0]}`;
  }
  function attachmentName(link){
    const filename = new URL(link).pathname.split('/').pop();
    try { return decodeURIComponent(filename); }
    catch(error){
      if(!(error instanceof URIError)) throw error;
      console.warn('ชื่อไฟล์แนบมีรูปแบบ URL ไม่ถูกต้อง',error);
      return 'ชื่อไฟล์เข้ารหัสไม่ถูกต้อง — เปิดไฟล์เพื่อตรวจสอบใน SharePoint';
    }
  }
  function restoreDetailFocus(){
    if(detailDialog.open) return;
    document.body.classList.remove('review-dialog-open');
    if(detailTrigger && detailTrigger.isConnected) detailTrigger.focus();
    detailTrigger = null;
  }
  function closeDetails(){
    detailDialog.close();
    restoreDetailFocus();
  }
  function createDetailDialog(){
    detailDialog = document.createElement('dialog');
    detailDialog.id = 'creditDetailDialog';
    detailDialog.className = 'review-dialog';
    detailDialog.setAttribute('aria-labelledby','creditDetailTitle');
    detailDialog.setAttribute('aria-describedby','creditDetailDescription');
    detailDialog.innerHTML = `
      <button type="button" class="review-dialog-close" data-review-close aria-label="ปิดรายละเอียดคำขอ">×</button>
      <header class="review-dialog-header">
        <h2 id="creditDetailTitle">ดูรายงานคำขอสินเชื่อ</h2>
        <p id="creditDetailDescription">แบบรายงานตามข้อมูล DemoApp สำหรับตรวจสอบสินเชื่อ</p>
      </header>
      <dl class="review-detail-grid">
        <div class="review-detail-full"><dt>ID</dt><dd id="creditDetailId"></dd></div>
        <div class="review-detail-full"><dt>ลูกค้า</dt><dd><strong id="creditDetailCustomer"></strong><small id="creditDetailCustomerSub"></small></dd></div>
        <div><dt>ประเภทธุรกิจ (business type)</dt><dd id="creditDetailBusiness"></dd></div>
        <div><dt>สถานะ</dt><dd id="creditDetailStatus"></dd></div>
        <div><dt>สาขา</dt><dd id="creditDetailBranch"></dd></div>
        <div><dt>ผู้ทำรายการ</dt><dd id="creditDetailOwner"></dd></div>
        <div><dt>ผู้แทนขาย</dt><dd id="creditDetailSales"></dd></div>
        <div><dt>วันที่ทำรายการ</dt><dd id="creditDetailDate"></dd></div>
        <div><dt>ผู้อนุมัติ</dt><dd id="creditDetailApprover"></dd></div>
      </dl>
      <dl class="review-credit-summary">
        <div><dt>วงเงินที่ขอสินเชื่อกับดูโฮม (บาท)</dt><dd id="creditDetailAmount"></dd></div>
        <div><dt>เครดิตเทอม (วัน)</dt><dd id="creditDetailTerm"></dd></div>
      </dl>
      <section class="review-attachments" aria-labelledby="creditFileHeading">
        <header><div><h3 id="creditFileHeading">ไฟล์แนบ</h3><p>แสดงไฟล์ที่ตรวจพบจากข้อมูลรายการนี้ อาจไม่ใช่ไฟล์ทั้งหมดใน SharePoint</p></div><span id="creditFileCount"></span></header>
        <ul id="creditFileList"></ul>
        <p id="creditFileNotice" role="status"></p>
        <a id="creditFileManage" target="_blank" rel="noopener">เปิดรายการ SharePoint เพื่อตรวจสอบไฟล์แนบ ↗</a>
      </section>
      <section class="review-report">
        <div><h3>รายงานเอกสาร KYC</h3><p>เปิดหน้า Credit Report แบบ A4 สำหรับพิมพ์หรือบันทึก PDF</p></div>
        <a class="btn" id="creditFullReport" target="_blank" rel="noopener">▣ ดูรายงานฉบับเต็ม</a>
      </section>`;
    document.body.append(detailDialog);
    detailDialog.querySelector('[data-review-close]').addEventListener('click',closeDetails);
    detailDialog.addEventListener('keydown',event=>{
      if(event.key === 'Escape'){
        event.preventDefault();
        closeDetails();
      }
    });
    detailDialog.addEventListener('click',event=>{
      if(event.target !== detailDialog) return;
      const bounds = detailDialog.getBoundingClientRect();
      if(event.clientX < bounds.left || event.clientX > bounds.right ||
         event.clientY < bounds.top || event.clientY > bounds.bottom) closeDetails();
    });
    detailDialog.addEventListener('close',restoreDetailFocus);
  }
  function showDetails(row,trigger){
    const source = raw(row);
    const values = {
      creditDetailId:row.id,
      creditDetailCustomer:row.customerName || source.Registered_Name,
      creditDetailCustomerSub:`${row.customerId || 'ไม่ระบุรหัสสมาชิก'} · ${row.typeRequest || 'ไม่ระบุประเภทคำขอ'}`,
      creditDetailBusiness:row.businessType || source.business_type,
      creditDetailStatus:row.status,
      creditDetailBranch:row.branch,
      creditDetailOwner:row.owner,
      creditDetailSales:source.sale_representative,
      creditDetailDate:displayDate(row.ts),
      creditDetailApprover:source['Approve Up'] || source.AppCredit || 'ยังไม่ระบุ',
      creditDetailAmount:fmt(row.limitNum),
      creditDetailTerm:row.credit1 ?? source.credit_semester1
    };
    Object.entries(values).forEach(([id,value])=>{
      document.getElementById(id).textContent = value === null || value === undefined || value === '' ? 'ไม่ระบุ' : String(value);
    });
    const links = attachmentLinks(row);
    const list = document.getElementById('creditFileList');
    list.replaceChildren();
    links.forEach(link=>{
      const item = document.createElement('li');
      const anchor = document.createElement('a');
      anchor.href = link;
      anchor.target = '_blank';
      anchor.rel = 'noopener';
      const icon = document.createElement('span');
      icon.textContent = '▤';
      icon.setAttribute('aria-hidden','true');
      const name = document.createElement('span');
      name.textContent = attachmentName(link);
      const external = document.createElement('span');
      external.textContent = '↗';
      external.setAttribute('aria-hidden','true');
      anchor.append(icon,name,external);
      item.append(anchor);
      list.append(item);
    });
    document.getElementById('creditFileCount').textContent = links.length ? `${links.length} ไฟล์ที่พบ` : attachmentLabel(row);
    const notice = document.getElementById('creditFileNotice');
    notice.hidden = links.length > 0;
    notice.textContent = source.Attachments === true || source.Attachments === 'true' ?
      'ข้อมูลระบุว่ามีไฟล์แนบ แต่ไม่มีลิงก์ไฟล์ในชุดข้อมูลนี้ โปรดเปิดรายการ SharePoint เพื่อตรวจสอบ' :
      'ไม่พบลิงก์ไฟล์แนบในชุดข้อมูลนี้ สามารถเปิดรายการ SharePoint เพื่อตรวจสอบข้อมูลล่าสุด';
    const manage = document.getElementById('creditFileManage');
    manage.href = editUrl(row);
    manage.hidden = links.length > 0;
    document.getElementById('creditFullReport').href = `print.html?id=${encodeURIComponent(row.id)}`;
    detailTrigger = trigger;
    if(!detailDialog.open) detailDialog.showModal();
    detailDialog.scrollTop = 0;
    document.body.classList.add('review-dialog-open');
  }
  const columns = [
    {title:'Action',data:null,orderable:false,render:(value,type,row)=>{
      if(type !== 'display') return '';
      const url = escape(editUrl(row));
      return `<div class="review-actions"><button type="button" data-review-action="view" aria-label="ดูรายละเอียดคำขอ">◉ ดู</button><button type="button" class="review-status-action" data-review-action="status" title="บันทึกผลพิจารณาใน DemoApp">สถานะ</button><a href="${url}" target="_blank" rel="noopener" title="แก้ไขข้อมูลใน SharePoint">✎ แก้ไข</a><a href="${url}" target="_blank" rel="noopener" title="เปิด SharePoint เพื่อจัดการไฟล์แนบ จำนวนลิงก์ที่พบอาจไม่ใช่จำนวนไฟล์ทั้งหมด">${escape(attachmentLabel(row))}</a></div>`;
    }},
    {title:'ลูกค้า',data:null,render:(value,type,row)=>{
      const name = row.customerName || raw(row).Registered_Name || '-';
      if(type !== 'display') return `${name} ${row.customerId || ''}`;
      return `<div class="review-customer"><strong>${escape(name)}</strong><small>${escape(row.customerId || '-')} · ${escape(row.businessType || '-')}</small></div>`;
    }},
    {title:'สถานะ',data:'status',render:(value,type)=>type === 'display' ? `<span class="review-status">${escape(value)}</span>` : value},
    {title:'สาขา',data:'branch',render:value=>escape(value || '-')},
    {title:'Channel',data:'team',render:value=>escape(value || '-')},
    {title:'Type_Distribution',data:distribution,render:escape},
    {title:'ผู้ทำรายการ',data:'owner',render:value=>escape(value || '-')},
    {title:'วันที่ทำรายการ',data:row=>dayOf(row.ts),render:(value,type)=>{
      if(type !== 'display' || !value) return value || '-';
      return escape(displayDate(value));
    }},
    {title:'เจ้าหน้าที่พิจารณาสินเชื่อ',data:officer,render:escape}
  ];
  function render(){
    const query = document.getElementById('creditSearch').value.trim().toLowerCase();
    const type = document.getElementById('creditType').value;
    const team = document.getElementById('creditTeam').value;
    const date = document.getElementById('creditDate').value;
    const matching = ROWS.filter(row => {
      if(!statuses.includes(row.status)) return false;
      if(type && row.typeRequest !== type) return false;
      if(team && row.team !== team) return false;
      if(date && dayOf(row.ts) !== date) return false;
      return !query || [row.customerName,raw(row).Registered_Name,row.customerId,
        raw(row).registration_number,row.owner,row.branch,officer(row),distribution(row)]
        .join(' ').toLowerCase().includes(query);
    });
    document.querySelectorAll('#creditStats button').forEach((button,index)=>{
      button.querySelector('strong').textContent = fmt(matching.filter(row=>row.status===statuses[index]).length);
      button.setAttribute('aria-pressed',String(selectedStatus===statuses[index]));
    });
    const visible = matching.filter(row=>!selectedStatus || row.status===selectedStatus);
    table = buildDT('#creditTable',columns,visible,[[7,'desc']]);
    document.getElementById('creditSummary').textContent = `แสดง ${fmt(visible.length)} จาก ${fmt(matching.length)} รายการใน 5 สถานะ` +
      (selectedStatus ? ` · ${selectedStatus}` : ' · ทุกสถานะที่แสดง');
  }
  function statusMessage(message){
    document.getElementById('creditStatusMessage').textContent = message;
  }
  function setStatusBusy(value){
    busy = value;
    statusDialog.setAttribute('aria-busy',String(value));
    statusDialog.querySelectorAll('button,select').forEach(control=>control.disabled=value);
  }
  function closeStatus(){
    if(busy) return;
    statusDialog.close();
    restoreStatusFocus();
  }
  function restoreStatusFocus(){
    if(statusDialog.open || !statusRow) return;
    document.body.classList.remove('review-dialog-open');
    const fallback = document.querySelector('#creditStats button[aria-pressed="true"]') ||
      document.querySelector('#creditStats button');
    if(statusTrigger && statusTrigger.isConnected) statusTrigger.focus();
    else if(fallback) fallback.focus();
    statusRow = null;
    statusTrigger = null;
  }
  function createStatusDialog(){
    statusDialog = document.createElement('dialog');
    statusDialog.id = 'creditStatusDialog';
    statusDialog.className = 'review-dialog review-status-dialog';
    statusDialog.setAttribute('aria-labelledby','creditStatusTitle');
    statusDialog.innerHTML = `
      <button type="button" class="review-dialog-close" data-status-close aria-label="ปิดแบบฟอร์มสถานะ">×</button>
      <header class="review-dialog-header"><h2 id="creditStatusTitle">แบบฟอร์มอนุมัติสินเชื่อ</h2>
        <p>เลือกผลการพิจารณา ระบบจะบันทึกลงคอลัมน์ Status ของตาราง DemoApp</p></header>
      <section id="creditStatusCustomer" class="review-status-customer"></section>
      <form id="creditStatusForm">
        <label for="creditStatusDecision">ผลการพิจารณา *</label>
        <select id="creditStatusDecision" required><option value="">เลือกผลการพิจารณา</option>
          ${decisions.map(status=>`<option value="${escape(status)}">${escape(status)}</option>`).join('')}</select>
        <section class="review-status-preview"><h3>ข้อมูลสำคัญสำหรับตรวจสอบก่อนบันทึก</h3>
          <dl id="creditStatusPreview" class="review-detail-grid"></dl>
          <details><summary>ดูรายละเอียดทุกคอลัมน์</summary><dl id="creditStatusColumns"></dl></details>
        </section>
        <p id="creditStatusAccount" role="status"></p>
        <button type="button" id="creditStatusLogin">ลงชื่อเข้าใช้ Microsoft 365</button>
        <p id="creditStatusMessage" role="alert"></p>
        <footer class="review-status-footer"><button type="button" data-status-close>ยกเลิก</button>
          <button type="submit" class="review-status-save">บันทึกลง DemoApp</button></footer>
      </form>`;
    document.body.append(statusDialog);
    const notice = document.createElement('p');
    notice.id = 'creditStatusNotice';
    notice.setAttribute('role','status');
    document.getElementById('creditSummary').after(notice);
    statusDialog.querySelectorAll('[data-status-close]').forEach(button=>button.addEventListener('click',closeStatus));
    statusDialog.addEventListener('cancel',event=>{
      event.preventDefault();
      closeStatus();
    });
    statusDialog.addEventListener('click',event=>{
      if(event.target !== statusDialog) return;
      const bounds = statusDialog.getBoundingClientRect();
      if(event.clientX < bounds.left || event.clientX > bounds.right ||
         event.clientY < bounds.top || event.clientY > bounds.bottom) closeStatus();
    });
    statusDialog.addEventListener('close',restoreStatusFocus);
    document.getElementById('creditStatusLogin').addEventListener('click',async ()=>{
      setStatusBusy(true);
      statusMessage('');
      try {
        if(!client){
          if(!window.SharePointRequests) throw new Error('โหลด sharepoint-client.js ไม่สำเร็จ กรุณาโหลดหน้าใหม่');
          client = SharePointRequests.create();
          try { account = await client.initialize(); }
          catch(error){ client = null; throw error; }
        }
        account = await client.login();
        document.getElementById('creditStatusAccount').textContent = `ลงชื่อเข้าใช้: ${account.username}`;
      } catch(error){
        statusMessage(error.message);
      } finally { setStatusBusy(false); }
    });
    document.getElementById('creditStatusForm').addEventListener('submit',async event=>{
      event.preventDefault();
      if(busy) return;
      const decision = document.getElementById('creditStatusDecision').value;
      if(!decisions.includes(decision)){ statusMessage('กรุณาเลือกผลการพิจารณา'); return; }
      if(!client || !account){ statusMessage('กรุณาลงชื่อเข้าใช้ Microsoft 365 ก่อนบันทึก'); return; }
      setStatusBusy(true);
      statusMessage('กำลังบันทึกลง DemoApp…');
      let saved = false;
      try {
        const context = await client.context();
        const fields = SharePointRequests.buildFields(context.columns,[{column:'Status',value:decision}]);
        await client.updateItem(statusRow.id,fields);
        statusRow.status = decision;
        statusRow._raw = {...raw(statusRow),...fields,Status:decision};
        statusRow._search = [
          ...Object.entries(statusRow).filter(([key])=>key !== '_raw' && key !== '_search').map(([,value])=>value),
          ...Object.values(statusRow._raw)
        ].join(' ').toLowerCase();
        saved = true;
      } catch(error){
        statusMessage(`บันทึกไม่สำเร็จ: ${error.message} กรุณาตรวจสอบรายการใน SharePoint ก่อนลองอีกครั้ง`);
      } finally { setStatusBusy(false); }
      if(saved){
        const id = statusRow.id;
        applyFilters();
        render();
        document.getElementById('creditStatusNotice').textContent = `บันทึกรายการ ${id} เป็น “${decision}” ใน DemoApp สำเร็จ`;
        closeStatus();
      }
    });
  }
  function showStatus(row,trigger){
    statusRow = row;
    statusTrigger = trigger;
    document.getElementById('creditStatusForm').reset();
    statusMessage('');
    document.getElementById('creditStatusNotice').textContent = '';
    document.getElementById('creditStatusCustomer').innerHTML = `<span class="review-status">${escape(row.status)}</span>
      <div><span>ID</span><strong>${escape(row.id)}</strong></div>
      <div><span>ลูกค้า</span><strong>${escape(row.customerName || raw(row).Registered_Name || '-')}</strong>
      <small>${escape(row.customerId || '-')} · ${escape(row.typeRequest || '-')}</small></div>`;
    const values = [['รหัสลูกค้า',row.customerId],['ประเภทคำขอ',row.typeRequest],['สาขา',row.branch],
      ['กลุ่มงาน',row.team],['วงเงินที่ขอสินเชื่อกับดูโฮม (บาท)',fmt(row.limitNum)],
      ['เครดิตเทอม (วัน)',row.credit1 ?? raw(row).credit_semester1]];
    const entries = pairs=>pairs.map(([label,value])=>`<div><dt>${escape(label)}</dt><dd>${escape(value ?? 'ไม่ระบุ')}</dd></div>`).join('');
    document.getElementById('creditStatusPreview').innerHTML = entries(values);
    document.getElementById('creditStatusColumns').innerHTML = entries(Object.entries({...raw(row),ID:row.id,Status:row.status}));
    statusDialog.querySelector('details').open = false;
    statusDialog.showModal();
    statusDialog.scrollTop = 0;
    document.body.classList.add('review-dialog-open');
  }
  function init(){
    createDetailDialog();
    createStatusDialog();
    const stats = document.getElementById('creditStats');
    statuses.forEach(status=>{
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'review-kpi';
      const value = document.createElement('strong');
      const label = document.createElement('span');
      label.textContent = status;
      button.append(value,label);
      button.addEventListener('click',()=>{
        selectedStatus = selectedStatus===status ? null : status;
        render();
      });
      stats.append(button);
    });
    fillSelect(document.getElementById('creditType'),uniq('typeRequest'),'ทุกประเภทคำขอ');
    fillSelect(document.getElementById('creditTeam'),uniq('team'),'ทุก Channel');
    document.getElementById('creditSearch').addEventListener('input',debounce(render,250));
    ['creditType','creditTeam','creditDate'].forEach(id=>document.getElementById(id).addEventListener('change',render));
    document.getElementById('creditClear').addEventListener('click',()=>{
      ['creditSearch','creditType','creditTeam','creditDate'].forEach(id=>document.getElementById(id).value='');
      selectedStatus = statuses[0];
      render();
    });
    document.getElementById('creditTable').addEventListener('click',event=>{
      const button = event.target.closest('button[data-review-action]');
      if(!button) return;
      const row = table.row(button.closest('tr')).data();
      if(row){
        if(button.dataset.reviewAction === 'status') showStatus(row,button);
        else showDetails(row,button);
      }
    });
    render();
  }
  document.addEventListener('DOMContentLoaded',init);
})();
