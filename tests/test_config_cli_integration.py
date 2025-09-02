"""Integration tests for configuration and session management CLI."""

import unittest
import tempfile
import shutil
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from io import StringIO
import sys

from src.cli.full_cli import ConfigurationCLI
from src.models import GameRules
from src.session import SessionData, SessionMetadata
from src.analytics import SessionStats


class TestConfigurationCLI(unittest.TestCase):
    """Test configuration CLI functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.cli = ConfigurationCLI()
        # Use temporary directory for session storage
        self.cli.session_manager.sessions_dir = Path(self.temp_dir)
        self.cli.session_manager.metadata_file = Path(self.temp_dir) / "sessions_index.json"
        self.cli.session_manager._metadata_index = {}
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_show_current_rules(self):
        """Test displaying current game rules."""
        # Capture stdout
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()
        
        self.cli._show_current_rules()
        
        sys.stdout = old_stdout
        output = captured_output.getvalue()
        
        self.assertIn("Current Game Rules", output)
        self.assertIn("Dealer hits soft 17", output)
        self.assertIn("Number of decks", output)
        self.assertIn("Penetration", output)
    
    @patch('builtins.input', side_effect=['y'])
    def test_configure_dealer_rules_hit_soft_17(self, mock_input):
        """Test configuring dealer to hit soft 17."""
        self.cli.current_rules.dealer_hits_soft_17 = False
        
        # Capture stdout
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()
        
        self.cli._configure_dealer_rules()
        
        sys.stdout = old_stdout
        output = captured_output.getvalue()
        
        self.assertTrue(self.cli.current_rules.dealer_hits_soft_17)
        self.assertIn("Dealer rules updated!", output)
    
    @patch('builtins.input', side_effect=['n'])
    def test_configure_dealer_rules_stand_soft_17(self, mock_input):
        """Test configuring dealer to stand on soft 17."""
        self.cli.current_rules.dealer_hits_soft_17 = True
        self.cli._configure_dealer_rules()
        
        self.assertFalse(self.cli.current_rules.dealer_hits_soft_17)
    
    @patch('builtins.input', side_effect=['y', 'n'])
    def test_configure_player_options(self, mock_input):
        """Test configuring player options."""
        self.cli.current_rules.double_after_split = False
        self.cli.current_rules.surrender_allowed = True
        
        # Capture stdout
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()
        
        self.cli._configure_player_options()
        
        sys.stdout = old_stdout
        output = captured_output.getvalue()
        
        self.assertTrue(self.cli.current_rules.double_after_split)
        self.assertFalse(self.cli.current_rules.surrender_allowed)
        self.assertIn("Player options updated!", output)
    
    @patch('builtins.input', side_effect=['8', '65'])
    def test_configure_deck_settings(self, mock_input):
        """Test configuring deck settings."""
        # Capture stdout
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()
        
        self.cli._configure_deck_settings()
        
        sys.stdout = old_stdout
        output = captured_output.getvalue()
        
        self.assertEqual(self.cli.current_rules.num_decks, 8)
        self.assertEqual(self.cli.current_rules.penetration, 0.65)
        self.assertIn("Deck settings updated!", output)
    
    @patch('builtins.input', side_effect=['9', '4', '50'])  # Invalid deck, valid deck, valid penetration
    def test_configure_deck_settings_invalid_input(self, mock_input):
        """Test deck configuration with invalid input."""
        self.cli._configure_deck_settings()
        
        self.assertEqual(self.cli.current_rules.num_decks, 4)
        self.assertEqual(self.cli.current_rules.penetration, 0.5)
    
    @patch('builtins.input', side_effect=['1'])
    def test_configure_counting_system(self, mock_input):
        """Test configuring counting system."""
        # Mock available systems
        self.cli.counting_manager.list_systems = MagicMock(return_value=['Hi-Lo', 'KO', 'Hi-Opt I'])
        
        # Capture stdout
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()
        
        self.cli._configure_counting_system()
        
        sys.stdout = old_stdout
        output = captured_output.getvalue()
        
        self.assertIn("Available counting systems", output)
        self.assertIn("Hi-Lo", output)
        self.assertIn("Selected counting system: Hi-Lo", output)
    
    @patch('builtins.input', side_effect=['y'])
    def test_reset_rules(self, mock_input):
        """Test resetting rules to defaults."""
        # Modify current rules
        self.cli.current_rules.num_decks = 8
        self.cli.current_rules.penetration = 0.5
        
        # Capture stdout
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()
        
        self.cli._reset_rules()
        
        sys.stdout = old_stdout
        output = captured_output.getvalue()
        
        # Should be back to defaults
        self.assertEqual(self.cli.current_rules.num_decks, 6)  # Default
        self.assertEqual(self.cli.current_rules.penetration, 0.75)  # Default
        self.assertIn("Rules reset to defaults!", output)
    
    @patch('builtins.input', side_effect=['n'])
    def test_reset_rules_cancelled(self, mock_input):
        """Test cancelling rule reset."""
        original_decks = self.cli.current_rules.num_decks
        
        # Capture stdout
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()
        
        self.cli._reset_rules()
        
        sys.stdout = old_stdout
        output = captured_output.getvalue()
        
        self.assertEqual(self.cli.current_rules.num_decks, original_decks)
        self.assertIn("Reset cancelled.", output)


class TestSessionManagement(unittest.TestCase):
    """Test session management functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.cli = ConfigurationCLI()
        self.cli.session_manager.sessions_dir = Path(self.temp_dir)
        self.cli.session_manager.metadata_file = Path(self.temp_dir) / "sessions_index.json"
        self.cli.session_manager._metadata_index = {}
        
        # Create test session data
        metadata = SessionMetadata(session_id="test-session-123")
        self.test_session = SessionData(
            session_id="test-session-123",
            metadata=metadata,
            rules=GameRules(num_decks=6, penetration=0.75),
            stats=SessionStats(session_id="test-session-123")
        )
        self.test_session.stats.hands_played = 100
        self.test_session.stats.hands_won = 45
        self.test_session.stats.hands_lost = 50
        self.test_session.stats.hands_pushed = 5
        # Set counting accuracy through the CountingAccuracy object
        self.test_session.stats.counting_accuracy.total_estimates = 100
        self.test_session.stats.counting_accuracy.correct_estimates = 85
        # Set strategy accuracy through the StrategyAccuracy object  
        self.test_session.stats.strategy_accuracy.total_decisions = 100
        self.test_session.stats.strategy_accuracy.correct_decisions = 92
        
        # Add dummy hand records to match the stats
        from src.session import HandRecord
        from src.models import Card, Suit, Rank, Action, GameResult, Outcome
        
        for i in range(100):
            dummy_hand = HandRecord(
                hand_number=i + 1,
                player_cards=[Card(Suit.HEARTS, Rank.TEN), Card(Suit.SPADES, Rank.NINE)],
                dealer_cards=[Card(Suit.DIAMONDS, Rank.KING), Card(Suit.CLUBS, Rank.SEVEN)],
                user_actions=[Action.STAND],
                optimal_actions=[Action.STAND],
                running_count=0,
                true_count=0.0,
                result=GameResult(Outcome.WIN, 19, 17, 1.0),
                bet_amount=1.0
            )
            self.test_session.hands_history.append(dummy_hand)
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_list_sessions_empty(self):
        """Test listing sessions when none exist."""
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()
        
        self.cli._list_sessions()
        
        sys.stdout = old_stdout
        output = captured_output.getvalue()
        
        self.assertIn("No sessions found.", output)
    
    def test_list_sessions_with_data(self):
        """Test listing sessions with existing data."""
        # Save a test session
        session_id = self.cli.session_manager.save_session(self.test_session, "Test Session")
        
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()
        
        self.cli._list_sessions()
        
        sys.stdout = old_stdout
        output = captured_output.getvalue()
        
        self.assertIn("Available Sessions", output)
        self.assertIn("Test Session", output)
        self.assertIn("100", output)  # hands played
    
    @patch('builtins.input', side_effect=['1'])
    def test_load_session(self, mock_input):
        """Test loading a session."""
        # Save a test session first
        session_id = self.cli.session_manager.save_session(self.test_session, "Test Session")
        
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()
        
        self.cli._load_session()
        
        sys.stdout = old_stdout
        output = captured_output.getvalue()
        
        self.assertIsNotNone(self.cli.current_session)
        self.assertEqual(self.cli.current_session.session_id, session_id)
        self.assertIn("Loaded session: Test Session", output)
        self.assertIn("Game rules updated from session.", output)
    
    def test_load_session_no_sessions(self):
        """Test loading session when none exist."""
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()
        
        self.cli._load_session()
        
        sys.stdout = old_stdout
        output = captured_output.getvalue()
        
        self.assertIn("No sessions available to load.", output)
    
    @patch('builtins.input', side_effect=['Test Save Session'])
    def test_save_session(self, mock_input):
        """Test saving current session."""
        self.cli.current_session = self.test_session
        
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()
        
        self.cli._save_session()
        
        sys.stdout = old_stdout
        output = captured_output.getvalue()
        
        self.assertIn("Session saved with ID:", output)
    
    def test_save_session_no_active(self):
        """Test saving when no active session."""
        self.cli.current_session = None
        
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()
        
        self.cli._save_session()
        
        sys.stdout = old_stdout
        output = captured_output.getvalue()
        
        self.assertIn("No active session to save.", output)


if __name__ == "__main__":
    unittest.main()