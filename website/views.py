from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from . import db
from .models import Product, Category, CartItem, Order, OrderItem, ProductVariant
from datetime import datetime
import uuid

views = Blueprint('views', __name__)

@views.route('/')
def home():
    featured_products = Product.query.filter_by(is_featured=True, is_active=True).limit(8).all()
    categories = Category.query.all()
    return render_template('home.html', 
                         featured_products=featured_products, 
                         categories=categories,
                         user=current_user)

@views.route('/products')
def products():
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
    categories = Category.query.all()
    
    return render_template('products.html', 
                         products=products, 
                         categories=categories,
                         current_category=category_id,
                         search=search,
                         sort=sort,
                         user=current_user)

@views.route('/product/<slug>')
def product_detail(slug):
    product = Product.query.filter_by(slug=slug, is_active=True).first_or_404()
    related_products = Product.query.filter_by(
        category_id=product.category_id, 
        is_active=True
    ).filter(Product.id != product.id).limit(4).all()
    
    return render_template('product_detail.html', 
                         product=product, 
                         related_products=related_products,
                         user=current_user)

@views.route('/cart')
@login_required
def cart():
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    total = sum(item.product.price * item.quantity for item in cart_items)
    return render_template('cart.html', cart_items=cart_items, total=total, user=current_user)

@views.route('/add-to-cart', methods=['POST'])
@login_required
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

