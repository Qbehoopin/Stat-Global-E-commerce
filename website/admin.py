from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from . import db
from .models import Product, Category, Order, User, ProductVariant
from werkzeug.utils import secure_filename
import os
import json

admin = Blueprint('admin', __name__)

def admin_required(f):
    from functools import wraps
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            flash('Admin access required.', category='error')
            return redirect(url_for('views.home'))
        return f(*args, **kwargs)
    return decorated_function

@admin.route('/')
@admin_required
def dashboard():
    total_products = Product.query.count()
    total_orders = Order.query.count()
    total_users = User.query.count()
    pending_orders = Order.query.filter_by(status='pending').count()
    
    recent_orders = Order.query.order_by(Order.date_created.desc()).limit(10).all()
    
    return render_template('admin/dashboard.html',
                         total_products=total_products,
                         total_orders=total_orders,
                         total_users=total_users,
                         pending_orders=pending_orders,
                         recent_orders=recent_orders,
                         user=current_user)

@admin.route('/products')
@admin_required
def products():
    products = Product.query.order_by(Product.date_created.desc()).all()
    categories = Category.query.all()
    return render_template('admin/products.html', products=products, categories=categories, user=current_user)

@admin.route('/products/add', methods=['GET', 'POST'])
@admin_required
def add_product():
    if request.method == 'POST':
        name = request.form.get('name')
        slug = request.form.get('slug') or name.lower().replace(' ', '-')
        description = request.form.get('description')
        price = float(request.form.get('price'))
        compare_at_price = request.form.get('compare_at_price')
        sku = request.form.get('sku')
        inventory = int(request.form.get('inventory', 0))
        category_id = int(request.form.get('category_id'))
        image_url = request.form.get('image_url')
        is_featured = request.form.get('is_featured') == 'on'
        
        # New product detail fields
        shipping_details = request.form.get('shipping_details')
        size_chart = request.form.get('size_chart')
        colorway = request.form.get('colorway')
        model_details = request.form.get('model_details')
        fabric_type = request.form.get('fabric_type')
        product_details = request.form.get('product_details')
        
        # Handle multiple images (on body, on ground, photoshoot)
        images_list = []
        on_body_image = request.form.get('on_body_image', '').strip()
        on_ground_image = request.form.get('on_ground_image', '').strip()
        photoshoot_image = request.form.get('photoshoot_image', '').strip()
        additional_image = request.form.get('additional_image', '').strip()
        
        if on_body_image:
            images_list.append({'type': 'on_body', 'url': on_body_image})
        if on_ground_image:
            images_list.append({'type': 'on_ground', 'url': on_ground_image})
        if photoshoot_image:
            images_list.append({'type': 'photoshoot', 'url': photoshoot_image})
        if additional_image:
            images_list.append({'type': 'additional', 'url': additional_image})
        
        images_json = json.dumps(images_list) if images_list else None
        
        product = Product(
            name=name,
            slug=slug,
            description=description,
            price=price,
            compare_at_price=float(compare_at_price) if compare_at_price else None,
            sku=sku,
            inventory=inventory,
            category_id=category_id,
            image_url=image_url,
            images=images_json,
            is_featured=is_featured,
            shipping_details=shipping_details if shipping_details else None,
            size_chart=size_chart if size_chart else None,
            colorway=colorway if colorway else None,
            model_details=model_details if model_details else None,
            fabric_type=fabric_type if fabric_type else None,
            product_details=product_details if product_details else None
        )
        
        db.session.add(product)
        db.session.commit()
        flash('Product added successfully!', category='success')
        return redirect(url_for('admin.products'))
    
    categories = Category.query.all()
    return render_template('admin/add_product.html', categories=categories, user=current_user)

