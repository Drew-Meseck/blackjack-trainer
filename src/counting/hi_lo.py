"""Hi-Lo card counting system implementation."""

from typing import TYPE_CHECKING
from .counting_system import CountingSystem

if TYPE_CHECKING:
    from src.models.card import Card, Rank


class HiLoSystem(CountingSystem):
    """Hi-Lo card counting system (+1, 0, -1).
    
    Low cards (2-6): +1
    Neutral cards (7-9): 0
    High cards (10, J, Q, K, A): -1
    """
    
    def card_value(self, card: 'Card') -> int:
        """Get the Hi-Lo counting value for a card.
        
        Args:
            card: The card to get the counting value for
            
        Returns:
            +1 for low cards (2-6)
            0 for neutral cards (7-9)
            -1 for high cards (10, J, Q, K, A)
        """
        from src.models.card import Rank
        
        # Low cards: +1
        if card.rank in [Rank.TWO, Rank.THREE, Rank.FOUR, Rank.FIVE, Rank.SIX]:
            return 1
        
        # Neutral cards: 0
        elif card.rank in [Rank.SEVEN, Rank.EIGHT, Rank.NINE]:
            return 0
        
        # High cards: -1
        else:  # 10, J, Q, K, A
            return -1
    
    def name(self) -> str:
        """Get the name of the counting system.
        
        Returns:
            The name "Hi-Lo"
        """
        return "Hi-Lo"