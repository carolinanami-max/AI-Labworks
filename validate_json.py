"""
Simple JSON Validation Test
Step 3 - Part 1: Just test loading JSON files
"""
import json

print("JSON FILE LOADING TEST")
print("="*50)

# First, let's just test if we can load JSON files
try:
    # Try to load the valid JSON file
    with open('json_samples/valid_product.json', 'r') as f:
        data = json.load(f)
    
    print("✓ Successfully loaded valid_product.json")
    print(f"  File contains: {list(data.keys())}")
    print(f"  Product name: {data['product']['name']}")
    print(f"  Price: ${data['product']['price']}")
    
except FileNotFoundError:
    print("✗ ERROR: File not found!")
    print("  Make sure you:")
    print("  1. Created the 'json_samples' folder")
    print("  2. Created 'valid_product.json' inside it")
    print("  3. Saved the file")
except json.JSONDecodeError as e:
    print(f"✗ ERROR: Invalid JSON format: {e}")
except Exception as e:
    print(f"✗ ERROR: {e}")

print("\n" + "="*50)
print("If you see the product name above, you're ready!")
print("="*50)