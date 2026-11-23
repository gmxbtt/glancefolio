# Heads Up: Even Realities — DESIGN.md

> **Status:** PREP ONLY (19 Nov 2026). No core app code has been written — hackathon
> rules require all core app code to be written during build week (23–29 Nov 2026).
> This file is the design + research record. The scaffold in `app/` is the untouched
> official minimal template (its `src/main.ts` is the template's own "Hello from G2!"
> starter, not our app).

## 1. Concept

- **Working name:** **Glancefolio** (name ≤ 20 chars, fits the `app.json` limit).
  Alternatives: `RadarLens`, `Pingfolio`.
- **One-line pitch:** Your crypto portfolio and price alerts, readable in one glance
  on Even G2 glasses — no phone in your hand.
- **Track:** 2 — Crypto & Wallet. **Also qualifies for Best Telegram ($1,000,
  stackable)** via the Telegram bot integration (see §4).
- **Why it can win:** Usefulness 30% (crypto holders check prices 20×/day) +
  G2 Experience 25% (designed glance-first, not a phone screen shrunk down) +
  Innovation 20% (no Even Hub app today combines portfolio + threshold alerts +
  Telegram delivery — see §6).

## 2. Glanceable screens (all text-first, native text containers)

Display is **576×288, 16 green shades, 27 px line height** → ~10 lines max per
screen. Every screen must be readable in ≤ 2 seconds. Navigation: swipe =
move cursor one item; tap = open; double-tap = one level up (root = exit dialog).

| # | Screen | Content (one glance) |
|---|--------|----------------------|
| 1 | **Portfolio** (home) | Total value (1 line, big), 24h change `▲/▼ $x (+y%)`, top 3 holdings `BTC $63.1k ▲1.0%` — one row each. Cursor moves between holdings; tap → detail. |
| 2 | **Alerts** | List of armed alerts, one per row: `● BTC > $70,000` / `○ SOL < $70`. Fired alerts show `✓` + time. Tap an alert → arm/disarm. Max ~7 rows visible (native list ≤ 20 items, ≤ 64 UTF-8 bytes each — but native lists emit NO selection events on real glasses, so use app-owned text rows with own cursor state). |
| 3 | **Coin detail** | `BTC $63,061` / `24h ▲0.99% · Hi 64.0k Lo 62.3k` / `Hold 0.42 · $26.5k` / `Alert >70k ●`. Tap cycles: set alert above / below / off (step sizes from current price). |
| 4 | **Watchlist / Movers** — **CUT Day 1 (23 Nov).** Adds nothing to the alert narrative (review Sev 5); do not rebuild. |

Design rules carried into build week:
- One invisible full-screen capture container (`content: ' '`, `isEventCapture: 1`,
  declared FIRST) so swipes never rubber-band visible containers.
- Single-container column pattern: each screen = ONE multi-line text container,
  screen changes = one atomic text update (no page rebuilds → no blinking).
- Cursor-first navigation: cursor is an absolute index; window derives from it.
- **Cursor rendering spec (Day 1, review Sev 2 fix):** the active row is
  prefixed `▶ `, inactive rows are prefixed with two spaces (same width, so
  text never shifts when the cursor moves). The cursor is an absolute index
  into the row list; the visible window is `start = clamp(cursor − VISIBLE + 1,
  0, max(0, rows − VISIBLE))`, so the active row is always on screen and the
  list scrolls only when the cursor leaves the window. On Screen 1 the
  cursorable rows are the holdings (VISIBLE = 3, whole list fits, window never
  scrolls yet); the header, totals, P&L, HOLD and status lines never take the
  cursor. A `HOLD <amount> <symbol> = <value>` line under the rows always
  reflects the cursor-selected holding, so the selection is visible even
  without a highlight colour (there is no colour — 16 green shades only).
- **P&L (Day 1 decision — keep the claim, add the line + formula):**
  `P&L = Σ (currentPrice − costBasis) × amount` over holdings with a cost
  basis; `P&L % = P&L ÷ Σ (costBasis × amount) × 100`. Holdings without a
  cost basis are excluded and the line reads `P&L — (set cost basis)`.
