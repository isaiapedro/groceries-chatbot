import json
import os

# Define the file where our "database" will live
DB_FILE = 'grocery_list.json'

def load_data():
    """Loads grocery data from the JSON file into a Python dictionary."""
    if not os.path.exists(DB_FILE):
        return {} # Return an empty dictionary if the file is brand new
    
    try:
        with open(DB_FILE, 'r') as file:
            return json.load(file)
    except json.JSONDecodeError:
        print("⚠️ Warning: JSON file is corrupted. Starting fresh.")
        return {}

def save_data(data):
    """Saves the Python dictionary back to the JSON file."""
    with open(DB_FILE, 'w') as file:
        # indent=4 makes the JSON file readable by humans
        json.dump(data, file, indent=4) 

def main():
    print("🛒 Local Grocery Manager Initialized!")
    print("Commands:")
    print("  - add [item] [quantity]")
    print("  - modify [item] [new_quantity]")
    print("  - delete [item]")
    print("  - list")
    print("  - exit")
    print("-" * 30)

    # Step 1: Load existing data into memory
    groceries = load_data()

    # Step 2: The Infinite Loop
    while True:
        try:
            # Step 3: Get and parse input
            raw_input = input("\nEnter command: ").strip().lower()
            if not raw_input:
                continue

            # Split the input string by spaces into a list of words
            parts = raw_input.split()
            command = parts[0]

            if command == 'exit':
                print("👋 Shutting down manager. See ya!")
                break

            elif command == 'list':
                if not groceries:
                    print("📝 The list is currently empty.")
                else:
                    print("\n--- Current Grocery List ---")
                    for item, qty in groceries.items():
                        print(f"📦 {item.capitalize()}: {qty}")
                    print("----------------------------")

            # Step 4: CRUD Operations
            elif command in ['add', 'modify']:
                # Basic validation to ensure they provided an item and a quantity
                if len(parts) < 3:
                    print(f"❌ Usage: {command} [item] [quantity]")
                    continue
                
                # Combine words in case the item has a space (e.g., 'oat milk')
                # parts[1:-1] grabs everything between the command and the last word
                item_name = " ".join(parts[1:-1])
                quantity = parts[-1] 

                # Logic for Adding vs Modifying
                if command == 'add':
                    if item_name in groceries:
                        print(f"⚠️ '{item_name}' is already on the list. Use 'modify' to change the quantity.")
                    else:
                        groceries[item_name] = quantity
                        print(f"✅ Added {quantity} of '{item_name}'.")
                
                elif command == 'modify':
                    if item_name not in groceries:
                        print(f"⚠️ '{item_name}' is not on the list yet. Use 'add' first.")
                    else:
                        groceries[item_name] = quantity
                        print(f"✅ Modified '{item_name}' quantity to {quantity}.")

                # Step 5: Save state after making a change
                save_data(groceries)

            elif command == 'delete':
                if len(parts) < 2:
                    print("❌ Usage: delete [item]")
                    continue
                
                item_name = " ".join(parts[1:])
                if item_name in groceries:
                    # Remove the key-value pair from the dictionary
                    del groceries[item_name]
                    print(f"🗑️ Deleted '{item_name}' from the list.")
                    save_data(groceries)
                else:
                    print(f"⚠️ '{item_name}' not found on the list.")

            else:
                print("❌ Unknown command. Please use add, modify, delete, list, or exit.")

        except KeyboardInterrupt:
            # Graceful shutdown if the user presses Ctrl+C
            print("\n👋 Force quitting. Data was saved safely!")
            break
        except Exception as e:
            print(f"❌ An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()