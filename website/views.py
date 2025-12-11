from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, session
from flask_login import login_required, current_user
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from . import db, limiter
from .models import Product, Category, CartItem, Order, OrderItem, ProductVariant, Waitlist, WishlistItem
from datetime import datetime
import uuid
import json

views = Blueprint('views', __name__)

# IP-based access tracking for landing page
landing_page_attempts = {}  # Store IP addresses and attempt counts
MAX_LANDING_ATTEMPTS = 5  # Maximum attempts per IP
LANDING_BLOCK_DURATION = 3600  # Block duration in seconds (1 hour)

def check_access():
    """Check if user has access to the site"""
    has_access = session.get('has_landing_access', False)
    if current_user.is_authenticated and current_user.is_admin:
        return True
    return has_access

@views.route('/')
def home():
    # Check if user has access (either logged in as admin or has entered access code)
    if not check_access():
        return redirect(url_for('views.landing'))
    
    featured_products = Product.query.filter_by(is_featured=True, is_active=True).limit(8).all()
    # Get only parent categories (main categories)
    main_categories = Category.query.filter_by(parent_id=None).all()
    return render_template('home.html', 
                         featured_products=featured_products, 
                         categories=main_categories,
                         user=current_user)

@views.route('/landing', methods=['GET', 'POST'])
def landing():
    from . import LANDING_ACCESS_CODE
    from datetime import datetime, timedelta
    
    # Get client IP address
    client_ip = get_remote_address()
    
    # Check IP-based restrictions
    if client_ip in landing_page_attempts:
        attempts_data = landing_page_attempts[client_ip]
        if attempts_data['blocked_until'] and datetime.now() < attempts_data['blocked_until']:
            remaining_time = (attempts_data['blocked_until'] - datetime.now()).seconds // 60
            flash(f'Too many failed attempts. Please try again in {remaining_time} minutes.', category='error')
            return render_template('landing.html', user=current_user, blocked=True)
        elif attempts_data['blocked_until'] and datetime.now() >= attempts_data['blocked_until']:
            # Unblock after duration
            landing_page_attempts[client_ip] = {'attempts': 0, 'blocked_until': None}
    
    if request.method == 'POST':
        access_code = request.form.get('access_code', '').strip().upper().replace(' ', '')
        correct_code = LANDING_ACCESS_CODE.upper().replace(' ', '')
        
        if access_code == correct_code:
            session['has_landing_access'] = True
            session.permanent = False  # Session expires when browser closes
            # Reset attempts on successful access
            if client_ip in landing_page_attempts:
                landing_page_attempts[client_ip] = {'attempts': 0, 'blocked_until': None}
            flash('Access granted! Welcome to STAT GLOBAL.', category='success')
            return redirect(url_for('views.home'))
        else:
            # Track failed attempts
            if client_ip not in landing_page_attempts:
                landing_page_attempts[client_ip] = {'attempts': 0, 'blocked_until': None}
            
            landing_page_attempts[client_ip]['attempts'] += 1
            
            if landing_page_attempts[client_ip]['attempts'] >= MAX_LANDING_ATTEMPTS:
                landing_page_attempts[client_ip]['blocked_until'] = datetime.now() + timedelta(seconds=LANDING_BLOCK_DURATION)
                flash(f'Too many failed attempts. Access blocked for 1 hour.', category='error')
            else:
                remaining = MAX_LANDING_ATTEMPTS - landing_page_attempts[client_ip]['attempts']
                flash(f'Invalid access code. {remaining} attempt(s) remaining.', category='error')
    
    return render_template('landing.html', user=current_user)

@views.route('/join-waitlist', methods=['POST'])
@limiter.limit("5 per minute")  # Rate limit: 5 requests per minute per IP
def join_waitlist():
    try:
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        preferred_size = request.form.get('preferred_size', '').strip()
        
        if not name or not email:
            return jsonify({'success': False, 'message': 'Name and email are required.'}), 400
        
        # Check if email already exists
        existing = Waitlist.query.filter_by(email=email).first()
        if existing:
            return jsonify({'success': False, 'message': 'You are already on the waitlist.'}), 400
        
        waitlist_entry = Waitlist(
            name=name,
            email=email,
            phone=phone if phone else None,
            preferred_size=preferred_size if preferred_size else None
        )
        
        db.session.add(waitlist_entry)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Successfully joined the waitlist!'})
    except Exception as e:
        return jsonify({'success': False, 'message': 'An error occurred. Please try again.'}), 500

