(function(){
'use strict';
const button=document.getElementById('openAnyDocument');
const input=document.getElementById('openAnyInput');
const status=document.getElementById('openAnyStatus');
if(!button||!input||!window.InkDeskFileRouter)return;
button.addEventListener('click',()=>{input.value='';input.click()});
input.addEventListener('change',async()=>{
  const file=input.files&&input.files[0];
  if(!file)return;
  button.disabled=true;
  status.textContent='Opening '+file.name+'…';
  try{
    const route=InkDeskFileRouter.routeForFile(file);
    status.textContent='Opening '+route.extension.toUpperCase()+' in the correct workspace…';
    await InkDeskFileRouter.openFromHub(file);
  }catch(error){
    console.error(error);
    status.textContent=error&&error.message?error.message:'The document could not be opened.';
    button.disabled=false;
    input.value='';
  }
});
})();