- Status vocabulary leads with a word (`HOLD / ALERT / FIRED / ERR`), not icon soup.
- Glyphs verified present on the glasses font: `● ○ ▶ ▷ ■ □ ✓ · …` (plus ▲▼ —
  verify on simulator before shipping; `⌖`/`▸` are ABSENT and render as nothing).
- Fit text by PIXELS (`@evenrealities/pretext`), never by character count.
- Keep ≥ 5 px slack inside containers or the scroll indicator flashes on every update.
- BLE budget: a text update costs 200–2000 ms on real glasses; design for
  ~2–5 updates/sec max. No animation, no per-second ticking.
- Serialize ALL bridge writes through ONE global promise chain; drop-not-queue.

## 3. Data sources (free price APIs — reachability verified from this VM, 19 Nov 2026)

| API | Reachability | Notes for the app |
|-----|--------------|-------------------|
| **CoinGecko** `api.coingecko.com/api/v3/simple/price` | ✅ HTTP 200, live (BTC $63,061 / ETH $1,778.11 / SOL $73.66, 24h %) | Primary. Free, no key. `simple/price` gives price + 24h change in one call. Poll ~60 s. |
| **Binance Vision** `data-api.binance.vision/api/v3/ticker/24hr?symbol=…` | ✅ HTTP 200, live (BTC $63,163.40 / SOL 24h stats) | Backup / 24h high-low. Single-symbol form only (multi-symbol array form failed). Note: `api.binance.com` is **HTTP 451 geo-blocked** from this VM — use the `.vision` mirror. |
| **Kraken** `api.kraken.com/0/public/Ticker` | ✅ HTTP 200, live | Second backup. |
| CoinCap `api.coincap.io` | ❌ HTTP 000 (unreachable from this VM) | Do NOT use. |

- **Rate budget (Day 1, review Sev 4 fix):** ≤1 CoinGecko call/min — one
  `simple/price` call covers BTC+ETH+SOL. Binance Vision only when CoinGecko
  fails (3 calls, one per symbol); Kraken only when both fail (1 call, 3
  pairs). The bot poll loop runs the same 60 s cadence independently, so worst
  case ≈ 2,880 calls/day across bot + glasses — inside the free tiers
  (CoinGecko free ≈ 10–30 calls/min). Never poll faster than 60 s on either
  side; tap-to-refresh is debounced 2 s.
- **Alert firing (hysteresis, review Sev 2 fix):** a level fires only after
  **2 consecutive polls** beyond it (60 s apart — kills wick false-fires),
  then a **15-minute per-alert cooldown** before it can re-fire; a fired alert
  stays FIRED until the user re-arms it or the price returns 1% inside the
  level (re-arm hysteresis).
- **CORS + permissions:** the app's `fetch()` calls need a `network` permission
  with a `whitelist` of the exact API hosts in `app.json` — and the whitelist does
  NOT bypass CORS, so the API must allow the origin (CoinGecko/Binance Vision/
  Kraken all serve `access-control-allow-origin: *` on these public endpoints;
  re-verify at build time from the phone WebView, not just curl).
- **Portfolio data:** holdings are entered on the phone (companion WebView page)
  or via the Telegram bot (`/add BTC 0.42`) and stored in local storage; prices
  come from the API above. No wallet connection, no private keys, no trading —
  read-only by design (also satisfies the hackathon's paper/testnet/read-only rule).

## 4. Telegram integration sketch (Best Telegram qualifier)

Goal: the app must genuinely USE Telegram (bot, Mini App, or Telegram API) —
that is what qualifies it for the $1,000 Best Telegram prize.

- **Bot (primary):** a Telegram bot (created via @BotFather during build week)
  is the alert-delivery + configuration channel:
  - `/price BTC` → current price + 24h change.
  - `/alert BTC above 70000` / `/alert SOL below 70` → arm an alert.
  - `/alerts` → list armed/fired alerts. `/portfolio` → holdings summary.
  - When a price crosses a level, the bot sends `🔔 BTC — price above $70,000`
    to the user. (Polling: a tiny serverless/worker or the phone app polls the
    price API every ~60 s and checks levels; the G2 app itself only reads the
    alert list when opened — see constraint below.)
- **G2 side:** the glasses app shows the same alert list + portfolio; arming/
  disarming from the glasses syncs to the bot's store (shared backend or the
  phone as the sync point). If sync turns out too costly in the week, fallback:
  alerts are configured in Telegram, displayed read-only on G2 (still a genuine
  Telegram-native flow).
