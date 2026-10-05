import os
import urllib.parse
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.sql import func

# ---------------------------------------------------------
# SECURE DATABASE SETUP
# ---------------------------------------------------------

def get_secure_password():
    """Reads the password from the .password file securely."""
    try:
        # Open the file in 'read' mode
        with open('.password', 'r') as file:
            # .strip() is crucial! It removes invisible newline characters (\n)
            # that might have been saved at the end of the file.
            raw_password = file.read().strip()
            
            # If the file is empty, raise an error
            if not raw_password:
                raise ValueError("The .password file is empty!")
                
            return raw_password
            
    except FileNotFoundError:
        print("❌ CRITICAL ERROR: '.password' file not found.")
        print("Please create a file named '.password' and paste your database password inside.")
        exit(1) # Stop the script entirely if the password is missing

# 1. Fetch the raw password
my_secret_password = get_secure_password()

# 2. URL-encode it to protect against special characters breaking the URI
encoded_password = urllib.parse.quote_plus(my_secret_password)

# 3. Dynamically construct the final Connection String using an f-string
DATABASE_URI = f'postgresql://postgres.yahofshjgjxfhogfpxtt:{encoded_password}@aws-1-sa-east-1.pooler.supabase.com:6543/postgres'

# Create the Engine: This manages the actual connections to the database
engine = create_engine(DATABASE_URI)

# Create a Session Factory: Sessions are the "workspaces" for our database transactions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a Base class that our Python models will inherit from
Base = declarative_base()

# Define the ORM Model: This tells Python exactly how the SQL table is structured
class GroceryItem(Base):
    # This must match the name of the table we created in SQL
    __tablename__ = 'grocery_list'

    # Map the Python attributes to the SQL columns
    id = Column(Integer, primary_key=True, index=True)
    item_name = Column(String(255), nullable=False, unique=True)
    quantity = Column(Integer, default=1)
    
    # We map the metadata, but notice we don't actively touch it in our CRUD functions
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    aisle_category = Column(String(100), default='Uncategorized')

# Note: We don't need Base.metadata.create_all(engine) here because we already 
# manually created the table using the SQL script above!

# ---------------------------------------------------------
# MANAGER APPLICATION
# ---------------------------------------------------------

def main():
    print("🐘 Local Postgres Grocery Manager Initialized!")
    print("Commands: add [item] [qty] | modify [item] [qty] | delete [item] | list | exit")
    print("-" * 50)

    # The Infinite Loop
    while True:
        try:
            raw_input = input("\nEnter command: ").strip().lower()
            if not raw_input:
                continue

            parts = raw_input.split()
            command = parts[0]

            if command == 'exit':
                print("👋 Shutting down manager. See ya!")
                break

            # Open a fresh database session for this command
            db = SessionLocal()

            try:
                # --- READ (List) ---
                if command == 'list':
                    # Translates to: SELECT * FROM grocery_list ORDER BY id;
                    items = db.query(GroceryItem).order_by(GroceryItem.id).all()
                    
                    if not items:
                        print("📝 The database list is currently empty.")
                    else:
                        print("\n--- Current Grocery List ---")
                        for item in items:
                            # We can access columns simply as properties of the object!
                            print(f"📦 {item.item_name.capitalize()}: {item.quantity}")
                        print("----------------------------")

                # --- CREATE (Add) ---
                elif command == 'add':
                    if len(parts) < 3:
                        print("❌ Usage: add [item] [quantity]")
                        continue
                    
                    item_name = " ".join(parts[1:-1])
                    quantity = int(parts[-1]) # Convert the string input to an integer
                    
                    # Check if it already exists (SELECT * FROM grocery_list WHERE item_name = '...')
                    existing_item = db.query(GroceryItem).filter(GroceryItem.item_name == item_name).first()
                    
                    if existing_item:
                        print(f"⚠️ '{item_name}' is already in the DB. Use 'modify'.")
                    else:
                        # Create a new Python object and add it to the session
                        new_item = GroceryItem(item_name=item_name, quantity=quantity)
                        db.add(new_item)
                        db.commit() # Save the changes to Postgres
                        print(f"✅ Added {quantity} of '{item_name}' to Postgres.")

                # --- UPDATE (Modify) ---
                elif command == 'modify':
                    if len(parts) < 3:
                        print("❌ Usage: modify [item] [new_quantity]")
                        continue
                        
                    item_name = " ".join(parts[1:-1])
                    new_quantity = int(parts[-1])
                    
                    # Find the specific item
                    item_to_update = db.query(GroceryItem).filter(GroceryItem.item_name == item_name).first()
                    
                    if not item_to_update:
                        print(f"⚠️ '{item_name}' not found in the DB. Use 'add' first.")
                    else:
                        # Simply change the property and commit! SQLAlchemy handles the UPDATE sql.
                        item_to_update.quantity = new_quantity
                        db.commit()
                        print(f"✅ Modified '{item_name}' quantity to {new_quantity} in Postgres.")

                # --- DELETE ---
                elif command == 'delete':
                    if len(parts) < 2:
                        print("❌ Usage: delete [item]")
                        continue
                    
                    item_name = " ".join(parts[1:])
                    item_to_delete = db.query(GroceryItem).filter(GroceryItem.item_name == item_name).first()
                    
                    if item_to_delete:
                        # Delete the object from the session and commit
                        db.delete(item_to_delete)
                        db.commit()
                        print(f"🗑️ Deleted '{item_name}' from Postgres.")
                    else:
                        print(f"⚠️ '{item_name}' not found in the DB.")

                else:
                    print("❌ Unknown command.")
            
            except Exception as e:
                # If anything goes wrong with the SQL, rollback the transaction to prevent corruption
                db.rollback()
                print(f"❌ Database error during command: {e}")
            finally:
                # ALWAYS close the session to free up the connection back to the database pool
                db.close()

        except KeyboardInterrupt:
            print("\n👋 Force quitting. See ya!")
            break
        except Exception as e:
            print(f"❌ An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()