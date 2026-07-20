# MediPOS Karachi

A Django-based medical store POS system for Karachi pharmacies.

## Local Preview

Use the project virtual environment:

```powershell
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py seed_demo
.\.venv\Scripts\python.exe manage.py runserver
```

The seed command prints a local preview username and random password.

## Included

- Public landing page with PKR pricing
- Store-only login
- POS sale screen with medicine availability checks
- Cart quantities and checkout
- Stock deduction after sale
- Medicine inventory maintenance
- Supplier and purchase stock management
- Expiry and low-stock alerts
- Sales reports and receipts
