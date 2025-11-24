import os
import json
from datetime import datetime, timedelta
from functools import wraps
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_from_directory
from models import db, User, Admin, MasterAdmin, Package, Payment, Withdrawal, PaymentMethod, Ad, AdView, Settings, Announcement, GuideVideo, PasswordResetRequest, ProfileUpdateRequest, LoginHistory
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SESSION_SECRET', 'yourempire-secret-key-change-in-production')
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ADS_FOLDER'] = 'static/ads'
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///yourempire.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 3600,
    'pool_size': 10,
    'max_overflow': 20,
    'connect_args': {'connect_timeout': 10, 'sslmode': 'allow'}
}

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf', 'mp4', 'webm'}

db.init_app(app)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in first.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session and 'master_admin_id' not in session:
            flash('Admin access required.', 'error')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def master_admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'master_admin_id' not in session:
            flash('Master Admin access required.', 'error')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def get_setting(key, default=None):
    setting = Settings.query.filter_by(key=key).first()
    return setting.value if setting else default

def set_setting(key, value):
    setting = Settings.query.filter_by(key=key).first()
    if setting:
        setting.value = str(value)
    else:
        setting = Settings(key=key, value=str(value))
        db.session.add(setting)
    db.session.commit()

def init_default_settings():
    # Create default settings
    if not Settings.query.first():
        defaults = {
            'commission_percentage': '50',
            'min_withdrawal': '225',
            'ads_enabled': 'true',
            'maintenance_mode': 'false'
        }
        for key, value in defaults.items():
            setting = Settings(key=key, value=value)
            db.session.add(setting)
        db.session.commit()
    
    # Create default Master Admin if not exist
    if not MasterAdmin.query.first():
        master_admin = MasterAdmin(email='admin@yourempire.com')
        master_admin.set_password('admin123')
        db.session.add(master_admin)
        db.session.commit()
    
    # Create default packages if not exist
    if not Package.query.first():
        packages = [
            Package(name='Bronze', price=450),
            Package(name='Silver', price=1000),
            Package(name='Diamond', price=1250),
            Package(name='Platinum', price=2000)
        ]
        db.session.add_all(packages)
        db.session.commit()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        full_name = request.form.get('full_name')
        phone = request.form.get('phone')
        city = request.form.get('city')
        address = request.form.get('address', '')
        referral_code = request.form.get('referral_code', '').strip()
        
        if len(password) < 8:
            flash('Password must be at least 8 characters!', 'error')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered!', 'error')
            return redirect(url_for('register'))
        
        referred_by = None
        if referral_code:
            referrer = User.query.filter_by(referral_code=referral_code).first()
            if referrer:
                referred_by = referrer.id
            else:
                flash('Invalid referral code!', 'error')
                return redirect(url_for('register'))
        
        new_user = User(
            email=email,
            full_name=full_name,
            phone=phone,
            city=city,
            address=address,
            referral_code=User.generate_referral_code(),
            referred_by=referred_by
        )
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    
    ref_code = request.args.get('ref', '')
    return render_template('register.html', ref_code=ref_code)

@app.route('/login', methods=['GET', 'POST'])
def login():
    maintenance = get_setting('maintenance_mode', 'false').lower() == 'true'
    if maintenance and request.method == 'POST':
        return render_template('maintenance.html'), 503
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Check Master Admin first
        master_admin = MasterAdmin.query.filter_by(email=email).first()
        if master_admin and master_admin.check_password(password):
            session['master_admin_id'] = master_admin.id
            session['admin_email'] = email
            login_log = LoginHistory(master_admin_id=master_admin.id, login_type='master', ip_address=request.remote_addr)
            db.session.add(login_log)
            db.session.commit()
            flash('Master Admin login successful!', 'success')
            return redirect(url_for('master_admin_dashboard'))
        
        # Check Admin
        admin = Admin.query.filter_by(email=email, is_active=True).first()
        if admin and admin.check_password(password):
            session['admin_id'] = admin.id
            session['admin_email'] = email
            login_log = LoginHistory(admin_id=admin.id, login_type='admin', ip_address=request.remote_addr)
            db.session.add(login_log)
            db.session.commit()
            flash('Admin login successful!', 'success')
            return redirect(url_for('admin_dashboard'))
        
        # Check Regular User
        user = User.query.filter_by(email=email, is_active=True).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['user_name'] = user.full_name
            login_log = LoginHistory(user_id=user.id, login_type='user', ip_address=request.remote_addr)
            db.session.add(login_log)
            db.session.commit()
            flash(f'Welcome back, {user.full_name}!', 'success')
            return redirect(url_for('user_dashboard'))
        
        flash('Invalid email or password!', 'error')
        return redirect(url_for('login'))
    
    return render_template('login.html')

