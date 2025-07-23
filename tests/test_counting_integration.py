"""Integration tests for counting with game flow."""

import unittest
from unittest.mock import Mock, patch
from src.models import GameRules
from src.models.card import Card, Suit, Rank
from src.counting import HiLoSystem, KOSystem, CountingSystemManager
from src.game import CountingBlackjackGame


class TestCountingGameIntegration(unittest.TestCase):
    """Test cases for counting integration with game flow."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.rules = GameRules(num_decks=6, penetration=0.75)
        self.game = CountingBlackjackGame(self.rules)
    
    def test_initial_count_state(self):
        """Test initial counting state."""
        self.assertEqual(self.game.get_running_count(), 0)
        self.assertEqual(self.game.get_true_count(), 0.0)
        self.assertEqual(self.game.get_cards_seen(), 0)
        self.assertEqual(self.game.get_remaining_decks(), 6.0)
        self.assertEqual(self.game.get_counting_system_name(), "Hi-Lo")
    
    def test_count_updates_on_initial_deal(self):
        """Test that count updates when initial cards are dealt."""
        # Mock the shoe to return specific cards
        with patch.object(self.game.shoe, 'deal_card') as mock_deal:
            # Player gets 5, 6 (both +1 in Hi-Lo)
            # Dealer gets K (face up, -1) and hidden card
            mock_deal.side_effect = [
                Card(Suit.HEARTS, Rank.FIVE),    # Player card 1: +1
                Card(Suit.DIAMONDS, Rank.KING),  # Dealer face up: -1
                Card(Suit.CLUBS, Rank.SIX),      # Player card 2: +1
                Card(Suit.SPADES, Rank.SEVEN)    # Dealer hole card: 0 (not counted yet)
            ]
            
            self.game.deal_initial_cards()
            
            # Should count: +1 (player 5) + 1 (player 6) - 1 (dealer K) = +1
            # Dealer hole card not counted until revealed
            self.assertEqual(self.game.get_running_count(), 1)
            self.assertEqual(self.game.get_cards_seen(), 3)
    
    def test_count_updates_on_player_hit(self):
        """Test that count updates when player hits."""
        # Set up initial deal
        with patch.object(self.game.shoe, 'deal_card') as mock_deal:
            mock_deal.side_effect = [
                Card(Suit.HEARTS, Rank.FIVE),    # Player: +1
                Card(Suit.DIAMONDS, Rank.KING),  # Dealer face up: -1
                Card(Suit.CLUBS, Rank.SIX),      # Player: +1
                Card(Suit.SPADES, Rank.SEVEN),   # Dealer hole: 0 (not counted)
                Card(Suit.HEARTS, Rank.THREE)    # Player hit: +1
            ]
            
            self.game.deal_initial_cards()
            initial_count = self.game.get_running_count()
            
            # Player hits
            self.game.player_hit()
            
            # Count should increase by 1 for the THREE
            self.assertEqual(self.game.get_running_count(), initial_count + 1)
            self.assertEqual(self.game.get_cards_seen(), 4)
    
    def test_dealer_cards_revealed_on_stand(self):
        """Test that dealer hole card and additional cards are counted when player stands."""
        with patch.object(self.game.shoe, 'deal_card') as mock_deal:
            # Set up a scenario where dealer needs to hit
            mock_deal.side_effect = [
                Card(Suit.HEARTS, Rank.TEN),     # Player: -1
                Card(Suit.DIAMONDS, Rank.SIX),   # Dealer face up: +1
                Card(Suit.CLUBS, Rank.NINE),     # Player: 0
                Card(Suit.SPADES, Rank.FIVE),    # Dealer hole: +1 (will be revealed)
                Card(Suit.HEARTS, Rank.KING)     # Dealer hits: -1 (will be revealed)
            ]
            
            self.game.deal_initial_cards()
            initial_count = self.game.get_running_count()  # Should be -1 + 1 + 0 = 0
            
            # Player stands (dealer has 6+5=11, must hit and gets K for 21)
            self.game.player_stand()
            
            # Now dealer hole card (+1) and hit card (-1) should be counted
            expected_count = initial_count + 1 - 1  # +1 for 5, -1 for K
            self.assertEqual(self.game.get_running_count(), expected_count)
    
    def test_count_reset_on_shuffle(self):
        """Test that count resets when shoe is shuffled."""
        # Deal some cards to establish a count
        with patch.object(self.game.shoe, 'deal_card') as mock_deal:
            mock_deal.side_effect = [
                Card(Suit.HEARTS, Rank.FIVE),    # +1
                Card(Suit.DIAMONDS, Rank.KING),  # -1
                Card(Suit.CLUBS, Rank.SIX),      # +1
                Card(Suit.SPADES, Rank.SEVEN)    # 0
            ]
            
            self.game.deal_initial_cards()
            self.assertNotEqual(self.game.get_running_count(), 0)
        
        # Force a shuffle
        self.game.shoe.shuffle()
        self.game._notify_shuffle()
        
        # Count should be reset
        self.assertEqual(self.game.get_running_count(), 0)
        self.assertEqual(self.game.get_cards_seen(), 0)
    
    def test_true_count_calculation_during_game(self):
        """Test true count calculation as cards are dealt."""
        with patch.object(self.game.shoe, 'deal_card') as mock_deal:
            # Deal cards that give running count of +6
            mock_deal.side_effect = [Card(Suit.HEARTS, Rank.TWO)] * 10  # 10 cards, all +1
            
            # Deal initial cards (4 cards total)
            self.game.deal_initial_cards()
            
            # Hit a few times (6 more cards)
            for _ in range(6):
                if not self.game.is_game_over():
                    self.game.player_hit()
            
            running_count = self.game.get_running_count()
            remaining_decks = self.game.get_remaining_decks()
            expected_true_count = running_count / remaining_decks
            
            self.assertAlmostEqual(self.game.get_true_count(), expected_true_count, places=2)
    
    def test_counting_system_switching(self):
        """Test switching between counting systems."""
        # Start with Hi-Lo
        self.assertEqual(self.game.get_counting_system_name(), "Hi-Lo")
        
        # Switch to KO
        ko_system = KOSystem()
        self.game.switch_counting_system(ko_system)
        
        self.assertEqual(self.game.get_counting_system_name(), "KO")
        # Count should be reset when switching systems
        self.assertEqual(self.game.get_running_count(), 0)
        self.assertEqual(self.game.get_cards_seen(), 0)
    
    def test_count_info_comprehensive(self):
        """Test comprehensive count information."""
        with patch.object(self.game.shoe, 'deal_card') as mock_deal:
            mock_deal.side_effect = [
                Card(Suit.HEARTS, Rank.FIVE),    # +1
                Card(Suit.DIAMONDS, Rank.KING),  # -1
                Card(Suit.CLUBS, Rank.SIX),      # +1
                Card(Suit.SPADES, Rank.SEVEN)    # 0
            ]
            
            self.game.deal_initial_cards()
            count_info = self.game.get_count_info()
            
            self.assertIn('system', count_info)
            self.assertIn('running_count', count_info)
            self.assertIn('true_count', count_info)
            self.assertIn('cards_seen', count_info)
            self.assertIn('remaining_decks', count_info)
            self.assertIn('penetration', count_info)
            
            self.assertEqual(count_info['system'], 'Hi-Lo')
            self.assertIsInstance(count_info['running_count'], int)
            self.assertIsInstance(count_info['true_count'], float)
    
    def test_card_reveal_callbacks(self):
        """Test card reveal callback functionality."""
        callback_mock = Mock()
        self.game.add_card_reveal_callback(callback_mock)
        
        with patch.object(self.game.shoe, 'deal_card') as mock_deal:
            # Set up initial deal first
            mock_deal.side_effect = [
                Card(Suit.HEARTS, Rank.TEN),     # Player
                Card(Suit.DIAMONDS, Rank.KING),  # Dealer face up
                Card(Suit.CLUBS, Rank.FIVE),     # Player
                Card(Suit.SPADES, Rank.SEVEN),   # Dealer hole
                Card(Suit.HEARTS, Rank.FIVE)     # Hit card
            ]
            
            self.game.deal_initial_cards()
            callback_mock.reset_mock()  # Reset to only track the hit
            
            self.game.player_hit()
            
            # Callback should have been called with the hit card
            callback_mock.assert_called_with(Card(Suit.HEARTS, Rank.FIVE))
    
    def test_shuffle_callbacks(self):
        """Test shuffle callback functionality."""
        callback_mock = Mock()
        self.game.add_shuffle_callback(callback_mock)
        
        # Force a shuffle
        self.game.shoe.shuffle()
        self.game._notify_shuffle()
        
        # Callback should have been called
        callback_mock.assert_called_once()
    
    def test_double_down_counting(self):
        """Test counting when player doubles down."""
        with patch.object(self.game.shoe, 'deal_card') as mock_deal:
            mock_deal.side_effect = [
                Card(Suit.HEARTS, Rank.FIVE),    # Player: +1
                Card(Suit.DIAMONDS, Rank.SIX),   # Dealer face up: +1
                Card(Suit.CLUBS, Rank.SIX),      # Player: +1 (total 11, can double)
                Card(Suit.SPADES, Rank.SEVEN),   # Dealer hole: 0
                Card(Suit.HEARTS, Rank.NINE),    # Player double card: 0
                Card(Suit.DIAMONDS, Rank.KING)   # Dealer hits: -1
            ]
            
            self.game.deal_initial_cards()
            initial_count = self.game.get_running_count()
            
            # Player doubles (gets 9, dealer reveals hole card and hits with K)
            self.game.player_double()
            
            # Should count the double card (9=0) and revealed dealer cards (7=0, K=-1)
            expected_count = initial_count + 0 + 0 - 1  # +0 for 9, +0 for 7, -1 for K
            self.assertEqual(self.game.get_running_count(), expected_count)
    
    def test_surrender_no_additional_counting(self):
        """Test that surrender doesn't reveal additional cards."""
        with patch.object(self.game.shoe, 'deal_card') as mock_deal:
            mock_deal.side_effect = [
                Card(Suit.HEARTS, Rank.TEN),     # Player: -1
                Card(Suit.DIAMONDS, Rank.ACE),   # Dealer face up: -1
                Card(Suit.CLUBS, Rank.SIX),      # Player: +1
                Card(Suit.SPADES, Rank.KING)     # Dealer hole: -1 (not revealed)
            ]
            
            # Enable surrender in rules
            self.game.rules.surrender_allowed = True
            self.game.deal_initial_cards()
            
            # Make sure game is not over (check for blackjacks)
            if not self.game.is_game_over():
                count_before_surrender = self.game.get_running_count()
                
                # Player surrenders
                self.game.player_surrender()
                
                # Count should not change (dealer hole card not revealed)
                self.assertEqual(self.game.get_running_count(), count_before_surrender)
            else:
                # If game ended due to blackjack, just verify surrender is not allowed
                with self.assertRaises(RuntimeError):
                    self.game.player_surrender()
    
    def test_game_reset_preserves_count(self):
        """Test that game reset preserves count unless shoe is shuffled."""
        with patch.object(self.game.shoe, 'deal_card') as mock_deal:
            mock_deal.side_effect = [
                Card(Suit.HEARTS, Rank.FIVE),    # +1
                Card(Suit.DIAMONDS, Rank.KING),  # -1
                Card(Suit.CLUBS, Rank.SIX),      # +1
                Card(Suit.SPADES, Rank.SEVEN)    # 0
            ]
            
            self.game.deal_initial_cards()
            count_before_reset = self.game.get_running_count()
            
            # Reset without triggering shuffle by patching both needs_shuffle and cards_dealt_count
            with patch.object(self.game.shoe, 'needs_shuffle', return_value=False), \
                 patch.object(self.game.shoe, 'cards_dealt_count', return_value=10):  # Non-zero to avoid shuffle notification
                self.game.reset()
            
            # Count should be preserved
            self.assertEqual(self.game.get_running_count(), count_before_reset)
    
    def test_string_representation_with_count(self):
        """Test string representation includes count information."""
        with patch.object(self.game.shoe, 'deal_card') as mock_deal:
            mock_deal.side_effect = [
                Card(Suit.HEARTS, Rank.FIVE),    # +1
                Card(Suit.DIAMONDS, Rank.KING),  # -1
                Card(Suit.CLUBS, Rank.SIX),      # +1
                Card(Suit.SPADES, Rank.SEVEN)    # 0
            ]
            
            self.game.deal_initial_cards()
            game_str = str(self.game)
            
            self.assertIn("Count:", game_str)
            self.assertIn("RC=", game_str)
            self.assertIn("TC=", game_str)
            self.assertIn("Hi-Lo", game_str)


