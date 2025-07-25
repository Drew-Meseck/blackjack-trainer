"""Game rules configuration for blackjack simulation."""

from dataclasses import dataclass
from typing import Optional
from ..utils.exceptions import InvalidConfigurationError
from ..utils.validation import validate_deck_count, validate_penetration, validate_blackjack_payout


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
        try:
            self.num_decks = validate_deck_count(self.num_decks)
            self.penetration = validate_penetration(self.penetration)
            self.blackjack_payout = validate_blackjack_payout(self.blackjack_payout)
        except Exception as e:
            raise InvalidConfigurationError(f"Invalid game rules: {e}")
    
    def total_cards(self) -> int:
        """Get total number of cards in the shoe."""
        return self.num_decks * 52
    
    def penetration_cards(self) -> int:
        """Get number of cards to deal before reshuffling."""
        return int(self.total_cards() * self.penetration)