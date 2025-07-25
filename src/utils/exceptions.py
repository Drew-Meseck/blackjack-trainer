"""
Custom exception hierarchy for the blackjack simulator.

This module defines all custom exceptions used throughout the simulator
to provide clear error handling and user feedback.
"""


class BlackjackSimulatorError(Exception):
    """Base exception for all simulator errors."""
    
    def __init__(self, message: str, details: str = None):
        super().__init__(message)
        self.message = message
        self.details = details
    
    def __str__(self):
        if self.details:
            return f"{self.message}: {self.details}"
        return self.message


class InvalidGameStateError(BlackjackSimulatorError):
    """Raised when game is in invalid state for requested action."""
    pass


class InvalidConfigurationError(BlackjackSimulatorError):
    """Raised when game rules or settings are invalid."""
    pass


class SessionNotFoundError(BlackjackSimulatorError):
    """Raised when requested session cannot be found."""
    pass


class SessionCorruptedError(BlackjackSimulatorError):
    """Raised when session data is corrupted or invalid."""
    pass


class CountingSystemError(BlackjackSimulatorError):
    """Raised when counting system encounters an error."""
    pass


class InvalidInputError(BlackjackSimulatorError):
    """Raised when user provides invalid input."""
    pass


class GameLogicError(BlackjackSimulatorError):
    """Raised when game logic encounters an unexpected state."""
    pass


class ValidationError(BlackjackSimulatorError):
    """Raised when data validation fails."""
    pass


class StrategyError(BlackjackSimulatorError):
    """Raised when strategy engine encounters an error."""
    pass


class AnalyticsError(BlackjackSimulatorError):
    """Raised when analytics calculations fail."""
    pass