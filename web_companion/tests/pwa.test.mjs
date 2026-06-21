import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const ROOT = new URL("../", import.meta.url);

test("index.html wires manifest, icons, and module app bootstrap", async () => {
  const html = await readFile(new URL("index.html", ROOT), "utf8");
  assert.match(html, /rel="manifest" href="\.\/*manifest\.webmanifest"/);
  assert.match(html, /rel="apple-touch-icon" href="\.\.\/UniversalMailCleaner_icon\.png"/);
  assert.match(html, /<script type="module" src="\.\/app\.js"><\/script>/);
});

test("manifest keeps standalone companion metadata", async () => {
  const manifest = JSON.parse(
    await readFile(new URL("manifest.webmanifest", ROOT), "utf8"),
  );
  assert.equal(manifest.name, "UniversalMailCleaner Companion");
  assert.equal(manifest.display, "standalone");
  assert.equal(manifest.start_url, "./index.html");
  assert.equal(manifest.icons[0].src, "../UniversalMailCleaner_icon.png");
});

test("service worker caches the app shell and icon", async () => {
  const sw = await readFile(new URL("sw.js", ROOT), "utf8");
  assert.match(sw, /const CACHE_NAME = "umc-web-companion-v1"/);
  assert.match(sw, /"\.\/library\.mjs"/);
  assert.match(sw, /"\.\.\/UniversalMailCleaner_icon\.png"/);
  assert.match(sw, /self\.skipWaiting\(\)/);
  assert.match(sw, /self\.clients\.claim\(\)/);
});
