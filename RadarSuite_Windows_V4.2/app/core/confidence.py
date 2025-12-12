"""
RadarSuite v4.2.0 - Confidence Normalization Module
Normalizes confidence values to human-readable percentages (0-100%)

FIXED v4.2.0: Created to handle inconsistent confidence scales
- Logit scale (-inf to +inf) -> sigmoid -> 0-100%
- Probability scale (0-1) -> 0-100%
- Raw percentage scale (0-100) -> pass-through
"""

import numpy as np
from typing import Union


class ConfidenceNormalizer:
    """
    Normalizes confidence values from various scales to 0-100%

    Supports:
    - logit: Raw logit values (e.g., -4.09, -0.03, +2.5) -> sigmoid -> 0-100%
    - probability: Probability values (0.0 to 1.0) -> 0-100%
    - percentage: Already normalized (0-100) -> pass-through
    """

    @staticmethod
    def normalize(raw_value: float, scale: str = 'logit') -> float:
        """
        Normalize confidence value to 0-100% range

        Args:
            raw_value: Raw confidence value
            scale: Input scale type ('logit', 'probability', 'percentage')

        Returns:
            Normalized confidence as percentage (0-100)

        Examples:
            >>> ConfidenceNormalizer.normalize(-4.09, 'logit')
            1.64  # Very low confidence

            >>> ConfidenceNormalizer.normalize(-0.03, 'logit')
            49.25  # Near 50%

            >>> ConfidenceNormalizer.normalize(2.5, 'logit')
            92.41  # High confidence

            >>> ConfidenceNormalizer.normalize(0.75, 'probability')
            75.0
        """
        if scale == 'logit':
            # Convert logit to probability using sigmoid function
            # sigmoid(x) = 1 / (1 + exp(-x))
            probability = 1.0 / (1.0 + np.exp(-raw_value))
            return probability * 100.0

        elif scale == 'probability':
            # Already 0-1, just scale to percentage
            return np.clip(raw_value, 0.0, 1.0) * 100.0

        elif scale == 'percentage':
            # Already 0-100, just clip to valid range
            return np.clip(raw_value, 0.0, 100.0)

        else:
            raise ValueError(f"Unknown scale: {scale}. Use 'logit', 'probability', or 'percentage'")

    @staticmethod
    def to_probability(percentage: float) -> float:
        """
        Convert normalized percentage (0-100) back to probability (0-1)

        Args:
            percentage: Normalized confidence (0-100)

        Returns:
            Probability (0-1)
        """
        return np.clip(percentage / 100.0, 0.0, 1.0)

    @staticmethod
    def format_confidence(confidence: float, precision: int = 1) -> str:
        """
        Format confidence for display

        Args:
            confidence: Normalized confidence (0-100)
            precision: Decimal places (default 1)

        Returns:
            Formatted string (e.g., "75.5%")
        """
        return f"{confidence:.{precision}f}%"


# Convenience function for quick access
def normalize_confidence(raw_value: float, scale: str = 'logit') -> float:
    """
    Convenience function for normalizing confidence values

    Args:
        raw_value: Raw confidence value
        scale: Input scale type ('logit', 'probability', 'percentage')

    Returns:
        Normalized confidence as percentage (0-100)
    """
    return ConfidenceNormalizer.normalize(raw_value, scale)
