"""Tests for basic strategy implementation."""

import unittest
from src.strategy.basic_strategy import BasicStrategy
from src.models import Card, Hand, GameRules, GameSituation, Action, Suit, Rank


class TestBasicStrategy(unittest.TestCase):
    """Test cases for BasicStrategy class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.strategy = BasicStrategy()
        self.rules = GameRules()
    
    def test_hard_hands_basic_cases(self):
        """Test basic hard hand decisions."""
        # Player 12 vs dealer 4 should stand
        hand = Hand([Card(Suit.HEARTS, Rank.TEN), Card(Suit.SPADES, Rank.TWO)])
        dealer_up = Card(Suit.CLUBS, Rank.FOUR)
        action = self.strategy.get_action(hand, dealer_up, self.rules)
        assert action == Action.STAND
        
        # Player 12 vs dealer 7 should hit
        dealer_up = Card(Suit.CLUBS, Rank.SEVEN)
        action = self.strategy.get_action(hand, dealer_up, self.rules)
        assert action == Action.HIT
        
        # Player 16 vs dealer 10 should hit
        hand = Hand([Card(Suit.HEARTS, Rank.TEN), Card(Suit.SPADES, Rank.SIX)])
        dealer_up = Card(Suit.CLUBS, Rank.TEN)
        action = self.strategy.get_action(hand, dealer_up, self.rules)
        assert action == Action.HIT
        
        # Player 17 should always stand
        hand = Hand([Card(Suit.HEARTS, Rank.TEN), Card(Suit.SPADES, Rank.SEVEN)])
        dealer_up = Card(Suit.CLUBS, Rank.TEN)
        action = self.strategy.get_action(hand, dealer_up, self.rules)
        assert action == Action.STAND
    
    def test_hard_hands_doubling(self):
        """Test hard hand doubling decisions."""
        # Player 11 vs dealer 6 should double
        hand = Hand([Card(Suit.HEARTS, Rank.FIVE), Card(Suit.SPADES, Rank.SIX)])
        dealer_up = Card(Suit.CLUBS, Rank.SIX)
        action = self.strategy.get_action(hand, dealer_up, self.rules)
        assert action == Action.DOUBLE
        
        # Player 10 vs dealer 9 should double
        hand = Hand([Card(Suit.HEARTS, Rank.FIVE), Card(Suit.SPADES, Rank.FIVE)])
        dealer_up = Card(Suit.CLUBS, Rank.NINE)
        action = self.strategy.get_action(hand, dealer_up, self.rules)
        assert action == Action.DOUBLE
        
        # Player 10 vs dealer Ace should hit (not double)
        dealer_up = Card(Suit.CLUBS, Rank.ACE)
        action = self.strategy.get_action(hand, dealer_up, self.rules)
        assert action == Action.HIT
        
        # Player 9 vs dealer 5 should double
        hand = Hand([Card(Suit.HEARTS, Rank.FOUR), Card(Suit.SPADES, Rank.FIVE)])
        dealer_up = Card(Suit.CLUBS, Rank.FIVE)
        action = self.strategy.get_action(hand, dealer_up, self.rules)
        assert action == Action.DOUBLE
    
    def test_soft_hands(self):
        """Test soft hand decisions."""
        # A,6 (soft 17) vs dealer 5 should double
        hand = Hand([Card(Suit.HEARTS, Rank.ACE), Card(Suit.SPADES, Rank.SIX)])
        dealer_up = Card(Suit.CLUBS, Rank.FIVE)
        action = self.strategy.get_action(hand, dealer_up, self.rules)
        assert action == Action.DOUBLE
        
        # A,7 (soft 18) vs dealer 6 should double
        hand = Hand([Card(Suit.HEARTS, Rank.ACE), Card(Suit.SPADES, Rank.SEVEN)])
        dealer_up = Card(Suit.CLUBS, Rank.SIX)
        action = self.strategy.get_action(hand, dealer_up, self.rules)
        assert action == Action.DOUBLE
        
        # A,7 (soft 18) vs dealer 9 should hit
        dealer_up = Card(Suit.CLUBS, Rank.NINE)
        action = self.strategy.get_action(hand, dealer_up, self.rules)
        assert action == Action.HIT
        
        # A,8 (soft 19) should always stand
        hand = Hand([Card(Suit.HEARTS, Rank.ACE), Card(Suit.SPADES, Rank.EIGHT)])
        dealer_up = Card(Suit.CLUBS, Rank.FIVE)
        action = self.strategy.get_action(hand, dealer_up, self.rules)
        assert action == Action.STAND
        
        # A,2 (soft 13) vs dealer 6 should double
        hand = Hand([Card(Suit.HEARTS, Rank.ACE), Card(Suit.SPADES, Rank.TWO)])
        dealer_up = Card(Suit.CLUBS, Rank.SIX)
        action = self.strategy.get_action(hand, dealer_up, self.rules)
        assert action == Action.DOUBLE
    
    def test_pair_splitting(self):
        """Test pair splitting decisions."""
        # A,A should always split
        hand = Hand([Card(Suit.HEARTS, Rank.ACE), Card(Suit.SPADES, Rank.ACE)])
        dealer_up = Card(Suit.CLUBS, Rank.TEN)
        action = self.strategy.get_action(hand, dealer_up, self.rules)
        assert action == Action.SPLIT
        
        # 8,8 should always split
        hand = Hand([Card(Suit.HEARTS, Rank.EIGHT), Card(Suit.SPADES, Rank.EIGHT)])
        dealer_up = Card(Suit.CLUBS, Rank.TEN)
        action = self.strategy.get_action(hand, dealer_up, self.rules)
        assert action == Action.SPLIT
        
        # 10,10 should never split (stand)
        hand = Hand([Card(Suit.HEARTS, Rank.TEN), Card(Suit.SPADES, Rank.TEN)])
        dealer_up = Card(Suit.CLUBS, Rank.SIX)
        action = self.strategy.get_action(hand, dealer_up, self.rules)
        assert action == Action.STAND
        
        # 5,5 should never split (double vs 6)
        hand = Hand([Card(Suit.HEARTS, Rank.FIVE), Card(Suit.SPADES, Rank.FIVE)])
        dealer_up = Card(Suit.CLUBS, Rank.SIX)
        action = self.strategy.get_action(hand, dealer_up, self.rules)
        assert action == Action.DOUBLE
        
        # 9,9 vs dealer 7 should stand
        hand = Hand([Card(Suit.HEARTS, Rank.NINE), Card(Suit.SPADES, Rank.NINE)])
        dealer_up = Card(Suit.CLUBS, Rank.SEVEN)
        action = self.strategy.get_action(hand, dealer_up, self.rules)
        assert action == Action.STAND
        
        # 9,9 vs dealer 6 should split
        dealer_up = Card(Suit.CLUBS, Rank.SIX)
        action = self.strategy.get_action(hand, dealer_up, self.rules)
        assert action == Action.SPLIT
    
    def test_blackjack_hands(self):
        """Test blackjack (21 with 2 cards) handling."""
        # Natural blackjack should always stand
        hand = Hand([Card(Suit.HEARTS, Rank.ACE), Card(Suit.SPADES, Rank.KING)])
        dealer_up = Card(Suit.CLUBS, Rank.TEN)
        action = self.strategy.get_action(hand, dealer_up, self.rules)
        assert action == Action.STAND
    
    def test_edge_cases(self):
        """Test edge cases and boundary conditions."""
        # Very low totals should hit
        hand = Hand([Card(Suit.HEARTS, Rank.TWO), Card(Suit.SPADES, Rank.THREE)])
        dealer_up = Card(Suit.CLUBS, Rank.TEN)
        action = self.strategy.get_action(hand, dealer_up, self.rules)
        assert action == Action.HIT
        
        # Test with face cards
        hand = Hand([Card(Suit.HEARTS, Rank.JACK), Card(Suit.SPADES, Rank.QUEEN)])
        dealer_up = Card(Suit.CLUBS, Rank.SIX)
        action = self.strategy.get_action(hand, dealer_up, self.rules)
        assert action == Action.STAND
    
    def test_game_situation_interface(self):
        """Test the GameSituation interface."""
        # Create a game situation
        situation = GameSituation(
            player_cards=[Card(Suit.HEARTS, Rank.TEN), Card(Suit.SPADES, Rank.SIX)],
            dealer_up_card=Card(Suit.CLUBS, Rank.SEVEN),
            can_double=True,
            can_split=False
        )
        
        action = self.strategy.get_action_from_situation(situation, self.rules)
        assert action == Action.HIT  # 16 vs 7 should hit
    
    def test_multi_card_hands(self):
        """Test hands with more than 2 cards."""
        # 3-card hand totaling 12 vs dealer 4 should stand
        hand = Hand([
            Card(Suit.HEARTS, Rank.FOUR),
            Card(Suit.SPADES, Rank.FIVE),
            Card(Suit.CLUBS, Rank.THREE)
        ])
        dealer_up = Card(Suit.DIAMONDS, Rank.FOUR)
        action = self.strategy.get_action(hand, dealer_up, self.rules)
        assert action == Action.STAND
        
        # 3-card soft hand (A,2,4 = soft 17) vs dealer 6 should hit (can't double)
        hand = Hand([
            Card(Suit.HEARTS, Rank.ACE),
            Card(Suit.SPADES, Rank.TWO),
            Card(Suit.CLUBS, Rank.FOUR)
        ])
        dealer_up = Card(Suit.DIAMONDS, Rank.SIX)
        action = self.strategy.get_action(hand, dealer_up, self.rules)
        assert action == Action.HIT
    
    def test_ace_handling_in_pairs(self):
        """Test that ace pairs are handled correctly."""
        # A,A should split regardless of dealer up card
        hand = Hand([Card(Suit.HEARTS, Rank.ACE), Card(Suit.SPADES, Rank.ACE)])
        
        for rank in [Rank.TWO, Rank.FIVE, Rank.TEN, Rank.ACE]:
            dealer_up = Card(Suit.CLUBS, rank)
            action = self.strategy.get_action(hand, dealer_up, self.rules)
            assert action == Action.SPLIT
    
    def test_dealer_ace_handling(self):
        """Test decisions against dealer Ace."""
        # Player 11 vs dealer Ace should hit (not double)
        hand = Hand([Card(Suit.HEARTS, Rank.FIVE), Card(Suit.SPADES, Rank.SIX)])
        dealer_up = Card(Suit.CLUBS, Rank.ACE)
        action = self.strategy.get_action(hand, dealer_up, self.rules)
        assert action == Action.HIT
        
        # Player hard 17 vs dealer Ace should stand
        hand = Hand([Card(Suit.HEARTS, Rank.TEN), Card(Suit.SPADES, Rank.SEVEN)])
        action = self.strategy.get_action(hand, dealer_up, self.rules)
        assert action == Action.STAND


if __name__ == "__main__":
    unittest.main()