@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    # Redirect to unified login page
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        
        if user:
            existing_request = PasswordResetRequest.query.filter_by(user_id=user.id, status='Pending').first()
            if not existing_request:
                reset_request = PasswordResetRequest(user_id=user.id)
                db.session.add(reset_request)
                db.session.commit()
                flash('Password reset request submitted. Master Admin will contact you soon.', 'success')
            else:
                flash('You already have a pending reset request.', 'info')
        else:
            flash('Email not found!', 'error')
        
        return redirect(url_for('login'))
    
    return render_template('forgot_password.html')

@app.route('/dashboard')
@login_required
def user_dashboard():
    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('login'))
    
    payments = Payment.query.filter_by(user_id=user.id).all()
    withdrawals = Withdrawal.query.filter_by(user_id=user.id).all()
    ad_views = AdView.query.filter_by(user_id=user.id).all()
    total_ad_earnings = sum(av.ad.reward for av in ad_views)
    ads_enabled = get_setting('ads_enabled', 'true').lower() == 'true'
    referrals = User.query.filter_by(referred_by=user.id).all()
    announcements = Announcement.query.filter_by(is_active=True).all()
    guide_videos = GuideVideo.query.all()
    
    return render_template('user_dashboard.html', 
                         user=user, 
                         payments=payments,
                         withdrawals=withdrawals,
                         ads_enabled=ads_enabled,
                         total_ad_earnings=total_ad_earnings,
                         referrals=referrals,
                         announcements=announcements,
                         guide_videos=guide_videos)

@app.route('/user-profile')
@login_required
def user_profile():
    user = User.query.get(session['user_id'])
    referral_tree = []
    
    def build_tree(u):
        return {
            'id': u.id,
            'name': u.full_name,
            'email': u.email,
            'is_invested': u.is_invested,
            'children': [build_tree(ref) for ref in u.referred_users]
        }
    
    referral_tree = build_tree(user)
    pending_updates = ProfileUpdateRequest.query.filter_by(user_id=user.id, status='Pending').all()
    
    return render_template('user_profile.html', user=user, referral_tree=referral_tree, pending_updates=pending_updates)

@app.route('/update-profile', methods=['POST'])
@login_required
def update_profile():
    user = User.query.get(session['user_id'])
    update_type = request.form.get('update_type')
    new_value = request.form.get('new_value')
    
    if update_type == 'password' and len(new_value) < 8:
        flash('Password must be at least 8 characters!', 'error')
        return redirect(url_for('user_profile'))
    
    update_request = ProfileUpdateRequest(user_id=user.id, update_type=update_type, new_value=new_value)
    db.session.add(update_request)
    db.session.commit()
    
    flash('Update request submitted. Admin will review it.', 'success')
    return redirect(url_for('user_profile'))

@app.route('/buy-package', methods=['GET', 'POST'])
@login_required
def buy_package():
    if request.method == 'POST':
        package_id = int(request.form.get('package_id'))
        payment_method_id = int(request.form.get('payment_method'))
        transaction_id = request.form.get('transaction_id')
        
        package = Package.query.get(package_id)
        payment_method = PaymentMethod.query.get(payment_method_id)
        
        if not package or not payment_method:
            flash('Invalid package or payment method!', 'error')
            return redirect(url_for('buy_package'))
        
        screenshot = None
        if 'screenshot' in request.files:
            file = request.files['screenshot']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(f"{session['user_id']}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}")
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                screenshot = filename
        
        new_payment = Payment(
            user_id=session['user_id'],
            package_id=package_id,
            amount=package.price,
            payment_method_id=payment_method_id,
            transaction_id=transaction_id,
            screenshot=screenshot
        )
        
        db.session.add(new_payment)
        db.session.commit()
        
        flash('Payment submitted successfully! Waiting for admin approval.', 'success')
        return redirect(url_for('user_dashboard'))
    
    packages = Package.query.all()
    payment_methods = PaymentMethod.query.all()
    
    return render_template('buy_package.html', packages=packages, payment_methods=payment_methods)

