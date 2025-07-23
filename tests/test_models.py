"""Unit tests for core data models."""

import unittest
import random
from src.models import Card, Suit, Rank, Shoe, Hand, GameRules, GameSituation, GameResult, Outcome


class TestCard(unittest.TestCase):
    """Test cases for the Card class."""
    
    def setUp(self):
        """Set up test cards."""
        self.ace_hearts = Card(Suit.HEARTS, Rank.ACE)
        self.king_spades = Card(Suit.SPADES, Rank.KING)
        self.five_diamonds = Card(Suit.DIAMONDS, Rank.FIVE)
        self.ten_clubs = Card(Suit.CLUBS, Rank.TEN)
    
    def test_card_creation(self):
        """Test card creation and basic properties."""
        self.assertEqual(self.ace_hearts.suit, Suit.HEARTS)
        self.assertEqual(self.ace_hearts.rank, Rank.ACE)
    
    def test_ace_value(self):
        """Test ace value calculation."""
        self.assertEqual(self.ace_hearts.value(ace_as_eleven=True), 11)
        self.assertEqual(self.ace_hearts.value(ace_as_eleven=False), 1)
    
    def test_face_card_value(self):
        """Test face card values."""
        self.assertEqual(self.king_spades.value(), 10)
        queen_hearts = Card(Suit.HEARTS, Rank.QUEEN)
        jack_clubs = Card(Suit.CLUBS, Rank.JACK)
        self.assertEqual(queen_hearts.value(), 10)
        self.assertEqual(jack_clubs.value(), 10)
    
    def test_number_card_value(self):
        """Test number card values."""
        self.assertEqual(self.five_diamonds.value(), 5)
        self.assertEqual(self.ten_clubs.value(), 10)
    
    def test_card_string_representation(self):
        """Test card string representations."""
        self.assertEqual(str(self.ace_hearts), "A♥")
        self.assertEqual(str(self.king_spades), "K♠")
        self.assertEqual(repr(self.five_diamonds), "Card(DIAMONDS, FIVE)")
    
    def test_card_equality(self):
        """Test card equality comparison."""
        ace_hearts_2 = Card(Suit.HEARTS, Rank.ACE)
        self.assertEqual(self.ace_hearts, ace_hearts_2)
        self.assertNotEqual(self.ace_hearts, self.king_spades)
    
    def test_card_hash(self):
        """Test card hashing for use in sets/dicts."""
        card_set = {self.ace_hearts, self.king_spades, self.ace_hearts}
        self.assertEqual(len(card_set), 2)  # Duplicate ace should be removed
    
    def test_count_value_placeholder(self):
        """Test count value method with placeholder implementation."""
        # Test with no system (should return 0)
        self.assertEqual(self.ace_hearts.count_value(None), 0)
        
        # Test with mock system
        class MockCountingSystem:
            def card_value(self, card):
                if card.rank == Rank.ACE:
                    return -1
                elif card.value() == 10:
                    return -1
                else:
                    return 1
        
        mock_system = MockCountingSystem()
        self.assertEqual(self.ace_hearts.count_value(mock_system), -1)
        self.assertEqual(self.king_spades.count_value(mock_system), -1)
        self.assertEqual(self.five_diamonds.count_value(mock_system), 1)


