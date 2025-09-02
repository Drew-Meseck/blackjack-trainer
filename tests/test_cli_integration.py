"""Integration tests for CLI functionality."""

import unittest
from unittest.mock import patch, MagicMock
from io import StringIO
import sys

from src.cli import GameCLI
from src.models import GameRules, Action


class TestGameCLI(unittest.TestCase):
    """Test cases for GameCLI integration."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.rules = GameRules(num_decks=1, penetration=0.5)
        self.cli = GameCLI(self.rules)
    
    def test_cli_initialization(self):
        """Test CLI initializes correctly."""
        assert self.cli.rules == self.rules
        assert not self.cli.running
        assert self.cli.game is not None
        assert len(self.cli.commands) > 0
    
    def test_command_mapping(self):
        """Test that all expected commands are mapped."""
        expected_commands = [
            'h', 'hit', 's', 'stand', 'd', 'double',
            'p', 'split', 'r', 'surrender', 'n', 'new',
            'q', 'quit', 'help', '?'
        ]
        
        for cmd in expected_commands:
            assert cmd in self.cli.commands
    
    @patch('builtins.input')
    @patch('sys.stdout', new_callable=StringIO)
    def test_new_hand_command(self, mock_stdout, mock_input):
        """Test starting a new hand."""
        mock_input.side_effect = ['q']  # Quit after new hand
        
        self.cli._new_hand()
        
        # Verify game state
        assert self.cli.game.player_hand.card_count() == 2
        assert self.cli.game.dealer_hand.card_count() == 2
        
        # Check output contains expected elements
        output = mock_stdout.getvalue()
        assert "NEW HAND" in output
    
    @patch('builtins.input')
    @patch('sys.stdout', new_callable=StringIO)
    def test_hit_command(self, mock_stdout, mock_input):
        """Test hit command functionality."""
        # Start a new hand first
        self.cli._new_hand()
        initial_cards = self.cli.game.player_hand.card_count()
        
        # Execute hit if game allows it
        if not self.cli.game.is_game_over():
            self.cli._hit()
            
            # Verify card was added
            assert self.cli.game.player_hand.card_count() == initial_cards + 1
            
            # Check output
            output = mock_stdout.getvalue()
            assert "You drew:" in output
    
    @patch('builtins.input')
    @patch('sys.stdout', new_callable=StringIO)
    def test_stand_command(self, mock_stdout, mock_input):
        """Test stand command functionality."""
        # Start a new hand first
        self.cli._new_hand()
        
        # Execute stand if game allows it
        if not self.cli.game.is_game_over():
            self.cli._stand()
            
            # Verify game is over after standing
            assert self.cli.game.is_game_over()
            
            # Check output
            output = mock_stdout.getvalue()
            assert "You stand" in output
    
    @patch('builtins.input')
    @patch('sys.stdout', new_callable=StringIO)
    def test_double_command(self, mock_stdout, mock_input):
        """Test double command functionality."""
        # Start a new hand first
        self.cli._new_hand()
        
        # Execute double if game allows it
        if self.cli.game.can_double() and not self.cli.game.is_game_over():
            initial_cards = self.cli.game.player_hand.card_count()
            self.cli._double()
            
            # Verify exactly one card was added and game is over
            assert self.cli.game.player_hand.card_count() == initial_cards + 1
            assert self.cli.game.is_game_over()
            
            # Check output
            output = mock_stdout.getvalue()
            assert "You double down" in output
    
    @patch('builtins.input')
    @patch('sys.stdout', new_callable=StringIO)
    def test_surrender_command(self, mock_stdout, mock_input):
        """Test surrender command functionality."""
        # Use rules that allow surrender
        rules_with_surrender = GameRules(surrender_allowed=True)
        cli_with_surrender = GameCLI(rules_with_surrender)
        
        # Start a new hand
        cli_with_surrender._new_hand()
        
        # Execute surrender if game allows it
        if cli_with_surrender.game.can_surrender():
            cli_with_surrender._surrender()
            
            # Verify game is over
            assert cli_with_surrender.game.is_game_over()
            
            # Check output
            output = mock_stdout.getvalue()
            assert "You surrender" in output
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_help_command(self, mock_stdout):
        """Test help command displays correct information."""
        self.cli._help()
        
        output = mock_stdout.getvalue()
        assert "BLACKJACK COMMANDS" in output
        assert "hit" in output
        assert "stand" in output
        assert "double" in output
        assert "quit" in output
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_display_game_state(self, mock_stdout):
        """Test game state display."""
        # Start a new hand
        self.cli._new_hand()
        
        # Display game state
        self.cli._display_game_state()
        
        output = mock_stdout.getvalue()
        assert "CURRENT HAND" in output
        assert "Player:" in output
        assert "Dealer:" in output
        
        # Should show hidden dealer card if game not over
        if not self.cli.game.is_game_over():
            assert "[Hidden]" in output
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_show_available_actions(self, mock_stdout):
        """Test available actions display."""
        # Start a new hand
        self.cli._new_hand()
        
        # Show available actions if game not over
        if not self.cli.game.is_game_over():
            self.cli._show_available_actions()
            
            output = mock_stdout.getvalue()
            assert "Available actions:" in output
            
            # Check that basic actions are shown
            available_actions = self.cli.game.get_available_actions()
            if Action.HIT in available_actions:
                assert "hit" in output.lower()
            if Action.STAND in available_actions:
                assert "stand" in output.lower()
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_display_final_result(self, mock_stdout):
        """Test final result display."""
        # Start and complete a hand
        self.cli._new_hand()
        
        # Force game to end if not already over
        if not self.cli.game.is_game_over():
            self.cli._stand()
        
        # Display final result
        self.cli._display_final_result()
        
        output = mock_stdout.getvalue()
        assert "HAND RESULT" in output
        assert "Player:" in output
        assert "Dealer:" in output
        assert "Result:" in output
    
    @patch('builtins.input')
    @patch('sys.stdout', new_callable=StringIO)
    def test_invalid_command_handling(self, mock_stdout, mock_input):
        """Test handling of invalid commands."""
        # Start a new hand
        self.cli._new_hand()
        
        # Simulate invalid command during game loop
        mock_input.side_effect = ['invalid_command', 'q']
        
        # Run one iteration of game loop
        if not self.cli.game.is_game_over():
            self.cli._game_loop()
        
        output = mock_stdout.getvalue()
        # Should handle invalid command gracefully
        assert "Unknown command" in output or "Invalid command" in output
    
    def test_quit_command(self):
        """Test quit command functionality."""
        self.cli.running = True
        self.cli._quit()
        
        assert not self.cli.running
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_welcome_message(self, mock_stdout):
        """Test welcome message displays game rules."""
        self.cli._print_welcome()
        
        output = mock_stdout.getvalue()
        assert "WELCOME TO BLACKJACK SIMULATOR" in output
        assert "Game Rules:" in output
        assert f"{self.rules.num_decks} deck" in output
        assert "Type 'help'" in output
    
    @patch('builtins.input')
    @patch('sys.stdout', new_callable=StringIO)
    def test_complete_game_flow(self, mock_stdout, mock_input):
        """Test a complete game flow from start to finish."""
        # Simulate a complete game: new hand -> stand -> new hand -> quit
        mock_input.side_effect = ['s', 'n', 'q']
        
        # Start CLI but don't run full loop (to avoid infinite loop in test)
        self.cli.running = True
        self.cli._new_hand()
        
        # Simulate game actions
        if not self.cli.game.is_game_over():
            self.cli._stand()
        
        # Verify game completed
        assert self.cli.game.is_game_over()
        
        # Start new hand
        self.cli._new_hand()
        assert self.cli.game.player_hand.card_count() == 2
        
        # Quit
        self.cli._quit()
        assert not self.cli.running


class TestCLIErrorHandling(unittest.TestCase):
    """Test error handling in CLI."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.cli = GameCLI()
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_hit_when_game_over(self, mock_stdout):
        """Test hit command when game is over."""
        # Start and finish a hand
        self.cli._new_hand()
        if not self.cli.game.is_game_over():
            self.cli._stand()
        
        # Try to hit when game is over
        self.cli._hit()
        
        output = mock_stdout.getvalue()
        assert "Cannot hit" in output
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_double_when_not_allowed(self, mock_stdout):
        """Test double command when not allowed."""
        # Start a hand and hit to make doubling invalid
        self.cli._new_hand()
        if not self.cli.game.is_game_over():
            self.cli._hit()  # Now can't double
            
            # Try to double
            self.cli._double()
            
            output = mock_stdout.getvalue()
            assert "Cannot double" in output
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_surrender_when_not_allowed(self, mock_stdout):
        """Test surrender command when not allowed."""
        # Use rules without surrender
        rules_no_surrender = GameRules(surrender_allowed=False)
        cli_no_surrender = GameCLI(rules_no_surrender)
        
        # Start a hand
        cli_no_surrender._new_hand()
        
        # Try to surrender
        cli_no_surrender._surrender()
        
        output = mock_stdout.getvalue()
        assert "Cannot surrender" in output


if __name__ == "__main__":
    unittest.main()