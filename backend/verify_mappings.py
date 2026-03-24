import sys
import os

# Add the current directory to sys.path to import main
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import OPUS_MT_MODEL_MAP, LANG_PREFIX_MAP, translate_text

def verify():
    frontend_targets = [
        ('en', 'English'),
        ('hi', 'Hindi'),
        ('te', 'Telugu'),
        ('ta', 'Tamil'),
        ('kn', 'Kannada'),
        ('ml', 'Malayalam'),
        ('gu', 'Gujarati'),
        ('mr', 'Marathi'),
        ('bn', 'Bengali'),
        ('od', 'Odia'),
        ('pa', 'Punjabi'),
        ('as', 'Assamese'),
        ('ne', 'Nepali')
    ]
    
    print("Verifying target language support in backend...")
    
    all_ok = True
    for code, name in frontend_targets:
        if code == 'en': continue
        
        pair = ('en', code)
        model = OPUS_MT_MODEL_MAP.get(pair)
        prefix = LANG_PREFIX_MAP.get(pair, '')
        
        if not model:
            print(f"✗ MISSING MODEL: {name} ({code}) has no model mapped for ('en', '{code}')")
            all_ok = False
        else:
            p_status = f"Prefix: '{prefix.strip()}'" if prefix else "No prefix"
            print(f"✓ {name:10} ({code}): Model={model}, {p_status}")
            
    # Check if we need to add more fallback or prefix entries
    print("\nChecking for missing prefixes in multilingual models...")
    for pair, model in OPUS_MT_MODEL_MAP.items():
        if 'en' in pair:
            if 'mul' in model or 'dra' in model or 'inc' in model:
                if pair not in LANG_PREFIX_MAP:
                    print(f"! WARNING: {pair} uses multilingual model {model} but HAS NO PREFIX")

    if all_ok:
        print("\nAll frontend targets are mapped correctly in the backend.")
    else:
        print("\nSome mappings are missing!")

if __name__ == "__main__":
    verify()
