// Cold entry, held room downloads, early interaction, failure/retry and persistent cache.
const fs=require('node:fs'),http=require('node:http'),path=require('node:path'),assert=require('node:assert/strict');
const {chromium}=require('playwright');
const root=path.resolve(__dirname,'../unity/VirtualMuseum/Build/WebGL');
const output=path.resolve(__dirname,'../unity/VirtualMuseum/Temp/room-streaming-test');
fs.mkdirSync(output,{recursive:true});
const room=JSON.parse(fs.readFileSync(path.join(root,'Content/room.json'),'utf8')).entries;
let released=false,failMicroscope=true;const held=[],requests=[];
const server=http.createServer((req,res)=>{
  const relative=new URL(req.url,'http://localhost').pathname.replace(/^\/virtual-museum\//,'')||'index.html';
  const file=path.resolve(root,relative),stat=file.startsWith(root+path.sep)&&fs.statSync(file,{throwIfNoEntry:false});
  if(!stat?.isFile()){res.writeHead(404).end();return;}
  requests.push({relative,bytes:stat.size,time:Date.now()});
  const send=()=>{
    if(res.destroyed||res.headersSent)return;
    if(relative.startsWith('Content/room-microscope-')&&failMicroscope){failMicroscope=false;res.writeHead(503).end('Test: retry room');return;}
    const types={'.html':'text/html','.js':'application/javascript','.css':'text/css','.svg':'image/svg+xml','.webmanifest':'application/manifest+json'};
    res.writeHead(200,{'Content-Type':types[path.extname(file)]||'application/octet-stream','Content-Length':stat.size});fs.createReadStream(file).pipe(res);
  };
  if(!released&&relative.startsWith('Content/room-'))held.push(send);else send();
});
(async()=>{let browser;try{
  await new Promise(r=>server.listen(0,'127.0.0.1',r));
  browser=await chromium.launch({channel:'chrome',headless:true});
  const page=await browser.newPage({viewport:{width:390,height:844},hasTouch:true,isMobile:true,deviceScaleFactor:1.5});
  const errors=[];page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error'&&!m.text().includes('503'))errors.push(m.text());});
  await page.goto(`http://127.0.0.1:${server.address().port}/virtual-museum/`);
  await page.evaluate(async()=>{await navigator.serviceWorker.ready;if(!navigator.serviceWorker.controller)await new Promise(r=>navigator.serviceWorker.addEventListener('controllerchange',r,{once:true}));});
  assert.equal(requests.filter(r=>/^(Build|Content)\//.test(r.relative)).length,0);
  const start=async()=>{await page.locator('#start-button').tap();await page.waitForFunction(()=>document.querySelector('#museum-app').dataset.state==='running',{}, {timeout:180000});await page.waitForTimeout(4000);};
  await start();
  const box=await page.locator('canvas').boundingBox(),tap=(x,y)=>page.touchscreen.tap(box.x+x,box.y+y);
  const snap=async name=>page.screenshot({path:path.join(output,name+'.png')});
  assert(held.length>0,'Room request should start after entry');
  assert.equal(requests.filter(r=>r.relative.startsWith('Content/specimen-')).length,0);
  await snap('01-room-pending');
  // Conversation can start with the existing guide rig/collider before its mesh arrives.
  await tap(box.width-60,box.height-35);await page.waitForTimeout(250);await tap(160,148);await page.waitForTimeout(1300);await snap('02-guide-pending');
  released=true;for(const send of held.splice(0))send();
  const deadline=Date.now()+120000;
  while(!room.every(e=>requests.some(r=>r.relative==='Content/'+e.file))&&Date.now()<deadline)await page.waitForTimeout(500);
  assert(room.every(e=>requests.some(r=>r.relative==='Content/'+e.file)),'All room groups must be scheduled');
  await page.waitForTimeout(3000);await snap('03-guide-restored');
  await page.keyboard.press('Escape');await page.waitForTimeout(350);await snap('04-retry-room');
  await tap(160,137);await page.waitForTimeout(3500);await snap('05-room-ready');
  const microscope=room.find(e=>e.file.startsWith('room-microscope-'));
  assert.equal(requests.filter(r=>r.relative==='Content/'+microscope.file).length,2,'Failed furniture group must retry');
  const firstRoomCount=requests.filter(r=>r.relative.startsWith('Content/room-')).length;
  await page.waitForTimeout(2000);await page.reload();await start();await page.waitForTimeout(7000);
  assert.equal(requests.filter(r=>r.relative.startsWith('Content/room-')).length,firstRoomCount,'Reload must reuse room cache');
  const cachesInfo=await page.evaluate(async()=>{
    const name=(await caches.keys()).find(n=>n.endsWith('room-v1'));const cache=await caches.open(name);const keys=await cache.keys();
    return {count:keys.length,bytes:(await Promise.all(keys.map(async k=>Number((await cache.match(k)).headers.get('X-Museum-Bytes'))))).reduce((a,b)=>a+b,0)};
  });
  assert.equal(cachesInfo.count,room.length);assert(cachesInfo.bytes<=40*1024*1024);
  await snap('06-cached-room');assert.deepEqual(errors,[]);
  const result={passed:true,roomGroups:room.length,cachesInfo,requests,errors,screenshotsRequireVisualReview:true};
  fs.writeFileSync(path.join(output,'result.json'),JSON.stringify(result,null,2));console.log(JSON.stringify({passed:true,roomGroups:room.length,cachesInfo,output}));
}finally{for(const send of held)send();if(browser)await browser.close();await new Promise(r=>server.close(r));}})().catch(e=>{console.error(e);process.exitCode=1;});
