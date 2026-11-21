'use strict';
const CACHE='proof-app-shell-v7';
const SHELL=['/','/demo','/manifest.webmanifest','/static/index.html','/static/styles.css','/static/script.js','/static/features.css','/static/features.js','/static/feature-registry.json','/static/demo.css','/static/demo.js'];
self.addEventListener('install',event=>event.waitUntil(caches.open(CACHE).then(cache=>cache.addAll(SHELL)).then(()=>self.skipWaiting())));
self.addEventListener('activate',event=>event.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k.startsWith('proof-app-shell-')&&k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim())));
self.addEventListener('fetch',event=>{
  const req=event.request;if(req.method!=='GET')return;
  const url=new URL(req.url);if(url.origin!==self.location.origin)return;
  if(url.pathname.startsWith('/api/'))return;
  if(!SHELL.includes(url.pathname)&&url.pathname!=='/sw.js')return;
  event.respondWith((async()=>{
    const cache=await caches.open(CACHE);
    try{const response=await fetch(req,{cache:'no-cache'});if(response.ok)await cache.put(req,response.clone());return response;}
    catch(error){const hit=await cache.match(req);if(hit)return hit;if(req.mode==='navigate')return (await cache.match('/'))||Response.error();return Response.error();}
  })());
});
