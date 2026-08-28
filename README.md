

# YourPOS : Café Point Of Sale ☕

A lightweight, multi-tenant, table-based Point of Sale (POS) system built for small cafés and restaurants. Originally a desktop app (Python + Tkinter + SQLite) used in an active café, rebuilt as a full Django + Django REST Framework web application — any café can sign up, log in, and run their own independent POS from a browser.

---

## 🚀 Overview

YourPOS lets café staff manage tables, take orders per table with item variants (Small/Large/Default), track a running bill in real time, settle payments (Cash/Card/UPI) with optional notes, and review order history and sales reports. Every café that signs up gets its own fully isolated tables, menu, orders, and bills — nothing is shared between cafés.

The frontend is a set of thin Django templates; **all data reads and writes happen through a REST API** built with Django REST Framework. Templates render an empty shell and JavaScript (`fetch`) does the rest — no full-page form POSTs anywhere except signup/login.

---

## 🛠️ Technologies Used

| Layer          | Technology                                              |
|----------------|-----------------------------------------------------------|
| Backend        | Python, Django, Django REST Framework                    |
| Database       | SQLite (default, swappable via Django ORM — PostgreSQL-ready) |
| Auth           | Django session authentication + CSRF (no JWT)             |
| Frontend       | HTML5, Bootstrap 5, vanilla JavaScript (Fetch API)         |
| Architecture   | REST API (DRF) + thin server-rendered template shells — every page loads/saves data via `/api/...` endpoints, no full page reloads for ordering/billing |

No heavy JS framework is used on purpose — every screen is powered by plain `fetch()` calls against DRF endpoints, keeping the stack simple, debuggable, and easy to extend.

---

## ✨ Core Features

### 🏢 Multi-Tenant Café Accounts
- Any café can **sign up** with its own account — name, username, password
- Each café's tables, categories, items, orders, and bills are **fully isolated** from every other café
- Session-based login/logout, CSRF-protected

### 🪑 Table Management
- Visual grid of all café tables, auto-numbered per café (starts at 1, increments per café — two different cafés can both have a "Table 1")
- Live status per table: **Available** / **Occupied**
- Add new tables with one click — no manual numbering

### 🍽️ Menu Management
- Categories (e.g. Coffee, Pizza, Sandwich, Burger, and others)
- Items grouped by category
- Each item supports either a **single default price** or **Small/Large variant pricing** — never both at once (enforced at the model level)
- Add, edit, and deactivate items and categories without deleting historical order data
- Inactive items stay visible in menu management (so they can be reactivated) but are automatically hidden from the order-taking screen

### 🧾 Order Taking (per table)
- Click a table → opens a dedicated ordering screen for that table
- Browse categories → pick items → select variant (or default price)
- Live running bill: quantity +/-, remove item, auto-recalculated subtotal & total
- All updates happen via the API — no page reloads while taking an order

### 💳 Billing & Settlement
- Settle a bill with **Cash**, **Card**, or **UPI**
- Optional note added at settlement time (e.g. "Table paid ₹50 extra as tip")
- Auto-generated bill number encoding table number, a daily counter (per café), and the date — collision-safe even under concurrent settle requests
- Table automatically flips back to **Available** once billed, and back to **Occupied** only once an item is actually added (not just on opening the order screen)
- Validation prevents settling an empty order or picking an invalid payment method

### 📜 Order History
- Every settled bill is logged with: bill number, table, items ordered, total, payment method, note, date & time
- Historical bills remain accurate even if menu items/prices change later

### 📊 Sales Reports & Dashboard
- Daily, weekly, and monthly sales totals and order counts at a glance
- Home dashboard shows today's sales, bills settled today, occupied tables, and the most recent bill — all live from the API

### 🔔 In-App Notifications
- Toast-style success/error messages for every action (add/rename/delete category or item, settle bill, etc.) — no server-rendered flash messages required, works fully with the API-driven flow

---

## 🏗️ System Architecture