@app.route('/withdraw', methods=['GET', 'POST'])
@login_required
def withdraw():
    user = User.query.get(session['user_id'])
    min_withdrawal = float(get_setting('min_withdrawal', 225))
    
    if request.method == 'POST':
        amount = float(request.form.get('amount'))
        payment_method = request.form.get('payment_method')
        account_number = request.form.get('account_number')
        account_name = request.form.get('account_name')
        
        if amount < min_withdrawal:
            flash(f'Minimum withdrawal amount is {min_withdrawal} PKR!', 'error')
            return redirect(url_for('withdraw'))
        
        if amount > user.wallet_balance:
            flash('Insufficient balance!', 'error')
            return redirect(url_for('withdraw'))
        
        new_withdrawal = Withdrawal(
            user_id=user.id,
            amount=amount,
            payment_method=payment_method,
            account_number=account_number,
            account_name=account_name
        )
        
        db.session.add(new_withdrawal)
        db.session.commit()
        
        flash('Withdrawal request submitted! Waiting for admin approval.', 'success')
        return redirect(url_for('user_dashboard'))
    
    return render_template('withdraw.html', user=user, min_withdrawal=min_withdrawal)

@app.route('/watch-ads')
@login_required
def watch_ads():
    ads_enabled = get_setting('ads_enabled', 'true').lower() == 'true'
    if not ads_enabled:
        flash('Ad section is currently disabled.', 'info')
        return redirect(url_for('user_dashboard'))
    
    today = datetime.utcnow().strftime('%Y-%m-%d')
    user_today_views = db.session.query(AdView).filter(
        AdView.user_id == session['user_id'],
        db.func.date(AdView.viewed_at) == today
    ).all()
    viewed_ad_ids = [av.ad_id for av in user_today_views]
    
    available_ads = Ad.query.filter(Ad.is_active == True, Ad.id.notin_(viewed_ad_ids)).all()
    ad_history = AdView.query.filter_by(user_id=session['user_id']).all()
    
    return render_template('watch_ads.html', ads=available_ads, ad_history=ad_history)

@app.route('/view-ad/<int:ad_id>')
@login_required
def view_ad(ad_id):
    ad = Ad.query.get(ad_id)
    
    if not ad:
        flash('Ad not found!', 'error')
        return redirect(url_for('watch_ads'))
    
    today = datetime.utcnow().strftime('%Y-%m-%d')
    already_viewed = db.session.query(AdView).filter(
        AdView.user_id == session['user_id'],
        AdView.ad_id == ad_id,
        db.func.date(AdView.viewed_at) == today
    ).first()
    
    if already_viewed:
        flash('You have already viewed this ad today!', 'info')
        return redirect(url_for('watch_ads'))
    
    new_view = AdView(user_id=session['user_id'], ad_id=ad_id)
    db.session.add(new_view)
    
    user = User.query.get(session['user_id'])
    user.wallet_balance += ad.reward
    
    db.session.commit()
    
    flash(f'You earned {ad.reward} PKR for viewing this ad!', 'success')
    return redirect(url_for('watch_ads'))

@app.route('/master-admin/dashboard')
@master_admin_required
def master_admin_dashboard():
    total_users = User.query.count()
    total_admins = Admin.query.count()
    pending_password_resets = PasswordResetRequest.query.filter_by(status='Pending').count()
    pending_profile_updates = ProfileUpdateRequest.query.filter_by(status='Pending').count()
    
    stats = {
        'total_users': total_users,
        'total_admins': total_admins,
        'pending_password_resets': pending_password_resets,
        'pending_profile_updates': pending_profile_updates
    }
    
    admins = Admin.query.all()
    return render_template('master_admin_dashboard.html', stats=stats, admins=admins)

