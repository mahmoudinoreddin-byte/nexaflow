# NexaFlow 🚀

A complete Django SaaS subscription platform with **Gumroad webhook integration**, user dashboard, and admin panel.

---

## Features

- 🔐 **Token-based account setup** — Users receive a secure email link after Gumroad purchase; no plain passwords stored
- 💳 **Gumroad webhook handler** — Auto-creates accounts on sale, handles refunds and cancellations
- 📊 **Admin Panel** — Manage users, toggle services, view webhook logs
- 👤 **User Dashboard** — Service grid, subscription status, activity log
- 📧 **Email via SendGrid** — Async welcome emails via Celery + Redis
- 🌍 **Multilingual landing page** — EN / FR / ES (your original HTML)
- ☁️ **Render-ready** — `render.yaml` included for one-click deploy

---

## Local Development

### 1. Clone & Install

```bash
git clone https://github.com/YOUR_USERNAME/nexaflow.git
cd nexaflow
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your values (SECRET_KEY is required)
```

### 3. Run Migrations & Seed

```bash
python manage.py migrate
python manage.py seed           # Creates demo services & categories
python manage.py createsuperuser  # Creates your admin account
```

### 4. Run the Dev Server

```bash
python manage.py runserver
```

Open http://localhost:8000

---

## Project Structure

```
nexaflow/
├── config/                  # Django settings, URLs, Celery
│   ├── settings.py
│   ├── urls.py
│   └── celery.py
├── apps/
│   ├── accounts/            # Custom User model, login, setup-password
│   ├── dashboard/           # Landing page + user dashboard
│   ├── admin_panel/         # Staff-only admin views
│   ├── webhooks/            # Gumroad webhook receiver + Celery tasks
│   └── services/            # Service model + user access
├── templates/
│   ├── landing_page.html    # Your original landing page
│   ├── accounts/            # Login, setup password
│   ├── dashboard/           # User dashboard
│   ├── admin_panel/         # Admin views
│   └── emails/              # HTML email templates
├── render.yaml              # Render deployment config
├── Procfile                 # Heroku / Railway
└── requirements.txt
```

---

## Deploy to Render

### Option A — One-click with render.yaml

1. Push this repo to GitHub
2. Go to [render.com](https://render.com) → New → Blueprint
3. Connect your GitHub repo
4. Render reads `render.yaml` and creates: **web service + worker + PostgreSQL + Redis**
5. Add these env vars manually in Render dashboard:
   - `SITE_URL` → your Render URL, e.g. `https://nexaflow.onrender.com`
   - `EMAIL_HOST_PASSWORD` → your SendGrid API key
   - `DEFAULT_FROM_EMAIL` → e.g. `hello@yourdomain.com`
   - `GUMROAD_WEBHOOK_SECRET` → from Gumroad settings

### Option B — Manual

1. Create a **Web Service** in Render
   - Build command: `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate`
   - Start command: `gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 2`
2. Add a **PostgreSQL** database and link `DATABASE_URL`
3. Add a **Redis** instance and link `REDIS_URL`
4. Add a **Background Worker** with: `celery -A config worker --loglevel=info`
5. Set all env vars from `.env.example`

---

## Gumroad Webhook Setup

1. Log in to Gumroad → Settings → Advanced → **Webhooks**
2. Add URL: `https://yourdomain.com/webhooks/gumroad/`
3. Optionally add a secret and set `GUMROAD_WEBHOOK_SECRET` in your env

The webhook handles:
| Event | Action |
|---|---|
| Sale | Creates user, assigns services, sends welcome email |
| Refund | Suspends user |
| Cancellation | Sets user to inactive |
| Subscription restart | Reactivates user |

---

## Creating Your First Admin

```bash
python manage.py createsuperuser
```

Then visit `/admin-panel/` — only `is_staff=True` users can access it.

---

## Environment Variables Reference

| Variable | Required | Description |
|---|---|---|
| `SECRET_KEY` | ✅ | Django secret key |
| `DEBUG` | | `True` for dev, `False` for prod |
| `ALLOWED_HOSTS` | ✅ prod | Comma-separated hosts |
| `DATABASE_URL` | ✅ prod | PostgreSQL connection string |
| `REDIS_URL` | | For async email (Celery) |
| `EMAIL_HOST_PASSWORD` | ✅ prod | SendGrid API key |
| `DEFAULT_FROM_EMAIL` | | Sender address |
| `GUMROAD_WEBHOOK_SECRET` | | Webhook verification |
| `SITE_URL` | ✅ prod | Full URL for email links |

---

## Tech Stack

- **Django 5** + **Gunicorn**
- **PostgreSQL** (SQLite for local dev)
- **Redis** + **Celery** (async email)
- **WhiteNoise** (static files)
- **SendGrid** (transactional email)
- **Gumroad Webhooks** (payment integration)