```
┌──────────────────────────┐
│   Browser (UI)             │
│  Bootstrap + Fetch (JS)    │
│  Thin template shells      │
└─────────┬───────────────────┘
          │ HTTP (JSON via /api/..., HTML shells via normal routes)
┌─────────▼────────────────┐
│   Django REST Framework    │
│  - Serializers             │
│  - APIView / generics      │
│  - Session auth + CSRF     │
└─────────┬────────────────┘
          │ ORM
┌─────────▼────────────────┐
│   Django Models             │
│  Cafe                       │
│  TableInfo                  │
│  MenuCategory                │
│  MenuItem                   │
│  MenuVariant                  │
│  Order / OrderItem            │
│  Bill                          │
└─────────┬────────────────┘
          │
┌─────────▼────────────────┐
│   SQLite Database            │
└──────────────────────────┘
```

**Data flow for a typical order:**
1. A café signs up and logs in — every subsequent request is scoped to `request.user.cafe`.
2. Staff opens a table → the frontend calls the API to create-or-reuse an active `Order` for that table.
3. Adding an item calls the API, which creates/updates an `OrderItem` tied to a specific `MenuVariant` (so pricing is always variant-driven, never guessed), and flips the table to *Occupied* only once it actually holds an item.
4. Settling the bill calls the API, which snapshots the order into a `Bill` record (bill number, total, payment method, note) and closes the `Order`.
5. The table flips back to *Available*, ready for the next customer — all without a page reload.

---

## 📂 Project Structure

```
POS/
├── home/                    # main app
│   ├── migrations/            # migration files
│   ├── models.py               # Cafe, TableInfo, MenuCategory, MenuItem,
│   │                            # MenuVariant, Order, OrderItem, Bill
│   ├── views.py                 # thin page views (render HTML shells) + auth views
│   ├── api_views.py              # all DRF endpoints (tables, menu, orders, bills, reports)
│   ├── serializers.py             # DRF serializers for every model
│   ├── urls.py                     # HTML page routes
│   ├── api_urls.py                  # /api/... routes
│   └── admin.py
├── POS/                       # project
│   ├── settings.py
│   ├── urls.py                  # includes home.urls + home.api_urls under /api/
│   ├── asgi.py
│   └── wsgi.py
├── static/
│   └── img/
│       └── logo.jpg
├── templates/
│   ├── base.html                  # nav, toast system, logout
│   ├── signup.html / login.html    # session-based auth, API-driven
│   ├── home.html                    # dashboard, fully API-driven
│   ├── orders.html                   # table grid, fully API-driven
│   ├── createorders.html              # order-taking + billing screen, fully API-driven
│   ├── managecategories.html           # fully API-driven
│   ├── manageitems.html / additems.html / edititem.html  # fully API-driven
│   ├── orderhistory.html                # fully API-driven
│   ├── salesreport.html                  # fully API-driven
│   └── settings.html
├── db.sqlite3
├── manage.py
└── requirements.txt
```

---

## ⚡ Quick Start

**Prerequisites:** Python 3.10+, pip

```bash
# 1. Clone the repository
git clone https://github.com/nextxlemons/YourPOS.git
cd YourPOS

# 2. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Apply migrations
python manage.py migrate

# 5. Run the development server
python manage.py runserver
```

Visit `http://127.0.0.1:8000/signup/` to create your café account, then log in at `/login/` to reach the dashboard. `/admin/` is also available for low-level data inspection if you create a superuser (`python manage.py createsuperuser`) — note that a superuser has no linked café by default, so it can browse `/admin/` but not the café-facing app itself unless a `Cafe` is manually linked to it.

---

## 🗺️ Roadmap / Ideas for Later

- Per-item sales breakdown (best/worst sellers) using itemized bill snapshots
- Printable/downloadable bill receipts
- Role-based staff accounts within a single café (waiter vs. manager permissions)
- KOT (Kitchen Order Ticket) printing for the kitchen counter
- Split billing across multiple payment methods for one table
- PostgreSQL + production deployment guide (Render/Railway/PythonAnywhere)
- API documentation (drf-spectacular / Swagger UI)

---

## 📝 Background

This project began as a fully offline Python + Tkinter + SQLite desktop app, actively used in a real café for day-to-day billing. YourPOS is its web-based evolution — same core workflow the staff already know, rebuilt on Django + DRF so any café can sign up and run their own instance, extend it, and eventually deploy it for multiple devices at once (e.g. a tablet per waiter).

---

## 📄 License

This project is currently unlicensed / for personal & portfolio use.