@views.route('/logout-access')
def logout_access():
    session.pop('has_landing_access', None)
    session.permanent = False  # Ensure session expires when browser closes
    # Also log out user if they're logged in
    if current_user.is_authenticated:
        from flask_login import logout_user
        logout_user()
    return redirect(url_for('views.landing'))

@views.route('/products')
def products():
    if not check_access():
        return redirect(url_for('views.landing'))
    
    category_id = request.args.get('category', type=int)
    search = request.args.get('search', '')
    sort = request.args.get('sort', 'newest')  # newest, price_low, price_high, name
    
    query = Product.query.filter_by(is_active=True)
    
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    if search:
        query = query.filter(Product.name.contains(search) | Product.description.contains(search))
    
    # Sorting
    if sort == 'price_low':
        query = query.order_by(Product.price.asc())
    elif sort == 'price_high':
        query = query.order_by(Product.price.desc())
    elif sort == 'name':
        query = query.order_by(Product.name.asc())
    else:  # newest
        query = query.order_by(Product.date_created.desc())
    
    products = query.all()
    # Get parent categories with their children
    main_categories = Category.query.filter_by(parent_id=None).all()
    
    return render_template('products.html', 
                         products=products, 
                         categories=main_categories,
                         current_category=category_id,
                         search=search,
                         sort=sort,
                         user=current_user)

@views.route('/product/<slug>')
def product_detail(slug):
    if not check_access():
        return redirect(url_for('views.landing'))
    
    product = Product.query.filter_by(slug=slug, is_active=True).first_or_404()
    related_products = Product.query.filter_by(
        category_id=product.category_id, 
        is_active=True
    ).filter(Product.id != product.id).limit(4).all()
    
    # Parse product images JSON
    product_images = []
    if product.images:
        try:
            product_images = json.loads(product.images)
        except:
            product_images = []
    
    # Check if product is in user's wishlist
    in_wishlist = False
    if current_user.is_authenticated:
        wishlist_item = WishlistItem.query.filter_by(user_id=current_user.id, product_id=product.id).first()
        in_wishlist = wishlist_item is not None
    
    return render_template('product_detail.html', 
                         product=product, 
                         related_products=related_products,
                         product_images=product_images,
                         in_wishlist=in_wishlist,
                         user=current_user)

@views.route('/cart')
@login_required
def cart():
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    total = sum(item.product.price * item.quantity for item in cart_items)
    return render_template('cart.html', cart_items=cart_items, total=total, user=current_user)

@views.route('/add-to-cart', methods=['POST'])
@login_required
@limiter.limit("20 per minute")  # Rate limit: 20 add-to-cart requests per minute
def add_to_cart():
    product_id = request.form.get('product_id')
    quantity = int(request.form.get('quantity', 1))
    variant_id = request.form.get('variant_id', type=int)
    
    product = Product.query.get_or_404(product_id)
    
    # Check if item already in cart
    existing_item = CartItem.query.filter_by(
        user_id=current_user.id,
        product_id=product_id,
        variant_id=variant_id
    ).first()
    
    if existing_item:
        existing_item.quantity += quantity
    else:
        cart_item = CartItem(
            user_id=current_user.id,
            product_id=product_id,
            quantity=quantity,
            variant_id=variant_id
        )
        db.session.add(cart_item)
    
    db.session.commit()
    flash('Item added to cart!', category='success')
    return redirect(request.referrer or url_for('views.cart'))

@views.route('/update-cart', methods=['POST'])
@login_required
def update_cart():
    cart_item_id = request.form.get('cart_item_id')
    quantity = int(request.form.get('quantity', 1))
    
    cart_item = CartItem.query.get_or_404(cart_item_id)
    
    if cart_item.user_id != current_user.id:
        flash('Unauthorized action.', category='error')
        return redirect(url_for('views.cart'))
    
    if quantity <= 0:
        db.session.delete(cart_item)
    else:
        cart_item.quantity = quantity
    
    db.session.commit()
    return redirect(url_for('views.cart'))

