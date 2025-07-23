"""Unit tests for session manager."""

import unittest
import tempfile
import shutil
import json
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, mock_open

from src.session.session_manager import SessionManager, SessionManagerError, SessionNotFoundError, SessionCorruptedError
from src.session.session_data import SessionData, SessionMetadata, HandRecord
from src.models import GameRules, Card, Suit, Rank, Action, GameResult, Outcome
from src.analytics.session_stats import SessionStats


class TestSessionManager(unittest.TestCase):
    """Test cases for SessionManager class."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.session_manager = SessionManager(self.temp_dir)
        
        # Create test data
        self.test_rules = GameRules(
            dealer_hits_soft_17=True,
            double_after_split=True,
            surrender_allowed=False,
            num_decks=6,
            penetration=0.75
        )
        
        self.test_stats = SessionStats(
            session_id="test-session-1",
            hands_played=10,
            hands_won=5,
            hands_lost=4,
            hands_pushed=1
        )
        
        self.test_metadata = SessionMetadata(
            session_id="test-session-1",
            name="Test Session",
            hands_played=10
        )
        
        self.test_session = SessionData(
            session_id="test-session-1",
            metadata=self.test_metadata,
            rules=self.test_rules,
            stats=self.test_stats,
            counting_system="Hi-Lo"
        )
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)
    
    def test_init_creates_directory(self):
        """Test that SessionManager creates sessions directory."""
        new_dir = Path(self.temp_dir) / "new_sessions"
        manager = SessionManager(str(new_dir))
        
        self.assertTrue(new_dir.exists())
        self.assertTrue(new_dir.is_dir())
    
    def test_generate_session_id(self):
        """Test session ID generation."""
        session_id1 = self.session_manager.generate_session_id()
        session_id2 = self.session_manager.generate_session_id()
        
        self.assertIsInstance(session_id1, str)
        self.assertIsInstance(session_id2, str)
        self.assertNotEqual(session_id1, session_id2)
        self.assertEqual(len(session_id1), 36)  # UUID4 length
    
    def test_save_session_success(self):
        """Test successful session saving."""
        session_id = self.session_manager.save_session(self.test_session, "Test Session")
        
        self.assertEqual(session_id, "test-session-1")
        
        # Check file was created
        session_file = Path(self.temp_dir) / "test-session-1.json"
        self.assertTrue(session_file.exists())
        
        # Check metadata index was updated
        self.assertIn("test-session-1", self.session_manager._metadata_index)
        
        # Check index file was created
        index_file = Path(self.temp_dir) / "sessions_index.json"
        self.assertTrue(index_file.exists())
    
    def test_save_session_generates_id_if_missing(self):
        """Test that save_session generates ID if session doesn't have one."""
        self.test_session.session_id = ""
        
        session_id = self.session_manager.save_session(self.test_session)
        
        self.assertIsInstance(session_id, str)
        self.assertEqual(len(session_id), 36)
        self.assertEqual(self.test_session.session_id, session_id)
    
    def test_load_session_success(self):
        """Test successful session loading."""
        # First save a session
        self.session_manager.save_session(self.test_session)
        
        # Then load it
        loaded_session = self.session_manager.load_session("test-session-1")
        
        self.assertEqual(loaded_session.session_id, "test-session-1")
        self.assertEqual(loaded_session.rules.num_decks, 6)
        self.assertEqual(loaded_session.stats.hands_played, 10)
        self.assertEqual(loaded_session.counting_system, "Hi-Lo")
    
    def test_load_session_not_found(self):
        """Test loading non-existent session raises error."""
        with self.assertRaises(SessionNotFoundError):
            self.session_manager.load_session("non-existent-session")
    
    def test_load_session_corrupted_data(self):
        """Test loading corrupted session data raises error."""
        # Create a corrupted session file
        session_file = Path(self.temp_dir) / "corrupted-session.json"
        with open(session_file, 'w') as f:
            f.write("invalid json content")
        
        with self.assertRaises(SessionCorruptedError):
            self.session_manager.load_session("corrupted-session")
    
    def test_list_sessions_empty(self):
        """Test listing sessions when none exist."""
        sessions = self.session_manager.list_sessions()
        self.assertEqual(len(sessions), 0)
    
    def test_list_sessions_with_data(self):
        """Test listing sessions with saved data."""
        # Save multiple sessions with different metadata
        metadata1 = SessionMetadata(session_id="session-1", name="Session 1")
        metadata2 = SessionMetadata(session_id="session-2", name="Session 2")
        stats1 = SessionStats(session_id="session-1")
        stats2 = SessionStats(session_id="session-2")
        
        session1 = SessionData("session-1", metadata1, self.test_rules, stats1)
        session2 = SessionData("session-2", metadata2, self.test_rules, stats2)
        
        self.session_manager.save_session(session1, "Session 1")
        self.session_manager.save_session(session2, "Session 2")
        
        sessions = self.session_manager.list_sessions()
        
        self.assertEqual(len(sessions), 2)
        self.assertIsInstance(sessions[0], SessionMetadata)
        
        # Should be sorted by last modified (newest first)
        session_ids = [s.session_id for s in sessions]
        self.assertIn("session-1", session_ids)
        self.assertIn("session-2", session_ids)
    
    def test_delete_session_success(self):
        """Test successful session deletion."""
        # Save a session first
        self.session_manager.save_session(self.test_session)
        
        # Verify it exists
        self.assertTrue(self.session_manager.session_exists("test-session-1"))
        
        # Delete it
        result = self.session_manager.delete_session("test-session-1")
        
        self.assertTrue(result)
        self.assertFalse(self.session_manager.session_exists("test-session-1"))
        
        # Check file was removed
        session_file = Path(self.temp_dir) / "test-session-1.json"
        self.assertFalse(session_file.exists())
    
    def test_delete_session_not_found(self):
        """Test deleting non-existent session returns False."""
        result = self.session_manager.delete_session("non-existent-session")
        self.assertFalse(result)
    
    def test_session_exists(self):
        """Test session existence checking."""
        self.assertFalse(self.session_manager.session_exists("test-session-1"))
        
        self.session_manager.save_session(self.test_session)
        
        self.assertTrue(self.session_manager.session_exists("test-session-1"))
    
    def test_get_session_metadata(self):
        """Test getting session metadata."""
        # Non-existent session
        metadata = self.session_manager.get_session_metadata("non-existent")
        self.assertIsNone(metadata)
        
        # Existing session
        self.session_manager.save_session(self.test_session, "Test Session")
        metadata = self.session_manager.get_session_metadata("test-session-1")
        
        self.assertIsNotNone(metadata)
        self.assertEqual(metadata.session_id, "test-session-1")
        self.assertEqual(metadata.name, "Test Session")
    
    def test_cleanup_orphaned_files(self):
        """Test cleanup of orphaned session files."""
        # Create an orphaned file
        orphaned_file = Path(self.temp_dir) / "orphaned-session.json"
        with open(orphaned_file, 'w') as f:
            json.dump({"test": "data"}, f)
        
        # Save a legitimate session
        self.session_manager.save_session(self.test_session)
        
        # Run cleanup
        removed_count = self.session_manager.cleanup_orphaned_files()
        
        self.assertEqual(removed_count, 1)
        self.assertFalse(orphaned_file.exists())
        
        # Legitimate session should still exist
        session_file = Path(self.temp_dir) / "test-session-1.json"
        self.assertTrue(session_file.exists())
    
    def test_validate_all_sessions(self):
        """Test validation of all sessions."""
        # Save a good session
        self.session_manager.save_session(self.test_session)
        
        # Create a corrupted session file
        corrupted_file = Path(self.temp_dir) / "corrupted-session.json"
        with open(corrupted_file, 'w') as f:
            f.write("invalid json")
        
        # Add to metadata index to simulate corruption
        corrupted_metadata = SessionMetadata("corrupted-session")
        self.session_manager._metadata_index["corrupted-session"] = corrupted_metadata
        
        errors = self.session_manager.validate_all_sessions()
        
        self.assertEqual(len(errors), 1)
        self.assertIn("corrupted-session", errors)
        self.assertNotIn("test-session-1", errors)
    
    def test_get_storage_info(self):
        """Test getting storage information."""
        # Save some sessions
        self.session_manager.save_session(self.test_session)
        
        info = self.session_manager.get_storage_info()
        
        self.assertIn("sessions_directory", info)
        self.assertIn("total_sessions", info)
        self.assertIn("total_size_bytes", info)
        self.assertIn("total_size_mb", info)
        self.assertIn("metadata_index_exists", info)
        
        self.assertEqual(info["total_sessions"], 1)
        self.assertTrue(info["total_size_bytes"] > 0)
        self.assertTrue(info["metadata_index_exists"])
    
    @patch("builtins.open", side_effect=OSError("Permission denied"))
    def test_save_session_file_error(self, mock_file):
        """Test handling of file system errors during save."""
        with self.assertRaises(SessionManagerError):
            self.session_manager.save_session(self.test_session)
    
    def test_rebuild_metadata_index(self):
        """Test rebuilding corrupted metadata index."""
        # Save a session normally
        self.session_manager.save_session(self.test_session)
        
        # Corrupt the metadata index
        index_file = Path(self.temp_dir) / "sessions_index.json"
        with open(index_file, 'w') as f:
            f.write("invalid json")
        
        # Create new session manager (should rebuild index)
        new_manager = SessionManager(self.temp_dir)
        
        # Should have rebuilt the index
        self.assertIn("test-session-1", new_manager._metadata_index)
        self.assertEqual(len(new_manager.list_sessions()), 1)


