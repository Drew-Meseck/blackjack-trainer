"""Performance analytics and trend tracking for blackjack simulation."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from collections import defaultdict
from ..models import GameSituation, Action, GameResult, Outcome


@dataclass
class AccuracyPoint:
    """Represents a point in time for accuracy tracking."""
    timestamp: datetime
    counting_accuracy: float
    strategy_accuracy: float
    hands_played: int
    session_id: Optional[str] = None


@dataclass
class DecisionAnalysis:
    """Analysis of a specific decision made by the player."""
    situation: GameSituation
    user_action: Action
    optimal_action: Action
    is_correct: bool
    is_deviation: bool
    true_count: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.now)
    
    def decision_key(self) -> str:
        """Generate a key for grouping similar decisions."""
        return f"{self.situation.player_total()}_vs_{self.situation.dealer_up_card.rank.value}"


@dataclass
class TrendData:
    """Trend data for performance metrics over time."""
    timestamps: List[datetime] = field(default_factory=list)
    values: List[float] = field(default_factory=list)
    
    def add_point(self, timestamp: datetime, value: float) -> None:
        """Add a new data point to the trend."""
        self.timestamps.append(timestamp)
        self.values.append(value)
    
    def get_recent_trend(self, hours: int = 1) -> 'TrendData':
        """Get trend data for the last N hours."""
        cutoff = datetime.now() - timedelta(hours=hours)
        recent_trend = TrendData()
        
        for timestamp, value in zip(self.timestamps, self.values):
            if timestamp >= cutoff:
                recent_trend.add_point(timestamp, value)
        
        return recent_trend
    
    def average(self) -> float:
        """Calculate average value."""
        if not self.values:
            return 0.0
        return sum(self.values) / len(self.values)
    
    def latest(self) -> Optional[float]:
        """Get the latest value."""
        return self.values[-1] if self.values else None
    
    def improvement_rate(self) -> float:
        """Calculate improvement rate (slope of trend)."""
        if len(self.values) < 2:
            return 0.0
        
        # Simple linear regression slope
        n = len(self.values)
        x_values = list(range(n))
        
        sum_x = sum(x_values)
        sum_y = sum(self.values)
        sum_xy = sum(x * y for x, y in zip(x_values, self.values))
        sum_x2 = sum(x * x for x in x_values)
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        return slope


@dataclass
class SessionReport:
    """Comprehensive session performance report."""
    session_id: str
    start_time: datetime
    end_time: Optional[datetime]
    hands_played: int
    
    # Win/Loss statistics
    win_rate: float
    loss_rate: float
    push_rate: float
    blackjack_rate: float
    
    # Financial performance
    net_result: float
    roi_percentage: float
    average_bet: float
    
    # Accuracy metrics
    counting_accuracy: float
    strategy_adherence: float
    deviation_accuracy: float
    
    # Decision analysis
    most_common_mistakes: List[Tuple[str, int]]  # (decision_key, count)
    best_decisions: List[Tuple[str, float]]  # (decision_key, accuracy)
    
    # Trends
    accuracy_trend: TrendData
    performance_trend: TrendData
    
    def duration_minutes(self) -> float:
        """Calculate session duration in minutes."""
        if self.end_time is None:
            return 0.0
        return (self.end_time - self.start_time).total_seconds() / 60.0
    
    def hands_per_hour(self) -> float:
        """Calculate hands played per hour."""
        duration = self.duration_minutes()
        if duration == 0:
            return 0.0
        return (self.hands_played / duration) * 60.0


class PerformanceTracker:
    """Tracks and analyzes player performance over time."""
    
    def __init__(self):
        """Initialize the performance tracker."""
        self.decisions: List[DecisionAnalysis] = []
        self.accuracy_history: List[AccuracyPoint] = []
        self.counting_trend = TrendData()
        self.strategy_trend = TrendData()
        self.performance_trend = TrendData()
        
        # Decision grouping for analysis
        self.decision_groups: Dict[str, List[DecisionAnalysis]] = defaultdict(list)
        
        # Session tracking
        self.current_session_id: Optional[str] = None
        self.session_start: Optional[datetime] = None
    
    def start_session(self, session_id: str) -> None:
        """Start tracking a new session."""
        self.current_session_id = session_id
        self.session_start = datetime.now()
    
    def track_decision(self, situation: GameSituation, user_action: Action,
                      optimal_action: Action, true_count: Optional[float] = None) -> None:
        """Track a player decision for analysis."""
        is_correct = user_action == optimal_action
        is_deviation = true_count is not None and abs(true_count) >= 2.0  # Simplified deviation detection
        
        decision = DecisionAnalysis(
            situation=situation,
            user_action=user_action,
            optimal_action=optimal_action,
            is_correct=is_correct,
            is_deviation=is_deviation,
            true_count=true_count
        )
        
        self.decisions.append(decision)
        
        # Group decision for analysis
        key = decision.decision_key()
        self.decision_groups[key].append(decision)
        
        # Update strategy trend
        recent_decisions = self.decisions[-20:]  # Last 20 decisions
        if recent_decisions:
            accuracy = sum(1 for d in recent_decisions if d.is_correct) / len(recent_decisions) * 100
            self.strategy_trend.add_point(datetime.now(), accuracy)
    
    def track_count_estimate(self, user_count: int, actual_count: int) -> None:
        """Track a counting estimate for accuracy analysis."""
        error = abs(user_count - actual_count)
        accuracy = 100.0 if error == 0 else max(0, 100 - (error * 10))  # Simplified accuracy calculation
        
        self.counting_trend.add_point(datetime.now(), accuracy)
    
    def update_accuracy_history(self, counting_accuracy: float, strategy_accuracy: float,
                              hands_played: int) -> None:
        """Update the accuracy history with a new data point."""
        point = AccuracyPoint(
            timestamp=datetime.now(),
            counting_accuracy=counting_accuracy,
            strategy_accuracy=strategy_accuracy,
            hands_played=hands_played,
            session_id=self.current_session_id
        )
        
        self.accuracy_history.append(point)
        
        # Update performance trend (combined metric)
        combined_performance = (counting_accuracy + strategy_accuracy) / 2
        self.performance_trend.add_point(datetime.now(), combined_performance)
    
    def get_accuracy_trends(self, hours: int = 24) -> List[AccuracyPoint]:
        """Get accuracy trends for the specified time period."""
        cutoff = datetime.now() - timedelta(hours=hours)
        return [point for point in self.accuracy_history if point.timestamp >= cutoff]
    
    def analyze_decision_patterns(self) -> Dict[str, Dict[str, any]]:
        """Analyze patterns in player decisions."""
        analysis = {}
        
        for decision_key, decisions in self.decision_groups.items():
            if len(decisions) < 3:  # Need at least 3 decisions for meaningful analysis
                continue
            
            correct_count = sum(1 for d in decisions if d.is_correct)
            total_count = len(decisions)
            accuracy = (correct_count / total_count) * 100
            
            # Find most common mistake
            incorrect_decisions = [d for d in decisions if not d.is_correct]
            mistake_actions = defaultdict(int)
            for d in incorrect_decisions:
                mistake_actions[d.user_action.value] += 1
            
            most_common_mistake = max(mistake_actions.items(), key=lambda x: x[1]) if mistake_actions else None
            
            analysis[decision_key] = {
                "total_decisions": total_count,
                "correct_decisions": correct_count,
                "accuracy_percentage": accuracy,
                "most_common_mistake": most_common_mistake,
                "optimal_action": decisions[0].optimal_action.value,  # Should be consistent
                "recent_trend": self._get_recent_accuracy_for_decision(decision_key)
            }
        
        return analysis
    
    def _get_recent_accuracy_for_decision(self, decision_key: str, count: int = 10) -> float:
        """Get recent accuracy for a specific decision type."""
        decisions = self.decision_groups[decision_key]
        recent_decisions = decisions[-count:] if len(decisions) >= count else decisions
        
        if not recent_decisions:
            return 0.0
        
        correct = sum(1 for d in recent_decisions if d.is_correct)
        return (correct / len(recent_decisions)) * 100
    
    def get_improvement_suggestions(self) -> List[str]:
        """Generate improvement suggestions based on performance analysis."""
        suggestions = []
        
        # Analyze counting accuracy
        if self.counting_trend.values:
            recent_counting = self.counting_trend.get_recent_trend(hours=2)
            if recent_counting.average() < 70:
                suggestions.append("Focus on counting accuracy - consider practicing with fewer distractions")
        
        # Analyze strategy adherence
        if self.strategy_trend.values:
            recent_strategy = self.strategy_trend.get_recent_trend(hours=2)
            if recent_strategy.average() < 80:
                suggestions.append("Review basic strategy - several suboptimal decisions detected")
        
        # Analyze specific decision patterns
        decision_analysis = self.analyze_decision_patterns()
        for decision_key, analysis in decision_analysis.items():
            if analysis["accuracy_percentage"] < 60 and analysis["total_decisions"] >= 5:
                suggestions.append(f"Practice {decision_key} situations - accuracy is {analysis['accuracy_percentage']:.1f}%")
        
        # Check for improvement trends
        if self.performance_trend.values and len(self.performance_trend.values) >= 10:
            improvement_rate = self.performance_trend.improvement_rate()
            if improvement_rate < 0:
                suggestions.append("Performance is declining - consider taking a break or reviewing fundamentals")
            elif improvement_rate > 1:
                suggestions.append("Great improvement trend! Keep up the consistent practice")
        
        return suggestions[:5]  # Limit to top 5 suggestions
    
    def generate_session_report(self, session_stats) -> SessionReport:
        """Generate a comprehensive session report."""
        # Get session-specific data
        session_decisions = [d for d in self.decisions 
                           if self.session_start and d.timestamp >= self.session_start]
        
        # Analyze mistakes
        mistake_counts = defaultdict(int)
        decision_accuracies = defaultdict(list)
        
        for decision in session_decisions:
            key = decision.decision_key()
            decision_accuracies[key].append(decision.is_correct)
            if not decision.is_correct:
                mistake_counts[key] += 1
        
        # Most common mistakes
        most_common_mistakes = sorted(mistake_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Best decisions (highest accuracy with sufficient sample size)
        best_decisions = []
        for key, correct_list in decision_accuracies.items():
            if len(correct_list) >= 3:  # Minimum sample size
                accuracy = (sum(correct_list) / len(correct_list)) * 100
                best_decisions.append((key, accuracy))
        best_decisions = sorted(best_decisions, key=lambda x: x[1], reverse=True)[:5]
        
        # Get trend data for the session
        session_accuracy_trend = TrendData()
        session_performance_trend = TrendData()
        
        if self.session_start:
            for point in self.accuracy_history:
                if point.timestamp >= self.session_start:
                    session_accuracy_trend.add_point(point.timestamp, point.strategy_accuracy)
                    session_performance_trend.add_point(
                        point.timestamp, 
                        (point.counting_accuracy + point.strategy_accuracy) / 2
                    )
        
        return SessionReport(
            session_id=self.current_session_id or "unknown",
            start_time=self.session_start or datetime.now(),
            end_time=datetime.now(),
            hands_played=session_stats.hands_played,
            win_rate=session_stats.win_rate(),
            loss_rate=session_stats.loss_rate(),
            push_rate=session_stats.push_rate(),
            blackjack_rate=session_stats.blackjack_rate(),
            net_result=session_stats.net_result,
            roi_percentage=session_stats.return_on_investment(),
            average_bet=session_stats.average_bet(),
            counting_accuracy=session_stats.counting_accuracy.accuracy_percentage(),
            strategy_adherence=session_stats.strategy_accuracy.adherence_percentage(),
            deviation_accuracy=session_stats.strategy_accuracy.deviation_accuracy(),
            most_common_mistakes=most_common_mistakes,
            best_decisions=best_decisions,
            accuracy_trend=session_accuracy_trend,
            performance_trend=session_performance_trend
        )
    
    def get_performance_summary(self) -> Dict[str, any]:
        """Get a summary of overall performance metrics."""
        return {
            "total_decisions": len(self.decisions),
            "total_accuracy_points": len(self.accuracy_history),
            "current_counting_accuracy": self.counting_trend.latest() or 0.0,
            "current_strategy_accuracy": self.strategy_trend.latest() or 0.0,
            "overall_performance": self.performance_trend.average(),
            "improvement_rate": self.performance_trend.improvement_rate(),
            "decision_patterns_analyzed": len(self.decision_groups),
            "improvement_suggestions": self.get_improvement_suggestions()
        }