@app.route('/master-admin/add-admin', methods=['POST'])
@master_admin_required
def add_admin():
    email = request.form.get('email')
    password = request.form.get('password')
    
    if Admin.query.filter_by(email=email).first():
        flash('Email already exists!', 'error')
        return redirect(url_for('master_admin_dashboard'))
    
    new_admin = Admin(email=email, created_by_master_id=session['master_admin_id'])
    new_admin.set_password(password)
    
    db.session.add(new_admin)
    db.session.commit()
    
    flash('Admin added successfully!', 'success')
    return redirect(url_for('master_admin_dashboard'))

@app.route('/master-admin/deactivate-admin/<int:admin_id>')
@master_admin_required
def deactivate_admin(admin_id):
    admin = Admin.query.get(admin_id)
    if admin:
        admin.is_active = False
        db.session.commit()
        flash('Admin deactivated!', 'success')
    return redirect(url_for('master_admin_dashboard'))

@app.route('/master-admin/approve-password-reset/<int:request_id>', methods=['POST'])
@master_admin_required
def approve_password_reset(request_id):
    new_password = request.form.get('new_password')
    reset_req = PasswordResetRequest.query.get(request_id)
    
    if reset_req and len(new_password) >= 8:
        reset_req.status = 'Resolved'
        reset_req.resolved_by_master_admin_id = session['master_admin_id']
        reset_req.resolved_at = datetime.utcnow()
        
        user = reset_req.user
        user.set_password(new_password)
        
        db.session.commit()
        flash('Password reset completed!', 'success')
    else:
        flash('Invalid request or password!', 'error')
    
    return redirect(url_for('master_admin_dashboard'))

@app.route('/master-admin/maintenance-mode', methods=['POST'])
@master_admin_required
def toggle_maintenance_mode():
    current = get_setting('maintenance_mode', 'false').lower() == 'true'
    set_setting('maintenance_mode', 'false' if current else 'true')
    flash('Maintenance mode toggled!', 'success')
    return redirect(url_for('master_admin_dashboard'))

@app.route('/master-admin/change-master-password', methods=['POST'])
@master_admin_required
def change_master_admin_password():
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    master_admin = MasterAdmin.query.get(session['master_admin_id'])
    
    if not master_admin:
        flash('Master Admin not found!', 'error')
        return redirect(url_for('master_admin_dashboard'))
    
    if not master_admin.check_password(current_password):
        flash('Current password is incorrect!', 'error')
        return redirect(url_for('master_admin_dashboard'))
    
    if len(new_password) < 8:
        flash('Password must be at least 8 characters!', 'error')
        return redirect(url_for('master_admin_dashboard'))
    
    if new_password != confirm_password:
        flash('Passwords do not match!', 'error')
        return redirect(url_for('master_admin_dashboard'))
    
    master_admin.set_password(new_password)
    db.session.commit()
    flash('Master Admin password changed successfully!', 'success')
    return redirect(url_for('master_admin_dashboard'))

@app.route('/master-admin/change-user-password', methods=['POST'])
@master_admin_required
def admin_change_user_password():
    user_email = request.form.get('user_email')
    new_password = request.form.get('new_password')
    
    if len(new_password) < 8:
        flash('Password must be at least 8 characters!', 'error')
        return redirect(url_for('master_admin_dashboard'))
    
    user = User.query.filter_by(email=user_email).first()
    
    if not user:
        flash('User not found!', 'error')
        return redirect(url_for('master_admin_dashboard'))
    
    user.set_password(new_password)
    db.session.commit()
    flash(f'Password changed for user {user_email}!', 'success')
    return redirect(url_for('master_admin_dashboard'))

