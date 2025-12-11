from . import db
from flask_login import UserMixin
from datetime import datetime
from sqlalchemy.orm import relationship

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    first_name = db.Column(db.String(150), nullable=False)
    last_name = db.Column(db.String(150), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    cart_items = relationship('CartItem', back_populates='user', cascade='all, delete-orphan')
    orders = relationship('Order', back_populates='user', cascade='all, delete-orphan')
    wishlist_items = relationship('WishlistItem', back_populates='user', cascade='all, delete-orphan')

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    image_url = db.Column(db.String(500))
    parent_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)  # For hierarchical categories
    
    # Relationships
    products = relationship('Product', back_populates='category', cascade='all, delete-orphan')
    parent = relationship('Category', remote_side=[id], backref='children')

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    compare_at_price = db.Column(db.Float)  # Original price for sale items
    sku = db.Column(db.String(100), unique=True)
    inventory = db.Column(db.Integer, default=0)
    image_url = db.Column(db.String(500))  # Main/primary image
    images = db.Column(db.Text)  # JSON string of multiple images (on body, on ground, photoshoot)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    is_featured = db.Column(db.Boolean, default=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    date_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Additional product details
    shipping_details = db.Column(db.Text)  # Shipping information
    size_chart = db.Column(db.Text)  # Size chart information (can be JSON or text)
    colorway = db.Column(db.String(200))  # Color options/variations
    model_details = db.Column(db.Text)  # Model information (fit, measurements, etc.)
    fabric_type = db.Column(db.String(200))  # Fabric/material information
    product_details = db.Column(db.Text)  # Additional product details
    
    # Relationships
    category = relationship('Category', back_populates='products')
    cart_items = relationship('CartItem', back_populates='product', cascade='all, delete-orphan')
    order_items = relationship('OrderItem', back_populates='product', cascade='all, delete-orphan')
    wishlist_items = relationship('WishlistItem', back_populates='product', cascade='all, delete-orphan')
    
    # Variants (size, color, etc.)
    variants = relationship('ProductVariant', back_populates='product', cascade='all, delete-orphan')

class ProductVariant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)  # e.g., "Size", "Color"
    value = db.Column(db.String(100), nullable=False)  # e.g., "M", "Red"
    price_adjustment = db.Column(db.Float, default=0.0)
    inventory = db.Column(db.Integer, default=0)
    sku = db.Column(db.String(100))
    
    product = relationship('Product', back_populates='variants')

class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1, nullable=False)
    variant_id = db.Column(db.Integer, db.ForeignKey('product_variant.id'))
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = relationship('User', back_populates='cart_items')
    product = relationship('Product', back_populates='cart_items')
    variant = relationship('ProductVariant')

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(50), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default='pending')  # pending, processing, shipped, delivered, cancelled
    shipping_address = db.Column(db.Text, nullable=False)
    billing_address = db.Column(db.Text, nullable=False)
    payment_method = db.Column(db.String(50))
    payment_status = db.Column(db.String(50), default='pending')  # pending, paid, failed, refunded
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    date_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship('User', back_populates='orders')
    items = relationship('OrderItem', back_populates='order', cascade='all, delete-orphan')

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)  # Price at time of purchase
    variant_id = db.Column(db.Integer, db.ForeignKey('product_variant.id'))
    
    order = relationship('Order', back_populates='items')
    product = relationship('Product', back_populates='order_items')
    variant = relationship('ProductVariant')

class WishlistItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = relationship('User', back_populates='wishlist_items')
    product = relationship('Product', back_populates='wishlist_items')
    
    # Ensure a user can't add the same product to wishlist twice
    __table_args__ = (db.UniqueConstraint('user_id', 'product_id', name='unique_user_product_wishlist'),)

class Waitlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), nullable=False)
    phone = db.Column(db.String(20))
    preferred_size = db.Column(db.String(20))
    date_joined = db.Column(db.DateTime, default=datetime.utcnow)
    access_granted = db.Column(db.Boolean, default=False)

