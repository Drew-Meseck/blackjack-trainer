"""Integration tests for session persistence system."""

import unittest
import tempfile
import shutil
from datetime import datetime

from src.session import SessionManager, SessionData, SessionMetadata, HandRecord
from src.models import GameRules, Card, Suit, Rank, Action, GameResult, Outcome
from src.analytics.session_stats import SessionStats


class TestSessionIntegration(unittest.TestCase):
    """Integration tests for the complete session persistence workflow."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.session_manager = SessionManager(self.temp_dir)
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)
    
    def test_complete_session_workflow(self):
        """Test a complete session save/load workflow."""
        # Create a realistic session with game data
        rules = GameRules(
            dealer_hits_soft_17=True,
            double_after_split=True,
            surrender_allowed=False,
            num_decks=6,
            penetration=0.75,
            blackjack_payout=1.5
        )
        
        stats = SessionStats(session_id="integration-test")
        metadata = SessionMetadata(
            session_id="integration-test",
            name="Integration Test Session"
        )
        
        # Create session with some hand history
        session = SessionData(
            session_id="integration-test",
            metadata=metadata,
            rules=rules,
            stats=stats,
            counting_system="Hi-Lo"
        )
        
        # Add some hand records
        for i in range(3):
            player_cards = [
                Card(Suit.HEARTS, Rank.ACE),
                Card(Suit.SPADES, Rank.KING)
            ]
            dealer_cards = [
                Card(Suit.DIAMONDS, Rank.QUEEN),
                Card(Suit.CLUBS, Rank.SEVEN)
            ]
            
            result = GameResult(
                outcome=Outcome.BLACKJACK if i == 0 else Outcome.WIN,
                player_total=21,
                dealer_total=17,
                payout=1.5 if i == 0 else 1.0
            )
            
            hand_record = HandRecord(
                hand_number=i + 1,
                player_cards=player_cards,
                dealer_cards=dealer_cards,
                user_actions=[Action.STAND],
                optimal_actions=[Action.STAND],
                running_count=i + 1,
                true_count=(i + 1) * 0.5,
                result=result,
                bet_amount=10.0
            )
            
            session.add_hand_record(hand_record)
            stats.update_hand_result(result, 10.0)
        
        # Save the session
        session_id = self.session_manager.save_session(session, "Test Session")
        self.assertEqual(session_id, "integration-test")
        
        # Verify session appears in list
        sessions = self.session_manager.list_sessions()
        self.assertEqual(len(sessions), 1)
        self.assertEqual(sessions[0].session_id, "integration-test")
        self.assertEqual(sessions[0].name, "Test Session")
        self.assertEqual(sessions[0].hands_played, 3)
        
        # Load the session back
        loaded_session = self.session_manager.load_session("integration-test")
        
        # Verify all data was preserved
        self.assertEqual(loaded_session.session_id, "integration-test")
        self.assertEqual(loaded_session.counting_system, "Hi-Lo")
        self.assertEqual(loaded_session.rules.num_decks, 6)
        self.assertEqual(loaded_session.rules.blackjack_payout, 1.5)
        self.assertEqual(len(loaded_session.hands_history), 3)
        
        # Verify hand records
        first_hand = loaded_session.hands_history[0]
        self.assertEqual(first_hand.hand_number, 1)
        self.assertEqual(first_hand.running_count, 1)
        self.assertEqual(first_hand.true_count, 0.5)
        self.assertEqual(first_hand.result.outcome, Outcome.BLACKJACK)
        self.assertEqual(first_hand.bet_amount, 10.0)
        
        # Verify stats were preserved
        self.assertEqual(loaded_session.stats.hands_played, 3)
        self.assertEqual(loaded_session.stats.total_bet, 30.0)
        
        # Test session metadata
        metadata = self.session_manager.get_session_metadata("integration-test")
        self.assertIsNotNone(metadata)
        self.assertEqual(metadata.name, "Test Session")
        self.assertEqual(metadata.hands_played, 3)
    
    def test_multiple_sessions_management(self):
        """Test managing multiple sessions."""
        # Create and save multiple sessions
        session_ids = []
        
        for i in range(3):
            rules = GameRules(num_decks=6)
            stats = SessionStats(session_id=f"session-{i}")
            metadata = SessionMetadata(
                session_id=f"session-{i}",
                name=f"Session {i}"
            )
            
            session = SessionData(
                session_id=f"session-{i}",
                metadata=metadata,
                rules=rules,
                stats=stats
            )
            
            session_id = self.session_manager.save_session(session)
            session_ids.append(session_id)
        
        # Verify all sessions exist
        sessions = self.session_manager.list_sessions()
        self.assertEqual(len(sessions), 3)
        
        # Verify we can load each session
        for session_id in session_ids:
            loaded_session = self.session_manager.load_session(session_id)
            self.assertEqual(loaded_session.session_id, session_id)
        
        # Delete one session
        self.assertTrue(self.session_manager.delete_session("session-1"))
        
        # Verify it's gone
        sessions = self.session_manager.list_sessions()
        self.assertEqual(len(sessions), 2)
        self.assertFalse(self.session_manager.session_exists("session-1"))
        
        # Verify others still exist
        self.assertTrue(self.session_manager.session_exists("session-0"))
        self.assertTrue(self.session_manager.session_exists("session-2"))
    
    def test_session_persistence_across_manager_instances(self):
        """Test that sessions persist across different SessionManager instances."""
        # Create and save a session
        rules = GameRules(num_decks=8)
        stats = SessionStats(session_id="persistence-test")
        metadata = SessionMetadata(
            session_id="persistence-test",
            name="Persistence Test"
        )
        
        session = SessionData(
            session_id="persistence-test",
            metadata=metadata,
            rules=rules,
            stats=stats
        )
        
        self.session_manager.save_session(session)
        
        # Create a new SessionManager instance pointing to same directory
        new_manager = SessionManager(self.temp_dir)
        
        # Verify the session is still available
        self.assertTrue(new_manager.session_exists("persistence-test"))
        
        loaded_session = new_manager.load_session("persistence-test")
        self.assertEqual(loaded_session.session_id, "persistence-test")
        self.assertEqual(loaded_session.metadata.name, "Persistence Test")
        self.assertEqual(loaded_session.rules.num_decks, 8)


if __name__ == '__main__':
    unittest.main()