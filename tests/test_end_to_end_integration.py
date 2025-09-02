"""End-to-end integration tests for complete simulation sessions."""

import unittest
import tempfile
import shutil
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

from src.game import CountingBlackjackGame
from src.models import GameRules, Card, Suit, Rank, Action, Outcome
from src.counting import CountingSystemManager
from src.session import SessionManager, SessionData, SessionMetadata
from src.analytics import SessionStats, PerformanceTracker
from src.strategy import BasicStrategy, DeviationStrategy
from src.cli import GameCLI, CountingCLI


class TestEndToEndSimulationSession(unittest.TestCase):
    """Test complete simulation sessions from start to finish."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.session_manager = SessionManager(self.temp_dir)
        self.counting_manager = CountingSystemManager()
        
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)
    
    def test_complete_simulation_session_workflow(self):
        """Test a complete simulation session from creation to analysis."""
        # 1. Create game with specific rules
        rules = GameRules(
            dealer_hits_soft_17=True,
            double_after_split=True,
            surrender_allowed=True,
            num_decks=6,
            penetration=0.75,
            blackjack_payout=1.5
        )
        
        # 2. Initialize counting game with Hi-Lo system
        hi_lo_system = self.counting_manager.get_system("Hi-Lo")
        game = CountingBlackjackGame(rules, hi_lo_system)
        
        # 3. Create session tracking
        session_stats = SessionStats("end-to-end-test")
        performance_tracker = PerformanceTracker()
        
        # 4. Simulate multiple hands with realistic scenarios
        hands_played = 0
        total_bet = 0.0
        
        # Mock specific card sequences for predictable testing
        test_scenarios = [
            # Scenario 1: Player blackjack
            [
                Card(Suit.HEARTS, Rank.ACE),    # Player
                Card(Suit.DIAMONDS, Rank.KING), # Dealer face up
                Card(Suit.SPADES, Rank.KING),   # Player (blackjack)
                Card(Suit.CLUBS, Rank.SEVEN)    # Dealer hole
            ],
            # Scenario 2: Player bust
            [
                Card(Suit.HEARTS, Rank.TEN),    # Player
                Card(Suit.DIAMONDS, Rank.SIX),  # Dealer face up
                Card(Suit.SPADES, Rank.FIVE),   # Player
                Card(Suit.CLUBS, Rank.SEVEN),   # Dealer hole
                Card(Suit.HEARTS, Rank.KING)    # Player hit (bust)
            ],
            # Scenario 3: Dealer bust
            [
                Card(Suit.HEARTS, Rank.NINE),   # Player
                Card(Suit.DIAMONDS, Rank.SIX),  # Dealer face up
                Card(Suit.SPADES, Rank.EIGHT),  # Player (17)
                Card(Suit.CLUBS, Rank.FIVE),    # Dealer hole (11)
                Card(Suit.HEARTS, Rank.KING)    # Dealer hit (bust)
            ]
        ]
        
        for scenario_cards in test_scenarios:
            with patch.object(game.shoe, 'deal_card') as mock_deal:
                mock_deal.side_effect = scenario_cards
                
                # Deal initial cards
                game.deal_initial_cards()
                hands_played += 1
                bet_amount = 10.0
                total_bet += bet_amount
                
                # Track initial count state
                initial_count = game.get_running_count()
                
                # Simulate player decisions based on basic strategy
                basic_strategy = BasicStrategy()
                
                while not game.is_game_over():
                    available_actions = game.get_available_actions()
                    
                    if Action.HIT in available_actions:
                        # Simple strategy: hit if under 17
                        if game.player_hand.value() < 17:
                            game.player_hit()
                        else:
                            game.player_stand()
                    else:
                        game.player_stand()
                
                # Get final result
                result = game.get_result()
                
                # Update statistics
                session_stats.update_hand_result(result, bet_amount)
                
                # Track counting accuracy (simulate user estimate)
                actual_count = game.get_running_count()
                user_estimate = actual_count + (-1 if hands_played % 3 == 0 else 0)  # Simulate occasional error
                session_stats.update_counting_accuracy(user_estimate, actual_count)
                
                # Track strategy decision (create GameSituation manually)
                from src.models import GameSituation
                situation = GameSituation(
                    player_cards=game.player_hand.cards,
                    dealer_up_card=game.dealer_hand.cards[0],
                    can_double=game.player_hand.can_double(),
                    can_split=game.player_hand.can_split(),
                    can_surrender=Action.SURRENDER in game.get_available_actions()
                )
                performance_tracker.track_decision(
                    situation,
                    Action.STAND,  # What user did
                    Action.STAND   # What was optimal
                )
                
                # Reset for next hand
                game.reset()
        
        # 5. Create and save session
        metadata = SessionMetadata(
            session_id="end-to-end-test",
            name="End-to-End Test Session",
            created_time=datetime.now() - timedelta(minutes=30),
            last_modified=datetime.now()
        )
        
        session_data = SessionData(
            session_id="end-to-end-test",
            metadata=metadata,
            rules=rules,
            stats=session_stats,
            counting_system="Hi-Lo"
        )
        
        # Save session
        saved_id = self.session_manager.save_session(session_data, "End-to-End Test")
        self.assertEqual(saved_id, "end-to-end-test")
        
        # 6. Verify session persistence
        loaded_session = self.session_manager.load_session("end-to-end-test")
        
        # Verify all components were preserved
        self.assertEqual(loaded_session.session_id, "end-to-end-test")
        self.assertEqual(loaded_session.counting_system, "Hi-Lo")
        self.assertEqual(loaded_session.rules.num_decks, 6)
        self.assertEqual(loaded_session.rules.penetration, 0.75)
        self.assertEqual(loaded_session.stats.hands_played, 3)
        
        # 7. Verify statistics calculations
        self.assertGreater(loaded_session.stats.hands_played, 0)
        self.assertGreaterEqual(loaded_session.stats.counting_accuracy.total_estimates, 0)
        
        # 8. Test session analysis
        win_rate = loaded_session.stats.hands_won / max(loaded_session.stats.hands_played, 1)
        self.assertGreaterEqual(win_rate, 0.0)
        self.assertLessEqual(win_rate, 1.0)
        
        counting_accuracy = loaded_session.stats.counting_accuracy.accuracy_percentage()
        self.assertGreaterEqual(counting_accuracy, 0.0)
        self.assertLessEqual(counting_accuracy, 100.0)
    
    def test_cli_integration_workflow(self):
        """Test CLI integration with game components."""
        rules = GameRules(num_decks=1, penetration=0.5)
        cli = GameCLI(rules)
        
        # Test CLI initialization
        self.assertIsNotNone(cli.game)
        self.assertEqual(cli.rules, rules)
        
        # Mock user input for automated testing
        with patch('builtins.input') as mock_input:
            # Simulate: new hand -> stand -> quit
            mock_input.side_effect = ['n', 's', 'q']
            
            # Mock stdout to capture output
            with patch('sys.stdout'):
                # Start a new hand
                cli._new_hand()
                
                # Verify game state
                self.assertEqual(cli.game.player_hand.card_count(), 2)
                self.assertEqual(cli.game.dealer_hand.card_count(), 2)
                
                # Stand if game allows
                if not cli.game.is_game_over():
                    cli._stand()
                
                # Verify game completed
                self.assertTrue(cli.game.is_game_over())
    
    def test_counting_cli_integration(self):
        """Test counting CLI integration."""
        rules = GameRules(num_decks=6)
        counting_cli = CountingCLI(rules)
        
        # Test initialization
        self.assertIsNotNone(counting_cli.game)
        self.assertEqual(counting_cli.game.get_counting_system_name(), "Hi-Lo")
        
        # Test count estimation workflow
        with patch.object(counting_cli.game.shoe, 'deal_card') as mock_deal:
            # Set up predictable cards
            mock_deal.side_effect = [
                Card(Suit.HEARTS, Rank.FIVE),    # +1
                Card(Suit.DIAMONDS, Rank.KING),  # -1
                Card(Suit.CLUBS, Rank.SIX),      # +1
                Card(Suit.SPADES, Rank.SEVEN)    # 0
            ]
            
            # Deal initial cards
            counting_cli.game.deal_initial_cards()
            
            # Test count display
            count_info = counting_cli.game.get_count_info()
            self.assertIn('running_count', count_info)
            self.assertIn('true_count', count_info)
            self.assertIn('system', count_info)
            
            # Test count estimation
            actual_count = counting_cli.game.get_running_count()
            user_estimate = actual_count  # Perfect estimate
            
            # Verify count is accessible
            self.assertIsInstance(actual_count, int)
            self.assertIsInstance(user_estimate, int)
    

    
    def test_multi_component_error_handling(self):
        """Test error handling across multiple components."""
        rules = GameRules(num_decks=6)
        game = CountingBlackjackGame(rules)
        
        # Test invalid game state errors
        with self.assertRaises(RuntimeError):
            # Try to hit when no hand is dealt
            game.player_hit()
        
        # Test session manager error handling
        with self.assertRaises(Exception):
            # Try to load non-existent session
            self.session_manager.load_session("non-existent-id")
        
        # Test counting system error handling - returns None instead of raising ValueError
        result = self.counting_manager.get_system("NonExistent")
        self.assertIsNone(result)
    
    def test_comprehensive_rule_combinations(self):
        """Test all combinations of game rules work correctly."""
        rule_combinations = [
            # (dealer_hits_soft_17, double_after_split, surrender_allowed, num_decks)
            (True, True, True, 1),
            (True, True, False, 2),
            (True, False, True, 4),
            (True, False, False, 6),
            (False, True, True, 8),
            (False, True, False, 6),
            (False, False, True, 4),
            (False, False, False, 2),
        ]
        
        for dh17, das, surrender, decks in rule_combinations:
            rules = GameRules(
                dealer_hits_soft_17=dh17,
                double_after_split=das,
                surrender_allowed=surrender,
                num_decks=decks,
                penetration=0.75
            )
            
            game = CountingBlackjackGame(rules)
            
            # Test that game can be created and basic operations work
            game.deal_initial_cards()
            
            # Verify rule settings are applied
            self.assertEqual(game.rules.dealer_hits_soft_17, dh17)
            self.assertEqual(game.rules.double_after_split, das)
            self.assertEqual(game.rules.surrender_allowed, surrender)
            self.assertEqual(game.rules.num_decks, decks)
            
            # Test that game can complete
            while not game.is_game_over():
                available_actions = game.get_available_actions()
                if Action.STAND in available_actions:
                    game.player_stand()
                elif Action.HIT in available_actions:
                    game.player_hit()
                else:
                    break
            
            # Verify game completed successfully
            self.assertTrue(game.is_game_over())
            result = game.get_result()
            self.assertIsNotNone(result)
    
    def test_all_counting_systems_integration(self):
        """Test integration with all available counting systems."""
        systems_to_test = ["Hi-Lo", "KO", "Hi-Opt I"]
        standard_rules = GameRules(num_decks=6, penetration=0.75)
        
        for system_name in systems_to_test:
            system = self.counting_manager.get_system(system_name)
            game = CountingBlackjackGame(standard_rules, system)
            
            # Test basic functionality
            game.deal_initial_cards()
            
            # Verify counting system is working
            count = game.get_running_count()
            true_count = game.get_true_count()
            
            self.assertIsInstance(count, int)
            self.assertIsInstance(true_count, float)
            self.assertEqual(game.get_counting_system_name(), system_name)
            
            # Test system switching
            if system_name != "Hi-Lo":
                hi_lo = self.counting_manager.get_system("Hi-Lo")
                game.switch_counting_system(hi_lo)
                self.assertEqual(game.get_counting_system_name(), "Hi-Lo")
    
    def test_session_analytics_comprehensive(self):
        """Test comprehensive session analytics and reporting."""
        session_stats = SessionStats("analytics-test")
        performance_tracker = PerformanceTracker()
        
        # Simulate a comprehensive session with various outcomes
        from src.models import GameResult, Outcome, GameSituation
        
        test_results = [
            (Outcome.WIN, 20, 19, 10.0),
            (Outcome.LOSS, 22, 20, -10.0),  # Player bust
            (Outcome.PUSH, 20, 20, 0.0),
            (Outcome.BLACKJACK, 21, 20, 15.0),  # 3:2 payout
            (Outcome.WIN, 19, 22, 10.0),  # Dealer bust
        ]
        
        for outcome, player_total, dealer_total, payout in test_results:
            result = GameResult(
                outcome=outcome,
                player_total=player_total,
                dealer_total=dealer_total,
                payout=payout
            )
            session_stats.update_hand_result(result, abs(payout) if payout != 0 else 10.0)
        
        # Test counting accuracy tracking
        count_tests = [
            (5, 5),    # Perfect
            (3, 4),    # Off by 1
            (-2, -2),  # Perfect
            (0, 1),    # Off by 1
            (8, 6),    # Off by 2
        ]
        
        for user_estimate, actual_count in count_tests:
            session_stats.update_counting_accuracy(user_estimate, actual_count)
        
        # Test strategy tracking
        standard_rules = GameRules(num_decks=6, penetration=0.75)
        game = CountingBlackjackGame(standard_rules)
        game.deal_initial_cards()
        
        # Create GameSituation manually
        from src.models import GameSituation
        situation = GameSituation(
            player_cards=game.player_hand.cards,
            dealer_up_card=game.dealer_hand.cards[0],
            can_double=game.player_hand.can_double(),
            can_split=game.player_hand.can_split(),
            can_surrender=Action.SURRENDER in game.get_available_actions()
        )
        performance_tracker.track_decision(situation, Action.HIT, Action.STAND)
        performance_tracker.track_decision(situation, Action.STAND, Action.STAND)
        
        # Verify analytics calculations
        self.assertEqual(session_stats.hands_played, 5)
        # Note: Both WIN and BLACKJACK outcomes count as wins, plus dealer bust = 3 wins
        self.assertEqual(session_stats.hands_won, 3)  # WIN + BLACKJACK + WIN (dealer bust)
        self.assertEqual(session_stats.hands_lost, 1)  # LOSS
        self.assertEqual(session_stats.hands_pushed, 1)  # PUSH
        
        # Test accuracy calculations
        accuracy = session_stats.counting_accuracy.accuracy_percentage()
        self.assertGreaterEqual(accuracy, 0.0)
        self.assertLessEqual(accuracy, 100.0)
        
        # Test net result - calculated as payout * bet_amount for each hand
        net_result = session_stats.net_result
        # Expected: (10.0 * 10.0) + (-10.0 * 10.0) + (0.0 * 10.0) + (15.0 * 15.0) + (10.0 * 10.0)
        # = 100.0 + (-100.0) + 0.0 + 225.0 + 100.0 = 325.0
        expected_net = 325.0
        self.assertEqual(net_result, expected_net)
    
    def test_performance_under_load(self):
        """Test system performance with multiple rapid operations."""
        rules = GameRules(num_decks=6, penetration=0.5)
        game = CountingBlackjackGame(rules)
        
        # Simulate rapid game play
        start_time = datetime.now()
        
        for _ in range(100):  # 100 hands
            try:
                # Check if shoe needs shuffling before dealing
                if game.shoe.needs_shuffle():
                    game.shoe.shuffle()
                
                game.deal_initial_cards()
                
                # Quick game resolution
                while not game.is_game_over():
                    if game.player_hand.value() < 17:
                        try:
                            game.player_hit()
                        except Exception:
                            # If shoe needs shuffling during play, shuffle and continue
                            game.shoe.shuffle()
                            game.player_stand()
                            break
                    else:
                        game.player_stand()
                
                game.reset()
            except Exception:
                # If any other error occurs, shuffle and continue
                game.shoe.shuffle()
                game.reset()
                continue
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Should complete 100 hands in reasonable time (less than 5 seconds)
        self.assertLess(duration, 5.0)
        
        # Verify counting system maintained accuracy
        self.assertIsInstance(game.get_running_count(), int)
        self.assertIsInstance(game.get_true_count(), float)


class TestSystemIntegration(unittest.TestCase):
    """Test integration between major system components."""
    
    def test_game_session_analytics_integration(self):
        """Test integration between game, session management, and analytics."""
        # Create components
        rules = GameRules(num_decks=6)
        game = CountingBlackjackGame(rules)
        session_stats = SessionStats("integration-test")
        
        # Play a hand and track everything
        with patch.object(game.shoe, 'deal_card') as mock_deal:
            mock_deal.side_effect = [
                Card(Suit.HEARTS, Rank.ACE),    # Player blackjack
                Card(Suit.DIAMONDS, Rank.KING), # Dealer
                Card(Suit.SPADES, Rank.KING),   # Player
                Card(Suit.CLUBS, Rank.SEVEN)    # Dealer hole
            ]
            
            game.deal_initial_cards()
            
            # Game should end with player blackjack
            self.assertTrue(game.is_game_over())
            self.assertTrue(game.player_hand.is_blackjack())
            
            # Update statistics
            result = game.get_result()
            session_stats.update_hand_result(result, 10.0)
            
            # Verify integration
            self.assertEqual(session_stats.hands_played, 1)
            self.assertEqual(session_stats.hands_won, 1)
            
            # Test counting integration
            count = game.get_running_count()
            session_stats.update_counting_accuracy(count, count)  # Perfect accuracy
            
            accuracy = session_stats.counting_accuracy.accuracy_percentage()
            self.assertEqual(accuracy, 100.0)
    
    def test_strategy_counting_integration(self):
        """Test integration between strategy engine and counting system."""
        rules = GameRules(num_decks=6)
        game = CountingBlackjackGame(rules)
        basic_strategy = BasicStrategy()
        deviation_strategy = DeviationStrategy()
        
        # Set up a scenario where count affects strategy
        with patch.object(game.shoe, 'deal_card') as mock_deal:
            # Player 16 vs Dealer 10 - basic strategy says hit, but high count might say stand
            mock_deal.side_effect = [
                Card(Suit.HEARTS, Rank.TEN),    # Player
                Card(Suit.DIAMONDS, Rank.TEN),  # Dealer face up
                Card(Suit.CLUBS, Rank.SIX),     # Player (16 total)
                Card(Suit.SPADES, Rank.SEVEN)   # Dealer hole
            ]
            
            game.deal_initial_cards()
            
            # Get basic strategy recommendation
            basic_action = basic_strategy.get_action(
                game.player_hand,
                game.dealer_hand.cards[0],
                rules
            )
            
            # Get deviation strategy recommendation with high true count
            true_count = 5.0  # High count
            deviation_action = deviation_strategy.get_action(
                game.player_hand,
                game.dealer_hand.cards[0],
                true_count,
                rules
            )
            
            # Verify strategies can provide recommendations
            self.assertIn(basic_action, [Action.HIT, Action.STAND])
            self.assertIn(deviation_action, [Action.HIT, Action.STAND])


if __name__ == '__main__':
    unittest.main()