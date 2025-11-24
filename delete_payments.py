#!/usr/bin/env python3
"""
Simple script to delete all payment methods from database
Run this in terminal: python delete_payments.py
"""

from app import app, db
from models import PaymentMethod

with app.app_context():
    # Delete all payment methods
    deleted_count = PaymentMethod.query.delete()
    db.session.commit()
    
    print(f"✅ Deleted {deleted_count} payment methods from database!")
    print("All payment methods have been removed. Admin can add new ones.")
