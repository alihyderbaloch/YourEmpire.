import os
import sys

# Must import before calling functions
from app import app, db, init_default_settings

print("=" * 50)
print("INITIALIZING DATABASE...")
print("=" * 50)

try:
    with app.app_context():
        print("Creating tables...")
        db.create_all()
        print("✓ All tables created")
        
        print("Initializing settings...")
        init_default_settings()
        print("✓ Settings initialized")
        
        print("Creating folders...")
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        os.makedirs(app.config['ADS_FOLDER'], exist_ok=True)
        print("✓ Folders ready")
        
        print("=" * 50)
        print("DATABASE INITIALIZATION COMPLETE ✓")
        print("=" * 50)
        
except Exception as e:
    print("\n" + "=" * 50, file=sys.stderr)
    print("FATAL ERROR DURING INITIALIZATION", file=sys.stderr)
    print(f"Error: {str(e)}", file=sys.stderr)
    print("=" * 50, file=sys.stderr)
    import traceback
    traceback.print_exc()
    sys.exit(1)

# The app object for Gunicorn