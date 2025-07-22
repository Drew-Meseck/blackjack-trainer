"""Game rules configuration for blackjack simulation."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class GameRules:
    """Configuration for blackjack game rules."""
    
    # Dealer behavior
    dealer_hits_soft_17: bool = True
    
    # Player options
    double_after_split: bool = True
    surrender_allowed: bool = False
    
    # Deck configuration
    num_decks: int = 6
    penetration: float = 0.75  # 75% penetration before reshuffle
    
    # Betting rules
    blackjack_payout: float = 1.5  # 3:2 payout
    
    def __post_init__(self):
        """Validate game rules after initialization."""
        if self.num_decks not in [1, 2, 4, 6, 8]:
            raise ValueError("Number of decks must be 1, 2, 4, 6, or 8")
        
        if not 0.1 <= self.penetration <= 0.9:
            raise ValueError("Penetration must be between 0.1 and 0.9")
        
        if self.blackjack_payout <= 0:
            raise ValueError("Blackjack payout must be positive")
    
    def total_cards(self) -> int:
        """Get total number of cards in the shoe."""
        return self.num_decks * 52
    
    def penetration_cards(self) -> int:
        """Get number of cards to deal before reshuffling."""
        return int(self.total_cards() * self.penetration)