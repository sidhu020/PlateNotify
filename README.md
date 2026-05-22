# PlateNotify 🚗

**PlateNotify** is a clean, modern, and beginner-friendly Flask web application that allows users to register their license plates and receive anonymous reports about vehicle issues (like lights left on, bad parking, alarm ringing, etc.).

It features a secure authentication system, input validation, rate limiting, secure HTTP response headers, and **real-time Telegram push notifications** directly to vehicle owners' devices without needing to keep the website open.

---

## ✨ Features

- **User Authentication**: Secure signup and login powered by `Flask-Login` and Werkzeug `scrypt` password hashing.
- **Vehicle Registry**: Users can register and manage their vehicles (license plates are globally unique to prevent conflicts).
- **Anonymous Reporting**: A public-facing form allowing anyone to submit reports on a license plate anonymously.
- **Telegram Push Notifications**: Real-time alerts dispatched to the owner's phone/desktop via Telegram bot `@PlateNotify2bot` when a report is filed.
- **Interactive Dashboard**: A simple control panel to manage vehicles, read notifications, and configure Telegram settings.
- **Security Headers & CSP**: Flask-Talisman configured with a strict Content Security Policy (CSP) to block malicious scripts and cross-site scripting (XSS).
- **Rate Limiting**: Built-in protection against spam and brute-force requests via Flask-Limiter.
- **Clean Theme / Dark Mode**: Modern styling with a native, CSP-compliant toggle to switch between light and dark modes.

---

## 📂 Project Structure

```
PlateNotify/
│   app.py                # Main application entry point, routes, and error handlers
│   config.py             # Configuration classes (Development & Production environment setups)
│   extensions.py         # Declares Flask extension instances (SQLAlchemy, LoginManager, Limiter, Talisman)
│   models.py             # Database models (User, Vehicle, Report)
│   helpers.py            # Utility helper functions (safe redirects, Telegram sender, etc.)
│   requirements.txt      # Python package dependencies
│   render.yaml           # Deployment configuration blueprint for Render
│   README.md             # This documentation file
│   .gitignore            # Files ignored by git (e.g. database files, venv)
│
├── static/
│   ├── css/
│   │   └── style.css     # Custom styles and CSS variables
│   └── js/
│       └── dark-mode.js  # CSP-compliant JavaScript for dark mode toggle
│
└── templates/
    ├── base.html         # Base template layout containing common navbar, footer, and scripts
    ├── index.html        # App landing page
    ├── register.html     # Secure signup form
    ├── login.html        # User login form
    ├── dashboard.html    # Vehicle owner control panel and Telegram setup
    ├── add_vehicle.html  # Form to register a new license plate
    ├── report.html       # Anonymous public issue submission form
    └── 404.html          # Custom 404 error page
```

---

## 🚀 Setup & Local Development

### Prerequisites
- Python 3.8 or higher
- `pip` (Python package manager)

### Installation Steps

1. **Clone or Download the Repository**
   ```bash
   git clone <repository-url>
   cd PlateNotify
   ```

2. **Create a Virtual Environment**
   ```bash
   python -m venv venv
   ```

3. **Activate the Virtual Environment**
   * **On Windows (PowerShell):**
     ```powershell
     venv\Scripts\Activate.ps1
     ```
   * **On Windows (Command Prompt):**
     ```cmd
     venv\Scripts\activate.bat
     ```
   * **On macOS/Linux:**
     ```bash
     source venv/bin/activate
     ```

4. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Initialize the SQLite Database**
   ```bash
   flask init-db
   ```

6. **Run the Application**
   ```bash
   python app.py
   ```
   Open `http://localhost:5000` in your web browser.

---

## ✉️ How to Setup Telegram Notifications

