(function(root){'use strict';
const NS=root.InkDOS2Spreadsheets=root.InkDOS2Spreadsheets||{};
function create({session}={}){const $=id=>document.getElementById(id),title=$('docTitle'),dirty=$('dirtyDot'),status=$('statusText'),selectionStats=$('selectionStats'),loading=$('loadingOverlay'),loadingLabel=$('loadingLabel'),toastEl=$('toast'),drawer=NS.FrameUI.bindDrawer({trigger:$('menuButton'),drawer:$('appDrawer'),backdrop:$('drawerBackdrop'),closeButton:$('drawerClose')});let timer=0;
 function sync(){title.value=session.fileName||'Untitled.xlsx';dirty.classList.toggle('visible',!!session.dirty);document.title=(session.fileName||'Untitled.xlsx')+(session.dirty?' •':'')+' — Spreadsheets';const share=$('menuShare');if(share)share.disabled=!session.book?.loaded}
 title.addEventListener('focus',()=>title.select());title.addEventListener('blur',()=>{session.rename(title.value);sync()});title.addEventListener('keydown',e=>{if(e.key==='Enter'){e.preventDefault();title.blur()}else if(e.key==='Escape'){title.value=session.fileName;title.blur()}});
 function setLoading(show,label='Working…'){loading.hidden=!show;if(label)loadingLabel.textContent=label}
 function toast(message){toastEl.textContent=String(message||'');toastEl.classList.add('show');clearTimeout(timer);timer=setTimeout(()=>toastEl.classList.remove('show'),2200)}
 function setStatus(text){status.textContent=text||''}function setSelectionStats(text){selectionStats.textContent=text||''}function showError(error){const panel=$('errorOverlay');$('errorMessage').textContent=String(error?.message||error||'Unknown error');panel.hidden=false;$('errorClose').focus({preventScroll:true})}function hideError(){$('errorOverlay').hidden=true}
 $('errorClose').addEventListener('click',hideError);$('errorOverlay').addEventListener('pointerdown',e=>{if(e.target===$('errorOverlay'))hideError()});document.querySelectorAll('[data-appearance-choice]').forEach(b=>b.addEventListener('click',()=>{NS.Appearance.set(b.dataset.appearanceChoice);drawer.close()}));
 return Object.freeze({sync,setLoading,toast,setStatus,setSelectionStats,showError,hideError,drawer})}
NS.ChromeController=Object.freeze({create});
})(globalThis);
