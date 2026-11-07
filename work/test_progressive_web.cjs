// npm install playwright, then: node work/test_progressive_web.cjs
// Serves only the local Web output, exercises a fresh mobile browser, closes it.
const fs = require('node:fs');
const http = require('node:http');
const path = require('node:path');
const assert = require('node:assert/strict');
const { chromium } = require('playwright');
const root = path.resolve(__dirname, '../unity/VirtualMuseum/Build/WebGL');
const output = path.resolve(__dirname, '../unity/VirtualMuseum/Temp/progressive-test');
fs.mkdirSync(output, { recursive: true });
const requests = [];
let failNext = true;
const server = http.createServer((req, res) => {
  const pathname = new URL(req.url, 'http://localhost').pathname;
  const relative = pathname.replace(/^\/virtual-museum\//, '') || 'index.html';
  const file = path.resolve(root, relative);
  const stat = file.startsWith(root + path.sep) && fs.statSync(file, { throwIfNoEntry: false });
  if (!stat?.isFile()) { res.writeHead(404).end(); return; }
  requests.push({ relative, bytes: stat.size });
  const send = () => {
    if (res.destroyed) return;
    if (/specimen-24-/.test(relative) && failNext) { failNext = false; res.writeHead(503).end('Test: temporary failure'); return; }
    const mime = { '.html': 'text/html', '.js': 'application/javascript', '.css': 'text/css', '.svg': 'image/svg+xml', '.webmanifest': 'application/manifest+json' };
    res.writeHead(200, { 'Content-Type': mime[path.extname(file)] || 'application/octet-stream', 'Content-Length': stat.size });
    fs.createReadStream(file).pipe(res);
  };
  if (/specimen-(23|25)-/.test(relative)) setTimeout(send, 2500); else send();
});

(async () => {
  let browser, context;
  try {
    await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
    browser = await chromium.launch({ channel: 'chrome', headless: true });
    context = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 1.5, hasTouch: true, isMobile: true });
    const page = await context.newPage();
    const errors = [], responses = [];
    page.on('pageerror', e => errors.push(e.message));
    page.on('console', m => { if (m.type() === 'error' && !m.text().includes('503')) errors.push(m.text()); });
    page.on('response', r => { if (r.url().includes('/Content/')) responses.push({ url: r.url(), status: r.status(), worker: r.fromServiceWorker() }); });
    const url = `http://127.0.0.1:${server.address().port}/virtual-museum/`;
    const snap = name => page.screenshot({ path: path.join(output, name + '.png') });
    const send = (method, arg) => page.evaluate(({ method, arg }) => window.unityInstance.SendMessage('Museum experience', method, arg), { method, arg });
    const start = async () => {
      await page.locator('#start-button').tap();
      await page.waitForFunction(() => document.querySelector('#museum-app').dataset.state === 'running', {}, { timeout: 180000 });
      await page.waitForTimeout(3500);
    };
    const count = id => requests.filter(r => r.relative.includes(`specimen-${id}-`)).length;
    await page.goto(url);
    await page.evaluate(async () => { await navigator.serviceWorker.ready; if (!navigator.serviceWorker.controller) await new Promise(resolve => navigator.serviceWorker.addEventListener('controllerchange', resolve, { once: true })); });
    assert.equal(requests.filter(r => /^(Build|Content)\//.test(r.relative)).length, 0, 'Entrance must not preload Unity or models');
    await start();
    assert.equal(requests.filter(r => r.relative.startsWith('Content/specimen-')).length, 0, 'Room must not fetch detailed models');
    const startupBytes = requests.filter(r => r.relative.startsWith('Build/')).reduce((sum, r) => sum + r.bytes, 0);
    await snap('01-room');
    const canvas = await page.locator('canvas').boundingBox();
    await page.touchscreen.tap(canvas.x + canvas.width - 90, canvas.y + 86);
    await page.waitForTimeout(400); await snap('02-backyard');
    await page.touchscreen.tap(canvas.x + 240, canvas.y + 164);
    await page.waitForTimeout(300); await snap('02b-fossil-category');
    await page.touchscreen.tap(canvas.x + 65, canvas.y + 164);
    await page.waitForTimeout(200);
    assert.equal(requests.filter(r => r.relative.startsWith('Content/specimen-')).length, 0, 'Gallery must not fetch all models');
    // First gallery card: actual touch path, not only a method invocation.
    await page.touchscreen.tap(canvas.x + 110, canvas.y + 270);
    await page.waitForTimeout(1000); await snap('03-loading');
    assert.equal(count('23'), 1, 'First stock card should fetch only its own model');
    const cdp=await context.newCDPSession(page);
    await cdp.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x:130,y:410,id:0}]});
    await cdp.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{x:240,y:460,id:0}]});
    await cdp.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});
    await page.waitForTimeout(3500); await snap('04-detail');
    await send('CloseObservation'); await page.waitForTimeout(1100); await snap('05-return-to-gallery');
    await send('ObserveReserve', 1); await page.waitForTimeout(1600); await snap('06-retry');
    assert.equal(count('24'), 1);
    await page.touchscreen.tap(canvas.x + 190, canvas.y + 112);
    await page.waitForTimeout(1600); await snap('07-recovered');
    assert.equal(count('24'), 2, 'Retry must initiate another request');
    await send('CloseObservation'); await page.waitForTimeout(900);
    await send('ObserveReserve', 2); await page.waitForTimeout(200); await send('CloseObservation');
    await page.waitForTimeout(3000); await snap('08-cancelled');
    const firstCount = count('23');
    await send('ObserveReserve', 0); await page.waitForTimeout(1000);
    assert.equal(count('23'), firstCount, 'In-memory revisit should not download again');
    await page.reload(); await start();
    await send('OpenBackyard'); await send('ObserveReserve', 0); await page.waitForTimeout(1800); await snap('09-cached-after-reload');
    assert.equal(count('23'), firstCount, 'Reload should reuse the persisted specimen bundle');
    await send('CloseObservation'); await page.waitForTimeout(900);
    // Fossils and artifacts use the same lazy path and stock catalog indexing.
    await send('ObserveReserve', 14); await page.waitForTimeout(1800); await snap('10-fossil');
    await send('CloseObservation'); await page.waitForTimeout(900);
    await send('ObserveReserve', 19); await page.waitForTimeout(1800); await snap('11-pottery');
    await send('CloseObservation'); await page.waitForTimeout(900);
    await page.setViewportSize({ width: 640, height: 360 }); await page.waitForTimeout(500); await snap('12-landscape');
    await page.setViewportSize({ width: 360, height: 640 }); await page.waitForTimeout(500); await snap('13-small-portrait');
    // Exercise eviction without keeping additional Unity objects resident.
    const bundleNames=fs.readdirSync(path.join(root,'Content')).filter(name=>name.startsWith('specimen-') && name.endsWith('.bundle')).slice(0,10);
    await page.evaluate(async names=>{for(const name of names){const response=await fetch('Content/'+name);if(!response.ok)throw Error('Cache fixture failed');await response.arrayBuffer();}},bundleNames);
    await page.waitForTimeout(1500);
    const cachesInfo = await page.evaluate(async () => {
      const result = {};
      for (const name of await caches.keys()) result[name] = (await (await caches.open(name)).keys()).map(r => new URL(r.url).pathname);
      return result;
    });
    const modelCache = Object.entries(cachesInfo).find(([name]) => name.endsWith('models-v1'));
    assert(modelCache && modelCache[1].length <= 8);
    await context.setOffline(true); await page.reload();
    await page.locator('#start-button').waitFor({ state: 'visible' });
    await snap('14-offline-entrance');
    assert.deepEqual(errors, [], 'No unexpected browser or Unity errors');
    const result = { passed: true, startupBytes, requests, responses, cachesInfo, errors };
    fs.writeFileSync(path.join(output, 'result.json'), JSON.stringify(result, null, 2));
    console.log(JSON.stringify({ passed: true, startupBytes, detailedDownloads: requests.filter(r => r.relative.startsWith('Content/specimen-')).length, cacheEntries: modelCache[1].length, output }));
  } finally {
    if (context) await context.close(); if (browser) await browser.close();
    await new Promise(resolve => server.close(resolve));
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
