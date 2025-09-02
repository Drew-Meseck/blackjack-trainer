"""Tests for deviation strategy implementation."""

import unittest
from src.strategy.deviation_strategy import DeviationStrategy
from src.strategy.basic_strategy import BasicStrategy
from src.models import Card, Hand, GameRules, GameSituation, Action, Suit, Rank


class TestDeviationStrategy(unittest.TestCase):
    """Test cases for DeviationStrategy class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.strategy = DeviationStrategy()
        self.rules = GameRules()
    
    def test_basic_strategy_fallback(self):
        """Test that deviation strategy falls back to basic strategy when no deviations apply."""
        # Test a situation with no deviations at neutral count
        hand = Hand([Card(Suit.HEARTS, Rank.TEN), Card(Suit.SPADES, Rank.SEVEN)])
        dealer_up = Card(Suit.CLUBS, Rank.SEVEN)
        
        # At neutral count, should follow basic strategy (stand on 17)
        action = self.strategy.get_action(hand, dealer_up, 0.0, self.rules)
        self.assertEqual(action, Action.STAND)
    
    def test_famous_16_vs_10_deviation(self):
        """Test the famous 16 vs 10 deviation."""
        hand = Hand([Card(Suit.HEARTS, Rank.TEN), Card(Suit.SPADES, Rank.SIX)])
        dealer_up = Card(Suit.CLUBS, Rank.TEN)
        
        # At negative count, should hit (basic strategy)
        action = self.strategy.get_action(hand, dealer_up, -1.0, self.rules)
        self.assertEqual(action, Action.HIT)
        
        # At neutral or positive count, should stand (deviation)
        action = self.strategy.get_action(hand, dealer_up, 0.0, self.rules)
        self.assertEqual(action, Action.STAND)
        
        action = self.strategy.get_action(hand, dealer_up, 2.0, self.rules)
        self.assertEqual(action, Action.STAND)
    
    def test_15_vs_10_deviation(self):
        """Test 15 vs 10 deviation."""
        hand = Hand([Card(Suit.HEARTS, Rank.TEN), Card(Suit.SPADES, Rank.FIVE)])
        dealer_up = Card(Suit.CLUBS, Rank.TEN)
        
        # Below threshold, should hit
        action = self.strategy.get_action(hand, dealer_up, 3.0, self.rules)
        self.assertEqual(action, Action.HIT)
        
        # At or above threshold (+4), should stand
        action = self.strategy.get_action(hand, dealer_up, 4.0, self.rules)
        self.assertEqual(action, Action.STAND)
        
        action = self.strategy.get_action(hand, dealer_up, 5.0, self.rules)
        self.assertEqual(action, Action.STAND)
    
    def test_13_vs_2_deviation(self):
        """Test 13 vs 2 deviation."""
        hand = Hand([Card(Suit.HEARTS, Rank.TEN), Card(Suit.SPADES, Rank.THREE)])
        dealer_up = Card(Suit.CLUBS, Rank.TWO)
        
        # At very negative count (-2 or lower), should hit (deviation)
        action = self.strategy.get_action(hand, dealer_up, -2.0, self.rules)
        self.assertEqual(action, Action.HIT)
        
        # At neutral or positive count, should stand (basic strategy)
        action = self.strategy.get_action(hand, dealer_up, 0.0, self.rules)
        self.assertEqual(action, Action.STAND)
    
    def test_12_vs_3_deviation(self):
        """Test 12 vs 3 deviation."""
        hand = Hand([Card(Suit.HEARTS, Rank.TEN), Card(Suit.SPADES, Rank.TWO)])
        dealer_up = Card(Suit.CLUBS, Rank.THREE)
        
        # At very negative count (-2 or lower), should hit (deviation)
        action = self.strategy.get_action(hand, dealer_up, -3.0, self.rules)
        self.assertEqual(action, Action.HIT)
        
        # At neutral count, should hit (basic strategy - no deviation applies)
        action = self.strategy.get_action(hand, dealer_up, 0.0, self.rules)
        self.assertEqual(action, Action.HIT)
    
    def test_12_vs_2_deviation(self):
        """Test 12 vs 2 deviation."""
        hand = Hand([Card(Suit.HEARTS, Rank.TEN), Card(Suit.SPADES, Rank.TWO)])
        dealer_up = Card(Suit.CLUBS, Rank.TWO)
        
        # Below threshold, should hit (basic strategy)
        action = self.strategy.get_action(hand, dealer_up, 2.0, self.rules)
        self.assertEqual(action, Action.HIT)
        
        # At or above threshold (+3), should stand
        action = self.strategy.get_action(hand, dealer_up, 3.0, self.rules)
        self.assertEqual(action, Action.STAND)
    
    def test_doubling_deviations(self):
        """Test doubling deviations."""
        # 10 vs 10 deviation
        hand = Hand([Card(Suit.HEARTS, Rank.FIVE), Card(Suit.SPADES, Rank.FIVE)])
        dealer_up = Card(Suit.CLUBS, Rank.TEN)
        
        # Below threshold, should hit
        action = self.strategy.get_action(hand, dealer_up, 3.0, self.rules)
        self.assertEqual(action, Action.HIT)
        
        # At or above threshold (+4), should double
        action = self.strategy.get_action(hand, dealer_up, 4.0, self.rules)
        self.assertEqual(action, Action.DOUBLE)
        
        # 11 vs A deviation
        hand = Hand([Card(Suit.HEARTS, Rank.FIVE), Card(Suit.SPADES, Rank.SIX)])
        dealer_up = Card(Suit.CLUBS, Rank.ACE)
        
        # Below threshold, should hit
        action = self.strategy.get_action(hand, dealer_up, 0.0, self.rules)
        self.assertEqual(action, Action.HIT)
        
        # At or above threshold (+1), should double
        action = self.strategy.get_action(hand, dealer_up, 1.0, self.rules)
        self.assertEqual(action, Action.DOUBLE)
    
    def test_splitting_deviations(self):
        """Test splitting deviations (10,10 vs 5 and 6)."""
        # 10,10 vs 5 deviation (very high count)
        hand = Hand([Card(Suit.HEARTS, Rank.TEN), Card(Suit.SPADES, Rank.TEN)])
        dealer_up = Card(Suit.CLUBS, Rank.FIVE)
        
        # Below threshold, should stand
        action = self.strategy.get_action(hand, dealer_up, 4.0, self.rules)
        self.assertEqual(action, Action.STAND)
        
        # At or above threshold (+5), should split
        action = self.strategy.get_action(hand, dealer_up, 5.0, self.rules)
        self.assertEqual(action, Action.SPLIT)
        
        # 10,10 vs 6 deviation
        dealer_up = Card(Suit.CLUBS, Rank.SIX)
        
        # Below threshold, should stand
        action = self.strategy.get_action(hand, dealer_up, 3.0, self.rules)
        self.assertEqual(action, Action.STAND)
        
        # At or above threshold (+4), should split
        action = self.strategy.get_action(hand, dealer_up, 4.0, self.rules)
        self.assertEqual(action, Action.SPLIT)
    
    def test_blackjack_handling(self):
        """Test that blackjack hands always stand regardless of count."""
        hand = Hand([Card(Suit.HEARTS, Rank.ACE), Card(Suit.SPADES, Rank.KING)])
        dealer_up = Card(Suit.CLUBS, Rank.TEN)
        
        # Should always stand on blackjack
        action = self.strategy.get_action(hand, dealer_up, 5.0, self.rules)
        self.assertEqual(action, Action.STAND)
    
    def test_should_deviate_method(self):
        """Test the should_deviate method."""
        # 16 vs 10 at positive count should deviate
        situation = GameSituation(
            player_cards=[Card(Suit.HEARTS, Rank.TEN), Card(Suit.SPADES, Rank.SIX)],
            dealer_up_card=Card(Suit.CLUBS, Rank.TEN)
        )
        
        self.assertTrue(self.strategy.should_deviate(situation, 1.0))
        self.assertFalse(self.strategy.should_deviate(situation, -1.0))
        
        # 17 vs 10 should not deviate (no deviation exists)
        situation = GameSituation(
            player_cards=[Card(Suit.HEARTS, Rank.TEN), Card(Suit.SPADES, Rank.SEVEN)],
            dealer_up_card=Card(Suit.CLUBS, Rank.TEN)
        )
        
        self.assertFalse(self.strategy.should_deviate(situation, 5.0))
    
    def test_game_situation_interface(self):
        """Test the GameSituation interface."""
        situation = GameSituation(
            player_cards=[Card(Suit.HEARTS, Rank.TEN), Card(Suit.SPADES, Rank.SIX)],
            dealer_up_card=Card(Suit.CLUBS, Rank.TEN),
            can_double=True,
            can_split=False
        )
        
        # At positive count, should stand (deviation)
        action = self.strategy.get_action_from_situation(situation, 1.0, self.rules)
        self.assertEqual(action, Action.STAND)
        
        # At negative count, should hit (basic strategy)
        action = self.strategy.get_action_from_situation(situation, -1.0, self.rules)
        self.assertEqual(action, Action.HIT)
    
    def test_custom_deviations(self):
        """Test adding custom deviation rules."""
        # Add a custom deviation
        self.strategy.add_custom_deviation(14, 5, Action.STAND, 2.0)
        
        # Test that the custom deviation works
        hand = Hand([Card(Suit.HEARTS, Rank.TEN), Card(Suit.SPADES, Rank.FOUR)])
        dealer_up = Card(Suit.CLUBS, Rank.FIVE)
        
        # This should now use our custom deviation
        threshold = self.strategy.get_deviation_threshold(14, 5, Action.STAND)
        self.assertEqual(threshold, 2.0)
    
    def test_get_all_deviations(self):
        """Test getting all deviation thresholds."""
        deviations = self.strategy.get_all_deviations()
        
        # Should contain the famous 16 vs 10 deviation
        self.assertIn((16, 10, Action.STAND), deviations)
        self.assertEqual(deviations[(16, 10, Action.STAND)], 0.0)
        
        # Should contain multiple deviations
        self.assertGreater(len(deviations), 10)
    
    def test_multi_card_hands(self):
        """Test deviations with multi-card hands."""
        # 3-card 16 vs 10 should still follow deviation
        hand = Hand([
            Card(Suit.HEARTS, Rank.FIVE),
            Card(Suit.SPADES, Rank.FIVE),
            Card(Suit.CLUBS, Rank.SIX)
        ])
        dealer_up = Card(Suit.DIAMONDS, Rank.TEN)
        
        # At positive count, should stand
        action = self.strategy.get_action(hand, dealer_up, 1.0, self.rules)
        self.assertEqual(action, Action.STAND)
        
        # At negative count, should hit
        action = self.strategy.get_action(hand, dealer_up, -1.0, self.rules)
        self.assertEqual(action, Action.HIT)
    
    def test_dealer_ace_handling(self):
        """Test deviations against dealer Ace."""
        # 11 vs A deviation
        hand = Hand([Card(Suit.HEARTS, Rank.FIVE), Card(Suit.SPADES, Rank.SIX)])
        dealer_up = Card(Suit.CLUBS, Rank.ACE)
        
        # Below threshold, should hit
        action = self.strategy.get_action(hand, dealer_up, 0.0, self.rules)
        self.assertEqual(action, Action.HIT)
        
        # At threshold (+1), should double
        action = self.strategy.get_action(hand, dealer_up, 1.0, self.rules)
        self.assertEqual(action, Action.DOUBLE)


if __name__ == "__main__":
    unittest.main()