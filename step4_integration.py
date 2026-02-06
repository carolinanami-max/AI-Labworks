"""
Step 4: Integrating Validation with ChatGPT API
"""
import os
import json
from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator, ValidationError
from typing import Optional, List
from enum import Enum
from openai import OpenAI

print("STEP 4: INTEGRATING VALIDATION WITH CHATGPT")
print("="*60)

# ========== 1. LOAD ENVIRONMENT ==========
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    print("❌ ERROR: OPENAI_API_KEY not found in .env file")
    print("   Make sure you have a .env file with: OPENAI_API_KEY=your-key")
    exit(1)

client = OpenAI(api_key=api_key)
print("✅ API Key loaded and client initialized")

# ========== 2. YOUR PYDANTIC MODELS ==========
print("\n1. Loading Pydantic models...")

class ProductCategory(str, Enum):
    ELECTRONICS = "electronics"
    CLOTHING = "clothing"
    HOME_GOODS = "home_goods"
    BOOKS = "books"
    OTHER = "other"

class Product(BaseModel):
    """Product model for validation."""
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
            raise ValueError('Price too high')
        return v

class ProductListingRequest(BaseModel):
    """Request for generating product listing."""
    product: Product
    target_audience: str = Field("general")
    tone: str = Field("professional")
    language: str = Field("English")

# ========== 3. CHATGPT RESPONSE MODEL ==========
class ChatGPTResponse(BaseModel):
    """Model for validating ChatGPT responses."""
    title: str = Field(..., min_length=10, max_length=100)
    description: str = Field(..., min_length=100, max_length=1000)
    features: List[str] = Field(..., min_length=3, max_length=10)
    keywords: str = Field(..., min_length=10)

print("   ✓ Models loaded")

# ========== 4. VALIDATION FUNCTION ==========
def validate_input(json_data: dict):
    """Validate input JSON using Pydantic."""
    print("\n2. Validating input data...")
    try:
        validated = ProductListingRequest(**json_data)
        print(f"   ✅ Input validation PASSED")
        print(f"   Product: {validated.product.name}")
        print(f"   Price: ${validated.product.price}")
        print(f"   Category: {validated.product.category}")
        return validated
    except ValidationError as e:
        print(f"   ❌ Input validation FAILED")
        print(f"   Found {len(e.errors())} error(s):")
        for error in e.errors():
            field = " → ".join(str(loc) for loc in error['loc'])
            print(f"     • {field}: {error['msg']}")
        return None

# ========== 5. CHATGPT FUNCTION ==========
def call_chatgpt(product_request: ProductListingRequest):
    """Call ChatGPT API with validated data."""
    print("\n3. Calling ChatGPT API...")
    
    product = product_request.product
    
    prompt = f"""Create a product listing for marketing purposes.

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

IMPORTANT: Respond with ONLY valid JSON in this exact format:
{{
    "title": "Product title here (catchy, 60 characters max)",
    "description": "Detailed product description (100-300 words)",
    "features": ["Feature 1", "Feature 2", "Feature 3", "Feature 4", "Feature 5"],
    "keywords": "comma, separated, keywords, for, seo"
}}"""

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # Using 3.5 for speed, can change to gpt-4
            messages=[
                {"role": "system", "content": "You are a marketing expert. Always respond with valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        content = response.choices[0].message.content
        
        # Clean response (remove markdown if present)
        if content.startswith("```json"):
            content = content[7:-3]
        elif content.startswith("```"):
            content = content[3:-3]
        
        print(f"   ✅ ChatGPT response received")
        return content
        
    except Exception as e:
        print(f"   ❌ ChatGPT API error: {e}")
        return None

# ========== 6. VALIDATE CHATGPT RESPONSE ==========
def validate_chatgpt_response(response_text: str):
    """Validate ChatGPT response using Pydantic."""
    print("\n4. Validating ChatGPT response...")
    
    try:
        # Parse JSON
        response_data = json.loads(response_text)
        
        # Validate with Pydantic
        validated_response = ChatGPTResponse(**response_data)
        
        print(f"   ✅ Response validation PASSED")
        print(f"   Title: {validated_response.title}")
        print(f"   Features: {len(validated_response.features)} items")
        print(f"   Keywords: {validated_response.keywords}")
        
        return validated_response
        
    except json.JSONDecodeError:
        print(f"   ❌ Response is not valid JSON")
        return None
    except ValidationError as e:
        print(f"   ❌ Response validation FAILED")
        for error in e.errors():
            field = " → ".join(str(loc) for loc in error['loc'])
            print(f"     • {field}: {error['msg']}")
        return None

# ========== 7. MAIN PROCESSING FUNCTION ==========
def process_product_request(json_data: dict):
    """Complete processing pipeline with validation at every step."""
    print("\n" + "="*60)
    print("STARTING PROCESSING PIPELINE")
    print("="*60)
    
    # Step 1: Validate input
    validated_input = validate_input(json_data)
    if not validated_input:
        return {"status": "input_validation_failed", "error": "Input data invalid"}
    
    # Step 2: Call ChatGPT
    chatgpt_response = call_chatgpt(validated_input)
    if not chatgpt_response:
        return {"status": "chatgpt_failed", "error": "ChatGPT API call failed"}
    
    # Step 3: Validate ChatGPT response
    validated_output = validate_chatgpt_response(chatgpt_response)
    if not validated_output:
        return {"status": "output_validation_failed", "error": "ChatGPT response invalid", "raw_response": chatgpt_response}
    
    # Success!
    return {
        "status": "success",
        "input": validated_input.dict(),
        "output": validated_output.dict(),
        "message": "✅ Complete pipeline successful with validation at every step!"
    }

# ========== 8. TEST FUNCTION ==========
def test_integration():
    """Test the complete integration."""
    print("\n" + "="*60)
    print("TESTING COMPLETE INTEGRATION")
    print("="*60)
    
    # Test data (using your valid_product.json structure)
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
    
    # Process the request
    result = process_product_request(test_data)
    
    # Display results
    print("\n" + "="*60)
    print("FINAL RESULT")
    print("="*60)
    
    if result["status"] == "success":
        print("🎉 SUCCESS! Complete pipeline worked!")
        print("\nGenerated Listing:")
        print(f"Title: {result['output']['title']}")
        print(f"\nDescription (first 100 chars):")
        print(f"{result['output']['description'][:100]}...")
        print(f"\nFeatures:")
        for i, feature in enumerate(result['output']['features'], 1):
            print(f"  {i}. {feature}")
        print(f"\nKeywords: {result['output']['keywords']}")
    else:
        print(f"❌ FAILED: {result.get('error', 'Unknown error')}")
        if "raw_response" in result:
            print(f"\nRaw ChatGPT response:")
            print(result["raw_response"][:200] + "...")
    
    return result

# ========== 9. MAIN ==========
if __name__ == "__main__":
    print("\n" + "="*60)
    print("STEP 4: VALIDATED CHATGPT API PIPELINE")
    print("="*60)
    
    # Run test
    result = test_integration()
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Status: {result['status']}")
    print(f"Validation steps: Input → ChatGPT → Output")
    print(f"Every step validated with Pydantic models")