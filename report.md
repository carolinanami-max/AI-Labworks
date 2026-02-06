"""
Lab M1.06 - API Calling with JSON
Complete API Validation System with Pydantic and ChatGPT Integration
Student: Carolina Nami
Date: [06.02]
"""

import os
import json
from typing import Optional, List
from enum import Enum
from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator, ValidationError
from openai import OpenAI

print("="*60)
print("LAB M1.06: API CALLING WITH JSON - COMPLETE SOLUTION")
print("="*60)

# ========== PART 1: PYDANTIC MODELS ==========
class ProductCategory(str, Enum):
    """Valid product categories."""
    ELECTRONICS = "electronics"
    CLOTHING = "clothing"
    HOME_GOODS = "home_goods"
    BOOKS = "books"
    OTHER = "other"

class Product(BaseModel):
    """Product model with comprehensive validation."""
    name: str = Field(..., min_length=1, max_length=100, description="Product name")
    price: float = Field(..., gt=0, description="Price must be positive")
    category: ProductCategory = Field(..., description="Valid product category")
    description: Optional[str] = Field(None, max_length=500, description="Optional description")
    brand: Optional[str] = Field(None, max_length=50, description="Brand name")
    in_stock: bool = Field(True, description="Availability status")
    
    @field_validator('price')
    @classmethod
    def price_not_too_high(cls, v):
        """Custom validator for reasonable price."""
        if v > 1000000:
            raise ValueError('Price seems unrealistically high')
        return v
    
    @field_validator('name')
    @classmethod
    def name_must_contain_letters(cls, v):
        """Custom validator for meaningful product names."""
        if not any(c.isalpha() for c in v):
            raise ValueError('Name must contain letters')
        return v.strip()

class ProductListingRequest(BaseModel):
    """Complete request model for product listing generation."""
    product: Product
    target_audience: str = Field("general", description="Target audience")
    tone: str = Field("professional", description="Tone of listing")
    language: str = Field("English", description="Language for listing")

class ChatGPTResponse(BaseModel):
    """Model for validating ChatGPT responses."""
    title: str = Field(..., min_length=10, max_length=100)
    description: str = Field(..., min_length=100, max_length=1000)
    features: List[str] = Field(..., min_length=3, max_length=10)
    keywords: str = Field(..., min_length=10)

# ========== PART 2: VALIDATION FUNCTIONS ==========
def validate_json_file(file_path: str):
    """
    Validate JSON file using Pydantic models.
    
    Args:
        file_path: Path to JSON file
        
    Returns:
        Dictionary with validation results
    """
    print(f"\nValidating: {file_path}")
    print("-"*40)
    
    try:
        # Load JSON
        with open(file_path, 'r') as f:
            json_data = json.load(f)
        
        # Validate with Pydantic
        validated_data = ProductListingRequest(**json_data)
        
        print("✅ VALIDATION PASSED")
        print(f"  Product: {validated_data.product.name}")
        print(f"  Price: ${validated_data.product.price}")
        print(f"  Category: {validated_data.product.category}")
        
        return {
            "status": "success",
            "data": validated_data.dict(),
            "errors": None
        }
        
    except ValidationError as e:
        print("❌ VALIDATION FAILED")
        print(f"  Found {len(e.errors())} error(s):")
        
        errors = []
        for error in e.errors():
            field_path = " → ".join(str(loc) for loc in error['loc'])
            errors.append(f"{field_path}: {error['msg']}")
            print(f"    • {field_path}: {error['msg']}")
        
        return {
            "status": "error",
            "data": None,
            "errors": errors
        }
    
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return {
            "status": "error",
            "data": None,
            "errors": str(e)
        }

# ========== PART 3: CHATGPT INTEGRATION ==========
def setup_chatgpt_client():
    """Initialize ChatGPT client with API key."""
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in .env file")
    
    return OpenAI(api_key=api_key)