class TestCountingSystemIntegration(unittest.TestCase):
    """Test integration with different counting systems."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.rules = GameRules(num_decks=6)
        self.manager = CountingSystemManager()
    
    def test_different_systems_different_counts(self):
        """Test that different counting systems produce different counts."""
        # Create games with different systems
        hi_lo_game = CountingBlackjackGame(self.rules, self.manager.get_system("Hi-Lo"))
        ko_game = CountingBlackjackGame(self.rules, self.manager.get_system("KO"))
        hi_opt_i_game = CountingBlackjackGame(self.rules, self.manager.get_system("Hi-Opt I"))
        
        # Deal the same cards to all games
        # Only the first 3 cards are counted during initial deal (2 player + 1 dealer face up)
        test_cards = [
            Card(Suit.HEARTS, Rank.SEVEN),    # Player 1: Hi-Lo: 0, KO: +1, Hi-Opt I: 0
            Card(Suit.DIAMONDS, Rank.ACE),    # Dealer face up: Hi-Lo: -1, KO: -1, Hi-Opt I: 0
            Card(Suit.CLUBS, Rank.TWO),       # Player 2: Hi-Lo: +1, KO: +1, Hi-Opt I: 0
            Card(Suit.SPADES, Rank.KING)      # Dealer hole (not counted initially)
        ]
        
        for game in [hi_lo_game, ko_game, hi_opt_i_game]:
            with patch.object(game.shoe, 'deal_card') as mock_deal:
                mock_deal.side_effect = test_cards
                game.deal_initial_cards()
        
        # Check that counts are different (only first 3 cards counted)
        hi_lo_count = hi_lo_game.get_running_count()  # 0 - 1 + 1 = 0
        ko_count = ko_game.get_running_count()        # 1 - 1 + 1 = 1
        hi_opt_i_count = hi_opt_i_game.get_running_count()  # 0 + 0 + 0 = 0
        
        self.assertEqual(hi_lo_count, 0)
        self.assertEqual(ko_count, 1)
        self.assertEqual(hi_opt_i_count, 0)
    
    def test_system_switching_during_game(self):
        """Test switching counting systems during gameplay."""
        game = CountingBlackjackGame(self.rules)
        
        # Deal some cards with Hi-Lo
        with patch.object(game.shoe, 'deal_card') as mock_deal:
            mock_deal.side_effect = [
                Card(Suit.HEARTS, Rank.FIVE),    # Hi-Lo: +1
                Card(Suit.DIAMONDS, Rank.KING),  # Hi-Lo: -1
                Card(Suit.CLUBS, Rank.SIX),      # Hi-Lo: +1
                Card(Suit.SPADES, Rank.SEVEN)    # Hi-Lo: 0
            ]
            
            game.deal_initial_cards()
            hi_lo_count = game.get_running_count()
        
        # Switch to KO system
        ko_system = self.manager.get_system("KO")
        game.switch_counting_system(ko_system)
        
        # Count should be reset
        self.assertEqual(game.get_running_count(), 0)
        self.assertEqual(game.get_counting_system_name(), "KO")


if __name__ == '__main__':
    unittest.main()