class TestSessionData(unittest.TestCase):
    """Test cases for SessionData serialization."""
    
    def setUp(self):
        """Set up test data."""
        self.rules = GameRules(num_decks=6, penetration=0.75)
        self.stats = SessionStats(session_id="test-session")
        self.metadata = SessionMetadata(session_id="test-session", name="Test")
        
        # Create a hand record
        player_cards = [Card(Suit.HEARTS, Rank.ACE), Card(Suit.SPADES, Rank.KING)]
        dealer_cards = [Card(Suit.DIAMONDS, Rank.QUEEN), Card(Suit.CLUBS, Rank.SEVEN)]
        result = GameResult(Outcome.WIN, 21, 17, 1.0)
        
        self.hand_record = HandRecord(
            hand_number=1,
            player_cards=player_cards,
            dealer_cards=dealer_cards,
            user_actions=[Action.STAND],
            optimal_actions=[Action.STAND],
            running_count=2,
            true_count=1.5,
            result=result
        )
        
        self.session_data = SessionData(
            session_id="test-session",
            metadata=self.metadata,
            rules=self.rules,
            stats=self.stats,
            hands_history=[self.hand_record]
        )
    
    def test_session_data_serialization(self):
        """Test SessionData to_dict and from_dict."""
        # Serialize to dict
        data_dict = self.session_data.to_dict()
        
        # Verify structure
        self.assertIn("session_id", data_dict)
        self.assertIn("metadata", data_dict)
        self.assertIn("rules", data_dict)
        self.assertIn("stats", data_dict)
        self.assertIn("hands_history", data_dict)
        
        # Deserialize back
        restored_session = SessionData.from_dict(data_dict)
        
        # Verify data integrity
        self.assertEqual(restored_session.session_id, "test-session")
        self.assertEqual(restored_session.rules.num_decks, 6)
        self.assertEqual(len(restored_session.hands_history), 1)
        
        # Verify hand record
        restored_hand = restored_session.hands_history[0]
        self.assertEqual(restored_hand.hand_number, 1)
        self.assertEqual(restored_hand.running_count, 2)
        self.assertEqual(restored_hand.true_count, 1.5)
        self.assertEqual(len(restored_hand.player_cards), 2)
        self.assertEqual(restored_hand.result.outcome, Outcome.WIN)
    
    def test_hand_record_serialization(self):
        """Test HandRecord to_dict and from_dict."""
        # Serialize to dict
        hand_dict = self.hand_record.to_dict()
        
        # Verify structure
        self.assertIn("player_cards", hand_dict)
        self.assertIn("dealer_cards", hand_dict)
        self.assertIn("result", hand_dict)
        
        # Deserialize back
        restored_hand = HandRecord.from_dict(hand_dict)
        
        # Verify data integrity
        self.assertEqual(restored_hand.hand_number, 1)
        self.assertEqual(len(restored_hand.player_cards), 2)
        self.assertEqual(restored_hand.player_cards[0].suit, Suit.HEARTS)
        self.assertEqual(restored_hand.player_cards[0].rank, Rank.ACE)
        self.assertEqual(restored_hand.result.outcome, Outcome.WIN)
    
    def test_metadata_serialization(self):
        """Test SessionMetadata to_dict and from_dict."""
        metadata = SessionMetadata(
            session_id="test-session",
            name="Test Session",
            hands_played=10
        )
        
        # Serialize to dict
        metadata_dict = metadata.to_dict()
        
        # Deserialize back
        restored_metadata = SessionMetadata.from_dict(metadata_dict)
        
        # Verify data integrity
        self.assertEqual(restored_metadata.session_id, "test-session")
        self.assertEqual(restored_metadata.name, "Test Session")
        self.assertEqual(restored_metadata.hands_played, 10)


