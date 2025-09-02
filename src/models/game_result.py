"""Game result model for blackjack outcomes."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class Outcome(Enum):
    """Possible game outcomes."""
    WIN = "win"
    LOSS = "loss"
    PUSH = "push"
    BLACKJACK = "blackjack"
    SURRENDER = "surrender"


@dataclass
class GameResult:
    """Represents the result of a blackjack hand."""
    
    # Game outcome
    outcome: Outcome
    
    # Final totals
    player_total: int
    dealer_total: Optional[int] = None  # None for surrender
    
    # Financial result
    payout: float = 0.0  # Multiplier of bet (1.0 = even money, 1.5 = 3:2, -1.0 = loss)
    
    # Additional context
    player_busted: bool = False
    dealer_busted: bool = False
    player_blackjack: bool = False
    dealer_blackjack: bool = False
    
    def __post_init__(self):
        """Validate and set derived properties."""
        # Set bust flags based on totals
        if self.player_total > 21:
            self.player_busted = True
        
        if self.dealer_total is not None and self.dealer_total > 21:
            self.dealer_busted = True
        
        # Set blackjack flags
        if self.outcome == Outcome.BLACKJACK:
            self.player_blackjack = True
        
        # Validate payout based on outcome
        if self.outcome == Outcome.LOSS and self.payout >= 0:
            self.payout = -1.0
        elif self.outcome == Outcome.WIN and self.payout <= 0:
            self.payout = 1.0
        elif self.outcome == Outcome.BLACKJACK and self.payout <= 1.0:
            self.payout = 1.5
        elif self.outcome == Outcome.PUSH and self.payout != 0:
            self.payout = 0.0
        elif self.outcome == Outcome.SURRENDER and self.payout != -0.5:
            self.payout = -0.5
    
    def is_winning_result(self) -> bool:
        """Check if this is a winning result for the player."""
        return self.outcome in [Outcome.WIN, Outcome.BLACKJACK]
    
    def is_losing_result(self) -> bool:
        """Check if this is a losing result for the player."""
        return self.outcome in [Outcome.LOSS, Outcome.SURRENDER]
    
    def net_result(self, bet_amount: float = 1.0) -> float:
        """Calculate the net monetary result."""
        return self.payout * bet_amount
    
    def __str__(self) -> str:
        """String representation of the game result."""
        if self.dealer_total is not None:
            return f"{self.outcome.value.title()}: Player {self.player_total} vs Dealer {self.dealer_total} (Payout: {self.payout:+.1f})"
        else:
            return f"{self.outcome.value.title()}: Player {self.player_total} (Payout: {self.payout:+.1f})"