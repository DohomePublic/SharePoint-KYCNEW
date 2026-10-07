(function(){
  'use strict';
  var form = document.getElementById('newCreditForm');
  var panels = Array.from(document.querySelectorAll('[data-page]'));
  var stepButtons = Array.from(document.querySelectorAll('[data-step]'));
  var next = document.getElementById('next');
  var previous = document.getElementById('previous');
  var save = document.getElementById('save');
  var signIn = document.getElementById('signIn');
  var signOut = document.getElementById('signOut');
  var message = document.getElementById('message');
  var confirmed = document.getElementById('confirmed');
  var step = 0, ready = false, busy = false, saved = false, dirty = false;
  var account = null, client = null, columns = null;
  var missingBindings = [];
  var requestType = 'คำขอเปิดวงเงินลูกค้าใหม่';
  var province = document.getElementById('province');
  var district = document.getElementById('district');
  var county = document.getElementById('county');
  var postcode = document.getElementById('postcode');
  var addressStatus = document.getElementById('addressStatus');
  var retryAddress = document.getElementById('retryAddress');
  var provinces = [], addressReady = false;

  form.addEventListener('submit', function(event){ event.preventDefault(); });
  function showMessage(text, kind){
    message.hidden = !text;
    message.className = 'panel ' + (kind || '');
    message.textContent = text;
  }
  function fieldLabel(control){
    if(control.type === 'radio') return 'หมวดธุรกิจ';
    return (control.labels && control.labels[0] ? control.labels[0].textContent : control.id).replace(/\s*\*\s*$/, '').trim();
  }
  function controls(){
    return Array.from(form.querySelectorAll('[data-column]')).filter(function(control){
      return control.type !== 'radio' || control.checked;
    });
  }
  function state(){
    signIn.disabled = !ready || busy;
    signOut.disabled = busy;
    signIn.hidden = !!account;
    signOut.hidden = !account;
    save.disabled = !ready || !account || busy || saved || !columns || !addressReady;
    next.disabled = busy || saved;
    previous.disabled = busy || saved;
    stepButtons.forEach(function(button){ button.disabled = busy || saved; });
    document.getElementById('formFields').disabled = busy || saved;
    document.getElementById('schemaNotice').querySelectorAll('select').forEach(function(select){ select.disabled = busy || saved; });
    document.getElementById('saving').textContent = busy ? 'กำลังดำเนินการ...' : '';
  }
  function review(){
    var list = document.getElementById('review');
    list.replaceChildren();
    controls().forEach(function(control){
      if(!control.value) return;
      var term = document.createElement('dt');
      var detail = document.createElement('dd');
      term.textContent = fieldLabel(control);
      detail.textContent = control.tagName === 'SELECT' ?
        control.options[control.selectedIndex].text : control.value;
      list.append(term, detail);
    });
  }
  function showStep(index, focus){
    step = index;
    panels.forEach(function(panel, i){ panel.hidden = i !== step; });
    stepButtons.forEach(function(button, i){
      button.classList.toggle('complete', i < step);
      if(i === step) button.setAttribute('aria-current', 'step');
      else button.removeAttribute('aria-current');
    });
    document.getElementById('stepStatus').textContent = 'หน้า ' + (step + 1) + ' จาก 5 — กรอกข้อมูลให้ครบก่อนดำเนินการต่อ';
    previous.textContent = step === 0 ? '← กลับ Dashboard' : '← ก่อนหน้า';
    next.hidden = step === 4;
    save.hidden = step !== 4;
    if(step === 4) review();
    if(focus) document.getElementById('heading' + (step + 1)).focus();
  }
  function validatePage(index){
    if(index === 1 && !addressReady){
      showStep(index, false);
      showMessage('ยังโหลดข้อมูลจังหวัด/อำเภอ/ตำบลไม่สำเร็จ โปรดตรวจข้อความในส่วนที่ตั้งสำนักงาน', 'error');
      if(!retryAddress.hidden) retryAddress.focus();
      return false;
    }
    var nodes = Array.from(panels[index].querySelectorAll('input,select,textarea'));
    if(index === 0) nodes.unshift(form.querySelector('[name=category]'));
    var invalid = nodes.find(function(control){ return !control.checkValidity(); });
    if(invalid){
      showStep(index, false);
      invalid.focus();
      invalid.reportValidity();
      return false;
    }
    return true;
  }
  function navigate(target){
    if(busy || saved) return;
    if(target > step){
      for(var i = step; i < target; i++) if(!validatePage(i)) return;
    }
    showStep(target, true);
  }
  stepButtons.forEach(function(button){
    button.addEventListener('click', function(){ navigate(Number(button.dataset.step)); });
  });
  next.addEventListener('click', function(){ navigate(step + 1); });
  previous.addEventListener('click', function(){
    if(step > 0) navigate(step - 1);
    else window.location.href = 'index.html';
  });
  form.addEventListener('input', function(event){
    dirty = true;
    if(event.target !== confirmed) confirmed.checked = false;
    if(step === 4) review();
  });
  form.addEventListener('change', function(event){
    if(event.target.name !== 'category') return;
    var contractor = event.target.value === 'รับเหมาก่อสร้าง';
    ['pastProject','pastValue','employer','currentValue','currentLocation','currentStatus'].forEach(function(id){
      var control = document.getElementById(id);
      control.required = contractor;
      var label = control.labels[0];
      var marker = label.querySelector('.required');
      if(contractor && !marker){
        marker = document.createElement('span');
        marker.className = 'required';
        marker.textContent = ' *';
        label.appendChild(marker);
      } else if(!contractor && marker) marker.remove();
    });
  });
  window.addEventListener('beforeunload', function(event){
    if(dirty && !saved){
      event.preventDefault();
      event.returnValue = '';
    }
  });
  function selectedEntries(){
    var unresolved = missingBindings.find(function(binding){
      return binding.control.value.trim() && !binding.select.value;
    });
    if(unresolved){
      unresolved.select.focus();
      throw new Error('กรุณาเลือกคอลัมน์จริงสำหรับ ' + fieldLabel(unresolved.control) + ' ในส่วนตรวจคอลัมน์ SharePoint');
    }
    return controls().filter(function(control){ return control.value.trim() !== ''; }).map(function(control){
      return {column:control.dataset.column, value:control.value.trim(), label:fieldLabel(control)};
    });
  }
  function manualInput(control){
    var input = document.createElement('input');
    Array.from(control.attributes).forEach(function(attribute){ input.setAttribute(attribute.name, attribute.value); });
    input.value = control.value;
    input.placeholder = 'กรอกค่าตามข้อมูลจริง';
    control.replaceWith(input);
    return input;
  }
  function configureSelect(control, column){
    if(control.tagName !== 'SELECT' || control.hasAttribute('data-address')) return;
    var selected = control.value;
    if(column.choice){
      control.replaceChildren(new Option('กรุณาเลือก', ''));
      (column.choice.choices || []).forEach(function(choice){ control.add(new Option(choice, choice)); });
      if((column.choice.choices || []).indexOf(selected) >= 0) control.value = selected;
    } else if(control.options.length <= 1){
      // A text column has no master options. Manual input is intentional.
      manualInput(control);
    }
  }
  function configureSchema(){
    var notice = document.getElementById('schemaNotice');
    notice.replaceChildren();
    missingBindings = [];
    var originalControls = Array.from(form.querySelectorAll('[data-column]'));
    originalControls.forEach(function(control){
      var name = control.dataset.column;
      // Missing fields require an explicit choice; never guess a similarly named column.
      var key = SharePointRequests.normalize(name);
      var found = columns.some(function(c){
        return c.name === name || c.displayName === name ||
          (key && (SharePointRequests.normalize(c.name) === key || SharePointRequests.normalize(c.displayName) === key));
      });
      if(found){
        configureSelect(control, SharePointRequests.columnFor(columns, name));
        return;
      }
      if(control.type === 'radio') throw new Error('ไม่พบคอลัมน์หมวดธุรกิจ: ' + name);
      if(control.tagName === 'SELECT' && control.options.length <= 1 && !control.hasAttribute('data-address')) control = manualInput(control);
      var wrapper = document.createElement('div');
      wrapper.className = 'field';
      var label = document.createElement('label');
      var select = document.createElement('select');
      select.id = 'mapping-' + control.id;
      label.htmlFor = select.id;
      label.textContent = fieldLabel(control) + ' — ไม่พบ ' + name + ': เลือกคอลัมน์จริง หรือเว้นช่องข้อมูลนี้ว่าง';
      select.add(new Option('ยังไม่กำหนดคอลัมน์', ''));
      columns.filter(function(c){
        return !c.readOnly && !c.calculated && !c.lookup && !c.personOrGroup &&
          !['linktitle','linktitlenomenu'].includes(SharePointRequests.normalize(c.name)) &&
          !['Status','CraditApprove','AppCredit','Type_Request','Request TimeStamp'].some(function(reserved){
            return SharePointRequests.normalize(reserved) === SharePointRequests.normalize(c.name) ||
              SharePointRequests.normalize(reserved) === SharePointRequests.normalize(c.displayName);
          });
      }).forEach(function(c){ select.add(new Option((c.displayName || c.name) + ' [' + c.name + ']', c.name)); });
      select.addEventListener('change', function(){
        control.dataset.column = select.value || name;
        confirmed.checked = false;
        dirty = true;
      });
      wrapper.append(label, select);
      notice.appendChild(wrapper);
      missingBindings.push({control:control, select:select});
    });
    notice.hidden = !missingBindings.length;
    if(missingBindings.length){
      var title = document.createElement('h2');
      title.textContent = 'ตรวจคอลัมน์ SharePoint ก่อนบันทึก';
      notice.prepend(title);
    }
  }
  async function loadSchema(){
    columns = null;
    var ctx = await client.context();
    columns = ctx.columns;
    try {
      configureSchema();
    } catch(error){
      columns = null;
      throw error;
    }
  }
  function updateAccount(){
    document.getElementById('authState').textContent = account ?
      'ลงชื่อเข้าใช้แล้ว: ' + account.username : 'ยังไม่ได้ลงชื่อเข้าใช้';
    document.getElementById('owner').value = account ? (account.name || account.username) : '';
    confirmed.checked = false;
  }
  signIn.addEventListener('click', async function(){
    if(!ready || busy) return;
    busy = true;
    state();
    showMessage('');
    try {
      account = await client.login();
      updateAccount();
      await loadSchema();
    } catch(error){ showMessage(error.message, 'error'); }
    finally { busy = false; state(); }
  });
  signOut.addEventListener('click', async function(){
    if(busy) return;
    busy = true;
    state();
    try {
      await client.logout();
      account = null;
      columns = null;
      updateAccount();
    } catch(error){ showMessage(error.message, 'error'); }
    finally { busy = false; state(); }
  });
  form.addEventListener('submit', async function(event){
    event.preventDefault();
    if(busy || saved) return;
    if(step !== 4){ navigate(step + 1); return; }
    if(!ready || !account || !columns){
      showMessage('กรุณา Login และตรวจการเชื่อมต่อคอลัมน์ SharePoint ก่อนบันทึก', 'error');
      return;
    }
    for(var i = 0; i < panels.length; i++) if(!validatePage(i)) return;
    showMessage('');
    var fields;
    try {
      var entries = selectedEntries();
      entries.push({column:'Type_Request',value:requestType});
      entries.push({column:'Request TimeStamp',value:new Date().toISOString()});
      fields = SharePointRequests.buildFields(columns, entries);
    } catch(error){
      showMessage(error.message, 'error');
      return;
    }
    busy = true;
    state();
    try {
      var item = await client.createItem(fields);
      if(!item || !item.id) throw new Error('ไม่ได้รับ Item ID โปรดตรวจรายการใน SharePoint ก่อนส่งซ้ำ');
      saved = true;
      dirty = false;
      showMessage('บันทึกคำขอสำเร็จ หมายเลขรายการ: ' + item.id + ' — ข้อมูลบน Dashboard/Print จะปรากฏหลังรอบอัปเดตข้อมูล', 'success');
      var link = document.createElement('a');
      link.href = 'https://dohomegroup.sharepoint.com/sites/AC-Accounting/Lists/DemoApp/DispForm.aspx?ID=' + encodeURIComponent(item.id);
      link.textContent = ' เปิดรายการ SharePoint / แนบเอกสาร';
      link.target = '_blank';
      link.rel = 'noopener';
      message.appendChild(link);
    } catch(error){
      showMessage(error.message + ' ข้อมูลที่กรอกยังอยู่ หากเครือข่ายขาดให้ตรวจ SharePoint ก่อนส่งซ้ำเพื่อป้องกันรายการซ้ำ', 'error');
    } finally {
      busy = false;
      state();
    }
  });
  async function initialize(){
    try {
      if(!window.SharePointRequests) throw new Error('โหลด sharepoint-client.js ไม่สำเร็จ กรุณาอัปโหลดไฟล์ที่เกี่ยวข้องให้ครบ');
      client = SharePointRequests.create();
      account = await client.initialize();
      ready = true;
      updateAccount();
      if(account) await loadSchema();
    } catch(error){
      showMessage(error.message, 'error');
      document.getElementById('authState').textContent = 'ระบบยังไม่พร้อมบันทึก โปรดตรวจข้อความด้านล่าง';
    } finally { state(); }
  }
  function addressOptions(control, rows, placeholder){
    control.replaceChildren(new Option(placeholder, ''));
    rows.forEach(function(row){ control.add(new Option(row.name, row.name)); });
    control.disabled = !rows.length;
  }
  function selectedProvince(){
    return provinces.find(function(row){ return row.name === province.value; });
  }
  function selectedDistrict(){
    var parent = selectedProvince();
    return parent && parent.districts.find(function(row){ return row.name === district.value; });
  }
  province.addEventListener('change', function(){
    var parent = selectedProvince();
    addressOptions(district, parent ? parent.districts : [], parent ? 'เลือกเขต/อำเภอ' : 'เลือกจังหวัดก่อน');
    addressOptions(county, [], 'เลือกเขต/อำเภอก่อน');
    postcode.value = '';
  });
  district.addEventListener('change', function(){
    var parent = selectedDistrict();
    addressOptions(county, parent ? parent.subdistricts : [], parent ? 'เลือกแขวง/ตำบล' : 'เลือกเขต/อำเภอก่อน');
    postcode.value = '';
  });
  county.addEventListener('change', function(){
    var parent = selectedDistrict();
    var selected = parent && parent.subdistricts.find(function(row){ return row.name === county.value; });
    postcode.value = selected ? selected.postcode : '';
  });
  function validAddressRows(rows){
    return Array.isArray(rows) && rows.length > 0 &&
      rows.every(function(row){ return row && typeof row.name === 'string' && row.name.trim(); }) &&
      new Set(rows.map(function(row){ return row.name; })).size === rows.length;
  }
  async function loadAddresses(){
    addressReady = false;
    retryAddress.hidden = true;
    addressStatus.className = 'notice';
    addressStatus.textContent = 'กำลังโหลดรายชื่อจังหวัด/อำเภอ/ตำบล...';
    state();
    try {
      var response = await fetch('data/thai-addresses.json');
      if(!response.ok) throw new Error('HTTP ' + response.status);
      var data = await response.json();
      if(!data || !validAddressRows(data.provinces) || data.provinces.length !== 77 ||
        !data.provinces.every(function(p){
          return validAddressRows(p.districts) && p.districts.every(function(d){
            return validAddressRows(d.subdistricts) && d.subdistricts.every(function(s){
              return typeof s.postcode === 'string' && /^[0-9]{5}$/.test(s.postcode);
            });
          });
        })) throw new Error('รูปแบบชุดข้อมูลที่อยู่ไม่ถูกต้อง');
      provinces = data.provinces;
      addressOptions(province, provinces, 'เลือกจังหวัด');
      addressReady = true;
      addressStatus.textContent = 'เลือกจังหวัด → เขต/อำเภอ → แขวง/ตำบล ระบบจะเติมรหัสไปรษณีย์ให้ ใช้ชุดข้อมูลที่เก็บในเว็บได้ก่อน Login โดยไม่เชื่อม Master Thep1';
    } catch(error){
      addressStatus.className = 'notice error';
      addressStatus.textContent = 'โหลดข้อมูลที่อยู่ไม่สำเร็จ: ' + error.message +
        ' กรุณาเปิดผ่านเว็บ HTTP/HTTPS และตรวจว่าอัปโหลด data/thai-addresses.json ครบแล้ว จากนั้นลองใหม่';
      retryAddress.hidden = false;
    } finally { state(); }
  }
  retryAddress.addEventListener('click', loadAddresses);
  showStep(0, false);
  loadAddresses();
  initialize();
})();
