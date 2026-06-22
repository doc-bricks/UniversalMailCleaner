import test from "node:test";
import assert from "node:assert/strict";
import { readFile, access } from "node:fs/promises";
import { constants } from "node:fs";

const ROOT = new URL("../", import.meta.url);

test("index.html wires manifest, icons, and module app bootstrap", async () => {
  const html = await readFile(new URL("index.html", ROOT), "utf8");
  assert.match(html, /rel="manifest" href="\.\/*manifest\.webmanifest"/);
  assert.match(html, /rel="apple-touch-icon"/);
  assert.match(html, /icons\/apple-touch-icon-180\.png/);
  assert.match(html, /<script type="module" src="\.\/app\.js"><\/script>/);
});

test("manifest keeps standalone companion metadata with split icons", async () => {
  const manifest = JSON.parse(
    await readFile(new URL("manifest.webmanifest", ROOT), "utf8"),
  );
  assert.equal(manifest.name, "UniversalMailCleaner Companion");
  assert.equal(manifest.display, "standalone");
  assert.equal(manifest.start_url, "./index.html");
  const anyIcons = manifest.icons.filter((i) => i.purpose === "any");
  const maskableIcons = manifest.icons.filter((i) => i.purpose === "maskable");
  assert.ok(anyIcons.length >= 2, "at least 2 any-purpose icons");
  assert.ok(maskableIcons.length >= 2, "at least 2 maskable icons");
  assert.ok(
    anyIcons.some((i) => i.sizes === "192x192"),
    "any icon includes 192x192",
  );
  assert.ok(
    anyIcons.some((i) => i.sizes === "512x512"),
    "any icon includes 512x512",
  );
});

test("service worker caches the app shell at v2", async () => {
  const sw = await readFile(new URL("sw.js", ROOT), "utf8");
  assert.match(sw, /const CACHE_NAME = "umc-web-companion-v2"/);
  assert.match(sw, /"\.\/library\.mjs"/);
  assert.match(sw, /"\.\/icons\/icon-192\.png"/);
  assert.match(sw, /self\.skipWaiting\(\)/);
  assert.match(sw, /self\.clients\.claim\(\)/);
});

test("SW fetch handler includes offline fallback .catch()", async () => {
  const sw = await readFile(new URL("sw.js", ROOT), "utf8");
  assert.match(sw, /\.catch\(/);
  assert.match(sw, /caches\.match\("\.\/index\.html"\)/);
});

test("index.html includes iOS meta tags", async () => {
  const html = await readFile(new URL("index.html", ROOT), "utf8");
  assert.match(html, /name="apple-mobile-web-app-title"/);
  assert.match(html, /content="UMC Companion"/);
  assert.match(html, /name="apple-mobile-web-app-status-bar-style"/);
  assert.match(html, /content="default"/);
});

test("index.html does not use deprecated apple-mobile-web-app-capable", async () => {
  const html = await readFile(new URL("index.html", ROOT), "utf8");
  assert.doesNotMatch(html, /apple-mobile-web-app-capable/);
});

test("index.html has viewport-fit=cover for iOS notch", async () => {
  const html = await readFile(new URL("index.html", ROOT), "utf8");
  assert.match(html, /viewport-fit=cover/);
});

test("CSS uses safe-area-inset for notch/home-bar", async () => {
  const css = await readFile(new URL("app.css", ROOT), "utf8");
  assert.match(css, /env\(safe-area-inset-top/);
  assert.match(css, /env\(safe-area-inset-bottom/);
});

test("buttons meet Apple HIG 44px touch target", async () => {
  const css = await readFile(new URL("app.css", ROOT), "utf8");
  assert.match(css, /min-height:\s*44px/);
});

test("dedicated icon files exist on disk", async () => {
  const icons = [
    "icons/icon-192.png",
    "icons/icon-512.png",
    "icons/icon-maskable-192.png",
    "icons/icon-maskable-512.png",
    "icons/apple-touch-icon-180.png",
  ];
  for (const icon of icons) {
    await access(new URL(icon, ROOT), constants.R_OK);
  }
});
