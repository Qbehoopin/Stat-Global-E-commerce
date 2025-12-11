from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.security import generate_password_hash

db = SQLAlchemy()
limiter = Limiter(key_func=get_remote_address)
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
    app.config['SESSION_PERMANENT'] = False  # Sessions expire when browser closes
    
    db.init_app(app)
    limiter.init_app(app)
    
    login_manager = LoginManager()
    login_manager.login_view = 'views.landing'  # Redirect to landing page if not authenticated
    login_manager.login_message = 'Please enter the access code to access this page.'
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
    
    # Context processor to make categories available globally
    @app.context_processor
    def inject_categories():
        try:
            main_categories = Category.query.filter_by(parent_id=None).order_by(Category.name).all()
            return dict(nav_categories=main_categories)
        except:
            return dict(nav_categories=[])
    
    # Create database tables and default admin account
    with app.app_context():
        from .models import Category
        
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
        
        # Create default categories structure
        try:
            # Main categories with subcategories (clothing items)
            categories_with_subcats = {
                'Mensware': ['Shirts', 'Hoodies', 'Hats'],
                'Womensware': ['Shirts', 'Hoodies', 'Hats'],
                'Global Babies/Kids': ['Shirts', 'Hoodies', 'Hats']
            }
            
            # Create categories with subcategories
            for parent_name, subcategories in categories_with_subcats.items():
                parent_category = Category.query.filter_by(name=parent_name).first()
                if not parent_category:
                    parent_slug = parent_name.lower().replace(' ', '-').replace('/', '-')
                    parent_category = Category(
                        name=parent_name,
                        slug=parent_slug,
                        description=f"{parent_name} collection"
                    )
                    db.session.add(parent_category)
                    db.session.flush()  # Get the ID
                
                # Create subcategories
                for subcat_name in subcategories:
                    subcat_slug = f"{parent_category.slug}-{subcat_name.lower().replace(' ', '-')}"
                    existing_subcat = Category.query.filter_by(slug=subcat_slug).first()
                    if not existing_subcat:
                        subcategory = Category(
                            name=subcat_name,  # Just the subcategory name, not prefixed
                            slug=subcat_slug,
                            description=f"{subcat_name} in {parent_name}",
                            parent_id=parent_category.id
                        )
                        db.session.add(subcategory)
            
            # Create Exclusive Art category (no subcategories)
            exclusive_art = Category.query.filter_by(name='Exclusive Art').first()
            if not exclusive_art:
                exclusive_art = Category(
                    name='Exclusive Art',
                    slug='exclusive-art',
                    description='Exclusive artwork collection'
                )
                db.session.add(exclusive_art)
            
            db.session.commit()
            print("OK: Default categories structure created")
        except Exception as e:
            print(f"Warning: Could not create default categories. Error: {e}")
            db.session.rollback()
    
    return app

