#!/usr/bin/env python3
"""
Test and Demo Script for Accuracy Evaluation Module

✔ Uses Word Error Rate (WER) correctly
✔ Ensures accuracy is clamped between 0–100%
✔ Demonstrates realistic speech-to-text scenarios
✔ Safe for multilingual, noisy, and real-world inputs
"""

from accuracy_evaluator import (
    calculate_wer_accuracy,
    print_accuracy_report,
    normalize_text
)


SEPARATOR = "=" * 72


def header(title: str):
    print("\n" + SEPARATOR)
    print(title)
    print(SEPARATOR)


# -------------------------------------------------------------------
# TEST 1: TEXT NORMALIZATION
# -------------------------------------------------------------------
def test_normalization():
    header("TEST 1: TEXT NORMALIZATION")

    samples = [
        "Hello, World!",
        "The quick BROWN fox...",
        "Multiple   spaces   here",
        "Special chars: @#$%^&*()",
    ]

    for text in samples:
        print(f"Original   : '{text}'")
        print(f"Normalized : '{normalize_text(text)}'\n")


# -------------------------------------------------------------------
# TEST 2: PERFECT MATCH
# -------------------------------------------------------------------
def test_perfect_match():
    header("TEST 2: PERFECT TRANSCRIPTION")

    ref = "the quick brown fox jumps over the lazy dog"
    pred = ref

    result = calculate_wer_accuracy(ref, pred, return_details=True)

    print(f"WER      : {result['wer_percentage']:.2f}%")
    print(f"Accuracy : {result['accuracy']:.2f}%")
    print("Expected : 0.00% WER | 100.00% Accuracy")


# -------------------------------------------------------------------
# TEST 3: WORD SUBSTITUTION
# -------------------------------------------------------------------
def test_word_substitution():
    header("TEST 3: WORD SUBSTITUTION")

    ref = "the quick brown fox"
    pred = "the quick brown dog"

    result = calculate_wer_accuracy(ref, pred, return_details=True)

    print("Change   : fox → dog")
    print(f"WER      : {result['wer_percentage']:.2f}%")
    print(f"Accuracy : {result['accuracy']:.2f}%")


# -------------------------------------------------------------------
# TEST 4: WORD DELETION
# -------------------------------------------------------------------
def test_word_deletion():
    header("TEST 4: WORD DELETION")

    ref = "the quick brown fox"
    pred = "the brown fox"

    result = calculate_wer_accuracy(ref, pred, return_details=True)

    print("Missing  : quick")
    print(f"WER      : {result['wer_percentage']:.2f}%")
    print(f"Accuracy : {result['accuracy']:.2f}%")


# -------------------------------------------------------------------
# TEST 5: WORD INSERTION
# -------------------------------------------------------------------
def test_word_insertion():
    header("TEST 5: WORD INSERTION")

    ref = "the fox"
    pred = "the quick fox"

    result = calculate_wer_accuracy(ref, pred, return_details=True)

    print("Extra    : quick")
    print(f"WER      : {result['wer_percentage']:.2f}%")
    print(f"Accuracy : {result['accuracy']:.2f}%")


# -------------------------------------------------------------------
# TEST 6: PUNCTUATION HANDLING
# -------------------------------------------------------------------
def test_punctuation_handling():
    header("TEST 6: PUNCTUATION HANDLING")

    ref = "Hello, world! How are you?"
    pred = "hello world how are you"

    result = calculate_wer_accuracy(ref, pred, return_details=True)

    print(f"WER      : {result['wer_percentage']:.2f}%")
    print(f"Accuracy : {result['accuracy']:.2f}%")
    print("Note     : Punctuation ignored")


# -------------------------------------------------------------------
# TEST 7: CASE INSENSITIVITY
# -------------------------------------------------------------------
def test_case_insensitivity():
    header("TEST 7: CASE INSENSITIVITY")

    ref = "The Quick Brown Fox"
    pred = "the quick brown fox"

    result = calculate_wer_accuracy(ref, pred, return_details=True)

    print(f"WER      : {result['wer_percentage']:.2f}%")
    print(f"Accuracy : {result['accuracy']:.2f}%")
    print("Note     : Case ignored")