@app.route('/master-admin/change-admin-password', methods=['POST'])
@master_admin_required
def admin_change_admin_password():
    admin_email = request.form.get('admin_email')
    new_password = request.form.get('new_password')
    
    if len(new_password) < 8:
        flash('Password must be at least 8 characters!', 'error')
        return redirect(url_for('master_admin_dashboard'))
    
    admin = Admin.query.filter_by(email=admin_email).first()
    
    if not admin:
        flash('Admin not found!', 'error')
        return redirect(url_for('master_admin_dashboard'))
    
    admin.set_password(new_password)
    db.session.commit()
    flash(f'Password changed for admin {admin_email}!', 'success')
    return redirect(url_for('master_admin_dashboard'))

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    users = User.query.all()
    payments = Payment.query.all()
    withdrawals = Withdrawal.query.all()
    packages = Package.query.all()
    ads = Ad.query.all()
    payment_methods = PaymentMethod.query.all()
    
    # Get all settings
    settings_list = Settings.query.all()
    settings = {s.key: s.value for s in settings_list}
    
    # Add referrer code to each user
    for user in users:
        if user.referred_by:
            referrer = User.query.get(user.referred_by)
            user.referrer_code = referrer.referral_code if referrer else None
        else:
            user.referrer_code = None
    
    stats = {
        'total_users': len(users),
        'total_payments': len([p for p in payments if p.status == 'Approved']),
        'total_withdrawals': len([w for w in withdrawals if w.status == 'Approved']),
        'pending_payments': len([p for p in payments if p.status == 'Pending']),
        'pending_withdrawals': len([w for w in withdrawals if w.status == 'Pending']),
        'total_ad_views': len(AdView.query.all())
    }
    
    return render_template('admin_dashboard.html', 
                         users=users,
                         payments=payments,
                         withdrawals=withdrawals,
                         packages=packages,
                         ads=ads,
                         payment_methods=payment_methods,
                         settings=settings,
                         stats=stats)

@app.route('/admin/approve-payment/<int:payment_id>')
@admin_required
def approve_payment(payment_id):
    payment = Payment.query.get(payment_id)
    
    if payment and payment.status == 'Pending':
        payment.status = 'Approved'
        payment.approved_by_admin_id = session.get('admin_id')
        
        commission_rate = float(get_setting('commission_percentage', 50)) / 100
        user = payment.user
        
        if user.referred_by:
            commission = payment.amount * commission_rate
            referrer = User.query.get(user.referred_by)
            referrer.wallet_balance += commission
            flash(f'Payment approved! Commission of {commission} PKR credited to referrer.', 'success')
        else:
            flash('Payment approved!', 'success')
        
        db.session.commit()
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/approve-payment-screenshot/<int:payment_id>')
@admin_required
def view_payment_screenshot(payment_id):
    payment = Payment.query.get(payment_id)
    if payment and payment.screenshot:
        return send_from_directory(app.config['UPLOAD_FOLDER'], payment.screenshot)
    return "File not found", 404

@app.route('/admin/reject-payment/<int:payment_id>')
@admin_required
def reject_payment(payment_id):
    payment = Payment.query.get(payment_id)
    if payment:
        payment.status = 'Rejected'
        db.session.commit()
        flash('Payment rejected!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/approve-withdrawal/<int:withdrawal_id>')
@admin_required
def approve_withdrawal(withdrawal_id):
    withdrawal = Withdrawal.query.get(withdrawal_id)
    
    if withdrawal and withdrawal.status == 'Pending':
        user = withdrawal.user
        
        if user.wallet_balance >= withdrawal.amount:
            withdrawal.status = 'Approved'
            withdrawal.approved_by_admin_id = session.get('admin_id')
            user.wallet_balance -= withdrawal.amount
            db.session.commit()
            flash('Withdrawal approved and amount deducted from wallet!', 'success')
        else:
            flash('User has insufficient balance!', 'error')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/reject-withdrawal/<int:withdrawal_id>')
@admin_required
def reject_withdrawal(withdrawal_id):
    withdrawal = Withdrawal.query.get(withdrawal_id)
    if withdrawal:
        withdrawal.status = 'Rejected'
        db.session.commit()
        flash('Withdrawal rejected!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/mark-invested/<int:user_id>')
@admin_required
def mark_invested(user_id):
    user = User.query.get(user_id)
    if user:
        user.is_invested = True
        db.session.commit()
        flash('User marked as invested!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/view-user-tree/<int:user_id>')
@admin_required
def view_user_tree(user_id):
    user = User.query.get(user_id)
    if not user:
        flash('User not found!', 'error')
        return redirect(url_for('admin_dashboard'))
    
    def build_tree(u, depth=0):
        if depth > 10:
            return None
        return {
            'id': u.id,
            'name': u.full_name,
            'email': u.email,
            'is_invested': u.is_invested,
            'wallet': u.wallet_balance,
            'children': [build_tree(ref, depth+1) for ref in u.referred_users]
        }
    
    tree = build_tree(user)
    return render_template('user_tree.html', user=user, tree=tree)

