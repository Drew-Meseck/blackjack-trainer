"""Game situation model for blackjack decisions."""

from dataclasses import dataclass
from typing import List, Optional
from .card import Card


@dataclass
class GameSituation:
    """Represents a specific game situation for decision making."""
    
    # Player's hand
    player_cards: List[Card]
    
    # Dealer's up card
    dealer_up_card: Card
    
    # Available actions
    can_double: bool = False
    can_split: bool = False
    can_surrender: bool = False
    
    # Game context
    is_first_decision: bool = True
    hand_number: int = 1  # For tracking multiple hands after splits
    
    def player_total(self) -> int:
        """Calculate the best total for the player's hand."""
        total = 0
        aces = 0
        
        for card in self.player_cards:
            if card.rank.value == "A":
                aces += 1
                total += 11
            else:
                total += card.value(ace_as_eleven=False)
        
        # Adjust for aces
        while total > 21 and aces > 0:
            total -= 10
            aces -= 1
        
        return total
    
    def is_soft_hand(self) -> bool:
        """Check if the player's hand is soft (contains an ace counted as 11)."""
        total = 0
        aces = 0
        
        for card in self.player_cards:
            if card.rank.value == "A":
                aces += 1
                total += 11
            else:
                total += card.value(ace_as_eleven=False)
        
        # If we have aces and total <= 21, it's soft
        return aces > 0 and total <= 21
    
    def is_pair(self) -> bool:
        """Check if the player has a pair (for splitting)."""
        if len(self.player_cards) != 2:
            return False
        
        # Check if both cards have the same rank or same value
        card1, card2 = self.player_cards
        return (card1.rank == card2.rank or 
                card1.value(ace_as_eleven=False) == card2.value(ace_as_eleven=False))
    
    def is_blackjack(self) -> bool:
        """Check if the player has blackjack (21 with first two cards)."""
        return (len(self.player_cards) == 2 and 
                self.player_total() == 21 and 
                self.is_first_decision)
    
    def __str__(self) -> str:
        """String representation of the game situation."""
        cards_str = " ".join(str(card) for card in self.player_cards)
        return f"Player: {cards_str} ({self.player_total()}) vs Dealer: {self.dealer_up_card}"