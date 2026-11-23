# DESIGN REVIEW — Glancefolio (second model: DeepSeek V4 Pro via APInex, free)

Reviewed 23 Nov 2026 ~11:35 WIB, before build week (kickoff 15:00 WIB).
Reviewer model: free/deepseek-v4-pro-0813. Source prompt + DESIGN.md fed in full.
This is a review only — no core code written. Fold the fixes into the Day 1–3 build.

## Severity 1
- **No real glasses.** Beta is blocked without an invite and email install; a simulator-only app cannot win track or Telegram prize. (§2, §5, §8)
  - Note (parent): Derr has no G2; pre-registration answered "G2 glasses No". Demo Day allows remote demo; DESIGN.md already plans simulator + portal checks, noted honestly in README. Securing a real unit / beta invite is Derr's decision, not something the build can fix.

## Severity 2
- **Cursor rendering undocumented.** "Native lists emit NO selection events on real glasses" is not enough — no documented cursor rendering (highlight glyph, active row, scroll offset) inside the single text container. (§2)
- **`min_app_version 2.0.0` vs SDK 0.0.16 floor 2.2.10.** Packaging will fail or install a stub until Day 1. (§10)
  - Note: DESIGN.md §10 already flags this as a Day 1 decision (upgrade SDK to latest, or pack with `--sdk-ver 0.0.10`).
- **Single 60 s price poll will miss crypto crosses on BLE.** Need threshold hysteresis, cooldowns, and backoff, not just a flag. (§3, §4)
- **CORS verified from a VM, not from the phone WebView.** `*` on curl does not guarantee Even WebView fetch works. (§3)
  - Note: already an open item in DESIGN.md §12 — verify from the real phone WebView on Day 1.

## Severity 3
- **No defined shared store between phone app and Telegram bot.** "Backend TBD Day 1" is too late for a 7-day build. (§4, §5) → Decide FIRST on Day 1.
- **Telegram bot is alert delivery, not a Mini App.** Judges may not count bot-to-app state sync as genuine Telegram integration for the prize. (§4)
  - Note: track examples include "Telegram bot for G2 (read messages, reply)", so a bot should qualify — but make the bot's role visible in the demo (real commands, real messages), not just background sync.
- **Double-tap "one level up; root exits" + shutdown debounce is UX that has not been prototyped on real glasses;** simulator will not reveal input timing failures. (§2, §7)
- **`pretext` pixel-fit + 5 px slack is premature polish on Day 4** before you know real-glasses glyph metrics. (§2, §8) → Deprioritise; fit after screens work.

## Severity 4
- **No rate-limit budget across 3 APIs, local storage schema, or cost-basis math.** (§3) → Write the storage schema + rate budget on Day 1.

## Severity 5
- **Portfolio screen holds only top 3; cost-basis P&L claimed in §6 but no screen or formula exists.** (§2, §6) → Either add a P&L line + formula, or drop the claim from the pitch.
- **Cut Screen 4 entirely on Day 1;** it adds nothing to the alert narrative. (Agrees with DESIGN.md "cut first if time is short".)

## Verdict (reviewer)
The biggest risk to winning is demoing a simulator-only app on glasses you do not own; Even Hub QA and judges will reject or ignore an uninstalled `.ehpk`. The single change that most improves the chance of top 1 is to secure a real G2 unit or Even Hub beta invite before Monday, then prove a crossed alert produces a real Telegram message and a FIRED row on actual hardware.
