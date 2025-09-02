"""Session data models for persistence."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
from ..models import Card, Action, GameResult, GameRules
from ..analytics.session_stats import SessionStats


@dataclass
class HandRecord:
    """Record of a single hand played during a session."""
    
    hand_number: int
    player_cards: List[Card]
    dealer_cards: List[Card]
    user_actions: List[Action]
    optimal_actions: List[Action]
    running_count: int
    true_count: float
    result: GameResult
    bet_amount: float = 1.0
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        """Set timestamp if not provided."""
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "hand_number": self.hand_number,
            "player_cards": [{"suit": card.suit.value, "rank": card.rank.value} for card in self.player_cards],
            "dealer_cards": [{"suit": card.suit.value, "rank": card.rank.value} for card in self.dealer_cards],
            "user_actions": [action.value for action in self.user_actions],
            "optimal_actions": [action.value for action in self.optimal_actions],
            "running_count": self.running_count,
            "true_count": self.true_count,
            "result": {
                "outcome": self.result.outcome.value,
                "player_total": self.result.player_total,
                "dealer_total": self.result.dealer_total,
                "payout": self.result.payout,
                "player_busted": self.result.player_busted,
                "dealer_busted": self.result.dealer_busted,
                "player_blackjack": self.result.player_blackjack,
                "dealer_blackjack": self.result.dealer_blackjack
            },
            "bet_amount": self.bet_amount,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HandRecord':
        """Create HandRecord from dictionary."""
        from ..models import Card, Suit, Rank, Action, GameResult, Outcome
        
        # Reconstruct cards
        player_cards = [Card(Suit(card["suit"]), Rank(card["rank"])) for card in data["player_cards"]]
        dealer_cards = [Card(Suit(card["suit"]), Rank(card["rank"])) for card in data["dealer_cards"]]
        
        # Reconstruct actions
        user_actions = [Action(action) for action in data["user_actions"]]
        optimal_actions = [Action(action) for action in data["optimal_actions"]]
        
        # Reconstruct result
        result_data = data["result"]
        result = GameResult(
            outcome=Outcome(result_data["outcome"]),
            player_total=result_data["player_total"],
            dealer_total=result_data["dealer_total"],
            payout=result_data["payout"],
            player_busted=result_data["player_busted"],
            dealer_busted=result_data["dealer_busted"],
            player_blackjack=result_data["player_blackjack"],
            dealer_blackjack=result_data["dealer_blackjack"]
        )
        
        return cls(
            hand_number=data["hand_number"],
            player_cards=player_cards,
            dealer_cards=dealer_cards,
            user_actions=user_actions,
            optimal_actions=optimal_actions,
            running_count=data["running_count"],
            true_count=data["true_count"],
            result=result,
            bet_amount=data["bet_amount"],
            timestamp=datetime.fromisoformat(data["timestamp"]) if data["timestamp"] else None
        )


@dataclass
class SessionMetadata:
    """Metadata for a saved session."""
    
    session_id: str
    name: Optional[str] = None
    created_time: Optional[datetime] = None
    last_modified: Optional[datetime] = None
    hands_played: int = 0
    duration_minutes: Optional[float] = None
    rules_summary: str = ""
    
    def __post_init__(self):
        """Set default timestamps."""
        if self.created_time is None:
            self.created_time = datetime.now()
        if self.last_modified is None:
            self.last_modified = self.created_time
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "session_id": self.session_id,
            "name": self.name,
            "created_time": self.created_time.isoformat() if self.created_time else None,
            "last_modified": self.last_modified.isoformat() if self.last_modified else None,
            "hands_played": self.hands_played,
            "duration_minutes": self.duration_minutes,
            "rules_summary": self.rules_summary
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionMetadata':
        """Create SessionMetadata from dictionary."""
        return cls(
            session_id=data["session_id"],
            name=data.get("name"),
            created_time=datetime.fromisoformat(data["created_time"]) if data.get("created_time") else None,
            last_modified=datetime.fromisoformat(data["last_modified"]) if data.get("last_modified") else None,
            hands_played=data.get("hands_played", 0),
            duration_minutes=data.get("duration_minutes"),
            rules_summary=data.get("rules_summary", "")
        )


@dataclass
class SessionData:
    """Complete session data for persistence."""
    
    session_id: str
    metadata: SessionMetadata
    rules: GameRules
    stats: SessionStats
    hands_history: List[HandRecord] = field(default_factory=list)
    counting_system: str = "Hi-Lo"
    
    def __post_init__(self):
        """Ensure metadata session_id matches."""
        self.metadata.session_id = self.session_id
    
    def add_hand_record(self, record: HandRecord) -> None:
        """Add a hand record to the session."""
        self.hands_history.append(record)
        self.metadata.hands_played = len(self.hands_history)
        self.metadata.last_modified = datetime.now()
    
    def update_metadata(self) -> None:
        """Update metadata based on current session state."""
        self.metadata.hands_played = len(self.hands_history)
        self.metadata.duration_minutes = self.stats.session_duration()
        self.metadata.last_modified = datetime.now()
        
        # Create rules summary
        self.metadata.rules_summary = (
            f"{self.rules.num_decks} decks, "
            f"{self.rules.penetration:.0%} penetration, "
            f"{'H17' if self.rules.dealer_hits_soft_17 else 'S17'}, "
            f"{'DAS' if self.rules.double_after_split else 'No DAS'}"
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        self.update_metadata()
        
        return {
            "session_id": self.session_id,
            "metadata": self.metadata.to_dict(),
            "rules": {
                "dealer_hits_soft_17": self.rules.dealer_hits_soft_17,
                "double_after_split": self.rules.double_after_split,
                "surrender_allowed": self.rules.surrender_allowed,
                "num_decks": self.rules.num_decks,
                "penetration": self.rules.penetration,
                "blackjack_payout": self.rules.blackjack_payout
            },
            "stats": self._serialize_stats(),
            "hands_history": [hand.to_dict() for hand in self.hands_history],
            "counting_system": self.counting_system
        }
    
    def _serialize_stats(self) -> Dict[str, Any]:
        """Serialize session stats to dictionary."""
        return {
            "session_id": self.stats.session_id,
            "start_time": self.stats.start_time.isoformat() if self.stats.start_time else None,
            "end_time": self.stats.end_time.isoformat() if self.stats.end_time else None,
            "hands_played": self.stats.hands_played,
            "hands_won": self.stats.hands_won,
            "hands_lost": self.stats.hands_lost,
            "hands_pushed": self.stats.hands_pushed,
            "blackjacks": self.stats.blackjacks,
            "surrenders": self.stats.surrenders,
            "total_bet": self.stats.total_bet,
            "total_winnings": self.stats.total_winnings,
            "net_result": self.stats.net_result,
            "counting_accuracy": {
                "total_estimates": self.stats.counting_accuracy.total_estimates,
                "correct_estimates": self.stats.counting_accuracy.correct_estimates,
                "total_error": self.stats.counting_accuracy.total_error,
                "max_error": self.stats.counting_accuracy.max_error
            },
            "strategy_accuracy": {
                "total_decisions": self.stats.strategy_accuracy.total_decisions,
                "correct_decisions": self.stats.strategy_accuracy.correct_decisions,
                "basic_strategy_decisions": self.stats.strategy_accuracy.basic_strategy_decisions,
                "deviation_decisions": self.stats.strategy_accuracy.deviation_decisions,
                "correct_deviations": self.stats.strategy_accuracy.correct_deviations
            },
            "results_history": [
                {
                    "outcome": result.outcome.value,
                    "player_total": result.player_total,
                    "dealer_total": result.dealer_total,
                    "payout": result.payout,
                    "player_busted": result.player_busted,
                    "dealer_busted": result.dealer_busted,
                    "player_blackjack": result.player_blackjack,
                    "dealer_blackjack": result.dealer_blackjack
                }
                for result in self.stats.results_history
            ]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionData':
        """Create SessionData from dictionary."""
        from ..models import GameRules, GameResult, Outcome
        from ..analytics.session_stats import SessionStats, CountingAccuracy, StrategyAccuracy
        
        # Reconstruct metadata
        metadata = SessionMetadata.from_dict(data["metadata"])
        
        # Reconstruct rules
        rules_data = data["rules"]
        rules = GameRules(
            dealer_hits_soft_17=rules_data["dealer_hits_soft_17"],
            double_after_split=rules_data["double_after_split"],
            surrender_allowed=rules_data["surrender_allowed"],
            num_decks=rules_data["num_decks"],
            penetration=rules_data["penetration"],
            blackjack_payout=rules_data["blackjack_payout"]
        )
        
        # Reconstruct stats
        stats_data = data["stats"]
        
        # Reconstruct counting accuracy
        counting_data = stats_data["counting_accuracy"]
        counting_accuracy = CountingAccuracy(
            total_estimates=counting_data["total_estimates"],
            correct_estimates=counting_data["correct_estimates"],
            total_error=counting_data["total_error"],
            max_error=counting_data["max_error"]
        )
        
        # Reconstruct strategy accuracy
        strategy_data = stats_data["strategy_accuracy"]
        strategy_accuracy = StrategyAccuracy(
            total_decisions=strategy_data["total_decisions"],
            correct_decisions=strategy_data["correct_decisions"],
            basic_strategy_decisions=strategy_data["basic_strategy_decisions"],
            deviation_decisions=strategy_data["deviation_decisions"],
            correct_deviations=strategy_data["correct_deviations"]
        )
        
        # Reconstruct results history
        results_history = []
        for result_data in stats_data["results_history"]:
            result = GameResult(
                outcome=Outcome(result_data["outcome"]),
                player_total=result_data["player_total"],
                dealer_total=result_data["dealer_total"],
                payout=result_data["payout"],
                player_busted=result_data["player_busted"],
                dealer_busted=result_data["dealer_busted"],
                player_blackjack=result_data["player_blackjack"],
                dealer_blackjack=result_data["dealer_blackjack"]
            )
            results_history.append(result)
        
        # Create stats object
        stats = SessionStats(
            session_id=stats_data["session_id"],
            start_time=datetime.fromisoformat(stats_data["start_time"]) if stats_data["start_time"] else None,
            end_time=datetime.fromisoformat(stats_data["end_time"]) if stats_data["end_time"] else None,
            hands_played=stats_data["hands_played"],
            hands_won=stats_data["hands_won"],
            hands_lost=stats_data["hands_lost"],
            hands_pushed=stats_data["hands_pushed"],
            blackjacks=stats_data["blackjacks"],
            surrenders=stats_data["surrenders"],
            total_bet=stats_data["total_bet"],
            total_winnings=stats_data["total_winnings"],
            net_result=stats_data["net_result"],
            counting_accuracy=counting_accuracy,
            strategy_accuracy=strategy_accuracy,
            results_history=results_history
        )
        
        # Reconstruct hands history
        hands_history = [HandRecord.from_dict(hand_data) for hand_data in data["hands_history"]]
        
        return cls(
            session_id=data["session_id"],
            metadata=metadata,
            rules=rules,
            stats=stats,
            hands_history=hands_history,
            counting_system=data.get("counting_system", "Hi-Lo")
        )