class TestHand(unittest.TestCase):
    """Test cases for the Hand class."""
    
    def setUp(self):
        """Set up test cards and hands."""
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
    
    def test_empty_hand_creation(self):
        """Test creating an empty hand."""
        hand = Hand()
        self.assertEqual(len(hand.cards), 0)
        self.assertEqual(hand.card_count(), 0)
        self.assertEqual(hand.value(), 0)
        self.assertFalse(hand.is_soft())
        self.assertFalse(hand.is_blackjack())
        self.assertFalse(hand.is_bust())
        self.assertFalse(hand.can_split())
        self.assertFalse(hand.can_double())
    
    def test_hand_creation_with_cards(self):
        """Test creating a hand with initial cards."""
        cards = [self.ace_hearts, self.king_spades]
        hand = Hand(cards)
        self.assertEqual(len(hand.cards), 2)
        self.assertEqual(hand.card_count(), 2)
        # Should not modify original list
        cards.append(self.five_diamonds)
        self.assertEqual(len(hand.cards), 2)
    
    def test_add_card(self):
        """Test adding cards to a hand."""
        hand = Hand()
        hand.add_card(self.ace_hearts)
        self.assertEqual(hand.card_count(), 1)
        self.assertEqual(hand.cards[0], self.ace_hearts)
        
        hand.add_card(self.king_spades)
        self.assertEqual(hand.card_count(), 2)
        self.assertEqual(hand.cards[1], self.king_spades)
    
    def test_hard_hand_values(self):
        """Test value calculation for hard hands."""
        # Simple hard hand
        hand = Hand([self.king_spades, self.five_diamonds])
        self.assertEqual(hand.value(), 15)
        self.assertFalse(hand.is_soft())
        
        # Hard hand with multiple cards
        hand = Hand([self.seven_diamonds, self.six_clubs, self.four_hearts])
        self.assertEqual(hand.value(), 17)
        self.assertFalse(hand.is_soft())
        
        # Hard 21
        hand = Hand([self.king_spades, self.queen_hearts, self.ace_hearts])
        self.assertEqual(hand.value(), 21)
        self.assertFalse(hand.is_soft())
    
    def test_soft_hand_values(self):
        """Test value calculation for soft hands."""
        # Soft 16 (A, 5)
        hand = Hand([self.ace_hearts, self.five_diamonds])
        self.assertEqual(hand.value(), 16)
        self.assertTrue(hand.is_soft())
        
        # Soft 18 (A, 7)
        hand = Hand([self.ace_hearts, self.seven_diamonds])
        self.assertEqual(hand.value(), 18)
        self.assertTrue(hand.is_soft())
        
        # Soft 21 (A, 10) - blackjack
        hand = Hand([self.ace_hearts, self.king_spades])
        self.assertEqual(hand.value(), 21)
        self.assertTrue(hand.is_soft())
    
    def test_ace_adjustment(self):
        """Test ace value adjustment to avoid busting."""
        # A, 6, 5 = 12 (ace becomes 1)
        hand = Hand([self.ace_hearts, self.six_clubs, self.five_diamonds])
        self.assertEqual(hand.value(), 12)
        self.assertFalse(hand.is_soft())
        
        # A, A, 9 = 21 (one ace becomes 1)
        hand = Hand([self.ace_hearts, self.ace_spades, self.nine_hearts])
        self.assertEqual(hand.value(), 21)
        self.assertTrue(hand.is_soft())  # Still has one ace as 11
        
        # A, A, A, 8 = 21 (two aces become 1)
        hand = Hand([self.ace_hearts, self.ace_spades, Card(Suit.CLUBS, Rank.ACE), self.eight_clubs])
        self.assertEqual(hand.value(), 21)
        self.assertTrue(hand.is_soft())  # Still has one ace as 11
        
        # A, A, A, A, 7 = 21 (three aces become 1)
        hand = Hand([self.ace_hearts, self.ace_spades, Card(Suit.CLUBS, Rank.ACE), Card(Suit.DIAMONDS, Rank.ACE), self.seven_diamonds])
        self.assertEqual(hand.value(), 21)
        self.assertTrue(hand.is_soft())  # Still has one ace as 11
    
    def test_bust_hands(self):
        """Test bust detection."""
        # Simple bust
        hand = Hand([self.king_spades, self.queen_hearts, self.five_diamonds])
        self.assertEqual(hand.value(), 25)
        self.assertTrue(hand.is_bust())
        self.assertFalse(hand.is_soft())
        
        # Bust with ace (all aces become 1)
        hand = Hand([self.ace_hearts, self.ace_spades, self.king_spades, self.queen_hearts])
        self.assertEqual(hand.value(), 22)
        self.assertTrue(hand.is_bust())
        self.assertFalse(hand.is_soft())
    
    def test_blackjack_detection(self):
        """Test blackjack detection."""
        # Ace-King blackjack
        hand = Hand([self.ace_hearts, self.king_spades])
        self.assertTrue(hand.is_blackjack())
        self.assertEqual(hand.value(), 21)
        self.assertTrue(hand.is_soft())
        
        # Ace-Queen blackjack
        hand = Hand([self.ace_hearts, self.queen_hearts])
        self.assertTrue(hand.is_blackjack())
        
        # Ace-Jack blackjack
        hand = Hand([self.ace_hearts, self.jack_clubs])
        self.assertTrue(hand.is_blackjack())
        
        # Ace-Ten blackjack
        hand = Hand([self.ace_hearts, self.ten_diamonds])
        self.assertTrue(hand.is_blackjack())
        
        # Not blackjack - 21 with 3 cards
        hand = Hand([self.seven_diamonds, self.seven_diamonds, self.seven_diamonds])
        self.assertFalse(hand.is_blackjack())
        self.assertEqual(hand.value(), 21)
        
        # Not blackjack - 20 with 2 cards
        hand = Hand([self.king_spades, self.queen_hearts])
        self.assertFalse(hand.is_blackjack())
        self.assertEqual(hand.value(), 20)
    
    def test_split_eligibility(self):
        """Test split eligibility detection."""
        # Same rank pairs
        hand = Hand([self.ace_hearts, self.ace_spades])
        self.assertTrue(hand.can_split())
        
        hand = Hand([self.king_spades, Card(Suit.HEARTS, Rank.KING)])
        self.assertTrue(hand.can_split())
        
        hand = Hand([self.five_diamonds, Card(Suit.CLUBS, Rank.FIVE)])
        self.assertTrue(hand.can_split())
        
        # Same value pairs (10-value cards)
        hand = Hand([self.king_spades, self.queen_hearts])
        self.assertTrue(hand.can_split())
        
        hand = Hand([self.ten_diamonds, self.jack_clubs])
        self.assertTrue(hand.can_split())
        
        hand = Hand([self.queen_hearts, self.jack_clubs])
        self.assertTrue(hand.can_split())
        
        # Not pairs
        hand = Hand([self.king_spades, self.five_diamonds])
        self.assertFalse(hand.can_split())
        
        hand = Hand([self.ace_hearts, self.two_clubs])
        self.assertFalse(hand.can_split())
        
        # More than 2 cards
        hand = Hand([self.king_spades, Card(Suit.HEARTS, Rank.KING), self.five_diamonds])
        self.assertFalse(hand.can_split())
        
        # Less than 2 cards
        hand = Hand([self.king_spades])
        self.assertFalse(hand.can_split())
    
    def test_double_eligibility(self):
        """Test double eligibility detection."""
        # Can double with exactly 2 cards
        hand = Hand([self.ace_hearts, self.king_spades])
        self.assertTrue(hand.can_double())
        
        hand = Hand([self.five_diamonds, self.six_clubs])
        self.assertTrue(hand.can_double())
        
        # Cannot double with more than 2 cards
        hand = Hand([self.five_diamonds, self.six_clubs, self.four_hearts])
        self.assertFalse(hand.can_double())
        
        # Cannot double with less than 2 cards
        hand = Hand([self.king_spades])
        self.assertFalse(hand.can_double())
        
        hand = Hand()
        self.assertFalse(hand.can_double())
    
    def test_clear_hand(self):
        """Test clearing all cards from hand."""
        hand = Hand([self.ace_hearts, self.king_spades, self.five_diamonds])
        self.assertEqual(hand.card_count(), 3)
        
        hand.clear()
        self.assertEqual(hand.card_count(), 0)
        self.assertEqual(hand.value(), 0)
        self.assertFalse(hand.is_soft())
        self.assertFalse(hand.is_blackjack())
        self.assertFalse(hand.is_bust())
    
    def test_get_cards(self):
        """Test getting a copy of cards."""
        original_cards = [self.ace_hearts, self.king_spades]
        hand = Hand(original_cards)
        
        cards_copy = hand.get_cards()
        self.assertEqual(cards_copy, original_cards)
        
        # Modifying copy should not affect hand
        cards_copy.append(self.five_diamonds)
        self.assertEqual(hand.card_count(), 2)
        self.assertNotEqual(hand.get_cards(), cards_copy)
    
    def test_string_representations(self):
        """Test string representations of hands."""
        # Empty hand
        hand = Hand()
        self.assertEqual(str(hand), "Empty hand")
        
        # Simple hard hand
        hand = Hand([self.king_spades, self.five_diamonds])
        self.assertEqual(str(hand), "K♠ 5♦ = 15")
        
        # Soft hand
        hand = Hand([self.ace_hearts, self.five_diamonds])
        self.assertEqual(str(hand), "A♥ 5♦ = 16 (soft)")
        
        # Blackjack (soft 21, no soft indicator)
        hand = Hand([self.ace_hearts, self.king_spades])
        self.assertEqual(str(hand), "A♥ K♠ = 21")
        
        # Hard 21 (no soft indicator)
        hand = Hand([self.seven_diamonds, self.seven_diamonds, self.seven_diamonds])
        self.assertEqual(str(hand), "7♦ 7♦ 7♦ = 21")
        
        # Repr
        hand = Hand([self.ace_hearts, self.king_spades])
        expected_repr = "Hand(cards=['A♥', 'K♠'], value=21)"
        self.assertEqual(repr(hand), expected_repr)
    
    def test_len_method(self):
        """Test __len__ method."""
        hand = Hand()
        self.assertEqual(len(hand), 0)
        
        hand.add_card(self.ace_hearts)
        self.assertEqual(len(hand), 1)
        
        hand.add_card(self.king_spades)
        self.assertEqual(len(hand), 2)
    
    def test_equality(self):
        """Test hand equality comparison."""
        hand1 = Hand([self.ace_hearts, self.king_spades])
        hand2 = Hand([self.ace_hearts, self.king_spades])
        hand3 = Hand([self.king_spades, self.ace_hearts])  # Different order
        hand4 = Hand([self.ace_hearts, self.queen_hearts])
        
        self.assertEqual(hand1, hand2)
        self.assertNotEqual(hand1, hand3)  # Order matters
        self.assertNotEqual(hand1, hand4)
        self.assertNotEqual(hand1, "not a hand")
    
    def test_iteration(self):
        """Test iterating over hand cards."""
        cards = [self.ace_hearts, self.king_spades, self.five_diamonds]
        hand = Hand(cards)
        
        iterated_cards = []
        for card in hand:
            iterated_cards.append(card)
        
        self.assertEqual(iterated_cards, cards)
    
    def test_edge_cases(self):
        """Test edge cases and complex scenarios."""
        # Multiple aces with various adjustments
        hand = Hand([self.ace_hearts, self.ace_spades, self.ace_hearts, self.ace_spades, self.seven_diamonds])
        self.assertEqual(hand.value(), 21)
        self.assertTrue(hand.is_soft())
        
        # All aces
        hand = Hand([self.ace_hearts, self.ace_spades, Card(Suit.CLUBS, Rank.ACE), Card(Suit.DIAMONDS, Rank.ACE)])
        self.assertEqual(hand.value(), 14)  # A, A, A, A = 1+1+1+11 = 14
        self.assertTrue(hand.is_soft())
        
        # Maximum possible hand without busting
        hand = Hand([self.ace_hearts, self.ace_spades, self.nine_hearts])
        self.assertEqual(hand.value(), 21)
        self.assertTrue(hand.is_soft())
        
        # Minimum bust
        hand = Hand([self.king_spades, self.queen_hearts, self.two_clubs])
        self.assertEqual(hand.value(), 22)
        self.assertTrue(hand.is_bust())


