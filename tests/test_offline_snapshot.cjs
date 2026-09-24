const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),crypto=require('node:crypto').webcrypto;
const source=fs.readFileSync('service-worker.js','utf8');
const scope='https://example.test/InkDOS/';
const paths=JSON.parse(source.match(/const APP_SHELL=(\[[\s\S]*?\]);/)[1]);
const original=new Map(paths.map(p=>[new URL(p,scope).href,fs.readFileSync(p.slice(2))]));
function harness(){
 const stores=new Map(),events={},network=new Map(original);let skip=0,claim=0,offline=false;
 const url=r=>typeof r==='string'?new URL(r,scope).href:r.url;
 const cache=name=>({async match(r){return stores.get(name).get(url(r))?.clone()},async put(r,v){stores.get(name).set(url(r),v.clone())},async addAll(ps){for(const p of ps)await this.put(p,await fetcher(p))}});
 const fetcher=async r=>{if(offline)throw Error('offline');const b=network.get(url(r));return new Response(b||'missing',{status:b?200:404})};
 const ctx={URL,Request,Response,crypto,Uint8Array,TextEncoder,console,fetch:fetcher,caches:{async open(n){if(!stores.has(n))stores.set(n,new Map());return cache(n)},async keys(){return [...stores.keys()]},async delete(n){return stores.delete(n)}},self:{registration:{scope},location:{origin:'https://example.test'},addEventListener:(t,f)=>events[t]=f,skipWaiting:async()=>skip++,clients:{claim:async()=>claim++}}};
 vm.createContext(ctx);vm.runInContext(source,ctx);
 const dispatch=async t=>{let promise;events[t]({waitUntil:p=>promise=p});await promise};
 const get=async(path,mode='same-origin')=>{let promise;events.fetch({request:{url:new URL(path,scope).href,method:'GET',mode},respondWith:p=>promise=p});return promise?await promise:null};
 return {stores,network,dispatch,get,offline(){offline=true},counts:()=>({skip,claim})};
}
(async()=>{
 const h=harness();await h.dispatch('install');await h.dispatch('activate');
 const target='./apps/documents/app.js',u=new URL(target,scope).href;
 h.network.set(u,Buffer.from('different deployment'));
 assert.equal(await (await h.get(target)).text(),original.get(u).toString(),'active snapshot must not mix newer network code');
 assert.deepEqual(h.counts(),{skip:0,claim:0},'updates must wait for existing clients');
 h.offline();assert.equal(await (await h.get('./apps/documents/?suite=1','navigate')).text(),original.get(new URL('./apps/documents/index.html',scope).href).toString());
 assert.equal(await h.get('./unmanaged.txt'),null,'unmanaged requests stay outside worker');
 const bad=harness();bad.network.set(u,Buffer.from('partial deployment'));
 await assert.rejects(bad.dispatch('install'),/integrity|snapshot|digest/i);
 assert.equal(bad.stores.size,0,'incomplete candidate cache removed');
 console.log('Worker snapshot: immutable fetch, native waiting, offline navigation, integrity rejection PASS');
})().catch(e=>{console.error(e);process.exitCode=1});