@admin.route('/products/edit/<int:product_id>', methods=['GET', 'POST'])
@admin_required
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    
    if request.method == 'POST':
        product.name = request.form.get('name')
        product.slug = request.form.get('slug')
        product.description = request.form.get('description')
        product.price = float(request.form.get('price'))
        compare_at_price = request.form.get('compare_at_price')
        product.compare_at_price = float(compare_at_price) if compare_at_price else None
        product.sku = request.form.get('sku')
        product.inventory = int(request.form.get('inventory', 0))
        product.category_id = int(request.form.get('category_id'))
        product.image_url = request.form.get('image_url')
        product.is_featured = request.form.get('is_featured') == 'on'
        product.is_active = request.form.get('is_active') == 'on'
        
        # Update new product detail fields
        product.shipping_details = request.form.get('shipping_details') or None
        product.size_chart = request.form.get('size_chart') or None
        product.colorway = request.form.get('colorway') or None
        product.model_details = request.form.get('model_details') or None
        product.fabric_type = request.form.get('fabric_type') or None
        product.product_details = request.form.get('product_details') or None
        
        # Handle multiple images
        images_list = []
        on_body_image = request.form.get('on_body_image', '').strip()
        on_ground_image = request.form.get('on_ground_image', '').strip()
        photoshoot_image = request.form.get('photoshoot_image', '').strip()
        additional_image = request.form.get('additional_image', '').strip()
        
        if on_body_image:
            images_list.append({'type': 'on_body', 'url': on_body_image})
        if on_ground_image:
            images_list.append({'type': 'on_ground', 'url': on_ground_image})
        if photoshoot_image:
            images_list.append({'type': 'photoshoot', 'url': photoshoot_image})
        if additional_image:
            images_list.append({'type': 'additional', 'url': additional_image})
        
        product.images = json.dumps(images_list) if images_list else None
        
        db.session.commit()
        flash('Product updated successfully!', category='success')
        return redirect(url_for('admin.products'))
    
    # Parse existing images for editing
    product_images = []
    if product.images:
        try:
            product_images = json.loads(product.images)
        except:
            product_images = []
    
    categories = Category.query.all()
    return render_template('admin/edit_product.html', product=product, categories=categories, product_images=product_images, user=current_user)

@admin.route('/products/delete/<int:product_id>')
@admin_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash('Product deleted successfully!', category='success')
    return redirect(url_for('admin.products'))

@admin.route('/categories')
@admin_required
def categories():
    all_categories = Category.query.all()
    # Separate parent and child categories
    parent_categories = [c for c in all_categories if c.parent_id is None]
    child_categories = [c for c in all_categories if c.parent_id is not None]
    return render_template('admin/categories.html', 
                         categories=all_categories,
                         parent_categories=parent_categories,
                         child_categories=child_categories,
                         user=current_user)

@admin.route('/categories/add', methods=['POST'])
@admin_required
def add_category():
    name = request.form.get('name')
    slug = request.form.get('slug') or name.lower().replace(' ', '-').replace('/', '-')
    description = request.form.get('description')
    image_url = request.form.get('image_url')
    parent_id = request.form.get('parent_id', type=int)
    
    category = Category(name=name, slug=slug, description=description, image_url=image_url, parent_id=parent_id if parent_id else None)
    db.session.add(category)
    db.session.commit()
    flash('Category added successfully!', category='success')
    return redirect(url_for('admin.categories'))

@admin.route('/categories/delete/<int:category_id>')
@admin_required
def delete_category(category_id):
    category = Category.query.get_or_404(category_id)
    db.session.delete(category)
    db.session.commit()
    flash('Category deleted successfully!', category='success')
    return redirect(url_for('admin.categories'))

@admin.route('/orders')
@admin_required
def orders():
    orders = Order.query.order_by(Order.date_created.desc()).all()
    return render_template('admin/orders.html', orders=orders, user=current_user)

@admin.route('/orders/<int:order_id>')
@admin_required
def order_detail(order_id):
    order = Order.query.get_or_404(order_id)
    return render_template('admin/order_detail.html', order=order, user=current_user)

@admin.route('/orders/<int:order_id>/update-status', methods=['POST'])
@admin_required
def update_order_status(order_id):
    order = Order.query.get_or_404(order_id)
    order.status = request.form.get('status')
    order.payment_status = request.form.get('payment_status')
    db.session.commit()
    flash('Order status updated!', category='success')
    return redirect(url_for('admin.order_detail', order_id=order_id))