class TestShoe(unittest.TestCase):
    """Test cases for the Shoe class."""
    
    def setUp(self):
        """Set up test shoes."""
        # Use a fixed seed for reproducible tests
        random.seed(42)
        self.single_deck = Shoe(num_decks=1, penetration=0.75, shuffle_on_init=False)
        self.six_deck = Shoe(num_decks=6, penetration=0.75, shuffle_on_init=False)
    
    def test_shoe_creation(self):
        """Test shoe creation with different configurations."""
        # Test valid configurations
        shoe1 = Shoe(num_decks=1, penetration=0.5)
        self.assertEqual(shoe1.num_decks, 1)
        self.assertEqual(shoe1.penetration, 0.5)
        self.assertEqual(shoe1.total_cards, 52)
        
        shoe6 = Shoe(num_decks=6, penetration=0.75)
        self.assertEqual(shoe6.num_decks, 6)
        self.assertEqual(shoe6.total_cards, 312)
    
    def test_invalid_deck_count(self):
        """Test invalid deck count validation."""
        with self.assertRaises(ValueError):
            Shoe(num_decks=3)  # Invalid deck count
        with self.assertRaises(ValueError):
            Shoe(num_decks=0)  # Invalid deck count
        with self.assertRaises(ValueError):
            Shoe(num_decks=10)  # Invalid deck count
    
    def test_invalid_penetration(self):
        """Test invalid penetration validation."""
        with self.assertRaises(ValueError):
            Shoe(num_decks=6, penetration=0.05)  # Too low
        with self.assertRaises(ValueError):
            Shoe(num_decks=6, penetration=1.5)   # Too high
        with self.assertRaises(ValueError):
            Shoe(num_decks=6, penetration=0.0)   # Too low
    
    def test_deck_creation(self):
        """Test that all cards are created correctly."""
        # Single deck should have 52 cards
        self.assertEqual(len(self.single_deck.cards), 52)
        self.assertEqual(self.single_deck.cards_remaining(), 52)
        
        # Six deck should have 312 cards
        self.assertEqual(len(self.six_deck.cards), 312)
        self.assertEqual(self.six_deck.cards_remaining(), 312)
        
        # Check that we have the right number of each card
        card_counts = {}
        for card in self.six_deck.cards:
            card_key = (card.suit, card.rank)
            card_counts[card_key] = card_counts.get(card_key, 0) + 1
        
        # Each card should appear 6 times (6 decks)
        for count in card_counts.values():
            self.assertEqual(count, 6)
    
    def test_card_dealing(self):
        """Test card dealing functionality."""
        initial_count = self.single_deck.cards_remaining()
        
        # Deal a card
        card = self.single_deck.deal_card()
        self.assertIsInstance(card, Card)
        self.assertEqual(self.single_deck.cards_remaining(), initial_count - 1)
        self.assertEqual(self.single_deck.cards_dealt_count(), 1)
        
        # Deal multiple cards
        for i in range(10):
            self.single_deck.deal_card()
        
        self.assertEqual(self.single_deck.cards_remaining(), initial_count - 11)
        self.assertEqual(self.single_deck.cards_dealt_count(), 11)
    
    def test_shuffle_functionality(self):
        """Test shuffle functionality."""
        # Get initial order
        initial_order = self.single_deck.cards.copy()
        
        # Shuffle
        self.single_deck.shuffle()
        
        # Order should be different (with very high probability)
        self.assertNotEqual(self.single_deck.cards, initial_order)
        
        # Should still have same number of cards
        self.assertEqual(len(self.single_deck.cards), 52)
        
        # Cards dealt count should reset
        self.assertEqual(self.single_deck.cards_dealt_count(), 0)
    
    def test_penetration_threshold(self):
        """Test penetration threshold calculation and detection."""
        # 75% penetration of 52 cards = 39 cards
        self.assertEqual(self.single_deck.penetration_threshold, 39)
        
        # Should not need shuffle initially
        self.assertFalse(self.single_deck.needs_shuffle())
        
        # Deal cards up to threshold
        for _ in range(39):
            self.single_deck.deal_card()
        
        # Should now need shuffle
        self.assertTrue(self.single_deck.needs_shuffle())
    
    def test_shuffle_required_exception(self):
        """Test that dealing when shuffle is needed raises exception."""
        # Deal cards to penetration threshold
        for _ in range(self.single_deck.penetration_threshold):
            self.single_deck.deal_card()
        
        # Should raise exception when trying to deal more
        with self.assertRaises(RuntimeError):
            self.single_deck.deal_card()
    
    def test_empty_shoe_exception(self):
        """Test that dealing from empty shoe raises exception."""
        # Deal all cards
        while self.single_deck.cards_remaining() > 0:
            if self.single_deck.needs_shuffle():
                break
            self.single_deck.deal_card()
        
        # Manually empty the shoe to test edge case
        empty_shoe = Shoe(num_decks=1, shuffle_on_init=False)
        empty_shoe.cards = []
        
        with self.assertRaises(RuntimeError):
            empty_shoe.deal_card()
    
    def test_decks_remaining_calculation(self):
        """Test calculation of remaining decks."""
        # Full shoe should have 6 decks
        self.assertAlmostEqual(self.six_deck.decks_remaining(), 6.0, places=1)
        
        # Deal half the cards
        for _ in range(156):  # Half of 312
            self.six_deck.deal_card()
        
        # Should have approximately 3 decks remaining
        self.assertAlmostEqual(self.six_deck.decks_remaining(), 3.0, places=1)
    
    def test_reset_functionality(self):
        """Test shoe reset functionality."""
        # Deal some cards
        for _ in range(20):
            self.single_deck.deal_card()
        
        initial_remaining = self.single_deck.cards_remaining()
        self.assertLess(initial_remaining, 52)
        
        # Reset the shoe
        self.single_deck.reset()
        
        # Should be back to full deck
        self.assertEqual(self.single_deck.cards_remaining(), 52)
        self.assertEqual(self.single_deck.cards_dealt_count(), 0)
        self.assertFalse(self.single_deck.needs_shuffle())
    
    def test_string_representations(self):
        """Test string representations of shoe."""
        shoe_str = str(self.six_deck)
        self.assertIn("6 decks", shoe_str)
        self.assertIn("312/312 cards", shoe_str)
        self.assertIn("75.0% penetration", shoe_str)
        
        shoe_repr = repr(self.six_deck)
        self.assertIn("num_decks=6", shoe_repr)
        self.assertIn("penetration=0.75", shoe_repr)
        self.assertIn("cards_remaining=312", shoe_repr)
    
    def test_len_method(self):
        """Test __len__ method."""
        self.assertEqual(len(self.single_deck), 52)
        self.assertEqual(len(self.six_deck), 312)
        
        # Deal some cards and test again
        self.single_deck.deal_card()
        self.assertEqual(len(self.single_deck), 51)


