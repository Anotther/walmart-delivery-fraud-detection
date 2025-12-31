import csv
import os

# Define file paths
BASE_DIR = r"C:\Users\leona\OneDrive\Documentos\Datatech Florida\Detecção de Fraudes em Entregas do Walmart"
INPUT_FILE = os.path.join(BASE_DIR, "products_data.csv")
TEMP_FILE = os.path.join(BASE_DIR, "products_data_temp.csv")

# Define category keywords
ELECTRONICS_KEYWORDS = [
    "Headphone", "Mouse", "Galaxy", "MacBook", "Earbuds", "PlayStation", "Echo", 
    "Camera", "Surface", "RTX", "iPad", "Dell", "GoPro", "Kindle", "Printer", 
    "Watch", "Chromecast", "Drone", "TV", "Fitbit", "Vacuum", "iPhone", "Laptop", 
    "Roku", "Speaker", "Thermostat", "Nintendo", "Switch"
]

def get_category(product_name):
    """Determines category based on product name."""
    for keyword in ELECTRONICS_KEYWORDS:
        if keyword.lower() in product_name.lower():
            return "Electronics"
    return "Supermarket"

def main():
    print(f"Processing {INPUT_FILE}...")
    
    with open(INPUT_FILE, mode='r', encoding='utf-8', newline='') as infile, \
         open(TEMP_FILE, mode='w', encoding='utf-8', newline='') as outfile:
        
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames
        
        # Ensure 'category' is in fieldnames (it should be, but just in case)
        if 'category' not in fieldnames:
            fieldnames.append('category')
            
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        
        count = 0
        categories_count = {"Electronics": 0, "Supermarket": 0}
        
        for row in reader:
            product_name = row['product_name']
            new_top_category = get_category(product_name)
            
            # Update the category column
            row['category'] = new_top_category
            
            categories_count[new_top_category] += 1
            writer.writerow(row)
            count += 1
            
    # Replace original file with new file
    os.replace(TEMP_FILE, INPUT_FILE)
    
    print(f"Successfully processed {count} items.")
    print("New Category Distribution:")
    for cat, qty in categories_count.items():
        print(f"  - {cat}: {qty}")

if __name__ == "__main__":
    main()
