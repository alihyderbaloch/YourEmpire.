import os
from app import app, db, init_default_settings

if __name__ == '__main__':
    with app.app_context():
        try:
            db.create_all()
            init_default_settings()
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            os.makedirs(app.config['ADS_FOLDER'], exist_ok=True)
        except Exception as e:
            print(f"Database init warning: {e}")
    
    app.run()