class TestGameRules(unittest.TestCase):
    """Test cases for the GameRules class."""
    
    def test_default_rules(self):
        """Test default game rules."""
        rules = GameRules()
        self.assertTrue(rules.dealer_hits_soft_17)
        self.assertTrue(rules.double_after_split)
        self.assertFalse(rules.surrender_allowed)
        self.assertEqual(rules.num_decks, 6)
        self.assertEqual(rules.penetration, 0.75)
        self.assertEqual(rules.blackjack_payout, 1.5)
    
    def test_custom_rules(self):
        """Test custom game rules."""
        rules = GameRules(
            dealer_hits_soft_17=False,
            num_decks=1,
            penetration=0.5,
            blackjack_payout=1.2
        )
        self.assertFalse(rules.dealer_hits_soft_17)
        self.assertEqual(rules.num_decks, 1)
        self.assertEqual(rules.penetration, 0.5)
        self.assertEqual(rules.blackjack_payout, 1.2)
    
    def test_invalid_deck_count(self):
        """Test validation of deck count."""
        with self.assertRaises(ValueError):
            GameRules(num_decks=3)
    
    def test_invalid_penetration(self):
        """Test validation of penetration."""
        with self.assertRaises(ValueError):
            GameRules(penetration=1.5)
        with self.assertRaises(ValueError):
            GameRules(penetration=0.05)
    
    def test_invalid_payout(self):
        """Test validation of blackjack payout."""
        with self.assertRaises(ValueError):
            GameRules(blackjack_payout=-0.5)
    
    def test_total_cards(self):
        """Test total cards calculation."""
        rules = GameRules(num_decks=6)
        self.assertEqual(rules.total_cards(), 312)
    
    def test_penetration_cards(self):
        """Test penetration cards calculation."""
        rules = GameRules(num_decks=6, penetration=0.75)
        self.assertEqual(rules.penetration_cards(), 234)


