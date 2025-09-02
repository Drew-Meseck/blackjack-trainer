"""
Unit tests for error handling and validation in the blackjack simulator.

This module tests the custom exception hierarchy, validation functions,
and error recovery mechanisms.
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch

from src.utils.exceptions import (
    BlackjackSimulatorError,
    InvalidGameStateError,
    InvalidConfigurationError,
    SessionNotFoundError,
    SessionCorruptedError,
    CountingSystemError,
    InvalidInputError,
    GameLogicError,
    ValidationError,
    StrategyError,
    AnalyticsError
)

from src.utils.validation import (
    validate_integer_input,
    validate_float_input,
    validate_choice_input,
    validate_menu_selection,
    validate_session_name,
    validate_deck_count,
    validate_penetration,
    validate_blackjack_payout,
    validate_count_estimate,
    validate_yes_no_input
)

from src.utils.error_recovery import (
    safe_execute,
    retry_operation,
    handle_user_input_error,
    format_error_for_user,
    ErrorRecoveryContext,
    validate_and_recover
)

from src.models.shoe import Shoe
from src.models.game_rules import GameRules


class TestCustomExceptions(unittest.TestCase):
    """Test the custom exception hierarchy."""
    
    def test_base_exception_with_message_only(self):
        """Test base exception with just a message."""
        error = BlackjackSimulatorError("Test error")
        self.assertEqual(str(error), "Test error")
        self.assertEqual(error.message, "Test error")
        self.assertIsNone(error.details)
    
    def test_base_exception_with_details(self):
        """Test base exception with message and details."""
        error = BlackjackSimulatorError("Test error", "Additional details")
        self.assertEqual(str(error), "Test error: Additional details")
        self.assertEqual(error.message, "Test error")
        self.assertEqual(error.details, "Additional details")
    
    def test_exception_inheritance(self):
        """Test that all custom exceptions inherit from base exception."""
        exceptions = [
            InvalidGameStateError,
            InvalidConfigurationError,
            SessionNotFoundError,
            SessionCorruptedError,
            CountingSystemError,
            InvalidInputError,
            GameLogicError,
            ValidationError,
            StrategyError,
            AnalyticsError
        ]
        
        for exc_class in exceptions:
            error = exc_class("Test message")
            self.assertIsInstance(error, BlackjackSimulatorError)
            self.assertEqual(str(error), "Test message")


class TestValidationFunctions(unittest.TestCase):
    """Test input validation functions."""
    
    def test_validate_integer_input_valid(self):
        """Test valid integer input validation."""
        self.assertEqual(validate_integer_input("42"), 42)
        self.assertEqual(validate_integer_input("  -10  "), -10)
        self.assertEqual(validate_integer_input("0"), 0)
    
    def test_validate_integer_input_with_bounds(self):
        """Test integer validation with min/max bounds."""
        self.assertEqual(validate_integer_input("5", 1, 10), 5)
        self.assertEqual(validate_integer_input("1", 1, 10), 1)
        self.assertEqual(validate_integer_input("10", 1, 10), 10)
    
    def test_validate_integer_input_invalid(self):
        """Test invalid integer input validation."""
        with self.assertRaises(InvalidInputError):
            validate_integer_input("")
        
        with self.assertRaises(InvalidInputError):
            validate_integer_input("not_a_number")
        
        with self.assertRaises(InvalidInputError):
            validate_integer_input("0", min_value=1)
        
        with self.assertRaises(InvalidInputError):
            validate_integer_input("15", max_value=10)
    
    def test_validate_float_input_valid(self):
        """Test valid float input validation."""
        self.assertEqual(validate_float_input("3.14"), 3.14)
        self.assertEqual(validate_float_input("  -2.5  "), -2.5)
        self.assertEqual(validate_float_input("42"), 42.0)
    
    def test_validate_float_input_invalid(self):
        """Test invalid float input validation."""
        with self.assertRaises(InvalidInputError):
            validate_float_input("")
        
        with self.assertRaises(InvalidInputError):
            validate_float_input("not_a_number")
        
        with self.assertRaises(InvalidInputError):
            validate_float_input("-1.0", min_value=0.0)
    
    def test_validate_choice_input_valid(self):
        """Test valid choice input validation."""
        choices = ["yes", "no", "maybe"]
        
        self.assertEqual(validate_choice_input("yes", choices), "yes")
        self.assertEqual(validate_choice_input("YES", choices, case_sensitive=False), "yes")
        self.assertEqual(validate_choice_input("  no  ", choices), "no")
    
    def test_validate_choice_input_invalid(self):
        """Test invalid choice input validation."""
        choices = ["yes", "no"]
        
        with self.assertRaises(InvalidInputError):
            validate_choice_input("", choices)
        
        with self.assertRaises(InvalidInputError):
            validate_choice_input("invalid", choices)
    
    def test_validate_deck_count_valid(self):
        """Test valid deck count validation."""
        for count in [1, 2, 4, 6, 8]:
            self.assertEqual(validate_deck_count(count), count)
    
    def test_validate_deck_count_invalid(self):
        """Test invalid deck count validation."""
        with self.assertRaises(ValidationError):
            validate_deck_count(3)
        
        with self.assertRaises(ValidationError):
            validate_deck_count(10)
    
    def test_validate_penetration_valid(self):
        """Test valid penetration validation."""
        self.assertEqual(validate_penetration(0.5), 0.5)
        self.assertEqual(validate_penetration(0.1), 0.1)
        self.assertEqual(validate_penetration(0.95), 0.95)
    
    def test_validate_penetration_invalid(self):
        """Test invalid penetration validation."""
        with self.assertRaises(ValidationError):
            validate_penetration(0.05)
        
        with self.assertRaises(ValidationError):
            validate_penetration(1.0)
    
    def test_validate_yes_no_input_valid(self):
        """Test valid yes/no input validation."""
        # Test yes variations
        for yes_input in ['y', 'yes', 'Y', 'YES', 'true', '1']:
            self.assertTrue(validate_yes_no_input(yes_input))
        
        # Test no variations
        for no_input in ['n', 'no', 'N', 'NO', 'false', '0']:
            self.assertFalse(validate_yes_no_input(no_input))
    
    def test_validate_yes_no_input_invalid(self):
        """Test invalid yes/no input validation."""
        with self.assertRaises(InvalidInputError):
            validate_yes_no_input("")
        
        with self.assertRaises(InvalidInputError):
            validate_yes_no_input("maybe")


class TestErrorRecovery(unittest.TestCase):
    """Test error recovery utilities."""
    
    def test_safe_execute_success(self):
        """Test safe_execute with successful function."""
        def success_func(x, y):
            return x + y
        
        result = safe_execute(success_func, 2, 3)
        self.assertEqual(result, 5)
    
    def test_safe_execute_with_error_default_return(self):
        """Test safe_execute with error and default return."""
        def error_func():
            raise ValueError("Test error")
        
        result = safe_execute(error_func, default_return="default")
        self.assertEqual(result, "default")
    
    def test_safe_execute_with_reraise(self):
        """Test safe_execute with reraise option."""
        def error_func():
            raise ValueError("Test error")
        
        with self.assertRaises(BlackjackSimulatorError):
            safe_execute(
                error_func, 
                reraise_as=BlackjackSimulatorError,
                error_message="Custom error"
            )
    
    def test_handle_user_input_error_with_simulator_error(self):
        """Test handle_user_input_error with simulator error."""
        error = InvalidInputError("Invalid input")
        result = handle_user_input_error(error)
        self.assertEqual(result, "❌ Invalid input")
    
    def test_handle_user_input_error_with_generic_error(self):
        """Test handle_user_input_error with generic error."""
        error = ValueError("Generic error")
        result = handle_user_input_error(error)
        self.assertEqual(result, "❌ Invalid input: Generic error")
    
    def test_format_error_for_user_with_simulator_error(self):
        """Test format_error_for_user with simulator error."""
        error = InvalidInputError("Invalid input")
        result = format_error_for_user(error)
        self.assertEqual(result, "❌ Invalid input")
    
    def test_error_recovery_context_no_error(self):
        """Test ErrorRecoveryContext with no error."""
        with ErrorRecoveryContext("test operation") as ctx:
            pass
        
        self.assertIsNone(ctx.error)
        self.assertEqual(ctx.get_user_message(), "")
    
    def test_error_recovery_context_with_error_no_reraise(self):
        """Test ErrorRecoveryContext with error and no reraise."""
        with ErrorRecoveryContext("test operation", reraise=False) as ctx:
            raise ValueError("Test error")
        
        self.assertIsNotNone(ctx.error)
        self.assertIn("Test error", ctx.get_user_message())
    
    def test_validate_and_recover_success(self):
        """Test validate_and_recover with successful validation."""
        def validate_positive(x):
            if x <= 0:
                raise ValueError("Must be positive")
            return x
        
        result = validate_and_recover(validate_positive, 5)
        self.assertEqual(result, 5)
    
    def test_validate_and_recover_with_recovery_value(self):
        """Test validate_and_recover with recovery value."""
        def validate_positive(x):
            if x <= 0:
                raise ValueError("Must be positive")
            return x
        
        result = validate_and_recover(validate_positive, -1, recovery_value=1)
        self.assertEqual(result, 1)


class TestModelErrorHandling(unittest.TestCase):
    """Test error handling in model classes."""
    
    def test_shoe_invalid_deck_count(self):
        """Test Shoe with invalid deck count."""
        with self.assertRaises(InvalidConfigurationError):
            Shoe(num_decks=3)
    
    def test_shoe_invalid_penetration(self):
        """Test Shoe with invalid penetration."""
        with self.assertRaises(InvalidConfigurationError):
            Shoe(penetration=1.5)
    
    def test_shoe_deal_card_when_needs_shuffle(self):
        """Test dealing card when shoe needs shuffle."""
        shoe = Shoe(num_decks=1, penetration=0.1)  # Very low penetration
        
        # Deal cards until penetration threshold
        while not shoe.needs_shuffle():
            shoe.deal_card()
        
        # Now trying to deal should raise error
        with self.assertRaises(GameLogicError):
            shoe.deal_card()
    
    def test_game_rules_invalid_deck_count(self):
        """Test GameRules with invalid deck count."""
        with self.assertRaises(InvalidConfigurationError):
            GameRules(num_decks=3)
    
    def test_game_rules_invalid_penetration(self):
        """Test GameRules with invalid penetration."""
        with self.assertRaises(InvalidConfigurationError):
            GameRules(penetration=1.5)
    
    def test_game_rules_invalid_payout(self):
        """Test GameRules with invalid payout."""
        with self.assertRaises(InvalidConfigurationError):
            GameRules(blackjack_payout=-1.0)


class TestSessionManagerErrorHandling(unittest.TestCase):
    """Test error handling in session manager."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.sessions_dir = Path(self.temp_dir) / "test_sessions"
    
    def tearDown(self):
        """Clean up test environment."""
        if hasattr(self, 'temp_dir'):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_session_not_found_error(self):
        """Test SessionNotFoundError when loading non-existent session."""
        from src.session.session_manager import SessionManager
        
        manager = SessionManager(str(self.sessions_dir))
        
        with self.assertRaises(SessionNotFoundError):
            manager.load_session("non-existent-id")


if __name__ == "__main__":
    unittest.main()