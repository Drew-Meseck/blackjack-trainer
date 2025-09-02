"""Session statistics tracking for blackjack simulation."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional
from ..models import GameResult, Outcome, Action


@dataclass
class CountingAccuracy:
    """Tracks counting accuracy statistics."""
    total_estimates: int = 0
    correct_estimates: int = 0
    total_error: float = 0.0
    max_error: float = 0.0
    
    def accuracy_percentage(self) -> float:
        """Calculate accuracy as percentage of correct estimates."""
        if self.total_estimates == 0:
            return 0.0
        return (self.correct_estimates / self.total_estimates) * 100.0
    
    def average_error(self) -> float:
        """Calculate average absolute error."""
        if self.total_estimates == 0:
            return 0.0
        return self.total_error / self.total_estimates


@dataclass
class StrategyAccuracy:
    """Tracks strategy adherence statistics."""
    total_decisions: int = 0
    correct_decisions: int = 0
    basic_strategy_decisions: int = 0
    deviation_decisions: int = 0
    correct_deviations: int = 0
    
    def adherence_percentage(self) -> float:
        """Calculate overall strategy adherence percentage."""
        if self.total_decisions == 0:
            return 0.0
        return (self.correct_decisions / self.total_decisions) * 100.0
    
    def deviation_accuracy(self) -> float:
        """Calculate accuracy of deviation decisions."""
        if self.deviation_decisions == 0:
            return 0.0
        return (self.correct_deviations / self.deviation_decisions) * 100.0


@dataclass
class SessionStats:
    """Comprehensive session statistics tracking."""
    
    # Session metadata
    session_id: str = ""
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    # Hand results
    hands_played: int = 0
    hands_won: int = 0
    hands_lost: int = 0
    hands_pushed: int = 0
    blackjacks: int = 0
    surrenders: int = 0
    
    # Financial tracking
    total_bet: float = 0.0
    total_winnings: float = 0.0
    net_result: float = 0.0
    
    # Counting accuracy
    counting_accuracy: CountingAccuracy = field(default_factory=CountingAccuracy)
    
    # Strategy adherence
    strategy_accuracy: StrategyAccuracy = field(default_factory=StrategyAccuracy)
    
    # Detailed tracking
    results_history: List[GameResult] = field(default_factory=list)
    
    def __post_init__(self):
        """Initialize session if not already set."""
        if self.start_time is None:
            self.start_time = datetime.now()
    
    def update_hand_result(self, result: GameResult, bet_amount: float = 1.0) -> None:
        """Update statistics with a new hand result."""
        self.hands_played += 1
        self.results_history.append(result)
        
        # Update win/loss counts
        if result.is_winning_result():
            self.hands_won += 1
        elif result.is_losing_result():
            self.hands_lost += 1
        else:
            self.hands_pushed += 1
        
        # Update specific outcome counts
        if result.outcome == Outcome.BLACKJACK:
            self.blackjacks += 1
        elif result.outcome == Outcome.SURRENDER:
            self.surrenders += 1
        
        # Update financial tracking
        self.total_bet += bet_amount
        hand_result = result.net_result(bet_amount)
        self.total_winnings += max(0, hand_result)  # Only positive results
        self.net_result += hand_result
    
    def update_counting_accuracy(self, user_count: int, actual_count: int, tolerance: int = 0) -> None:
        """Update counting accuracy statistics."""
        self.counting_accuracy.total_estimates += 1
        
        error = abs(user_count - actual_count)
        self.counting_accuracy.total_error += error
        self.counting_accuracy.max_error = max(self.counting_accuracy.max_error, error)
        
        if error <= tolerance:
            self.counting_accuracy.correct_estimates += 1
    
    def update_strategy_adherence(self, user_action: Action, optimal_action: Action, 
                                is_deviation: bool = False) -> None:
        """Update strategy adherence statistics."""
        self.strategy_accuracy.total_decisions += 1
        
        if is_deviation:
            self.strategy_accuracy.deviation_decisions += 1
            if user_action == optimal_action:
                self.strategy_accuracy.correct_deviations += 1
        else:
            self.strategy_accuracy.basic_strategy_decisions += 1
        
        if user_action == optimal_action:
            self.strategy_accuracy.correct_decisions += 1
    
    def win_rate(self) -> float:
        """Calculate win rate percentage."""
        if self.hands_played == 0:
            return 0.0
        return (self.hands_won / self.hands_played) * 100.0
    
    def loss_rate(self) -> float:
        """Calculate loss rate percentage."""
        if self.hands_played == 0:
            return 0.0
        return (self.hands_lost / self.hands_played) * 100.0
    
    def push_rate(self) -> float:
        """Calculate push rate percentage."""
        if self.hands_played == 0:
            return 0.0
        return (self.hands_pushed / self.hands_played) * 100.0
    
    def blackjack_rate(self) -> float:
        """Calculate blackjack rate percentage."""
        if self.hands_played == 0:
            return 0.0
        return (self.blackjacks / self.hands_played) * 100.0
    
    def average_bet(self) -> float:
        """Calculate average bet size."""
        if self.hands_played == 0:
            return 0.0
        return self.total_bet / self.hands_played
    
    def return_on_investment(self) -> float:
        """Calculate ROI as percentage."""
        if self.total_bet == 0:
            return 0.0
        return (self.net_result / self.total_bet) * 100.0
    
    def session_duration(self) -> Optional[float]:
        """Calculate session duration in minutes."""
        if self.start_time is None:
            return None
        
        end = self.end_time or datetime.now()
        duration = end - self.start_time
        return duration.total_seconds() / 60.0
    
    def hands_per_hour(self) -> float:
        """Calculate hands played per hour."""
        duration = self.session_duration()
        if duration is None or duration == 0:
            return 0.0
        
        hours = duration / 60.0
        return self.hands_played / hours
    
    def end_session(self) -> None:
        """Mark the session as ended."""
        self.end_time = datetime.now()
    
    def generate_summary(self) -> Dict[str, any]:
        """Generate a comprehensive statistics summary."""
        return {
            "session_info": {
                "session_id": self.session_id,
                "start_time": self.start_time.isoformat() if self.start_time else None,
                "end_time": self.end_time.isoformat() if self.end_time else None,
                "duration_minutes": self.session_duration(),
                "hands_per_hour": self.hands_per_hour()
            },
            "hand_results": {
                "hands_played": self.hands_played,
                "hands_won": self.hands_won,
                "hands_lost": self.hands_lost,
                "hands_pushed": self.hands_pushed,
                "blackjacks": self.blackjacks,
                "surrenders": self.surrenders,
                "win_rate": self.win_rate(),
                "loss_rate": self.loss_rate(),
                "push_rate": self.push_rate(),
                "blackjack_rate": self.blackjack_rate()
            },
            "financial": {
                "total_bet": self.total_bet,
                "total_winnings": self.total_winnings,
                "net_result": self.net_result,
                "average_bet": self.average_bet(),
                "roi_percentage": self.return_on_investment()
            },
            "counting_accuracy": {
                "total_estimates": self.counting_accuracy.total_estimates,
                "correct_estimates": self.counting_accuracy.correct_estimates,
                "accuracy_percentage": self.counting_accuracy.accuracy_percentage(),
                "average_error": self.counting_accuracy.average_error(),
                "max_error": self.counting_accuracy.max_error
            },
            "strategy_adherence": {
                "total_decisions": self.strategy_accuracy.total_decisions,
                "correct_decisions": self.strategy_accuracy.correct_decisions,
                "adherence_percentage": self.strategy_accuracy.adherence_percentage(),
                "basic_strategy_decisions": self.strategy_accuracy.basic_strategy_decisions,
                "deviation_decisions": self.strategy_accuracy.deviation_decisions,
                "deviation_accuracy": self.strategy_accuracy.deviation_accuracy()
            }
        }
    
    def __str__(self) -> str:
        """String representation of session statistics."""
        summary = self.generate_summary()
        return (
            f"Session {self.session_id}:\n"
            f"  Hands: {self.hands_played} (W:{self.hands_won} L:{self.hands_lost} P:{self.hands_pushed})\n"
            f"  Win Rate: {self.win_rate():.1f}%\n"
            f"  Net Result: {self.net_result:+.2f} (ROI: {self.return_on_investment():+.1f}%)\n"
            f"  Counting Accuracy: {self.counting_accuracy.accuracy_percentage():.1f}%\n"
            f"  Strategy Adherence: {self.strategy_accuracy.adherence_percentage():.1f}%"
        )