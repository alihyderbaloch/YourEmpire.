# YourEmpire - Deployment to Render (Simple Guide)

## What is Render?
Render is a cloud platform where you can host your web app and database for free/paid. It's like hosting your app on the internet so anyone can access it.

---

## STEP 1: Prepare Your App for Deployment

### 1.1 Create a `requirements.txt` file
This file tells Render what packages your app needs.

Create a new file called `requirements.txt` in your root folder with this content:

```
Flask==3.0.0
Flask-SQLAlchemy==3.1.1
psycopg2-binary==2.9.11
python-dotenv==1.0.0
Werkzeug==3.0.1
Pillow==10.1.0
gunicorn==21.2.0
```

### 1.2 Create a `runtime.txt` file
This tells Render which Python version to use.

Create file `runtime.txt` with:
```
python-3.11.7
```

### 1.3 Create a `Procfile` file
This tells Render how to start your app.

Create file `Procfile` with:
```
web: gunicorn app:app
```

### 1.4 Update `app.py` - Add this line at the TOP after all imports:
```python
import os

# Add this line to allow running on different hosts:
app.config['ENV'] = 'production'
```

---

## STEP 2: Create Render Account

1. Go to **https://render.com**
2. Click **"Sign Up"** (top right)
3. Sign up with:
   - Email: Your email
   - Password: Create a strong password
   - OR use GitHub/Google to sign up
4. Verify your email

---

## STEP 3: Push Your Code to GitHub (REQUIRED)

Render needs your code on GitHub to deploy it.

### 3.1 Create a GitHub Repository
1. Go to **https://github.com** and log in (or create account)
2. Click **"+"** (top right) → **"New repository"**
3. Name it: `yourempire`
4. Make it **PUBLIC** (important!)
5. Click **"Create repository"**

### 3.2 Upload Your Code to GitHub

In Replit terminal, run these commands:

```bash
cd /home/runner/workspace

# Initialize git
git init

# Add all files
git add .

# Create first commit
git commit -m "Initial YourEmpire deployment"

# Add GitHub as remote (replace YOUR_USERNAME and repo name)
git remote add origin https://github.com/YOUR_USERNAME/yourempire.git

# Push to GitHub
git branch -M main
git push -u origin main
```

**Note:** Replace `YOUR_USERNAME` with your actual GitHub username.

---

## STEP 4: Create PostgreSQL Database on Render

1. Go back to **https://render.com** (logged in)
2. Click **"+ New +"** button (top right)
3. Select **"PostgreSQL"**
4. Fill in:
   - **Name:** `yourempire-db`
   - **Database:** `yourempire`
   - **User:** `admin`
   - **Region:** Choose closest to you
   - **PostgreSQL Version:** 15
5. Click **"Create Database"**
6. **WAIT** 2-3 minutes for database to be created
7. Once created, you'll see a **Connection String** - **COPY THIS AND SAVE IT SOMEWHERE SAFE**

The connection string looks like:
```
postgresql://admin:PASSWORD@hostname:5432/yourempire
```

---

## STEP 5: Deploy Your Flask App on Render

1. Go to **https://render.com** (logged in)
2. Click **"+ New +"** button (top right)
3. Select **"Web Service"**
4. Connect GitHub:
   - Click **"Connect account"**
   - Authorize Render to access GitHub
   - Select repository: `yourempire`
5. Fill in settings:
   - **Name:** `yourempire-app`
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
   - **Region:** Same as your database
6. Click **"Create Web Service"**

---

## STEP 6: Add Environment Variables

After creating the service:

1. On Render dashboard, click your `yourempire-app` service
2. Go to **"Environment"** tab (left sidebar)
3. Click **"Add Environment Variable"**
4. Add these variables:

| Key | Value |
|-----|-------|
| `DATABASE_URL` | Paste the connection string from Step 4 |
| `FLASK_ENV` | `production` |
| `SECRET_KEY` | Generate random string (use: `python -c "import secrets; print(secrets.token_hex(32))"`) |
| `SESSION_SECRET` | Same as SECRET_KEY |

5. Click **"Save"**

---

## STEP 7: Deploy Your App

After adding environment variables:

1. The app will automatically start deploying
2. Go to **"Logs"** tab to watch deployment
3. **WAIT** 3-5 minutes for deployment to complete
4. Once you see: `"Listening on port 10000"` - it's LIVE! ✅
5. Click the URL at the top to visit your app

---

## STEP 8: Initialize Database on Render

Your database is empty. You need to create tables and add default data.

### Option A: Use Python Script (Easiest)

1. In Replit, run this in the terminal:
```bash
# Connect to Render database and initialize
python -c "
import os
os.environ['DATABASE_URL'] = 'PASTE_YOUR_CONNECTION_STRING_HERE'
from app import app, db
with app.app_context():
    db.create_all()
    print('Database created!')
"
```

Replace `PASTE_YOUR_CONNECTION_STRING_HERE` with your actual connection string.

### Option B: Use Render Shell
1. On Render dashboard, go to your database service
2. Click **"Connect"**
3. Click **"Using psql"**
4. Copy the command and run in terminal
5. Then run: `\q` to exit

---

## STEP 9: Test Your Live App

1. Click the URL given by Render (looks like: `https://yourempire-app.onrender.com`)
2. You should see your YourEmpire homepage! 🎉
3. Test:
   - Click **"Register"** - try creating account
   - Click **"Login"** - try logging in with existing account
   - Test **"Admin"** - try Master Admin login with:
     - Email: `masteradmin@yourempire.com`
     - Password: `Master@lihyder1866`

---

## STEP 10: Update Code (In Future)

Whenever you update code in Replit:

```bash
cd /home/runner/workspace
git add .
git commit -m "Your message here"
git push origin main
```

Render will automatically redeploy your app within 1-2 minutes!

---

## TROUBLESHOOTING

### App shows "Service Unavailable"
- Check logs on Render dashboard
- Wait 5 more minutes
- Restart service (Settings → Restart)

### Database connection error
- Check `DATABASE_URL` environment variable is correct
- Make sure database is running (check Render dashboard)

### App runs locally but not on Render
- Make sure all required packages are in `requirements.txt`
- Check that `Procfile` is correct
- Check `gunicorn` command works

---

## IMPORTANT NOTES

✅ **Free Plan Includes:**
- 1 web service
- 1 PostgreSQL database
- Auto-sleep if no traffic (free tier)

⚠️ **Important:**
- Render free tier apps sleep after 15 mins of no activity (restart automatically when accessed)
- Free database is limited to 90 days - then you need to add payment method
- Keep your GitHub repo updated

---

## Need Help?

Common Issues & Solutions:

| Problem | Solution |
|---------|----------|
| App won't deploy | Check `Procfile` and `requirements.txt` |
| Database won't connect | Verify `DATABASE_URL` in Environment |
| Registration not working | Check database was initialized |
| Admin login fails | Make sure database has Master Admin data |

---

**That's it! Your app is now LIVE on the internet!** 🚀
