"""Hi-Opt I card counting system implementation."""

from typing import TYPE_CHECKING
from .counting_system import CountingSystem

if TYPE_CHECKING:
    from src.models.card import Card, Rank


class HiOptISystem(CountingSystem):
    """Hi-Opt I card counting system.
    
    This is a balanced counting system:
    Low cards (3-6): +1
    Neutral cards (2, 7-9, A): 0
    High cards (10, J, Q, K): -1
    
    Note: Unlike Hi-Lo, Aces and 2s are neutral (0).
    """
    
    def card_value(self, card: 'Card') -> int:
        """Get the Hi-Opt I counting value for a card.
        
        Args:
            card: The card to get the counting value for
            
        Returns:
            +1 for low cards (3-6)
            0 for neutral cards (2, 7-9, A)
            -1 for high cards (10, J, Q, K)
        """
        from src.models.card import Rank
        
        # Low cards: +1
        if card.rank in [Rank.THREE, Rank.FOUR, Rank.FIVE, Rank.SIX]:
            return 1
        
        # Neutral cards: 0 (includes 2, 7-9, and A)
        elif card.rank in [Rank.TWO, Rank.SEVEN, Rank.EIGHT, Rank.NINE, Rank.ACE]:
            return 0
        
        # High cards: -1 (10, J, Q, K only - A is neutral)
        else:  # 10, J, Q, K
            return -1
    
    def name(self) -> str:
        """Get the name of the counting system.
        
        Returns:
            The name "Hi-Opt I"
        """
        return "Hi-Opt I"