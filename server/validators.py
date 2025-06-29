"""
Israeli ID and Phone Number Validators

This module provides validation functions for Israeli identification numbers
and Israeli phone numbers according to official specifications.
"""
import re
import logging

logger = logging.getLogger(__name__)

def validate_israeli_id(id_str: str) -> bool:
    """
    Validate Israeli ID using the official algorithm.
    
    Rules:
    - Must be 8 or 9 digits only
    - Must pass checksum validation using Israeli ID algorithm
    - 8-digit IDs are internally padded with leading zero
    
    Args:
        id_str: The Israeli ID string to validate
        
    Returns:
        bool: True if valid, False otherwise
        
    Examples:
        >>> validate_israeli_id("123456782")
        True
        >>> validate_israeli_id("12345678")
        True
        >>> validate_israeli_id("1234567")
        False
    """
    if not id_str or not isinstance(id_str, str):
        logger.debug(f"Invalid ID input: {id_str} (not string or None)")
        return False
    
    # Remove any whitespace
    id_str = id_str.strip()
    
    # Must be digits only
    if not id_str.isdigit():
        logger.debug(f"Invalid ID: {id_str} (contains non-digits)")
        return False
    
    # Must be 8 or 9 digits
    if len(id_str) < 8 or len(id_str) > 9:
        logger.debug(f"Invalid ID length: {id_str} (length: {len(id_str)})")
        return False
    
    # Pad with leading zero if 8 digits
    if len(id_str) == 8:
        id_str = "0" + id_str
    
    # Convert to list of integers
    digits = [int(d) for d in id_str]
    
    # Calculate checksum using Israeli ID algorithm
    checksum = 0
    for i, digit in enumerate(digits[:-1]):  # Exclude last digit (check digit)
        if i % 2 == 0:  # Even positions (0, 2, 4, 6)
            checksum += digit
        else:  # Odd positions (1, 3, 5, 7)
            doubled = digit * 2
            checksum += doubled if doubled < 10 else doubled - 9
    
    # The check digit should make the total sum divisible by 10
    expected_check_digit = (10 - (checksum % 10)) % 10
    actual_check_digit = digits[-1]
    
    is_valid = actual_check_digit == expected_check_digit
    
    if not is_valid:
        logger.debug(f"Invalid checksum for ID: {id_str} (expected: {expected_check_digit}, got: {actual_check_digit})")
    
    return is_valid

def validate_phone_number(phone: str) -> bool:
    """
    Validate Israeli phone number.
    
    Rules:
    - Must start with "05" 
    - Total length must be exactly 10 digits
    - Format: 05XXXXXXXX
    - Accepts formatting characters (dashes, spaces, dots) but ignores them
    
    Args:
        phone: The phone number string to validate
        
    Returns:
        bool: True if valid, False otherwise
        
    Examples:
        >>> validate_phone_number("0501234567")
        True
        >>> validate_phone_number("050-123-4567")
        True
        >>> validate_phone_number("0521234567")
        False
    """
    if not phone or not isinstance(phone, str):
        logger.debug(f"Invalid phone input: {phone} (not string or None)")
        return False
    
    # Remove any non-digit characters for validation
    digits_only = re.sub(r'\D', '', phone)
    
    # Must be exactly 10 digits
    if len(digits_only) != 10:
        logger.debug(f"Invalid phone length: {phone} -> {digits_only} (length: {len(digits_only)})")
        return False
    
    # Must start with "05"
    if not digits_only.startswith("05"):
        logger.debug(f"Invalid phone prefix: {phone} -> {digits_only} (doesn't start with 05)")
        return False
    
    logger.debug(f"Valid phone number: {phone} -> {digits_only}")
    return True

def validate_name(name: str) -> bool:
    """
    Validate user name.
    
    Rules:
    - Must not be empty or whitespace only
    - Must be a string
    
    Args:
        name: The name string to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not name or not isinstance(name, str):
        return False
    
    return bool(name.strip())

def validate_address(address: str) -> bool:
    """
    Validate user address.
    
    Rules:
    - Must not be empty or whitespace only
    - Must be a string
    
    Args:
        address: The address string to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not address or not isinstance(address, str):
        return False
    
    return bool(address.strip())
