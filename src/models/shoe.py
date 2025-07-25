"""Shoe model for multi-deck blackjack simulation."""

import random
from typing import List, Optional
from .card import Card, Suit, Rank
from ..utils.exceptions import InvalidConfigurationError, GameLogicError
from ..utils.validation import validate_deck_count, validate_penetration


class Shoe:
    """Represents a shoe containing multiple decks of cards for blackjack."""
    
    def __init__(self, num_decks: int = 6, penetration: float = 0.75, shuffle_on_init: bool = True):
        """Initialize a shoe with specified number of decks and penetration.
        
        Args:
            num_decks: Number of decks to include in the shoe (1, 2, 4, 6, or 8)
            penetration: Percentage of cards to deal before reshuffling (0.1 to 0.95)
            shuffle_on_init: Whether to shuffle the shoe on initialization
            
        Raises:
            InvalidConfigurationError: If num_decks or penetration are invalid
        """
        try:
            self.num_decks = validate_deck_count(num_decks)
            self.penetration = validate_penetration(penetration)
        except Exception as e:
            raise InvalidConfigurationError(f"Invalid shoe configuration: {e}")
        
        self.num_decks = num_decks
        self.penetration = penetration
        self.total_cards = num_decks * 52
        self.penetration_threshold = int(self.total_cards * penetration)
        
        # Initialize the shoe with all cards
        self.cards: List[Card] = []
        self._create_decks()
        
        if shuffle_on_init:
            self.shuffle()
        
        self.cards_dealt = 0
    
    def _create_decks(self) -> None:
        """Create all decks and add them to the shoe."""
        self.cards = []
        for _ in range(self.num_decks):
            for suit in Suit:
                for rank in Rank:
                    self.cards.append(Card(suit, rank))
    
    def shuffle(self) -> None:
        """Shuffle all cards in the shoe and reset dealt count."""
        random.shuffle(self.cards)
        self.cards_dealt = 0
    
    def deal_card(self) -> Card:
        """Deal one card from the shoe.
        
        Returns:
            The next card from the shoe
            
        Raises:
            GameLogicError: If the shoe is empty or needs shuffling
        """
        if self.needs_shuffle():
            raise GameLogicError("Shoe needs shuffling - penetration threshold reached")
        
        if not self.cards:
            raise GameLogicError("Shoe is empty - no cards to deal")
        
        card = self.cards.pop(0)
        self.cards_dealt += 1
        return card
    
    def cards_remaining(self) -> int:
        """Get the number of cards remaining in the shoe.
        
        Returns:
            Number of cards left in the shoe
        """
        return len(self.cards)
    
    def cards_dealt_count(self) -> int:
        """Get the number of cards dealt from the shoe.
        
        Returns:
            Number of cards dealt since last shuffle
        """
        return self.cards_dealt
    
    def needs_shuffle(self) -> bool:
        """Check if the shoe needs to be shuffled based on penetration.
        
        Returns:
            True if penetration threshold has been reached
        """
        return self.cards_dealt >= self.penetration_threshold
    
    def decks_remaining(self) -> float:
        """Calculate approximate number of decks remaining.
        
        Returns:
            Approximate number of decks remaining (for true count calculation)
        """
        return self.cards_remaining() / 52.0
    
    def reset(self) -> None:
        """Reset the shoe to initial state with all cards and shuffle."""
        self._create_decks()
        self.shuffle()
    
    def __len__(self) -> int:
        """Return the number of cards remaining in the shoe."""
        return len(self.cards)
    
    def __str__(self) -> str:
        """String representation of the shoe."""
        return f"Shoe({self.num_decks} decks, {self.cards_remaining()}/{self.total_cards} cards, {self.penetration:.1%} penetration)"
    
    def __repr__(self) -> str:
        """Detailed string representation of the shoe."""
        return f"Shoe(num_decks={self.num_decks}, penetration={self.penetration}, cards_remaining={self.cards_remaining()})"