// Render animation/index.html to MP4 frame-by-frame (deterministic).
// Usage: node scripts/render.js [out.mp4] [fps]      Stills: node scripts/render.js --stills 5,20,40
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const path = require('path');

const FFMPEG = process.env.FFMPEG || 'ffmpeg';
const page_url = 'file://' + path.resolve(__dirname, '../animation/index.html') + '?render=1';

(async () => {
  const args = process.argv.slice(2);
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
  await page.goto(page_url, { waitUntil: 'networkidle' });
  await page.evaluate(() => document.fonts.ready);

  if (args[0] === '--stills') {
    const dir = args[2] || '.';
    for (const t of args[1].split(',').map(Number)) {
      await page.evaluate(t => window.render(t), t);
      await page.screenshot({ path: path.join(dir, `still_${String(t).padStart(5, '0')}.png`) });
    }
    await browser.close();
    return;
  }

  const out = args[0] || 'iso27001_intro.mp4';
  const fps = +(args[1] || 30);
  const [from, to] = [+(args[2] || 0), +(args[3] || 0) || await page.evaluate(() => window.DUR)];
  const ff = spawn(FFMPEG, ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'mjpeg', '-i', '-',
    '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out], { stdio: ['pipe', 'inherit', 'inherit'] });
  const n0 = Math.round(from * fps), n1 = Math.round(to * fps);
  for (let i = n0; i < n1; i++) {
    await page.evaluate(t => window.render(t), i / fps);
    const buf = await page.screenshot({ type: 'jpeg', quality: 92 });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (i % (fps * 10) === 0) console.log(`frame ${i}/${n1} (${(i / fps).toFixed(0)}s)`);
  }
  ff.stdin.end();
  await new Promise(r => ff.on('close', r));
  await browser.close();
})();
