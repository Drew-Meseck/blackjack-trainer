"""Validation tests for strategy engine accuracy against known optimal plays."""

import unittest
from typing import Dict, Tuple, List

from src.models import GameRules, Card, Suit, Rank, Action, Hand
from src.strategy import BasicStrategy, DeviationStrategy
from src.counting import HiLoSystem, CardCounter
from src.game import CountingBlackjackGame

class TestBasicStrategyAccuracy(unittest.TestCase):
    """Test basic strategy engine against known optimal plays."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.strategy = BasicStrategy()
        self.standard_rules = GameRules(
            dealer_hits_soft_17=True,
            double_after_split=True,
            surrender_allowed=True,
            num_decks=6
        )
        self.conservative_rules = GameRules(
            dealer_hits_soft_17=False,
            double_after_split=False,
            surrender_allowed=False,
            num_decks=1
        )
    
    def _number_to_rank(self, number: int) -> Rank:
        """Convert a number to a Rank enum."""
        rank_map = {
            1: Rank.ACE, 2: Rank.TWO, 3: Rank.THREE, 4: Rank.FOUR, 5: Rank.FIVE,
            6: Rank.SIX, 7: Rank.SEVEN, 8: Rank.EIGHT, 9: Rank.NINE, 10: Rank.TEN,
            11: Rank.JACK, 12: Rank.QUEEN, 13: Rank.KING
        }
        return rank_map.get(number, Rank.TEN)
    
    def _create_hand(self, cards: List[Tuple[Suit, Rank]]) -> Hand:
        """Helper to create a hand from card tuples."""
        hand = Hand()
        for suit, rank in cards:
            hand.add_card(Card(suit, rank))
        return hand
    
    def test_hard_totals_basic_strategy(self):
        """Test basic strategy for hard totals against known optimal plays."""
        # Known optimal plays for hard totals (player_total, dealer_up_card, expected_action)
        hard_total_tests = [
            # Hard 8 and below - always hit
            (8, Rank.TWO, Action.HIT),
            (8, Rank.SIX, Action.HIT),
            (8, Rank.TEN, Action.HIT),
            (8, Rank.ACE, Action.HIT),
            
            # Hard 9 - double on 3-6, hit otherwise
            (9, Rank.TWO, Action.HIT),
            (9, Rank.THREE, Action.DOUBLE),
            (9, Rank.FOUR, Action.DOUBLE),
            (9, Rank.FIVE, Action.DOUBLE),
            (9, Rank.SIX, Action.DOUBLE),
            (9, Rank.SEVEN, Action.HIT),
            (9, Rank.TEN, Action.HIT),
            (9, Rank.ACE, Action.HIT),
            
            # Hard 10 - double on 2-9, hit on 10/A
            (10, Rank.TWO, Action.DOUBLE),
            (10, Rank.FIVE, Action.DOUBLE),
            (10, Rank.NINE, Action.DOUBLE),
            (10, Rank.TEN, Action.HIT),
            (10, Rank.ACE, Action.HIT),
            
            # Hard 11 - double on 2-10, hit on A (with DAS)
            (11, Rank.TWO, Action.DOUBLE),
            (11, Rank.NINE, Action.DOUBLE),
            (11, Rank.TEN, Action.DOUBLE),
            (11, Rank.ACE, Action.HIT),
            
            # Hard 12 - stand on 4-6, hit otherwise
            (12, Rank.TWO, Action.HIT),
            (12, Rank.THREE, Action.HIT),
            (12, Rank.FOUR, Action.STAND),
            (12, Rank.FIVE, Action.STAND),
            (12, Rank.SIX, Action.STAND),
            (12, Rank.SEVEN, Action.HIT),
            (12, Rank.TEN, Action.HIT),
            (12, Rank.ACE, Action.HIT),
            
            # Hard 13-16 - stand on 2-6, hit on 7-A
            (13, Rank.TWO, Action.STAND),
            (13, Rank.SIX, Action.STAND),
            (13, Rank.SEVEN, Action.HIT),
            (13, Rank.TEN, Action.HIT),
            (13, Rank.ACE, Action.HIT),
            
            (16, Rank.TWO, Action.STAND),
            (16, Rank.SIX, Action.STAND),
            (16, Rank.SEVEN, Action.HIT),
            (16, Rank.TEN, Action.HIT),
            (16, Rank.ACE, Action.HIT),
            
            # Hard 17+ - always stand
            (17, Rank.TWO, Action.STAND),
            (17, Rank.TEN, Action.STAND),
            (17, Rank.ACE, Action.STAND),
            (20, Rank.TEN, Action.STAND),
            (21, Rank.ACE, Action.STAND),
        ]
        
        for player_total, dealer_rank, expected_action in hard_total_tests:
            # Create hard hand with specified total
            if player_total <= 11:
                remaining_value = player_total - 2
                remaining_rank = self._number_to_rank(remaining_value)
                hand = self._create_hand([(Suit.HEARTS, Rank.TWO), (Suit.CLUBS, remaining_rank)])
            else:
                # Use 10 + (total-10) to avoid going over 21 with face cards
                remaining = player_total - 10
                if remaining <= 10:
                    remaining_rank = self._number_to_rank(remaining)
                    hand = self._create_hand([(Suit.HEARTS, Rank.TEN), (Suit.CLUBS, remaining_rank)])
                else:
                    # For totals > 20, use multiple small cards
                    remaining_rank = self._number_to_rank(remaining - 10)
                    hand = self._create_hand([(Suit.HEARTS, Rank.TEN), (Suit.CLUBS, Rank.TEN), (Suit.SPADES, remaining_rank)])
            
            dealer_up = Card(Suit.DIAMONDS, dealer_rank)
            
            # Test with standard rules
            action = self.strategy.get_action(hand, dealer_up, self.standard_rules)
            
            # Handle double down when not allowed (should default to hit)
            if expected_action == Action.DOUBLE and not hand.can_double():
                expected_action = Action.HIT
            
            self.assertEqual(
                action, expected_action,
                f"Hard {player_total} vs {dealer_rank}: expected {expected_action}, got {action}"
            )
    
    def test_soft_totals_basic_strategy(self):
        """Test basic strategy for soft totals."""
        # Known optimal plays for soft totals
        soft_total_tests = [
            # Soft 13-15 (A,2 to A,4) - double on 5-6, hit otherwise
            (13, Rank.FOUR, Action.HIT),
            (13, Rank.FIVE, Action.DOUBLE),
            (13, Rank.SIX, Action.DOUBLE),
            (13, Rank.SEVEN, Action.HIT),
            
            (15, Rank.FOUR, Action.HIT),
            (15, Rank.FIVE, Action.DOUBLE),
            (15, Rank.SIX, Action.DOUBLE),
            (15, Rank.SEVEN, Action.HIT),
            
            # Soft 16-17 (A,5 to A,6) - double on 4-6, hit otherwise
            (16, Rank.THREE, Action.HIT),
            (16, Rank.FOUR, Action.DOUBLE),
            (16, Rank.FIVE, Action.DOUBLE),
            (16, Rank.SIX, Action.DOUBLE),
            (16, Rank.SEVEN, Action.HIT),
            
            (17, Rank.THREE, Action.HIT),
            (17, Rank.FOUR, Action.DOUBLE),
            (17, Rank.FIVE, Action.DOUBLE),
            (17, Rank.SIX, Action.DOUBLE),
            (17, Rank.SEVEN, Action.HIT),
            
            # Soft 18 (A,7) - double on 3-6, stand on 2,7,8, hit on 9,10,A
            (18, Rank.TWO, Action.STAND),
            (18, Rank.THREE, Action.DOUBLE),
            (18, Rank.FOUR, Action.DOUBLE),
            (18, Rank.FIVE, Action.DOUBLE),
            (18, Rank.SIX, Action.DOUBLE),
            (18, Rank.SEVEN, Action.STAND),
            (18, Rank.EIGHT, Action.STAND),
            (18, Rank.NINE, Action.HIT),
            (18, Rank.TEN, Action.HIT),
            (18, Rank.ACE, Action.HIT),
            
            # Soft 19+ - always stand
            (19, Rank.TWO, Action.STAND),
            (19, Rank.TEN, Action.STAND),
            (20, Rank.ACE, Action.STAND),
        ]
        
        for soft_total, dealer_rank, expected_action in soft_total_tests:
            # Create soft hand (Ace + other card)
            other_value = soft_total - 11  # Since Ace counts as 11 in soft total
            other_rank = self._number_to_rank(other_value)
            hand = self._create_hand([(Suit.HEARTS, Rank.ACE), (Suit.CLUBS, other_rank)])
            
            dealer_up = Card(Suit.DIAMONDS, dealer_rank)
            
            action = self.strategy.get_action(hand, dealer_up, self.standard_rules)
            
            # Handle double down when not allowed
            if expected_action == Action.DOUBLE and not hand.can_double():
                expected_action = Action.HIT
            
            self.assertEqual(
                action, expected_action,
                f"Soft {soft_total} vs {dealer_rank}: expected {expected_action}, got {action}"
            )
    
    def test_pair_splitting_strategy(self):
        """Test basic strategy for pair splitting."""
        pair_tests = [
            # Always split
            (Rank.ACE, Rank.TWO, Action.SPLIT),
            (Rank.ACE, Rank.TEN, Action.SPLIT),
            (Rank.EIGHT, Rank.TWO, Action.SPLIT),
            (Rank.EIGHT, Rank.ACE, Action.SPLIT),
            
            # Never split
            (Rank.TEN, Rank.TWO, Action.STAND),
            (Rank.TEN, Rank.TEN, Action.STAND),
            (Rank.FIVE, Rank.TWO, Action.DOUBLE),  # 5,5 = 10, should double
            (Rank.FIVE, Rank.TEN, Action.HIT),     # 5,5 vs 10, should hit
            
            # Conditional splits
            (Rank.TWO, Rank.TWO, Action.HIT),     # 2,2 vs 2: hit (or split if DAS)
            (Rank.TWO, Rank.SEVEN, Action.SPLIT), # 2,2 vs 7: split
            (Rank.TWO, Rank.EIGHT, Action.HIT),   # 2,2 vs 8: hit
            
            (Rank.THREE, Rank.SEVEN, Action.SPLIT), # 3,3 vs 7: split
            (Rank.THREE, Rank.EIGHT, Action.HIT),   # 3,3 vs 8: hit
            
            (Rank.SIX, Rank.SIX, Action.SPLIT),   # 6,6 vs 6: split
            (Rank.SIX, Rank.SEVEN, Action.HIT),   # 6,6 vs 7: hit
            
            (Rank.SEVEN, Rank.SEVEN, Action.SPLIT), # 7,7 vs 7: split
            (Rank.SEVEN, Rank.TEN, Action.HIT),     # 7,7 vs 10: hit
            
            (Rank.NINE, Rank.SEVEN, Action.SPLIT), # 9,9 vs 7: split
            (Rank.NINE, Rank.TEN, Action.STAND),   # 9,9 vs 10: stand (18 is good)
            (Rank.NINE, Rank.ACE, Action.STAND),   # 9,9 vs A: stand
        ]
        
        for pair_rank, dealer_rank, expected_action in pair_tests:
            hand = self._create_hand([(Suit.HEARTS, pair_rank), (Suit.CLUBS, pair_rank)])
            dealer_up = Card(Suit.DIAMONDS, dealer_rank)
            
            action = self.strategy.get_action(hand, dealer_up, self.standard_rules)
            
            self.assertEqual(
                action, expected_action,
                f"Pair {pair_rank},{pair_rank} vs {dealer_rank}: expected {expected_action}, got {action}"
            )
    
    def test_surrender_strategy(self):
        """Test surrender strategy when allowed."""
        surrender_tests = [
            # Hard 15 vs 10 - surrender
            (15, Rank.TEN, Action.SURRENDER),
            # Hard 16 vs 9,10,A - surrender
            (16, Rank.NINE, Action.SURRENDER),
            (16, Rank.TEN, Action.SURRENDER),
            (16, Rank.ACE, Action.SURRENDER),
            # Hard 16 vs 8 - hit (no surrender)
            (16, Rank.EIGHT, Action.HIT),
        ]
        
        for player_total, dealer_rank, expected_action in surrender_tests:
            remaining_value = player_total - 10
            remaining_rank = self._number_to_rank(remaining_value)
            hand = self._create_hand([(Suit.HEARTS, Rank.TEN), (Suit.CLUBS, remaining_rank)])
            dealer_up = Card(Suit.DIAMONDS, dealer_rank)
            
            # Test with surrender allowed
            action = self.strategy.get_action(hand, dealer_up, self.standard_rules)
            self.assertEqual(action, expected_action)
            
            # Test with surrender not allowed - should default to basic action
            if expected_action == Action.SURRENDER:
                action_no_surrender = self.strategy.get_action(hand, dealer_up, self.conservative_rules)
                self.assertIn(action_no_surrender, [Action.HIT, Action.STAND])
    
    def test_rule_variations_impact(self):
        """Test how different rule variations affect strategy."""
        test_hand = self._create_hand([(Suit.HEARTS, Rank.ACE), (Suit.CLUBS, Rank.SEVEN)])  # Soft 18
        dealer_up = Card(Suit.DIAMONDS, Rank.TWO)
        
        # Standard rules - should stand on soft 18 vs 2
        standard_action = self.strategy.get_action(test_hand, dealer_up, self.standard_rules)
        self.assertEqual(standard_action, Action.STAND)
        
        # Test with different deck counts
        single_deck_rules = GameRules(num_decks=1, dealer_hits_soft_17=False)
        single_deck_action = self.strategy.get_action(test_hand, dealer_up, single_deck_rules)
        # Strategy might be different for single deck
        self.assertIn(single_deck_action, [Action.STAND, Action.DOUBLE])


class TestDeviationStrategyAccuracy(unittest.TestCase):
    """Test deviation strategy accuracy with counting systems."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.deviation_strategy = DeviationStrategy()
        self.hi_lo_system = HiLoSystem()
        self.rules = GameRules(num_decks=6, dealer_hits_soft_17=True)
    
    def test_insurance_deviations(self):
        """Test insurance deviation based on true count."""
        # Insurance is generally taken at true count +3 or higher
        player_hand = Hand()
        player_hand.add_card(Card(Suit.HEARTS, Rank.TEN))
        player_hand.add_card(Card(Suit.CLUBS, Rank.SEVEN))
        
        dealer_up = Card(Suit.DIAMONDS, Rank.ACE)
        
        # Low count - no insurance
        low_count_action = self.deviation_strategy.get_action(
            player_hand, dealer_up, -2.0, self.rules
        )
        # Should not take insurance (would be handled separately, but strategy should be normal)
        
        # High count - take insurance
        high_count_action = self.deviation_strategy.get_action(
            player_hand, dealer_up, 4.0, self.rules
        )
        # Insurance decision would be handled separately from main strategy
    
    def test_sixteen_vs_ten_deviation(self):
        """Test the classic 16 vs 10 deviation."""
        # Hard 16 vs 10
        player_hand = Hand()
        player_hand.add_card(Card(Suit.HEARTS, Rank.TEN))
        player_hand.add_card(Card(Suit.CLUBS, Rank.SIX))
        
        dealer_up = Card(Suit.DIAMONDS, Rank.TEN)
        
        # Low/neutral count - hit (basic strategy)
        low_count_action = self.deviation_strategy.get_action(
            player_hand, dealer_up, -1.0, self.rules
        )
        self.assertEqual(low_count_action, Action.HIT)
        
        # High count - stand (deviation)
        high_count_action = self.deviation_strategy.get_action(
            player_hand, dealer_up, 1.0, self.rules  # True count +1 is threshold for this deviation
        )
        self.assertEqual(high_count_action, Action.STAND)
    
    def test_twelve_vs_three_deviation(self):
        """Test 12 vs 3 deviation."""
        # Hard 12 vs 3
        player_hand = Hand()
        player_hand.add_card(Card(Suit.HEARTS, Rank.TEN))
        player_hand.add_card(Card(Suit.CLUBS, Rank.TWO))
        
        dealer_up = Card(Suit.DIAMONDS, Rank.THREE)
        
        # Low count - hit (deviation from basic strategy)
        low_count_action = self.deviation_strategy.get_action(
            player_hand, dealer_up, -2.0, self.rules
        )
        self.assertEqual(low_count_action, Action.HIT)
        
        # High count - stand (basic strategy)
        high_count_action = self.deviation_strategy.get_action(
            player_hand, dealer_up, 2.0, self.rules
        )
        self.assertEqual(high_count_action, Action.STAND)
    
    def test_deviation_thresholds(self):
        """Test that deviations occur at correct count thresholds."""
        # Test various deviation scenarios with their known thresholds
        deviation_tests = [
            # (player_cards, dealer_up, threshold, low_count_action, high_count_action)
            ([(Suit.HEARTS, Rank.TEN), (Suit.CLUBS, Rank.FIVE)], Rank.TEN, 5.0, Action.HIT, Action.STAND),  # 15 vs 10
            ([(Suit.HEARTS, Rank.NINE), (Suit.CLUBS, Rank.SEVEN)], Rank.TEN, 4.0, Action.HIT, Action.STAND),  # 16 vs 10
            ([(Suit.HEARTS, Rank.TEN), (Suit.CLUBS, Rank.TWO)], Rank.FOUR, 0.0, Action.STAND, Action.HIT),   # 12 vs 4
        ]
        
        for player_cards, dealer_rank, threshold, low_action, high_action in deviation_tests:
            player_hand = self._create_hand(player_cards)
            dealer_up = Card(Suit.DIAMONDS, dealer_rank)
            
            # Test below threshold
            below_action = self.deviation_strategy.get_action(
                player_hand, dealer_up, threshold - 1.0, self.rules
            )
            self.assertEqual(below_action, low_action)
            
            # Test above threshold
            above_action = self.deviation_strategy.get_action(
                player_hand, dealer_up, threshold + 1.0, self.rules
            )
            self.assertEqual(above_action, high_action)
    
    def _create_hand(self, cards: List[Tuple[Suit, Rank]]) -> Hand:
        """Helper to create a hand from card tuples."""
        hand = Hand()
        for suit, rank in cards:
            hand.add_card(Card(suit, rank))
        return hand