To receive instant alerts on your phone or desktop:
1. Open Telegram and search for **`@userinfobot`**. Send it any message; it will reply with your unique numeric **ID** (e.g., `123456789`).
2. Search for our bot **`@PlateNotify2bot`** (or go to [t.me/PlateNotify2bot](https://t.me/PlateNotify2bot)) and click **Start** (or send `/start`).
3. Log in to your PlateNotify account, navigate to the **Dashboard**, paste your numeric ID under **Telegram Alerts**, and click **Save Settings**.
4. Test it by registering a license plate, logging out, going to **Report Issue**, and submitting an anonymous report on your plate!

---

## 🌐 Free Cloud Deployment Guides

### Option 1: Render (Free Web Service + Neon PostgreSQL)
Render is a popular platform-as-a-service. While Render has a free tier for hosting web services, its local SQLite database resets every time the app restarts (which happens daily or on code updates). To host **100% free with persistent data**, we can link a free PostgreSQL database from **Neon.tech** or **Supabase**.

#### Step 1: Create a Free Database
1. Go to [Neon.tech](https://neon.tech/) or [Supabase](https://supabase.com/) and create a free PostgreSQL database.
2. Copy the database connection string. It will look like:
   `postgresql://username:password@hostname/dbname?sslmode=require`

#### Step 2: Deploy on Render
1. Push your PlateNotify project code to a GitHub repository.
2. Sign in to [Render](https://render.com/) and click **New > Web Service**.
3. Link your GitHub repository.
4. Set the following options:
   * **Runtime**: `Python`
   * **Build Command**: `pip install -r requirements.txt`
   * **Start Command**: `gunicorn app:app`
5. Click **Advanced** and add the following **Environment Variables**:
   * `SECRET_KEY`: *Enter a long, random secret phrase for session security.*
   * `FLASK_DEBUG`: `0`
   * `FLASK_ENV`: `production`
   * `DATABASE_URL`: *Paste the connection string from Neon/Supabase here.*  
     *(Note: If the connection string starts with `postgres://`, change the prefix to `postgresql://` so SQLAlchemy recognizes it).*
   * `TELEGRAM_BOT_TOKEN`: `8940519709:AAF3YJKvwtawWaWhW7MxPG68Se6rr4y3Bc0` *(or your custom bot token)*
6. Click **Deploy Web Service**. Render will automatically detect the database and build the tables on startup.

---

### Option 2: PythonAnywhere (Free Python Hosting with SQLite)
PythonAnywhere provides free Python hosting where SQLite databases **never reset** because files are stored on persistent storage.

#### Step 1: Upload and Configure
1. Create a free account at [PythonAnywhere](https://www.pythonanywhere.com/).
2. Go to the **Consoles** tab and start a new **Bash** console.
3. Clone your GitHub repository:
   ```bash
   git clone <your-github-repo-url>
   cd PlateNotify
   ```
4. Create a virtual environment and install the dependencies:
   ```bash
   mkvirtualenv --python=/usr/bin/python3.10 venv
   pip install -r requirements.txt
   ```
5. Initialize the database:
   ```bash
   export FLASK_APP=app.py
   flask init-db
   ```

#### Step 2: Set Up the Web App
1. Go to the **Web** tab in PythonAnywhere and click **Add a new web app**.
2. Select **Manual Configuration** and choose **Python 3.10**.
3. Under the **Code** section of the configuration page:
   * **Source code**: `/home/YOUR_USERNAME/PlateNotify`
   * **Working directory**: `/home/YOUR_USERNAME/PlateNotify`
4. Under the **Virtualenv** section:
   * Enter: `/home/YOUR_USERNAME/.virtualenvs/venv` (or your venv directory path)
5. Open the **WSGI configuration file** link (found under Code section) and replace its contents with:
   ```python
   import sys
   import os

   path = '/home/YOUR_USERNAME/PlateNotify'
   if path not in sys.path:
       sys.path.insert(0, path)

   # Load environment secrets
   os.environ['SECRET_KEY'] = 'your-super-secret-key-goes-here'
   os.environ['TELEGRAM_BOT_TOKEN'] = '8940519709:AAF3YJKvwtawWaWhW7MxPG68Se6rr4y3Bc0'
   os.environ['FLASK_DEBUG'] = '0'

   from app import app as application
   ```
6. Click the green **Reload** button at the top of the Web tab. Your web application is now live at `http://YOUR_USERNAME.pythonanywhere.com`!

---

## 🔒 Security & Best Practices Highlights

- **Password Hashing**: We do not store plaintext passwords. The application uses Werkzeug's `scrypt` hashing algorithm.
- **Anti-Enumeration Protection**: On submitting an anonymous report, the system returns a success message regardless of whether the license plate is registered. This prevents malicious scans to see which users own specific license plates.
- **SQL Injection Prevention**: All queries are structured through the SQLAlchemy ORM, which automatically parameterizes SQL statements.
- **No Unsafe Inline JS/CSS**: Adheres strictly to the Content Security Policy to eliminate the risks of cross-site scripting (XSS).
- **Safe Redirection**: Redirection endpoints are checked using host validation to prevent Open Redirect attacks.

---

## 📄 License
This project is open-source and free to use or modify for educational purposes.
