"""Unit tests for session statistics tracking."""

import unittest
from datetime import datetime, timedelta
from src.analytics.session_stats import SessionStats, CountingAccuracy, StrategyAccuracy
from src.models import GameResult, Outcome, Action


class TestCountingAccuracy(unittest.TestCase):
    """Test counting accuracy tracking."""
    
    def test_initial_state(self):
        """Test initial counting accuracy state."""
        accuracy = CountingAccuracy()
        self.assertEqual(accuracy.total_estimates, 0)
        self.assertEqual(accuracy.correct_estimates, 0)
        self.assertEqual(accuracy.total_error, 0.0)
        self.assertEqual(accuracy.max_error, 0.0)
        self.assertEqual(accuracy.accuracy_percentage(), 0.0)
        self.assertEqual(accuracy.average_error(), 0.0)
    
    def test_accuracy_percentage(self):
        """Test accuracy percentage calculation."""
        accuracy = CountingAccuracy(total_estimates=10, correct_estimates=8)
        self.assertEqual(accuracy.accuracy_percentage(), 80.0)
    
    def test_average_error(self):
        """Test average error calculation."""
        accuracy = CountingAccuracy(total_estimates=4, total_error=10.0)
        self.assertEqual(accuracy.average_error(), 2.5)


class TestStrategyAccuracy(unittest.TestCase):
    """Test strategy adherence tracking."""
    
    def test_initial_state(self):
        """Test initial strategy accuracy state."""
        accuracy = StrategyAccuracy()
        self.assertEqual(accuracy.total_decisions, 0)
        self.assertEqual(accuracy.correct_decisions, 0)
        self.assertEqual(accuracy.basic_strategy_decisions, 0)
        self.assertEqual(accuracy.deviation_decisions, 0)
        self.assertEqual(accuracy.correct_deviations, 0)
        self.assertEqual(accuracy.adherence_percentage(), 0.0)
        self.assertEqual(accuracy.deviation_accuracy(), 0.0)
    
    def test_adherence_percentage(self):
        """Test strategy adherence percentage calculation."""
        accuracy = StrategyAccuracy(total_decisions=20, correct_decisions=18)
        self.assertEqual(accuracy.adherence_percentage(), 90.0)
    
    def test_deviation_accuracy(self):
        """Test deviation accuracy calculation."""
        accuracy = StrategyAccuracy(deviation_decisions=5, correct_deviations=4)
        self.assertEqual(accuracy.deviation_accuracy(), 80.0)


