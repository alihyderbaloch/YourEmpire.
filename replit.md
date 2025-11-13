# YourEmpire - Network Marketing Platform

## Overview
YourEmpire is a complete full-stack network marketing platform built with Flask, Python, and TailwindCSS. It features a referral system, package purchases, wallet management, ad watching rewards, and comprehensive admin controls. All data is stored locally in JSON files for 100% offline operation.

## Key Features

### User Features
- **Registration & Login**: Secure user authentication with password hashing
- **Referral System**: Auto-generated referral codes (YE####) with commission tracking
- **Package Purchases**: Buy packages (Bronze, Silver, Diamond, Platinum) via multiple payment methods
- **Wallet System**: Track earnings, commissions, and ad rewards
- **Withdrawal Requests**: Request withdrawals to Easypaisa, JazzCash, or bank accounts
- **Ad Watching**: Earn micro-rewards (PKR) by viewing ads uploaded by admin
- **Dashboard**: View referral code, wallet balance, payment/withdrawal history

### Admin Features
- **User Management**: View all users, adjust wallet balances manually
- **Payment Method Management**: Add/edit/delete payment methods (Easypaisa, JazzCash, bank accounts) with account details
- **Payment Approval**: Approve or reject user package purchases
- **Withdrawal Management**: Approve or reject withdrawal requests
- **Package Management**: Add, edit, or delete packages
- **Commission Settings**: Adjust global commission percentage (default 50%)
- **Withdrawal Limits**: Set minimum withdrawal amount
- **Ad Management**: Upload video/image/link ads, set rewards per view, track analytics
- **System Settings**: Enable/disable ad section, set contact information
- **Password Management**: Change admin password

## Technology Stack
- **Backend**: Flask (Python 3.11)
- **Frontend**: TailwindCSS via CDN
- **Data Storage**: JSON files (users.json, packages.json, payments.json, withdraws.json, ads.json, ad_views.json, settings.json)
- **Security**: Werkzeug password hashing, session-based authentication
- **File Uploads**: Pillow for image processing

## Project Structure
```
/YourEmpire
├── app.py                          # Main Flask application
├── users.json                      # User data and wallets
├── packages.json                   # Available packages
├── payments.json                   # Payment history
├── withdraws.json                  # Withdrawal requests
├── ads.json                        # Ad data
├── ad_views.json                   # Ad view tracking
├── settings.json                   # System settings & payment methods
├── templates/                      # HTML templates
│   ├── index.html                 # Landing page
│   ├── register.html              # User registration
│   ├── login.html                 # Login page
│   ├── forgot_password.html       # Password reset request
│   ├── user_dashboard.html        # User dashboard
│   ├── buy_package.html           # Package purchase form
│   ├── withdraw.html              # Withdrawal request form
│   ├── watch_ads.html             # Ad watching interface
│   ├── admin_dashboard.html       # Admin control panel
│   ├── manage_ads.html            # Ad management
│   └── change_admin_password.html # Admin password change
├── static/
│   ├── uploads/                   # Payment screenshots
│   └── ads/                       # Ad media files
└── replit.md                      # This file
```

## Default Login Credentials
- **Admin Email**: admin@yourempire.com
- **Admin Password**: admin123
- **Note**: Change admin password immediately after first login

## Default Settings
- Commission Percentage: 50%
- Minimum Withdrawal: 225 PKR
- Ads Enabled: Yes
- Default Payment Methods: Easypaisa, JazzCash, Bank Account (with sample details)

## Packages
1. **Bronze**: 450 PKR
2. **Silver**: 1000 PKR
3. **Diamond**: 1250 PKR
4. **Platinum**: 2000 PKR

## How It Works

### Referral Commission Flow
1. User A registers and gets referral code (e.g., YE1234)
2. User B registers using User A's referral code
3. User B buys a package and submits payment
4. Admin approves the payment
5. User A automatically receives 50% commission in their wallet

### Ad Rewards Flow
1. Admin uploads an ad (video/image/link) with a reward amount
2. Admin enables the ad section for users
3. User views/clicks the ad
4. Reward is automatically credited to user's wallet
5. Each ad can only be claimed once per day per user

### Withdrawal Flow
1. User requests withdrawal (minimum 225 PKR)
2. Admin reviews and approves the request
3. Amount is automatically deducted from user's wallet
4. Admin processes payment to user's account

## Admin-Controlled Payment Methods
The admin can manage payment methods that users see when purchasing packages:
- Add new payment methods (Easypaisa, JazzCash, Bank Account)
- Edit account numbers and account names
- Delete payment methods
- All payment details are displayed to users during package purchase

## Security Features
- Password hashing with Werkzeug PBKDF2
- Session-based authentication
- File upload validation (5MB limit)
- Secure file naming
- Admin-only routes protected by decorators

## Design
- Purple-blue gradient theme
- Fully responsive (mobile and desktop)
- Modern card-based UI
- TailwindCSS utility classes
- Glass-morphism effects

## Running the Application
The Flask server runs on port 5000:
```bash
python app.py
```
Access at: http://localhost:5000

## Recent Changes
- 2025-11-13: Initial project creation with all features implemented
- Payment method management system added with admin controls
- All templates created with responsive design
- Ad watching system with daily limits implemented
- Referral commission system with automatic wallet updates

## Notes
- All data is stored locally in JSON files
- No external APIs or databases required
- 100% offline operation
- Made with ❤️ by YourEmpire
