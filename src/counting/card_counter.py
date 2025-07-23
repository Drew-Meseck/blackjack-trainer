"""Card counter implementation for tracking counts during gameplay."""

from typing import TYPE_CHECKING
from .counting_system import CountingSystem

if TYPE_CHECKING:
    from src.models.card import Card


class CardCounter:
    """Tracks running count and true count using a specified counting system."""
    
    def __init__(self, system: CountingSystem, num_decks: int):
        """Initialize the card counter.
        
        Args:
            system: The counting system to use
            num_decks: The number of decks in the shoe
        """
        self.system = system
        self.num_decks = num_decks
        self._running_count = 0
        self._cards_seen = 0
    
    def update_count(self, card: 'Card') -> None:
        """Update the running count with a new card.
        
        Args:
            card: The card that was revealed
        """
        self._running_count += self.system.card_value(card)
        self._cards_seen += 1
    
    def running_count(self) -> int:
        """Get the current running count.
        
        Returns:
            The current running count
        """
        return self._running_count
    
    def true_count(self) -> float:
        """Calculate the true count based on remaining decks.
        
        Returns:
            The true count (running count divided by remaining decks)
        """
        # Calculate remaining decks based on cards seen
        cards_per_deck = 52
        total_cards = self.num_decks * cards_per_deck
        remaining_cards = total_cards - self._cards_seen
        remaining_decks = remaining_cards / cards_per_deck
        
        # Avoid division by zero
        if remaining_decks <= 0:
            return 0.0
        
        return self._running_count / remaining_decks
    
    def reset(self) -> None:
        """Reset the count (typically called when shoe is shuffled)."""
        self._running_count = 0
        self._cards_seen = 0
    
    def cards_seen(self) -> int:
        """Get the number of cards seen since last reset.
        
        Returns:
            The number of cards seen
        """
        return self._cards_seen
    
    def remaining_decks(self) -> float:
        """Calculate the number of remaining decks.
        
        Returns:
            The estimated number of remaining decks
        """
        cards_per_deck = 52
        total_cards = self.num_decks * cards_per_deck
        remaining_cards = total_cards - self._cards_seen
        return remaining_cards / cards_per_deck
    
    def __str__(self) -> str:
        """String representation of the counter state."""
        return f"CardCounter({self.system.name()}: RC={self._running_count}, TC={self.true_count():.1f})"