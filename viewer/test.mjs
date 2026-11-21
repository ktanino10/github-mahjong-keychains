import { chromium } from "playwright";
import { mkdir, readFile, unlink, writeFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import assert from "node:assert/strict";

const root = dirname(fileURLToPath(import.meta.url));
const project = dirname(root);
const url = pathToFileURL(join(project, "docs/index.html")).href;
const screenshots = join(project, "docs/images");
const scratch = join(project, ".work/browser");
await mkdir(screenshots, { recursive: true });
await mkdir(scratch, { recursive: true });
const launchOptions = process.env.CHROME_PATH
  ? { executablePath: process.env.CHROME_PATH, headless: true }
  : { channel: "chrome", headless: true };
const browser = await chromium.launch({
  ...launchOptions,
});
const failures = [];
const captureDiagnostics = [];
const requests = [];
const results = [];
const track = (page) => {
  page.on("pageerror", (error) => failures.push(error.message));
  page.on("console", (message) => {
    if (!["error", "warning"].includes(message.type())) return;
    const text = message.text();
    // Chromium may report its own GPU readback stall during screenshot capture.
    if (message.type() === "warning" && /^\[\.WebGL-0x[\da-f]+\]GL Driver Message .*GPU stall due to ReadPixels/.test(text)) {
      captureDiagnostics.push(text);
    } else {
      failures.push(text);
    }
  });
  page.on("request", (request) => {
    if (/^https?:/.test(request.url())) requests.push(request.url());
  });
};
const ready = (page) => page.locator('body[data-state="ready"]').waitFor({ timeout: 45000 });
const number = async (page, name) => Number(await page.locator("#viewport").getAttribute(`data-${name}`));
const angularDistance = (a, b) => Math.abs(((a - b + 540) % 360) - 180);
const select = async (page, value) => {
  await page.locator(".design-choice").filter({ has: page.locator(`input[value="${value}"]`) }).click();
  assert.equal(await page.locator("#viewport").getAttribute("data-selection"), value);
};
const snapshot = async (page, name) => {
  await page.evaluate(() => document.fonts.ready);
  const directory = name.startsWith("viewer-") ? screenshots : scratch;
  await page.screenshot({ path: join(directory, name), fullPage: true });
};

try {
  const context = await browser.newContext({ viewport: { width: 1440, height: 1050 }, deviceScaleFactor: 1, offline: true });
  const page = await context.newPage();
  track(page);
  await page.goto(url);
  await ready(page);
  assert.equal(await number(page, "meshes"), 14);
  assert.equal(await number(page, "designs"), 4);
  assert.equal(await page.locator("#viewport").getAttribute("data-selection"), "all");
  assert.equal(await page.locator("#show-hardware").isChecked(), true);
  assert.equal(await page.locator("#auto-rotate").getAttribute("aria-pressed"), "false");
  assert.equal(await page.locator("#poster").isVisible(), false);
  assert.deepEqual(await page.locator(".specs dd").allTextContents(), ["21 × 28", "16.5", "5.5", "5.0", "Ø 4.6", "36"]);
  assert.ok((await page.locator(".spec-note").textContent()).includes("耳全体は黒"));
  assert.equal(await page.locator("#hardware-type").inputValue(), "ball");
  assert.equal(await page.locator("#viewport").getAttribute("data-hardware-type"), "ball");
  assert.ok((await page.locator("#hardware-note").textContent()).includes("2.4 mm"));
  const structural = await page.evaluate(() => ({
    overflow: document.documentElement.scrollWidth - innerWidth,
    headings: [...document.querySelectorAll("h1")].map((node) => node.textContent),
    invalidControls: [...document.querySelectorAll("button")].filter((button) => !button.textContent?.trim() && !button.getAttribute("aria-label")).length,
    externalSources: [...document.querySelectorAll("script[src], link[rel=stylesheet], img")].filter((node) => /^(http|\/\/)/.test(node.getAttribute("src") ?? node.getAttribute("href") ?? "")).length,
  }));
  assert.ok(structural.overflow <= 1, structural);
  assert.equal(structural.headings.length, 1);
  assert.equal(structural.invalidControls, 0);
  assert.equal(structural.externalSources, 0);
  results.push("Offline first load: four models, fourteen exact printed parts, named controls, no external assets.");
  await snapshot(page, "viewer-ja-ball-chain.png");

  await page.getByRole("button", { name: "表", exact: true }).click();
  assert.ok(angularDistance(await number(page, "angle"), 0) < 0.5);
  await page.getByRole("button", { name: "裏", exact: true }).click();
  assert.ok(angularDistance(await number(page, "angle"), 180) < 0.5);
  await snapshot(page, "desktop-backs.png");
  await page.getByRole("button", { name: "側面", exact: true }).click();
  assert.ok(angularDistance(await number(page, "angle"), 90) < 0.5);
  await page.getByRole("button", { name: "表", exact: true }).click();
  const canvas = page.locator("canvas.three-canvas");
  await canvas.focus();
  const angles = [];
  for (let i = 0; i < 36; i++) {
    await canvas.press("ArrowRight");
    angles.push(await number(page, "angle"));
  }
  assert.ok(angles.some((angle) => angularDistance(angle, 90) < 0.5));
  assert.ok(angles.some((angle) => angularDistance(angle, 180) < 0.5));
  assert.ok(angles.some((angle) => angularDistance(angle, 270) < 0.5));
  assert.ok(angularDistance(angles.at(-1), 0) < 0.5);
  results.push("Front/back/side presets and a complete keyboard-controlled 360-degree revolution.");

  const bounds = await canvas.boundingBox();
  assert.ok(bounds);
  const beforeDrag = await number(page, "angle");
  await page.mouse.move(bounds.x + bounds.width * 0.62, bounds.y + bounds.height * 0.50);
  await page.mouse.down();
  await page.mouse.move(bounds.x + bounds.width * 0.38, bounds.y + bounds.height * 0.52, { steps: 15 });
  await page.mouse.up();
  await page.waitForTimeout(700);
  assert.ok(angularDistance(await number(page, "angle"), beforeDrag) > 20);
  const beforeWheel = await number(page, "distance");
  await page.mouse.wheel(0, -280);
  await page.waitForTimeout(600);
  assert.ok(await number(page, "distance") < beforeWheel);
  await page.getByRole("button", { name: "全体を見る", exact: true }).click();
  const beforeButton = await number(page, "distance");
  await page.getByRole("button", { name: "拡大する", exact: true }).click();
  assert.ok(await number(page, "distance") < beforeButton * 0.9);
  await page.getByRole("button", { name: "縮小する", exact: true }).click();
  assert.ok(Math.abs((await number(page, "distance")) - beforeButton) < 0.05);
  results.push("Native pointer dragging, wheel zoom and accessible zoom buttons.");

  for (const id of ["git_branch", "octocat", "hatsu"]) await select(page, id);
  assert.equal(await page.locator("#color-count").textContent(), "4色");
  assert.equal(await page.locator("#light-green-chip").isVisible(), true);
  assert.equal(await page.locator("#red-chip").isVisible(), false);
  await page.getByRole("checkbox", { name: /金具を表示/ }).uncheck();
  assert.equal(await page.locator("#viewport").getAttribute("data-hardware"), "false");
  await page.getByRole("button", { name: "斜め", exact: true }).click();
  await snapshot(page, "hatsu-without-chain.png");
  await select(page, "chun");
  assert.equal(await page.locator("#color-count").textContent(), "3色");
  assert.equal(await page.locator("#green-chip").isVisible(), false);
  assert.equal(await page.locator("#light-green-chip").isVisible(), false);
  assert.equal(await page.locator("#red-chip").isVisible(), true);
  assert.ok((await page.locator(".print-split").textContent()).includes("別プロジェクト"));
  assert.ok((await page.locator(".print-split").textContent()).includes("4スロットAMS"));
  assert.match(await page.locator('[data-i18n="downloadChun"]').getAttribute("href"), /\/chun-P1S-0\.2-AMS-PLA\.3mf$/);
  assert.match(await page.locator('[data-i18n="downloadAll"]').getAttribute("href"), /\/all-three-P1S-0\.2-AMS-PLA\.3mf$/);
  assert.match(await page.locator('[data-i18n="downloadBundle"]').getAttribute("href"), /github-mahjong-keychains-P1S-0\.2-AMS-PLA\.zip$/);
  assert.ok((await canvas.getAttribute("aria-label")).includes("黒い円形Invertocat"));
  assert.equal(await page.locator('[data-i18n="chunDetail"]').textContent(), "赤い中＋黒い円形Invertocat");
  await page.getByRole("checkbox", { name: /金具を表示/ }).check();
  await page.getByRole("button", { name: "表", exact: true }).click();
  await snapshot(page, "viewer-ja-chun.png");
  await page.getByRole("button", { name: "English", exact: true }).click();
  assert.equal(await page.locator("#selection-name").textContent(), "Red Chun / Black circular Invertocat");
  assert.equal(await page.locator("#color-count").textContent(), "3 colors");
  assert.ok((await page.locator(".print-split").textContent()).includes("5 colors"));
  assert.ok((await page.locator(".print-split").textContent()).includes("physical red spool"));
  assert.ok((await page.locator('[data-i18n="downloadChun"]').textContent()).includes("separate"));
  assert.ok((await canvas.getAttribute("aria-label")).includes("Black circular Invertocat"));
  assert.equal(await page.locator('[data-i18n="chunDetail"]').textContent(), "Red Chun + black circular Invertocat");
  await snapshot(page, "viewer-en-chun.png");
  await page.getByRole("button", { name: "日本語", exact: true }).click();
  await page.getByRole("checkbox", { name: /金具を表示/ }).uncheck();
  results.push("Chun names the red glyph and black circular Invertocat in both languages, has white/black/red only, a separate three-color download, unchanged all-three URL and an explicit five-color/four-slot AMS warning.");
  await select(page, "octocat");
  assert.equal(await page.locator("#green-chip").isVisible(), false);
  assert.equal(await page.locator("#light-green-chip").isVisible(), false);
  assert.equal(await page.locator("#red-chip").isVisible(), false);
  await page.getByRole("button", { name: "裏", exact: true }).click();
  await snapshot(page, "octocat-back-closeup.png");
  await select(page, "all");
  assert.equal(await page.locator("#red-chip").isVisible(), true);
  assert.equal(await page.locator("#color-count").textContent(), "計5色");
  await page.getByRole("checkbox", { name: /金具を表示/ }).check();
  results.push("All design selectors, chain removal/re-fit, color count and black back close-up.");

  const beforeSpin = await number(page, "angle");
  await page.locator("#auto-rotate").click();
  assert.equal(await page.locator("#auto-rotate").getAttribute("aria-pressed"), "true");
  await page.waitForTimeout(1600);
  const afterSpin = await number(page, "angle");
  assert.ok(angularDistance(afterSpin, beforeSpin) > 3, { beforeSpin, afterSpin });
  await page.locator("#auto-rotate").click();
  await page.waitForTimeout(1000);
  const paused = await number(page, "angle");
  await page.waitForTimeout(500);
  assert.ok(angularDistance(await number(page, "angle"), paused) < 0.2);
  results.push("Auto rotation starts and really stops.");

  await page.locator("#hardware-type").selectOption("clasp");
  assert.equal(await page.locator("#viewport").getAttribute("data-hardware-type"), "clasp");
  assert.ok((await page.locator("#hardware-note").textContent()).includes("適合は未確認"));
  await select(page, "git_branch");
  await page.locator('[data-view="angle"]').click();
  const beforeLanguage = await number(page, "angle");
  await page.getByRole("button", { name: "English", exact: true }).click();
  assert.equal(await page.locator("html").getAttribute("lang"), "en");
  assert.equal(await page.title(), "Mahjong keychains — 360° viewer");
  assert.equal(await page.locator("#viewport").getAttribute("data-selection"), "git_branch");
  assert.equal(await page.locator("#viewport").getAttribute("data-hardware-type"), "clasp");
  assert.ok(angularDistance(await number(page, "angle"), beforeLanguage) < 0.05);
  assert.ok((await page.locator("#hardware-note").textContent()).includes("unverified"));
  assert.equal(await page.locator("#color-count").textContent(), "3 colors");
  assert.ok((await canvas.getAttribute("aria-label")).includes("arrow keys"));
  assert.ok((await page.locator("#poster").getAttribute("alt")).includes("ball chains"));
  const untranslated = await page.evaluate(() => {
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    const remaining = [];
    while (walker.nextNode()) {
      const node = walker.currentNode;
      if (node.parentElement.closest("script, style, pre, noscript, [lang=ja], [aria-hidden=true]")) continue;
      if (/[\u3040-\u30ff\u4e00-\u9fff]/u.test(node.textContent)) remaining.push(node.textContent.trim());
    }
    return remaining;
  });
  assert.deepEqual(untranslated, [], "Japanese interface text remains in English mode.");
  await snapshot(page, "viewer-en-swivel-clasp.png");
  await select(page, "all");
  await page.locator("#hardware-type").selectOption("ball");
  assert.ok((await page.locator("#hardware-note").textContent()).includes("120 mm"));
  await page.locator('[data-view="angle"]').click();
  await snapshot(page, "viewer-en-ball-chain.png");
  assert.ok((await page.locator("body").ariaSnapshot()).includes("Show hardware"));
  for (const [id, colors] of [["octocat", "2 colors"], ["hatsu", "4 colors"], ["chun", "3 colors"], ["all", "5 total colors"]]) {
    await select(page, id);
    assert.equal(await page.locator("#color-count").textContent(), colors);
  }
  await page.locator("#auto-rotate").click();
  assert.equal(await page.locator("#rotation-state").textContent(), "On");
  await page.locator("#auto-rotate").click();
  assert.equal(await page.locator("#rotation-state").textContent(), "Off");
  results.push("Full English translation, accessible names, dynamic color/rotation/selection states, purchased hardware switching and preserved view state.");

  const downloadPromise = page.waitForEvent("download");
  await page.getByRole("button", { name: "Save HTML", exact: true }).click();
  const download = await downloadPromise;
  const saved = join(scratch, "download-roundtrip.html");
  await download.saveAs(saved);
  const savedText = await readFile(saved, "utf8");
  assert.ok(savedText.includes('id="model-data"'));
  await page.goto(pathToFileURL(saved).href);
  await ready(page);
  assert.equal(await page.locator("#viewport").getAttribute("data-selection"), "all");
  assert.equal(await page.locator("html").getAttribute("lang"), "en");
  await page.getByRole("button", { name: "日本語", exact: true }).click();
  assert.equal(await page.locator("#color-count").textContent(), "計5色");
  assert.equal(await page.locator("#selection-name").textContent(), "4種類を並べて表示");
  assert.ok((await page.locator("#hardware-note").textContent()).includes("球径2.4 mm"));
  await unlink(saved);
  results.push("Downloaded HTML reopens offline in the chosen language and switches back to Japanese.");
  await context.close();

  const mobileContext = await browser.newContext({
    viewport: { width: 390, height: 844 }, deviceScaleFactor: 1,
    isMobile: true, hasTouch: true, reducedMotion: "reduce", offline: true,
  });
  const mobile = await mobileContext.newPage();
  track(mobile);
  await mobile.goto(url);
  await ready(mobile);
  const mobileLayout = await mobile.evaluate(() => ({
    overflow: document.documentElement.scrollWidth - innerWidth,
    canvas: document.querySelector("canvas").getBoundingClientRect().toJSON(),
    hint: getComputedStyle(document.querySelector(".touch-hint")).display,
  }));
  assert.ok(mobileLayout.overflow <= 1, mobileLayout);
  assert.ok(mobileLayout.canvas.width >= 350 && mobileLayout.canvas.height >= 340, mobileLayout);
  assert.notEqual(mobileLayout.hint, "none");
  assert.equal(await mobile.locator(".touch-hint").isVisible(), true);
  assert.equal(await mobile.locator("#auto-rotate").getAttribute("aria-pressed"), "false");
  const stable = await number(mobile, "angle");
  await mobile.waitForTimeout(500);
  assert.ok(angularDistance(await number(mobile, "angle"), stable) < 0.05);
  await snapshot(mobile, "mobile-all-four.png");
  await select(mobile, "chun");
  assert.equal(await mobile.locator("#red-chip").isVisible(), true);
  assert.equal(await mobile.locator("#green-chip").isVisible(), false);
  await select(mobile, "git_branch");
  await mobile.getByRole("checkbox", { name: /金具を表示/ }).uncheck();
  await mobile.getByRole("button", { name: "裏", exact: true }).click();
  assert.ok(angularDistance(await number(mobile, "angle"), 180) < 0.5);
  const mobileCanvas = mobile.locator("canvas.three-canvas");
  await mobileCanvas.scrollIntoViewIfNeeded();
  const mobileBox = await mobileCanvas.boundingBox();
  assert.ok(mobileBox);
  const touch = await mobileContext.newCDPSession(mobile);
  const centerX = mobileBox.x + mobileBox.width / 2;
  const centerY = mobileBox.y + mobileBox.height / 2;
  const beforeTouch = await number(mobile, "angle");
  await touch.send("Input.dispatchTouchEvent", { type: "touchStart", touchPoints: [{ x: centerX + 45, y: centerY }] });
  for (let step = 1; step <= 8; step++) {
    await touch.send("Input.dispatchTouchEvent", { type: "touchMove", touchPoints: [{ x: centerX + 45 - step * 12, y: centerY }] });
  }
  await touch.send("Input.dispatchTouchEvent", { type: "touchEnd", touchPoints: [] });
  assert.ok(angularDistance(await number(mobile, "angle"), beforeTouch) > 15);
  const beforePinch = await number(mobile, "distance");
  await touch.send("Input.dispatchTouchEvent", {
    type: "touchStart", touchPoints: [{ x: centerX - 30, y: centerY, id: 0 }, { x: centerX + 30, y: centerY, id: 1 }],
  });
  for (let step = 1; step <= 6; step++) {
    await touch.send("Input.dispatchTouchEvent", {
      type: "touchMove",
      touchPoints: [{ x: centerX - 30 - step * 6, y: centerY, id: 0 }, { x: centerX + 30 + step * 6, y: centerY, id: 1 }],
    });
  }
  await touch.send("Input.dispatchTouchEvent", { type: "touchEnd", touchPoints: [] });
  assert.ok(await number(mobile, "distance") < beforePinch);
  await touch.detach();
  await mobile.getByRole("button", { name: "English", exact: true }).click();
  assert.ok(await mobile.evaluate(() => document.documentElement.scrollWidth - innerWidth <= 1));
  await mobile.locator("#hardware-type").selectOption("clasp");
  await mobile.getByRole("checkbox", { name: /Show hardware/ }).check();
  await mobile.locator('[data-view="angle"]').click();
  await snapshot(mobile, "viewer-mobile-en.png");
  for (const width of [320, 600, 800]) {
    await mobile.setViewportSize({ width, height: 844 });
    assert.ok(await mobile.evaluate(() => document.documentElement.scrollWidth - innerWidth <= 1), `Horizontal overflow at ${width}px`);
    assert.equal(await mobile.locator('input[name="design"]').count(), 5);
  }
  results.push("390 px mobile layout, reduced motion, native touch rotation and pinch zoom.");
  await mobileContext.close();
} finally {
  await browser.close();
}

assert.deepEqual(requests, [], "The standalone viewer made an external request.");
assert.deepEqual(failures, [], "Browser errors or warnings were observed.");
const fallbackBrowser = await chromium.launch({ ...launchOptions, args: ["--disable-webgl"] });
try {
  const page = await fallbackBrowser.newPage({ viewport: { width: 1100, height: 850 } });
  await page.goto(url);
  await page.locator('body[data-state="error"]').waitFor({ timeout: 15000 });
  assert.equal(await page.locator("#error").isVisible(), true);
  assert.equal(await page.locator("#poster").isVisible(), true);
  assert.equal(await page.locator("#auto-rotate").isDisabled(), true);
  await page.getByRole("button", { name: "English", exact: true }).click();
  assert.equal(await page.locator("#error-title").textContent(), "3D is unavailable in this environment");
  assert.ok((await page.locator("#error-message").textContent()).includes("hardware acceleration"));
  assert.equal(await page.locator("#reload").textContent(), "Reload page");
  await snapshot(page, "webgl-unavailable.png");
  results.push("WebGL-unavailable state: explicit error, labeled static preview, disabled 3D controls.");
} finally {
  await fallbackBrowser.close();
}
await writeFile(join(project, "validation/browser-checks.json"), JSON.stringify({
  results, applicationConsoleErrorsOrWarnings: failures,
  screenshotDriverReadbackDiagnostics: captureDiagnostics.length, externalRequests: requests,
  testedFromLocalFile: true, offline: true,
}, null, 2));
console.log(results.join("\n"));
