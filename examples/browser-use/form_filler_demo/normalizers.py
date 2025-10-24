"""
Data Normalization Utilities for Smart Form Filler
Transforms raw input data into format-compliant values based on learned rules.

Author: Enterprise ML/AI Team
Version: 1.0.0
"""

import re
from datetime import datetime
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class DateNormalizer:
    """Normalize dates into various formats based on target mask hints."""

    @staticmethod
    def normalize(raw: str, target_mask_hint: str = "MM/DD/YYYY") -> str:
        """
        Normalize date from DD-MM-YYYY to target format.

        Args:
            raw: Raw date string (e.g., "12-08-1998")
            target_mask_hint: Target format (e.g., "MM/DD/YYYY", "YYYY-MM-DD", "DD/MM/YYYY")

        Returns:
            Normalized date string
        """
        try:
            # Split by common separators
            parts = re.split(r"[^\d]", raw)

            if len(parts) != 3:
                logger.warning(f"Could not parse date: {raw}")
                return raw

            # Assume input is DD-MM-YYYY (as per PRD)
            day, month, year = parts[0], parts[1], parts[2]

            # Ensure valid ranges
            if not (1 <= int(day) <= 31 and 1 <= int(month) <= 12):
                # Try alternative parsing (MM-DD-YYYY input)
                month, day, year = parts[0], parts[1], parts[2]

            # Normalize based on target hint
            hint_upper = target_mask_hint.upper()

            if "YYYY-MM-DD" in hint_upper or "ISO" in hint_upper:
                return f"{year}-{month.zfill(2)}-{day.zfill(2)}"

            elif "MM/DD/YYYY" in hint_upper or "MONTH/DAY/YEAR" in hint_upper or "M/D/Y" in hint_upper:
                return f"{month.zfill(2)}/{day.zfill(2)}/{year}"

            elif "DD/MM/YYYY" in hint_upper or "DAY/MONTH/YEAR" in hint_upper or "D/M/Y" in hint_upper:
                return f"{day.zfill(2)}/{month.zfill(2)}/{year}"

            elif "DD-MM-YYYY" in hint_upper:
                return f"{day.zfill(2)}-{month.zfill(2)}-{year}"

            elif "MM-DD-YYYY" in hint_upper:
                return f"{month.zfill(2)}-{day.zfill(2)}-{year}"

            else:
                # Fallback: try ISO format
                logger.info(f"Unknown date format hint '{target_mask_hint}', using ISO format")
                return f"{year}-{month.zfill(2)}-{day.zfill(2)}"

        except Exception as e:
            logger.error(f"Date normalization failed for '{raw}': {e}")
            return raw


class PhoneNormalizer:
    """Normalize phone numbers based on learned constraints."""

    @staticmethod
    def normalize(
        raw: str,
        min_digits: int = 9,
        max_digits: int = 11,
        allow_country_code: bool = True,
        default_country_code: str = "34",
        output_format: str = "digits_only"
    ) -> str:
        """
        Normalize phone number.

        Args:
            raw: Raw phone string (e.g., "+34 600-12-34-56")
            min_digits: Minimum required digits
            max_digits: Maximum allowed digits
            allow_country_code: Whether country code is allowed/required
            default_country_code: Default CC to add if missing
            output_format: "digits_only", "international", "dashed"

        Returns:
            Normalized phone string
        """
        try:
            # Extract only digits
            digits = re.sub(r"\D", "", raw)

            # Handle country code
            if allow_country_code:
                # If too short and doesn't start with CC, add it
                if len(digits) < min_digits and not digits.startswith(default_country_code):
                    digits = default_country_code + digits

            # Truncate if too long
            if max_digits and len(digits) > max_digits:
                digits = digits[:max_digits]

            # Apply output format
            if output_format == "digits_only":
                return digits

            elif output_format == "international" and len(digits) >= min_digits:
                # Format: +34 600123456
                if digits.startswith(default_country_code):
                    return f"+{digits[:2]} {digits[2:]}"
                return f"+{digits}"

            elif output_format == "dashed" and len(digits) >= 9:
                # Format: 600-12-34-56
                if digits.startswith(default_country_code):
                    main = digits[len(default_country_code):]
                else:
                    main = digits

                # Split into groups
                if len(main) == 9:
                    return f"{main[:3]}-{main[3:5]}-{main[5:7]}-{main[7:]}"
                return main

            else:
                return digits

        except Exception as e:
            logger.error(f"Phone normalization failed for '{raw}': {e}")
            return raw