@views.route('/remove-from-cart/<int:cart_item_id>')
@login_required
def remove_from_cart(cart_item_id):
    cart_item = CartItem.query.get_or_404(cart_item_id)
    
    if cart_item.user_id != current_user.id:
        flash('Unauthorized action.', category='error')
        return redirect(url_for('views.cart'))
    
    db.session.delete(cart_item)
    db.session.commit()
    flash('Item removed from cart.', category='success')
    return redirect(url_for('views.cart'))

@views.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    
    if not cart_items:
        flash('Your cart is empty.', category='error')
        return redirect(url_for('views.cart'))
    
    if request.method == 'POST':
        shipping_address = request.form.get('shipping_address')
        billing_address = request.form.get('billing_address')
        payment_method = request.form.get('payment_method')
        
        total_amount = sum(item.product.price * item.quantity for item in cart_items)
        
        # Create order
        order_number = f"STAT-{uuid.uuid4().hex[:8].upper()}"
        order = Order(
            order_number=order_number,
            user_id=current_user.id,
            total_amount=total_amount,
            shipping_address=shipping_address,
            billing_address=billing_address,
            payment_method=payment_method,
            status='pending',
            payment_status='pending'
        )
        db.session.add(order)
        db.session.flush()
        
        # Create order items
        for cart_item in cart_items:
            order_item = OrderItem(
                order_id=order.id,
                product_id=cart_item.product_id,
                quantity=cart_item.quantity,
                price=cart_item.product.price,
                variant_id=cart_item.variant_id
            )
            db.session.add(order_item)
        
        # Clear cart
        for cart_item in cart_items:
            db.session.delete(cart_item)
        
        db.session.commit()
        flash(f'Order placed successfully! Order #: {order_number}', category='success')
        return redirect(url_for('views.order_confirmation', order_id=order.id))
    
    total = sum(item.product.price * item.quantity for item in cart_items)
    return render_template('checkout.html', cart_items=cart_items, total=total, user=current_user)

@views.route('/order/<int:order_id>')
@login_required
def order_confirmation(order_id):
    order = Order.query.get_or_404(order_id)
    
    if order.user_id != current_user.id:
        flash('Unauthorized access.', category='error')
        return redirect(url_for('views.home'))
    
    return render_template('order_confirmation.html', order=order, user=current_user)

@views.route('/orders')
@login_required
def orders():
    user_orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.date_created.desc()).all()
    return render_template('orders.html', orders=user_orders, user=current_user)

@views.route('/wishlist')
@login_required
def wishlist():
    if not check_access():
        flash('You need access to view the wishlist.', category='error')
        return redirect(url_for('views.landing'))
    
    wishlist_items = WishlistItem.query.filter_by(user_id=current_user.id).order_by(WishlistItem.date_added.desc()).all()
    return render_template('wishlist.html', wishlist_items=wishlist_items, user=current_user)

@views.route('/add-to-wishlist', methods=['POST'])
@login_required
@limiter.limit("10 per minute")  # Rate limit: 10 wishlist additions per minute
def add_to_wishlist():
    if not check_access():
        flash('You need access to add items to wishlist.', category='error')
        return redirect(url_for('views.landing'))
    
    product_id = request.form.get('product_id')
    product = Product.query.get_or_404(product_id)
    
    # Check if already in wishlist
    existing = WishlistItem.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    if existing:
        flash('Product is already in your wishlist!', category='info')
        return redirect(request.referrer or url_for('views.wishlist'))
    
    wishlist_item = WishlistItem(
        user_id=current_user.id,
        product_id=product_id
    )
    db.session.add(wishlist_item)
    db.session.commit()
    flash('Added to wishlist!', category='success')
    return redirect(request.referrer or url_for('views.wishlist'))

@views.route('/remove-from-wishlist/<int:wishlist_item_id>')
@login_required
def remove_from_wishlist(wishlist_item_id):
    wishlist_item = WishlistItem.query.get_or_404(wishlist_item_id)
    
    if wishlist_item.user_id != current_user.id:
        flash('Unauthorized action.', category='error')
        return redirect(url_for('views.wishlist'))
    
    db.session.delete(wishlist_item)
    db.session.commit()
    flash('Removed from wishlist.', category='success')
    return redirect(url_for('views.wishlist'))

