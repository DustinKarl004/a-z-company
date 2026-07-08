# A.Z. Company

Inventory, sales, and profit tracking system for A.Z. Company's branches — replacing the current manual Messenger-based stock reporting with a proper web app.

## Status

📋 **Plan phase** — requirements gathering, tech stack decisions, and design in progress. No implementation yet.

## Background

Currently, each branch reports its stock and sales manually through Messenger at the end of the day. This doesn't scale well and makes it hard to track profits and expenses reliably across branches. This project replaces that process with a web app where staff log daily stock/sales data per branch, and admins get consolidated reporting across all branches.

## Core Requirements

### Stocks

- **Daily stock delivery** — record stock delivered each day per branch (flags shortfalls, e.g. delivery was insufficient).
- **End-of-day stock count** — before a branch closes, list all stock remaining (replaces the current Messenger listing).
- **Profit tracking** — profit is recorded and checked daily, per branch.

### Reporting (Excel-style)

- Automatic calculations via formulas (no manual math):
  - Stock expenses
  - Sales
  - Daily profit
- Monthly rollup across all branches — generated **automatically on the 1st of every month** (scheduled job aggregates the prior month's stocks/sales/expenses/profit per branch). Admin can also re-trigger it manually if a correction is needed.

### Website

**Branding**
- Name: **Z. A. Company**
- Logo: no final design yet — using a placeholder mockup for now. See [`assets/logo-mockup.svg`](assets/logo-mockup.svg).

  <img src="assets/logo-mockup.svg" width="120" alt="Z.A. Company mockup logo" />

**Auth & Roles**
- Login only — no public self-registration.
- A default admin account is created on first setup (seeded, not self-registered).
- Admin can create staff accounts from a Staff management page.
- Suggestion: add 2FA/authenticator app (TOTP) support for both staff and admin logins.

**Staff permissions (per branch)**
- Staff belong to a specific branch and can only see their own branch's data.
- Staff can input/edit records only until 23:59 on the day they're entered — locked after 24 hours.
- Staff can view their branch's past records, but **only stock and sales entries** — not profits or expenses.
- Staff cannot see other branches' data at all.

**Admin permissions**
- Full visibility across all branches: stocks, sales, expenses, and profits.
- Can view monthly rollups across branches.

## Tech Stack

| Layer | Choice |
|---|---|
| Frontend | Vue.js, hosted on **Vercel** |
| Backend | Python, hosted on **Railway** |

**Why Vercel + Railway instead of AWS:** avoids the cost of managing a custom domain/infrastructure setup on AWS — Vercel/Railway are cheaper and simpler to run for a project this size.

## Suggested Color Palette

Since the business is inventory/finance-driven, a palette that reads as trustworthy and clear (good for numbers, tables, and profit/loss states) works well:

| Role | Color | Hex |
|---|---|---|
| Primary (brand) | Deep Teal | `#0F6E6E` |
| Primary Dark (headers/nav) | Ink Navy | `#0B2A3B` |
| Accent | Warm Amber | `#F2A93B` |
| Success (profit, positive) | Leaf Green | `#2E8B57` |
| Danger (loss, expense, shortfall) | Muted Red | `#D64545` |
| Background | Off-white | `#F7F9F9` |
| Surface (cards/tables) | White | `#FFFFFF` |
| Text (primary) | Charcoal | `#1F2A2E` |
| Text (secondary/muted) | Slate Gray | `#6B7A80` |

- **Deep Teal + Ink Navy** as the brand pair feels professional without being generic corporate blue.
- **Amber** as a single accent color for calls-to-action/highlights (don't overuse).
- **Green/Red** reserved strictly for profit vs. loss / positive vs. negative deltas, so staff can scan numbers at a glance.

## Open Questions

- Final logo design (currently using the placeholder mockup above).
- Whether `sales.amount` is entered directly by staff or computed from a per-item unit price.
- Whether stock delivery / count entries are per-item or a single free-text/aggregate entry per branch per day.
