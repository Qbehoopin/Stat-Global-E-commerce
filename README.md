# STAT GLOBAL - E-Commerce Platform

A modern, full-featured e-commerce platform built with Flask, inspired by Shopify functionality with an earth-tone design aesthetic similar to Zara and H&M.

## Features

### Customer Features
- **Product Catalog**: Browse products by category with search and sorting
- **Product Details**: Detailed product pages with images and descriptions
- **Shopping Cart**: Add, update, and remove items from cart
- **User Authentication**: Secure login and registration system
- **Checkout Process**: Complete order placement with shipping information
- **Order Management**: View order history and order details
- **Responsive Design**: Mobile-friendly interface with earth-tone styling

### Admin Features (Shopify-like)
- **Dashboard**: Overview of products, orders, and users
- **Product Management**: Add, edit, delete products with categories
- **Category Management**: Organize products by categories
- **Order Management**: View and update order statuses
- **Inventory Tracking**: Monitor product inventory levels

## Step-by-Step Setup Guide

### Step 1: Create Virtual Environment

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Mac/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- Flask 3.0.0
- Flask-SQLAlchemy 3.1.1
- Flask-Login 0.6.3
- Werkzeug 3.0.1

### Step 3: Run the Application

```bash
python main.py
```

The application will start on `http://127.0.0.1:5000` (or `http://localhost:5000`)

### Step 4: Create Your First Admin User

1. First, register a regular account through the website at `/sign-up`
2. Then, run this Python script to make yourself an admin:

```python
from website import create_app, db
from website.models import User

app = create_app()
with app.app_context():
    # Replace 'your-email@example.com' with your registered email
    user = User.query.filter_by(email='your-email@example.com').first()
    if user:
        user.is_admin = True
        db.session.commit()
        print(f"User {user.email} is now an admin!")
    else:
        print("User not found. Make sure you've registered first.")
```

Or use the interactive script:

```bash
python create_admin.py
```

### Step 5: Access Admin Panel

1. Log in with your admin account
2. Navigate to `/admin` to access the admin dashboard
3. Start adding products and categories!

## Project Structure

```
Stat-Global-E-commerce/
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
├── website/
│   ├── __init__.py        # Flask app factory
│   ├── models.py          # Database models
│   ├── views.py           # Customer-facing routes
│   ├── auth.py            # Authentication routes
│   ├── admin.py           # Admin panel routes
│   ├── templates/         # Jinja2 templates
│   │   ├── base.html
│   │   ├── home.html
│   │   ├── products.html
│   │   ├── product_detail.html
│   │   ├── cart.html
│   │   ├── checkout.html
│   │   ├── orders.html
│   │   ├── auth/
│   │   │   ├── login.html
│   │   │   └── signup.html
│   │   └── admin/
│   │       ├── dashboard.html
│   │       ├── products.html
│   │       ├── categories.html
│   │       └── orders.html
│   └── static/
│       └── css/
│           └── styles.css  # Earth-tone styling
└── stat_global.db         # SQLite database (created automatically)
```

## Database Models

- **User**: Customer and admin accounts
- **Product**: Product catalog with variants support
- **Category**: Product categories
- **CartItem**: Shopping cart items
- **Order**: Customer orders
- **OrderItem**: Individual items in orders
- **ProductVariant**: Product variants (size, color, etc.)

## Design Philosophy

The design uses an **earth-tone color palette**:
- Cream and beige backgrounds
- Taupe and brown accents
- Minimal, clean layouts
- Modern typography
- Inspired by Zara and H&M's aesthetic

## Key Routes

### Customer Routes
- `/` - Homepage
- `/products` - Product catalog
- `/product/<slug>` - Product detail page
- `/cart` - Shopping cart
- `/checkout` - Checkout process
- `/orders` - Order history
- `/login` - User login
- `/sign-up` - User registration

### Admin Routes
- `/admin` - Admin dashboard
- `/admin/products` - Manage products
- `/admin/products/add` - Add new product
- `/admin/products/edit/<id>` - Edit product
- `/admin/categories` - Manage categories
- `/admin/orders` - View all orders
- `/admin/orders/<id>` - Order details

## Next Steps for Development

1. **Payment Integration**: Add Stripe or PayPal integration
2. **Image Upload**: Implement file upload for product images
3. **Email Notifications**: Send order confirmations via email
4. **Product Reviews**: Add customer review system
5. **Wishlist**: Allow users to save favorite products
6. **Search Enhancement**: Add advanced search filters
7. **Shipping Calculator**: Integrate shipping API
8. **Inventory Alerts**: Notify when products are low in stock
9. **Analytics**: Add sales and visitor analytics
10. **Multi-currency**: Support multiple currencies

## Security Notes

- Change the `SECRET_KEY` in `website/__init__.py` for production
- Use environment variables for sensitive configuration
- Implement HTTPS in production
- Add rate limiting for API endpoints
- Use a production-grade database (PostgreSQL) instead of SQLite

## Troubleshooting

**Database not created?**
- Make sure you've run the app at least once
- Check that you have write permissions in the project directory

**Can't access admin panel?**
- Make sure your user account has `is_admin = True` in the database
- Log out and log back in after making yourself admin

**Images not showing?**
- Use full URLs for product images (e.g., `https://example.com/image.jpg`)
- Or implement file upload functionality for local storage

## License

This project is for educational and commercial use.

---

**STAT GLOBAL** - Premium Clothing for the Modern Lifestyle
