import os
import requests
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
SARVAM_API_KEY = os.getenv('SARVAM_API_KEY')

async def test_sarvam_translation():
    """Test Sarvam AI translation directly"""
    
    print(f"API Key: {SARVAM_API_KEY}")
    
    test_text = "Hello, how are you? I am learning English."
    source_lang = "en-IN" 
    target_lang = "hi-IN"
    
    url = 'https://api.sarvam.ai/translate'
    headers = {
        'api-subscription-key': SARVAM_API_KEY,
        'content-type': 'application/json'
    }
    
    payload = {
        "input": test_text,
        "source_language_code": source_lang,
        "target_language_code": target_lang,
        "model": "sarvam-translate:v1",
        "mode": "formal",
        "numerals_format": "native",
        "speaker_gender": "Male",
        "enable_preprocessing": True
    }
    
    print(f"Testing translation:")
    print(f"From: {source_lang}")
    print(f"To: {target_lang}")
    print(f"Text: {test_text}")
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            translated = result.get('translated_text', 'No translation found')
            print(f"Translated: {translated}")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    asyncio.run(test_sarvam_translation())