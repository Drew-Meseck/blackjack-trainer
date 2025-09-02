"""Unit tests for card counting systems."""

import unittest
from src.models.card import Card, Suit, Rank
from src.counting import (
    CountingSystem, HiLoSystem, KOSystem, HiOptISystem, 
    CardCounter, CountingSystemManager
)


class TestHiLoSystem(unittest.TestCase):
    """Test cases for Hi-Lo counting system."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.hi_lo = HiLoSystem()
    
    def test_name(self):
        """Test that the system returns correct name."""
        self.assertEqual(self.hi_lo.name(), "Hi-Lo")
        self.assertEqual(str(self.hi_lo), "Hi-Lo")
    
    def test_low_cards_value(self):
        """Test that low cards (2-6) return +1."""
        low_cards = [
            Card(Suit.HEARTS, Rank.TWO),
            Card(Suit.DIAMONDS, Rank.THREE),
            Card(Suit.CLUBS, Rank.FOUR),
            Card(Suit.SPADES, Rank.FIVE),
            Card(Suit.HEARTS, Rank.SIX)
        ]
        
        for card in low_cards:
            with self.subTest(card=card):
                self.assertEqual(self.hi_lo.card_value(card), 1)
    
    def test_neutral_cards_value(self):
        """Test that neutral cards (7-9) return 0."""
        neutral_cards = [
            Card(Suit.HEARTS, Rank.SEVEN),
            Card(Suit.DIAMONDS, Rank.EIGHT),
            Card(Suit.CLUBS, Rank.NINE)
        ]
        
        for card in neutral_cards:
            with self.subTest(card=card):
                self.assertEqual(self.hi_lo.card_value(card), 0)
    
    def test_high_cards_value(self):
        """Test that high cards (10, J, Q, K, A) return -1."""
        high_cards = [
            Card(Suit.HEARTS, Rank.TEN),
            Card(Suit.DIAMONDS, Rank.JACK),
            Card(Suit.CLUBS, Rank.QUEEN),
            Card(Suit.SPADES, Rank.KING),
            Card(Suit.HEARTS, Rank.ACE)
        ]
        
        for card in high_cards:
            with self.subTest(card=card):
                self.assertEqual(self.hi_lo.card_value(card), -1)
    
    def test_all_cards_coverage(self):
        """Test that all card ranks have defined values."""
        for rank in Rank:
            card = Card(Suit.HEARTS, rank)
            value = self.hi_lo.card_value(card)
            self.assertIn(value, [-1, 0, 1], f"Card {card} should have value -1, 0, or 1")


class TestCardCounter(unittest.TestCase):
    """Test cases for CardCounter class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.hi_lo = HiLoSystem()
        self.counter = CardCounter(self.hi_lo, num_decks=6)
    
    def test_initial_state(self):
        """Test initial counter state."""
        self.assertEqual(self.counter.running_count(), 0)
        self.assertEqual(self.counter.cards_seen(), 0)
        self.assertEqual(self.counter.remaining_decks(), 6.0)
        self.assertEqual(self.counter.true_count(), 0.0)
    
    def test_update_count_single_card(self):
        """Test updating count with a single card."""
        # Add a low card (+1)
        card = Card(Suit.HEARTS, Rank.FIVE)
        self.counter.update_count(card)
        
        self.assertEqual(self.counter.running_count(), 1)
        self.assertEqual(self.counter.cards_seen(), 1)
    
    def test_update_count_multiple_cards(self):
        """Test updating count with multiple cards."""
        cards = [
            Card(Suit.HEARTS, Rank.FIVE),    # +1
            Card(Suit.DIAMONDS, Rank.KING),  # -1
            Card(Suit.CLUBS, Rank.EIGHT),    # 0
            Card(Suit.SPADES, Rank.THREE)    # +1
        ]
        
        for card in cards:
            self.counter.update_count(card)
        
        self.assertEqual(self.counter.running_count(), 1)  # +1 -1 +0 +1 = 1
        self.assertEqual(self.counter.cards_seen(), 4)
    
    def test_true_count_calculation(self):
        """Test true count calculation."""
        # Add 52 cards (1 deck worth) with running count of +6
        cards = [Card(Suit.HEARTS, Rank.TWO)] * 6  # 6 low cards = +6
        for card in cards:
            self.counter.update_count(card)
        
        # After 6 cards, we have 6*52-6 = 306 cards remaining = 5.88 decks
        expected_remaining_decks = (6 * 52 - 6) / 52
        expected_true_count = 6 / expected_remaining_decks
        
        self.assertAlmostEqual(self.counter.true_count(), expected_true_count, places=2)
        self.assertAlmostEqual(self.counter.remaining_decks(), expected_remaining_decks, places=2)
    
    def test_true_count_with_full_deck_seen(self):
        """Test true count when a full deck has been seen."""
        # Simulate seeing 52 cards
        for _ in range(52):
            self.counter.update_count(Card(Suit.HEARTS, Rank.SEVEN))  # Neutral cards
        
        # Should have 5 decks remaining
        self.assertAlmostEqual(self.counter.remaining_decks(), 5.0, places=1)
    
    def test_true_count_edge_case_no_cards_remaining(self):
        """Test true count when no cards remain (edge case)."""
        # Simulate seeing all cards
        for _ in range(6 * 52):
            self.counter.update_count(Card(Suit.HEARTS, Rank.SEVEN))
        
        # Should return 0 to avoid division by zero
        self.assertEqual(self.counter.true_count(), 0.0)
    
    def test_reset_functionality(self):
        """Test that reset clears all counts."""
        # Add some cards
        cards = [Card(Suit.HEARTS, Rank.FIVE)] * 5
        for card in cards:
            self.counter.update_count(card)
        
        # Verify counts are non-zero
        self.assertNotEqual(self.counter.running_count(), 0)
        self.assertNotEqual(self.counter.cards_seen(), 0)
        
        # Reset and verify
        self.counter.reset()
        self.assertEqual(self.counter.running_count(), 0)
        self.assertEqual(self.counter.cards_seen(), 0)
        self.assertEqual(self.counter.true_count(), 0.0)
    
    def test_different_deck_counts(self):
        """Test counter with different deck counts."""
        # Test with single deck
        single_deck_counter = CardCounter(self.hi_lo, num_decks=1)
        self.assertEqual(single_deck_counter.remaining_decks(), 1.0)
        
        # Test with 8 decks
        eight_deck_counter = CardCounter(self.hi_lo, num_decks=8)
        self.assertEqual(eight_deck_counter.remaining_decks(), 8.0)
    
    def test_string_representation(self):
        """Test string representation of counter."""
        # Add a card to make it more interesting
        self.counter.update_count(Card(Suit.HEARTS, Rank.FIVE))
        
        str_repr = str(self.counter)
        self.assertIn("CardCounter", str_repr)
        self.assertIn("Hi-Lo", str_repr)
        self.assertIn("RC=1", str_repr)
        self.assertIn("TC=", str_repr)
    
    def test_balanced_count_sequence(self):
        """Test a balanced sequence that should return to zero."""
        # Create a balanced sequence: equal high and low cards
        balanced_cards = [
            Card(Suit.HEARTS, Rank.TWO),    # +1
            Card(Suit.DIAMONDS, Rank.ACE),  # -1
            Card(Suit.CLUBS, Rank.FIVE),    # +1
            Card(Suit.SPADES, Rank.KING),   # -1
            Card(Suit.HEARTS, Rank.EIGHT)   # 0
        ]
        
        for card in balanced_cards:
            self.counter.update_count(card)
        
        self.assertEqual(self.counter.running_count(), 0)
    
    def test_extreme_positive_count(self):
        """Test handling of extreme positive counts."""
        # Add many low cards
        for _ in range(20):
            self.counter.update_count(Card(Suit.HEARTS, Rank.TWO))
        
        self.assertEqual(self.counter.running_count(), 20)
        self.assertTrue(self.counter.true_count() > 0)
    
    def test_extreme_negative_count(self):
        """Test handling of extreme negative counts."""
        # Add many high cards
        for _ in range(20):
            self.counter.update_count(Card(Suit.HEARTS, Rank.ACE))
        
        self.assertEqual(self.counter.running_count(), -20)
        self.assertTrue(self.counter.true_count() < 0)


