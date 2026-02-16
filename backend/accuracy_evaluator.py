"""
Accuracy Evaluation Module for Speech-to-Text Output

This module provides functions to evaluate the accuracy of speech-to-text models
using Word Error Rate (WER) metric and derived accuracy percentage.

Functions:
    - calculate_wer_accuracy: Calculate WER and accuracy percentage
    - normalize_text: Normalize text for fair comparison
"""

import re
from jiwer import wer, cer


def normalize_text(text):
    """
    Normalize text for fair comparison by:
    1. Converting to lowercase
    2. Removing punctuation
    3. Removing extra whitespace
    
    Args:
        text (str): Input text to normalize
        
    Returns:
        str: Normalized text
        
    Example:
        >>> normalize_text("Hello, World!")
        'hello world'
    """
    # Convert to lowercase
    text = text.lower()
    
    # Remove punctuation (keep spaces and alphanumeric)
    text = re.sub(r'[^\w\s]', '', text)
    
    # Remove extra whitespace (multiple spaces -> single space)
    text = re.sub(r'\s+', ' ', text)
    
    # Strip leading/trailing whitespace
    text = text.strip()
    
    return text


def validate_inputs(reference_text, predicted_text):
    """
    Validate input texts and handle edge cases.
    
    Args:
        reference_text (str): Ground truth transcript
        predicted_text (str): Model-generated transcript
        
    Returns:
        tuple: (is_valid, error_message)
        
    Raises:
        ValueError: If inputs are invalid
    """
    # Check if inputs are strings
    if not isinstance(reference_text, str):
        raise ValueError("reference_text must be a string")
    if not isinstance(predicted_text, str):
        raise ValueError("predicted_text must be a string")
    
    # Check if texts are empty
    if not reference_text.strip():
        raise ValueError("reference_text cannot be empty")
    if not predicted_text.strip():
        raise ValueError("predicted_text cannot be empty")
    
    return True


def calculate_wer_accuracy(reference_text, predicted_text, return_details=False):
    """
    Calculate Word Error Rate (WER) and accuracy percentage for speech-to-text output.
    
    WER is the standard metric for speech recognition evaluation:
    - WER = (S + D + I) / N * 100
      where S=substitutions, D=deletions, I=insertions, N=reference word count
    - Accuracy = (1 - WER) * 100
    
    Args:
        reference_text (str): Ground truth transcript (human-verified)
        predicted_text (str): Model-generated transcript
        return_details (bool): If True, return additional metrics (WER, CER, word counts)
        
    Returns:
        dict: Contains:
            - 'wer': Word Error Rate (as decimal, 0-1 range)
            - 'wer_percentage': WER as percentage (0-100%)
            - 'accuracy': Accuracy percentage (0-100%)
            - 'cer': Character Error Rate (if return_details=True)
            - 'reference_words': Number of words in reference (if return_details=True)
            - 'predicted_words': Number of words in predicted (if return_details=True)
            
    Example:
        >>> reference = "the quick brown fox"
        >>> predicted = "the quick brown dog"
        >>> result = calculate_wer_accuracy(reference, predicted)
        >>> print(f"WER: {result['wer_percentage']:.2f}%")
        >>> print(f"Accuracy: {result['accuracy']:.2f}%")
    """
    # Validate inputs
    try:
        validate_inputs(reference_text, predicted_text)
    except ValueError as e:
        print(f"Error: {e}")
        return None
    
    # Normalize both texts
    ref_normalized = normalize_text(reference_text)
    pred_normalized = normalize_text(predicted_text)
    
    # Handle edge case: if both are empty after normalization
    if not ref_normalized or not pred_normalized:
        return {
            'wer': 1.0,
            'wer_percentage': 100.0,
            'accuracy': 0.0,
            'cer': 1.0,
            'reference_words': 0,
            'predicted_words': 0,
            'warning': 'Text became empty after normalization'
        }
    
    # Calculate Word Error Rate using jiwer library
    wer_value = wer(ref_normalized, pred_normalized)
    
    # Calculate Character Error Rate for additional insight
    cer_value = cer(ref_normalized, pred_normalized)
    
    # Convert WER to percentage (jiwer returns values 0-1 for perfect/worst cases)
    wer_percentage = wer_value * 100
    
    # Calculate accuracy as inverse of WER, clamped to 0
    # Logic: Accuracy = max(0, 1 - WER)
    accuracy = max(0.0, (1 - wer_value) * 100)
    
    # Calculate Similarity Score (0-100%) using SequenceMatcher
    # This is often more intuitive for users than WER-based accuracy
    from difflib import SequenceMatcher
    similarity_ratio = SequenceMatcher(None, ref_normalized, pred_normalized).ratio()
    similarity_score = similarity_ratio * 100
    
    # Count words for reference
    ref_word_count = len(ref_normalized.split())
    pred_word_count = len(pred_normalized.split())
    
    # Build result dictionary
    result = {
        'wer': wer_value,
        'wer_percentage': round(wer_percentage, 2),
        'accuracy': round(accuracy, 2),
        'similarity_score': round(similarity_score, 2),  # New metric
        'cer': round(cer_value, 4) if return_details else None,
        'reference_words': ref_word_count if return_details else None,
        'predicted_words': pred_word_count if return_details else None,
    }
    
    # Remove None values if not needed
    if not return_details:
        result = {k: v for k, v in result.items() if v is not None}
    
    return result