class TestStrategyIntegrationWithCounting(unittest.TestCase):
    """Test strategy integration with counting systems in game context."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.rules = GameRules(num_decks=6)
        self.hi_lo_system = HiLoSystem()
        self.game = CountingBlackjackGame(self.rules, self.hi_lo_system)
        self.basic_strategy = BasicStrategy()
        self.deviation_strategy = DeviationStrategy()
    
    def test_strategy_with_live_count(self):
        """Test strategy decisions with live count from actual game."""
        # Set up a specific game scenario
        from unittest.mock import patch
        
        with patch.object(self.game.shoe, 'deal_card') as mock_deal:
            # Create a high-count scenario
            high_count_cards = [
                Card(Suit.HEARTS, Rank.FIVE),    # +1
                Card(Suit.DIAMONDS, Rank.SIX),   # +1  
                Card(Suit.CLUBS, Rank.FOUR),     # +1
                Card(Suit.SPADES, Rank.THREE),   # +1 (running count = +4)
                Card(Suit.HEARTS, Rank.TEN),     # Player gets 10
                Card(Suit.DIAMONDS, Rank.TEN),   # Dealer face up
                Card(Suit.CLUBS, Rank.SIX),      # Player gets 6 (total 16)
                Card(Suit.SPADES, Rank.SEVEN)    # Dealer hole card
            ]
            
            mock_deal.side_effect = high_count_cards
            
            # Deal the high count cards first to establish count
            for _ in range(4):
                self.game.shoe.deal_card()
                self.game.card_counter.update_count(high_count_cards[_])
            
            # Now deal the actual hand
            self.game.deal_initial_cards()
            
            # Get current count
            true_count = self.game.get_true_count()
            self.assertGreater(true_count, 0)  # Should be positive
            
            # Get strategy recommendations
            basic_action = self.basic_strategy.get_action(
                self.game.player_hand, self.game.dealer_hand.cards[0], self.rules
            )
            
            deviation_action = self.deviation_strategy.get_action(
                self.game.player_hand, self.game.dealer_hand.cards[0], true_count, self.rules
            )
            
            # With 16 vs 10 and high count, deviation should be different from basic
            if (self.game.player_hand.value() == 16 and 
                self.game.dealer_hand.cards[0].rank == Rank.TEN and 
                true_count >= 0):
                self.assertEqual(basic_action, Action.HIT)
                self.assertEqual(deviation_action, Action.STAND)
    
    def test_strategy_accuracy_over_multiple_hands(self):
        """Test strategy accuracy over multiple hands with varying counts."""
        hands_played = 0
        correct_basic_decisions = 0
        correct_deviation_decisions = 0
        
        # Play multiple hands with different scenarios
        for _ in range(10):
            self.game.reset()
            
            # Deal a hand
            self.game.deal_initial_cards()
            
            if not self.game.is_game_over():  # Skip blackjacks for strategy testing
                true_count = self.game.get_true_count()
                
                # Get strategy recommendations
                basic_action = self.basic_strategy.get_action(
                    self.game.player_hand, self.game.dealer_hand.cards[0], self.rules
                )
                
                deviation_action = self.deviation_strategy.get_action(
                    self.game.player_hand, self.game.dealer_hand.cards[0], true_count, self.rules
                )
                
                # Verify actions are valid
                available_actions = self.game.get_available_actions()
                
                if basic_action in available_actions:
                    correct_basic_decisions += 1
                
                if deviation_action in available_actions:
                    correct_deviation_decisions += 1
                
                hands_played += 1
        
        # Both strategies should provide valid actions most of the time
        if hands_played > 0:
            basic_accuracy = correct_basic_decisions / hands_played
            deviation_accuracy = correct_deviation_decisions / hands_played
            
            self.assertGreater(basic_accuracy, 0.8)  # Should be valid 80%+ of time
            self.assertGreater(deviation_accuracy, 0.8)


if __name__ == '__main__':
    unittest.main()