class TestSessionStats(unittest.TestCase):
    """Test session statistics tracking."""
    
    def test_initial_state(self):
        """Test initial session state."""
        stats = SessionStats(session_id="test_session")
        self.assertEqual(stats.session_id, "test_session")
        self.assertIsNotNone(stats.start_time)
        self.assertIsNone(stats.end_time)
        self.assertEqual(stats.hands_played, 0)
        self.assertEqual(stats.hands_won, 0)
        self.assertEqual(stats.hands_lost, 0)
        self.assertEqual(stats.hands_pushed, 0)
        self.assertEqual(stats.blackjacks, 0)
        self.assertEqual(stats.surrenders, 0)
        self.assertEqual(stats.total_bet, 0.0)
        self.assertEqual(stats.total_winnings, 0.0)
        self.assertEqual(stats.net_result, 0.0)
        self.assertIsInstance(stats.counting_accuracy, CountingAccuracy)
        self.assertIsInstance(stats.strategy_accuracy, StrategyAccuracy)
        self.assertEqual(len(stats.results_history), 0)
    
    def test_update_hand_result_win(self):
        """Test updating with winning hand result."""
        stats = SessionStats()
        result = GameResult(outcome=Outcome.WIN, player_total=20, dealer_total=19, payout=1.0)
        
        stats.update_hand_result(result, bet_amount=10.0)
        
        self.assertEqual(stats.hands_played, 1)
        self.assertEqual(stats.hands_won, 1)
        self.assertEqual(stats.hands_lost, 0)
        self.assertEqual(stats.hands_pushed, 0)
        self.assertEqual(stats.total_bet, 10.0)
        self.assertEqual(stats.total_winnings, 10.0)
        self.assertEqual(stats.net_result, 10.0)
        self.assertEqual(len(stats.results_history), 1)
    
    def test_update_hand_result_loss(self):
        """Test updating with losing hand result."""
        stats = SessionStats()
        result = GameResult(outcome=Outcome.LOSS, player_total=22, dealer_total=20, payout=-1.0)
        
        stats.update_hand_result(result, bet_amount=5.0)
        
        self.assertEqual(stats.hands_played, 1)
        self.assertEqual(stats.hands_won, 0)
        self.assertEqual(stats.hands_lost, 1)
        self.assertEqual(stats.hands_pushed, 0)
        self.assertEqual(stats.total_bet, 5.0)
        self.assertEqual(stats.total_winnings, 0.0)
        self.assertEqual(stats.net_result, -5.0)
    
    def test_update_hand_result_push(self):
        """Test updating with push result."""
        stats = SessionStats()
        result = GameResult(outcome=Outcome.PUSH, player_total=20, dealer_total=20, payout=0.0)
        
        stats.update_hand_result(result, bet_amount=15.0)
        
        self.assertEqual(stats.hands_played, 1)
        self.assertEqual(stats.hands_won, 0)
        self.assertEqual(stats.hands_lost, 0)
        self.assertEqual(stats.hands_pushed, 1)
        self.assertEqual(stats.total_bet, 15.0)
        self.assertEqual(stats.total_winnings, 0.0)
        self.assertEqual(stats.net_result, 0.0)
    
    def test_update_hand_result_blackjack(self):
        """Test updating with blackjack result."""
        stats = SessionStats()
        result = GameResult(outcome=Outcome.BLACKJACK, player_total=21, dealer_total=20, payout=1.5)
        
        stats.update_hand_result(result, bet_amount=20.0)
        
        self.assertEqual(stats.hands_played, 1)
        self.assertEqual(stats.hands_won, 1)
        self.assertEqual(stats.blackjacks, 1)
        self.assertEqual(stats.total_bet, 20.0)
        self.assertEqual(stats.total_winnings, 30.0)
        self.assertEqual(stats.net_result, 30.0)
    
    def test_update_hand_result_surrender(self):
        """Test updating with surrender result."""
        stats = SessionStats()
        result = GameResult(outcome=Outcome.SURRENDER, player_total=16, payout=-0.5)
        
        stats.update_hand_result(result, bet_amount=10.0)
        
        self.assertEqual(stats.hands_played, 1)
        self.assertEqual(stats.hands_lost, 1)
        self.assertEqual(stats.surrenders, 1)
        self.assertEqual(stats.total_bet, 10.0)
        self.assertEqual(stats.total_winnings, 0.0)
        self.assertEqual(stats.net_result, -5.0)
    
    def test_update_counting_accuracy_correct(self):
        """Test updating counting accuracy with correct estimate."""
        stats = SessionStats()
        
        stats.update_counting_accuracy(user_count=5, actual_count=5)
        
        self.assertEqual(stats.counting_accuracy.total_estimates, 1)
        self.assertEqual(stats.counting_accuracy.correct_estimates, 1)
        self.assertEqual(stats.counting_accuracy.total_error, 0.0)
        self.assertEqual(stats.counting_accuracy.max_error, 0.0)
        self.assertEqual(stats.counting_accuracy.accuracy_percentage(), 100.0)
    
    def test_update_counting_accuracy_incorrect(self):
        """Test updating counting accuracy with incorrect estimate."""
        stats = SessionStats()
        
        stats.update_counting_accuracy(user_count=3, actual_count=7)
        
        self.assertEqual(stats.counting_accuracy.total_estimates, 1)
        self.assertEqual(stats.counting_accuracy.correct_estimates, 0)
        self.assertEqual(stats.counting_accuracy.total_error, 4.0)
        self.assertEqual(stats.counting_accuracy.max_error, 4.0)
        self.assertEqual(stats.counting_accuracy.accuracy_percentage(), 0.0)
        self.assertEqual(stats.counting_accuracy.average_error(), 4.0)
    
    def test_update_counting_accuracy_with_tolerance(self):
        """Test counting accuracy with tolerance."""
        stats = SessionStats()
        
        # Within tolerance
        stats.update_counting_accuracy(user_count=5, actual_count=6, tolerance=1)
        self.assertEqual(stats.counting_accuracy.correct_estimates, 1)
        
        # Outside tolerance
        stats.update_counting_accuracy(user_count=5, actual_count=8, tolerance=1)
        self.assertEqual(stats.counting_accuracy.correct_estimates, 1)
        self.assertEqual(stats.counting_accuracy.total_estimates, 2)
    
    def test_update_strategy_adherence_basic_correct(self):
        """Test strategy adherence with correct basic strategy."""
        stats = SessionStats()
        
        stats.update_strategy_adherence(Action.HIT, Action.HIT, is_deviation=False)
        
        self.assertEqual(stats.strategy_accuracy.total_decisions, 1)
        self.assertEqual(stats.strategy_accuracy.correct_decisions, 1)
        self.assertEqual(stats.strategy_accuracy.basic_strategy_decisions, 1)
        self.assertEqual(stats.strategy_accuracy.deviation_decisions, 0)
        self.assertEqual(stats.strategy_accuracy.adherence_percentage(), 100.0)
    
    def test_update_strategy_adherence_basic_incorrect(self):
        """Test strategy adherence with incorrect basic strategy."""
        stats = SessionStats()
        
        stats.update_strategy_adherence(Action.STAND, Action.HIT, is_deviation=False)
        
        self.assertEqual(stats.strategy_accuracy.total_decisions, 1)
        self.assertEqual(stats.strategy_accuracy.correct_decisions, 0)
        self.assertEqual(stats.strategy_accuracy.basic_strategy_decisions, 1)
        self.assertEqual(stats.strategy_accuracy.adherence_percentage(), 0.0)
    
    def test_update_strategy_adherence_deviation_correct(self):
        """Test strategy adherence with correct deviation."""
        stats = SessionStats()
        
        stats.update_strategy_adherence(Action.STAND, Action.STAND, is_deviation=True)
        
        self.assertEqual(stats.strategy_accuracy.total_decisions, 1)
        self.assertEqual(stats.strategy_accuracy.correct_decisions, 1)
        self.assertEqual(stats.strategy_accuracy.deviation_decisions, 1)
        self.assertEqual(stats.strategy_accuracy.correct_deviations, 1)
        self.assertEqual(stats.strategy_accuracy.deviation_accuracy(), 100.0)
    
    def test_update_strategy_adherence_deviation_incorrect(self):
        """Test strategy adherence with incorrect deviation."""
        stats = SessionStats()
        
        stats.update_strategy_adherence(Action.HIT, Action.STAND, is_deviation=True)
        
        self.assertEqual(stats.strategy_accuracy.total_decisions, 1)
        self.assertEqual(stats.strategy_accuracy.correct_decisions, 0)
        self.assertEqual(stats.strategy_accuracy.deviation_decisions, 1)
        self.assertEqual(stats.strategy_accuracy.correct_deviations, 0)
        self.assertEqual(stats.strategy_accuracy.deviation_accuracy(), 0.0)
    
    def test_win_rate_calculation(self):
        """Test win rate calculation."""
        stats = SessionStats()
        
        # Add some results
        stats.update_hand_result(GameResult(outcome=Outcome.WIN, player_total=20, dealer_total=19, payout=1.0))
        stats.update_hand_result(GameResult(outcome=Outcome.LOSS, player_total=22, dealer_total=20, payout=-1.0))
        stats.update_hand_result(GameResult(outcome=Outcome.WIN, player_total=21, dealer_total=20, payout=1.0))
        stats.update_hand_result(GameResult(outcome=Outcome.PUSH, player_total=20, dealer_total=20, payout=0.0))
        
        self.assertEqual(stats.win_rate(), 50.0)  # 2 wins out of 4 hands
        self.assertEqual(stats.loss_rate(), 25.0)  # 1 loss out of 4 hands
        self.assertEqual(stats.push_rate(), 25.0)  # 1 push out of 4 hands
    
    def test_blackjack_rate_calculation(self):
        """Test blackjack rate calculation."""
        stats = SessionStats()
        
        stats.update_hand_result(GameResult(outcome=Outcome.BLACKJACK, player_total=21, dealer_total=20, payout=1.5))
        stats.update_hand_result(GameResult(outcome=Outcome.WIN, player_total=20, dealer_total=19, payout=1.0))
        stats.update_hand_result(GameResult(outcome=Outcome.BLACKJACK, player_total=21, dealer_total=19, payout=1.5))
        
        self.assertAlmostEqual(stats.blackjack_rate(), 66.67, places=2)  # 2 blackjacks out of 3 hands
    
    def test_financial_calculations(self):
        """Test financial calculation methods."""
        stats = SessionStats()
        
        # Add various results with different bet amounts
        stats.update_hand_result(GameResult(outcome=Outcome.WIN, player_total=20, dealer_total=19, payout=1.0), bet_amount=10.0)
        stats.update_hand_result(GameResult(outcome=Outcome.LOSS, player_total=22, dealer_total=20, payout=-1.0), bet_amount=15.0)
        stats.update_hand_result(GameResult(outcome=Outcome.BLACKJACK, player_total=21, dealer_total=20, payout=1.5), bet_amount=20.0)
        
        self.assertEqual(stats.average_bet(), 15.0)  # (10 + 15 + 20) / 3
        self.assertEqual(stats.total_bet, 45.0)
        self.assertEqual(stats.net_result, 25.0)  # 10 - 15 + 30
        self.assertAlmostEqual(stats.return_on_investment(), 55.56, places=2)  # 25/45 * 100
    
    def test_session_duration(self):
        """Test session duration calculation."""
        start_time = datetime.now()
        stats = SessionStats(start_time=start_time)
        
        # Test with no end time (should use current time)
        duration = stats.session_duration()
        self.assertIsNotNone(duration)
        self.assertGreaterEqual(duration, 0)
        
        # Test with explicit end time
        stats.end_time = start_time + timedelta(minutes=30)
        self.assertEqual(stats.session_duration(), 30.0)
    
    def test_hands_per_hour(self):
        """Test hands per hour calculation."""
        start_time = datetime.now()
        stats = SessionStats(start_time=start_time)
        stats.end_time = start_time + timedelta(minutes=30)
        
        # Add some hands
        for _ in range(60):
            stats.update_hand_result(GameResult(outcome=Outcome.WIN, player_total=20, dealer_total=19, payout=1.0))
        
        self.assertEqual(stats.hands_per_hour(), 120.0)  # 60 hands in 30 minutes = 120 hands/hour
    
    def test_end_session(self):
        """Test ending a session."""
        stats = SessionStats()
        self.assertIsNone(stats.end_time)
        
        stats.end_session()
        self.assertIsNotNone(stats.end_time)
        self.assertIsInstance(stats.end_time, datetime)
    
    def test_generate_summary(self):
        """Test comprehensive summary generation."""
        stats = SessionStats(session_id="test_summary")
        
        # Add some data
        stats.update_hand_result(GameResult(outcome=Outcome.WIN, player_total=20, dealer_total=19, payout=1.0), bet_amount=10.0)
        stats.update_counting_accuracy(5, 5)
        stats.update_strategy_adherence(Action.HIT, Action.HIT, is_deviation=False)
        
        summary = stats.generate_summary()
        
        # Check structure
        self.assertIn("session_info", summary)
        self.assertIn("hand_results", summary)
        self.assertIn("financial", summary)
        self.assertIn("counting_accuracy", summary)
        self.assertIn("strategy_adherence", summary)
        
        # Check some values
        self.assertEqual(summary["session_info"]["session_id"], "test_summary")
        self.assertEqual(summary["hand_results"]["hands_played"], 1)
        self.assertEqual(summary["hand_results"]["win_rate"], 100.0)
        self.assertEqual(summary["financial"]["net_result"], 10.0)
        self.assertEqual(summary["counting_accuracy"]["accuracy_percentage"], 100.0)
        self.assertEqual(summary["strategy_adherence"]["adherence_percentage"], 100.0)
    
    def test_string_representation(self):
        """Test string representation of session stats."""
        stats = SessionStats(session_id="test_str")
        
        # Add some data
        stats.update_hand_result(GameResult(outcome=Outcome.WIN, player_total=20, dealer_total=19, payout=1.0))
        stats.update_hand_result(GameResult(outcome=Outcome.LOSS, player_total=22, dealer_total=20, payout=-1.0))
        
        str_repr = str(stats)
        self.assertIn("test_str", str_repr)
        self.assertIn("Hands: 2", str_repr)
        self.assertIn("W:1 L:1 P:0", str_repr)
        self.assertIn("Win Rate: 50.0%", str_repr)
    
    def test_multiple_updates_consistency(self):
        """Test that multiple updates maintain consistency."""
        stats = SessionStats()
        
        # Add multiple results
        results = [
            (GameResult(outcome=Outcome.WIN, player_total=20, dealer_total=19, payout=1.0), 10.0),
            (GameResult(outcome=Outcome.LOSS, player_total=22, dealer_total=20, payout=-1.0), 10.0),
            (GameResult(outcome=Outcome.BLACKJACK, player_total=21, dealer_total=20, payout=1.5), 10.0),
            (GameResult(outcome=Outcome.PUSH, player_total=20, dealer_total=20, payout=0.0), 10.0),
            (GameResult(outcome=Outcome.SURRENDER, player_total=16, payout=-0.5), 10.0)
        ]
        
        for result, bet in results:
            stats.update_hand_result(result, bet)
        
        # Verify totals
        self.assertEqual(stats.hands_played, 5)
        self.assertEqual(stats.hands_won, 2)  # WIN + BLACKJACK
        self.assertEqual(stats.hands_lost, 2)  # LOSS + SURRENDER
        self.assertEqual(stats.hands_pushed, 1)
        self.assertEqual(stats.blackjacks, 1)
        self.assertEqual(stats.surrenders, 1)
        self.assertEqual(stats.total_bet, 50.0)
        self.assertEqual(stats.net_result, 10.0)  # 10 - 10 + 15 + 0 - 5
        
        # Verify percentages add up correctly
        total_percentage = stats.win_rate() + stats.loss_rate() + stats.push_rate()
        self.assertAlmostEqual(total_percentage, 100.0, places=10)


if __name__ == '__main__':
    unittest.main()