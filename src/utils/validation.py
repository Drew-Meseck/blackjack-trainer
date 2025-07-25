"""
Input validation utilities for the blackjack simulator.

This module provides validation functions for user inputs and system data
to ensure data integrity and provide clear error messages.
"""

import re
from typing import Any, List, Optional, Union
from .exceptions import InvalidInputError, ValidationError


def validate_integer_input(
    value: str, 
    min_value: Optional[int] = None, 
    max_value: Optional[int] = None,
    field_name: str = "value"
) -> int:
    """
    Validate and convert string input to integer.
    
    Args:
        value: String value to validate
        min_value: Minimum allowed value (inclusive)
        max_value: Maximum allowed value (inclusive)
        field_name: Name of the field for error messages
        
    Returns:
        Validated integer value
        
    Raises:
        InvalidInputError: If validation fails
    """
    if not value or not value.strip():
        raise InvalidInputError(f"{field_name} cannot be empty")
    
    try:
        int_value = int(value.strip())
    except ValueError:
        raise InvalidInputError(f"{field_name} must be a valid integer, got: '{value}'")
    
    if min_value is not None and int_value < min_value:
        raise InvalidInputError(f"{field_name} must be at least {min_value}, got: {int_value}")
    
    if max_value is not None and int_value > max_value:
        raise InvalidInputError(f"{field_name} must be at most {max_value}, got: {int_value}")
    
    return int_value


def validate_float_input(
    value: str, 
    min_value: Optional[float] = None, 
    max_value: Optional[float] = None,
    field_name: str = "value"
) -> float:
    """
    Validate and convert string input to float.
    
    Args:
        value: String value to validate
        min_value: Minimum allowed value (inclusive)
        max_value: Maximum allowed value (inclusive)
        field_name: Name of the field for error messages
        
    Returns:
        Validated float value
        
    Raises:
        InvalidInputError: If validation fails
    """
    if not value or not value.strip():
        raise InvalidInputError(f"{field_name} cannot be empty")
    
    try:
        float_value = float(value.strip())
    except ValueError:
        raise InvalidInputError(f"{field_name} must be a valid number, got: '{value}'")
    
    if min_value is not None and float_value < min_value:
        raise InvalidInputError(f"{field_name} must be at least {min_value}, got: {float_value}")
    
    if max_value is not None and float_value > max_value:
        raise InvalidInputError(f"{field_name} must be at most {max_value}, got: {float_value}")
    
    return float_value


def validate_choice_input(
    value: str, 
    valid_choices: List[str], 
    case_sensitive: bool = False,
    field_name: str = "choice"
) -> str:
    """
    Validate that input is one of the allowed choices.
    
    Args:
        value: String value to validate
        valid_choices: List of valid choices
        case_sensitive: Whether comparison should be case sensitive
        field_name: Name of the field for error messages
        
    Returns:
        Validated choice (in original case from valid_choices)
        
    Raises:
        InvalidInputError: If validation fails
    """
    if not value or not value.strip():
        raise InvalidInputError(f"{field_name} cannot be empty")
    
    value = value.strip()
    
    if case_sensitive:
        if value in valid_choices:
            return value
    else:
        for choice in valid_choices:
            if value.lower() == choice.lower():
                return choice
    
    choices_str = "', '".join(valid_choices)
    raise InvalidInputError(f"{field_name} must be one of: '{choices_str}', got: '{value}'")


def validate_menu_selection(
    value: str, 
    max_option: int, 
    min_option: int = 1,
    field_name: str = "selection"
) -> int:
    """
    Validate menu selection input.
    
    Args:
        value: String value to validate
        max_option: Maximum valid option number
        min_option: Minimum valid option number (default: 1)
        field_name: Name of the field for error messages
        
    Returns:
        Validated selection number
        
    Raises:
        InvalidInputError: If validation fails
    """
    return validate_integer_input(value, min_option, max_option, field_name)


def validate_session_name(name: str) -> str:
    """
    Validate session name input.
    
    Args:
        name: Session name to validate
        
    Returns:
        Validated session name
        
    Raises:
        InvalidInputError: If validation fails
    """
    if not name or not name.strip():
        raise InvalidInputError("Session name cannot be empty")
    
    name = name.strip()
    
    if len(name) > 100:
        raise InvalidInputError("Session name cannot be longer than 100 characters")
    
    # Check for invalid characters
    if re.search(r'[<>:"/\\|?*]', name):
        raise InvalidInputError("Session name contains invalid characters")
    
    return name


def validate_deck_count(num_decks: int) -> int:
    """
    Validate number of decks for blackjack game.
    
    Args:
        num_decks: Number of decks to validate
        
    Returns:
        Validated deck count
        
    Raises:
        ValidationError: If validation fails
    """
    valid_deck_counts = [1, 2, 4, 6, 8]
    if num_decks not in valid_deck_counts:
        raise ValidationError(
            f"Invalid number of decks: {num_decks}",
            f"Must be one of: {valid_deck_counts}"
        )
    return num_decks


def validate_penetration(penetration: float) -> float:
    """
    Validate deck penetration percentage.
    
    Args:
        penetration: Penetration value to validate (0.0 to 1.0)
        
    Returns:
        Validated penetration value
        
    Raises:
        ValidationError: If validation fails
    """
    if not 0.1 <= penetration <= 0.95:
        raise ValidationError(
            f"Invalid penetration: {penetration}",
            "Must be between 0.1 (10%) and 0.95 (95%)"
        )
    return penetration


def validate_blackjack_payout(payout: float) -> float:
    """
    Validate blackjack payout multiplier.
    
    Args:
        payout: Payout multiplier to validate
        
    Returns:
        Validated payout value
        
    Raises:
        ValidationError: If validation fails
    """
    if payout <= 0:
        raise ValidationError(
            f"Invalid blackjack payout: {payout}",
            "Payout must be positive"
        )
    return payout


def validate_count_estimate(estimate: str) -> int:
    """
    Validate user's count estimate input.
    
    Args:
        estimate: Count estimate string to validate
        
    Returns:
        Validated count estimate
        
    Raises:
        InvalidInputError: If validation fails
    """
    return validate_integer_input(estimate, -100, 100, "count estimate")


def validate_yes_no_input(value: str, field_name: str = "input") -> bool:
    """
    Validate yes/no input and convert to boolean.
    
    Args:
        value: String value to validate
        field_name: Name of the field for error messages
        
    Returns:
        Boolean value (True for yes, False for no)
        
    Raises:
        InvalidInputError: If validation fails
    """
    if not value or not value.strip():
        raise InvalidInputError(f"{field_name} cannot be empty")
    
    value = value.strip().lower()
    
    if value in ['y', 'yes', 'true', '1']:
        return True
    elif value in ['n', 'no', 'false', '0']:
        return False
    else:
        raise InvalidInputError(f"{field_name} must be yes/no (y/n), got: '{value}'")