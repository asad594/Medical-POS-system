d# MediPOS Karachi 💊

A premium, production-grade medical store Point-of-Sale (POS) and inventory management system designed for pharmacies in Karachi. Built with Django and wrapped in a lightweight desktop Webview client, it provides an offline-first, native-feeling desktop experience with a clean visual design inspired by Stripe and Vercel.

![MediPOS Karachi Dashboard Mockup](https://raw.githubusercontent.com/asad594/Medical-POS-system/main/screenshots/medipos_dashboard.png)

---

## Key Features 🚀

- **📊 High-End Analytics Dashboard**: Features responsive KPI widgets (PKR sales, invoices count, low stock warnings), batch expiry logs, and a dynamic line graph displaying recent sales using Chart.js.
- **🛒 Cashier Counter POS**: Split-pane cashier screen featuring a large medicine catalog search panel, stock indicators, quantity counter adjustments, and customer info fields.
- **📁 Collapsible Sidebar**: Collapsible navigation sidebar utilizing Lucide icons with persistent collapse state stored in `localStorage`.
- **🚨 Stock Health Alerts**: Automated warning pages detailing low-stock quantities and expiring batches (safety filters warn cashier prior to completing sales).
- **🖨️ Thermal Receipt Printing**: Custom print styles formatted for thermal slip printers (hides headers, sidebars, and buttons automatically during print).
- **🔒 Secure Portal access**: Login authentication locks for counter billing staff.
- **🖥️ Silent VBS Launcher**: Launches the backend and GUI window in the background without any command prompt console windows showing.

---

## Technology Stack 🛠️

- **Backend**: Django 6.0.6 (Python 3.13)
- **Database**: SQLite3 (Local, offline-first file database)
- **Desktop Client Wrapper**: PyWebView (powered by Microsoft Edge WebView2)
- **Frontend Assets**: CSS Grid/Flexbox, Lucide Icon Library, Chart.js Analytics

---

## Directory Structure 📂

```text
c:\Users\RB Tech\Desktop\Medical POS\
├── .git/                 # Git version history database
├── .venv/                 # Python local virtual environment
├── medipos/               # Django main project configuration module
├── store/                 # POS store application module (models, templates, views, static assets)
├── screenshots/           # Application preview screenshot mockups
│   └── medipos_dashboard.png
├── db.sqlite3             # Local SQLite database file
├── manage.py              # Django CLI utility
├── requirements.txt       # Python package dependencies
├── .gitignore             # Git ignore file
├── run_desktop.py         # Desktop application python entry script
├── run_desktop.bat        # Python launcher batch script
└── MediPOS.vbs            # Silent taskbar/desktop launcher
```

---

## Getting Started & Installation ⚙️

### Prerequisites
Make sure you have **Python 3.13** or higher installed on your Windows system.

### 1. Setup the Environment
Clone this project, navigate to the directory in PowerShell, and configure the local environment:
```powershell
# Create virtual environment
python -m venv .venv --clear

# Activate environment and install dependencies
.\.venv\Scripts\activate.bat
pip install -r requirements.txt
```

### 2. Initialize Database and Seed Sample Data
Run the migrations and seed sample Karachi pharmacy suppliers, medicines, and default admin credentials:
```powershell
python manage.py migrate
python manage.py seed_demo
```

---

## How to Launch the Application 🖥️

There are two ways to start the POS desktop system:

### Option A: Double-Click Silent Launcher (Recommended)
1. Open your File Explorer and navigate to the project directory: `c:\Users\RB Tech\Desktop\Medical POS`.
2. Double-click the **`MediPOS.vbs`** file.
3. The background Django server will start silently, and a dedicated native desktop window will open immediately (no command prompt window will flash).

### Option B: VS Code Editor Play Button
1. Open the [run_desktop.py](file:///c:/Users/RB%20Tech/Desktop/Medical%20POS/run_desktop.py) file in your IDE.
2. Click the **Run/Play** icon in the editor.
3. The script will automatically switch to the virtual environment Python interpreter and boot the desktop GUI window.

---

## Default Login Credentials 🔑

When the window opens, enter these credentials to log in:
- **Username**: `admin`
- **Password**: `admin123`