@app.route('/admin/ad-analytics')
@admin_required
def ad_analytics():
    # Get all ads
    ads = Ad.query.all()
    
    ads_data = []
    summary = {'total_ads': len(ads), 'total_views': 0, 'total_rewards': 0, 'active_users': 0}
    
    for ad in ads:
        # Count UNIQUE user-ad combinations (each user can view once per day)
        unique_viewers = db.session.query(AdView.user_id).filter_by(ad_id=ad.id).distinct().count()
        total_paid = unique_viewers * ad.reward
        
        ads_data.append({
            'id': ad.id,
            'title': ad.title,
            'type': ad.type,
            'views': unique_viewers,
            'reward': ad.reward,
            'total_paid': total_paid,
            'is_active': ad.is_active
        })
        
        summary['total_views'] += unique_viewers
        summary['total_rewards'] += total_paid
    
    # Get unique users who watched ads
    unique_viewers = db.session.query(AdView.user_id).distinct().count()
    summary['active_users'] = unique_viewers
    
    # Get viewer details - count unique user-ad pairs only
    viewers_data = []
    unique_views = db.session.query(AdView.user_id, AdView.ad_id, db.func.max(AdView.viewed_at).label('last_viewed')).group_by(AdView.user_id, AdView.ad_id).all()
    
    for view in unique_views:
        user = User.query.get(view.user_id)
        ad = Ad.query.get(view.ad_id)
        if user and ad:
            viewers_data.append({
                'ad_title': ad.title,
                'user_name': user.full_name,
                'view_count': 1,
                'reward_earned': ad.reward,
                'last_viewed': view.last_viewed
            })
    
    return render_template('ad_analytics.html', ads_data=ads_data, viewers_data=viewers_data, summary=summary)

@app.route('/admin/commission-tracking', methods=['GET', 'POST'])
@admin_required
def commission_tracking():
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        user = User.query.get(user_id)
        if user:
            # Mark all pending commissions as paid for this user
            for referral in user.referred_users:
                paid_payments = Payment.query.filter_by(user_id=referral.id, status='Approved').all()
                for payment in paid_payments:
                    # Add pending commission to wallet
                    try:
                        commission_rate = float(get_setting('commission_percentage', 50)) / 100
                    except:
                        commission_rate = 0.5
                    commission = payment.amount * commission_rate
                    user.wallet_balance += commission
            db.session.commit()
            flash(f'Commissions marked as paid for {user.full_name}!', 'success')
    
    # Get all users
    all_users = User.query.all()
    
    commissions = []
    summary = {'total_pending': 0, 'total_paid': 0, 'active_sellers': 0}
    
    try:
        commission_rate = float(get_setting('commission_percentage', 50)) / 100
    except:
        commission_rate = 0.5
    
    # Calculate commissions for users with referrals
    for user in all_users:
        if user.referred_users and len(user.referred_users) > 0:
            total_referrals = len(user.referred_users)
            paid_referrals = 0
            pending_commission = 0
            
            for referral in user.referred_users:
                payments = Payment.query.filter_by(user_id=referral.id, status='Approved').all()
                if payments:
                    paid_referrals += 1
                    for payment in payments:
                        pending_commission += payment.amount * commission_rate
            
            if pending_commission > 0 or total_referrals > 0:
                commissions.append({
                    'user_id': user.id,
                    'user_name': user.full_name,
                    'referral_code': user.referral_code,
                    'total_referrals': total_referrals,
                    'paid_referrals': paid_referrals,
                    'pending_commission': pending_commission,
                    'paid_commission': 0
                })
                
                summary['total_pending'] += pending_commission
                summary['active_sellers'] += 1
    
    summary['total_paid'] = 0
    
    return render_template('commission_tracking.html', commissions=commissions, summary=summary)

@app.route('/admin/profile-updates')
@admin_required
def profile_updates():
    pending_updates = ProfileUpdateRequest.query.filter_by(status='Pending').all()
    return render_template('profile_updates.html', updates=pending_updates)

