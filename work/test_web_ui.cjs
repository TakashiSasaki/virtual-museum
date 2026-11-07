// Smoke test the optimized player through its mobile UI; screenshots need visual review.
const fs=require('node:fs'),http=require('node:http'),path=require('node:path'),assert=require('node:assert/strict');
const {chromium}=require('playwright');
const root=path.resolve(__dirname,'../unity/VirtualMuseum/Build/WebGL');
const output=path.resolve(__dirname,'../unity/VirtualMuseum/Temp/web-ui-test');
fs.mkdirSync(output,{recursive:true});
const server=http.createServer((req,res)=>{
  const relative=new URL(req.url,'http://localhost').pathname.replace(/^\/virtual-museum\//,'')||'index.html';
  const file=path.resolve(root,relative);
  if(!file.startsWith(root+path.sep)||!fs.statSync(file,{throwIfNoEntry:false})?.isFile()){res.writeHead(404).end();return;}
  const types={'.html':'text/html','.js':'application/javascript','.css':'text/css','.svg':'image/svg+xml','.webmanifest':'application/manifest+json'};
  res.writeHead(200,{'Content-Type':types[path.extname(file)]||'application/octet-stream'});fs.createReadStream(file).pipe(res);
});
(async()=>{let browser;try{
  await new Promise(r=>server.listen(0,'127.0.0.1',r));
  browser=await chromium.launch({channel:'chrome',headless:true});
  const page=await browser.newPage({viewport:{width:390,height:844},hasTouch:true,isMobile:true,deviceScaleFactor:1.5});
  const errors=[],downloads=[];
  page.on('response',r=>{if(r.status()>=400)console.error('HTTP '+r.status()+' '+r.url());});
  page.on('request',r=>{if(r.url().includes('/Content/specimen-'))downloads.push(r.url());});
  page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
  await page.goto(`http://127.0.0.1:${server.address().port}/virtual-museum/`);
  await page.locator('#start-button').tap();
  await page.waitForFunction(()=>document.querySelector('#museum-app').dataset.state==='running',{}, {timeout:180000});
  await page.waitForTimeout(3500);
  const box=await page.locator('canvas').boundingBox();
  const tap=(x,y)=>page.touchscreen.tap(box.x+x,box.y+y);
  const snap=async(name)=>{await page.waitForTimeout(1200);await page.screenshot({path:path.join(output,name+'.png')});};
  const send=(method,arg)=>page.evaluate(({method,arg})=>window.unityInstance.SendMessage('Museum experience',method,arg),{method,arg});
  await send('Jump',0);await snap('00-preview-on-display');
  await tap(65,box.height-35);await snap('01-observation');
  await tap(90,box.height-82);await snap('02-microscope');
  await tap(42,28);await page.waitForTimeout(1200);
  await send('Jump',0);await snap('02b-detail-on-display');
  const firstRoomDownloads=downloads.filter(url=>url.includes('specimen-00-')).length;
  assert.equal(firstRoomDownloads,1);
  // Stock observations exceed their LRU limit while the upgraded display stays resident.
  for(const index of [0,1,2,3]){
    await send('OpenBackyard');await send('ObserveReserve',index);await page.waitForTimeout(1200);
    await send('CloseObservation');await page.waitForTimeout(900);
  }
  await send('Jump',0);await send('Observe',0);await snap('02c-detail-after-stock-eviction');
  assert.equal(downloads.filter(url=>url.includes('specimen-00-')).length,firstRoomDownloads);
  await send('CloseObservation');await page.waitForTimeout(1200);
  await tap(box.width-60,box.height-35);await snap('03-menu');
  await tap(160,148);await snap('04-guide');
  await page.setViewportSize({width:320,height:568});await snap('04b-guide-small-portrait');
  await page.setViewportSize({width:640,height:360});await snap('04c-guide-landscape');
  await page.setViewportSize({width:390,height:844});await page.waitForTimeout(300);
  await page.keyboard.press('Escape');await page.waitForTimeout(250);
  await tap(box.width-60,box.height-35);await page.waitForTimeout(250);
  await tap(160,210);await snap('05-tour');
  await tap(190,box.height-76);await snap('06-tour-next');
  await tap(box.width-60,box.height-76);await snap('07-tour-exit');
  assert.deepEqual(errors,[]);
  fs.writeFileSync(path.join(output,'result.json'),JSON.stringify({passed:true,errors,screenshotsRequireVisualReview:true},null,2));
  console.log(JSON.stringify({passed:true,output}));
}finally{if(browser)await browser.close();await new Promise(r=>server.close(r));}})().catch(e=>{console.error(e);process.exitCode=1;});