if __name__ == '__main__':
    unittest.main()


class TestKOSystem(unittest.TestCase):
    """Test cases for KO (Knock-Out) counting system."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.ko = KOSystem()
    
    def test_name(self):
        """Test that the system returns correct name."""
        self.assertEqual(self.ko.name(), "KO")
        self.assertEqual(str(self.ko), "KO")
    
    def test_low_cards_value(self):
        """Test that low cards (2-7) return +1."""
        low_cards = [
            Card(Suit.HEARTS, Rank.TWO),
            Card(Suit.DIAMONDS, Rank.THREE),
            Card(Suit.CLUBS, Rank.FOUR),
            Card(Suit.SPADES, Rank.FIVE),
            Card(Suit.HEARTS, Rank.SIX),
            Card(Suit.DIAMONDS, Rank.SEVEN)  # 7 is +1 in KO, unlike Hi-Lo
        ]
        
        for card in low_cards:
            with self.subTest(card=card):
                self.assertEqual(self.ko.card_value(card), 1)
    
    def test_neutral_cards_value(self):
        """Test that neutral cards (8-9) return 0."""
        neutral_cards = [
            Card(Suit.HEARTS, Rank.EIGHT),
            Card(Suit.DIAMONDS, Rank.NINE)
        ]
        
        for card in neutral_cards:
            with self.subTest(card=card):
                self.assertEqual(self.ko.card_value(card), 0)
    
    def test_high_cards_value(self):
        """Test that high cards (10, J, Q, K, A) return -1."""
        high_cards = [
            Card(Suit.HEARTS, Rank.TEN),
            Card(Suit.DIAMONDS, Rank.JACK),
            Card(Suit.CLUBS, Rank.QUEEN),
            Card(Suit.SPADES, Rank.KING),
            Card(Suit.HEARTS, Rank.ACE)
        ]
        
        for card in high_cards:
            with self.subTest(card=card):
                self.assertEqual(self.ko.card_value(card), -1)
    
    def test_seven_difference_from_hi_lo(self):
        """Test that 7 is counted differently than Hi-Lo."""
        seven = Card(Suit.HEARTS, Rank.SEVEN)
        hi_lo = HiLoSystem()
        
        # In KO, 7 should be +1
        self.assertEqual(self.ko.card_value(seven), 1)
        # In Hi-Lo, 7 should be 0
        self.assertEqual(hi_lo.card_value(seven), 0)
    
    def test_unbalanced_nature(self):
        """Test that KO is unbalanced (doesn't sum to 0 for full deck)."""
        total = 0
        for rank in Rank:
            card = Card(Suit.HEARTS, rank)
            total += self.ko.card_value(card) * 4  # 4 cards of each rank
        
        # KO should not sum to 0 (it's unbalanced)
        self.assertNotEqual(total, 0)
        # Should be positive due to extra +1 for 7s
        self.assertGreater(total, 0)


class TestHiOptISystem(unittest.TestCase):
    """Test cases for Hi-Opt I counting system."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.hi_opt_i = HiOptISystem()
    
    def test_name(self):
        """Test that the system returns correct name."""
        self.assertEqual(self.hi_opt_i.name(), "Hi-Opt I")
        self.assertEqual(str(self.hi_opt_i), "Hi-Opt I")
    
    def test_low_cards_value(self):
        """Test that low cards (3-6) return +1."""
        low_cards = [
            Card(Suit.DIAMONDS, Rank.THREE),
            Card(Suit.CLUBS, Rank.FOUR),
            Card(Suit.SPADES, Rank.FIVE),
            Card(Suit.HEARTS, Rank.SIX)
        ]
        
        for card in low_cards:
            with self.subTest(card=card):
                self.assertEqual(self.hi_opt_i.card_value(card), 1)
    
    def test_neutral_cards_value(self):
        """Test that neutral cards (2, 7-9, A) return 0."""
        neutral_cards = [
            Card(Suit.HEARTS, Rank.TWO),    # 2 is neutral in Hi-Opt I
            Card(Suit.HEARTS, Rank.SEVEN),
            Card(Suit.DIAMONDS, Rank.EIGHT),
            Card(Suit.CLUBS, Rank.NINE),
            Card(Suit.SPADES, Rank.ACE)     # A is neutral in Hi-Opt I
        ]
        
        for card in neutral_cards:
            with self.subTest(card=card):
                self.assertEqual(self.hi_opt_i.card_value(card), 0)
    
    def test_high_cards_value(self):
        """Test that high cards (10, J, Q, K) return -1."""
        high_cards = [
            Card(Suit.HEARTS, Rank.TEN),
            Card(Suit.DIAMONDS, Rank.JACK),
            Card(Suit.CLUBS, Rank.QUEEN),
            Card(Suit.SPADES, Rank.KING)
        ]
        
        for card in high_cards:
            with self.subTest(card=card):
                self.assertEqual(self.hi_opt_i.card_value(card), -1)
    
    def test_ace_and_two_neutral(self):
        """Test that Aces and 2s are neutral (different from Hi-Lo)."""
        ace = Card(Suit.HEARTS, Rank.ACE)
        two = Card(Suit.HEARTS, Rank.TWO)
        hi_lo = HiLoSystem()
        
        # In Hi-Opt I, both should be 0
        self.assertEqual(self.hi_opt_i.card_value(ace), 0)
        self.assertEqual(self.hi_opt_i.card_value(two), 0)
        
        # In Hi-Lo, they should be different
        self.assertEqual(hi_lo.card_value(ace), -1)
        self.assertEqual(hi_lo.card_value(two), 1)
    
    def test_balanced_nature(self):
        """Test that Hi-Opt I is balanced (sums to 0 for full deck)."""
        total = 0
        for rank in Rank:
            card = Card(Suit.HEARTS, rank)
            total += self.hi_opt_i.card_value(card) * 4  # 4 cards of each rank
        
        # Hi-Opt I should sum to 0 (it's balanced)
        self.assertEqual(total, 0)


class TestCountingSystemManager(unittest.TestCase):
    """Test cases for CountingSystemManager."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.manager = CountingSystemManager()
    
    def test_default_systems_registered(self):
        """Test that default systems are registered."""
        expected_systems = ["Hi-Lo", "KO", "Hi-Opt I"]
        available_systems = self.manager.list_systems()
        
        for system in expected_systems:
            self.assertIn(system, available_systems)
    
    def test_get_system(self):
        """Test getting systems by name."""
        hi_lo = self.manager.get_system("Hi-Lo")
        self.assertIsInstance(hi_lo, HiLoSystem)
        
        ko = self.manager.get_system("KO")
        self.assertIsInstance(ko, KOSystem)
        
        hi_opt_i = self.manager.get_system("Hi-Opt I")
        self.assertIsInstance(hi_opt_i, HiOptISystem)
    
    def test_get_nonexistent_system(self):
        """Test getting a system that doesn't exist."""
        result = self.manager.get_system("NonExistent")
        self.assertIsNone(result)
    
    def test_get_default_system(self):
        """Test getting the default system."""
        default = self.manager.get_default_system()
        self.assertIsInstance(default, HiLoSystem)
        self.assertEqual(default.name(), "Hi-Lo")
    
    def test_is_system_available(self):
        """Test checking system availability."""
        self.assertTrue(self.manager.is_system_available("Hi-Lo"))
        self.assertTrue(self.manager.is_system_available("KO"))
        self.assertTrue(self.manager.is_system_available("Hi-Opt I"))
        self.assertFalse(self.manager.is_system_available("NonExistent"))
    
    def test_register_custom_system(self):
        """Test registering a custom system."""
        # Create a mock system
        class MockSystem(CountingSystem):
            def card_value(self, card):
                return 0
            def name(self):
                return "Mock"
        
        mock_system = MockSystem()
        initial_count = len(self.manager)
        
        self.manager.register_system(mock_system)
        
        self.assertEqual(len(self.manager), initial_count + 1)
        self.assertTrue(self.manager.is_system_available("Mock"))
        self.assertIsInstance(self.manager.get_system("Mock"), MockSystem)
    
    def test_manager_length(self):
        """Test manager length."""
        # Should have 3 default systems
        self.assertEqual(len(self.manager), 3)
    
    def test_manager_iteration(self):
        """Test iterating over systems."""
        systems = list(self.manager)
        self.assertEqual(len(systems), 3)
        
        system_names = [system.name() for system in systems]
        expected_names = ["Hi-Lo", "KO", "Hi-Opt I"]
        
        for name in expected_names:
            self.assertIn(name, system_names)
    
    def test_string_representation(self):
        """Test string representation of manager."""
        str_repr = str(self.manager)
        self.assertIn("CountingSystemManager", str_repr)
        self.assertIn("Hi-Lo", str_repr)
        self.assertIn("KO", str_repr)
        self.assertIn("Hi-Opt I", str_repr)


class TestSystemSwitching(unittest.TestCase):
    """Test cases for switching between counting systems."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.manager = CountingSystemManager()
    
    def test_counter_with_different_systems(self):
        """Test CardCounter with different counting systems."""
        # Test with Hi-Lo
        hi_lo = self.manager.get_system("Hi-Lo")
        hi_lo_counter = CardCounter(hi_lo, num_decks=6)
        
        # Test with KO
        ko = self.manager.get_system("KO")
        ko_counter = CardCounter(ko, num_decks=6)
        
        # Test with Hi-Opt I
        hi_opt_i = self.manager.get_system("Hi-Opt I")
        hi_opt_i_counter = CardCounter(hi_opt_i, num_decks=6)
        
        # Test with a 7 (different values in different systems)
        seven = Card(Suit.HEARTS, Rank.SEVEN)
        
        hi_lo_counter.update_count(seven)
        ko_counter.update_count(seven)
        hi_opt_i_counter.update_count(seven)
        
        # Hi-Lo: 7 = 0
        self.assertEqual(hi_lo_counter.running_count(), 0)
        # KO: 7 = +1
        self.assertEqual(ko_counter.running_count(), 1)
        # Hi-Opt I: 7 = 0
        self.assertEqual(hi_opt_i_counter.running_count(), 0)
    
    def test_system_comparison_with_ace(self):
        """Test different systems with Ace cards."""
        hi_lo = self.manager.get_system("Hi-Lo")
        hi_opt_i = self.manager.get_system("Hi-Opt I")
        
        ace = Card(Suit.HEARTS, Rank.ACE)
        
        # Hi-Lo: A = -1
        self.assertEqual(hi_lo.card_value(ace), -1)
        # Hi-Opt I: A = 0
        self.assertEqual(hi_opt_i.card_value(ace), 0)
    
    def test_system_comparison_with_two(self):
        """Test different systems with 2 cards."""
        hi_lo = self.manager.get_system("Hi-Lo")
        hi_opt_i = self.manager.get_system("Hi-Opt I")
        
        two = Card(Suit.HEARTS, Rank.TWO)
        
        # Hi-Lo: 2 = +1
        self.assertEqual(hi_lo.card_value(two), 1)
        # Hi-Opt I: 2 = 0
        self.assertEqual(hi_opt_i.card_value(two), 0)