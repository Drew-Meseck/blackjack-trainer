"""Core blackjack game implementation."""

from typing import Tuple, Optional, List
from src.models import Card, Hand, Shoe, GameRules, GameResult, Outcome
from src.models.action import Action


class BlackjackGame:
    """Core blackjack game with configurable rules."""
    
    def __init__(self, rules: GameRules):
        """Initialize a blackjack game with specified rules.
        
        Args:
            rules: The game rules configuration
        """
        self.rules = rules
        self.shoe = Shoe(num_decks=rules.num_decks, penetration=rules.penetration)
        self.player_hand = Hand()
        self.dealer_hand = Hand()
        self.game_over = False
        self.result: Optional[GameResult] = None
        
    def deal_initial_cards(self) -> Tuple[Hand, Hand]:
        """Deal initial two cards to player and dealer.
        
        Returns:
            Tuple of (player_hand, dealer_hand)
            
        Raises:
            RuntimeError: If shoe needs shuffling or game already started
        """
        if self.player_hand.card_count() > 0 or self.dealer_hand.card_count() > 0:
            raise RuntimeError("Game already started. Call reset() first.")
        
        if self.shoe.needs_shuffle():
            raise RuntimeError("Shoe needs shuffling before dealing.")
        
        # Deal two cards to player, two to dealer (alternating)
        self.player_hand.add_card(self.shoe.deal_card())
        self.dealer_hand.add_card(self.shoe.deal_card())
        self.player_hand.add_card(self.shoe.deal_card())
        self.dealer_hand.add_card(self.shoe.deal_card())
        
        # Check for immediate blackjacks
        if self.player_hand.is_blackjack() or self.dealer_hand.is_blackjack():
            self.game_over = True
            self.result = self._determine_winner()
        
        return self.player_hand, self.dealer_hand
    
    def player_hit(self) -> Card:
        """Deal one card to the player.
        
        Returns:
            The card that was dealt
            
        Raises:
            RuntimeError: If game is over or invalid state
        """
        if self.game_over:
            raise RuntimeError("Game is over. Cannot hit.")
        
        if self.player_hand.card_count() == 0:
            raise RuntimeError("Game not started. Call deal_initial_cards() first.")
        
        card = self.shoe.deal_card()
        self.player_hand.add_card(card)
        
        # Check if player busted
        if self.player_hand.is_bust():
            self.game_over = True
            self.result = GameResult(
                outcome=Outcome.LOSS,
                player_total=self.player_hand.value(),
                dealer_total=self.dealer_hand.value(),
                player_busted=True
            )
        
        return card
    
    def player_stand(self) -> None:
        """Player stands - complete dealer's hand and determine winner."""
        if self.game_over:
            raise RuntimeError("Game is over. Cannot stand.")
        
        if self.player_hand.card_count() == 0:
            raise RuntimeError("Game not started. Call deal_initial_cards() first.")
        
        # Complete dealer's hand
        self._dealer_play()
        
        # Determine winner
        self.game_over = True
        self.result = self._determine_winner()
    
    def player_double(self) -> Card:
        """Player doubles down - take exactly one more card and stand.
        
        Returns:
            The card that was dealt
            
        Raises:
            RuntimeError: If doubling is not allowed or invalid state
        """
        if self.game_over:
            raise RuntimeError("Game is over. Cannot double.")
        
        if not self.can_double():
            raise RuntimeError("Cannot double in current situation.")
        
        # Deal one card
        card = self.shoe.deal_card()
        self.player_hand.add_card(card)
        
        # Check if player busted
        if self.player_hand.is_bust():
            self.game_over = True
            self.result = GameResult(
                outcome=Outcome.LOSS,
                player_total=self.player_hand.value(),
                dealer_total=self.dealer_hand.value(),
                player_busted=True,
                payout=-2.0  # Double bet loss
            )
        else:
            # Complete dealer's hand
            self._dealer_play()
            self.game_over = True
            self.result = self._determine_winner()
            # Adjust payout for double bet
            if self.result.payout > 0:
                self.result.payout *= 2
            elif self.result.payout < 0:
                self.result.payout *= 2
        
        return card
    
    def player_surrender(self) -> None:
        """Player surrenders - lose half the bet.
        
        Raises:
            RuntimeError: If surrender is not allowed or invalid state
        """
        if self.game_over:
            raise RuntimeError("Game is over. Cannot surrender.")
        
        if not self.can_surrender():
            raise RuntimeError("Cannot surrender in current situation.")
        
        self.game_over = True
        self.result = GameResult(
            outcome=Outcome.SURRENDER,
            player_total=self.player_hand.value(),
            dealer_total=None,  # Dealer hand not revealed
            payout=-0.5
        )
    
    def can_double(self) -> bool:
        """Check if player can double down.
        
        Returns:
            True if doubling is allowed, False otherwise
        """
        return (not self.game_over and 
                self.player_hand.can_double() and
                not self.player_hand.is_blackjack())
    
    def can_split(self) -> bool:
        """Check if player can split their hand.
        
        Returns:
            True if splitting is allowed, False otherwise
        """
        return (not self.game_over and 
                self.player_hand.can_split() and
                not self.player_hand.is_blackjack())
    
    def can_surrender(self) -> bool:
        """Check if player can surrender.
        
        Returns:
            True if surrender is allowed, False otherwise
        """
        return (not self.game_over and
                self.rules.surrender_allowed and
                self.player_hand.card_count() == 2 and
                not self.player_hand.is_blackjack())
    
    def get_available_actions(self) -> List[Action]:
        """Get list of available actions for the player.
        
        Returns:
            List of available actions
        """
        if self.game_over or self.player_hand.card_count() == 0:
            return []
        
        actions = [Action.HIT, Action.STAND]
        
        if self.can_double():
            actions.append(Action.DOUBLE)
        
        if self.can_split():
            actions.append(Action.SPLIT)
        
        if self.can_surrender():
            actions.append(Action.SURRENDER)
        
        return actions
    
    def is_game_over(self) -> bool:
        """Check if the game is over.
        
        Returns:
            True if game is over, False otherwise
        """
        return self.game_over
    
    def get_result(self) -> Optional[GameResult]:
        """Get the game result if game is over.
        
        Returns:
            GameResult if game is over, None otherwise
        """
        return self.result if self.game_over else None
    
    def reset(self) -> None:
        """Reset the game for a new hand."""
        self.player_hand.clear()
        self.dealer_hand.clear()
        self.game_over = False
        self.result = None
        
        # Shuffle shoe if needed
        if self.shoe.needs_shuffle():
            self.shoe.shuffle()
    
    def _dealer_play(self) -> None:
        """Complete the dealer's hand according to rules."""
        # Dealer plays only if player didn't bust
        if self.player_hand.is_bust():
            return
        
        # Dealer hits until reaching 17 or busting
        while True:
            dealer_value = self.dealer_hand.value()
            
            # Stand on hard 17 or higher
            if dealer_value >= 17:
                # Check soft 17 rule
                if dealer_value == 17 and self.dealer_hand.is_soft() and self.rules.dealer_hits_soft_17:
                    # Hit on soft 17
                    self.dealer_hand.add_card(self.shoe.deal_card())
                else:
                    # Stand
                    break
            else:
                # Hit on 16 or less
                self.dealer_hand.add_card(self.shoe.deal_card())
    
    def _determine_winner(self) -> GameResult:
        """Determine the winner and create game result.
        
        Returns:
            GameResult with outcome and payout
        """
        player_value = self.player_hand.value()
        dealer_value = self.dealer_hand.value()
        player_blackjack = self.player_hand.is_blackjack()
        dealer_blackjack = self.dealer_hand.is_blackjack()
        player_busted = self.player_hand.is_bust()
        dealer_busted = self.dealer_hand.is_bust()
        
        # Player busted - dealer wins
        if player_busted:
            return GameResult(
                outcome=Outcome.LOSS,
                player_total=player_value,
                dealer_total=dealer_value,
                player_busted=True,
                payout=-1.0
            )
        
        # Dealer busted - player wins
        if dealer_busted:
            return GameResult(
                outcome=Outcome.WIN,
                player_total=player_value,
                dealer_total=dealer_value,
                dealer_busted=True,
                payout=1.0
            )
        
        # Both have blackjack - push
        if player_blackjack and dealer_blackjack:
            return GameResult(
                outcome=Outcome.PUSH,
                player_total=player_value,
                dealer_total=dealer_value,
                player_blackjack=True,
                dealer_blackjack=True,
                payout=0.0
            )
        
        # Player has blackjack, dealer doesn't - player wins
        if player_blackjack and not dealer_blackjack:
            return GameResult(
                outcome=Outcome.BLACKJACK,
                player_total=player_value,
                dealer_total=dealer_value,
                player_blackjack=True,
                payout=self.rules.blackjack_payout
            )
        
        # Dealer has blackjack, player doesn't - dealer wins
        if dealer_blackjack and not player_blackjack:
            return GameResult(
                outcome=Outcome.LOSS,
                player_total=player_value,
                dealer_total=dealer_value,
                dealer_blackjack=True,
                payout=-1.0
            )
        
        # Compare values
        if player_value > dealer_value:
            return GameResult(
                outcome=Outcome.WIN,
                player_total=player_value,
                dealer_total=dealer_value,
                payout=1.0
            )
        elif player_value < dealer_value:
            return GameResult(
                outcome=Outcome.LOSS,
                player_total=player_value,
                dealer_total=dealer_value,
                payout=-1.0
            )
        else:
            return GameResult(
                outcome=Outcome.PUSH,
                player_total=player_value,
                dealer_total=dealer_value,
                payout=0.0
            )
    
    def __str__(self) -> str:
        """String representation of the game state."""
        if self.player_hand.card_count() == 0:
            return "Game not started"
        
        player_str = f"Player: {self.player_hand}"
        
        # Show only first dealer card until game is over
        if self.game_over:
            dealer_str = f"Dealer: {self.dealer_hand}"
        else:
            if self.dealer_hand.card_count() >= 1:
                first_card = self.dealer_hand.cards[0]
                dealer_str = f"Dealer: {first_card} [Hidden]"
            else:
                dealer_str = "Dealer: No cards"
        
        status = ""
        if self.game_over and self.result:
            status = f" - {self.result.outcome.value.title()}"
        
        return f"{player_str}\n{dealer_str}{status}"