- **Why not a Mini App:** a Mini App is a second web app to build and review;
  the bot + G2 app is one integration surface and matches the track examples
  ("Telegram bot for G2 (read messages, reply)").
- **Hard constraint — foreground-only plugins:** Even Hub plugins CANNOT push
  notifications to the lens. Alerts do NOT pop up on the glasses by themselves;
  the Telegram message lands on the phone, and the G2 app shows fired alerts
  when the user opens it. The design must not promise push-to-glass. The demo
  video must show the real flow: Telegram message arrives → open app on G2 →
  alert shown as FIRED.

## 5. Architecture (what runs where)

```
Telegram user ──► Bot (polls CoinGecko/Binance Vision ~60s, checks alert levels)
                     │  sends 🔔 on cross; stores alerts + holdings
                     ▼
Phone (Even app WebView) ──► G2 app (Vite + SDK, renders 576×288 text containers)
   │  fetches prices directly (network permission + whitelist) for live screens
   │  reads alerts/holdings from the bot backend (or local storage fallback)
   ▼
Even G2 glasses (BLE) ──► text containers only; taps/swipes back as events
```

- **Backend — DECIDED Day 1 (review Sev 3 fix):** a tiny Node worker on this
  VM (`bot/`, built Day 3) is the alert-polling host + Telegram long-poller,
  kept alive by a 15-minute keepalive check (same pattern as the project's
  other services). No new accounts, no cost. The bot's durable store is
  `bot/state.json` on the VM; it publishes the same state as
  `state/alerts.json` via **GitHub Pages** (public repo `gmxbtt/glancefolio`,
  created Day 3) so the phone WebView can fetch it. The glasses app reads
  that Pages URL when online and falls back to phone localStorage. The bot is
  the writer, the glasses are the reader — no live two-way sync on Day 1.
  If the worker is down, alerts simply don't fire (bot degrades) while the
  glasses keep working standalone with local holdings + direct price fetches.
- **Shared store — DECIDED Day 1 (review Sev 3 fix):** phone localStorage is
  the primary store for what the glasses show; the bot's `state.json` is the
  durable copy. One schema, two copies (see §13).
- **No backend fallback:** G2 app works standalone with local holdings + direct
  price fetches; Telegram features degrade gracefully (alerts list shows local
  state, bot sync marked OFF).

## 6. Catalogue gap check (19 Nov 2026)

- **Official catalogue** (`hub.evenrealities.com/catalogue`) is JS-rendered and
  could not be read by a text fetch — only the stub "Discover more in the Even
  Realities app" was returned. Gap analysis below is from web sources instead.
- **Even Hub size:** ~50 apps at launch (Apr 2026), **200+ plugins** by 13 Nov 2026
  (hinty.eu, checked against the public catalog that day).
- **Crypto/market apps that already exist:**
  - **EvenMarket** (open source, by fabioglimb) — live prices + candlestick charts
    for stocks, forex, crypto, ETFs. Closest competitor.
  - **ER Market** and **My Markets** — stocks and crypto (listed under "Markets").
  - **Stocks Indicator** — live portfolio monitoring.
- **What is missing (our opening):** none of the above is documented to do
  **threshold price alerts**, **Telegram bot delivery**, or **portfolio P&L with
  cost basis**. They are price *viewers*. Glancefolio owns *alerts + Telegram +
  portfolio in one glanceable flow* — and the Telegram leg is exactly what the
  stackable $1,000 prize rewards.
- **Risk:** EvenMarket is open source and could add alerts; our edge is the
  Telegram-native loop + the alert-first UX, not raw prices.

## 7. Hard platform constraints (from official docs + community skill)

Sources: `hub.evenrealities.com/docs` (Quickstart, Your First App) and
`github.com/pxi10/even-g2-development-skill` (SKILL.md, verified on real glasses
against SDK 0.0.10–0.0.12, simulator 0.7.3–0.8.0, manifest edition `202601`).
Full notes: `app/` scaffold + §2 above. The killers, in one list:

