(function(){
'use strict';
const registryUrl='/static/feature-registry.json';
let registry=[];
let page=1;
const PAGE_SIZE=60;
function esc(s){return String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
function safeGet(key, fallback=''){try{return localStorage.getItem(key) ?? fallback;}catch{return fallback;}}
function safeSet(key,value){try{localStorage.setItem(key,value);return true;}catch{return false;}}
function readJSON(key,fallback){try{const v=JSON.parse(safeGet(key,''));return v??fallback;}catch{return fallback;}}
function keyFor(id){return 'proof_feature_v5_'+id;}
function enabled(id){return safeGet(keyFor(id))==='1';}
function groupKey(name){return name.toLowerCase().replace(/[^a-z0-9]+/g,'_');}
const filterAliases={security:['security / privacy','security'],case:['case management','case'],evidence:['evidence'],analytics:['analytics','executive dashboard','dashboard'],notify:['notification','smart notification'],mobile:['mobile / pwa','advanced mobile','mobile']};
function filtered(){const q=(document.getElementById('featureSearch')?.value||'').trim().toLowerCase();const f=(document.getElementById('featureFilter')?.value||'all').toLowerCase();const allowed=filterAliases[f];return registry.filter(x=>(f==='all'||allowed?.some(a=>x.group.toLowerCase()===a||x.group.toLowerCase().includes(a)))&&(`${x.title} ${x.desc} ${x.group}`).toLowerCase().includes(q));}
function render(){const root=document.getElementById('featureGroups');if(!root)return;const all=filtered();const visible=all.slice(0,page*PAGE_SIZE);const groups={};visible.forEach(x=>(groups[x.group]??=[]).push(x));root.innerHTML=Object.entries(groups).map(([group,items])=>`<section class="feature-group"><h2>✦ ${esc(group)}</h2><div class="feature-grid">${items.map(x=>`<article class="feature-card" data-feature-id="${x.id}"><div class="ico">✦</div><div style="flex:1"><b>${x.id}. ${esc(x.title)}</b><small>${esc(x.desc)}</small></div><span class="feature-status ${enabled(x.id)?'enabled':''}">${enabled(x.id)?'ON':'READY'}</span><button class="btn secondary small feature-run" data-id="${x.id}">Open</button></article>`).join('')}</div></section>`).join('')||'<div class="feature-output">ရှာဖွေထားသော Feature မရှိပါ။</div>';
let more=document.getElementById('featureLoadMore');if(!more){more=document.createElement('button');more.id='featureLoadMore';more.className='btn secondary';root.after(more);}
more.textContent=visible.length<all.length?`နောက်ထပ် ${Math.min(PAGE_SIZE,all.length-visible.length)} ခု ပြရန် (${visible.length}/${all.length})`:`အားလုံးပြပြီးပါပြီ (${all.length})`;more.hidden=visible.length>=all.length;updateKpis();}
function updateKpis(){const active=registry.filter(x=>enabled(x.id)).length;const total=registry.length;const el=id=>document.getElementById(id);if(el('featureActiveCount'))el('featureActiveCount').textContent=active;if(el('featureTotalCount'))el('featureTotalCount').textContent=total;if(el('featureSavedCount'))el('featureSavedCount').textContent=readJSON('proof_saved_searches_v1',[]).length;if(el('featureDraftCount'))el('featureDraftCount').textContent=safeGet('proof_offline_draft_v3')?1:0;}
function run(id){const x=registry.find(v=>v.id===id);if(!x)return;const on=enabled(id);safeSet(keyFor(id),on?'0':'1');const out=document.getElementById('featureOutput');if(out)out.innerHTML=`<b>${x.id}. ${esc(x.title)}</b><p>${esc(x.desc)}</p><p class="muted">${on?'Feature ကို OFF ပြန်လုပ်ထားသည်။':'Feature workspace ကို ON လုပ်ထားသည်။'} Production-only integrations (OAuth/provider/backend credentials) ကို deployment configuration မှာ ချိတ်ဆက်ရန်လိုပါသည်။</p>`;render();}
function saved(){const list=document.getElementById('savedSearches');if(!list)return;const arr=readJSON('proof_saved_searches_v1',[]);list.innerHTML=arr.map((x,i)=>`<span class="saved-search"><button data-load="${i}">${esc(x.name)}</button><button data-del="${i}" aria-label="delete">×</button></span>`).join('')||'<span class="muted">Saved Search မရှိသေးပါ။</span>';}
function exportAll(){const blob=new Blob([JSON.stringify(registry,null,2)],{type:'application/json'});const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download='proof-complete-feature-registry.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
async function init(){
 try{const r=await fetch(registryUrl,{cache:'no-store'});registry=(await r.json()).features||[];}catch(e){registry=[];}
 render();saved();
 const search=document.getElementById('featureSearch');const filter=document.getElementById('featureFilter');
 search?.addEventListener('input',()=>{page=1;requestAnimationFrame(render);});
 filter?.addEventListener('change',()=>{page=1;requestAnimationFrame(render);});
 document.getElementById('featureExportBtn')?.addEventListener('click',exportAll);
 document.getElementById('featureGroups')?.addEventListener('click',e=>{
   const runBtn=e.target.closest('[data-id]');
   if(runBtn){run(Number(runBtn.dataset.id));return;}
 });
 document.getElementById('featureLoadMore')?.addEventListener('click',()=>{page++;requestAnimationFrame(render);});
 document.getElementById('saveSearchBtn')?.addEventListener('click',()=>{const name=document.getElementById('savedSearchName')?.value.trim()||`Search ${Date.now()}`;const arr=readJSON('proof_saved_searches_v1',[]);arr.push({name,query:document.getElementById('featureSearch')?.value||'',filter:document.getElementById('featureFilter')?.value||'all'});safeSet('proof_saved_searches_v1',JSON.stringify(arr));if(document.getElementById('savedSearchName'))document.getElementById('savedSearchName').value='';saved();updateKpis();});
 document.getElementById('savedSearches')?.addEventListener('click',e=>{const load=e.target.closest('[data-load]'),del=e.target.closest('[data-del]');const arr=readJSON('proof_saved_searches_v1',[]);if(load){const x=arr[Number(load.dataset.load)];if(x){const a=document.getElementById('featureSearch');if(a){a.value=x.query||'';}const f=document.getElementById('featureFilter');if(f){f.value=x.filter||'all';}page=1;requestAnimationFrame(render);const out=document.getElementById('featureOutput');if(out)out.innerHTML=`<b>${esc(x.name)}</b><p>Saved filter ပြန်ဖွင့်ပြီးပါပြီ။</p>`;}}else if(del){arr.splice(Number(del.dataset.del),1);safeSet('proof_saved_searches_v1',JSON.stringify(arr));saved();updateKpis();}});
}

window.addEventListener('DOMContentLoaded',init);
})();
