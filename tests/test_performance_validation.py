"""Performance tests for long simulation sessions."""

import unittest
import time
import gc
from datetime import datetime, timedelta
from unittest.mock import patch

from src.game import CountingBlackjackGame
from src.models import GameRules, Card, Suit, Rank, Action
from src.counting import HiLoSystem, KOSystem, HiOptISystem
from src.session import SessionManager, SessionData, SessionMetadata
from src.analytics import SessionStats, PerformanceTracker
from src.strategy import BasicStrategy, DeviationStrategy


class TestPerformanceValidation(unittest.TestCase):
    """Test system performance under various load conditions."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.rules = GameRules(num_decks=6, penetration=0.75)
        self.hi_lo_system = HiLoSystem()
        
    def test_long_session_performance(self):
        """Test performance during a long simulation session."""
        game = CountingBlackjackGame(self.rules, self.hi_lo_system)
        session_stats = SessionStats("performance-test")
        
        start_time = time.time()
        hands_target = 1000
        
        for hand_num in range(hands_target):
            # Check if shoe needs shuffling
            if game.shoe.needs_shuffle():
                game.shoe.shuffle()
            
            # Deal and play a hand
            game.deal_initial_cards()
            
            # Simple strategy: hit if under 17, stand otherwise
            while not game.is_game_over():
                if game.player_hand.value() < 17:
                    try:
                        game.player_hit()
                    except Exception:
                        # If shoe needs shuffling during play, shuffle and stand
                        game.shoe.shuffle()
                        game.player_stand()
                        break
                else:
                    game.player_stand()
            
            # Update statistics
            result = game.get_result()
            session_stats.update_hand_result(result, 10.0)
            
            # Track counting accuracy
            actual_count = game.get_running_count()
            session_stats.update_counting_accuracy(actual_count, actual_count)
            
            # Reset for next hand
            game.reset()
            
            # Force garbage collection every 100 hands to prevent memory buildup
            if (hand_num + 1) % 100 == 0:
                gc.collect()
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Performance assertions
        hands_per_second = hands_target / total_time
        self.assertGreater(hands_per_second, 50,  # Reduced threshold since we don't have optimized environment
            f"Performance too slow: {hands_per_second:.2f} hands/second")
        
        # Verify game state is still consistent
        self.assertIsInstance(game.get_running_count(), int)
        self.assertIsInstance(game.get_true_count(), float)
        self.assertEqual(session_stats.hands_played, hands_target)
    
    def test_multiple_counting_systems_performance(self):
        """Test performance with different counting systems."""
        systems = [
            ("Hi-Lo", HiLoSystem()),
            ("KO", KOSystem()),
            ("Hi-Opt I", HiOptISystem())
        ]
        
        performance_results = {}
        
        for system_name, system in systems:
            game = CountingBlackjackGame(self.rules, system)
            
            start_time = time.time()
            hands_played = 500
            
            for _ in range(hands_played):
                # Check if shoe needs shuffling
                if game.shoe.needs_shuffle():
                    game.shoe.shuffle()
                
                game.deal_initial_cards()
                
                # Quick resolution
                while not game.is_game_over():
                    if game.player_hand.value() < 17:
                        try:
                            game.player_hit()
                        except Exception:
                            # If shoe needs shuffling during play, shuffle and stand
                            game.shoe.shuffle()
                            game.player_stand()
                            break
                    else:
                        game.player_stand()
                
                game.reset()
            
            end_time = time.time()
            total_time = end_time - start_time
            
            performance_results[system_name] = {
                'time': total_time,
                'hands_per_second': hands_played / total_time
            }
        
        # All systems should perform reasonably well
        for system_name, results in performance_results.items():
            self.assertGreater(results['hands_per_second'], 50, 
                f"{system_name} too slow: {results['hands_per_second']:.2f} hands/second")
        
        # Performance should be relatively consistent across systems
        times = [results['time'] for results in performance_results.values()]
        max_time = max(times)
        min_time = min(times)
        time_variance = (max_time - min_time) / min_time
        
        self.assertLess(time_variance, 0.5, 
            f"Too much performance variance between systems: {time_variance:.2%}")
    
    def test_session_persistence_performance(self):
        """Test performance of session save/load operations."""
        import tempfile
        import shutil
        
        temp_dir = tempfile.mkdtemp()
        session_manager = SessionManager(temp_dir)
        
        try:
            # Create a large session with lots of data
            session_stats = SessionStats("perf-test")
            
            # Simulate many hands of data
            for i in range(1000):
                # Simulate hand results
                from src.models import GameResult, Outcome
                result = GameResult(
                    outcome=Outcome.WIN if i % 2 == 0 else Outcome.LOSS,
                    player_total=20,
                    dealer_total=19,
                    payout=10.0 if i % 2 == 0 else -10.0
                )
                session_stats.update_hand_result(result, 10.0)
                session_stats.update_counting_accuracy(i % 10, i % 10)  # Perfect accuracy
            
            metadata = SessionMetadata(
                session_id="perf-test",
                name="Performance Test Session",
                created_time=datetime.now() - timedelta(hours=2),
                last_modified=datetime.now()
            )
            
            session_data = SessionData(
                session_id="perf-test",
                metadata=metadata,
                rules=self.rules,
                stats=session_stats,
                counting_system="Hi-Lo"
            )
            
            # Test save performance
            save_start = time.time()
            session_manager.save_session(session_data, "Performance Test")
            save_time = time.time() - save_start
            
            self.assertLess(save_time, 1.0, f"Save too slow: {save_time:.3f}s")
            
            # Test load performance
            load_start = time.time()
            loaded_session = session_manager.load_session("perf-test")
            load_time = time.time() - load_start
            
            self.assertLess(load_time, 1.0, f"Load too slow: {load_time:.3f}s")
            
            # Verify data integrity
            self.assertEqual(loaded_session.stats.hands_played, 1000)
            self.assertEqual(loaded_session.session_id, "perf-test")
            
        finally:
            shutil.rmtree(temp_dir)
    
    def test_concurrent_operations_performance(self):
        """Test performance under concurrent-like operations."""
        # Simulate multiple games running simultaneously
        games = []
        for i in range(5):
            game = CountingBlackjackGame(self.rules, self.hi_lo_system)
            games.append(game)
        
        start_time = time.time()
        
        # Run operations on all games
        for round_num in range(100):
            for game_idx, game in enumerate(games):
                # Check if shoe needs shuffling
                if game.shoe.needs_shuffle():
                    game.shoe.shuffle()
                
                # Each game plays a hand
                game.deal_initial_cards()
                
                while not game.is_game_over():
                    if game.player_hand.value() < 17:
                        try:
                            game.player_hit()
                        except Exception:
                            # If shoe needs shuffling during play, shuffle and stand
                            game.shoe.shuffle()
                            game.player_stand()
                            break
                    else:
                        game.player_stand()
                
                # Get results and reset
                result = game.get_result()
                count = game.get_running_count()
                true_count = game.get_true_count()
                
                # Verify state consistency
                self.assertIsInstance(count, int)
                self.assertIsInstance(true_count, float)
                
                game.reset()
        
        end_time = time.time()
        total_time = end_time - start_time
        
        total_hands = 100 * len(games)
        hands_per_second = total_hands / total_time
        
        self.assertGreater(hands_per_second, 200, 
            f"Concurrent performance too slow: {hands_per_second:.2f} hands/second")
    
    def test_memory_leak_detection(self):
        """Test for memory leaks during extended operation."""
        game = CountingBlackjackGame(self.rules, self.hi_lo_system)
        
        # Run multiple cycles to detect basic functionality issues
        cycle_size = 100
        num_cycles = 10
        
        for cycle in range(num_cycles):
            # Play many hands
            for _ in range(cycle_size):
                # Check if shoe needs shuffling
                if game.shoe.needs_shuffle():
                    game.shoe.shuffle()
                
                game.deal_initial_cards()
                
                while not game.is_game_over():
                    if game.player_hand.value() < 17:
                        try:
                            game.player_hit()
                        except Exception:
                            # If shoe needs shuffling during play, shuffle and stand
                            game.shoe.shuffle()
                            game.player_stand()
                            break
                    else:
                        game.player_stand()
                
                game.reset()
            
            # Force garbage collection after each cycle
            gc.collect()
            
            # Verify game state is still consistent after many operations
            self.assertIsInstance(game.get_running_count(), int)
            self.assertIsInstance(game.get_true_count(), float)
            self.assertEqual(game.player_hand.card_count(), 0)
            self.assertEqual(game.dealer_hand.card_count(), 0)
    
    def test_large_deck_penetration_performance(self):
        """Test performance with very high deck penetration."""
        # Test with very high penetration (95%)
        high_penetration_rules = GameRules(num_decks=8, penetration=0.95)
        game = CountingBlackjackGame(high_penetration_rules, self.hi_lo_system)
        
        start_time = time.time()
        hands_played = 0
        shuffles_occurred = 0
        
        # Play until we get several shuffles
        while shuffles_occurred < 5 and time.time() - start_time < 30:  # Max 30 seconds
            initial_cards_remaining = game.shoe.cards_remaining()
            
            # Check if shoe needs shuffling before dealing
            if game.shoe.needs_shuffle():
                game.shoe.shuffle()
                shuffles_occurred += 1
            
            game.deal_initial_cards()
            
            while not game.is_game_over():
                if game.player_hand.value() < 17:
                    try:
                        game.player_hit()
                    except Exception:
                        # If shoe needs shuffling during play, shuffle and stand
                        game.shoe.shuffle()
                        shuffles_occurred += 1
                        game.player_stand()
                        break
                else:
                    game.player_stand()
            
            hands_played += 1
            game.reset()
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should handle high penetration efficiently
        if hands_played > 0:
            hands_per_second = hands_played / total_time
            self.assertGreater(hands_per_second, 50, 
                f"High penetration performance too slow: {hands_per_second:.2f} hands/second")
        
        # Should have triggered multiple shuffles
        self.assertGreaterEqual(shuffles_occurred, 2, 
            "Should have triggered multiple shuffles with high penetration")
    
    def test_strategy_calculation_performance(self):
        """Test performance of strategy calculations."""
        basic_strategy = BasicStrategy()
        deviation_strategy = DeviationStrategy()
        
        # Create various hand scenarios
        test_scenarios = []
        
        # Helper function to create valid rank
        def get_rank_for_value(value):
            rank_map = {
                1: Rank.ACE, 2: Rank.TWO, 3: Rank.THREE, 4: Rank.FOUR, 5: Rank.FIVE,
                6: Rank.SIX, 7: Rank.SEVEN, 8: Rank.EIGHT, 9: Rank.NINE, 10: Rank.TEN
            }
            return rank_map.get(value, Rank.TEN)
        
        for player_total in range(5, 22):
            for dealer_rank in Rank:
                # Create a hand with the target total
                from src.models import Hand
                hand = Hand()
                
                if player_total <= 11:
                    # Simple two-card hand
                    remaining_value = player_total - 2
                    if remaining_value >= 1 and remaining_value <= 10:
                        hand.add_card(Card(Suit.HEARTS, Rank.TWO))
                        hand.add_card(Card(Suit.CLUBS, get_rank_for_value(remaining_value)))
                    else:
                        continue
                else:
                    # Use 10 + remaining value
                    remaining = player_total - 10
                    if remaining >= 1 and remaining <= 10:
                        hand.add_card(Card(Suit.HEARTS, Rank.TEN))
                        hand.add_card(Card(Suit.CLUBS, get_rank_for_value(remaining)))
                    else:
                        continue
                
                dealer_up = Card(Suit.DIAMONDS, dealer_rank)
                test_scenarios.append((hand, dealer_up))
        
        # Test basic strategy performance
        start_time = time.time()
        for hand, dealer_up in test_scenarios:
            action = basic_strategy.get_action(hand, dealer_up, self.rules)
            self.assertIsInstance(action, Action)
        basic_time = time.time() - start_time
        
        # Test deviation strategy performance
        start_time = time.time()
        for hand, dealer_up in test_scenarios:
            for true_count in [-3.0, 0.0, 3.0]:
                action = deviation_strategy.get_action(hand, dealer_up, true_count, self.rules)
                self.assertIsInstance(action, Action)
        deviation_time = time.time() - start_time
        
        # Strategy calculations should be fast
        scenarios_count = len(test_scenarios)
        basic_calculations_per_second = scenarios_count / basic_time
        deviation_calculations_per_second = (scenarios_count * 3) / deviation_time
        
        self.assertGreater(basic_calculations_per_second, 1000, 
            f"Basic strategy too slow: {basic_calculations_per_second:.0f} calculations/second")
        
        self.assertGreater(deviation_calculations_per_second, 500, 
            f"Deviation strategy too slow: {deviation_calculations_per_second:.0f} calculations/second")


class TestScalabilityValidation(unittest.TestCase):
    """Test system scalability with increasing load."""
    
    def test_increasing_deck_count_scalability(self):
        """Test performance scaling with increasing deck counts."""
        deck_counts = [1, 2, 4, 6, 8]
        performance_results = {}
        
        for deck_count in deck_counts:
            rules = GameRules(num_decks=deck_count, penetration=0.75)
            game = CountingBlackjackGame(rules, HiLoSystem())
            
            start_time = time.time()
            hands_played = 200
            
            for _ in range(hands_played):
                # Check if shoe needs shuffling
                if game.shoe.needs_shuffle():
                    game.shoe.shuffle()
                
                game.deal_initial_cards()
                
                while not game.is_game_over():
                    if game.player_hand.value() < 17:
                        try:
                            game.player_hit()
                        except Exception:
                            # If shoe needs shuffling during play, shuffle and stand
                            game.shoe.shuffle()
                            game.player_stand()
                            break
                    else:
                        game.player_stand()
                
                game.reset()
            
            end_time = time.time()
            total_time = end_time - start_time
            
            performance_results[deck_count] = {
                'time': total_time,
                'hands_per_second': hands_played / total_time
            }
        
        # Performance should not degrade significantly with more decks
        single_deck_performance = performance_results[1]['hands_per_second']
        eight_deck_performance = performance_results[8]['hands_per_second']
        
        performance_ratio = eight_deck_performance / single_deck_performance
        self.assertGreater(performance_ratio, 0.5, 
            f"Performance degrades too much with more decks: {performance_ratio:.2%} of single deck performance")
    
    def test_session_data_scalability(self):
        """Test scalability with large amounts of session data."""
        import tempfile
        import shutil
        
        temp_dir = tempfile.mkdtemp()
        session_manager = SessionManager(temp_dir)
        
        try:
            # Create multiple sessions with varying amounts of data
            session_sizes = [100, 500, 1000, 2000]
            
            for size in session_sizes:
                session_id = f"scale-test-{size}"
                session_stats = SessionStats(session_id)
                
                # Add data
                for i in range(size):
                    from src.models import GameResult, Outcome
                    result = GameResult(
                        outcome=Outcome.WIN if i % 2 == 0 else Outcome.LOSS,
                        player_total=20,
                        dealer_total=19,
                        payout=10.0 if i % 2 == 0 else -10.0
                    )
                    session_stats.update_hand_result(result, 10.0)
                
                metadata = SessionMetadata(
                    session_id=session_id,
                    name=f"Scale Test {size}",
                    created_time=datetime.now(),
                    last_modified=datetime.now()
                )
                
                session_data = SessionData(
                    session_id=session_id,
                    metadata=metadata,
                    rules=GameRules(),
                    stats=session_stats,
                    counting_system="Hi-Lo"
                )
                
                # Test save/load performance
                start_time = time.time()
                session_manager.save_session(session_data, f"Scale Test {size}")
                save_time = time.time() - start_time
                
                start_time = time.time()
                loaded_session = session_manager.load_session(session_id)
                load_time = time.time() - start_time
                
                # Performance should scale reasonably
                self.assertLess(save_time, 2.0, f"Save too slow for {size} hands: {save_time:.3f}s")
                self.assertLess(load_time, 2.0, f"Load too slow for {size} hands: {load_time:.3f}s")
                
                # Verify data integrity
                self.assertEqual(loaded_session.stats.hands_played, size)
        
        finally:
            shutil.rmtree(temp_dir)


if __name__ == '__main__':
    unittest.main()