"""Utility functions and helper classes."""

from .exceptions import (
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

from .validation import (
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

from .error_recovery import (
    safe_execute,
    retry_operation,
    handle_user_input_error,
    format_error_for_user,
    log_error_with_context,
    ErrorRecoveryContext,
    validate_and_recover
)

__all__ = [
    # Exceptions
    'BlackjackSimulatorError',
    'InvalidGameStateError',
    'InvalidConfigurationError',
    'SessionNotFoundError',
    'SessionCorruptedError',
    'CountingSystemError',
    'InvalidInputError',
    'GameLogicError',
    'ValidationError',
    'StrategyError',
    'AnalyticsError',
    
    # Validation
    'validate_integer_input',
    'validate_float_input',
    'validate_choice_input',
    'validate_menu_selection',
    'validate_session_name',
    'validate_deck_count',
    'validate_penetration',
    'validate_blackjack_payout',
    'validate_count_estimate',
    'validate_yes_no_input',
    
    # Error Recovery
    'safe_execute',
    'retry_operation',
    'handle_user_input_error',
    'format_error_for_user',
    'log_error_with_context',
    'ErrorRecoveryContext',
    'validate_and_recover'
]