1. Display 576×288, 16 green shades, 27 px line height, proportional font.
2. ≤ 8 text containers, ≤ 4 image containers (each ≤ 288×144), ≤ 12 total per page;
   `containerName` ≤ 16 chars; exactly ONE container may set `isEventCapture: 1`.
3. `waitForEvenAppBridge()` MUST be awaited before any SDK call.
4. Protobuf omits zero-valued fields: CLICK (0) arrives as `eventType: undefined`
   — coalesce inside the envelope check, never assume a field exists.
5. Taps/double-taps/lifecycle arrive on `sysEvent`; swipes on `textEvent`.
6. Double-tap on the root page MUST call `shutDownPageContainer(1)` (system exit
   dialog). Mode 0 / custom exit UI is rejected in QA. (Community refinement:
   double-tap walks ONE level up; debounce the top-screen exit ~1.2 s.)
7. `app.json`: `package_id` lowercase reverse-domain, NO hyphens; `edition`
   `"202601"`; `name` ≤ 20 chars; `version` strict `x.y.z`; `permissions` is an
   array of `{name, desc[, whitelist]}`; network permission needs `whitelist`.
8. `textContainerUpgrade` = flicker-free text update; `rebuildPageContainer`
   only for layout changes. Same-shape rebuilds redraw near-seamlessly;
   shape-changing rebuilds visibly clear the screen — and on REAL glasses they
   also CLEAR image content (the simulator preserves it — a lie).
9. Images are a minefield: PNG dims must EXACTLY match the container; concurrent
   pushes wedge the BLE chunking (one global serial mutex); opaque compositing
   (never overlap image + text). Prefer native text; use images only if needed.
10. Simulator ≠ device: timings (sim ~1–30 ms vs BLE 200–2000 ms), image
    persistence, native-list events, `imuControl` rejected in sim 0.8.0.
11. Background: the Even app moves the WebView headless when the phone locks —
    implement `window.__getStateSnapshot` / `window.__restoreState`; re-create
    the page after N consecutive send failures (self-heal).
12. Packaging: `npm run build && evenhub pack app.json dist` → `.ehpk`. Bump
    `app.json` version on EVERY upload (portal rejects duplicates). Beta testing
    (email invite → Accept and install) is the deterministic install path;
    "In development → Open" serves a STALE cached copy — the trap that eats an
    afternoon. Put a build stamp (e.g. `b7`) on-glass and bump it every build.
13. Review: ~10 MB size cap; 5-minute locked-phone test; first-run behavior;
    privacy (no secrets in the client); the CLI has NO upload command — packaging
    + submission happen in the browser portal.

## 8. Build-week plan (23–29 Nov 2026)

| Day | Focus | Done when… |
|-----|-------|------------|
| Mon 23 Nov | **Day 1 — skeleton + data.** Rename scaffold (package_id `com.gmxbtt.glancefolio`, name `Glancefolio`), `network` permission + whitelist. Live price fetch (CoinGecko primary, Binance Vision fallback) rendering on Screen 1 in the simulator. BotFather bot created; `/price` working. | **DONE 23 Nov ~20:00 WIB** (code + decisions; BotFather still pending Derr — see §13). Simulator screenshot shows real BTC/ETH/SOL prices. |
| Tue 24 Nov | **Day 2 — screens + navigation.** Screens 1–3 as single-container columns; cursor-first nav; tap/double-tap routing; holdings entry (local storage). | **DONE 24 Nov ~00:00 WIB** (code + simulator verification; see §13). All 3 screens navigable by simulator `POST /api/input`. |
| Wed 25 Nov | **Day 3 — alerts engine.** Arm/disarm from glasses + bot commands; poll loop checks levels; Telegram 🔔 delivery working end-to-end. | A crossed level produces a real Telegram message + FIRED row on G2. |
| Thu 26 Nov | **Day 4 — polish.** Pixel-fit pass (`pretext`, deprioritised — fit only after screens work), glyph audit on simulator screenshots, ≥5 px slack, build stamp. Screen 4 CUT Day 1. | Screenshots of all screens verified readable. |
| Fri 27 Nov | **Day 5 — packaging + beta.** `npm run pack` → `.ehpk`; upload to Even Hub portal; beta invite → install on… (no real glasses in hand — verify via simulator + portal checks; note this honestly in the README). Fix review blockers. | `.ehpk` builds clean; portal accepts the build. |
| Sat 28 Nov | **Day 6 — demo video + submission draft.** Record ≤3-min demo video (simulator screen capture + real workflow), 3 screenshots, README, description, feature request for Even Hub. Submit to DoraHacks (draft). | Submission draft complete, video uploaded (YouTube/Vimeo). |
| Sun 29 Nov | **Day 7 — buffer + submit.** Fix anything found in review, re-record if needed, FINAL submit before 30 Nov 02:59 WIB. | Submission confirmed on DoraHacks. |

