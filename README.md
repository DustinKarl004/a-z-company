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
| Database (local/dev) | SQLite |
| Database (production) | PostgreSQL |
| ORM | Yes (e.g. SQLAlchemy) |

**Why Vercel + Railway instead of AWS:** avoids the cost of managing a custom domain/infrastructure setup on AWS — Vercel/Railway are cheaper and simpler to run for a project this size.

## Database Schema (draft)

Proposed starting schema — will evolve as implementation details firm up.

**ID strategy:** primary keys use short, random, non-sequential IDs (e.g. [nanoid](https://github.com/ai/nanoid), ~12 characters, URL-safe) instead of auto-increment integers. With sequential IDs (`1`, `2`, `3`, ...) anyone can guess neighboring IDs and probe for other branches'/users' records — random short IDs prevent that kind of enumeration. This applies to every table below.

**`branches`**
| Column | Type | Notes |
|---|---|---|
| id | PK, short ID | non-sequential, e.g. nanoid |
| name | text | e.g. "Branch 1 - Quezon City" |
| created_at | timestamp | |

**`users`**
| Column | Type | Notes |
|---|---|---|
| id | PK, short ID | non-sequential, e.g. nanoid |
| name | text | |
| email | text, unique | |
| password_hash | text | |
| role | enum: `admin`, `staff` | |
| branch_id | FK → branches, nullable | null for admin, required for staff |
| totp_secret | text, nullable | for authenticator app 2FA |
| is_active | bool | for disabling staff accounts |
| created_at | timestamp | |

**`stock_items`**
| Column | Type | Notes |
|---|---|---|
| id | PK, short ID | non-sequential, e.g. nanoid |
| name | text | product/item name |
| unit | text | e.g. "pcs", "kg" |
| created_at | timestamp | |

**`stock_deliveries`** — daily stock delivered per branch
| Column | Type | Notes |
|---|---|---|
| id | PK, short ID | non-sequential, e.g. nanoid |
| branch_id | FK → branches | |
| item_id | FK → stock_items | |
| date | date | |
| quantity_delivered | numeric | |
| is_short | bool | flags "not enough" deliveries |
| created_by | FK → users | |
| created_at | timestamp | |

**`stock_counts`** — end-of-day remaining stock (replaces the Messenger listing)
| Column | Type | Notes |
|---|---|---|
| id | PK, short ID | non-sequential, e.g. nanoid |
| branch_id | FK → branches | |
| item_id | FK → stock_items | |
| date | date | |
| quantity_remaining | numeric | |
| created_by | FK → users | |
| created_at | timestamp | |

**`sales`**
| Column | Type | Notes |
|---|---|---|
| id | PK, short ID | non-sequential, e.g. nanoid |
| branch_id | FK → branches | |
| item_id | FK → stock_items | |
| date | date | |
| quantity_sold | numeric | |
| amount | numeric | computed: quantity × unit price, or entered directly |
| created_by | FK → users | |
| created_at | timestamp | |

**`expenses`** — admin/system visibility only, not staff
| Column | Type | Notes |
|---|---|---|
| id | PK, short ID | non-sequential, e.g. nanoid |
| branch_id | FK → branches | |
| date | date | |
| description | text | |
| amount | numeric | |
| created_by | FK → users | |
| created_at | timestamp | |

**`daily_profits`** — computed daily, admin-only visibility
| Column | Type | Notes |
|---|---|---|
| id | PK, short ID | non-sequential, e.g. nanoid |
| branch_id | FK → branches | |
| date | date | |
| total_sales | numeric | |
| total_expenses | numeric | |
| profit | numeric | `total_sales - total_expenses` |
| computed_at | timestamp | |

**`monthly_rollups`** — auto-generated on the 1st of each month
| Column | Type | Notes |
|---|---|---|
| id | PK, short ID | non-sequential, e.g. nanoid |
| branch_id | FK → branches, nullable | null = all-branches summary row |
| year | int | |
| month | int | |
| total_sales | numeric | |
| total_expenses | numeric | |
| total_profit | numeric | |
| generated_at | timestamp | |

**Edit-lock rule** (staff entries editable only until 23:59 same day): rather than a stored "locked" flag, enforce this at the API layer by comparing the request time against each row's `date` — reject edits once the entry's day has passed. Admin edits are not subject to this lock.

**Visibility rule**: `expenses` and `daily_profits` are only ever exposed to `role = admin` in the API layer — staff-facing endpoints for stocks/sales should not join against these tables.

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
