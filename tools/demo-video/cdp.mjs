import { spawn } from "node:child_process";
import { writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

export async function launch(width = 1440, height = 900, port = 9333) {
  const chrome = spawn(process.env.CHROME ?? "google-chrome", [
    "--headless=new", "--no-sandbox", "--ignore-certificate-errors", "--disable-gpu", `--remote-debugging-port=${port}`,
    `--window-size=${width},${height}`, "--user-data-dir=" + join(tmpdir(), "hk-chrome-" + port), "about:blank",
  ], { stdio: "ignore" });
  let info;
  for (let i = 0; i < 50; i++) {
    try { info = await (await fetch(`http://127.0.0.1:${port}/json`)).json(); if (info.length) break; } catch {}
    await new Promise((r) => setTimeout(r, 200));
  }
  const ws = new WebSocket(info.find((t) => t.type === "page").webSocketDebuggerUrl);
  await new Promise((r) => (ws.onopen = r));
  let id = 0; const pending = new Map(); const events = []; let handler = null;
  ws.onmessage = (m) => { const d = JSON.parse(m.data); if (d.id && pending.has(d.id)) { pending.get(d.id)(d); pending.delete(d.id); } else if (handler && handler(d)) {} else events.push(d); };
  const send = (method, params = {}) => new Promise((res, rej) => { const i = ++id; pending.set(i, (d) => d.error ? rej(new Error(JSON.stringify(d.error))) : res(d.result)); ws.send(JSON.stringify({ id: i, method, params })); });
  await send("Page.enable"); await send("Runtime.enable");
  await send("Emulation.setDeviceMetricsOverride", { width, height, deviceScaleFactor: 1, mobile: width < 700 });
  const api = {
    send, events, onEvent(fn) { handler = fn; },
    async goto(url) { await send("Page.navigate", { url }); await api.sleep(1200); },
    sleep: (ms) => new Promise((r) => setTimeout(r, ms)),
    async eval(expr) { const r = await send("Runtime.evaluate", { expression: expr, awaitPromise: true, returnByValue: true }); if (r.exceptionDetails) throw new Error(JSON.stringify(r.exceptionDetails)); return r.result.value; },
    async shot(file, full = false) {
      let clip;
      if (full) { const h = await api.eval("document.documentElement.scrollHeight"); await send("Emulation.setDeviceMetricsOverride", { width, height: Math.min(h, 4000), deviceScaleFactor: 1, mobile: width < 700 }); await api.sleep(300); }
      const r = await send("Page.captureScreenshot", { format: "png" });
      writeFileSync(file, Buffer.from(r.data, "base64"));
      if (full) await send("Emulation.setDeviceMetricsOverride", { width, height, deviceScaleFactor: 1, mobile: width < 700 });
    },
    async type(selector, text) { await api.eval(`(()=>{const el=document.querySelector(${JSON.stringify(selector)}); el.focus(); const set=Object.getOwnPropertyDescriptor(el.__proto__,'value').set; set.call(el, ${JSON.stringify(text)}); el.dispatchEvent(new Event('input',{bubbles:true}));})()`); },
    async click(selector) { await api.eval(`document.querySelector(${JSON.stringify(selector)}).click()`); },
    async clickText(text, tag = "button") { await api.eval(`[...document.querySelectorAll(${JSON.stringify(tag)})].find(e=>e.textContent.trim().includes(${JSON.stringify(text)})).click()`); },
    close() { ws.close(); chrome.kill(); },
  };
  return api;
}
