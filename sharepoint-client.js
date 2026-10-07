(function(){
  'use strict';

  var config = {
    clientId: 'a37bd62d-e74d-4ea0-9546-1eb5aa96f604',
    tenantId: '7f8918d9-718a-495b-ac9a-17cba381c4a0',
    hostname: 'dohomegroup.sharepoint.com',
    sitePath: '/sites/AC-Accounting',
    listName: 'DemoApp'
  };
  function normalize(value){
    return String(value || '').replace(/_x([0-9a-fA-F]{4})_/g, function(_, hex){
      return String.fromCharCode(parseInt(hex, 16));
    }).toLowerCase().replace(/[^a-z0-9]/g, '');
  }
  function columnFor(columns, name){
    var key = normalize(name);
    var matches = columns.filter(function(c){ return c.name === name; });
    if(!matches.length && key) matches = columns.filter(function(c){ return normalize(c.name) === key; });
    if(!matches.length) matches = columns.filter(function(c){
      return c.displayName === name || (key && normalize(c.displayName) === key);
    });
    if(!matches.length) throw new Error('ไม่พบคอลัมน์ SharePoint: ' + name);
    matches = matches.filter(function(c){
      return !c.readOnly && !c.calculated && ['linktitle','linktitlenomenu'].indexOf(normalize(c.name)) < 0;
    });
    if(!matches.length) throw new Error('คอลัมน์ SharePoint เป็นแบบอ่านอย่างเดียว: ' + name);
    if(matches.length !== 1) throw new Error('ชื่อคอลัมน์ SharePoint ซ้ำ กรุณาระบุชื่อ internal: ' + name);
    return matches[0];
  }
  function encode(column, value){
    if(column.personOrGroup || column.lookup){
      throw new Error('คอลัมน์ ' + column.name + ' ต้องใช้ Lookup ID ไม่ใช่ข้อความ กรุณาตรวจการตั้งค่าคอลัมน์');
    }
    if(column.number || column.currency){
      var numberText = String(value).trim();
      if(!/^-?(?:\d+|\d{1,3}(?:,\d{3})+)(?:\.\d+)?$/.test(numberText)){
        throw new Error('คอลัมน์ ' + column.name + ' ต้องเป็นตัวเลข');
      }
      var number = Number(numberText.replace(/,/g, ''));
      var rules = column.number || {};
      if(!Number.isFinite(number) ||
         (rules.minimum !== undefined && number < rules.minimum) ||
         (rules.maximum !== undefined && number > rules.maximum)){
        throw new Error('ตัวเลขอยู่นอกช่วงที่กำหนด: ' + column.name);
      }
      return number;
    }
    if(column.boolean){
      if(value === true || value === 'true') return true;
      if(value === false || value === 'false') return false;
      throw new Error('คอลัมน์ ' + column.name + ' ต้องเป็น true หรือ false');
    }
    if(column.dateTime){
      var date = String(value);
      if(/^\d{4}-\d{2}-\d{2}$/.test(date)) date += 'T00:00:00Z';
      if(!/^\d{4}-\d{2}-\d{2}T/.test(date) || !Number.isFinite(Date.parse(date))){
        throw new Error('รูปแบบวันที่ไม่ถูกต้อง: ' + column.name);
      }
      return new Date(date).toISOString();
    }
    if(column.choice){
      var values = Array.isArray(value) ? value : [String(value)];
      if(!column.choice.allowTextEntry && values.some(function(v){
        return (column.choice.choices || []).indexOf(v) < 0;
      })) throw new Error('ค่าที่เลือกไม่ตรงตัวเลือกใน SharePoint: ' + column.name);
      if(column.choice.displayAs === 'checkBoxes') return values;
      if(values.length !== 1) throw new Error('เลือกได้หนึ่งค่าเท่านั้น: ' + column.name);
      return values[0];
    }
    var text = String(value);
    if(column.text && column.text.maxLength && text.length > column.text.maxLength){
      throw new Error('ข้อความยาวเกิน ' + column.text.maxLength + ' ตัวอักษร: ' + column.name);
    }
    return text;
  }
  function buildFields(columns, entries){
    var fields = {};
    entries.forEach(function(entry){
      if(entry.value === '' || entry.value === null || entry.value === undefined) return;
      try {
        var column = columnFor(columns, entry.column);
        if(Object.prototype.hasOwnProperty.call(fields, column.name)){
          throw new Error('มีข้อมูลซ้ำสำหรับคอลัมน์ ' + column.name);
        }
        var encoded = encode(column, entry.value);
        if(Array.isArray(encoded)) fields[column.name + '@odata.type'] = 'Collection(Edm.String)';
        fields[column.name] = encoded;
      } catch(error){
        throw new Error((entry.label || entry.column) + ': ' + error.message);
      }
    });
    return fields;
  }
  function create(){
    var app, account = null, initialized = false, contextCache = null;
    var scopes = ['Sites.ReadWrite.All'];
    async function initialize(){
      var local = location.protocol === 'http:' && ['localhost','127.0.0.1','[::1]'].indexOf(location.hostname) >= 0;
      if(location.protocol !== 'https:' && !local) throw new Error('กรุณาเปิดผ่าน HTTPS หรือ localhost ไม่ใช่ไฟล์ในเครื่อง');
      if(!window.msal) throw new Error('โหลด Microsoft 365 Login ไม่สำเร็จ กรุณาตรวจเครือข่ายแล้วโหลดหน้าใหม่');
      app = new msal.PublicClientApplication({
        auth: {clientId:config.clientId, authority:'https://login.microsoftonline.com/' + config.tenantId,
          redirectUri:location.origin + location.pathname},
        cache: {cacheLocation:'sessionStorage'}
      });
      await app.initialize();
      var result = await app.handleRedirectPromise();
      var accounts = app.getAllAccounts();
      account = (result && result.account) || (accounts.length === 1 ? accounts[0] : null);
      initialized = true;
      return account;
    }
    async function login(){
      if(!initialized) throw new Error('ระบบ Login ยังไม่พร้อม');
      account = (await app.loginPopup({scopes:scopes, prompt:'select_account'})).account;
      contextCache = null;
      return account;
    }
    async function logout(){
      if(!initialized) throw new Error('ระบบ Login ยังไม่พร้อม');
      await app.logoutPopup({account:account});
      account = null;
      contextCache = null;
    }
    async function token(){
      if(!initialized || !account) throw new Error('กรุณาลงชื่อเข้าใช้ Microsoft 365');
      try {
        return (await app.acquireTokenSilent({account:account, scopes:scopes})).accessToken;
      } catch(error){
        if(!(error instanceof msal.InteractionRequiredAuthError)) throw error;
        return (await app.acquireTokenPopup({account:account, scopes:scopes})).accessToken;
      }
    }
    async function graph(path, options){
      var url = new URL(path, 'https://graph.microsoft.com/v1.0/');
      if(url.origin !== 'https://graph.microsoft.com' || !url.pathname.startsWith('/v1.0/')){
        throw new Error('ปลายทาง Microsoft Graph ไม่ถูกต้อง');
      }
      var headers = new Headers(options && options.headers);
      headers.set('Authorization', 'Bearer ' + await token());
      headers.set('Accept', 'application/json');
      var response = await fetch(url.href, Object.assign({}, options || {}, {headers:headers}));
      if(!response.ok) throw new Error('Microsoft Graph ตอบกลับ ' + response.status + ': ' + await response.text());
      return response.status === 204 ? null : response.json();
    }
    async function all(path){
      var items = [];
      while(path){
        var result = await graph(path);
        items = items.concat(result.value);
        path = result['@odata.nextLink'];
      }
      return items;
    }
    async function context(){
      if(contextCache) return contextCache;
      var site = await graph('sites/' + config.hostname + ':' + config.sitePath);
      var lists = await all('sites/' + site.id + '/lists?$select=id,name,displayName&$top=200');
      var matching = lists.filter(function(list){
        return normalize(list.name) === normalize(config.listName) || normalize(list.displayName) === normalize(config.listName);
      });
      if(matching.length !== 1) throw new Error('ไม่พบ List DemoApp ที่ตรงเพียงรายการเดียว');
      var list = matching[0];
      var columns = await all('sites/' + site.id + '/lists/' + list.id + '/columns?$top=200');
      contextCache = {siteId:site.id, listId:list.id, columns:columns};
      return contextCache;
    }
    async function createItem(fields){
      var ctx = await context();
      Object.keys(fields).forEach(function(name){
        if(name.endsWith('@odata.type')) return;
        var c = ctx.columns.find(function(column){ return column.name === name; });
        if(!c || columnFor([c], name).name !== name) throw new Error('คอลัมน์ไม่พร้อมบันทึก: ' + name);
      });
      // Do not retry POST: a lost response may still have created the item.
      return graph('sites/' + ctx.siteId + '/lists/' + ctx.listId + '/items', {
        method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({fields:fields})
      });
    }
    return {initialize:initialize, login:login, logout:logout, context:context, createItem:createItem};
  }
  window.SharePointRequests = {create:create, normalize:normalize, columnFor:columnFor, buildFields:buildFields};
})();
