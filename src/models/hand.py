"""Hand model for blackjack simulation."""

from typing import List, Optional
from .card import Card, Rank


class Hand:
    """Represents a blackjack hand with cards and game logic."""
    
    def __init__(self, cards: Optional[List[Card]] = None):
        """Initialize a hand with optional starting cards.
        
        Args:
            cards: Optional list of cards to start with
        """
        self.cards: List[Card] = cards.copy() if cards else []
    
    def add_card(self, card: Card) -> None:
        """Add a card to the hand.
        
        Args:
            card: The card to add to the hand
        """
        self.cards.append(card)
    
    def value(self) -> int:
        """Calculate the best possible value for the hand.
        
        Returns:
            The best blackjack value for the hand (not over 21 if possible)
        """
        total = 0
        aces = 0
        
        # Count all cards, treating aces as 11 initially
        for card in self.cards:
            if card.rank == Rank.ACE:
                aces += 1
                total += 11
            else:
                total += card.value(ace_as_eleven=False)
        
        # Adjust aces from 11 to 1 if needed to avoid busting
        while total > 21 and aces > 0:
            total -= 10
            aces -= 1
        
        return total
    
    def is_soft(self) -> bool:
        """Check if the hand is soft (contains an ace counted as 11).
        
        Returns:
            True if the hand contains an ace counted as 11, False otherwise
        """
        if not any(card.rank == Rank.ACE for card in self.cards):
            return False
        
        total = 0
        aces = 0
        
        # Count all cards, treating aces as 11 initially
        for card in self.cards:
            if card.rank == Rank.ACE:
                aces += 1
                total += 11
            else:
                total += card.value(ace_as_eleven=False)
        
        # Adjust aces from 11 to 1 if needed to avoid busting
        aces_as_eleven = aces
        while total > 21 and aces_as_eleven > 0:
            total -= 10
            aces_as_eleven -= 1
        
        # Hand is soft if at least one ace is still counted as 11
        return aces_as_eleven > 0
    
    def is_blackjack(self) -> bool:
        """Check if the hand is a blackjack (21 with exactly 2 cards).
        
        Returns:
            True if the hand is a blackjack, False otherwise
        """
        return len(self.cards) == 2 and self.value() == 21
    
    def is_bust(self) -> bool:
        """Check if the hand is busted (value over 21).
        
        Returns:
            True if the hand value is over 21, False otherwise
        """
        return self.value() > 21
    
    def can_split(self) -> bool:
        """Check if the hand can be split (exactly 2 cards of same rank or value).
        
        Returns:
            True if the hand can be split, False otherwise
        """
        if len(self.cards) != 2:
            return False
        
        card1, card2 = self.cards
        # Can split if same rank or same blackjack value
        return (card1.rank == card2.rank or 
                card1.value(ace_as_eleven=False) == card2.value(ace_as_eleven=False))
    
    def can_double(self) -> bool:
        """Check if the hand can be doubled (exactly 2 cards).
        
        Returns:
            True if the hand can be doubled, False otherwise
        """
        return len(self.cards) == 2
    
    def clear(self) -> None:
        """Clear all cards from the hand."""
        self.cards.clear()
    
    def card_count(self) -> int:
        """Get the number of cards in the hand.
        
        Returns:
            The number of cards in the hand
        """
        return len(self.cards)
    
    def get_cards(self) -> List[Card]:
        """Get a copy of the cards in the hand.
        
        Returns:
            A copy of the list of cards in the hand
        """
        return self.cards.copy()
    
    def __str__(self) -> str:
        """String representation of the hand."""
        if not self.cards:
            return "Empty hand"
        
        cards_str = " ".join(str(card) for card in self.cards)
        value = self.value()
        soft_indicator = " (soft)" if self.is_soft() and value != 21 else ""
        
        return f"{cards_str} = {value}{soft_indicator}"
    
    def __repr__(self) -> str:
        """Detailed string representation of the hand."""
        cards_str = [str(card) for card in self.cards]
        return f"Hand(cards={cards_str}, value={self.value()})"
    
    def __len__(self) -> int:
        """Return the number of cards in the hand."""
        return len(self.cards)
    
    def __eq__(self, other) -> bool:
        """Check equality with another hand."""
        if not isinstance(other, Hand):
            return False
        return self.cards == other.cards
    
    def __iter__(self):
        """Make the hand iterable over its cards."""
        return iter(self.cards)