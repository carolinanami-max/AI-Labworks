"""
Step 3: JSON Validation with Pydantic
"""
import json
from pydantic import BaseModel, Field, field_validator, ValidationError
from typing import Optional
from enum import Enum

print("STEP 3: JSON VALIDATION WITH PYDANTIC")
print("="*50)

# ========== 1. COPY YOUR MODELS FROM STEP 2 ==========
print("\n1. Defining Pydantic models...")

class ProductCategory(str, Enum):
    ELECTRONICS = "electronics"
    CLOTHING = "clothing"
    HOME_GOODS = "home_goods"
    BOOKS = "books"
    OTHER = "other"

class Product(BaseModel):
    """Main product model for validation."""
    name: str = Field(..., min_length=1, max_length=100)
    price: float = Field(..., gt=0)
    category: ProductCategory
    description: Optional[str] = Field(None, max_length=500)
    brand: Optional[str] = Field(None, max_length=50)
    in_stock: bool = Field(True)
    
    @field_validator('price')
    @classmethod
    def price_not_too_high(cls, v):
        if v > 1000000:
            raise ValueError('Price seems unrealistically high')
        return v
    
    @field_validator('name')
    @classmethod
    def name_must_contain_letters(cls, v):
        if not any(c.isalpha() for c in v):
            raise ValueError('Name must contain letters')
        return v.strip()

class ProductListingRequest(BaseModel):
    """Full request for generating a product listing."""
    product: Product
    target_audience: str = Field("general")
    tone: str = Field("professional")
    language: str = Field("English")

print("   ✓ Models defined")

# ========== 2. TEST VALID JSON ==========
print("\n2. Testing valid_product.json with Pydantic:")

try:
    # Load JSON
    with open('json_samples/valid_product.json', 'r') as f:
        json_data = json.load(f)
    
    print("   ✓ JSON loaded")
    
    # Validate with Pydantic
    validated_data = ProductListingRequest(**json_data)
    print("   ✓ PYDANTIC VALIDATION PASSED!")
    print(f"   Product: {validated_data.product.name}")
    print(f"   Price: ${validated_data.product.price}")
    print(f"   Category: {validated_data.product.category}")
    print(f"   In stock: {validated_data.product.in_stock}")
    
except ValidationError as e:
    print(f"   ✗ Validation failed: {e}")
except Exception as e:
    print(f"   ✗ Error: {e}")

# ========== 3. TEST INVALID JSON ==========
print("\n3. Testing invalid_product.json with Pydantic:")

try:
    # Load JSON
    with open('json_samples/invalid_product.json', 'r') as f:
        json_data = json.load(f)
    
    print("   ✓ JSON loaded (but data is invalid)")
    
    # Try to validate with Pydantic - THIS SHOULD FAIL!
    validated_data = ProductListingRequest(**json_data)
    print("   ✗ ERROR: This should have failed but didn't!")
    
except ValidationError as e:
    print("   ✓ PYDANTIC CORRECTLY REJECTED INVALID DATA!")
    print(f"\n   Found {len(e.errors())} error(s):")
    
    for i, error in enumerate(e.errors(), 1):
        # Get the field path
        field_path = " → ".join(str(loc) for loc in error['loc'])
        error_msg = error['msg']
        error_type = error['type']
        
        print(f"\n   Error {i}:")
        print(f"     Field: {field_path}")
        print(f"     Problem: {error_msg}")
        print(f"     Type: {error_type}")
        
except Exception as e:
    print(f"   ✗ Different error: {e}")

print("\n" + "="*50)
print("✓ Step 3 complete!")
print("Valid JSON: Passed validation")
print("Invalid JSON: Correctly rejected")
print("="*50)