def print_accuracy_report(reference_text, predicted_text):
    """
    Print a formatted accuracy report comparing reference and predicted text.
    
    Args:
        reference_text (str): Ground truth transcript
        predicted_text (str): Model-generated transcript
    """
    result = calculate_wer_accuracy(reference_text, predicted_text, return_details=True)
    
    if result is None:
        return
    
    print("\n" + "="*60)
    print("SPEECH-TO-TEXT ACCURACY EVALUATION REPORT")
    print("="*60)
    print(f"\nReference Text:     {reference_text[:80]}...")
    print(f"Predicted Text:     {predicted_text[:80]}...")
    print("\n" + "-"*60)
    print(f"Word Error Rate (WER):      {result['wer_percentage']:.2f}%")
    print(f"Character Error Rate (CER): {result['cer']*100:.2f}%")
    print(f"\nSimilarity Score:           {result['similarity_score']:.2f}%  <-- User-friendly match %")
    print(f"WER-based Accuracy:         {result['accuracy']:.2f}%")
    print(f"Reference Word Count:       {result['reference_words']} words")
    print(f"Predicted Word Count:       {result['predicted_words']} words")
    print("\n" + "="*60)
    
    # Quality assessment based on Similarity Score (more intuitive)
    accuracy = result['similarity_score']
    if accuracy >= 95:
        quality = "EXCELLENT"
    elif accuracy >= 85:
        quality = "VERY GOOD"
    elif accuracy >= 75:
        quality = "GOOD"
    elif accuracy >= 60:
        quality = "FAIR"
    else:
        quality = "POOR"
    
    print(f"Quality Assessment:         {quality}")
    print("="*60 + "\n")


# Example usage and testing
if __name__ == "__main__":
    # Test Case 1: Perfect match
    ref1 = "the quick brown fox jumps over the lazy dog"
    pred1 = "the quick brown fox jumps over the lazy dog"
    
    print("\n### Test Case 1: Perfect Match ###")
    result1 = calculate_wer_accuracy(ref1, pred1, return_details=True)
    print(f"Result: {result1}")
    
    # Test Case 2: Minor differences
    ref2 = "the quick brown fox jumps"
    pred2 = "the quick brown dog jumps"
    
    print("\n### Test Case 2: One Word Substitution ###")
    result2 = calculate_wer_accuracy(ref2, pred2, return_details=True)
    print(f"Result: {result2}")
    
    # Test Case 3: Completely different
    ref3 = "hello world"
    pred3 = "goodbye moon"
    
    print("\n### Test Case 3: Mostly Different ###")
    result3 = calculate_wer_accuracy(ref3, pred3, return_details=True)
    print(f"Result: {result3}")
    
    # Test Case 4: With punctuation and formatting
    ref4 = "Hello, world! How are you?"
    pred4 = "hello world how are you"
    
    print("\n### Test Case 4: With Punctuation ###")
    result4 = calculate_wer_accuracy(ref4, pred4, return_details=True)
    print(f"Result: {result4}")
    
    # Print formatted report
    print("\n### Formatted Report Example ###")
    print_accuracy_report(ref2, pred2)