@app.route('/admin/approve-profile-update/<int:update_id>')
@admin_required
def approve_profile_update(update_id):
    update_req = ProfileUpdateRequest.query.get(update_id)
    
    if update_req:
        user = update_req.user
        update_req.status = 'Approved'
        update_req.approved_by_admin_id = session.get('admin_id')
        
        if update_req.update_type == 'phone':
            user.phone = update_req.new_value
        elif update_req.update_type == 'city':
            user.city = update_req.new_value
        elif update_req.update_type == 'address':
            user.address = update_req.new_value
        elif update_req.update_type == 'password':
            user.set_password(update_req.new_value)
        
        db.session.commit()
        flash('Profile update approved!', 'success')
    
    return redirect(url_for('profile_updates'))

@app.route('/admin/reject-profile-update/<int:update_id>')
@admin_required
def reject_profile_update(update_id):
    update_req = ProfileUpdateRequest.query.get(update_id)
    if update_req:
        update_req.status = 'Rejected'
        db.session.commit()
        flash('Profile update rejected!', 'success')
    return redirect(url_for('profile_updates'))

@app.route('/admin/manage-payment-methods', methods=['POST'])
@admin_required
def manage_payment_methods():
    try:
        action = request.form.get('action')
        
        if action == 'add':
            new_method = PaymentMethod(
                type=request.form.get('type'),
                account_number=request.form.get('account_number'),
                account_name=request.form.get('account_name'),
                bank_name=request.form.get('bank_name', '')
            )
            db.session.add(new_method)
            flash('Payment method added!', 'success')
        
        elif action == 'edit':
            method_id = request.form.get('method_id')
            if method_id:
                method = PaymentMethod.query.get(int(method_id))
                if method:
                    method.type = request.form.get('type')
                    method.account_number = request.form.get('account_number')
                    method.account_name = request.form.get('account_name')
                    method.bank_name = request.form.get('bank_name', '')
                    flash('Payment method updated!', 'success')
        
        
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'error')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete-all-payment-methods', methods=['POST'])
@admin_required
def delete_all_payment_methods():
    try:
        # First delete all payments that reference payment methods
        Payment.query.delete()
        db.session.flush()
        
        # Then delete all payment methods
        PaymentMethod.query.delete()
        db.session.commit()
        flash('✅ All payment methods and their payments deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'❌ Error deleting payment methods: {str(e)}', 'error')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/manage-packages', methods=['POST'])
@admin_required
def manage_packages():
    action = request.form.get('action')
    
    if action == 'add':
        new_package = Package(
            name=request.form.get('name'),
            price=float(request.form.get('price')),
            description=request.form.get('description', '')
        )
        db.session.add(new_package)
        flash('Package added!', 'success')
    
    elif action == 'edit':
        package = Package.query.get(int(request.form.get('package_id')))
        if package:
            package.name = request.form.get('name')
            package.price = float(request.form.get('price'))
            package.description = request.form.get('description', '')
            flash('Package updated!', 'success')
    
    elif action == 'delete':
        package = Package.query.get(int(request.form.get('package_id')))
        if package:
            db.session.delete(package)
            flash('Package deleted!', 'success')
    
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/manage-ads', methods=['GET', 'POST'])
@admin_required
def manage_ads():
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'add':
            ad_type = request.form.get('ad_type')
            media_data = None
            media_mime_type = None
            link = None
            
            if ad_type in ['video', 'image']:
                if 'media_file' in request.files:
                    file = request.files['media_file']
                    if file and file.filename and allowed_file(file.filename):
                        media_data = file.read()
                        media_mime_type = file.content_type
            elif ad_type == 'link':
                link = request.form.get('link')
            
            new_ad = Ad(
                title=request.form.get('title'),
                type=ad_type,
                media_data=media_data,
                media_mime_type=media_mime_type,
                link=link,
                reward=float(request.form.get('reward'))
            )
            db.session.add(new_ad)
            flash('Ad added! (Stored permanently in database)', 'success')
        
        elif action == 'delete':
            ad = Ad.query.get(int(request.form.get('ad_id')))
            if ad:
                db.session.delete(ad)
                flash('Ad deleted!', 'success')
        
        db.session.commit()
    
    ads = Ad.query.all()
    return render_template('manage_ads.html', ads=ads)

@app.route('/ad-media/<int:ad_id>')
def get_ad_media(ad_id):
    ad = Ad.query.get(ad_id)
    if ad and ad.media_data:
        return send_from_directory('.', ad.media_data, mimetype=ad.media_mime_type or 'application/octet-stream')
    return '', 404

