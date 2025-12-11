"""
Script to update categories structure to the new simplified format:
- Mensware (with Shirts, Hoodies, Hats subcategories)
- Womensware (with Shirts, Hoodies, Hats subcategories)
- Global Babies/Kids (with Shirts, Hoodies, Hats subcategories)
- Exclusive Art (no subcategories)
"""

from website import create_app, db
from website.models import Category

def update_categories():
    app = create_app()
    
    with app.app_context():
        print("=" * 60)
        print("STAT GLOBAL - Category Structure Update")
        print("=" * 60)
        print()
        
        # Delete old subcategories that don't match the new structure
        print("Cleaning up old category structure...")
        
        # Get all categories
        all_categories = Category.query.all()
        
        # Define the new structure
        new_structure = {
            'Mensware': ['Shirts', 'Hoodies', 'Hats'],
            'Womensware': ['Shirts', 'Hoodies', 'Hats'],
            'Global Babies/Kids': ['Shirts', 'Hoodies', 'Hats']
        }
        
        # Find and update/create main categories
        for parent_name, subcat_names in new_structure.items():
            parent = Category.query.filter_by(name=parent_name, parent_id=None).first()
            
            if not parent:
                parent_slug = parent_name.lower().replace(' ', '-').replace('/', '-')
                parent = Category(
                    name=parent_name,
                    slug=parent_slug,
                    description=f"{parent_name} collection"
                )
                db.session.add(parent)
                db.session.flush()
                print(f"Created main category: {parent_name}")
            else:
                print(f"Found existing category: {parent_name}")
            
            # Delete old subcategories that aren't in the new list
            existing_subcats = Category.query.filter_by(parent_id=parent.id).all()
            for old_subcat in existing_subcats:
                if old_subcat.name not in subcat_names:
                    print(f"  Deleting old subcategory: {old_subcat.name}")
                    db.session.delete(old_subcat)
            
            # Create/update subcategories
            for subcat_name in subcat_names:
                subcat_slug = f"{parent.slug}-{subcat_name.lower().replace(' ', '-')}"
                # Use no_autoflush to prevent premature flush that causes unique constraint errors
                with db.session.no_autoflush:
                    subcat = Category.query.filter_by(slug=subcat_slug, parent_id=parent.id).first()
                    
                    if not subcat:
                        subcat = Category(
                            name=subcat_name,
                            slug=subcat_slug,
                            description=f"{subcat_name} in {parent_name}",
                            parent_id=parent.id
                        )
                        db.session.add(subcat)
                        print(f"  Created subcategory: {subcat_name}")
                    else:
                        print(f"  Found existing subcategory: {subcat_name}")
        
        # Create/update Exclusive Art category
        exclusive_art = Category.query.filter_by(name='Exclusive Art', parent_id=None).first()
        if not exclusive_art:
            exclusive_art = Category(
                name='Exclusive Art',
                slug='exclusive-art',
                description='Exclusive artwork collection'
            )
            db.session.add(exclusive_art)
            print("Created category: Exclusive Art")
        else:
            print("Found existing category: Exclusive Art")
        
        # Delete any other main categories that aren't in our new structure
        all_main_categories = Category.query.filter_by(parent_id=None).all()
        valid_main_names = ['Mensware', 'Womensware', 'Global Babies/Kids', 'Exclusive Art']
        
        for main_cat in all_main_categories:
            if main_cat.name not in valid_main_names:
                print(f"Deleting old main category: {main_cat.name}")
                # Delete all its subcategories first
                subcats = Category.query.filter_by(parent_id=main_cat.id).all()
                for subcat in subcats:
                    db.session.delete(subcat)
                db.session.delete(main_cat)
        
        db.session.commit()
        print()
        print("=" * 60)
        print("Category structure updated successfully!")
        print("=" * 60)
        print()
        print("New category structure:")
        main_cats = Category.query.filter_by(parent_id=None).order_by(Category.name).all()
        for main_cat in main_cats:
            print(f"  - {main_cat.name}")
            if main_cat.name != 'Exclusive Art':
                subcats = Category.query.filter_by(parent_id=main_cat.id).order_by(Category.name).all()
                for subcat in subcats:
                    print(f"    + {subcat.name}")

if __name__ == '__main__':
    update_categories()

