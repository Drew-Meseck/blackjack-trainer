"""Unit tests for performance tracking and analytics."""

import unittest
from datetime import datetime, timedelta
from src.analytics.performance_tracker import (
    PerformanceTracker, AccuracyPoint, DecisionAnalysis, TrendData, SessionReport
)
from src.models import GameSituation, Action, Hand, Card, Suit, Rank, GameResult, Outcome
from src.analytics.session_stats import SessionStats


class TestTrendData(unittest.TestCase):
    """Test trend data tracking."""
    
    def test_initial_state(self):
        """Test initial trend data state."""
        trend = TrendData()
        self.assertEqual(len(trend.timestamps), 0)
        self.assertEqual(len(trend.values), 0)
        self.assertEqual(trend.average(), 0.0)
        self.assertIsNone(trend.latest())
    
    def test_add_point(self):
        """Test adding data points."""
        trend = TrendData()
        timestamp = datetime.now()
        
        trend.add_point(timestamp, 85.5)
        
        self.assertEqual(len(trend.timestamps), 1)
        self.assertEqual(len(trend.values), 1)
        self.assertEqual(trend.timestamps[0], timestamp)
        self.assertEqual(trend.values[0], 85.5)
        self.assertEqual(trend.latest(), 85.5)
    
    def test_average_calculation(self):
        """Test average calculation."""
        trend = TrendData()
        
        trend.add_point(datetime.now(), 80.0)
        trend.add_point(datetime.now(), 90.0)
        trend.add_point(datetime.now(), 70.0)
        
        self.assertEqual(trend.average(), 80.0)
    
    def test_get_recent_trend(self):
        """Test getting recent trend data."""
        trend = TrendData()
        now = datetime.now()
        
        # Add old data (2 hours ago)
        trend.add_point(now - timedelta(hours=2), 60.0)
        # Add recent data (30 minutes ago)
        trend.add_point(now - timedelta(minutes=30), 80.0)
        # Add current data
        trend.add_point(now, 90.0)
        
        recent = trend.get_recent_trend(hours=1)
        
        self.assertEqual(len(recent.values), 2)  # Only recent data
        self.assertIn(80.0, recent.values)
        self.assertIn(90.0, recent.values)
    
    def test_improvement_rate(self):
        """Test improvement rate calculation."""
        trend = TrendData()
        
        # Add increasing trend
        for i in range(5):
            trend.add_point(datetime.now(), float(i * 10))
        
        improvement_rate = trend.improvement_rate()
        self.assertGreater(improvement_rate, 0)  # Should be positive for increasing trend
        
        # Test with single point
        single_trend = TrendData()
        single_trend.add_point(datetime.now(), 50.0)
        self.assertEqual(single_trend.improvement_rate(), 0.0)


class TestAccuracyPoint(unittest.TestCase):
    """Test accuracy point data structure."""
    
    def test_creation(self):
        """Test accuracy point creation."""
        timestamp = datetime.now()
        point = AccuracyPoint(
            timestamp=timestamp,
            counting_accuracy=85.5,
            strategy_accuracy=92.3,
            hands_played=150,
            session_id="test_session"
        )
        
        self.assertEqual(point.timestamp, timestamp)
        self.assertEqual(point.counting_accuracy, 85.5)
        self.assertEqual(point.strategy_accuracy, 92.3)
        self.assertEqual(point.hands_played, 150)
        self.assertEqual(point.session_id, "test_session")


