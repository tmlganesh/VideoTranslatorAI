"""
Test the local Helsinki-NLP/opus-mt translation endpoint.
Make sure the backend server is running before executing this script:
    python main.py

Models are loaded on-demand at first use (no API keys needed).
"""

import requests
import json

BASE_URL = "http://localhost:8000"


def test_translation(text: str, source_language: str, target_language: str):
    """POST to /api/translate/ and print the result."""
    payload = {
        "text": text,
        "source_language": source_language,
        "target_language": target_language,
    }
    print(f"\n{'='*60}")
    print(f"  {source_language} → {target_language}")
    print(f"  Source: {text[:80]}{'...' if len(text) > 80 else ''}")

    try:
        response = requests.post(
            f"{BASE_URL}/api/translate/",
            json=payload,
            timeout=180,  # First load can take time on CPU
        )
        print(f"  HTTP Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"  Status     : {result.get('status')}")
            translated = result.get('translated_text', '')
            print(f"  Translated : {translated[:120]}{'...' if len(translated) > 120 else ''}")
            return True
        else:
            print(f"  ERROR: {response.text}")
            return False
    except requests.exceptions.ConnectionError:
        print("  ERROR: Could not connect. Is the server running? (python main.py)")
        return False
    except Exception as e:
        print(f"  Exception: {e}")
        return False


if __name__ == "__main__":
    # Check server is up
    try:
        health = requests.get(f"{BASE_URL}/", timeout=10)
        print(f"Server health check: {health.json()}")
    except Exception:
        print("Server not reachable. Start it with: python main.py")
        exit(1)

    results = []

    # --- English → Indian Languages ---
    print("\n" + "#"*60)
    print("# English → Indian Languages")
    print("#"*60)

    results.append(("en→hi", test_translation(
        text="Hello, how are you? I am learning to speak Hindi.",
        source_language="en",
        target_language="hi",
    )))

    results.append(("en→te", test_translation(
        text="The weather today is very pleasant and the sky is clear.",
        source_language="en",
        target_language="te",
    )))

    results.append(("en→ta", test_translation(
        text="Good morning, welcome to our school.",
        source_language="en",
        target_language="ta",
    )))

    # --- Indian Languages → English ---
    print("\n" + "#"*60)
    print("# Indian Languages → English")
    print("#"*60)

    results.append(("hi→en", test_translation(
        text="नमस्ते, आप कैसे हैं? मैं हिंदी सीख रहा हूं।",
        source_language="hi",
        target_language="en",
    )))

    results.append(("te→en", test_translation(
        text="నమస్కారం. మీరు ఎలా ఉన్నారు? భారతదేశం ఒక గొప్ప దేశం.",
        source_language="te",
        target_language="en",
    )))

    # --- European Languages ---
    print("\n" + "#"*60)
    print("# European Languages")
    print("#"*60)

    results.append(("en→fr", test_translation(
        text="Hello, how are you? I am learning French.",
        source_language="en",
        target_language="fr",
    )))

    results.append(("fr→en", test_translation(
        text="Bonjour, comment allez-vous? Je suis heureux.",
        source_language="fr",
        target_language="en",
    )))

    # --- Pivot Translation (non-English ↔ non-English) ---
    print("\n" + "#"*60)
    print("# Pivot Translation (via English)")
    print("#"*60)

    results.append(("te→hi (pivot)", test_translation(
        text="నమస్కారం. మీరు ఎలా ఉన్నారు?",
        source_language="te",
        target_language="hi",
    )))

    results.append(("hi→fr (pivot)", test_translation(
        text="नमस्ते, आज मौसम बहुत अच्छा है।",
        source_language="hi",
        target_language="fr",
    )))

    # --- Summary ---
    print("\n" + "="*60)
    print("  RESULTS SUMMARY")
    print("="*60)
    passed = sum(1 for _, ok in results if ok)
    total = len(results)
    for label, ok in results:
        status = "✓ PASS" if ok else "✗ FAIL"
        print(f"  {status}  {label}")
    print(f"\n  {passed}/{total} tests passed")
    print("="*60)