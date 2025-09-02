"""Basic strategy implementation for blackjack."""

from typing import Dict, Tuple, Optional
from src.models import Action, Card, Hand, GameRules, GameSituation, Rank


class BasicStrategy:
    """Implements mathematically optimal basic strategy for blackjack."""
    
    def __init__(self):
        """Initialize basic strategy with default charts."""
        self._hard_strategy: Dict[Tuple[int, int], Action] = {}
        self._soft_strategy: Dict[Tuple[int, int], Action] = {}
        self._pair_strategy: Dict[Tuple[str, int], Action] = {}
        self._load_default_strategy()
    
    def get_action(self, player_hand: Hand, dealer_up: Card, rules: GameRules) -> Action:
        """Get the optimal basic strategy action for a given situation.
        
        Args:
            player_hand: The player's current hand
            dealer_up: The dealer's up card
            rules: The game rules configuration
            
        Returns:
            The optimal action according to basic strategy
        """
        if player_hand.is_blackjack():
            return Action.STAND
        
        player_total = player_hand.value()
        # For strategy purposes, Ace is treated as 11 in dealer up card
        dealer_value = 11 if dealer_up.rank == Rank.ACE else dealer_up.value(ace_as_eleven=False)
        
        # Check for pairs first (if splitting is possible)
        if player_hand.can_split() and len(player_hand.cards) == 2:
            pair_rank = player_hand.cards[0].rank.value
            action = self._get_pair_action(pair_rank, dealer_value, rules)
            if action == Action.SPLIT:
                return action
        
        # Check if doubling is possible (only with 2 cards)
        can_double = player_hand.can_double()
        
        # Check for soft hands
        if player_hand.is_soft():
            return self._get_soft_action(player_total, dealer_value, rules, can_double)
        
        # Hard hands
        return self._get_hard_action(player_total, dealer_value, rules, can_double)
    
    def get_action_from_situation(self, situation: GameSituation, rules: GameRules) -> Action:
        """Get the optimal action from a GameSituation object.
        
        Args:
            situation: The game situation
            rules: The game rules configuration
            
        Returns:
            The optimal action according to basic strategy
        """
        # Create a temporary hand from the situation
        temp_hand = Hand(situation.player_cards)
        return self.get_action(temp_hand, situation.dealer_up_card, rules)
    
    def _get_hard_action(self, player_total: int, dealer_value: int, rules: GameRules, can_double: bool = True) -> Action:
        """Get action for hard hands (no aces counted as 11)."""
        key = (player_total, dealer_value)
        action = self._hard_strategy.get(key, Action.STAND)
        
        # Check if doubling is available for hard hands
        if action == Action.DOUBLE and not can_double:
            # If we can't double, hit instead
            return Action.HIT
        
        return action
    
    def _get_soft_action(self, player_total: int, dealer_value: int, rules: GameRules, can_double: bool = True) -> Action:
        """Get action for soft hands (ace counted as 11)."""
        key = (player_total, dealer_value)
        action = self._soft_strategy.get(key, Action.STAND)
        
        # Check if doubling is available for soft hands
        if action == Action.DOUBLE and not can_double:
            # If we can't double, hit instead
            return Action.HIT
        
        return action
    
    def _get_pair_action(self, pair_rank: str, dealer_value: int, rules: GameRules) -> Action:
        """Get action for pairs."""
        key = (pair_rank, dealer_value)
        action = self._pair_strategy.get(key, Action.HIT)
        
        # If we can't split, fall back to hard/soft strategy
        if action == Action.SPLIT:
            return Action.SPLIT
        
        return action
    
    def _load_default_strategy(self) -> None:
        """Load the default basic strategy charts."""
        self._load_hard_strategy()
        self._load_soft_strategy()
        self._load_pair_strategy()
    
    def _load_hard_strategy(self) -> None:
        """Load hard hand strategy chart."""
        # Hard totals strategy (player_total, dealer_up) -> Action
        hard_chart = {
            # Player 5-8: Always hit
            (5, 2): Action.HIT, (5, 3): Action.HIT, (5, 4): Action.HIT, (5, 5): Action.HIT,
            (5, 6): Action.HIT, (5, 7): Action.HIT, (5, 8): Action.HIT, (5, 9): Action.HIT,
            (5, 10): Action.HIT, (5, 11): Action.HIT,
            
            (6, 2): Action.HIT, (6, 3): Action.HIT, (6, 4): Action.HIT, (6, 5): Action.HIT,
            (6, 6): Action.HIT, (6, 7): Action.HIT, (6, 8): Action.HIT, (6, 9): Action.HIT,
            (6, 10): Action.HIT, (6, 11): Action.HIT,
            
            (7, 2): Action.HIT, (7, 3): Action.HIT, (7, 4): Action.HIT, (7, 5): Action.HIT,
            (7, 6): Action.HIT, (7, 7): Action.HIT, (7, 8): Action.HIT, (7, 9): Action.HIT,
            (7, 10): Action.HIT, (7, 11): Action.HIT,
            
            (8, 2): Action.HIT, (8, 3): Action.HIT, (8, 4): Action.HIT, (8, 5): Action.HIT,
            (8, 6): Action.HIT, (8, 7): Action.HIT, (8, 8): Action.HIT, (8, 9): Action.HIT,
            (8, 10): Action.HIT, (8, 11): Action.HIT,
            
            # Player 9: Double vs 3-6, otherwise hit
            (9, 2): Action.HIT, (9, 3): Action.DOUBLE, (9, 4): Action.DOUBLE, (9, 5): Action.DOUBLE,
            (9, 6): Action.DOUBLE, (9, 7): Action.HIT, (9, 8): Action.HIT, (9, 9): Action.HIT,
            (9, 10): Action.HIT, (9, 11): Action.HIT,
            
            # Player 10: Double vs 2-9, otherwise hit
            (10, 2): Action.DOUBLE, (10, 3): Action.DOUBLE, (10, 4): Action.DOUBLE, (10, 5): Action.DOUBLE,
            (10, 6): Action.DOUBLE, (10, 7): Action.DOUBLE, (10, 8): Action.DOUBLE, (10, 9): Action.DOUBLE,
            (10, 10): Action.HIT, (10, 11): Action.HIT,
            
            # Player 11: Double vs 2-10, hit vs Ace
            (11, 2): Action.DOUBLE, (11, 3): Action.DOUBLE, (11, 4): Action.DOUBLE, (11, 5): Action.DOUBLE,
            (11, 6): Action.DOUBLE, (11, 7): Action.DOUBLE, (11, 8): Action.DOUBLE, (11, 9): Action.DOUBLE,
            (11, 10): Action.DOUBLE, (11, 11): Action.HIT,
            
            # Player 12: Stand vs 4-6, otherwise hit
            (12, 2): Action.HIT, (12, 3): Action.HIT, (12, 4): Action.STAND, (12, 5): Action.STAND,
            (12, 6): Action.STAND, (12, 7): Action.HIT, (12, 8): Action.HIT, (12, 9): Action.HIT,
            (12, 10): Action.HIT, (12, 11): Action.HIT,
            
            # Player 13-16: Stand vs 2-6, otherwise hit
            (13, 2): Action.STAND, (13, 3): Action.STAND, (13, 4): Action.STAND, (13, 5): Action.STAND,
            (13, 6): Action.STAND, (13, 7): Action.HIT, (13, 8): Action.HIT, (13, 9): Action.HIT,
            (13, 10): Action.HIT, (13, 11): Action.HIT,
            
            (14, 2): Action.STAND, (14, 3): Action.STAND, (14, 4): Action.STAND, (14, 5): Action.STAND,
            (14, 6): Action.STAND, (14, 7): Action.HIT, (14, 8): Action.HIT, (14, 9): Action.HIT,
            (14, 10): Action.HIT, (14, 11): Action.HIT,
            
            (15, 2): Action.STAND, (15, 3): Action.STAND, (15, 4): Action.STAND, (15, 5): Action.STAND,
            (15, 6): Action.STAND, (15, 7): Action.HIT, (15, 8): Action.HIT, (15, 9): Action.HIT,
            (15, 10): Action.HIT, (15, 11): Action.HIT,
            
            (16, 2): Action.STAND, (16, 3): Action.STAND, (16, 4): Action.STAND, (16, 5): Action.STAND,
            (16, 6): Action.STAND, (16, 7): Action.HIT, (16, 8): Action.HIT, (16, 9): Action.HIT,
            (16, 10): Action.HIT, (16, 11): Action.HIT,
            
            # Player 17-21: Always stand
            (17, 2): Action.STAND, (17, 3): Action.STAND, (17, 4): Action.STAND, (17, 5): Action.STAND,
            (17, 6): Action.STAND, (17, 7): Action.STAND, (17, 8): Action.STAND, (17, 9): Action.STAND,
            (17, 10): Action.STAND, (17, 11): Action.STAND,
            
            (18, 2): Action.STAND, (18, 3): Action.STAND, (18, 4): Action.STAND, (18, 5): Action.STAND,
            (18, 6): Action.STAND, (18, 7): Action.STAND, (18, 8): Action.STAND, (18, 9): Action.STAND,
            (18, 10): Action.STAND, (18, 11): Action.STAND,
            
            (19, 2): Action.STAND, (19, 3): Action.STAND, (19, 4): Action.STAND, (19, 5): Action.STAND,
            (19, 6): Action.STAND, (19, 7): Action.STAND, (19, 8): Action.STAND, (19, 9): Action.STAND,
            (19, 10): Action.STAND, (19, 11): Action.STAND,
            
            (20, 2): Action.STAND, (20, 3): Action.STAND, (20, 4): Action.STAND, (20, 5): Action.STAND,
            (20, 6): Action.STAND, (20, 7): Action.STAND, (20, 8): Action.STAND, (20, 9): Action.STAND,
            (20, 10): Action.STAND, (20, 11): Action.STAND,
            
            (21, 2): Action.STAND, (21, 3): Action.STAND, (21, 4): Action.STAND, (21, 5): Action.STAND,
            (21, 6): Action.STAND, (21, 7): Action.STAND, (21, 8): Action.STAND, (21, 9): Action.STAND,
            (21, 10): Action.STAND, (21, 11): Action.STAND,
        }
        
        self._hard_strategy = hard_chart
    
    def _load_soft_strategy(self) -> None:
        """Load soft hand strategy chart."""
        # Soft totals strategy (player_total, dealer_up) -> Action
        soft_chart = {
            # A,2 (13): Double vs 5-6, otherwise hit
            (13, 2): Action.HIT, (13, 3): Action.HIT, (13, 4): Action.HIT, (13, 5): Action.DOUBLE,
            (13, 6): Action.DOUBLE, (13, 7): Action.HIT, (13, 8): Action.HIT, (13, 9): Action.HIT,
            (13, 10): Action.HIT, (13, 11): Action.HIT,
            
            # A,3 (14): Double vs 5-6, otherwise hit
            (14, 2): Action.HIT, (14, 3): Action.HIT, (14, 4): Action.HIT, (14, 5): Action.DOUBLE,
            (14, 6): Action.DOUBLE, (14, 7): Action.HIT, (14, 8): Action.HIT, (14, 9): Action.HIT,
            (14, 10): Action.HIT, (14, 11): Action.HIT,
            
            # A,4 (15): Double vs 4-6, otherwise hit
            (15, 2): Action.HIT, (15, 3): Action.HIT, (15, 4): Action.DOUBLE, (15, 5): Action.DOUBLE,
            (15, 6): Action.DOUBLE, (15, 7): Action.HIT, (15, 8): Action.HIT, (15, 9): Action.HIT,
            (15, 10): Action.HIT, (15, 11): Action.HIT,
            
            # A,5 (16): Double vs 4-6, otherwise hit
            (16, 2): Action.HIT, (16, 3): Action.HIT, (16, 4): Action.DOUBLE, (16, 5): Action.DOUBLE,
            (16, 6): Action.DOUBLE, (16, 7): Action.HIT, (16, 8): Action.HIT, (16, 9): Action.HIT,
            (16, 10): Action.HIT, (16, 11): Action.HIT,
            
            # A,6 (17): Double vs 3-6, otherwise hit
            (17, 2): Action.HIT, (17, 3): Action.DOUBLE, (17, 4): Action.DOUBLE, (17, 5): Action.DOUBLE,
            (17, 6): Action.DOUBLE, (17, 7): Action.HIT, (17, 8): Action.HIT, (17, 9): Action.HIT,
            (17, 10): Action.HIT, (17, 11): Action.HIT,
            
            # A,7 (18): Stand vs 2,7,8; Double vs 3-6; Hit vs 9,10,A
            (18, 2): Action.STAND, (18, 3): Action.DOUBLE, (18, 4): Action.DOUBLE, (18, 5): Action.DOUBLE,
            (18, 6): Action.DOUBLE, (18, 7): Action.STAND, (18, 8): Action.STAND, (18, 9): Action.HIT,
            (18, 10): Action.HIT, (18, 11): Action.HIT,
            
            # A,8 (19): Always stand
            (19, 2): Action.STAND, (19, 3): Action.STAND, (19, 4): Action.STAND, (19, 5): Action.STAND,
            (19, 6): Action.STAND, (19, 7): Action.STAND, (19, 8): Action.STAND, (19, 9): Action.STAND,
            (19, 10): Action.STAND, (19, 11): Action.STAND,
            
            # A,9 (20): Always stand
            (20, 2): Action.STAND, (20, 3): Action.STAND, (20, 4): Action.STAND, (20, 5): Action.STAND,
            (20, 6): Action.STAND, (20, 7): Action.STAND, (20, 8): Action.STAND, (20, 9): Action.STAND,
            (20, 10): Action.STAND, (20, 11): Action.STAND,
        }
        
        self._soft_strategy = soft_chart
    
    def _load_pair_strategy(self) -> None:
        """Load pair splitting strategy chart."""
        # Pair strategy (pair_rank, dealer_up) -> Action
        pair_chart = {
            # A,A: Always split
            ("A", 2): Action.SPLIT, ("A", 3): Action.SPLIT, ("A", 4): Action.SPLIT, ("A", 5): Action.SPLIT,
            ("A", 6): Action.SPLIT, ("A", 7): Action.SPLIT, ("A", 8): Action.SPLIT, ("A", 9): Action.SPLIT,
            ("A", 10): Action.SPLIT, ("A", 11): Action.SPLIT,
            
            # 2,2: Split vs 2-7, otherwise hit
            ("2", 2): Action.SPLIT, ("2", 3): Action.SPLIT, ("2", 4): Action.SPLIT, ("2", 5): Action.SPLIT,
            ("2", 6): Action.SPLIT, ("2", 7): Action.SPLIT, ("2", 8): Action.HIT, ("2", 9): Action.HIT,
            ("2", 10): Action.HIT, ("2", 11): Action.HIT,
            
            # 3,3: Split vs 2-7, otherwise hit
            ("3", 2): Action.SPLIT, ("3", 3): Action.SPLIT, ("3", 4): Action.SPLIT, ("3", 5): Action.SPLIT,
            ("3", 6): Action.SPLIT, ("3", 7): Action.SPLIT, ("3", 8): Action.HIT, ("3", 9): Action.HIT,
            ("3", 10): Action.HIT, ("3", 11): Action.HIT,
            
            # 4,4: Hit vs all (don't split)
            ("4", 2): Action.HIT, ("4", 3): Action.HIT, ("4", 4): Action.HIT, ("4", 5): Action.HIT,
            ("4", 6): Action.HIT, ("4", 7): Action.HIT, ("4", 8): Action.HIT, ("4", 9): Action.HIT,
            ("4", 10): Action.HIT, ("4", 11): Action.HIT,
            
            # 5,5: Never split, treat as 10 (double vs 2-9)
            ("5", 2): Action.DOUBLE, ("5", 3): Action.DOUBLE, ("5", 4): Action.DOUBLE, ("5", 5): Action.DOUBLE,
            ("5", 6): Action.DOUBLE, ("5", 7): Action.DOUBLE, ("5", 8): Action.DOUBLE, ("5", 9): Action.DOUBLE,
            ("5", 10): Action.HIT, ("5", 11): Action.HIT,
            
            # 6,6: Split vs 2-6, otherwise hit
            ("6", 2): Action.SPLIT, ("6", 3): Action.SPLIT, ("6", 4): Action.SPLIT, ("6", 5): Action.SPLIT,
            ("6", 6): Action.SPLIT, ("6", 7): Action.HIT, ("6", 8): Action.HIT, ("6", 9): Action.HIT,
            ("6", 10): Action.HIT, ("6", 11): Action.HIT,
            
            # 7,7: Split vs 2-7, otherwise hit
            ("7", 2): Action.SPLIT, ("7", 3): Action.SPLIT, ("7", 4): Action.SPLIT, ("7", 5): Action.SPLIT,
            ("7", 6): Action.SPLIT, ("7", 7): Action.SPLIT, ("7", 8): Action.HIT, ("7", 9): Action.HIT,
            ("7", 10): Action.HIT, ("7", 11): Action.HIT,
            
            # 8,8: Always split
            ("8", 2): Action.SPLIT, ("8", 3): Action.SPLIT, ("8", 4): Action.SPLIT, ("8", 5): Action.SPLIT,
            ("8", 6): Action.SPLIT, ("8", 7): Action.SPLIT, ("8", 8): Action.SPLIT, ("8", 9): Action.SPLIT,
            ("8", 10): Action.SPLIT, ("8", 11): Action.SPLIT,
            
            # 9,9: Split vs 2-9 except 7, stand vs 7,10,A
            ("9", 2): Action.SPLIT, ("9", 3): Action.SPLIT, ("9", 4): Action.SPLIT, ("9", 5): Action.SPLIT,
            ("9", 6): Action.SPLIT, ("9", 7): Action.STAND, ("9", 8): Action.SPLIT, ("9", 9): Action.SPLIT,
            ("9", 10): Action.STAND, ("9", 11): Action.STAND,
            
            # 10,10: Never split (always stand)
            ("10", 2): Action.STAND, ("10", 3): Action.STAND, ("10", 4): Action.STAND, ("10", 5): Action.STAND,
            ("10", 6): Action.STAND, ("10", 7): Action.STAND, ("10", 8): Action.STAND, ("10", 9): Action.STAND,
            ("10", 10): Action.STAND, ("10", 11): Action.STAND,
            
            # J,J: Never split (always stand)
            ("J", 2): Action.STAND, ("J", 3): Action.STAND, ("J", 4): Action.STAND, ("J", 5): Action.STAND,
            ("J", 6): Action.STAND, ("J", 7): Action.STAND, ("J", 8): Action.STAND, ("J", 9): Action.STAND,
            ("J", 10): Action.STAND, ("J", 11): Action.STAND,
            
            # Q,Q: Never split (always stand)
            ("Q", 2): Action.STAND, ("Q", 3): Action.STAND, ("Q", 4): Action.STAND, ("Q", 5): Action.STAND,
            ("Q", 6): Action.STAND, ("Q", 7): Action.STAND, ("Q", 8): Action.STAND, ("Q", 9): Action.STAND,
            ("Q", 10): Action.STAND, ("Q", 11): Action.STAND,
            
            # K,K: Never split (always stand)
            ("K", 2): Action.STAND, ("K", 3): Action.STAND, ("K", 4): Action.STAND, ("K", 5): Action.STAND,
            ("K", 6): Action.STAND, ("K", 7): Action.STAND, ("K", 8): Action.STAND, ("K", 9): Action.STAND,
            ("K", 10): Action.STAND, ("K", 11): Action.STAND,
        }
        
        self._pair_strategy = pair_chart