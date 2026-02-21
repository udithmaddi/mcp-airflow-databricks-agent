import csv
import random
import datetime
import os

# ==============================================================================
# 🎲 DATA SIMULATOR
# This file creates fake "Sales Data" so we have something to practice with.
# It makes 100,000 rows of pretend orders.
# ==============================================================================

# 1. SETTINGS: How much data do we want?
NUM_ROWS = 100_000
OUTPUT_FILE = "sales_data.csv"

# 2. DEFINITIONS: What does our business sell?
CATEGORIES = ["Electronics", "Clothing", "Home & Garden", "Toys", "Books"]
STATUSES = ["COMPLETED", "PENDING", "CANCELLED", "RETURNED"]
PRODUCTS = {
    "Electronics": ["Laptop", "Smartphone", "Headphones", "Monitor"],
    "Clothing": ["T-Shirt", "Jeans", "Jacket", "Sneakers"],
    "Home & Garden": ["Sofa", "Chair", "Table", "Lamp"],
    "Toys": ["Lego Set", "Doll", "Action Figure", "Board Game"],
    "Books": ["Novel", "Textbook", "Cookbook", "Comic"]
}

def generate_data():
    """Main function to create the file."""
    print(f"Generating {NUM_ROWS} rows of data...")
    
    with open(OUTPUT_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        # WRITE HEADER: The names of the columns
        writer.writerow(["order_id", "date", "customer_id", "category", "product", "amount", "status"])
        
        start_date = datetime.date(2024, 1, 1)
        
        # LOOP: Do this 100,000 times
        for i in range(1, NUM_ROWS + 1):
            order_id = f"ORD-{i:06d}"
            
            # Pick a random date in 2024/2025
            days_offset = random.randint(0, 365)
            date = start_date + datetime.timedelta(days=days_offset)
            
            # Pick a random customer
            customer_id = random.randint(1000, 5000)
            
            # Pick a random product
            category = random.choice(CATEGORIES)
            product = random.choice(PRODUCTS[category])
            
            # Pick a random price (between $10 and $500)
            amount = round(random.uniform(10.0, 500.0), 2)
            
            # Pick a status (Most orders should be COMPLETED)
            status = random.choices(STATUSES, weights=[70, 10, 10, 10], k=1)[0]
            
            # Save the row
            writer.writerow([order_id, date, customer_id, category, product, amount, status])

    print(f"Success! Data saved to '{os.path.abspath(OUTPUT_FILE)}'")

if __name__ == "__main__":
    generate_data()