class TestSessionManagerEdgeCases(unittest.TestCase):
    """Test cases for SessionManager edge cases and error handling."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.session_manager = SessionManager(self.temp_dir)
        
        # Create test data
        self.test_rules = GameRules(num_decks=6, penetration=0.75)
        self.test_stats = SessionStats(session_id="test-session-1")
        self.test_metadata = SessionMetadata(session_id="test-session-1", name="Test Session")
        self.test_session = SessionData(
            session_id="test-session-1",
            metadata=self.test_metadata,
            rules=self.test_rules,
            stats=self.test_stats
        )
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)
    
    def test_recover_corrupted_sessions_without_removal(self):
        """Test recovery of corrupted sessions without removing them."""
        # Save a good session
        self.session_manager.save_session(self.test_session)
        
        # Create a corrupted session file
        corrupted_file = Path(self.temp_dir) / "corrupted-session.json"
        with open(corrupted_file, 'w') as f:
            f.write("invalid json content")
        
        # Add to metadata index
        corrupted_metadata = SessionMetadata("corrupted-session")
        self.session_manager._metadata_index["corrupted-session"] = corrupted_metadata
        
        # Run recovery without removal
        recovery_actions = self.session_manager.recover_corrupted_sessions(remove_corrupted=False)
        
        self.assertEqual(len(recovery_actions), 1)
        self.assertIn("corrupted-session", recovery_actions)
        self.assertIn("Corrupted session found", recovery_actions["corrupted-session"])
        
        # Corrupted session should still exist
        self.assertTrue(corrupted_file.exists())
        self.assertIn("corrupted-session", self.session_manager._metadata_index)
    
    def test_recover_corrupted_sessions_with_removal(self):
        """Test recovery of corrupted sessions with removal."""
        # Save a good session
        self.session_manager.save_session(self.test_session)
        
        # Create a corrupted session file
        corrupted_file = Path(self.temp_dir) / "corrupted-session.json"
        with open(corrupted_file, 'w') as f:
            f.write("invalid json content")
        
        # Add to metadata index
        corrupted_metadata = SessionMetadata("corrupted-session")
        self.session_manager._metadata_index["corrupted-session"] = corrupted_metadata
        
        # Run recovery with removal
        recovery_actions = self.session_manager.recover_corrupted_sessions(remove_corrupted=True)
        
        self.assertEqual(len(recovery_actions), 1)
        self.assertIn("corrupted-session", recovery_actions)
        self.assertIn("Removed corrupted session", recovery_actions["corrupted-session"])
        
        # Corrupted session should be removed
        self.assertFalse(corrupted_file.exists())
        self.assertNotIn("corrupted-session", self.session_manager._metadata_index)
        
        # Good session should still exist
        self.assertTrue(self.session_manager.session_exists("test-session-1"))
    
    def test_delete_multiple_sessions_success(self):
        """Test successful deletion of multiple sessions."""
        # Create multiple sessions
        sessions = []
        for i in range(3):
            session_id = f"test-session-{i}"
            metadata = SessionMetadata(session_id=session_id, name=f"Session {i}")
            stats = SessionStats(session_id=session_id)
            session = SessionData(session_id, metadata, self.test_rules, stats)
            sessions.append(session)
            self.session_manager.save_session(session)
        
        # Delete multiple sessions
        session_ids = ["test-session-0", "test-session-1", "test-session-2"]
        results = self.session_manager.delete_multiple_sessions(session_ids)
        
        # All should be deleted successfully
        for session_id in session_ids:
            self.assertTrue(results[session_id])
            self.assertFalse(self.session_manager.session_exists(session_id))
    
    def test_delete_multiple_sessions_partial_failure(self):
        """Test deletion of multiple sessions with some failures."""
        # Create one session
        self.session_manager.save_session(self.test_session)
        
        # Try to delete existing and non-existing sessions
        session_ids = ["test-session-1", "non-existent-session"]
        results = self.session_manager.delete_multiple_sessions(session_ids)
        
        # One should succeed, one should fail
        self.assertTrue(results["test-session-1"])
        self.assertFalse(results["non-existent-session"])
    
    def test_get_sessions_by_date_range(self):
        """Test filtering sessions by date range."""
        from datetime import timedelta
        
        base_time = datetime(2024, 1, 1, 12, 0, 0)
        
        # Create sessions with different creation times
        sessions_data = [
            ("session-1", base_time),
            ("session-2", base_time + timedelta(days=1)),
            ("session-3", base_time + timedelta(days=2)),
            ("session-4", base_time + timedelta(days=3))
        ]
        
        for session_id, created_time in sessions_data:
            metadata = SessionMetadata(session_id=session_id, created_time=created_time)
            stats = SessionStats(session_id=session_id)
            session = SessionData(session_id, metadata, self.test_rules, stats)
            self.session_manager.save_session(session)
        
        # Test date range filtering
        start_date = base_time + timedelta(hours=12)  # After session-1
        end_date = base_time + timedelta(days=2, hours=12)  # After session-3
        
        filtered_sessions = self.session_manager.get_sessions_by_date_range(start_date, end_date)
        
        # Should return session-2 and session-3
        self.assertEqual(len(filtered_sessions), 2)
        session_ids = [s.session_id for s in filtered_sessions]
        self.assertIn("session-2", session_ids)
        self.assertIn("session-3", session_ids)
        self.assertNotIn("session-1", session_ids)
        self.assertNotIn("session-4", session_ids)
    
    def test_get_sessions_by_hands_played(self):
        """Test filtering sessions by hands played."""
        # Create sessions with different hands played by adding actual hand records
        sessions_data = [
            ("session-1", 5),
            ("session-2", 15),
            ("session-3", 25),
            ("session-4", 35)
        ]
        
        for session_id, hands_played in sessions_data:
            metadata = SessionMetadata(session_id=session_id)
            stats = SessionStats(session_id=session_id)
            session = SessionData(session_id, metadata, self.test_rules, stats)
            
            # Add hand records to match the desired hands_played count
            for i in range(hands_played):
                player_cards = [Card(Suit.HEARTS, Rank.ACE), Card(Suit.SPADES, Rank.KING)]
                dealer_cards = [Card(Suit.DIAMONDS, Rank.QUEEN), Card(Suit.CLUBS, Rank.SEVEN)]
                result = GameResult(Outcome.WIN, 21, 17, 1.0)
                
                hand_record = HandRecord(
                    hand_number=i,
                    player_cards=player_cards,
                    dealer_cards=dealer_cards,
                    user_actions=[Action.STAND],
                    optimal_actions=[Action.STAND],
                    running_count=0,
                    true_count=0.0,
                    result=result
                )
                session.add_hand_record(hand_record)
            
            self.session_manager.save_session(session)
        
        # Test filtering with min hands only
        filtered_sessions = self.session_manager.get_sessions_by_hands_played(min_hands=20)
        self.assertEqual(len(filtered_sessions), 2)
        session_ids = [s.session_id for s in filtered_sessions]
        self.assertIn("session-3", session_ids)
        self.assertIn("session-4", session_ids)
        
        # Test filtering with min and max hands
        filtered_sessions = self.session_manager.get_sessions_by_hands_played(min_hands=10, max_hands=30)
        self.assertEqual(len(filtered_sessions), 2)
        session_ids = [s.session_id for s in filtered_sessions]
        self.assertIn("session-2", session_ids)
        self.assertIn("session-3", session_ids)
        
        # Test sorting (should be descending by hands played)
        self.assertEqual(filtered_sessions[0].session_id, "session-3")  # 25 hands
        self.assertEqual(filtered_sessions[1].session_id, "session-2")  # 15 hands
    
    def test_metadata_index_corruption_recovery(self):
        """Test recovery from metadata index corruption."""
        # Save a session normally
        self.session_manager.save_session(self.test_session)
        
        # Corrupt the metadata index file
        index_file = Path(self.temp_dir) / "sessions_index.json"
        with open(index_file, 'w') as f:
            f.write("invalid json content")
        
        # Create new session manager (should trigger rebuild)
        new_manager = SessionManager(self.temp_dir)
        
        # Should have recovered the session from the file
        self.assertEqual(len(new_manager.list_sessions()), 1)
        self.assertTrue(new_manager.session_exists("test-session-1"))
        
        # Should be able to load the session
        loaded_session = new_manager.load_session("test-session-1")
        self.assertEqual(loaded_session.session_id, "test-session-1")
    
    def test_session_file_permission_error(self):
        """Test handling of permission errors during file operations."""
        import os
        import stat
        
        # Save a session
        self.session_manager.save_session(self.test_session)
        session_file = Path(self.temp_dir) / "test-session-1.json"
        
        # Make file read-only (simulate permission error)
        try:
            os.chmod(session_file, stat.S_IRUSR)
            
            # Try to save again (should fail)
            with self.assertRaises(SessionManagerError):
                self.session_manager.save_session(self.test_session)
        finally:
            # Restore permissions for cleanup
            try:
                os.chmod(session_file, stat.S_IRUSR | stat.S_IWUSR)
            except:
                pass
    
    def test_empty_session_directory(self):
        """Test behavior with empty session directory."""
        # Create empty session manager
        empty_manager = SessionManager(self.temp_dir)
        
        # Should handle empty directory gracefully
        self.assertEqual(len(empty_manager.list_sessions()), 0)
        self.assertEqual(empty_manager.cleanup_orphaned_files(), 0)
        self.assertEqual(len(empty_manager.validate_all_sessions()), 0)
        
        storage_info = empty_manager.get_storage_info()
        self.assertEqual(storage_info["total_sessions"], 0)
        self.assertEqual(storage_info["total_size_bytes"], 0)
    
    def test_large_session_data_handling(self):
        """Test handling of sessions with large amounts of data."""
        # Create session with many hand records
        large_session = SessionData(
            session_id="large-session",
            metadata=SessionMetadata(session_id="large-session"),
            rules=self.test_rules,
            stats=SessionStats(session_id="large-session")
        )
        
        # Add many hand records
        for i in range(1000):
            player_cards = [Card(Suit.HEARTS, Rank.ACE), Card(Suit.SPADES, Rank.KING)]
            dealer_cards = [Card(Suit.DIAMONDS, Rank.QUEEN), Card(Suit.CLUBS, Rank.SEVEN)]
            result = GameResult(Outcome.WIN, 21, 17, 1.0)
            
            hand_record = HandRecord(
                hand_number=i,
                player_cards=player_cards,
                dealer_cards=dealer_cards,
                user_actions=[Action.STAND],
                optimal_actions=[Action.STAND],
                running_count=i % 10,
                true_count=float(i % 5),
                result=result
            )
            large_session.add_hand_record(hand_record)
        
        # Should be able to save and load large session
        session_id = self.session_manager.save_session(large_session)
        loaded_session = self.session_manager.load_session(session_id)
        
        self.assertEqual(len(loaded_session.hands_history), 1000)
        self.assertEqual(loaded_session.metadata.hands_played, 1000)
    
    def test_concurrent_session_operations(self):
        """Test handling of concurrent session operations."""
        import threading
        import time
        
        results = []
        errors = []
        
        def save_session_worker(session_id):
            try:
                metadata = SessionMetadata(session_id=session_id)
                stats = SessionStats(session_id=session_id)
                session = SessionData(session_id, metadata, self.test_rules, stats)
                result = self.session_manager.save_session(session)
                results.append(result)
            except Exception as e:
                errors.append(str(e))
        
        # Create multiple threads to save sessions concurrently
        threads = []
        for i in range(5):
            thread = threading.Thread(target=save_session_worker, args=(f"concurrent-session-{i}",))
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Should have saved all sessions successfully
        self.assertEqual(len(results), 5)
        self.assertEqual(len(errors), 0)
        
        # All sessions should exist
        for i in range(5):
            self.assertTrue(self.session_manager.session_exists(f"concurrent-session-{i}"))
    
    def test_invalid_session_id_characters(self):
        """Test handling of invalid characters in session IDs."""
        # Test with various invalid characters
        invalid_ids = [
            "session/with/slashes",
            "session\\with\\backslashes",
            "session:with:colons",
            "session*with*asterisks",
            "session?with?questions",
            "session<with>brackets"
        ]
        
        for invalid_id in invalid_ids:
            metadata = SessionMetadata(session_id=invalid_id)
            stats = SessionStats(session_id=invalid_id)
            session = SessionData(invalid_id, metadata, self.test_rules, stats)
            
            # Should be able to save (filesystem will handle invalid chars)
            try:
                saved_id = self.session_manager.save_session(session)
                self.assertEqual(saved_id, invalid_id)
                
                # Should be able to load back
                loaded_session = self.session_manager.load_session(invalid_id)
                self.assertEqual(loaded_session.session_id, invalid_id)
            except (SessionManagerError, OSError):
                # Some filesystems may reject certain characters
                pass
    
    def test_session_metadata_edge_cases(self):
        """Test edge cases in session metadata handling."""
        # Test with None values
        metadata = SessionMetadata(
            session_id="edge-case-session",
            name=None,
            created_time=None,
            last_modified=None,
            hands_played=0,
            duration_minutes=None,
            rules_summary=""
        )
        
        stats = SessionStats(session_id="edge-case-session")
        session = SessionData("edge-case-session", metadata, self.test_rules, stats)
        
        # Should handle None values gracefully
        session_id = self.session_manager.save_session(session)
        loaded_session = self.session_manager.load_session(session_id)
        
        self.assertEqual(loaded_session.metadata.name, None)
        self.assertIsNotNone(loaded_session.metadata.created_time)  # Should be set during save
        self.assertIsNotNone(loaded_session.metadata.last_modified)  # Should be set during save
    
    def test_recovery_with_index_save_failure(self):
        """Test recovery when metadata index save fails."""
        # Create a corrupted session
        corrupted_file = Path(self.temp_dir) / "corrupted-session.json"
        with open(corrupted_file, 'w') as f:
            f.write("invalid json")
        
        corrupted_metadata = SessionMetadata("corrupted-session")
        self.session_manager._metadata_index["corrupted-session"] = corrupted_metadata
        
        # Mock the _save_metadata_index to raise an exception
        original_save = self.session_manager._save_metadata_index
        def failing_save():
            raise OSError("Simulated save failure")
        
        self.session_manager._save_metadata_index = failing_save
        
        try:
            # Run recovery with removal
            recovery_actions = self.session_manager.recover_corrupted_sessions(remove_corrupted=True)
            
            # Should report both the session removal and index save failure
            self.assertIn("corrupted-session", recovery_actions)
            self.assertIn("metadata_index", recovery_actions)
            self.assertIn("Failed to save updated index", recovery_actions["metadata_index"])
        finally:
            # Restore original method
            self.session_manager._save_metadata_index = original_save


if __name__ == '__main__':
    unittest.main()