@app.route('/ad-media-inline/<int:ad_id>')
def get_ad_media_inline(ad_id):
    ad = Ad.query.get(ad_id)
    if ad and ad.media_data:
        from flask import Response
        return Response(ad.media_data, mimetype=ad.media_mime_type or 'application/octet-stream')
    return '', 404

@app.route('/admin/manage-announcements', methods=['GET', 'POST'])
@admin_required
def manage_announcements():
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'add':
            ann_type = request.form.get('announcement_type')
            media_data = None
            media_mime_type = None
            
            if ann_type in ['image', 'video']:
                if 'media_file' in request.files:
                    file = request.files['media_file']
                    if file and file.filename and allowed_file(file.filename):
                        media_data = file.read()
                        media_mime_type = file.content_type
            
            new_ann = Announcement(
                type=ann_type,
                content=request.form.get('content'),
                media_data=media_data,
                media_mime_type=media_mime_type
            )
            db.session.add(new_ann)
            flash('Announcement added! (Stored permanently in database)', 'success')
        
        elif action == 'delete':
            ann = Announcement.query.get(int(request.form.get('ann_id')))
            if ann:
                db.session.delete(ann)
                flash('Announcement deleted!', 'success')
        
        db.session.commit()
    
    announcements = Announcement.query.all()
    return render_template('manage_announcements.html', announcements=announcements)

@app.route('/announcement-media/<int:ann_id>')
def get_announcement_media(ann_id):
    ann = Announcement.query.get(ann_id)
    if ann and ann.media_data:
        from flask import Response
        return Response(ann.media_data, mimetype=ann.media_mime_type or 'application/octet-stream')
    return '', 404

@app.route('/admin/toggle-announcement/<int:ann_id>')
@admin_required
def toggle_announcement(ann_id):
    ann = Announcement.query.get(ann_id)
    if ann:
        ann.is_active = not ann.is_active
        db.session.commit()
        flash('Announcement toggled!', 'success')
    return redirect(url_for('manage_announcements'))

@app.route('/admin/manage-guide-videos', methods=['GET', 'POST'])
@admin_required
def manage_guide_videos():
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'add':
            new_video = GuideVideo(
                title=request.form.get('title'),
                video_url=request.form.get('video_url')
            )
            db.session.add(new_video)
            db.session.commit()
            flash('Guide video added!', 'success')
        
        elif action == 'delete':
            video = GuideVideo.query.get(int(request.form.get('video_id')))
            if video:
                db.session.delete(video)
                db.session.commit()
                flash('Guide video deleted!', 'success')
    
    videos = GuideVideo.query.all()
    return render_template('manage_guide_videos.html', videos=videos)

@app.route('/admin/settings', methods=['GET', 'POST'])
@admin_required
def admin_settings():
    if request.method == 'POST':
        set_setting('commission_percentage', request.form.get('commission_percentage'))
        set_setting('min_withdrawal', request.form.get('min_withdrawal'))
        set_setting('ads_enabled', 'true' if request.form.get('ads_enabled') else 'false')
        flash('Settings updated!', 'success')
        return redirect(url_for('admin_settings'))
    
    settings = {
        'commission_percentage': get_setting('commission_percentage', 50),
        'min_withdrawal': get_setting('min_withdrawal', 225),
        'ads_enabled': get_setting('ads_enabled', 'true').lower() == 'true'
    }
    
    return render_template('admin_settings.html', settings=settings)

@app.route('/admin/adjust-wallet/<int:user_id>', methods=['POST'])
@admin_required
def adjust_wallet(user_id):
    user = User.query.get(user_id)
    if user:
        try:
            amount = float(request.form.get('amount', 0))
            user.wallet_balance += amount
            db.session.commit()
            if amount >= 0:
                flash(f'Added {amount} PKR to {user.full_name}\'s wallet!', 'success')
            else:
                flash(f'Deducted {abs(amount)} PKR from {user.full_name}\'s wallet!', 'success')
        except ValueError:
            flash('Invalid amount!', 'error')
    return redirect(url_for('admin_dashboard'))

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        init_default_settings()
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        os.makedirs(app.config['ADS_FOLDER'], exist_ok=True)
    app.run(host='0.0.0.0', port=5000, debug=True)
