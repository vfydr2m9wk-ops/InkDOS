// Real worker runtime in an in-memory CacheStorage/network environment.
// Optional path compares an immutable baseline without changing its source.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const {webcrypto,createHash}=require('node:crypto');
const source=fs.readFileSync(process.argv[2]||'service-worker.js','utf8');
const scope='https://example.test/InkDOS/',suffix=':'+encodeURIComponent(scope);
const shell=JSON.parse(source.match(/const APP_SHELL=(\[[\s\S]*?\]);/)[1]);
const original=new Map(shell.map(p=>[new URL(p,scope).href,fs.readFileSync(p.slice(2))]));
const target=new URL('./apps/documents/app.js',scope).href;
function harness(){
 const stores=new Map(),network=new Map(original),requests=[];let offline=false,skip=0,claim=0,digests=0,pending=0;
 const url=r=>typeof r==='string'?new URL(r,scope).href:r.url;
 const cache=n=>({async match(r){return stores.get(n)?.get(url(r))?.clone()},async put(r,v){await new Promise(r=>setTimeout(r,1));if(!stores.has(n))stores.set(n,new Map());stores.get(n).set(url(r),v.clone())}});
 function worker(code){
  const events={};const ctx={URL,Request,Response,Uint8Array,TextEncoder,console,
   crypto:{subtle:{async digest(...args){digests++;return webcrypto.subtle.digest(...args)}}},
   fetch:async r=>{requests.push(url(r));pending++;try{await new Promise(r=>setTimeout(r,1));if(offline)throw Error('offline');const b=network.get(url(r));return new Response(b||'missing',{status:b?200:404})}finally{pending--}},
   caches:{async open(n){if(!stores.has(n))stores.set(n,new Map());return cache(n)},async keys(){return [...stores.keys()]},async delete(n){return stores.delete(n)}},
   self:{registration:{scope},location:{origin:'https://example.test'},addEventListener:(t,f)=>events[t]=f,skipWaiting(){skip++},clients:{claim(){claim++}}}};
  vm.runInNewContext(code,ctx);
  return {async dispatch(t){let p;events[t]({waitUntil:v=>p=v});await p},async get(path){let p;events.fetch({request:{url:new URL(path,scope).href,method:'GET',mode:'same-origin'},respondWith:v=>p=v});return await p}};
 }
 return {stores,network,requests,worker,setOffline(v){offline=v},reset(){requests.length=0;digests=0},stats:()=>({requests:requests.length,networkBytes:requests.reduce((n,u)=>n+(network.get(u)?.length||0),0),digests,pending,skip,claim})};
}
const changed=Buffer.from(original.get(target).toString()+'\n// synthetic update\n');
const oldHash=createHash('sha256').update(original.get(target)).digest('hex');
const newHash=createHash('sha256').update(changed).digest('hex');
const update=source.replace(/const CACHE_NAME='[^']+';/,"const CACHE_NAME='inkdos-v-test-update';").replace(oldHash,newHash);
async function seed(h){const old=h.worker(source);await old.dispatch('install');await old.dispatch('activate');return old}
(async()=>{
 const h=harness(),old=await seed(h),oldKey=[...h.stores.keys()][0];
 assert.equal(h.requests.length,shell.length,'clean install fetches entire shell');
 h.reset();h.network.set(target,changed);const next=h.worker(update);await next.dispatch('install');
 console.log(JSON.stringify({scenario:'one-file update',assets:shell.length,...h.stats()}));
 if(process.env.INKDOS_BENCHMARK_ONLY==='1')return;
 assert.equal(h.requests.length,1,'unchanged assets must be hash-verified locally, not fetched');
 assert.equal(h.requests[0],target);assert.equal(h.stats().pending,0);
 assert.equal(h.stores.size,2,'old snapshot survives while new worker waits');
 assert.equal(await (await old.get(target)).text(),original.get(target).toString());
 assert.equal(h.stats().skip,0);assert.equal(h.stats().claim,0);
 h.setOffline(true);assert.equal(await (await next.get(target)).text(),changed.toString());
 await next.dispatch('activate');assert.equal(h.stores.has(oldKey),false,'cleanup only on activation');
 assert.equal(h.stores.size,1);

 const tamper=harness();await seed(tamper);const key=[...tamper.stores.keys()][0];
 const another=new URL(shell[2],scope).href;tamper.stores.get(key).set(another,new Response('tampered'));
 tamper.network.set(target,changed);tamper.reset();await tamper.worker(update).dispatch('install');
 assert.deepEqual(new Set(tamper.requests),new Set([target,another]),'tampered local bytes require verified network repair');

 for(const failure of ['integrity','offline']){
  const bad=harness(),previous=await seed(bad);const previousKey=[...bad.stores.keys()][0];
  bad.network.set(target,Buffer.from('wrong hash'));if(failure==='offline')bad.setOffline(true);
  await assert.rejects(bad.worker(update).dispatch('install'),/integrity|offline|snapshot/);
  await new Promise(r=>setTimeout(r,30));
  assert.deepEqual([...bad.stores.keys()],[previousKey],'failed concurrent batch must not recreate partial cache');
  bad.setOffline(true);assert.equal(await (await previous.get(target)).text(),original.get(target).toString());
 }
 const isolated=harness();const foreign='inkdos-v-foreign:'+encodeURIComponent('https://example.test/Other/');
 isolated.stores.set(foreign,new Map(original));await seed(isolated);
 assert.equal(isolated.requests.length,shell.length);assert.ok(isolated.stores.has(foreign));
 console.log('Incremental snapshot: clean/update/reuse/tamper/rejection/rollback/offline/waiting/scope PASS');
})().catch(e=>{console.error(e);process.exitCode=1});
