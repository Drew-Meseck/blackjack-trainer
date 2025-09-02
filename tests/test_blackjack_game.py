"""Unit tests for BlackjackGame class."""

import unittest
from unittest.mock import Mock, patch
from src.models import Card, Suit, Rank, GameRules, Outcome, Action
from src.game.blackjack_game import BlackjackGame


class TestBlackjackGame(unittest.TestCase):
    """Test cases for the BlackjackGame class."""
    
    def setUp(self):
        """Set up test game and cards."""
        self.rules = GameRules(
            dealer_hits_soft_17=True,
            double_after_split=True,
            surrender_allowed=True,
            num_decks=1,
            penetration=0.75,
            blackjack_payout=1.5
        )
        self.game = BlackjackGame(self.rules)
        
        # Test cards
        self.ace_hearts = Card(Suit.HEARTS, Rank.ACE)
        self.ace_spades = Card(Suit.SPADES, Rank.ACE)
        self.king_spades = Card(Suit.SPADES, Rank.KING)
        self.queen_hearts = Card(Suit.HEARTS, Rank.QUEEN)
        self.jack_clubs = Card(Suit.CLUBS, Rank.JACK)
        self.ten_diamonds = Card(Suit.DIAMONDS, Rank.TEN)
        self.nine_hearts = Card(Suit.HEARTS, Rank.NINE)
        self.eight_clubs = Card(Suit.CLUBS, Rank.EIGHT)
        self.seven_diamonds = Card(Suit.DIAMONDS, Rank.SEVEN)
        self.six_clubs = Card(Suit.CLUBS, Rank.SIX)
        self.five_diamonds = Card(Suit.DIAMONDS, Rank.FIVE)
        self.four_hearts = Card(Suit.HEARTS, Rank.FOUR)
        self.three_spades = Card(Suit.SPADES, Rank.THREE)
        self.two_clubs = Card(Suit.CLUBS, Rank.TWO)
    
    def test_game_initialization(self):
        """Test game initialization."""
        self.assertEqual(self.game.rules, self.rules)
        self.assertEqual(self.game.player_hand.card_count(), 0)
        self.assertEqual(self.game.dealer_hand.card_count(), 0)
        self.assertFalse(self.game.game_over)
        self.assertIsNone(self.game.result)
        self.assertFalse(self.game.is_game_over())
        self.assertIsNone(self.game.get_result())
    
    @patch('src.models.shoe.Shoe.deal_card')
    def test_deal_initial_cards_normal(self, mock_deal):
        """Test dealing initial cards in normal scenario."""
        # Mock cards to be dealt
        mock_deal.side_effect = [
            self.king_spades,    # Player card 1
            self.five_diamonds,  # Dealer card 1
            self.six_clubs,      # Player card 2
            self.seven_diamonds  # Dealer card 2
        ]
        
        player_hand, dealer_hand = self.game.deal_initial_cards()
        
        # Check hands
        self.assertEqual(player_hand.card_count(), 2)
        self.assertEqual(dealer_hand.card_count(), 2)
        self.assertEqual(player_hand.value(), 16)  # K + 6
        self.assertEqual(dealer_hand.value(), 12)  # 5 + 7
        
        # Game should not be over (no blackjacks)
        self.assertFalse(self.game.is_game_over())
        self.assertIsNone(self.game.get_result())
    
    @patch('src.models.shoe.Shoe.deal_card')
    def test_deal_initial_cards_player_blackjack(self, mock_deal):
        """Test dealing initial cards with player blackjack."""
        mock_deal.side_effect = [
            self.ace_hearts,     # Player card 1
            self.five_diamonds,  # Dealer card 1
            self.king_spades,    # Player card 2
            self.seven_diamonds  # Dealer card 2
        ]
        
        player_hand, dealer_hand = self.game.deal_initial_cards()
        
        # Check hands
        self.assertTrue(player_hand.is_blackjack())
        self.assertFalse(dealer_hand.is_blackjack())
        
        # Game should be over
        self.assertTrue(self.game.is_game_over())
        result = self.game.get_result()
        self.assertIsNotNone(result)
        self.assertEqual(result.outcome, Outcome.BLACKJACK)
        self.assertEqual(result.payout, 1.5)
    
    @patch('src.models.shoe.Shoe.deal_card')
    def test_deal_initial_cards_both_blackjack(self, mock_deal):
        """Test dealing initial cards with both blackjacks."""
        mock_deal.side_effect = [
            self.ace_hearts,     # Player card 1
            self.ace_spades,     # Dealer card 1
            self.king_spades,    # Player card 2
            self.queen_hearts    # Dealer card 2
        ]
        
        player_hand, dealer_hand = self.game.deal_initial_cards()
        
        # Check hands
        self.assertTrue(player_hand.is_blackjack())
        self.assertTrue(dealer_hand.is_blackjack())
        
        # Game should be over with push
        self.assertTrue(self.game.is_game_over())
        result = self.game.get_result()
        self.assertIsNotNone(result)
        self.assertEqual(result.outcome, Outcome.PUSH)
        self.assertEqual(result.payout, 0.0)
    
    def test_deal_initial_cards_already_started(self):
        """Test dealing initial cards when game already started."""
        # Add a card to player hand to simulate started game
        self.game.player_hand.add_card(self.king_spades)
        
        with self.assertRaises(RuntimeError) as context:
            self.game.deal_initial_cards()
        
        self.assertIn("Game already started", str(context.exception))
    
    @patch('src.models.shoe.Shoe.needs_shuffle')
    def test_deal_initial_cards_needs_shuffle(self, mock_needs_shuffle):
        """Test dealing initial cards when shoe needs shuffling."""
        mock_needs_shuffle.return_value = True
        
        with self.assertRaises(RuntimeError) as context:
            self.game.deal_initial_cards()
        
        self.assertIn("Shoe needs shuffling", str(context.exception))
    
    @patch('src.models.shoe.Shoe.deal_card')
    def test_player_hit_normal(self, mock_deal):
        """Test player hitting in normal scenario."""
        # Set up initial game state
        self.game.player_hand.add_card(self.king_spades)
        self.game.player_hand.add_card(self.five_diamonds)
        self.game.dealer_hand.add_card(self.seven_diamonds)
        self.game.dealer_hand.add_card(self.eight_clubs)
        
        mock_deal.return_value = self.four_hearts
        
        card = self.game.player_hit()
        
        self.assertEqual(card, self.four_hearts)
        self.assertEqual(self.game.player_hand.value(), 19)  # K + 5 + 4
        self.assertFalse(self.game.is_game_over())
    
    @patch('src.models.shoe.Shoe.deal_card')
    def test_player_hit_bust(self, mock_deal):
        """Test player hitting and busting."""
        # Set up initial game state
        self.game.player_hand.add_card(self.king_spades)
        self.game.player_hand.add_card(self.five_diamonds)
        self.game.dealer_hand.add_card(self.seven_diamonds)
        self.game.dealer_hand.add_card(self.eight_clubs)
        
        mock_deal.return_value = self.ten_diamonds  # This will bust (K + 5 + 10 = 25)
        
        card = self.game.player_hit()
        
        self.assertEqual(card, self.ten_diamonds)
        self.assertEqual(self.game.player_hand.value(), 25)
        self.assertTrue(self.game.is_game_over())
        
        result = self.game.get_result()
        self.assertEqual(result.outcome, Outcome.LOSS)
        self.assertTrue(result.player_busted)
        self.assertEqual(result.payout, -1.0)
    
    def test_player_hit_game_over(self):
        """Test player hitting when game is over."""
        self.game.game_over = True
        
        with self.assertRaises(RuntimeError) as context:
            self.game.player_hit()
        
        self.assertIn("Game is over", str(context.exception))
    
    def test_player_hit_not_started(self):
        """Test player hitting when game not started."""
        with self.assertRaises(RuntimeError) as context:
            self.game.player_hit()
        
        self.assertIn("Game not started", str(context.exception))
    
    @patch('src.models.shoe.Shoe.deal_card')
    def test_player_stand_dealer_hits(self, mock_deal):
        """Test player standing and dealer hitting."""
        # Set up game state: Player 18, Dealer showing 6 with hidden 10 (16 total)
        self.game.player_hand.add_card(self.king_spades)
        self.game.player_hand.add_card(self.eight_clubs)
        self.game.dealer_hand.add_card(self.six_clubs)
        self.game.dealer_hand.add_card(self.ten_diamonds)
        
        # Dealer will hit and get 5 (16 + 5 = 21)
        mock_deal.return_value = self.five_diamonds
        
        self.game.player_stand()
        
        self.assertTrue(self.game.is_game_over())
        self.assertEqual(self.game.dealer_hand.value(), 21)
        
        result = self.game.get_result()
        self.assertEqual(result.outcome, Outcome.LOSS)  # Dealer 21 beats player 18
        self.assertEqual(result.payout, -1.0)
    
    @patch('src.models.shoe.Shoe.deal_card')
    def test_player_stand_dealer_busts(self, mock_deal):
        """Test player standing and dealer busting."""
        # Set up game state: Player 18, Dealer 16
        self.game.player_hand.add_card(self.king_spades)
        self.game.player_hand.add_card(self.eight_clubs)
        self.game.dealer_hand.add_card(self.six_clubs)
        self.game.dealer_hand.add_card(self.ten_diamonds)
        
        # Dealer will hit and bust (16 + 10 = 26)
        mock_deal.return_value = self.king_spades
        
        self.game.player_stand()
        
        self.assertTrue(self.game.is_game_over())
        self.assertEqual(self.game.dealer_hand.value(), 26)
        
        result = self.game.get_result()
        self.assertEqual(result.outcome, Outcome.WIN)
        self.assertTrue(result.dealer_busted)
        self.assertEqual(result.payout, 1.0)
    
    @patch('src.models.shoe.Shoe.deal_card')
    def test_player_double_win(self, mock_deal):
        """Test player doubling and winning."""
        # Set up game state: Player has 11, dealer has 6
        self.game.player_hand.add_card(self.six_clubs)
        self.game.player_hand.add_card(self.five_diamonds)
        self.game.dealer_hand.add_card(self.six_clubs)
        self.game.dealer_hand.add_card(self.ten_diamonds)
        
        # Player gets 10 (11 + 10 = 21), dealer stays at 16
        mock_deal.side_effect = [self.ten_diamonds, self.king_spades]  # Player card, then dealer bust
        
        card = self.game.player_double()
        
        self.assertEqual(card, self.ten_diamonds)
        self.assertEqual(self.game.player_hand.value(), 21)
        self.assertTrue(self.game.is_game_over())
        
        result = self.game.get_result()
        self.assertEqual(result.outcome, Outcome.WIN)
        self.assertEqual(result.payout, 2.0)  # Double bet win
    
    @patch('src.models.shoe.Shoe.deal_card')
    def test_player_double_bust(self, mock_deal):
        """Test player doubling and busting."""
        # Set up game state: Player has 12
        self.game.player_hand.add_card(self.seven_diamonds)
        self.game.player_hand.add_card(self.five_diamonds)
        self.game.dealer_hand.add_card(self.six_clubs)
        self.game.dealer_hand.add_card(self.ten_diamonds)
        
        # Player gets 10 and busts (12 + 10 = 22)
        mock_deal.return_value = self.ten_diamonds
        
        card = self.game.player_double()
        
        self.assertEqual(card, self.ten_diamonds)
        self.assertEqual(self.game.player_hand.value(), 22)
        self.assertTrue(self.game.is_game_over())
        
        result = self.game.get_result()
        self.assertEqual(result.outcome, Outcome.LOSS)
        self.assertTrue(result.player_busted)
        self.assertEqual(result.payout, -2.0)  # Double bet loss
    
    def test_player_double_cannot_double(self):
        """Test player doubling when not allowed."""
        # Set up game state with 3 cards (can't double)
        self.game.player_hand.add_card(self.two_clubs)
        self.game.player_hand.add_card(self.three_spades)
        self.game.player_hand.add_card(self.four_hearts)
        
        with self.assertRaises(RuntimeError) as context:
            self.game.player_double()
        
        self.assertIn("Cannot double", str(context.exception))
    
    def test_player_surrender(self):
        """Test player surrendering."""
        # Set up game state
        self.game.player_hand.add_card(self.ten_diamonds)
        self.game.player_hand.add_card(self.six_clubs)
        self.game.dealer_hand.add_card(self.ace_hearts)
        self.game.dealer_hand.add_card(self.king_spades)
        
        self.game.player_surrender()
        
        self.assertTrue(self.game.is_game_over())
        
        result = self.game.get_result()
        self.assertEqual(result.outcome, Outcome.SURRENDER)
        self.assertEqual(result.payout, -0.5)
        self.assertIsNone(result.dealer_total)  # Dealer hand not revealed
    
    def test_player_surrender_not_allowed(self):
        """Test player surrendering when not allowed."""
        # Disable surrender in rules
        rules = GameRules(surrender_allowed=False)
        game = BlackjackGame(rules)
        
        game.player_hand.add_card(self.ten_diamonds)
        game.player_hand.add_card(self.six_clubs)
        
        with self.assertRaises(RuntimeError) as context:
            game.player_surrender()
        
        self.assertIn("Cannot surrender", str(context.exception))
    
    def test_can_double_conditions(self):
        """Test can_double conditions."""
        # Can double with 2 cards
        self.game.player_hand.add_card(self.five_diamonds)
        self.game.player_hand.add_card(self.six_clubs)
        self.assertTrue(self.game.can_double())
        
        # Cannot double with 3 cards
        self.game.player_hand.add_card(self.four_hearts)
        self.assertFalse(self.game.can_double())
        
        # Cannot double with blackjack
        self.game.player_hand.clear()
        self.game.player_hand.add_card(self.ace_hearts)
        self.game.player_hand.add_card(self.king_spades)
        self.assertFalse(self.game.can_double())
        
        # Cannot double when game over
        self.game.game_over = True
        self.assertFalse(self.game.can_double())
    
    def test_can_split_conditions(self):
        """Test can_split conditions."""
        # Can split with pair
        self.game.player_hand.add_card(self.eight_clubs)
        self.game.player_hand.add_card(Card(Suit.HEARTS, Rank.EIGHT))
        self.assertTrue(self.game.can_split())
        
        # Can split with 10-value cards
        self.game.player_hand.clear()
        self.game.player_hand.add_card(self.king_spades)
        self.game.player_hand.add_card(self.queen_hearts)
        self.assertTrue(self.game.can_split())
        
        # Cannot split with different values
        self.game.player_hand.clear()
        self.game.player_hand.add_card(self.king_spades)
        self.game.player_hand.add_card(self.five_diamonds)
        self.assertFalse(self.game.can_split())
        
        # Cannot split with blackjack
        self.game.player_hand.clear()
        self.game.player_hand.add_card(self.ace_hearts)
        self.game.player_hand.add_card(self.king_spades)
        self.assertFalse(self.game.can_split())
        
        # Cannot split when game over
        self.game.game_over = True
        self.assertFalse(self.game.can_split())
    
    def test_can_surrender_conditions(self):
        """Test can_surrender conditions."""
        # Can surrender with 2 cards and surrender allowed
        self.game.player_hand.add_card(self.ten_diamonds)
        self.game.player_hand.add_card(self.six_clubs)
        self.assertTrue(self.game.can_surrender())
        
        # Cannot surrender with 3 cards
        self.game.player_hand.add_card(self.four_hearts)
        self.assertFalse(self.game.can_surrender())
        
        # Cannot surrender with blackjack
        self.game.player_hand.clear()
        self.game.player_hand.add_card(self.ace_hearts)
        self.game.player_hand.add_card(self.king_spades)
        self.assertFalse(self.game.can_surrender())
        
        # Cannot surrender when not allowed in rules
        rules = GameRules(surrender_allowed=False)
        game = BlackjackGame(rules)
        game.player_hand.add_card(self.ten_diamonds)
        game.player_hand.add_card(self.six_clubs)
        self.assertFalse(game.can_surrender())
    
    def test_get_available_actions(self):
        """Test getting available actions."""
        # Game not started - no actions (empty hands)
        self.assertEqual(self.game.get_available_actions(), [])
        
        # Normal situation - hit and stand always available
        self.game.player_hand.add_card(self.ten_diamonds)
        self.game.player_hand.add_card(self.six_clubs)
        self.game.dealer_hand.add_card(self.seven_diamonds)
        
        actions = self.game.get_available_actions()
        self.assertIn(Action.HIT, actions)
        self.assertIn(Action.STAND, actions)
        self.assertIn(Action.DOUBLE, actions)  # Can double with 2 cards
        self.assertIn(Action.SURRENDER, actions)  # Surrender allowed
        
        # With pair - can split
        self.game.player_hand.clear()
        self.game.player_hand.add_card(self.eight_clubs)
        self.game.player_hand.add_card(Card(Suit.HEARTS, Rank.EIGHT))
        
        actions = self.game.get_available_actions()
        self.assertIn(Action.SPLIT, actions)
        
        # Game over - no actions
        self.game.game_over = True
        self.assertEqual(self.game.get_available_actions(), [])
    
    @patch('src.models.shoe.Shoe.deal_card')
    def test_dealer_play_soft_17_hit(self, mock_deal):
        """Test dealer hitting on soft 17."""
        # Set up dealer with soft 17 (A, 6)
        self.game.dealer_hand.add_card(self.ace_hearts)
        self.game.dealer_hand.add_card(self.six_clubs)
        self.game.player_hand.add_card(self.king_spades)
        self.game.player_hand.add_card(self.nine_hearts)  # Player 19
        
        # Dealer hits soft 17 and gets 4 (A, 6, 4 = 21)
        mock_deal.return_value = self.four_hearts
        
        self.game._dealer_play()
        
        self.assertEqual(self.game.dealer_hand.value(), 21)
        self.assertEqual(self.game.dealer_hand.card_count(), 3)
    
    def test_dealer_play_soft_17_stand(self):
        """Test dealer standing on soft 17 when rule is disabled."""
        # Create game with dealer stands on soft 17
        rules = GameRules(dealer_hits_soft_17=False)
        game = BlackjackGame(rules)
        
        # Set up dealer with soft 17 (A, 6)
        game.dealer_hand.add_card(self.ace_hearts)
        game.dealer_hand.add_card(self.six_clubs)
        game.player_hand.add_card(self.king_spades)
        game.player_hand.add_card(self.nine_hearts)  # Player 19
        
        game._dealer_play()
        
        # Dealer should stand on soft 17
        self.assertEqual(game.dealer_hand.value(), 17)
        self.assertEqual(game.dealer_hand.card_count(), 2)
    
    @patch('src.models.shoe.Shoe.deal_card')
    def test_dealer_play_hits_until_17(self, mock_deal):
        """Test dealer hitting until reaching 17."""
        # Set up dealer with 12 (6, 6)
        self.game.dealer_hand.add_card(self.six_clubs)
        self.game.dealer_hand.add_card(Card(Suit.HEARTS, Rank.SIX))
        self.game.player_hand.add_card(self.king_spades)
        self.game.player_hand.add_card(self.nine_hearts)  # Player 19
        
        # Dealer hits and gets 5 (12 + 5 = 17)
        mock_deal.return_value = self.five_diamonds
        
        self.game._dealer_play()
        
        self.assertEqual(self.game.dealer_hand.value(), 17)
        self.assertEqual(self.game.dealer_hand.card_count(), 3)
    
    def test_dealer_play_player_busted(self):
        """Test dealer not playing when player busted."""
        # Set up busted player
        self.game.player_hand.add_card(self.king_spades)
        self.game.player_hand.add_card(self.queen_hearts)
        self.game.player_hand.add_card(self.five_diamonds)  # 25 - busted
        
        # Set up dealer with low total
        self.game.dealer_hand.add_card(self.two_clubs)
        self.game.dealer_hand.add_card(self.three_spades)  # 5
        
        initial_count = self.game.dealer_hand.card_count()
        self.game._dealer_play()
        
        # Dealer should not hit when player busted
        self.assertEqual(self.game.dealer_hand.card_count(), initial_count)
        self.assertEqual(self.game.dealer_hand.value(), 5)
    
    def test_reset_game(self):
        """Test resetting the game."""
        # Set up game state
        self.game.player_hand.add_card(self.king_spades)
        self.game.dealer_hand.add_card(self.ace_hearts)
        self.game.game_over = True
        self.game.result = Mock()
        
        self.game.reset()
        
        self.assertEqual(self.game.player_hand.card_count(), 0)
        self.assertEqual(self.game.dealer_hand.card_count(), 0)
        self.assertFalse(self.game.game_over)
        self.assertIsNone(self.game.result)
    
    @patch('src.models.shoe.Shoe.needs_shuffle')
    @patch('src.models.shoe.Shoe.shuffle')
    def test_reset_shuffles_if_needed(self, mock_shuffle, mock_needs_shuffle):
        """Test reset shuffles shoe if needed."""
        mock_needs_shuffle.return_value = True
        
        self.game.reset()
        
        mock_shuffle.assert_called_once()
    
    def test_string_representation(self):
        """Test string representation of game."""
        # Game not started
        self.assertEqual(str(self.game), "Game not started")
        
        # Game in progress
        self.game.player_hand.add_card(self.king_spades)
        self.game.player_hand.add_card(self.six_clubs)
        self.game.dealer_hand.add_card(self.ace_hearts)
        self.game.dealer_hand.add_card(self.ten_diamonds)
        
        game_str = str(self.game)
        self.assertIn("Player: K♠ 6♣ = 16", game_str)
        self.assertIn("Dealer: A♥ [Hidden]", game_str)
        
        # Game over
        self.game.game_over = True
        self.game.result = Mock()
        self.game.result.outcome.value = "win"
        
        game_str = str(self.game)
        self.assertIn("Player: K♠ 6♣ = 16", game_str)
        self.assertIn("Dealer: A♥ 10♦ = 21", game_str)  # Both cards shown
        self.assertIn("- Win", game_str)


if __name__ == '__main__':
    unittest.main()