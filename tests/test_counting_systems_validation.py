"""Comprehensive tests for all counting systems with various game configurations."""

import unittest
from unittest.mock import patch
from typing import List, Dict, Any

from src.models import GameRules, Card, Suit, Rank
from src.counting import (
    CountingSystemManager, HiLoSystem, KOSystem, HiOptISystem,
    CardCounter, CountingSystem
)
from src.game import CountingBlackjackGame


class TestAllCountingSystems(unittest.TestCase):
    """Test all counting systems with various game configurations."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.manager = CountingSystemManager()
        self.all_systems = [
            self.manager.get_system("Hi-Lo"),
            self.manager.get_system("KO"),
            self.manager.get_system("Hi-Opt I")
        ]
        
        # Test configurations
        self.test_configs = [
            GameRules(num_decks=1, penetration=0.5),
            GameRules(num_decks=2, penetration=0.75),
            GameRules(num_decks=6, penetration=0.8),
            GameRules(num_decks=8, penetration=0.6)
        ]
    
    def test_all_systems_card_values(self):
        """Test card value assignments for all counting systems."""
        # Define expected values for each system
        expected_values = {
            "Hi-Lo": {
                Rank.TWO: 1, Rank.THREE: 1, Rank.FOUR: 1, Rank.FIVE: 1, Rank.SIX: 1,
                Rank.SEVEN: 0, Rank.EIGHT: 0, Rank.NINE: 0,
                Rank.TEN: -1, Rank.JACK: -1, Rank.QUEEN: -1, Rank.KING: -1, Rank.ACE: -1
            },
            "KO": {
                Rank.TWO: 1, Rank.THREE: 1, Rank.FOUR: 1, Rank.FIVE: 1, Rank.SIX: 1, Rank.SEVEN: 1,
                Rank.EIGHT: 0, Rank.NINE: 0,
                Rank.TEN: -1, Rank.JACK: -1, Rank.QUEEN: -1, Rank.KING: -1, Rank.ACE: -1
            },
            "Hi-Opt I": {
                Rank.TWO: 0, Rank.THREE: 1, Rank.FOUR: 1, Rank.FIVE: 1, Rank.SIX: 1,
                Rank.SEVEN: 0, Rank.EIGHT: 0, Rank.NINE: 0,
                Rank.TEN: -1, Rank.JACK: -1, Rank.QUEEN: -1, Rank.KING: -1, Rank.ACE: 0
            }
        }
        
        for system in self.all_systems:
            system_name = system.name()
            expected = expected_values[system_name]
            
            for rank in Rank:
                card = Card(Suit.HEARTS, rank)
                actual_value = system.card_value(card)
                expected_value = expected[rank]
                
                self.assertEqual(
                    actual_value, expected_value,
                    f"{system_name} system: {rank} should be {expected_value}, got {actual_value}"
                )
    
    def test_systems_with_different_deck_counts(self):
        """Test all counting systems with different deck configurations."""
        test_cards = [
            Card(Suit.HEARTS, Rank.FIVE),    # +1 in Hi-Lo and KO, +1 in Hi-Opt I
            Card(Suit.DIAMONDS, Rank.KING),  # -1 in Hi-Lo and KO, -1 in Hi-Opt I
            Card(Suit.CLUBS, Rank.ACE),      # -1 in Hi-Lo and KO, 0 in Hi-Opt I
            Card(Suit.SPADES, Rank.SEVEN),   # 0 in Hi-Lo, +1 in KO, 0 in Hi-Opt I
            Card(Suit.HEARTS, Rank.TWO)      # +1 in Hi-Lo and KO, 0 in Hi-Opt I
        ]
        
        for rules in self.test_configs:
            for system in self.all_systems:
                counter = CardCounter(system, rules.num_decks)
                
                # Process test cards
                for card in test_cards:
                    counter.update_count(card)
                
                # Verify running count calculation
                expected_running = sum(system.card_value(card) for card in test_cards)
                self.assertEqual(counter.running_count(), expected_running)
                
                # Verify true count calculation
                expected_true = expected_running / counter.remaining_decks()
                self.assertAlmostEqual(counter.true_count(), expected_true, places=2)
                
                # Verify cards seen
                self.assertEqual(counter.cards_seen(), len(test_cards))
    
    def test_counting_accuracy_across_systems(self):
        """Test counting accuracy across different systems during gameplay."""
        for rules in self.test_configs:
            for system in self.all_systems:
                game = CountingBlackjackGame(rules, system)
                
                # Define a sequence of cards that will test the system
                card_sequence = [
                    # Initial deal
                    Card(Suit.HEARTS, Rank.TEN),     # Player
                    Card(Suit.DIAMONDS, Rank.SIX),   # Dealer face up
                    Card(Suit.CLUBS, Rank.FIVE),     # Player
                    Card(Suit.SPADES, Rank.KING),    # Dealer hole (not counted initially)
                    
                    # Player hits
                    Card(Suit.HEARTS, Rank.THREE),   # Player hit
                    Card(Suit.DIAMONDS, Rank.TWO),   # Player hit
                    
                    # Dealer reveals and hits
                    Card(Suit.CLUBS, Rank.SEVEN)     # Dealer hit
                ]
                
                with patch.object(game.shoe, 'deal_card') as mock_deal:
                    mock_deal.side_effect = card_sequence
                    
                    # Deal initial cards (first 3 cards counted: player cards + dealer face up)
                    game.deal_initial_cards()
                    initial_count = game.get_running_count()
                    
                    # Calculate expected count for first 3 cards
                    counted_cards = card_sequence[:3]  # Player 10, Dealer 6, Player 5
                    expected_initial = sum(system.card_value(card) for card in counted_cards)
                    self.assertEqual(initial_count, expected_initial)
                    
                    # Player hits twice
                    game.player_hit()  # Gets 3
                    game.player_hit()  # Gets 2
                    
                    # Player stands (dealer reveals hole card and hits)
                    game.player_stand()
                    
                    # Final count should include all revealed cards
                    final_count = game.get_running_count()
                    all_revealed = card_sequence  # All cards should be revealed
                    expected_final = sum(system.card_value(card) for card in all_revealed)
                    self.assertEqual(final_count, expected_final)
    
    def test_system_switching_during_game(self):
        """Test switching between counting systems during gameplay."""
        rules = GameRules(num_decks=6)
        game = CountingBlackjackGame(rules, self.all_systems[0])  # Start with Hi-Lo
        
        # Deal some cards
        with patch.object(game.shoe, 'deal_card') as mock_deal:
            mock_deal.side_effect = [
                Card(Suit.HEARTS, Rank.FIVE),    # +1 in Hi-Lo
                Card(Suit.DIAMONDS, Rank.KING),  # -1 in Hi-Lo
                Card(Suit.CLUBS, Rank.SIX),      # +1 in Hi-Lo
                Card(Suit.SPADES, Rank.SEVEN)    # 0 in Hi-Lo
            ]
            
            game.deal_initial_cards()
            hi_lo_count = game.get_running_count()  # Should be +1
            
            # Switch to KO system
            ko_system = self.manager.get_system("KO")
            game.switch_counting_system(ko_system)
            
            # Count should be reset
            self.assertEqual(game.get_running_count(), 0)
            self.assertEqual(game.get_counting_system_name(), "KO")
            
            # Switch to Hi-Opt I
            hi_opt_system = self.manager.get_system("Hi-Opt I")
            game.switch_counting_system(hi_opt_system)
            
            self.assertEqual(game.get_running_count(), 0)
            self.assertEqual(game.get_counting_system_name(), "Hi-Opt I")
    
    def test_true_count_accuracy_all_systems(self):
        """Test true count accuracy for all systems with different penetrations."""
        test_scenarios = [
            # (cards_dealt, num_decks, expected_remaining_decks)
            (52, 1, 0.0),      # Full single deck
            (52, 2, 1.0),      # Half of double deck
            (156, 6, 3.0),     # Half of 6-deck shoe
            (208, 8, 4.0)      # Half of 8-deck shoe
        ]
        
        for system in self.all_systems:
            for cards_dealt, num_decks, expected_remaining in test_scenarios:
                counter = CardCounter(system, num_decks)
                
                # Simulate cards being dealt
                for _ in range(cards_dealt):
                    # Use neutral cards to focus on deck calculation
                    card = Card(Suit.HEARTS, Rank.SEVEN if system.name() != "KO" else Rank.EIGHT)
                    counter.update_count(card)
                
                # Check remaining deck calculation
                self.assertAlmostEqual(counter.remaining_decks(), expected_remaining, places=1)
                
                # If there's a running count, verify true count calculation
                if counter.running_count() != 0 and expected_remaining > 0:
                    expected_true = counter.running_count() / expected_remaining
                    self.assertAlmostEqual(counter.true_count(), expected_true, places=2)
    
    def test_system_performance_comparison(self):
        """Compare performance characteristics of different counting systems."""
        # Test with a standardized deck sequence
        full_deck_sequence = []
        for suit in Suit:
            for rank in Rank:
                full_deck_sequence.append(Card(suit, rank))
        
        system_results = {}
        
        for system in self.all_systems:
            counter = CardCounter(system, 1)  # Single deck for comparison
            
            running_counts = []
            for card in full_deck_sequence:
                counter.update_count(card)
                running_counts.append(counter.running_count())
            
            system_results[system.name()] = {
                'final_count': counter.running_count(),
                'max_count': max(running_counts),
                'min_count': min(running_counts),
                'count_range': max(running_counts) - min(running_counts)
            }
        
        # Verify balanced systems return to 0 after full deck
        balanced_systems = ["Hi-Lo", "Hi-Opt I"]
        for system_name in balanced_systems:
            self.assertEqual(
                system_results[system_name]['final_count'], 0,
                f"{system_name} should be balanced (return to 0 after full deck)"
            )
        
        # KO is unbalanced, should not return to 0
        self.assertNotEqual(
            system_results["KO"]['final_count'], 0,
            "KO should be unbalanced (not return to 0 after full deck)"
        )
    
    def test_edge_cases_all_systems(self):
        """Test edge cases for all counting systems."""
        for system in self.all_systems:
            # Test with minimum deck count
            counter_1_deck = CardCounter(system, 1)
            
            # Test with maximum typical deck count
            counter_8_deck = CardCounter(system, 8)
            
            # Test reset functionality
            test_card = Card(Suit.HEARTS, Rank.FIVE)
            counter_1_deck.update_count(test_card)
            self.assertNotEqual(counter_1_deck.running_count(), 0)
            
            counter_1_deck.reset()
            self.assertEqual(counter_1_deck.running_count(), 0)
            self.assertEqual(counter_1_deck.cards_seen(), 0)
            
            # Test true count with very few cards remaining
            # Deal almost all cards to simulate near-empty shoe
            for _ in range(410):  # Almost full 8-deck shoe (416 cards total)
                counter_8_deck.update_count(Card(Suit.HEARTS, Rank.SEVEN))
            
            # Add multiple non-neutral cards to create a significant running count
            for _ in range(5):
                counter_8_deck.update_count(Card(Suit.HEARTS, Rank.FIVE))  # +1 each
            
            # Should handle near-zero remaining decks gracefully
            true_count = counter_8_deck.true_count()
            self.assertIsInstance(true_count, float)
            # With very few cards remaining and a running count of +5, true count should be significant
            running_count = counter_8_deck.running_count()
            if running_count != 0:
                self.assertGreater(abs(true_count), 0)
                # With only 1 card remaining, true count should be very high
                self.assertGreater(abs(true_count), 1.0)
    
    def test_counting_with_different_rule_variations(self):
        """Test counting systems with different rule variations."""
        rule_variations = [
            GameRules(dealer_hits_soft_17=True, num_decks=6),
            GameRules(dealer_hits_soft_17=False, num_decks=6),
            GameRules(double_after_split=True, num_decks=6),
            GameRules(double_after_split=False, num_decks=6),
            GameRules(surrender_allowed=True, num_decks=6),
            GameRules(surrender_allowed=False, num_decks=6)
        ]
        
        for rules in rule_variations:
            for system in self.all_systems:
                game = CountingBlackjackGame(rules, system)
                
                # Test that counting works regardless of rule variations
                with patch.object(game.shoe, 'deal_card') as mock_deal:
                    mock_deal.side_effect = [
                        Card(Suit.HEARTS, Rank.FIVE),    # +1 in most systems
                        Card(Suit.DIAMONDS, Rank.KING),  # -1 in most systems
                        Card(Suit.CLUBS, Rank.SIX),      # +1 in most systems
                        Card(Suit.SPADES, Rank.SEVEN)    # Varies by system
                    ]
                    
                    game.deal_initial_cards()
                    
                    # Count should be calculated correctly regardless of rules
                    count = game.get_running_count()
                    self.assertIsInstance(count, int)
                    
                    # True count should be calculated
                    true_count = game.get_true_count()
                    self.assertIsInstance(true_count, float)
    
    def test_counting_system_manager_functionality(self):
        """Test the counting system manager with all systems."""
        # Test system listing
        available_systems = self.manager.list_systems()
        expected_systems = ["Hi-Lo", "KO", "Hi-Opt I"]
        
        for expected in expected_systems:
            self.assertIn(expected, available_systems)
        
        # Test system retrieval
        for system_name in expected_systems:
            system = self.manager.get_system(system_name)
            self.assertIsInstance(system, CountingSystem)
            self.assertEqual(system.name(), system_name)
        
        # Test default system
        default_system = self.manager.get_default_system()
        self.assertEqual(default_system.name(), "Hi-Lo")
        
        # Test invalid system - returns None instead of raising ValueError
        result = self.manager.get_system("NonExistentSystem")
        self.assertIsNone(result)
    
    def test_multi_deck_penetration_effects(self):
        """Test how different penetration levels affect counting across systems."""
        penetration_levels = [0.5, 0.75, 0.8, 0.9]
        
        for system in self.all_systems:
            for penetration in penetration_levels:
                rules = GameRules(num_decks=6, penetration=penetration)
                game = CountingBlackjackGame(rules, system)
                
                # Calculate cards until shuffle
                total_cards = 52 * rules.num_decks
                cards_until_shuffle = int(total_cards * penetration)
                
                # Simulate dealing cards until shuffle point
                cards_dealt = 0
                while cards_dealt < cards_until_shuffle and not game.shoe.needs_shuffle():
                    with patch.object(game.shoe, 'deal_card') as mock_deal:
                        mock_deal.return_value = Card(Suit.HEARTS, Rank.SEVEN)  # Neutral card
                        
                        game.deal_initial_cards()
                        cards_dealt += 4  # 2 player + 2 dealer cards
                        
                        if not game.is_game_over():
                            game.player_stand()
                        
                        game.reset()
                
                # Verify penetration affects when shuffle occurs
                self.assertGreaterEqual(cards_dealt, cards_until_shuffle * 0.8)  # Allow some variance


if __name__ == '__main__':
    unittest.main()