class TestDecisionAnalysis(unittest.TestCase):
    """Test decision analysis data structure."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.player_cards = [Card(Suit.HEARTS, Rank.TEN), Card(Suit.SPADES, Rank.SIX)]
        self.dealer_card = Card(Suit.CLUBS, Rank.FIVE)
        self.situation = GameSituation(
            player_cards=self.player_cards,
            dealer_up_card=self.dealer_card,
            can_double=True,
            can_split=False,
            can_surrender=False
        )
    
    def test_creation(self):
        """Test decision analysis creation."""
        decision = DecisionAnalysis(
            situation=self.situation,
            user_action=Action.HIT,
            optimal_action=Action.STAND,
            is_correct=False,
            is_deviation=False,
            true_count=2.5
        )
        
        self.assertEqual(decision.situation, self.situation)
        self.assertEqual(decision.user_action, Action.HIT)
        self.assertEqual(decision.optimal_action, Action.STAND)
        self.assertFalse(decision.is_correct)
        self.assertFalse(decision.is_deviation)
        self.assertEqual(decision.true_count, 2.5)
        self.assertIsInstance(decision.timestamp, datetime)
    
    def test_decision_key(self):
        """Test decision key generation."""
        decision = DecisionAnalysis(
            situation=self.situation,
            user_action=Action.HIT,
            optimal_action=Action.STAND,
            is_correct=False,
            is_deviation=False
        )
        
        expected_key = f"{self.situation.player_total()}_vs_{self.dealer_card.rank.value}"
        self.assertEqual(decision.decision_key(), expected_key)


class TestPerformanceTracker(unittest.TestCase):
    """Test performance tracker functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.tracker = PerformanceTracker()
        self.player_cards = [Card(Suit.HEARTS, Rank.TEN), Card(Suit.SPADES, Rank.SIX)]
        self.dealer_card = Card(Suit.CLUBS, Rank.FIVE)
        self.situation = GameSituation(
            player_cards=self.player_cards,
            dealer_up_card=self.dealer_card,
            can_double=True,
            can_split=False,
            can_surrender=False
        )
    
    def test_initial_state(self):
        """Test initial tracker state."""
        self.assertEqual(len(self.tracker.decisions), 0)
        self.assertEqual(len(self.tracker.accuracy_history), 0)
        self.assertEqual(len(self.tracker.counting_trend.values), 0)
        self.assertEqual(len(self.tracker.strategy_trend.values), 0)
        self.assertEqual(len(self.tracker.performance_trend.values), 0)
        self.assertEqual(len(self.tracker.decision_groups), 0)
        self.assertIsNone(self.tracker.current_session_id)
        self.assertIsNone(self.tracker.session_start)
    
    def test_start_session(self):
        """Test starting a new session."""
        session_id = "test_session_123"
        
        self.tracker.start_session(session_id)
        
        self.assertEqual(self.tracker.current_session_id, session_id)
        self.assertIsNotNone(self.tracker.session_start)
        self.assertIsInstance(self.tracker.session_start, datetime)
    
    def test_track_decision(self):
        """Test tracking player decisions."""
        self.tracker.track_decision(
            situation=self.situation,
            user_action=Action.HIT,
            optimal_action=Action.STAND,
            true_count=1.5
        )
        
        self.assertEqual(len(self.tracker.decisions), 1)
        
        decision = self.tracker.decisions[0]
        self.assertEqual(decision.situation, self.situation)
        self.assertEqual(decision.user_action, Action.HIT)
        self.assertEqual(decision.optimal_action, Action.STAND)
        self.assertFalse(decision.is_correct)
        self.assertFalse(decision.is_deviation)  # true_count < 2.0
        self.assertEqual(decision.true_count, 1.5)
        
        # Check decision grouping
        decision_key = decision.decision_key()
        self.assertIn(decision_key, self.tracker.decision_groups)
        self.assertEqual(len(self.tracker.decision_groups[decision_key]), 1)
    
    def test_track_decision_with_deviation(self):
        """Test tracking decisions with high count (deviation)."""
        self.tracker.track_decision(
            situation=self.situation,
            user_action=Action.STAND,
            optimal_action=Action.STAND,
            true_count=3.0  # High count should trigger deviation flag
        )
        
        decision = self.tracker.decisions[0]
        self.assertTrue(decision.is_correct)
        self.assertTrue(decision.is_deviation)  # true_count >= 2.0
    
    def test_track_count_estimate(self):
        """Test tracking counting estimates."""
        # Perfect estimate
        self.tracker.track_count_estimate(user_count=5, actual_count=5)
        self.assertEqual(len(self.tracker.counting_trend.values), 1)
        self.assertEqual(self.tracker.counting_trend.values[0], 100.0)
        
        # Estimate with error
        self.tracker.track_count_estimate(user_count=3, actual_count=5)
        self.assertEqual(len(self.tracker.counting_trend.values), 2)
        self.assertLess(self.tracker.counting_trend.values[1], 100.0)
    
    def test_update_accuracy_history(self):
        """Test updating accuracy history."""
        self.tracker.update_accuracy_history(
            counting_accuracy=85.5,
            strategy_accuracy=92.3,
            hands_played=150
        )
        
        self.assertEqual(len(self.tracker.accuracy_history), 1)
        
        point = self.tracker.accuracy_history[0]
        self.assertEqual(point.counting_accuracy, 85.5)
        self.assertEqual(point.strategy_accuracy, 92.3)
        self.assertEqual(point.hands_played, 150)
        self.assertIsInstance(point.timestamp, datetime)
        
        # Check performance trend update
        self.assertEqual(len(self.tracker.performance_trend.values), 1)
        expected_combined = (85.5 + 92.3) / 2
        self.assertEqual(self.tracker.performance_trend.values[0], expected_combined)
    
    def test_get_accuracy_trends(self):
        """Test getting accuracy trends for time period."""
        now = datetime.now()
        
        # Add old data
        old_point = AccuracyPoint(
            timestamp=now - timedelta(hours=25),
            counting_accuracy=70.0,
            strategy_accuracy=75.0,
            hands_played=50
        )
        self.tracker.accuracy_history.append(old_point)
        
        # Add recent data
        recent_point = AccuracyPoint(
            timestamp=now - timedelta(hours=1),
            counting_accuracy=85.0,
            strategy_accuracy=90.0,
            hands_played=100
        )
        self.tracker.accuracy_history.append(recent_point)
        
        # Get last 24 hours
        recent_trends = self.tracker.get_accuracy_trends(hours=24)
        
        self.assertEqual(len(recent_trends), 1)  # Only recent data
        self.assertEqual(recent_trends[0], recent_point)
    
    def test_analyze_decision_patterns(self):
        """Test decision pattern analysis."""
        # Add multiple decisions for the same situation
        for i in range(5):
            is_correct = i < 3  # 3 correct, 2 incorrect
            optimal_action = Action.STAND
            user_action = optimal_action if is_correct else Action.HIT
            
            self.tracker.track_decision(
                situation=self.situation,
                user_action=user_action,
                optimal_action=optimal_action
            )
        
        analysis = self.tracker.analyze_decision_patterns()
        
        decision_key = self.tracker.decisions[0].decision_key()
        self.assertIn(decision_key, analysis)
        
        pattern = analysis[decision_key]
        self.assertEqual(pattern["total_decisions"], 5)
        self.assertEqual(pattern["correct_decisions"], 3)
        self.assertEqual(pattern["accuracy_percentage"], 60.0)
        self.assertEqual(pattern["optimal_action"], "stand")
        self.assertIsNotNone(pattern["most_common_mistake"])
    
    def test_get_improvement_suggestions(self):
        """Test improvement suggestion generation."""
        # Add some poor performance data
        self.tracker.counting_trend.add_point(datetime.now(), 50.0)  # Low counting accuracy
        self.tracker.strategy_trend.add_point(datetime.now(), 60.0)  # Low strategy accuracy
        
        suggestions = self.tracker.get_improvement_suggestions()
        
        self.assertIsInstance(suggestions, list)
        self.assertLessEqual(len(suggestions), 5)  # Should limit to 5 suggestions
        
        # Should contain suggestions about counting and strategy
        suggestion_text = " ".join(suggestions).lower()
        self.assertTrue(any(word in suggestion_text for word in ["counting", "strategy", "practice"]))
    
    def test_generate_session_report(self):
        """Test session report generation."""
        # Set up session
        self.tracker.start_session("test_session")
        
        # Add some decisions
        self.tracker.track_decision(
            situation=self.situation,
            user_action=Action.STAND,
            optimal_action=Action.STAND
        )
        
        # Add accuracy data
        self.tracker.update_accuracy_history(80.0, 85.0, 50)
        
        # Create session stats
        session_stats = SessionStats(session_id="test_session")
        session_stats.update_hand_result(
            GameResult(outcome=Outcome.WIN, player_total=20, dealer_total=19, payout=1.0),
            bet_amount=10.0
        )
        
        report = self.tracker.generate_session_report(session_stats)
        
        self.assertIsInstance(report, SessionReport)
        self.assertEqual(report.session_id, "test_session")
        self.assertEqual(report.hands_played, 1)
        self.assertEqual(report.win_rate, 100.0)
        self.assertIsInstance(report.most_common_mistakes, list)
        self.assertIsInstance(report.best_decisions, list)
        self.assertIsInstance(report.accuracy_trend, TrendData)
        self.assertIsInstance(report.performance_trend, TrendData)
    
    def test_get_performance_summary(self):
        """Test performance summary generation."""
        # Add some data
        self.tracker.track_decision(
            situation=self.situation,
            user_action=Action.STAND,
            optimal_action=Action.STAND
        )
        self.tracker.update_accuracy_history(85.0, 90.0, 100)
        
        summary = self.tracker.get_performance_summary()
        
        self.assertIsInstance(summary, dict)
        self.assertIn("total_decisions", summary)
        self.assertIn("total_accuracy_points", summary)
        self.assertIn("current_counting_accuracy", summary)
        self.assertIn("current_strategy_accuracy", summary)
        self.assertIn("overall_performance", summary)
        self.assertIn("improvement_rate", summary)
        self.assertIn("decision_patterns_analyzed", summary)
        self.assertIn("improvement_suggestions", summary)
        
        self.assertEqual(summary["total_decisions"], 1)
        self.assertEqual(summary["total_accuracy_points"], 1)
        self.assertIsInstance(summary["improvement_suggestions"], list)
    
    def test_strategy_trend_updates(self):
        """Test that strategy trend updates correctly with decisions."""
        # Add 20 decisions to trigger trend calculation
        for i in range(20):
            is_correct = i < 16  # 80% accuracy
            optimal_action = Action.STAND
            user_action = optimal_action if is_correct else Action.HIT
            
            self.tracker.track_decision(
                situation=self.situation,
                user_action=user_action,
                optimal_action=optimal_action
            )
        
        # Should have strategy trend data
        self.assertGreater(len(self.tracker.strategy_trend.values), 0)
        
        # Latest trend should reflect the 80% accuracy
        latest_accuracy = self.tracker.strategy_trend.latest()
        self.assertIsNotNone(latest_accuracy)
        self.assertAlmostEqual(latest_accuracy, 80.0, places=1)


