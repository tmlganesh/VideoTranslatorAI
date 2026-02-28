/**
 * Calculate similarity accuracy between two texts
 * Uses multiple algorithms for better accuracy measurement
 */

// Levenshtein Distance Algorithm
export const levenshteinDistance = (str1, str2) => {
  const len1 = str1.length;
  const len2 = str2.length;
  const matrix = Array(len2 + 1)
    .fill(null)
    .map(() => Array(len1 + 1).fill(0));

  for (let i = 0; i <= len1; i++) {
    matrix[0][i] = i;
  }
  for (let j = 0; j <= len2; j++) {
    matrix[j][0] = j;
  }

  for (let j = 1; j <= len2; j++) {
    for (let i = 1; i <= len1; i++) {
      const indicator = str1[i - 1] === str2[j - 1] ? 0 : 1;
      matrix[j][i] = Math.min(
        matrix[j][i - 1] + 1, // insertion
        matrix[j - 1][i] + 1, // deletion
        matrix[j - 1][i - 1] + indicator // substitution
      );
    }
  }

  return matrix[len2][len1];
};

// Normalize text for comparison
export const normalizeText = (text) => {
  return text
    .toLowerCase()
    .trim()
    .replace(/\s+/g, ' ')
    .replace(/[.,!?;:—\-()[\]{}'"]/g, '');
};

// Calculate Word Error Rate (WER) based accuracy (local fallback)
// WER = editDistance(words_predicted, words_reference) / words_reference
// Accuracy = (1 - WER) * 100
export const calculateWERAccuracy = (original, generated) => {
  const refWords = normalizeText(original).split(' ').filter(w => w);
  const hypWords = normalizeText(generated).split(' ').filter(w => w);

  const n = refWords.length;
  const m = hypWords.length;

  if (n === 0 && m === 0) {
    return { wer: 0, werPercentage: 0, accuracy: 100, refWords: 0, predWords: 0 };
  }
  if (n === 0) {
    // No reference words: cannot compute meaningful WER; treat as 0 accuracy
    return { wer: 1, werPercentage: 100, accuracy: 0, refWords: 0, predWords: m };
  }

  // DP edit distance over word tokens (insertions, deletions, substitutions)
  const dp = Array(n + 1)
    .fill(null)
    .map(() => Array(m + 1).fill(0));

  for (let i = 0; i <= n; i++) dp[i][0] = i; // deletions
  for (let j = 0; j <= m; j++) dp[0][j] = j; // insertions

  for (let i = 1; i <= n; i++) {
    for (let j = 1; j <= m; j++) {
      const cost = refWords[i - 1] === hypWords[j - 1] ? 0 : 1;
      dp[i][j] = Math.min(
        dp[i - 1][j] + 1,      // deletion
        dp[i][j - 1] + 1,      // insertion
        dp[i - 1][j - 1] + cost // substitution
      );
    }
  }

  const editDistance = dp[n][m];
  const wer = editDistance / n;
  const werPercentage = Math.min(100, Math.max(0, wer * 100));
  const accuracy = Math.max(0, Math.min(100, 100 - werPercentage));

  return {
    wer,
    werPercentage: Math.round(werPercentage * 100) / 100,
    accuracy: Math.round(accuracy * 100) / 100,
    refWords: n,
    predWords: m,
  };
};

// Calculate similarity percentage using Levenshtein distance
export const calculateLevenshteinSimilarity = (original, generated) => {
  const norm1 = normalizeText(original);
  const norm2 = normalizeText(generated);

  const distance = levenshteinDistance(norm1, norm2);
  const maxLength = Math.max(norm1.length, norm2.length);

  if (maxLength === 0) return 100;

  const similarity = ((maxLength - distance) / maxLength) * 100;
  return Math.round(similarity * 100) / 100;
};

// Word-level similarity
export const calculateWordSimilarity = (original, generated) => {
  const words1 = normalizeText(original).split(' ').filter(w => w);
  const words2 = normalizeText(generated).split(' ').filter(w => w);

  const set1 = new Set(words1);
  const set2 = new Set(words2);

  const intersection = new Set([...set1].filter(x => set2.has(x)));
  const union = new Set([...set1, ...set2]);

  if (union.size === 0) return 100;

  const jaccardSimilarity = (intersection.size / union.size) * 100;
  return Math.round(jaccardSimilarity * 100) / 100;
};

// Detailed accuracy report
export const generateAccuracyReport = (original, generated) => {
  // Calculate WER for additional metrics
  const werResult = calculateWERAccuracy(original, generated);
  
  // Calculate word counts
  const originalWordCount = normalizeText(original).split(' ').filter(w => w).length;
  const generatedWordCount = normalizeText(generated).split(' ').filter(w => w).length;
  const wordDifference = Math.abs(originalWordCount - generatedWordCount);
  
  // Primary accuracy: Use Levenshtein similarity to align with backend "Similarity Score"
  // This is more user-friendly than WER (which can be harsh on word order)
  const overallAccuracy = calculateLevenshteinSimilarity(original, generated);


  // Get accuracy quality assessment
  let qualityLevel = 'Poor';
  if (overallAccuracy >= 95) qualityLevel = 'Excellent';
  else if (overallAccuracy >= 85) qualityLevel = 'Very Good';
  else if (overallAccuracy >= 75) qualityLevel = 'Good';
  else if (overallAccuracy >= 60) qualityLevel = 'Fair';
  else qualityLevel = 'Poor';

  return {
    overallAccuracy,
    // Keep supplemental metrics for insight
    levenshteinScore: calculateLevenshteinSimilarity(original, generated),
    wordScore: calculateWordSimilarity(original, generated),
    qualityLevel,
    originalWordCount,
    generatedWordCount,
    wordDifference,
    metrics: {
      werPercentage: werResult.werPercentage,
      characterAccuracy: calculateLevenshteinSimilarity(original, generated),
      vocabularyAccuracy: calculateWordSimilarity(original, generated),
    }
  };
};

// Get quality color based on accuracy
export const getAccuracyColor = (accuracy) => {
  if (accuracy >= 95) return '#10b981'; // Excellent - Green
  if (accuracy >= 85) return '#3b82f6'; // Very Good - Blue
  if (accuracy >= 75) return '#f59e0b'; // Good - Amber
  if (accuracy >= 60) return '#f97316'; // Fair - Orange
  return '#ef4444'; // Poor - Red
};