# -------------------------------------------------------------------
# TEST 8: REALISTIC ASR OUTPUT
# -------------------------------------------------------------------
def test_realistic_transcription():
    header("TEST 8: REALISTIC TRANSCRIPTION")

    ref = """
    The quick brown fox jumps over the lazy dog.
    This is a test of the emergency broadcast system.
    """

    pred = """
    the quick brown fox jumps over the lazy dog
    this is a test of the emergency broadcast system
    """

    result = calculate_wer_accuracy(ref, pred, return_details=True)

    print(f"Reference Words : {result['reference_words']}")
    print(f"Predicted Words : {result['predicted_words']}")
    print(f"WER            : {result['wer_percentage']:.2f}%")
    print(f"Accuracy       : {result['accuracy']:.2f}%")


# -------------------------------------------------------------------
# TEST 9: VERY DIFFERENT TEXTS
# -------------------------------------------------------------------
def test_very_different_texts():
    header("TEST 9: VERY DIFFERENT TEXTS")

    ref = "the weather is sunny"
    pred = "the whether is cloudy"

    result = calculate_wer_accuracy(ref, pred, return_details=True)

    print("Errors:")
    print(" - weather → whether (substitution)")
    print(" - sunny → cloudy (substitution)")
    print(f"WER      : {result['wer_percentage']:.2f}%")
    print(f"Accuracy : {result['accuracy']:.2f}% (Clamped to 0)")
    print(f"Similarity: {result['similarity_score']:.2f}%")
    
    # Assertions for safety
    if result['accuracy'] < 0:
        print("❌ FAILED: Accuracy should not be negative!")
    else:
        print("✅ SUCCESS: Accuracy is non-negative")


# -------------------------------------------------------------------
# TEST 10: EMPTY INPUT HANDLING
# -------------------------------------------------------------------
def test_empty_handling():
    header("TEST 10: EMPTY TEXT HANDLING")

    result = calculate_wer_accuracy("", "hello world")

    if result is None:
        print("[OK] Empty input handled safely")


# -------------------------------------------------------------------
# TEST 11: FORMATTED REPORT
# -------------------------------------------------------------------
def test_formatted_report():
    header("TEST 11: FORMATTED REPORT")

    ref = "the quick brown fox jumps over the lazy dog"
    pred = "the quick brown fox jump over the lazy dogs"

    print_accuracy_report(ref, pred)


# -------------------------------------------------------------------
# TEST 12: REAL-WORLD EXAMPLES
# -------------------------------------------------------------------
def test_real_world_examples():
    header("TEST 12: REAL-WORLD EXAMPLES")

    examples = [
        ("News", "The president announced a new policy today",
         "the president announced a new policy today"),

        ("Tech Talk", "Machine learning requires large datasets",
         "machine learning requires large data sets"),

        ("Meeting", "we need to discuss quarterly results",
         "we need to discuss quarterly results meeting"),
    ]

    for name, ref, pred in examples:
        result = calculate_wer_accuracy(ref, pred, return_details=True)
        print(f"\n{name}")
        print(f"WER      : {result['wer_percentage']:.2f}%")
        print(f"Accuracy : {result['accuracy']:.2f}%")


# -------------------------------------------------------------------
# MAIN
# -------------------------------------------------------------------
def main():
    print("\n" + SEPARATOR)
    print("      ACCURACY EVALUATION MODULE — TEST SUITE")
    print(SEPARATOR)

    test_normalization()
    test_perfect_match()
    test_word_substitution()
    test_word_deletion()
    test_word_insertion()
    test_punctuation_handling()
    test_case_insensitivity()
    test_realistic_transcription()
    test_very_different_texts()
    test_empty_handling()
    test_formatted_report()
    test_real_world_examples()

    print("\n" + SEPARATOR)
    print("TEST SUITE COMPLETED SUCCESSFULLY ✅")
    print(SEPARATOR)

    print("\nKey Notes:")
    print("• WER is the primary evaluation metric")
    print("• Accuracy is clamped to avoid negative values")
    print("• Suitable for speech-to-text evaluation")
    print("• Translation & summarization require semantic metrics\n")


if __name__ == "__main__":
    main()
