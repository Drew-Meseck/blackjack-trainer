"""Card model for blackjack simulation."""

from enum import Enum
from typing import Union


class Suit(Enum):
    """Card suits."""
    HEARTS = "♥"
    DIAMONDS = "♦"
    CLUBS = "♣"
    SPADES = "♠"


class Rank(Enum):
    """Card ranks."""
    ACE = "A"
    TWO = "2"
    THREE = "3"
    FOUR = "4"
    FIVE = "5"
    SIX = "6"
    SEVEN = "7"
    EIGHT = "8"
    NINE = "9"
    TEN = "10"
    JACK = "J"
    QUEEN = "Q"
    KING = "K"


class Card:
    """Represents a playing card with blackjack-specific functionality."""
    
    def __init__(self, suit: Suit, rank: Rank):
        """Initialize a card with suit and rank.
        
        Args:
            suit: The card's suit
            rank: The card's rank
        """
        self.suit = suit
        self.rank = rank
    
    def value(self, ace_as_eleven: bool = True) -> int:
        """Get the blackjack value of the card.
        
        Args:
            ace_as_eleven: Whether to count Ace as 11 (True) or 1 (False)
            
        Returns:
            The blackjack value of the card
        """
        if self.rank == Rank.ACE:
            return 11 if ace_as_eleven else 1
        elif self.rank in [Rank.JACK, Rank.QUEEN, Rank.KING]:
            return 10
        else:
            return int(self.rank.value)
    
    def __str__(self) -> str:
        """String representation of the card."""
        return f"{self.rank.value}{self.suit.value}"
    
    def __repr__(self) -> str:
        """Detailed string representation of the card."""
        return f"Card({self.suit.name}, {self.rank.name})"
    
    def __eq__(self, other) -> bool:
        """Check equality with another card."""
        if not isinstance(other, Card):
            return False
        return self.suit == other.suit and self.rank == other.rank
    
    def __hash__(self) -> int:
        """Hash function for using cards in sets/dicts."""
        return hash((self.suit, self.rank))
    
    def count_value(self, system) -> int:
        """Get the card's value for a specific counting system.
        
        Args:
            system: The counting system to use
            
        Returns:
            The card's value in the specified counting system
        """
        # This will be implemented when counting systems are available
        # For now, return 0 as a placeholder
        if hasattr(system, 'card_value'):
            return system.card_value(self)
        return 0