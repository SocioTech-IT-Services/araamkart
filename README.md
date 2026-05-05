# AaramKart — B2B eCommerce Platform

A complete full-stack B2B eCommerce system for shopkeepers and bulk buyers built with Django and Vanilla JS.

## Features

- **Authentication**: 2FA Login (Phone OTP / Email+Pass+OTP)
- **Catalog**: Categories, Products, and **Bulk Pricing Tiers**
- **Cart**: AJAX-powered cart with automatic bulk discount calculation
- **Checkout**: Business details collection, COD payment
- **Admin Panel**: Dashboard stats, order management, stock updates
- **Notifications**: Email & Console OTP/Order confirmations

## Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
Copy `.env.example` to `.env` and fill in your settings (or use defaults for testing).

### 3. Database Setup
```bash
python manage.py migrate
```

### 4. Load Seed Data
```bash
python manage.py loaddata fixtures/initial_data.json
```

### 5. Create Superuser (Admin)
```bash
python manage.py createsuperuser
```

### 6. Run Server
```bash
python manage.py runserver
```

## UI Brand Colors
- **Primary Blue**: `#0B2C5A`
- **Primary Green**: `#3FAE2A`
- **Light Green**: `#6EDB5A`

## Design Principles
- Minimal & Mobile-first
- Business-oriented (No retail grocery visuals)
- Fast loading with Vanilla JS