class TestGameSituation(unittest.TestCase):
    """Test cases for the GameSituation class."""
    
    def setUp(self):
        """Set up test game situations."""
        self.ace_hearts = Card(Suit.HEARTS, Rank.ACE)
        self.king_spades = Card(Suit.SPADES, Rank.KING)
        self.five_diamonds = Card(Suit.DIAMONDS, Rank.FIVE)
        self.six_clubs = Card(Suit.CLUBS, Rank.SIX)
        self.ten_hearts = Card(Suit.HEARTS, Rank.TEN)
    
    def test_hard_hand_total(self):
        """Test hard hand total calculation."""
        situation = GameSituation(
            player_cards=[self.king_spades, self.five_diamonds],
            dealer_up_card=self.six_clubs
        )
        self.assertEqual(situation.player_total(), 15)
        self.assertFalse(situation.is_soft_hand())
    
    def test_soft_hand_total(self):
        """Test soft hand total calculation."""
        situation = GameSituation(
            player_cards=[self.ace_hearts, self.five_diamonds],
            dealer_up_card=self.six_clubs
        )
        self.assertEqual(situation.player_total(), 16)
        self.assertTrue(situation.is_soft_hand())
    
    def test_bust_hand_with_ace(self):
        """Test hand that busts even with ace adjustment."""
        situation = GameSituation(
            player_cards=[self.ace_hearts, self.king_spades, self.five_diamonds, self.six_clubs],
            dealer_up_card=self.ten_hearts
        )
        self.assertEqual(situation.player_total(), 22)
        self.assertFalse(situation.is_soft_hand())
    
    def test_blackjack_detection(self):
        """Test blackjack detection."""
        situation = GameSituation(
            player_cards=[self.ace_hearts, self.king_spades],
            dealer_up_card=self.five_diamonds,
            is_first_decision=True
        )
        self.assertTrue(situation.is_blackjack())
        self.assertEqual(situation.player_total(), 21)
    
    def test_pair_detection(self):
        """Test pair detection for splitting."""
        # Same rank pair
        situation = GameSituation(
            player_cards=[self.king_spades, Card(Suit.HEARTS, Rank.KING)],
            dealer_up_card=self.five_diamonds
        )
        self.assertTrue(situation.is_pair())
        
        # Same value pair (10 and King)
        situation2 = GameSituation(
            player_cards=[self.ten_hearts, self.king_spades],
            dealer_up_card=self.five_diamonds
        )
        self.assertTrue(situation2.is_pair())
        
        # Not a pair
        situation3 = GameSituation(
            player_cards=[self.king_spades, self.five_diamonds],
            dealer_up_card=self.six_clubs
        )
        self.assertFalse(situation3.is_pair())
    
    def test_string_representation(self):
        """Test string representation of game situation."""
        situation = GameSituation(
            player_cards=[self.king_spades, self.five_diamonds],
            dealer_up_card=self.six_clubs
        )
        expected = "Player: K♠ 5♦ (15) vs Dealer: 6♣"
        self.assertEqual(str(situation), expected)