def generate_product_listing(client: OpenAI, product_request: ProductListingRequest):
    """
    Generate product listing using ChatGPT with validated input.
    
    Args:
        client: OpenAI client
        product_request: Validated product request
        
    Returns:
        Dictionary with generated listing
    """
    product = product_request.product
    
    prompt = f"""Create a professional product listing for marketing.

PRODUCT DETAILS:
- Name: {product.name}
- Price: ${product.price}
- Category: {product.category}
- Brand: {product.brand if product.brand else 'Not specified'}
- Description: {product.description if product.description else 'No description provided'}
- In Stock: {'Yes' if product.in_stock else 'No'}

TARGET AUDIENCE: {product_request.target_audience}
TONE: {product_request.tone}
LANGUAGE: {product_request.language}

Respond with ONLY valid JSON in this exact format:
{{
    "title": "Product title here",
    "description": "Detailed product description",
    "features": ["Feature 1", "Feature 2", "Feature 3", "Feature 4", "Feature 5"],
    "keywords": "comma, separated, keywords, for, seo"
}}"""

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a marketing expert. Always respond with valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        content = response.choices[0].message.content
        
        # Clean markdown if present
        if content.startswith("```json"):
            content = content[7:-3]
        elif content.startswith("```"):
            content = content[3:-3]
        
        # Validate the response
        response_data = json.loads(content)
        validated_response = ChatGPTResponse(**response_data)
        
        return {
            "status": "success",
            "response": validated_response.dict()
        }
        
    except ValidationError as e:
        return {
            "status": "validation_error",
            "error": f"ChatGPT response validation failed: {e}",
            "raw_response": content
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

# ========== PART 4: CLIENT REQUEST HANDLER ==========
def handle_client_request(json_data: dict):
    """
    Complete handler for client requests with validation at every step.
    
    Args:
        json_data: Dictionary with product data
        
    Returns:
        Dictionary with processing results
    """
    print("\n" + "="*60)
    print("HANDLING CLIENT REQUEST")
    print("="*60)
    
    # Step 1: Validate input
    print("\n1. Validating input data...")
    try:
        validated_input = ProductListingRequest(**json_data)
        print("   ✅ Input validation passed")
    except ValidationError as e:
        print("   ❌ Input validation failed")
        return {
            "status": "input_validation_failed",
            "errors": [f"{' → '.join(str(loc) for loc in err['loc'])}: {err['msg']}" for err in e.errors()]
        }
    
    # Step 2: Initialize ChatGPT client
    print("\n2. Initializing ChatGPT client...")
    try:
        client = setup_chatgpt_client()
        print("   ✅ ChatGPT client ready")
    except Exception as e:
        print(f"   ❌ Failed to initialize client: {e}")
        return {"status": "setup_failed", "error": str(e)}
    
    # Step 3: Generate listing
    print("\n3. Generating product listing...")
    result = generate_product_listing(client, validated_input)
    
    if result["status"] == "success":
        print("   ✅ Listing generated successfully")
        return {
            "status": "success",
            "input": validated_input.dict(),
            "output": result["response"],
            "message": "Complete pipeline successful with validation at every step"
        }
    else:
        print(f"   ❌ Generation failed: {result.get('error')}")
        return result

# ========== PART 5: DEMONSTRATION FUNCTIONS ==========
def create_sample_json_files():
    """Create sample JSON files for demonstration."""
    # Create sample folder if it doesn't exist
    os.makedirs("json_samples", exist_ok=True)
    
    # Create valid sample
    valid_data = {
        "product": {
            "name": "Wireless Headphones",
            "price": 129.99,
            "category": "electronics",
            "description": "Noise-cancelling wireless headphones with 30-hour battery life",
            "brand": "SoundMax",
            "in_stock": True
        },
        "target_audience": "tech enthusiasts",
        "tone": "enthusiastic",
        "language": "English"
    }
    
    # Create invalid sample (with multiple errors)
    invalid_data = {
        "product": {
            "name": "",  # Empty name
            "price": -50.00,  # Negative price
            "category": "invalid_category",  # Invalid category
            "in_stock": "yes"  # Wrong type
        },
        "target_audience": "",  # Empty
        "tone": 123,  # Wrong type
        "language": 456  # Wrong type
    }
    
    # Save files
    with open("json_samples/valid_product.json", "w") as f:
        json.dump(valid_data, f, indent=2)
    
    with open("json_samples/invalid_product.json", "w") as f:
        json.dump(invalid_data, f, indent=2)
    
    print("✅ Sample JSON files created in 'json_samples/' folder")
    print("   - valid_product.json: Complete valid product data")
    print("   - invalid_product.json: Data with multiple validation errors")

def demonstrate_json_validation():
    """Demonstrate JSON file validation."""
    print("\n" + "="*60)
    print("DEMONSTRATION 1: JSON FILE VALIDATION")
    print("="*60)
    
    # Create sample files
    create_sample_json_files()
    
    # Test valid file
    print("\n" + "-"*40)
    print("Testing valid_product.json:")
    print("-"*40)
    valid_result = validate_json_file("json_samples/valid_product.json")
    
    # Test invalid file
    print("\n" + "-"*40)
    print("Testing invalid_product.json:")
    print("-"*40)
    invalid_result = validate_json_file("json_samples/invalid_product.json")
    
    return valid_result, invalid_result

def demonstrate_complete_workflow():
    """Demonstrate complete workflow with ChatGPT integration."""
    print("\n" + "="*60)
    print("DEMONSTRATION 2: COMPLETE WORKFLOW")
    print("="*60)
    
    test_data = {
        "product": {
            "name": "Premium Coffee Maker",
            "price": 89.99,
            "category": "home_goods",
            "description": "Programmable coffee maker with thermal carafe",
            "brand": "BrewMaster",
            "in_stock": True
        },
        "target_audience": "home baristas",
        "tone": "warm and inviting",
        "language": "English"
    }
    
    print(f"\nTest Product: {test_data['product']['name']}")
    print(f"Price: ${test_data['product']['price']}")
    print(f"Category: {test_data['product']['category']}")
    
    result = handle_client_request(test_data)
    
    print("\n" + "="*60)
    print("WORKFLOW RESULT")
    print("="*60)
    
    if result["status"] == "success":
        print("✅ COMPLETE WORKFLOW SUCCESSFUL!")
        print(f"\nGenerated Listing:")
        print(f"Title: {result['output']['title']}")
        print(f"\nDescription (first 150 chars):")
        print(f"{result['output']['description'][:150]}...")
        print(f"\nFeatures:")
        for i, feature in enumerate(result['output']['features'], 1):
            print(f"  {i}. {feature}")
        print(f"\nKeywords: {result['output']['keywords']}")
    else:
        print(f"❌ Workflow failed: {result.get('error', 'Unknown error')}")
        if "errors" in result:
            for error in result["errors"]:
                print(f"  - {error}")
    
    return result

# ========== PART 6: MAIN EXECUTION & DEMONSTRATION ==========
def run_complete_demonstration():
    """Run the complete demonstration of all features."""
    print("\n" + "="*60)
    print("COMPLETE SYSTEM DEMONSTRATION")
    print("="*60)
    
    print("\n🎯 This demonstration will show:")
    print("   1. JSON file validation (valid and invalid examples)")
    print("   2. Complete workflow with ChatGPT integration")
    print("   3. Validation at every step of the pipeline")
    
    # Part 1: JSON Validation Demo
    print("\n" + "="*60)
    print("STARTING PART 1: JSON VALIDATION")
    print("="*60)
    valid_result, invalid_result = demonstrate_json_validation()
    
    # Part 2: Complete Workflow Demo (only if API key is available)
    print("\n" + "="*60)
    print("STARTING PART 2: COMPLETE WORKFLOW")
    print("="*60)
    
    # Check for API key
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    
    if api_key:
        print(f"✅ OpenAI API key found: {api_key[:12]}...")
        workflow_result = demonstrate_complete_workflow()
    else:
        print("⚠️  OpenAI API key not found in .env file")
        print("   Complete workflow demonstration requires API key")
        print("   Add your key to .env file as: OPENAI_API_KEY=your_key_here")
        print("\n   For now, showing what would happen with valid data...")
        
        # Show the validation part would work
        test_data = {
            "product": {
                "name": "Sample Product",
                "price": 99.99,
                "category": "electronics",
                "in_stock": True
            },
            "target_audience": "general",
            "tone": "professional",
            "language": "English"
        }
        
        print(f"\nInput validation would pass for:")
        print(f"  Product: {test_data['product']['name']}")
        print(f"  Price: ${test_data['product']['price']}")
        print(f"  Category: {test_data['product']['category']}")
        workflow_result = {"status": "api_key_missing", "note": "Add API key to test ChatGPT"}
    
    # Summary
    print("\n" + "="*60)
    print("DEMONSTRATION SUMMARY")
    print("="*60)
    
    print(f"\n📊 Results:")
    print(f"  JSON Validation Test 1 (valid): {'✅ PASSED' if valid_result['status'] == 'success' else '❌ FAILED'}")
    print(f"  JSON Validation Test 2 (invalid): {'✅ Correctly rejected' if invalid_result['status'] == 'error' else '❌ Should have failed'}")
    
    if api_key and workflow_result.get('status') == 'success':
        print(f"  Complete Workflow: ✅ SUCCESSFUL")
    elif api_key:
        print(f"  Complete Workflow: ❌ FAILED")
    else:
        print(f"  Complete Workflow: ⚠️  API key needed")
    
    print(f"\n✅ Validation errors caught: {len(invalid_result.get('errors', [])) if invalid_result.get('errors') else 0}")
    
    print("\n" + "="*60)
    print("DEMONSTRATION COMPLETE")
    print("="*60)
    
    return valid_result, invalid_result, workflow_result

# ========== MAIN FUNCTION ==========
def main():
    """Main entry point for the application."""
    print("\n" + "="*60)
    print("LAB M1.06 - API CALLING WITH JSON")
    print("Student: Carolina Nami")
    print("="*60)
    
    # Ask user what they want to do
    print("\nSelect demonstration mode:")
    print("  1. Run complete demonstration (all features)")
    print("  2. Test JSON validation only")
    print("  3. Test complete workflow (requires API key)")
    
    try:
        choice = input("\nEnter choice (1-3, default=1): ").strip()
        
        if choice == "2":
            # JSON validation only
            valid_result, invalid_result = demonstrate_json_validation()
        elif choice == "3":
            # Complete workflow only
            workflow_result = demonstrate_complete_workflow()
        else:
            # Complete demonstration (default)
            run_complete_demonstration()
            
    except KeyboardInterrupt:
        print("\n\n👋 Demonstration interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during demonstration: {e}")

# ========== RUN THE APPLICATION ==========
if __name__ == "__main__":
    main()
    print("\n" + "="*60)
    print("Thank you for using the API Validation System!")
    print("="*60)