Daily rule: verify in the simulator headlessly after every change (`GET
/api/screenshot/glasses`), then kill the simulator. Never generalize from the
simulator what only real glasses can prove — say so in the README.

## 9. Submission checklist (deadline: 30 Nov 2026, 02:59 WIB)

- [ ] Public GitHub repo (`gmxbtt/…`) with README (setup, run, deploy).
- [ ] Demo video ≤ 3 min on YouTube/Vimeo, showing the app on the simulator
      (or real G2) doing a real workflow — must show the app running, not slides.
- [ ] Project description: what it does, who it is for, why it matters.
- [ ] Track selected: Crypto & Wallet (Telegram use noted for Best Telegram).
- [ ] 3 screenshots of the app on G2 / simulator.
- [ ] 1 feature request for Even Hub (candidate: push-to-glass for foreground
      plugins, or a real alert/notification channel for plugins).
- [ ] `app.json` final: package_id, name ≤ 20 chars, version bumped, network
      whitelist = the APIs actually used.
- [ ] All core code written 23–29 Nov (nothing from before build week except
      libraries/frameworks and this prep scaffold's template files).

## 10. Tooling verified (19 Nov 2026)

- Node **v24.22.1**, npm **10.9.4** (requirement: Node 20 LTS or 22+ ✅).
- Scaffold route: **`npx degit even-realities/evenhub-templates/minimal app`**
  (degit 3.10.1 auto-installed by npx; clone OK).
- `npm install` in `app/`: 83 packages, exit 0.
- Installed versions: SDK `@evenrealities/even_hub_sdk` **0.0.10**,
  CLI `@evenrealities/evenhub-cli` **0.1.14**, simulator
  `@evenrealities/evenhub-simulator` **0.7.3**, Vite **5.4.21**, TypeScript **5.9.3**.
- Dev server: `npm run dev` → Vite ready in ~371 ms, `http://localhost:5173/`
  serves index.html (HTTP 200) ✅.
- Production build: `npm run build` (tsc + vite) exit 0, `dist/` produced ✅.
- CLI: `./node_modules/.bin/evenhub --help` works (login / init / pack / qr).
- Packaging: `./node_modules/.bin/evenhub pack app.json dist` exit 0 →
  `out.ehpk` (30,387 bytes) ✅. **Warning to fix in build week:** the template's
  `app.json` sets `min_app_version 2.0.0`, below the floor 2.2.10 of SDK 0.0.16
  (the CLI's "latest"); it stamped 2.2.10. The template pins SDK ^0.0.10 while
  the current latest is 0.0.16 — decide on Day 1 whether to upgrade the SDK to
  latest (recommended: aligns `min_sdk_version`/`min_app_version` with the
  current platform) or pass `--sdk-ver 0.0.10` at pack time.
- Simulator: see §11.

## 11. Simulator verification — ✅ SUCCEEDED (19 Nov 2026, ~17:00 WIB)

- **First attempts failed (all observed, not assumed):**
  1. `npx evenhub-simulator …` → npm E404: npx resolved the unscoped name
     `evenhub-simulator`, which does not exist. Use the scoped package.
  2. `./node_modules/.bin/evenhub-simulator` → no such file: npm did NOT link
     the simulator bin (only `evenhub` is linked). The wrapper exists at
     `node_modules/@evenrealities/evenhub-simulator/bin/index.js` and delegates
     to the native binary in `@evenrealities/sim-linux-x64/bin/`.
  3. `node …/evenhub-simulator/bin/index.js --automation-port 18080
     http://localhost:5173` → exit 127: `libwebkit2gtk-4.1.so.0: cannot open
     shared object file`. The simulator is a GTK/WebKit desktop app; the VM
     lacked the library.
- **Fix (worked):** `apt-get update -o Acquire::Languages=none` (the full
  update stalled ~20 min on the huge Translation files through the egress
  proxy; `Languages=none` finished in 1m55s) then
  `apt-get install -y libwebkit2gtk-4.1-0` (64 newly installed + 4 upgraded,
  exit 0; `ldconfig -p` confirms `libwebkit2gtk-4.1.so.0`). Xvfb was already
  installed, so the simulator runs headless under `xvfb-run -a`.
- **Verified working commands:**
  ```bash
  cd ~/workspace/headsup-g2/app
  npm run dev                                   # Vite on :5173 (HTTP 200)
  xvfb-run -a node node_modules/@evenrealities/evenhub-simulator/bin/index.js \
      --automation-port 18080 http://localhost:5173
  curl http://localhost:18080/api/ping          # → "pong" (HTTP 200)
  curl http://localhost:18080/api/console        # → bridge init + "Page created: success"
  curl http://localhost:18080/api/screenshot/glasses   # → 576×288 RGBA PNG
  curl -X POST http://localhost:18080/api/input -d '{"action":"click"}'  # → {"ok":true}
  ```
- **Screenshots (visually inspected, both show green-on-black 576×288 text):**
  - `evidence/simulator-hello.png` — "Hello from G2! / Tap to count ·
    double-tap to exit." (raw RGBA: `simulator-hello-raw.png`)
  - `evidence/simulator-hello-click.png` — after one injected click:
    "Taps: 1 / Tap to count · double-tap to exit." — full round-trip
    (render → input → state update → re-render) confirmed.
  - Note: the screenshot API returns RGBA where ALPHA carries brightness —
    composite onto black to view (PIL `alpha_composite` used).
- **Cleanup:** simulator + dev server stopped after verification (both ports
  refuse connections). Restart with the commands above on Day 1.

## 12. Open items before build week

- [x] Simulator screenshot — DONE (§11, `evidence/simulator-hello*.png`).
- [x] DoraHacks pre-registration — DONE 19 Nov 23:58 WIB (solo, itaro91100).
- [x] Decide the alert-polling host (VM worker vs free serverless cron) — DECIDED Day 1: VM worker (`bot/`), see §5/§13.
- [x] Decide the shared store phone-app ↔ Telegram bot — DECIDED Day 1: localStorage primary + bot `state.json` published via GitHub Pages, see §5/§13.
- [ ] Telegram bot token: create via @BotFather on Day 1; token stays server-side.
  **Still open — needs Derr's own Telegram (@zafranneth); build does not block on it.**
- [ ] Confirm CoinGecko/Binance Vision CORS from a real phone WebView (curl
      proves the API, not the browser origin).
- [ ] Demo video: needs a screen recorder for the simulator window (check
      availability on the machine used for recording) + a voiceover/script.

## 13. Day 1 decisions log (23 Nov 2026, build week)

1. **Shared store (review Sev 3):** phone localStorage = primary store for
   what the glasses show; bot `state.json` (VM) = durable copy, published as
   `state/alerts.json` via GitHub Pages (`gmxbtt/glancefolio`, created Day 3).
   Bot writes, glasses read; localStorage fallback when offline.
2. **Alert-polling host (review Sev 3):** tiny Node worker on the VM
   (`bot/`, Day 3), 15-min keepalive. No new accounts, no cost.
3. **SDK version (review Sev 2):** upgrade to `@evenrealities/even_hub_sdk`
   **0.0.16** (from template 0.0.10). Core API unchanged (verified: template
   builds clean on 0.0.16; `OsEventTypeList` is a superset). `app.json`:
   `min_app_version 2.2.10`, `min_sdk_version 0.0.16`. Pack stamps 2.2.10.
4. **Storage schema `glancefolio:v1:*` (review Sev 4):**
   - `holdings`: `[{symbol, amount, costBasis}]` — costBasis in USD/unit,
     `null` = excluded from P&L.
   - `alerts`: `[{id, symbol, direction: 'above'|'below', price, armed, firedAt}]`
     (Day 3).
   - `settings`: `{pollSeconds: 60}` (15–600, validated on load).
5. **Rate budget (review Sev 4):** ≤1 CoinGecko call/min (one call, 3 coins);
   Binance Vision only on CG failure; Kraken only if both fail. Worst case
   ~2,880 calls/day total. Alert firing: 2 consecutive polls beyond the
   level + 15-min per-alert cooldown + 1% re-arm hysteresis.
6. **Cursor rendering (review Sev 2):** active row `▶ `, inactive rows two
   spaces; absolute cursor index; window `clamp(cursor − VISIBLE + 1, 0,
   max(0, rows − VISIBLE))`; HOLD line always shows the selected holding.
7. **Screen 4 Movers: CUT** (review Sev 5). Day 4 is polish only.
8. **P&L: keep the claim, add the line + formula** (review Sev 5):
   `P&L = Σ (price − costBasis) × amount`, `P&L % = P&L ÷ total cost × 100`.
9. **Pixel-fit (`pretext`): deprioritised** (review Sev 3) — fit after the
   screens work, Day 4 at the earliest.
10. **Double-tap UX (review Sev 3):** root double-tap exits via
    `shutDownPageContainer(1)`, debounced 1.2 s; simulator cannot prove real
    glasses timing — noted honestly in the README.
11. **Day 1 build delivered:** `app/` renamed (package_id
    `com.gmxbtt.glancefolio`, name Glancefolio), network permission +
    whitelist (CoinGecko, Binance Vision, Kraken), `src/main.ts` rewritten
    (Screen 1: live prices, total, P&L, cursor nav, tap-refresh, state
    snapshot/restore, self-heal re-create after 3 failed sends), `npm run
    build` clean, `evenhub pack` → `out.ehpk` 38,650 bytes. Simulator
    screenshot: `evidence/day1-screen1.png` (real BTC/ETH/SOL prices).
    Simulator env note: the VM lost `libwebkit2gtk-4.1` in a runtime reset;
    reinstalled via apt (see §11 commands).
12. **Day 2 build delivered (24 Nov ~00:00 WIB):** all three screens live
    in one text container, cursor-first (`src/main.ts` rewritten, build stamp
    `b2`, `app.json` version 0.2.0). New modules: `src/store.ts` (shared
    `glancefolio:v1:*` store — pure functions, Node-tested) and
    `src/companion.ts` (holdings form on the phone page). Verified in the
    headless simulator (screenshots in `evidence/day2-*.png`):
    - Screen 1: live prices + cursor now includes an `ALERTS ▸` nav row
      (window scrolls: 4 rows, 3 visible); HOLD line becomes an alerts
      summary (`ALERTS n armed · m fired`) on that row.
    - Screen 2: alerts list, sorted (coin order, above first — same order on
      the companion page); tap toggles arm/disarm, fired re-arms.
    - Screen 3: coin detail (price, 24h change, holding value, position
      P&L, alert state); tap cycles alert off → above → below → off (levels
      ±5%, 3 significant figures: BTC 63,177 → 66,300 / 60,000).
    - Navigation: tap opens/selects, double-tap goes one level up (root
      exits); double-click sends a single DOUBLE_CLICK_EVENT (verified: no
      stray click cycles the alert). Tap-to-refresh from Day 1 is gone —
      refresh is the 60 s poll + foreground-enter.
    - Companion form renders in the WebView (screenshot
      `evidence/day2-companion.png`); glasses→companion sync verified live
      (alerts list updated after a glasses tap); companion→glasses sync
      verified by Node tests (form submit → store → event) + code path.
    - 24h Hi/Lo shows only while Binance Vision is the active source
      (CoinGecko `simple/price` has none — by design, no extra calls).
    - `npm test` green (store + companion suites); `npm run build` clean;
      `evenhub pack` → `out.ehpk` 42,060 bytes, `min_app_version 2.2.10`.
    - Simulator env note: `libwebkit2gtk-4.1` was gone again after a runtime
      reset; the runtime's os-intent replay reinstalled it (it is in the
      replay ledger) — check `ldconfig -p | grep webkit2gtk` before starting
      the simulator. Simulator localStorage PERSISTS across restarts (the
      mutated demo alerts survived a restart). Automation `/api/input`
      requires header `Content-Type: application/json` (bare `-d` → HTTP 415).
