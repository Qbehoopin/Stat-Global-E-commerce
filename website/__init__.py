from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from werkzeug.security import generate_password_hash

db = SQLAlchemy()
DB_NAME = "stat_global.db"

# Default admin credentials
ADMIN_EMAIL = "STATGLOBALADMIN@SG.com"
ADMIN_PASSWORD = "Password123"
ADMIN_FIRST_NAME = "STAT"
ADMIN_LAST_NAME = "GLOBAL"

# Landing page access code (change this to your desired password)
LANDING_ACCESS_CODE = "STAT2024"

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'stat-global-secret-key-2024'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = 'website/static/images/products'
    
    db.init_app(app)
    
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    login_manager.init_app(app)
    
    from .models import User
    
    @login_manager.user_loader
    def load_user(id):
        if id is None:
            return None
        try:
            return User.query.get(int(id))
        except (ValueError, TypeError):
            return None
    
    # Register blueprints
    from .views import views
    from .auth import auth
    from .admin import admin
    
    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')
    app.register_blueprint(admin, url_prefix='/admin')
    
    # Create database tables and default admin account
    with app.app_context():
        db.create_all()
        
        # Create default admin account if it doesn't exist
        admin_user = User.query.filter_by(email=ADMIN_EMAIL).first()
        if not admin_user:
            admin_user = User(
                email=ADMIN_EMAIL,
                first_name=ADMIN_FIRST_NAME,
                last_name=ADMIN_LAST_NAME,
                password=generate_password_hash(ADMIN_PASSWORD, method='pbkdf2:sha256'),
                is_admin=True
            )
            db.session.add(admin_user)
            db.session.commit()
            print(f"✓ Default admin account created: {ADMIN_EMAIL}")
    
    return app

