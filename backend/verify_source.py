import re
import ast

def verify_from_source(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract OPUS_MT_MODEL_MAP
    model_map_match = re.search(r'OPUS_MT_MODEL_MAP\s*=\s*({.*?})', content, re.DOTALL)
    if not model_map_match:
        print("Could not find OPUS_MT_MODEL_MAP in main.py")
        return
    
    # Extract LANG_PREFIX_MAP
    prefix_map_match = re.search(r'LANG_PREFIX_MAP\s*=\s*({.*?})', content, re.DOTALL)
    if not prefix_map_match:
        print("Could not find LANG_PREFIX_MAP in main.py")
        return

    try:
        # Use ast.literal_eval for safety, but with some preprocessing if needed
        # We need to handle potential comments or trailing commas
        model_map_str = model_map_match.group(1)
        # Simple cleanup of comments (crude but should work for this case)
        model_map_str = re.sub(r'#.*', '', model_map_str)
        model_map = ast.literal_eval(model_map_str)
        
        prefix_map_str = prefix_map_match.group(1)
        prefix_map_str = re.sub(r'#.*', '', prefix_map_str)
        prefix_map = ast.literal_eval(prefix_map_str)
        
        frontend_targets = [
            ('en', 'English'), ('hi', 'Hindi'), ('te', 'Telugu'), 
            ('ta', 'Tamil'), ('kn', 'Kannada'), ('ml', 'Malayalam'), 
            ('gu', 'Gujarati'), ('mr', 'Marathi'), ('bn', 'Bengali'), 
            ('od', 'Odia'), ('pa', 'Punjabi'), ('as', 'Assamese'), 
            ('ne', 'Nepali')
        ]
        
        print(f"Verifying {len(frontend_targets)-1} target languages from main.py source...")
        
        all_ok = True
        for code, name in frontend_targets:
            if code == 'en': continue
            
            pair = ('en', code)
            model = model_map.get(pair)
            prefix = prefix_map.get(pair, '')
            
            if not model:
                print(f"✗ MISSING: {name} ({code})")
                all_ok = False
            else:
                p_info = f"Prefix='{prefix.strip()}'" if prefix else "No prefix"
                print(f"✓ {name:10} ({code}): Model={model}, {p_info}")
        
        if all_ok:
            print("\nSUCCESS: All frontend languages are mapped correctly in main.py!")
        else:
            print("\nFAILURE: Some mappings are missing!")
            
    except Exception as e:
        print(f"Error parsing main.py: {e}")

if __name__ == "__main__":
    verify_from_source('backend/main.py')