class ZipNormalizer:
    """Normalize ZIP/postal codes."""

    @staticmethod
    def normalize(
        raw: str,
        length_hint: Optional[int] = None,
        digits_only: bool = True,
        uppercase: bool = True,
        allow_spaces: bool = False
    ) -> str:
        """
        Normalize ZIP/postal code.

        Args:
            raw: Raw ZIP string (e.g., "48001")
            length_hint: Expected length (e.g., 5 for US, 5 for ES)
            digits_only: Whether to strip non-digits
            uppercase: Whether to uppercase letters
            allow_spaces: Whether spaces are allowed

        Returns:
            Normalized ZIP string
        """
        try:
            s = raw.strip()

            # Remove spaces if not allowed
            if not allow_spaces:
                s = re.sub(r"\s", "", s)

            # Strip non-digits if required
            if digits_only:
                s = re.sub(r"\D", "", s)

            # Uppercase if required
            if uppercase:
                s = s.upper()

            # Truncate to length if specified
            if length_hint and len(s) > length_hint:
                s = s[:length_hint]

            # Pad with zeros if too short (for numeric codes)
            if length_hint and digits_only and len(s) < length_hint:
                s = s.zfill(length_hint)

            return s

        except Exception as e:
            logger.error(f"ZIP normalization failed for '{raw}': {e}")
            return raw


class FormNormalizer:
    """
    High-level form data normalizer that applies learned rules from ACE playbook.
    """

    def __init__(self, playbook_hints: Optional[Dict[str, Any]] = None):
        """
        Initialize with optional playbook hints.

        Args:
            playbook_hints: Dictionary of learned normalization rules
        """
        self.playbook_hints = playbook_hints or {}

    def normalize_all(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply all normalizations to payload.

        Args:
            payload: Raw form data

        Returns:
            Normalized form data with additional *_norm fields
        """
        normalized = payload.copy()

        # Date normalization
        if "ship_date_raw" in payload:
            date_hint = self.playbook_hints.get("date_format", "MM/DD/YYYY")
            normalized["ship_date_norm"] = DateNormalizer.normalize(
                payload["ship_date_raw"],
                date_hint
            )
            logger.info(f"Date: {payload['ship_date_raw']} → {normalized['ship_date_norm']} (hint: {date_hint})")

        # Phone normalization
        if "phone_raw" in payload:
            phone_config = self.playbook_hints.get("phone", {})
            normalized["phone_norm"] = PhoneNormalizer.normalize(
                payload["phone_raw"],
                min_digits=phone_config.get("min_digits", 9),
                max_digits=phone_config.get("max_digits", 11),
                allow_country_code=phone_config.get("allow_country_code", True),
                default_country_code=phone_config.get("default_country_code", "34"),
                output_format=phone_config.get("output_format", "digits_only")
            )
            logger.info(f"Phone: {payload['phone_raw']} → {normalized['phone_norm']}")

        # ZIP normalization
        if "zip_postal_raw" in payload:
            zip_config = self.playbook_hints.get("zip", {})
            normalized["zip_postal_norm"] = ZipNormalizer.normalize(
                payload["zip_postal_raw"],
                length_hint=zip_config.get("length", 5),
                digits_only=zip_config.get("digits_only", True),
                uppercase=zip_config.get("uppercase", True),
                allow_spaces=zip_config.get("allow_spaces", False)
            )
            logger.info(f"ZIP: {payload['zip_postal_raw']} → {normalized['zip_postal_norm']}")

        return normalized


# Convenience functions for standalone usage
def normalize_date(raw: str, target_mask_hint: str = "MM/DD/YYYY") -> str:
    """Normalize date - convenience wrapper."""
    return DateNormalizer.normalize(raw, target_mask_hint)


def normalize_phone(
    raw: str,
    min_digits: int = 9,
    allow_cc: bool = True,
    default_cc: str = "34"
) -> str:
    """Normalize phone - convenience wrapper."""
    return PhoneNormalizer.normalize(
        raw,
        min_digits=min_digits,
        allow_country_code=allow_cc,
        default_country_code=default_cc,
        output_format="digits_only"
    )


def normalize_zip(
    raw: str,
    length_hint: int = 5,
    digits_only: bool = True
) -> str:
    """Normalize ZIP - convenience wrapper."""
    return ZipNormalizer.normalize(
        raw,
        length_hint=length_hint,
        digits_only=digits_only
    )


if __name__ == "__main__":
    # Test normalizations
    logging.basicConfig(level=logging.INFO)

    print("=== Date Normalization Tests ===")
    print(f"12-08-1998 → MM/DD/YYYY: {normalize_date('12-08-1998', 'MM/DD/YYYY')}")
    print(f"12-08-1998 → YYYY-MM-DD: {normalize_date('12-08-1998', 'YYYY-MM-DD')}")
    print(f"12-08-1998 → DD/MM/YYYY: {normalize_date('12-08-1998', 'DD/MM/YYYY')}")

    print("\n=== Phone Normalization Tests ===")
    print(f"+34 600-12-34-56 → digits: {normalize_phone('+34 600-12-34-56')}")
    print(f"600123456 → with CC: {normalize_phone('600123456', allow_cc=True, default_cc='34')}")

    print("\n=== ZIP Normalization Tests ===")
    print(f"48001 → 5 digits: {normalize_zip('48001', length_hint=5)}")
    print(f"48 → padded: {normalize_zip('48', length_hint=5)}")
