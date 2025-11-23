#!/usr/bin/env python
import os
import json
from app import app, db
from models import User, Admin, MasterAdmin, Package, PaymentMethod, Settings, Ad, Payment, Withdrawal, AdView
from werkzeug.security import generate_password_hash


def migrate_from_json():
    """Migrate existing JSON data to PostgreSQL"""
    
    with app.app_context():
        # Create all tables
        db.create_all()
        
        print("Starting data migration from JSON to PostgreSQL...")
        
        # Load JSON files
        users_data = load_json_file('users.json', [])
        packages_data = load_json_file('packages.json', [])
        settings_data = load_json_file('settings.json', {})
        payments_data = load_json_file('payments.json', [])
        withdraws_data = load_json_file('withdraws.json', [])
        ads_data = load_json_file('ads.json', [])
        ad_views_data = load_json_file('ad_views.json', [])
        
        # Create Master Admin
        master_admin_email = 'masteradmin@yourempire.com'
        if not MasterAdmin.query.filter_by(email=master_admin_email).first():
            master_admin = MasterAdmin(email=master_admin_email)
            master_admin.set_password('Master@lihyder1866')
            db.session.add(master_admin)
            print(f"✓ Created Master Admin: {master_admin_email}")
        else:
            master_admin = MasterAdmin.query.filter_by(email=master_admin_email).first()
            print(f"✓ Master Admin already exists: {master_admin_email}")
        
        db.session.commit()
        
        # Migrate Users
        user_id_map = {}
        for user_data in users_data:
            if not User.query.filter_by(email=user_data['email']).first():
                user = User(
                    email=user_data['email'],
                    full_name=user_data.get('name', user_data['email']),
                    phone=user_data.get('phone', '+92XXXXXXXXXX'),
                    city=user_data.get('city', 'Not specified'),
                    address=user_data.get('address', ''),
                    referral_code=user_data['referral_code'],
                    wallet_balance=user_data.get('wallet', 0.0),
                    is_invested=user_data.get('is_invested', False)
                )
                user.password_hash = user_data['password']
                user_id_map[user_data['id']] = None
                db.session.add(user)
                print(f"✓ Migrated user: {user_data['email']}")
        
        db.session.commit()
        
        # Update referrals
        for user_data in users_data:
            user = User.query.filter_by(email=user_data['email']).first()
            if user and user_data.get('referred_by'):
                referrer = User.query.filter_by(referral_code=user_data.get('referred_by', '')).first()
                if referrer:
                    user.referred_by = referrer.id
                    print(f"✓ Set referral for {user.email} -> {referrer.email}")
        
        db.session.commit()
        
        # Migrate Packages
        for pkg_data in packages_data:
            if not Package.query.filter_by(name=pkg_data['name']).first():
                package = Package(
                    name=pkg_data['name'],
                    price=pkg_data['price']
                )
                db.session.add(package)
                print(f"✓ Migrated package: {pkg_data['name']}")
        
        db.session.commit()
        
        # Migrate Payment Methods
        for pm_data in settings_data.get('payment_methods', []):
            if not PaymentMethod.query.filter_by(account_number=pm_data['account_number']).first():
                pm = PaymentMethod(
                    type=pm_data['type'],
                    account_number=pm_data['account_number'],
                    account_name=pm_data['account_name'],
                    bank_name=pm_data.get('bank_name', '')
                )
                db.session.add(pm)
                print(f"✓ Migrated payment method: {pm_data['type']}")
        
        # Add Default Payment Methods if not already present
        default_methods = [
            {'type': 'Easypaisa', 'account_number': '03001234567', 'account_name': 'YourEmpire Business'},
            {'type': 'JazzCash', 'account_number': '03015678901', 'account_name': 'YourEmpire Official'},
            {'type': 'Sadapay', 'account_number': 'sadapay@yourempire', 'account_name': 'YourEmpire Sadapay'},
            {'type': 'Bank Account', 'account_number': '1234567890123', 'account_name': 'YourEmpire Ltd', 'bank_name': 'HBL'}
        ]
        
        for method in default_methods:
            if not PaymentMethod.query.filter_by(type=method['type']).first():
                pm = PaymentMethod(
                    type=method['type'],
                    account_number=method['account_number'],
                    account_name=method['account_name'],
                    bank_name=method.get('bank_name', '')
                )
                db.session.add(pm)
                print(f"✓ Created default payment method: {method['type']}")
        
        db.session.commit()
        
        # Migrate Settings
        settings_map = {
            'commission_percentage': settings_data.get('commission_percentage', 50),
            'min_withdrawal': settings_data.get('min_withdrawal', 225),
            'ads_enabled': settings_data.get('ads_enabled', True)
        }
        
        for key, value in settings_map.items():
            if not Settings.query.filter_by(key=key).first():
                setting = Settings(key=key, value=str(value))
                db.session.add(setting)
                print(f"✓ Migrated setting: {key}")
        
        db.session.commit()
        
        # Migrate Ads
        for ad_data in ads_data:
            if not Ad.query.filter_by(title=ad_data.get('title', '')).first():
                ad = Ad(
                    title=ad_data.get('title', ''),
                    type=ad_data.get('type', 'image'),
                    media_file=ad_data.get('media_file'),
                    link=ad_data.get('link'),
                    reward=ad_data.get('reward', 0)
                )
                db.session.add(ad)
                print(f"✓ Migrated ad: {ad_data.get('title', 'Unknown')}")
        
        db.session.commit()
        
        print("\n✅ Data migration completed successfully!")
        print("\nDefault Credentials:")
        print(f"Master Admin Email: {master_admin_email}")
        print(f"Master Admin Password: Master@lihyder1866")
        print("\nTo create regular admins, log in to Master Admin dashboard.")

def load_json_file(filename, default):
    """Load JSON file safely"""
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default

if __name__ == '__main__':
    with app.app_context():
    db.create_all()
    migrate_from_json()

