
# YourPOS : Cafe Point Of Sell☕

A lightweight, table-based Point of Sale (POS) system built for small cafés and restaurants. Originally a desktop app (Python + Tkinter + SQLite) used in an active café, rebuilt as a Django web application for easier access, better data handling, and room to grow.

---

## 🚀 Overview

YourPOS lets café staff manage tables, take orders per table with item variants (Small/Large/Default), track a running bill in real time, settle payments (Cash/Card/UPI) with optional notes, and review order history and sales reports — all from a browser.

---

## 🛠️ Technologies Used

| Layer          | Technology                          |
|----------------|--------------------------------------|
| Backend        | Python, Django                       |
| Database       | SQLite (default, swappable via Django ORM) |
| Frontend       | HTML5, Bootstrap 5, vanilla JavaScript (Fetch API) |
| Architecture   | Server-rendered templates + JSON endpoints for dynamic UI updates (no full page reloads for ordering/billing) |

No heavy JS framework is used on purpose — the ordering screen is powered by plain `fetch()` calls against small Django JSON views, keeping the stack simple and easy to maintain.

---

## ✨ Core Features

### 🪑 Table Management
- Visual grid of all café tables
- Live status per table: **Available** / **Occupied**
- Add new tables on the fly

### 🍽️ Menu Management
- Categories (e.g. Coffee, Pizza, Sandwich, Burger, and others)
- Items grouped by category
- Each item supports either a **single default price** or **Small/Large variant pricing** — never both at once (enforced at the model level)
- Edit/deactivate items and categories without deleting historical order data

### 🧾 Order Taking (per table)
- Click a table → opens a dedicated ordering screen for that table
- Browse categories → pick items → select variant (or default price)
- Live running bill: quantity +/-, remove item, auto-recalculated subtotal & total
- All updates happen via AJAX — no page reloads while taking an order

### 💳 Billing & Settlement
- Settle a bill with **Cash**, **Card**, or **UPI**
- Optional note added at settlement time (e.g. "Table paid ₹50 extra as tip")
- Auto-generated, unique bill number encoding table number, a daily counter, and the date
- Table automatically flips back to **Available** once billed
- Validation prevents settling an empty order or picking an invalid payment method

### 📜 Order History
- Every settled bill is logged with: bill number, table, items ordered, total, payment method, note, date & time
- Historical bills remain accurate even if menu items/prices change later

### 📊 Sales Reports
- Daily, weekly, and monthly sales totals and order counts at a glance

---

## 🏗️ System Architecture

```
┌─────────────────────┐
│   Browser (UI)      │
│  Bootstrap + Fetch  │
└─────────┬───────────┘
          │ HTTP (JSON + HTML)
┌─────────▼────────────┐
│   Django Views       │
│  - Page views (HTML) │
│  - JSON views (AJAX) │
└─────────┬────────────┘
          │ ORM
┌─────────▼────────────┐
│   Django Models      │
│  TableInfo           │
│  MenuCategory        │
│  MenuItem            │
│  MenuVariant         │
│  Order / OrderItem   │
│  Bill                │
└─────────┬────────────┘
          │
┌─────────▼────────────┐
│   SQLite Database    │
└──────────────────────┘
```

**Data flow for a typical order:**
1. Staff selects a table → a `TableInfo` status flips to *Occupied*, an active `Order` is created (or reused).
2. Adding an item creates/updates an `OrderItem`, tied to a specific `MenuVariant` (so pricing is always variant-driven, never guessed).
3. Settling the bill snapshots the order into a `Bill` record (bill number, total, payment method, note) and closes the `Order`.
4. The table flips back to *Available*, ready for the next customer.

---

## 📂 Project Structure

```
POS/
├── home/           # main app
│   ├── __pycache__/      # cache files
│   ├── migrations/       # migration files
│   ├── __init__.py
│   ├── admin.py          # site settings about Admin Panel
│   ├── apps.py           # AppConfig
│   ├── models.py         # all models
│   ├── urls.py           # app-level routes
│   ├── views.py          # page views + JSON endpoints for AJAX
├── POS/            # project
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
├── static/         # static file for images and css
│   └── img/
│       └──logo.jpg
├── templates/      # templages for HTML files
│   ├── additems.html
│   ├── base.html
│   ├── createorders.html
│   ├── edititem.html
│   ├── home.html
│   ├── managecategories.html
│   ├── manageitems.html
│   ├── orderhistory.html
│   ├── orders.html # table grid
│   ├── salesreport.html
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
pip install django

# 4. Apply migrations
python manage.py migrate

# 5. Create an admin user (to manage categories/items via /admin)
python manage.py createsuperuser

# 6. Run the development server
python manage.py runserver
```

Visit `http://127.0.0.1:8000/orders/` to see the table grid, or `http://127.0.0.1:8000/admin/` to add categories, items, and variants.

---

## 🗺️ Roadmap / Ideas for Later

- Per-item sales breakdown (best/worst sellers) using itemized bill snapshots
- Printable/downloadable bill receipts
- Role-based login (waiter vs. manager/admin views)
- KOT (Kitchen Order Ticket) printing for the kitchen counter
- Deployment guide (Render/Railway/PythonAnywhere) with PostgreSQL for production

---

## 📝 Background

This project began as a fully offline Python + Tkinter + SQLite desktop app, actively used in a real café for day-to-day billing. YourPOS is its web-based evolution — same core workflow the staff already know, rebuilt on Django to make it easier to access, extend, and eventually deploy for multiple devices at once (e.g. a tablet per waiter).

---

## 📄 License

This project is currently unlicensed / for personal & portfolio use.
