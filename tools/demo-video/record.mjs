import { mkdirSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { launch } from "./cdp.mjs";

const TMP = tmpdir();
const FRAMES = process.env.FRAMES ?? join(TMP, "hk-frames");
const BASE = process.env.BASE ?? "http://localhost:5173";
const CSV = process.env.DEMO_CSV ?? join(TMP, "hk-demo-week.csv");
const EMAIL = process.env.DEMO_EMAIL ?? EMAIL;
const PASSWORD = process.env.DEMO_PASSWORD ?? PASSWORD;
rmSync(FRAMES, { recursive: true, force: true });
mkdirSync(FRAMES, { recursive: true });
rmSync(join(TMP, "hk-chrome-9800"), { recursive: true, force: true });

const b = await launch(1280, 720, 9800);
await b.send("Network.enable");
await b.send("Network.clearBrowserCookies");

const frames = [];
b.onEvent((d) => {
  if (d.method !== "Page.screencastFrame") return false;
  const name = `${FRAMES}/${String(frames.length).padStart(6, "0")}.jpg`;
  writeFileSync(name, Buffer.from(d.params.data, "base64"));
  frames.push({ name, ts: d.params.metadata.timestamp });
  b.send("Page.screencastFrameAck", { sessionId: d.params.sessionId }).catch(() => {});
  return true;
});

const OVERLAY = `(() => {
  if (window.__hk) return;
  const style = document.createElement('style');
  style.textContent = \`
    html{scrollbar-width:none}::-webkit-scrollbar{display:none}
    [popover].hk{position:fixed;margin:0;padding:0;border:0;background:none;overflow:visible;inset:auto;color:inherit}
    #hk-caption{left:50%;bottom:26px;transform:translateX(-50%);max-width:880px;padding:16px 28px;border-radius:22px;background:rgba(17,18,20,.9);color:#f6f4ef;font:600 21px/1.4 'Inter Variable',system-ui,sans-serif;text-align:center;opacity:0;transition:opacity .5s;pointer-events:none;box-shadow:0 18px 50px rgba(0,0,0,.35)}
    #hk-caption.on{opacity:1}
    #hk-cursor{left:0;top:0;width:34px;height:34px;pointer-events:none;transition:transform .8s cubic-bezier(.22,1,.36,1)}
    #hk-ripple{left:0;top:0;width:60px;height:60px;border-radius:50%;background:rgba(17,18,20,.28);pointer-events:none;opacity:0}
    #hk-card{left:0;top:0;width:100vw;height:100vh;background:#f2f0eb;color:#111214;display:grid;place-content:center;gap:18px;text-align:center;font-family:'Fraunces Variable',Georgia,serif;opacity:0;transition:opacity .7s;pointer-events:none}
    #hk-card.on{opacity:1}
    #hk-card h1{font-size:92px;font-weight:420;letter-spacing:-.03em;margin:0}
    #hk-card p{font:500 26px/1.4 'Inter Variable',system-ui,sans-serif;color:#6a6f78;margin:0}
    #hk-card ul{list-style:none;margin:8px auto 0;padding:0;display:grid;gap:12px;font:500 24px/1.4 'Inter Variable',system-ui,sans-serif;text-align:left}
    #hk-card li::before{content:'';display:inline-block;width:10px;height:10px;border-radius:50%;background:#111214;margin-right:16px}
  \`;
  document.head.appendChild(style);
  const make = (id, html) => { const el = document.createElement('div'); el.id = id; el.className = 'hk'; el.setAttribute('popover', 'manual'); el.innerHTML = html || ''; document.body.appendChild(el); return el; };
  make('hk-card'); make('hk-caption');
  make('hk-ripple');
  make('hk-cursor', '<svg viewBox="0 0 24 24" width="34" height="34"><path d="M4 2l15 9-6.5 1.6L9.8 19z" fill="#111214" stroke="#f6f4ef" stroke-width="1.6" stroke-linejoin="round"/></svg>');
  window.__hk = { x: 640, y: 380 };
  window.__hkTop = () => { for (const id of ['hk-card','hk-caption','hk-ripple','hk-cursor']) { const el = document.getElementById(id); try { el.hidePopover(); } catch {} try { el.showPopover(); } catch {} } };
  window.__hkTop();
  document.getElementById('hk-cursor').style.transform = 'translate(640px,380px)';
})()`;

const ensure = async () => { await b.eval(OVERLAY); await b.eval("window.__hkTop()"); };
const sleep = (ms) => b.sleep(ms);
const say = async (text, hold = 1400 + text.split(' ').length * 290) => {
  await ensure();
  await b.eval(`(()=>{const c=document.getElementById('hk-caption');c.textContent=${JSON.stringify(text)};c.classList.add('on')})()`);
  await sleep(hold);
};
const hush = async (wait = 500) => { await b.eval("document.getElementById('hk-caption')?.classList.remove('on')"); await sleep(wait); };
const card = async (html, hold) => {
  await ensure();
  await b.eval(`(()=>{const c=document.getElementById('hk-card');c.innerHTML=${JSON.stringify(html)};c.classList.add('on')})()`);
  await sleep(hold);
};
const uncard = async () => { await b.eval("document.getElementById('hk-card').classList.remove('on')"); await sleep(800); };

const centre = (sel, text) => `(() => {
  const nodes = [...document.querySelectorAll(${JSON.stringify(sel)})];
  const el = ${text ? `nodes.find((n) => n.textContent.includes(${JSON.stringify(text)}))` : "nodes[0]"};
  if (!el) return null;
  el.scrollIntoView({ block: 'center', behavior: 'instant' });
  const r = el.getBoundingClientRect();
  return { x: r.left + Math.min(r.width / 2, 120), y: r.top + r.height / 2 };
})()`;

const move = async (sel, text) => {
  await ensure();
  const point = await b.eval(centre(sel, text));
  if (!point) throw new Error(`not found: ${sel} ${text ?? ""}`);
  await b.eval(`document.getElementById('hk-cursor').style.transform='translate(${point.x}px,${point.y}px)'`);
  await sleep(950);
  return point;
};
const click = async (sel, text) => {
  const point = await move(sel, text);
  await b.eval(`(()=>{const r=document.getElementById('hk-ripple');r.style.transform='translate(${point.x - 30}px,${point.y - 30}px) scale(.3)';r.style.transition='none';r.style.opacity='1';requestAnimationFrame(()=>{r.style.transition='transform .6s, opacity .6s';r.style.transform='translate(${point.x - 30}px,${point.y - 30}px) scale(1.4)';r.style.opacity='0'})})()`);
  await b.eval(`(() => { const nodes=[...document.querySelectorAll(${JSON.stringify(sel)})]; const el=${text ? `nodes.find((n)=>n.textContent.includes(${JSON.stringify(text)}))` : "nodes[0]"}; el.click(); })()`);
  await sleep(700);
};
const typeInto = async (sel, text) => {
  await move(sel);
  for (let i = 1; i <= text.length; i++) {
    await b.eval(`(()=>{const el=document.querySelector(${JSON.stringify(sel)});el.focus();Object.getOwnPropertyDescriptor(el.__proto__,'value').set.call(el,${JSON.stringify(text.slice(0, i))});el.dispatchEvent(new Event('input',{bubbles:true}))})()`);
    await sleep(55);
  }
  await sleep(250);
};
const scroll = async (sel, text, block = "start") => {
  await b.eval(`(() => { const nodes=[...document.querySelectorAll(${JSON.stringify(sel)})]; const el=${text ? `nodes.find((n)=>n.textContent.includes(${JSON.stringify(text)}))` : "nodes[0]"}; el.scrollIntoView({block:${JSON.stringify(block)},behavior:'smooth'}); })()`);
  await sleep(1600);
};
const scrollInDialog = async (y) => { await b.eval(`document.querySelector('dialog[open]').scrollTo({top:${y},behavior:'smooth'})`); await sleep(1500); };

await b.send("Page.startScreencast", { format: "jpeg", quality: 82, everyNthFrame: 1 });
await b.goto(`${BASE}/login`);
await sleep(1200);

await ensure();
await card(`<h1>Hakiki</h1><p>Know before you submit.</p><p style="font-size:20px">A glass box pre-audit for Social Health Authority claims</p>`, 3200);
await uncard();

await say("Kenyan facilities lose revenue to rejected SHA claims, and clerks cannot see why.");
await hush();
await typeInto("input[type=email]", EMAIL);
await typeInto("input[type=password]", PASSWORD);
await click("button[type=submit]");
await sleep(3000);

await say("Finance sees what Hakiki already caught before SHA did.");
await hush();

await click("a.rail__link", "Batch check");
await sleep(1200);
await say("A week of claims in one pass. Upload a CSV.");
await hush(300);
await ensure();
const doc = await b.send("DOM.getDocument");
const node = await b.send("DOM.querySelector", { nodeId: doc.root.nodeId, selector: "input[type=file]" });
await move(".dropzone");
await b.send("DOM.setFileInputFiles", { nodeId: node.nodeId, files: [CSV] });
await sleep(1200);
await say("Each claim runs through 11 rules, each tied to a SHA regulation.");
await hush(200);
await say("Patient identifiers are hashed on arrival, never stored.");
await hush(200);
for (let i = 0; i < 60; i++) {
  if (await b.eval("!!document.querySelector('.revenue')")) break;
  await sleep(700);
}
await sleep(800);
await say("24 claims checked: the revenue at risk, and the rules behind the failures.");
await scroll(".revenue", null, "start");
await sleep(1200);
await hush(200);

await scroll(".batch-rows", null, "start");
await click(".batch-rows .segmented button", "Will fail");
await sleep(900);
await say("Filter to the claims that would fail, and open one.");
await hush(200);
await click(".rows__item");
await sleep(2000);
await say("Every verdict shows its full reasoning.");
await hush(200);
await scrollInDialog(520);
await click("dialog[open] .trace__step--fail .chip");
await sleep(1800);
await say("And the SHA regulation behind each rule, quoted from the source.");
await hush(200);
await b.eval("[...document.querySelectorAll('dialog[open]')].reverse().forEach((d) => d.close())");
await sleep(800);

await click("a.rail__link", "Check claim");
await sleep(1200);
await say("Now one claim, before it goes to SHA: a caesarean section under SHIF.");
await hush(200);
await click("button", "Sample");
await sleep(800);
await click("form.claim-form button[type=submit]");
await sleep(3000);
await say("Will fail. The verdict, the truth value and the revenue at risk.");
await hush(200);
await scroll(".fixes", null, "start");
await say("The smallest fix: attach the pre-authorisation reference.");
await hush(200);
await scroll(".trace-section", null, "start");
await say("Eleven checks. Ten passed. Pre-authorisation failed.");
await hush(200);
await click(".trace__step--fail .chip");
await sleep(1600);
await say("Regulation 60: specialised services need pre-authorisation, except in an emergency.");
await hush(200);
await click("dialog[open] .dialog__close");
await sleep(700);

await b.eval("window.scrollTo({top:0,behavior:'smooth'})");
await sleep(1200);
await click(".fix .btn--solid");
await sleep(3000);
await say("Applying the fix re-runs the rules. The claim passes, and the placeholder is flagged.");
await hush(200);

await scroll(".narration", null, "center");
await click(".narration .segmented button", "Kiswahili");
await sleep(2000);
await say("Also in Kiswahili. The model only explains, and never changes the verdict.");
await hush(200);

await scroll(".audit", null, "center");
await click(".audit .btn--soft");
await sleep(3000);
await say("Run it again: identical trace hash, chained in a tamper-evident log.");
await hush(200);

await click("a.rail__link", "Overview");
await sleep(3800);
await say("The fixed claim now counts as revenue protected.");
await hush(300);

await card(`<h1 style="font-size:64px">Hakiki</h1><ul><li>Every verdict cites the SHA regulation behind it</li><li>Reproducible, hash-chained audit log</li><li>The language model explains, and never decides</li><li>Patient data is pseudonymised on arrival</li></ul><p style="font-size:20px;margin-top:20px">github.com/ByteGigs-Labs/hakiki-claims</p>`, 5000);

await b.send("Page.stopScreencast");
await sleep(500);
writeFileSync(`${FRAMES}/index.json`, JSON.stringify(frames));
console.log("frames:", frames.length, "seconds:", (frames.at(-1).ts - frames[0].ts).toFixed(1));
for (const e of b.events) if (e.method === "Runtime.exceptionThrown") console.log(JSON.stringify(e.params).slice(0, 300));
b.close();
