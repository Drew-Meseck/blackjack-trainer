"""Blackjack game with integrated card counting capabilities."""

from typing import Tuple, Optional, List, Callable
from src.models import Card, Hand, GameRules, GameResult
from src.models.action import Action
from src.counting import CountingSystem, CardCounter, CountingSystemManager
from .blackjack_game import BlackjackGame


class CountingBlackjackGame(BlackjackGame):
    """Blackjack game with integrated card counting functionality."""
    
    def __init__(self, rules: GameRules, counting_system: Optional[CountingSystem] = None):
        """Initialize a counting-enabled blackjack game.
        
        Args:
            rules: The game rules configuration
            counting_system: The counting system to use (defaults to Hi-Lo)
        """
        super().__init__(rules)
        
        # Set up counting system
        if counting_system is None:
            manager = CountingSystemManager()
            counting_system = manager.get_default_system()
        
        self.counting_system = counting_system
        self.card_counter = CardCounter(counting_system, rules.num_decks)
        
        # Event callbacks for card reveals
        self._card_reveal_callbacks: List[Callable[[Card], None]] = []
        self._shuffle_callbacks: List[Callable[[], None]] = []
    
    def add_card_reveal_callback(self, callback: Callable[[Card], None]) -> None:
        """Add a callback to be called when a card is revealed.
        
        Args:
            callback: Function to call when a card is revealed
        """
        self._card_reveal_callbacks.append(callback)
    
    def add_shuffle_callback(self, callback: Callable[[], None]) -> None:
        """Add a callback to be called when the shoe is shuffled.
        
        Args:
            callback: Function to call when the shoe is shuffled
        """
        self._shuffle_callbacks.append(callback)
    
    def _notify_card_revealed(self, card: Card) -> None:
        """Notify that a card has been revealed and update count.
        
        Args:
            card: The card that was revealed
        """
        # Update the card counter
        self.card_counter.update_count(card)
        
        # Notify any registered callbacks
        for callback in self._card_reveal_callbacks:
            callback(card)
    
    def _notify_shuffle(self) -> None:
        """Notify that the shoe has been shuffled and reset count."""
        # Reset the card counter
        self.card_counter.reset()
        
        # Notify any registered callbacks
        for callback in self._shuffle_callbacks:
            callback()
    
    def deal_initial_cards(self) -> Tuple[Hand, Hand]:
        """Deal initial cards and update count for revealed cards.
        
        Returns:
            Tuple of (player_hand, dealer_hand)
        """
        # Check if shoe needs shuffling before dealing
        if self.shoe.needs_shuffle():
            self.shoe.shuffle()
            self._notify_shuffle()
        
        # Deal cards using parent method
        player_hand, dealer_hand = super().deal_initial_cards()
        
        # Update count for revealed cards
        # Player cards are always revealed
        for card in player_hand.cards:
            self._notify_card_revealed(card)
        
        # Only the first dealer card is revealed initially
        if dealer_hand.card_count() > 0:
            self._notify_card_revealed(dealer_hand.cards[0])
        
        return player_hand, dealer_hand
    
    def player_hit(self) -> Card:
        """Deal a card to player and update count.
        
        Returns:
            The card that was dealt
        """
        card = super().player_hit()
        self._notify_card_revealed(card)
        return card
    
    def player_double(self) -> Card:
        """Player doubles and update count for the dealt card.
        
        Returns:
            The card that was dealt
        """
        card = super().player_double()
        self._notify_card_revealed(card)
        
        # If game is over, reveal dealer's hole card and any additional cards
        if self.game_over and not self.player_hand.is_bust():
            self._reveal_dealer_cards()
        
        return card
    
    def player_stand(self) -> None:
        """Player stands and reveal dealer cards with count updates."""
        super().player_stand()
        
        # Reveal dealer's hole card and any additional cards
        if self.game_over:
            self._reveal_dealer_cards()
    
    def player_surrender(self) -> None:
        """Player surrenders - no additional cards revealed."""
        super().player_surrender()
        # No additional cards to reveal on surrender
    
    def _reveal_dealer_cards(self) -> None:
        """Reveal dealer's hole card and any cards dealt during dealer play."""
        # Reveal the hole card (second card) if not already revealed
        if self.dealer_hand.card_count() >= 2:
            hole_card = self.dealer_hand.cards[1]
            self._notify_card_revealed(hole_card)
        
        # Reveal any additional cards dealt during dealer play
        # (cards beyond the initial two)
        for i in range(2, self.dealer_hand.card_count()):
            card = self.dealer_hand.cards[i]
            self._notify_card_revealed(card)
    
    def reset(self) -> None:
        """Reset the game and handle shuffling if needed."""
        super().reset()
        
        # If shoe was shuffled during reset, notify
        if self.shoe.cards_dealt_count() == 0:
            self._notify_shuffle()
    
    def get_running_count(self) -> int:
        """Get the current running count.
        
        Returns:
            The current running count
        """
        return self.card_counter.running_count()
    
    def get_true_count(self) -> float:
        """Get the current true count.
        
        Returns:
            The current true count
        """
        return self.card_counter.true_count()
    
    def get_cards_seen(self) -> int:
        """Get the number of cards seen since last shuffle.
        
        Returns:
            Number of cards seen
        """
        return self.card_counter.cards_seen()
    
    def get_remaining_decks(self) -> float:
        """Get the estimated number of remaining decks.
        
        Returns:
            Estimated remaining decks
        """
        return self.card_counter.remaining_decks()
    
    def get_counting_system_name(self) -> str:
        """Get the name of the current counting system.
        
        Returns:
            Name of the counting system
        """
        return self.counting_system.name()
    
    def switch_counting_system(self, new_system: CountingSystem) -> None:
        """Switch to a different counting system.
        
        Args:
            new_system: The new counting system to use
            
        Note:
            This will reset the count as different systems have different values
        """
        self.counting_system = new_system
        self.card_counter = CardCounter(new_system, self.rules.num_decks)
        
        # Note: We don't re-count seen cards as that would require storing
        # all seen cards, which is memory intensive. The count starts fresh.
    
    def get_count_info(self) -> dict:
        """Get comprehensive counting information.
        
        Returns:
            Dictionary with counting statistics
        """
        return {
            'system': self.counting_system.name(),
            'running_count': self.card_counter.running_count(),
            'true_count': self.card_counter.true_count(),
            'cards_seen': self.card_counter.cards_seen(),
            'remaining_decks': self.card_counter.remaining_decks(),
            'penetration': self.shoe.cards_dealt_count() / self.shoe.total_cards
        }
    
    def __str__(self) -> str:
        """String representation including count information."""
        base_str = super().__str__()
        
        if self.card_counter.cards_seen() > 0:
            count_str = (f"\nCount: RC={self.card_counter.running_count()}, "
                        f"TC={self.card_counter.true_count():.1f} "
                        f"({self.counting_system.name()})")
            return base_str + count_str
        
        return base_str