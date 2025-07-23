"""Deviation strategy implementation for count-based decisions."""

from typing import Dict, Tuple, Optional
from src.models import Action, Card, Hand, GameRules, GameSituation, Rank
from .basic_strategy import BasicStrategy


class DeviationStrategy:
    """Implements count-based strategy deviations from basic strategy."""
    
    def __init__(self, basic_strategy: Optional[BasicStrategy] = None):
        """Initialize deviation strategy with basic strategy fallback.
        
        Args:
            basic_strategy: BasicStrategy instance to use as fallback
        """
        self.basic_strategy = basic_strategy or BasicStrategy()
        self._deviation_thresholds: Dict[Tuple[int, int, Action], float] = {}
        self._load_common_deviations()
    
    def get_action(self, player_hand: Hand, dealer_up: Card, true_count: float, 
                  rules: GameRules) -> Action:
        """Get the optimal action considering count-based deviations.
        
        Args:
            player_hand: The player's current hand
            dealer_up: The dealer's up card
            true_count: The current true count
            rules: The game rules configuration
            
        Returns:
            The optimal action considering deviations
        """
        if player_hand.is_blackjack():
            return Action.STAND
        
        player_total = player_hand.value()
        dealer_value = 11 if dealer_up.rank == Rank.ACE else dealer_up.value(ace_as_eleven=False)
        
        # Check for deviations first
        deviation_action = self._check_deviations(player_total, dealer_value, true_count, 
                                                player_hand, rules)
        if deviation_action:
            return deviation_action
        
        # Fall back to basic strategy
        return self.basic_strategy.get_action(player_hand, dealer_up, rules)
    
    def get_action_from_situation(self, situation: GameSituation, true_count: float, 
                                rules: GameRules) -> Action:
        """Get the optimal action from a GameSituation object with count.
        
        Args:
            situation: The game situation
            true_count: The current true count
            rules: The game rules configuration
            
        Returns:
            The optimal action considering deviations
        """
        # Create a temporary hand from the situation
        temp_hand = Hand(situation.player_cards)
        return self.get_action(temp_hand, situation.dealer_up_card, true_count, rules)
    
    def should_deviate(self, situation: GameSituation, true_count: float) -> bool:
        """Check if the current situation warrants a deviation from basic strategy.
        
        Args:
            situation: The game situation
            true_count: The current true count
            
        Returns:
            True if a deviation should be made, False otherwise
        """
        player_total = situation.player_total()
        dealer_value = 11 if situation.dealer_up_card.rank == Rank.ACE else situation.dealer_up_card.value(ace_as_eleven=False)
        
        # Check if any deviation applies
        for (p_total, d_value, action), threshold in self._deviation_thresholds.items():
            if p_total == player_total and d_value == dealer_value:
                if (action in [Action.STAND, Action.DOUBLE, Action.SPLIT] and true_count >= threshold) or \
                   (action == Action.HIT and true_count <= threshold):
                    return True
        
        return False
    
    def _check_deviations(self, player_total: int, dealer_value: int, true_count: float,
                         player_hand: Hand, rules: GameRules) -> Optional[Action]:
        """Check if any deviations apply to the current situation.
        
        Args:
            player_total: Player's hand total
            dealer_value: Dealer's up card value
            true_count: Current true count
            player_hand: Player's hand (for checking doubling/splitting eligibility)
            rules: Game rules
            
        Returns:
            Deviation action if applicable, None otherwise
        """
        # Insurance deviation (not implemented in basic game logic, but included for completeness)
        if dealer_value == 11 and true_count >= 3.0:
            # Would take insurance if available
            pass
        
        # 16 vs 10 deviation (most famous deviation)
        if player_total == 16 and dealer_value == 10:
            threshold = self._deviation_thresholds.get((16, 10, Action.STAND), float('inf'))
            if true_count >= threshold:
                return Action.STAND
            else:
                return Action.HIT
        
        # 15 vs 10 deviation
        if player_total == 15 and dealer_value == 10:
            threshold = self._deviation_thresholds.get((15, 10, Action.STAND), float('inf'))
            if true_count >= threshold:
                return Action.STAND
        
        # 13 vs 2 deviation
        if player_total == 13 and dealer_value == 2:
            threshold = self._deviation_thresholds.get((13, 2, Action.HIT), float('-inf'))
            if true_count <= threshold:
                return Action.HIT
        
        # 12 vs 3 deviation
        if player_total == 12 and dealer_value == 3:
            threshold = self._deviation_thresholds.get((12, 3, Action.HIT), float('-inf'))
            if true_count <= threshold:
                return Action.HIT
        
        # 12 vs 2 deviation
        if player_total == 12 and dealer_value == 2:
            threshold = self._deviation_thresholds.get((12, 2, Action.STAND), float('inf'))
            if true_count >= threshold:
                return Action.STAND
        
        # 10 vs 10 deviation (double)
        if player_total == 10 and dealer_value == 10 and player_hand.can_double():
            threshold = self._deviation_thresholds.get((10, 10, Action.DOUBLE), float('inf'))
            if true_count >= threshold:
                return Action.DOUBLE
        
        # 11 vs A deviation (double)
        if player_total == 11 and dealer_value == 11 and player_hand.can_double():
            threshold = self._deviation_thresholds.get((11, 11, Action.DOUBLE), float('inf'))
            if true_count >= threshold:
                return Action.DOUBLE
        
        # 9 vs 2 deviation (double)
        if player_total == 9 and dealer_value == 2 and player_hand.can_double():
            threshold = self._deviation_thresholds.get((9, 2, Action.DOUBLE), float('inf'))
            if true_count >= threshold:
                return Action.DOUBLE
        
        # 10,10 vs 5 deviation (split) - very high count only
        if (player_hand.can_split() and len(player_hand.cards) == 2 and 
            player_hand.cards[0].value(ace_as_eleven=False) == 10 and dealer_value == 5):
            threshold = self._deviation_thresholds.get((20, 5, Action.SPLIT), float('inf'))
            if true_count >= threshold:
                return Action.SPLIT
        
        # 10,10 vs 6 deviation (split) - very high count only
        if (player_hand.can_split() and len(player_hand.cards) == 2 and 
            player_hand.cards[0].value(ace_as_eleven=False) == 10 and dealer_value == 6):
            threshold = self._deviation_thresholds.get((20, 6, Action.SPLIT), float('inf'))
            if true_count >= threshold:
                return Action.SPLIT
        
        return None
    
    def _load_common_deviations(self) -> None:
        """Load common Hi-Lo deviation thresholds."""
        # Format: (player_total, dealer_value, action) -> true_count_threshold
        # Positive thresholds mean "do this action when count >= threshold"
        # Negative thresholds mean "do this action when count <= threshold"
        
        self._deviation_thresholds = {
            # Standing deviations (stand when count is high enough)
            (16, 10, Action.STAND): 0.0,    # 16 vs 10: Stand at TC 0 or higher
            (15, 10, Action.STAND): 4.0,    # 15 vs 10: Stand at TC +4 or higher
            (13, 2, Action.HIT): -1.0,     # 13 vs 2: Hit when TC -1 or lower (stand otherwise)
            (12, 3, Action.HIT): -2.0,     # 12 vs 3: Hit when TC -2 or lower (stand otherwise)  
            (12, 2, Action.STAND): 3.0,    # 12 vs 2: Stand at TC +3 or higher
            (12, 4, Action.STAND): 0.0,    # 12 vs 4: Stand at TC 0 or higher (basic strategy boundary)
            (12, 5, Action.HIT): -2.0,     # 12 vs 5: Hit when TC -2 or lower
            (12, 6, Action.HIT): -1.0,     # 12 vs 6: Hit when TC -1 or lower
            
            # Doubling deviations
            (10, 10, Action.DOUBLE): 4.0,  # 10 vs 10: Double at TC +4 or higher
            (11, 11, Action.DOUBLE): 1.0,  # 11 vs A: Double at TC +1 or higher
            (9, 2, Action.DOUBLE): 1.0,    # 9 vs 2: Double at TC +1 or higher
            (9, 7, Action.DOUBLE): 3.0,    # 9 vs 7: Double at TC +3 or higher
            (8, 6, Action.DOUBLE): 2.0,    # 8 vs 6: Double at TC +2 or higher
            
            # Splitting deviations (very rare and high count)
            (20, 5, Action.SPLIT): 5.0,    # 10,10 vs 5: Split at TC +5 or higher
            (20, 6, Action.SPLIT): 4.0,    # 10,10 vs 6: Split at TC +4 or higher
        }
    
    def get_deviation_threshold(self, player_total: int, dealer_value: int, 
                              action: Action) -> Optional[float]:
        """Get the true count threshold for a specific deviation.
        
        Args:
            player_total: Player's hand total
            dealer_value: Dealer's up card value
            action: The action to check
            
        Returns:
            The true count threshold, or None if no deviation exists
        """
        return self._deviation_thresholds.get((player_total, dealer_value, action))
    
    def add_custom_deviation(self, player_total: int, dealer_value: int, 
                           action: Action, threshold: float) -> None:
        """Add a custom deviation rule.
        
        Args:
            player_total: Player's hand total
            dealer_value: Dealer's up card value
            action: The action to take
            threshold: The true count threshold
        """
        self._deviation_thresholds[(player_total, dealer_value, action)] = threshold
    
    def get_all_deviations(self) -> Dict[Tuple[int, int, Action], float]:
        """Get all loaded deviation thresholds.
        
        Returns:
            Dictionary of all deviation thresholds
        """
        return self._deviation_thresholds.copy()