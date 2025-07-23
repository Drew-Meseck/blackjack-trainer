"""KO (Knock-Out) card counting system implementation."""

from typing import TYPE_CHECKING
from .counting_system import CountingSystem

if TYPE_CHECKING:
    from src.models.card import Card, Rank


class KOSystem(CountingSystem):
    """KO (Knock-Out) card counting system.
    
    This is an unbalanced counting system:
    Low cards (2-7): +1
    Neutral cards (8-9): 0
    High cards (10, J, Q, K, A): -1
    
    Note: Unlike Hi-Lo, the 7 is counted as +1 instead of 0,
    making this an unbalanced system.
    """
    
    def card_value(self, card: 'Card') -> int:
        """Get the KO counting value for a card.
        
        Args:
            card: The card to get the counting value for
            
        Returns:
            +1 for low cards (2-7)
            0 for neutral cards (8-9)
            -1 for high cards (10, J, Q, K, A)
        """
        from src.models.card import Rank
        
        # Low cards: +1 (includes 7, unlike Hi-Lo)
        if card.rank in [Rank.TWO, Rank.THREE, Rank.FOUR, Rank.FIVE, Rank.SIX, Rank.SEVEN]:
            return 1
        
        # Neutral cards: 0
        elif card.rank in [Rank.EIGHT, Rank.NINE]:
            return 0
        
        # High cards: -1
        else:  # 10, J, Q, K, A
            return -1
    
    def name(self) -> str:
        """Get the name of the counting system.
        
        Returns:
            The name "KO"
        """
        return "KO"