"""Abstract base class for card counting systems."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.models.card import Card


class CountingSystem(ABC):
    """Abstract base class for card counting systems."""
    
    @abstractmethod
    def card_value(self, card: 'Card') -> int:
        """Get the counting value for a specific card.
        
        Args:
            card: The card to get the counting value for
            
        Returns:
            The counting value for the card (typically -1, 0, or +1)
        """
        pass
    
    @abstractmethod
    def name(self) -> str:
        """Get the name of the counting system.
        
        Returns:
            The name of the counting system
        """
        pass
    
    def __str__(self) -> str:
        """String representation of the counting system."""
        return self.name()