class TestGameResult(unittest.TestCase):
    """Test cases for the GameResult class."""
    
    def test_win_result(self):
        """Test winning game result."""
        result = GameResult(
            outcome=Outcome.WIN,
            player_total=20,
            dealer_total=19
        )
        self.assertTrue(result.is_winning_result())
        self.assertFalse(result.is_losing_result())
        self.assertEqual(result.payout, 1.0)
        self.assertEqual(result.net_result(10.0), 10.0)
    
    def test_loss_result(self):
        """Test losing game result."""
        result = GameResult(
            outcome=Outcome.LOSS,
            player_total=22,
            dealer_total=20,
            player_busted=True
        )
        self.assertFalse(result.is_winning_result())
        self.assertTrue(result.is_losing_result())
        self.assertEqual(result.payout, -1.0)
        self.assertEqual(result.net_result(10.0), -10.0)
    
    def test_blackjack_result(self):
        """Test blackjack result."""
        result = GameResult(
            outcome=Outcome.BLACKJACK,
            player_total=21,
            dealer_total=20,
            player_blackjack=True
        )
        self.assertTrue(result.is_winning_result())
        self.assertEqual(result.payout, 1.5)
        self.assertEqual(result.net_result(10.0), 15.0)
    
    def test_push_result(self):
        """Test push (tie) result."""
        result = GameResult(
            outcome=Outcome.PUSH,
            player_total=20,
            dealer_total=20
        )
        self.assertFalse(result.is_winning_result())
        self.assertFalse(result.is_losing_result())
        self.assertEqual(result.payout, 0.0)
        self.assertEqual(result.net_result(10.0), 0.0)
    
    def test_surrender_result(self):
        """Test surrender result."""
        result = GameResult(
            outcome=Outcome.SURRENDER,
            player_total=16,
            dealer_total=None
        )
        self.assertFalse(result.is_winning_result())
        self.assertTrue(result.is_losing_result())
        self.assertEqual(result.payout, -0.5)
        self.assertEqual(result.net_result(10.0), -5.0)
    
    def test_string_representation(self):
        """Test string representation of game result."""
        result = GameResult(
            outcome=Outcome.WIN,
            player_total=20,
            dealer_total=19,
            payout=1.0
        )
        expected = "Win: Player 20 vs Dealer 19 (Payout: +1.0)"
        self.assertEqual(str(result), expected)
        
        # Test surrender (no dealer total)
        surrender_result = GameResult(
            outcome=Outcome.SURRENDER,
            player_total=16,
            payout=-0.5
        )
        expected_surrender = "Surrender: Player 16 (Payout: -0.5)"
        self.assertEqual(str(surrender_result), expected_surrender)


if __name__ == '__main__':
    unittest.main()
        