class TestSessionReport(unittest.TestCase):
    """Test session report functionality."""
    
    def test_duration_calculation(self):
        """Test session duration calculation."""
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=45)
        
        report = SessionReport(
            session_id="test",
            start_time=start_time,
            end_time=end_time,
            hands_played=90,
            win_rate=55.0,
            loss_rate=35.0,
            push_rate=10.0,
            blackjack_rate=4.5,
            net_result=25.0,
            roi_percentage=12.5,
            average_bet=10.0,
            counting_accuracy=85.0,
            strategy_adherence=92.0,
            deviation_accuracy=78.0,
            most_common_mistakes=[],
            best_decisions=[],
            accuracy_trend=TrendData(),
            performance_trend=TrendData()
        )
        
        self.assertEqual(report.duration_minutes(), 45.0)
        self.assertEqual(report.hands_per_hour(), 120.0)  # 90 hands in 45 minutes = 120/hour
    
    def test_duration_with_no_end_time(self):
        """Test duration calculation with no end time."""
        report = SessionReport(
            session_id="test",
            start_time=datetime.now(),
            end_time=None,
            hands_played=0,
            win_rate=0.0,
            loss_rate=0.0,
            push_rate=0.0,
            blackjack_rate=0.0,
            net_result=0.0,
            roi_percentage=0.0,
            average_bet=0.0,
            counting_accuracy=0.0,
            strategy_adherence=0.0,
            deviation_accuracy=0.0,
            most_common_mistakes=[],
            best_decisions=[],
            accuracy_trend=TrendData(),
            performance_trend=TrendData()
        )
        
        self.assertEqual(report.duration_minutes(), 0.0)
        self.assertEqual(report.hands_per_hour(), 0.0)


if __name__ == '__main__':
    unittest.main()