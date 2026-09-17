(function(global){'use strict';
const NS=global.InkDOS2Documents=global.InkDOS2Documents||{};
function create({session,chooseFile}={}){const $=id=>document.getElementById(id);let retryChoose=chooseFile;
 function status(text){$('statusText').textContent=text}
 function displayName(){return session.fileName||'Untitled.docx'}
 function normalizeDocxName(name){name=String(name||'').trim()||'Untitled.docx';return /\.docx$/i.test(name)?name:name+'.docx'}
 function title(name){$('titleText').value=name||displayName();document.title=displayName()+(session.dirty?' •':'')+' — Documents'}
 function syncDirty(){$('dirtyDot').classList.toggle('visible',session.dirty);document.title=displayName()+(session.dirty?' •':'')+' — Documents'}
 function setLoading(text){let p=$('loadingOverlay');if(!p){p=document.createElement('div');p.id='loadingOverlay';p.className='loading';p.innerHTML='<div class="loading-card"></div>';document.body.appendChild(p)}p.querySelector('.loading-card').textContent=text;p.classList.remove('hidden')}
 function clearLoading(){const p=$('loadingOverlay');if(p)p.classList.add('hidden')}
 function errorPanel(error,file){let p=$('openErrorPanel');if(!p){p=document.createElement('div');p.id='openErrorPanel';p.className='error-overlay';p.innerHTML='<div class="error-card"><h2>Document could not be opened</h2><p id="openErrorMessage"></p><div class="error-details"><span>File</span><code id="openErrorFile"></code><span>Engine</span><code>Documents 2.0 private reader</code></div><div class="error-actions"><button id="dismissError">Close</button><button id="retryOpen" class="retry-open">Choose another file</button></div></div>';document.body.appendChild(p);p.querySelector('#dismissError').onclick=()=>p.classList.add('hidden');p.querySelector('#retryOpen').onclick=()=>{p.classList.add('hidden');retryChoose?.()}}p.querySelector('#openErrorMessage').textContent=error?.message||String(error);p.querySelector('#openErrorFile').textContent=file?.name||'Unknown';p.classList.remove('hidden')}
 function setChooseFile(fn){retryChoose=fn}
 return Object.freeze({status,displayName,normalizeDocxName,title,syncDirty,setLoading,clearLoading,errorPanel,setChooseFile});
}
NS.ChromeController=Object.freeze({create});
})(globalThis);
