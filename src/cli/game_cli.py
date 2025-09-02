"""Command-line interface for blackjack game interaction."""

import sys
from datetime import datetime
from typing import Optional, Dict, Callable
from src.game import BlackjackGame
from src.models import GameRules, Action, Outcome
from src.session import SessionManager, SessionData, SessionMetadata, HandRecord
from src.analytics import SessionStats
from src.utils.exceptions import (
    BlackjackSimulatorError, 
    InvalidInputError, 
    InvalidGameStateError,
    SessionNotFoundError
)
from src.utils.validation import validate_choice_input, validate_yes_no_input
from src.utils.error_recovery import handle_user_input_error, ErrorRecoveryContext


class GameCLI:
    """Command-line interface for interactive blackjack gameplay."""
    
    def __init__(self, rules: Optional[GameRules] = None):
        """Initialize the CLI with game rules.
        
        Args:
            rules: Game rules configuration. Uses defaults if None.
        """
        self.rules = rules or GameRules()
        self.game = BlackjackGame(self.rules)
        self.running = False
        
        # Session management
        self.session_manager = SessionManager()
        self.current_session: Optional[SessionData] = None
        self.hand_number = 0
        
        # Command mapping
        self.commands: Dict[str, Callable] = {
            'h': self._hit,
            'hit': self._hit,
            's': self._stand,
            'stand': self._stand,
            'd': self._double,
            'double': self._double,
            'p': self._split,
            'split': self._split,
            'r': self._surrender,
            'surrender': self._surrender,
            'n': self._new_hand,
            'new': self._new_hand,
            'q': self._quit,
            'quit': self._quit,
            'help': self._help,
            '?': self._help
        }
    
    def start(self) -> None:
        """Start the interactive CLI session with automatic session creation."""
        self.running = True
        
        with ErrorRecoveryContext("starting CLI session", reraise=False) as ctx:
            self._create_session()
            self._print_welcome()
            self._new_hand()
        
        if ctx.error:
            print(ctx.get_user_message())
            return
        
        while self.running:
            try:
                self._game_loop()
            except KeyboardInterrupt:
                print("\n\nSaving session...")
                self._auto_save_session()
                print("Goodbye!")
                break
            except BlackjackSimulatorError as e:
                print(handle_user_input_error(e, "Type 'help' for available commands."))
            except Exception as e:
                print(f"❌ Unexpected error: {e}")
                print("Type 'help' for available commands.")
    
    def _game_loop(self) -> None:
        """Main game interaction loop."""
        if not self.game.is_game_over():
            self._display_game_state()
            self._show_available_actions()
            
            command = input("\nEnter command: ").strip().lower()
            
            if command in self.commands:
                self.commands[command]()
            else:
                print(f"Unknown command: {command}")
                print("Type 'help' for available commands.")
        else:
            self._display_final_result()
            print("\nType 'n' for new hand or 'q' to quit.")
            
            command = input("Enter command: ").strip().lower()
            if command in ['n', 'new']:
                self._new_hand()
            elif command in ['q', 'quit']:
                self._quit()
            else:
                print("Invalid command. Type 'n' for new hand or 'q' to quit.")
    
    def _hit(self) -> None:
        """Execute hit action."""
        with ErrorRecoveryContext("hitting", reraise=False) as ctx:
            card = self.game.player_hit()
            print(f"\nYou drew: {card}")
            
            if self.game.is_game_over():
                print("Hand complete!")
        
        if ctx.error:
            print(f"❌ Cannot hit: {ctx.error}")
    
    def _stand(self) -> None:
        """Execute stand action."""
        with ErrorRecoveryContext("standing", reraise=False) as ctx:
            self.game.player_stand()
            print("\nYou stand. Dealer plays...")
        
        if ctx.error:
            print(f"❌ Cannot stand: {ctx.error}")
    
    def _double(self) -> None:
        """Execute double down action."""
        with ErrorRecoveryContext("doubling down", reraise=False) as ctx:
            card = self.game.player_double()
            print(f"\nYou double down and draw: {card}")
            print("Hand complete!")
        
        if ctx.error:
            print(f"❌ Cannot double: {ctx.error}")
    
    def _split(self) -> None:
        """Execute split action (placeholder - not fully implemented in base game)."""
        print("❌ Split functionality not yet implemented in this version.")
    
    def _surrender(self) -> None:
        """Execute surrender action."""
        with ErrorRecoveryContext("surrendering", reraise=False) as ctx:
            self.game.player_surrender()
            print("\nYou surrender.")
        
        if ctx.error:
            print(f"❌ Cannot surrender: {ctx.error}")
    
    def _new_hand(self) -> None:
        """Start a new hand."""
        try:
            self.game.reset()
            self.game.deal_initial_cards()
            print("\n" + "="*50)
            print("NEW HAND")
            print("="*50)
            
            # Check for immediate blackjacks
            if self.game.is_game_over():
                print("Immediate result!")
        except RuntimeError as e:
            print(f"Cannot start new hand: {e}")
    
    def _quit(self) -> None:
        """Quit the game and save the session."""
        # Record the current hand if it's completed
        if self.game.is_game_over():
            self._record_hand()
        
        self._auto_save_session()
        self.running = False
        print("Session saved. Thanks for playing!")
    
    def _help(self) -> None:
        """Display help information."""
        print("\n" + "="*40)
        print("BLACKJACK COMMANDS")
        print("="*40)
        print("Game Actions:")
        print("  h, hit      - Take another card")
        print("  s, stand    - Keep current hand")
        print("  d, double   - Double bet and take one card")
        print("  p, split    - Split pair (if available)")
        print("  r, surrender - Surrender hand (if available)")
        print("\nGame Control:")
        print("  n, new      - Start new hand")
        print("  q, quit     - Exit game")
        print("  help, ?     - Show this help")
        print("="*40)
    
    def _display_game_state(self) -> None:
        """Display current game state."""
        print("\n" + "-"*40)
        print("CURRENT HAND")
        print("-"*40)
        
        # Show player hand
        print(f"Player: {self.game.player_hand}")
        
        # Show dealer hand (hide hole card if game not over)
        if self.game.is_game_over():
            print(f"Dealer: {self.game.dealer_hand}")
        else:
            if self.game.dealer_hand.card_count() >= 1:
                first_card = self.game.dealer_hand.cards[0]
                print(f"Dealer: {first_card} [Hidden]")
        
        print("-"*40)
    
    def _show_available_actions(self) -> None:
        """Display available actions for the player."""
        actions = self.game.get_available_actions()
        
        if not actions:
            return
        
        print("\nAvailable actions:")
        action_descriptions = {
            Action.HIT: "h/hit - Take another card",
            Action.STAND: "s/stand - Keep current hand", 
            Action.DOUBLE: "d/double - Double bet and take one card",
            Action.SPLIT: "p/split - Split your pair",
            Action.SURRENDER: "r/surrender - Surrender (lose half bet)"
        }
        
        for action in actions:
            if action in action_descriptions:
                print(f"  {action_descriptions[action]}")
    
    def _display_final_result(self) -> None:
        """Display the final result of the hand."""
        print("\n" + "="*50)
        print("HAND RESULT")
        print("="*50)
        
        # Show both hands
        print(f"Player: {self.game.player_hand}")
        print(f"Dealer: {self.game.dealer_hand}")
        
        result = self.game.get_result()
        if result:
            print(f"\nResult: {result}")
            
            # Add descriptive outcome
            outcome_messages = {
                Outcome.WIN: "🎉 You win!",
                Outcome.LOSS: "😞 You lose.",
                Outcome.PUSH: "🤝 Push (tie).",
                Outcome.BLACKJACK: "🃏 Blackjack! You win!",
                Outcome.SURRENDER: "🏳️ You surrendered."
            }
            
            if result.outcome in outcome_messages:
                print(outcome_messages[result.outcome])
        
        print("="*50)
    
    def _print_welcome(self) -> None:
        """Print welcome message and game rules."""
        print("="*60)
        print("🃏 WELCOME TO BLACKJACK SIMULATOR 🃏")
        print("="*60)
        print("\nGame Rules:")
        print(f"  • {self.rules.num_decks} deck(s)")
        print(f"  • Dealer {'hits' if self.rules.dealer_hits_soft_17 else 'stands on'} soft 17")
        print(f"  • Blackjack pays {self.rules.blackjack_payout}:1")
        print(f"  • Double after split: {'Yes' if self.rules.double_after_split else 'No'}")
        print(f"  • Surrender allowed: {'Yes' if self.rules.surrender_allowed else 'No'}")
        print("\nType 'help' or '?' for commands.")
        print("="*60)
    
    def _create_session(self) -> None:
        """Create a new session for tracking gameplay."""
        session_id = self.session_manager.generate_session_id()
        metadata = SessionMetadata(
            session_id=session_id,
            name=f"Blackjack Session {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )
        
        stats = SessionStats(session_id=session_id)
        
        self.current_session = SessionData(
            session_id=session_id,
            metadata=metadata,
            rules=self.rules,
            stats=stats,
            counting_system="None"  # Basic game doesn't use counting
        )
        
        print(f"📊 Session created: {metadata.name}")
    
    def _record_hand(self) -> None:
        """Record the current hand to the session."""
        if not self.current_session:
            return
        
        # Get the game result
        result = self.game.get_result()
        if not result:
            return
        
        self.hand_number += 1
        
        # Create hand record
        hand_record = HandRecord(
            hand_number=self.hand_number,
            player_cards=list(self.game.player_hand.cards),
            dealer_cards=list(self.game.dealer_hand.cards),
            user_actions=[],  # We'll track this in enhanced versions
            optimal_actions=[],  # We'll track this in enhanced versions
            running_count=0,  # No counting in basic game
            true_count=0.0,   # No counting in basic game
            result=result,
            bet_amount=1.0  # Default bet amount
        )
        
        # Add to session
        self.current_session.add_hand_record(hand_record)
        
        # Update session stats
        self.current_session.stats.update_hand_result(result, 1.0)
    
    def _new_hand(self) -> None:
        """Start a new hand and record the previous one if completed."""
        # Record the previous hand if it was completed
        if self.game.is_game_over():
            with ErrorRecoveryContext("recording hand", reraise=False) as ctx:
                self._record_hand()
            
            if ctx.error:
                print(f"⚠️ Warning: Failed to record hand: {ctx.error}")
        
        with ErrorRecoveryContext("starting new hand", reraise=False) as ctx:
            self.game.reset()
            self.game.deal_initial_cards()
            print("\n" + "="*50)
            print("NEW HAND")
            print("="*50)
            
            # Check for immediate blackjacks
            if self.game.is_game_over():
                print("Immediate result!")
        
        if ctx.error:
            print(f"❌ Cannot start new hand: {ctx.error}")
    
    def _auto_save_session(self) -> None:
        """Automatically save the current session."""
        if self.current_session and self.current_session.hands_history:
            try:
                session_id = self.session_manager.save_session(self.current_session)
                print(f"💾 Session saved: {session_id[:8]}... ({len(self.current_session.hands_history)} hands)")
            except Exception as e:
                print(f"⚠️ Failed to save session: {e}")
        elif self.current_session:
            print("📝 No hands played - session not saved")


def main():
    """Main entry point for the CLI."""
    # Create default rules
    rules = GameRules()
    
    # Create and start CLI
    cli = GameCLI(rules)
    cli.start()


if __name__ == "__main__":
    main()