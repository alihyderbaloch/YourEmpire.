# 🚀 YourEmpire - QUICK DEPLOYMENT STEPS

## ⚡ TL;DR - Deploy in 10 Minutes

### 1️⃣ PREPARE (2 minutes)
- ✅ Files already ready: `Procfile`, `runtime.txt`, `requirements.txt`

### 2️⃣ GITHUB (3 minutes)
```bash
# In Replit terminal:
cd /home/runner/workspace
git init
git add .
git commit -m "Initial deployment"
git remote add origin https://github.com/YOUR_USERNAME/yourempire.git
git branch -M main
git push -u origin main
```

### 3️⃣ RENDER DATABASE (2 minutes)
- Go to **render.com**
- Click **"+ New +"** → **"PostgreSQL"**
- Name: `yourempire-db`
- Database: `yourempire`
- User: `admin`
- Copy CONNECTION STRING when done

### 4️⃣ RENDER APP (2 minutes)
- Click **"+ New +"** → **"Web Service"**
- Connect GitHub → Select `yourempire` repo
- Build Command: `pip install -r requirements.txt`
- Start Command: `gunicorn app:app`
- Click Create

### 5️⃣ ENVIRONMENT VARIABLES (1 minute)
In Render dashboard, go to your app → Environment:
```
DATABASE_URL = [PASTE CONNECTION STRING FROM STEP 3]
FLASK_ENV = production
SECRET_KEY = [generate: python -c "import secrets; print(secrets.token_hex(32))"]
SESSION_SECRET = [same as SECRET_KEY]
```

### 6️⃣ DONE! ✅
- Wait 5 minutes for deployment
- Click the live URL
- Your app is LIVE! 🎉

---

## 📚 Need Detailed Help?
See **DEPLOYMENT_GUIDE.md** for complete step-by-step guide with screenshots and troubleshooting.

---

## 🔑 Login Credentials

**Master Admin:**
- Email: `masteradmin@yourempire.com`
- Password: `Master@lihyder1866`

**Existing User:**
- Email: `alihyderrohani3@gmail.com`
- Password: (same as before)

---

## ⚠️ Important Notes
- Your GitHub repo must be PUBLIC
- Free tier Render apps sleep after 15 mins (restart auto when accessed)
- Free database expires after 90 days (add payment to continue)

**That's it! You're deployed!** 🚀
