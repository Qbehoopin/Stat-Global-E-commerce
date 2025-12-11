"""
Database migration script to add new columns to existing tables.
Run this script once to update your database schema.
"""

import sqlite3
import os

def migrate_database():
    # Find the database file
    db_path = os.path.join('instance', 'stat_global.db')
    if not os.path.exists(db_path):
        db_path = 'stat_global.db'
    
    if not os.path.exists(db_path):
        print(f"Error: Database file not found at {db_path}")
        return
    
    print("=" * 60)
    print("STAT GLOBAL - Database Migration")
    print("=" * 60)
    print()
    print(f"Migrating database: {db_path}")
    print()
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if parent_id column exists in category table
        cursor.execute("PRAGMA table_info(category)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'parent_id' not in columns:
            print("Adding parent_id column to category table...")
            cursor.execute("ALTER TABLE category ADD COLUMN parent_id INTEGER")
            conn.commit()
            print("OK: Added parent_id column to category table")
        else:
            print("OK: parent_id column already exists in category table")
        
        # Check if new product columns exist
        cursor.execute("PRAGMA table_info(product)")
        columns = [row[1] for row in cursor.fetchall()]
        
        new_columns = {
            'shipping_details': 'TEXT',
            'size_chart': 'TEXT',
            'colorway': 'VARCHAR(200)',
            'model_details': 'TEXT',
            'fabric_type': 'VARCHAR(200)',
            'product_details': 'TEXT'
        }
        
        for col_name, col_type in new_columns.items():
            if col_name not in columns:
                print(f"Adding {col_name} column to product table...")
                cursor.execute(f"ALTER TABLE product ADD COLUMN {col_name} {col_type}")
                conn.commit()
                print(f"OK: Added {col_name} column to product table")
            else:
                print(f"OK: {col_name} column already exists in product table")
        
        # Check if wishlist_item table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='wishlist_item'")
        if not cursor.fetchone():
            print("Creating wishlist_item table...")
            # Create the table using SQL
            cursor.execute("""
                CREATE TABLE wishlist_item (
                    id INTEGER NOT NULL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    date_added DATETIME,
                    FOREIGN KEY(user_id) REFERENCES user (id),
                    FOREIGN KEY(product_id) REFERENCES product (id),
                    UNIQUE (user_id, product_id)
                )
            """)
            conn.commit()
            print("OK: Created wishlist_item table")
        else:
            print("OK: wishlist_item table already exists")
        
        print()
        print("=" * 60)
        print("Migration completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"Error during migration: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    migrate_database()

