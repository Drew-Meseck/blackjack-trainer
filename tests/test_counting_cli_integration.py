"""Integration tests for counting CLI functionality."""

import unittest
from unittest.mock import patch, MagicMock
from io import StringIO
import sys

from src.cli import CountingCLI
from src.models import GameRules
from src.counting import CountingSystemManager


class TestCountingCLI(unittest.TestCase):
    """Test cases for CountingCLI integration."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.rules = GameRules(num_decks=1, penetration=0.5)
        self.cli = CountingCLI(self.rules)
    
    def test_counting_cli_initialization(self):
        """Test counting CLI initializes correctly."""
        assert self.cli.rules == self.rules
        assert not self.cli.running
        assert self.cli.game is not None
        assert self.cli.counting_system is not None
        assert not self.cli.counting_practice_mode
        # CountingCLI should have more commands than basic GameCLI
        from src.cli import GameCLI
        basic_cli = GameCLI()
        assert len(self.cli.commands) > len(basic_cli.commands)
    
    def test_counting_command_mapping(self):
        """Test that counting-specific commands are mapped."""
        counting_commands = [
            'c', 'count', 'e', 'estimate', 'practice',
            'system', 'systems', 'accuracy'
        ]
        
        for cmd in counting_commands:
            assert cmd in self.cli.commands
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_show_count_command(self, mock_stdout):
        """Test show count command."""
        # Start a new hand to have some cards dealt
        self.cli._new_hand()
        
        # Show count
        self.cli._show_count()
        
        output = mock_stdout.getvalue()
        assert "COUNT INFORMATION" in output
        assert "Running Count:" in output
        assert "True Count:" in output
        assert "Cards Seen:" in output
    
    @patch('builtins.input')
    @patch('sys.stdout', new_callable=StringIO)
    def test_estimate_count_command(self, mock_stdout, mock_input):
        """Test count estimation functionality."""
        # Start a new hand
        self.cli._new_hand()
        
        # Mock user input for count estimation
        mock_input.side_effect = ['0', '0.0']  # Estimate RC=0, TC=0.0
        
        # Execute estimate command
        self.cli._estimate_count()
        
        output = mock_stdout.getvalue()
        assert "COUNT FEEDBACK" in output
        assert "Your Running Count:" in output
        assert "Actual Running Count:" in output
        
        # Check that estimate was recorded
        assert len(self.cli.count_estimates) == 1
    
    @patch('builtins.input')
    @patch('sys.stdout', new_callable=StringIO)
    def test_estimate_count_no_cards(self, mock_stdout, mock_input):
        """Test count estimation when no cards dealt."""
        # Try to estimate without dealing cards
        self.cli._estimate_count()
        
        output = mock_stdout.getvalue()
        assert "No cards have been dealt yet" in output
    
    @patch('builtins.input')
    @patch('sys.stdout', new_callable=StringIO)
    def test_estimate_count_invalid_input(self, mock_stdout, mock_input):
        """Test count estimation with invalid input."""
        # Start a new hand
        self.cli._new_hand()
        
        # Mock invalid input
        mock_input.side_effect = ['invalid', '0.0']
        
        # Execute estimate command
        self.cli._estimate_count()
        
        output = mock_stdout.getvalue()
        assert "Please enter valid numbers" in output
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_toggle_practice_mode(self, mock_stdout):
        """Test toggling practice mode."""
        # Initially disabled
        assert not self.cli.counting_practice_mode
        
        # Enable practice mode
        self.cli._toggle_practice_mode()
        assert self.cli.counting_practice_mode
        
        output = mock_stdout.getvalue()
        assert "Practice Mode ENABLED" in output
        
        # Disable practice mode
        mock_stdout.truncate(0)
        mock_stdout.seek(0)
        self.cli._toggle_practice_mode()
        assert not self.cli.counting_practice_mode
        
        output = mock_stdout.getvalue()
        assert "Practice Mode DISABLED" in output
    
    @patch('builtins.input')
    @patch('sys.stdout', new_callable=StringIO)
    def test_change_counting_system(self, mock_stdout, mock_input):
        """Test changing counting system."""
        # Mock user selecting first system
        mock_input.side_effect = ['1']
        
        original_system = self.cli.counting_system.name()
        
        # Execute system change
        self.cli._change_counting_system()
        
        output = mock_stdout.getvalue()
        assert "Available counting systems:" in output
        
        # System might have changed or stayed the same depending on available systems
        # Just verify the command executed without error
    
    @patch('builtins.input')
    @patch('sys.stdout', new_callable=StringIO)
    def test_change_counting_system_cancel(self, mock_stdout, mock_input):
        """Test cancelling counting system change."""
        # Mock user pressing Enter to cancel
        mock_input.side_effect = ['']
        
        original_system = self.cli.counting_system.name()
        
        # Execute system change
        self.cli._change_counting_system()
        
        # System should remain unchanged
        assert self.cli.counting_system.name() == original_system
    
    @patch('builtins.input')
    @patch('sys.stdout', new_callable=StringIO)
    def test_change_counting_system_invalid(self, mock_stdout, mock_input):
        """Test invalid counting system selection."""
        # Mock user entering invalid choice
        mock_input.side_effect = ['999']
        
        # Execute system change
        self.cli._change_counting_system()
        
        output = mock_stdout.getvalue()
        assert "Invalid choice" in output
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_list_counting_systems(self, mock_stdout):
        """Test listing available counting systems."""
        self.cli._list_counting_systems()
        
        output = mock_stdout.getvalue()
        assert "AVAILABLE COUNTING SYSTEMS" in output
        assert "Card values:" in output
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_show_accuracy_stats_no_data(self, mock_stdout):
        """Test accuracy stats with no estimates."""
        self.cli._show_accuracy_stats()
        
        output = mock_stdout.getvalue()
        assert "No count estimates recorded yet" in output
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_show_accuracy_stats_with_data(self, mock_stdout):
        """Test accuracy stats with estimate data."""
        # Add some mock estimate data
        self.cli.count_estimates = [
            {'rc_correct': True, 'tc_correct': True},
            {'rc_correct': False, 'tc_correct': True},
            {'rc_correct': True, 'tc_correct': False}
        ]
        
        self.cli._show_accuracy_stats()
        
        output = mock_stdout.getvalue()
        assert "COUNTING ACCURACY STATISTICS" in output
        assert "Total Estimates: 3" in output
        assert "Running Count Accuracy:" in output
        assert "True Count Accuracy:" in output
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_help_command_extended(self, mock_stdout):
        """Test help command shows counting commands."""
        self.cli._help()
        
        output = mock_stdout.getvalue()
        assert "COUNTING SIMULATOR COMMANDS" in output
        assert "Counting Commands:" in output
        assert "count" in output
        assert "estimate" in output
        assert "practice" in output
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_display_game_state_with_count(self, mock_stdout):
        """Test game state display includes count information."""
        # Start a new hand
        self.cli._new_hand()
        
        # Display game state (not in practice mode)
        self.cli._display_game_state()
        
        output = mock_stdout.getvalue()
        assert "CURRENT HAND" in output
        
        # Should show count if cards have been dealt
        if self.cli.game.get_cards_seen() > 0:
            assert "Count: RC=" in output
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_display_game_state_practice_mode(self, mock_stdout):
        """Test game state display in practice mode."""
        # Enable practice mode
        self.cli.counting_practice_mode = True
        
        # Start a new hand
        self.cli._new_hand()
        
        # Display game state
        self.cli._display_game_state()
        
        output = mock_stdout.getvalue()
        
        # Should show practice mode indicator if cards dealt
        if self.cli.game.get_cards_seen() > 0:
            assert "Practice Mode: Count hidden" in output
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_welcome_message_counting(self, mock_stdout):
        """Test welcome message includes counting information."""
        self.cli._print_welcome()
        
        output = mock_stdout.getvalue()
        assert "COUNTING SIMULATOR" in output
        assert "Counting System:" in output
        assert "Counting Features:" in output
        assert "Real-time count tracking" in output
    
    @patch('builtins.input')
    @patch('sys.stdout', new_callable=StringIO)
    def test_complete_counting_workflow(self, mock_stdout, mock_input):
        """Test a complete counting practice workflow."""
        # Simulate: new hand -> show count -> estimate -> toggle practice -> new hand
        mock_input.side_effect = ['0', '0.0']  # For count estimation
        
        # Start new hand
        self.cli._new_hand()
        
        # Show count
        self.cli._show_count()
        
        # Estimate count
        self.cli._estimate_count()
        
        # Toggle practice mode
        self.cli._toggle_practice_mode()
        
        # Show accuracy
        self.cli._show_accuracy_stats()
        
        output = mock_stdout.getvalue()
        
        # Verify all operations completed
        assert "NEW HAND" in output
        assert "COUNT INFORMATION" in output
        assert "COUNT FEEDBACK" in output
        assert "Practice Mode ENABLED" in output
        assert "COUNTING ACCURACY STATISTICS" in output


class TestCountingCLIErrorHandling(unittest.TestCase):
    """Test error handling in counting CLI."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.cli = CountingCLI()
    
    @patch('builtins.input')
    @patch('sys.stdout', new_callable=StringIO)
    def test_estimate_count_keyboard_interrupt(self, mock_stdout, mock_input):
        """Test count estimation with keyboard interrupt."""
        # Start a new hand
        self.cli._new_hand()
        
        # Mock keyboard interrupt
        mock_input.side_effect = KeyboardInterrupt()
        
        # Execute estimate command
        self.cli._estimate_count()
        
        output = mock_stdout.getvalue()
        assert "Count estimation cancelled" in output
    
    @patch('builtins.input')
    @patch('sys.stdout', new_callable=StringIO)
    def test_change_system_keyboard_interrupt(self, mock_stdout, mock_input):
        """Test system change with keyboard interrupt."""
        # Mock keyboard interrupt
        mock_input.side_effect = KeyboardInterrupt()
        
        # Execute system change
        self.cli._change_counting_system()
        
        output = mock_stdout.getvalue()
        assert "System change cancelled" in output
    
    @patch('builtins.input')
    @patch('sys.stdout', new_callable=StringIO)
    def test_change_system_value_error(self, mock_stdout, mock_input):
        """Test system change with invalid number."""
        # Mock invalid input
        mock_input.side_effect = ['not_a_number']
        
        # Execute system change
        self.cli._change_counting_system()
        
        output = mock_stdout.getvalue()
        assert "Please enter a valid number" in output


if __name__ == "__main__":
    unittest.main()