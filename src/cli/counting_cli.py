"""Command-line interface for counting practice."""

import sys
from datetime import datetime
from typing import Optional, Dict, Callable, List
from src.game import CountingBlackjackGame
from src.models import GameRules, Action, Outcome, Card
from src.counting import CountingSystemManager, CountingSystem
from src.session import SessionManager, SessionData, SessionMetadata, HandRecord
from src.analytics import SessionStats
from src.utils.exceptions import InvalidInputError, BlackjackSimulatorError
from src.utils.validation import validate_count_estimate, validate_integer_input
from src.utils.error_recovery import handle_user_input_error, ErrorRecoveryContext
from .game_cli import GameCLI


class CountingCLI(GameCLI):
    """Extended CLI with counting practice functionality."""
    
    def __init__(self, rules: Optional[GameRules] = None, counting_system: Optional[CountingSystem] = None):
        """Initialize the counting CLI.
        
        Args:
            rules: Game rules configuration. Uses defaults if None.
            counting_system: Counting system to use. Uses Hi-Lo if None.
        """
        self.rules = rules or GameRules()
        
        # Set up counting system
        self.system_manager = CountingSystemManager()
        if counting_system is None:
            counting_system = self.system_manager.get_default_system()
        
        self.counting_system = counting_system
        self.game = CountingBlackjackGame(self.rules, counting_system)
        self.running = False
        
        # Session management
        self.session_manager = SessionManager()
        self.current_session: Optional[SessionData] = None
        self.hand_number = 0
        
        # Counting practice state
        self.counting_practice_mode = False
        self.count_estimates = []  # Store user estimates for accuracy tracking
        self.count_accuracy_history = []
        
        # Extended command mapping
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
            '?': self._help,
            'c': self._show_count,
            'count': self._show_count,
            'e': self._estimate_count,
            'estimate': self._estimate_count,
            'practice': self._toggle_practice_mode,
            'system': self._change_counting_system,
            'systems': self._list_counting_systems,
            'accuracy': self._show_accuracy_stats,
            'session': self._show_session_info,
            'save': self._save_session
        }
    
    def _show_count(self) -> None:
        """Display current count information."""
        count_info = self.game.get_count_info()
        
        print("\n" + "="*40)
        print("COUNT INFORMATION")
        print("="*40)
        print(f"System: {count_info['system']}")
        print(f"Running Count: {count_info['running_count']}")
        print(f"True Count: {count_info['true_count']:.1f}")
        print(f"Cards Seen: {count_info['cards_seen']}")
        print(f"Remaining Decks: {count_info['remaining_decks']:.1f}")
        print(f"Penetration: {count_info['penetration']:.1%}")
        print("="*40)
    
    def _estimate_count(self) -> None:
        """Allow user to estimate the count and get feedback."""
        if self.game.get_cards_seen() == 0:
            print("❌ No cards have been dealt yet. Start a hand first.")
            return
        
        with ErrorRecoveryContext("getting count estimates", reraise=False) as ctx:
            # Get user's running count estimate
            rc_input = input("What's your running count estimate? ")
            user_rc = validate_count_estimate(rc_input)
            
            # Get user's true count estimate
            tc_input = input("What's your true count estimate? ")
            user_tc = validate_integer_input(tc_input, -50, 50, "true count estimate")
            
            # Get actual counts
            actual_rc = self.game.get_running_count()
            actual_tc = self.game.get_true_count()
            
            # Calculate accuracy
            rc_correct = user_rc == actual_rc
            tc_accuracy = abs(user_tc - actual_tc)
            tc_correct = tc_accuracy <= 0.5  # Within 0.5 is considered correct
            
            # Store estimate for accuracy tracking
            estimate_record = {
                'user_rc': user_rc,
                'actual_rc': actual_rc,
                'user_tc': user_tc,
                'actual_tc': actual_tc,
                'rc_correct': rc_correct,
                'tc_correct': tc_correct
            }
            self.count_estimates.append(estimate_record)
            
            # Provide feedback
            print("\n" + "-"*40)
            print("COUNT FEEDBACK")
            print("-"*40)
            print(f"Your Running Count: {user_rc}")
            print(f"Actual Running Count: {actual_rc}")
            print(f"Running Count: {'✓ Correct' if rc_correct else '✗ Incorrect'}")
            print()
            print(f"Your True Count: {user_tc:.1f}")
            print(f"Actual True Count: {actual_tc:.1f}")
            print(f"True Count: {'✓ Correct' if tc_correct else '✗ Incorrect'}")
            
            if not rc_correct or not tc_correct:
                print("\nTip: Keep practicing! Count each card as it's revealed.")
            
            print("-"*40)
        
        if ctx.error:
            print(handle_user_input_error(ctx.error, "Please try again with valid numbers."))
    
    def _toggle_practice_mode(self) -> None:
        """Toggle counting practice mode on/off."""
        self.counting_practice_mode = not self.counting_practice_mode
        
        if self.counting_practice_mode:
            print("\n🎯 Counting Practice Mode ENABLED")
            print("The count will be hidden during play.")
            print("Use 'e' or 'estimate' to test your count knowledge.")
        else:
            print("\n📊 Counting Practice Mode DISABLED")
            print("Count information will be displayed normally.")
    
    def _change_counting_system(self) -> None:
        """Allow user to change the counting system."""
        print("\nAvailable counting systems:")
        system_names = self.system_manager.list_systems()
        
        for i, name in enumerate(system_names, 1):
            current = " (current)" if name == self.counting_system.name() else ""
            print(f"  {i}. {name}{current}")
        
        try:
            choice = input("\nEnter system number (or press Enter to cancel): ").strip()
            if not choice:
                return
            
            choice_num = int(choice)
            if 1 <= choice_num <= len(system_names):
                system_name = system_names[choice_num - 1]
                new_system = self.system_manager.get_system(system_name)
                
                if new_system:
                    # Switch the counting system
                    self.game.switch_counting_system(new_system)
                    self.counting_system = new_system
                    
                    print(f"\nSwitched to {system_name} counting system.")
                    print("Count has been reset due to system change.")
                else:
                    print(f"System {system_name} not found.")
            else:
                print("Invalid choice.")
                
        except ValueError:
            print("Please enter a valid number.")
        except KeyboardInterrupt:
            print("\nSystem change cancelled.")
    
    def _list_counting_systems(self) -> None:
        """List all available counting systems with descriptions."""
        print("\n" + "="*50)
        print("AVAILABLE COUNTING SYSTEMS")
        print("="*50)
        
        system_names = self.system_manager.list_systems()
        for name in system_names:
            system = self.system_manager.get_system(name)
            current = " (current)" if name == self.counting_system.name() else ""
            print(f"\n{name}{current}:")
            
            # Show card values for this system
            from src.models import Card, Suit, Rank
            sample_cards = [
                Card(Suit.HEARTS, Rank.TWO),
                Card(Suit.HEARTS, Rank.FIVE),
                Card(Suit.HEARTS, Rank.SEVEN),
                Card(Suit.HEARTS, Rank.TEN),
                Card(Suit.HEARTS, Rank.ACE)
            ]
            
            values = []
            for card in sample_cards:
                value = system.card_value(card)
                values.append(f"{card.rank.value}={value:+d}")
            
            print(f"  Card values: {', '.join(values)}")
        
        print("="*50)
    
    def _show_accuracy_stats(self) -> None:
        """Show counting accuracy statistics."""
        if not self.count_estimates:
            print("No count estimates recorded yet. Use 'e' or 'estimate' to practice counting.")
            return
        
        # Calculate statistics
        total_estimates = len(self.count_estimates)
        rc_correct = sum(1 for est in self.count_estimates if est['rc_correct'])
        tc_correct = sum(1 for est in self.count_estimates if est['tc_correct'])
        
        rc_accuracy = (rc_correct / total_estimates) * 100
        tc_accuracy = (tc_correct / total_estimates) * 100
        
        print("\n" + "="*40)
        print("COUNTING ACCURACY STATISTICS")
        print("="*40)
        print(f"Total Estimates: {total_estimates}")
        print(f"Running Count Accuracy: {rc_correct}/{total_estimates} ({rc_accuracy:.1f}%)")
        print(f"True Count Accuracy: {tc_correct}/{total_estimates} ({tc_accuracy:.1f}%)")
        
        # Show recent performance (last 10 estimates)
        if total_estimates >= 5:
            recent_estimates = self.count_estimates[-10:]
            recent_rc_correct = sum(1 for est in recent_estimates if est['rc_correct'])
            recent_tc_correct = sum(1 for est in recent_estimates if est['tc_correct'])
            recent_total = len(recent_estimates)
            
            print(f"\nRecent Performance (last {recent_total}):")
            print(f"Running Count: {recent_rc_correct}/{recent_total} ({(recent_rc_correct/recent_total)*100:.1f}%)")
            print(f"True Count: {recent_tc_correct}/{recent_total} ({(recent_tc_correct/recent_total)*100:.1f}%)")
        
        print("="*40)
    
    def _help(self) -> None:
        """Display help information including counting and session commands."""
        print("\n" + "="*50)
        print("BLACKJACK COUNTING SIMULATOR COMMANDS")
        print("="*50)
        print("Game Actions:")
        print("  h, hit      - Take another card")
        print("  s, stand    - Keep current hand")
        print("  d, double   - Double bet and take one card")
        print("  p, split    - Split pair (if available)")
        print("  r, surrender - Surrender hand (if available)")
        print("\nCounting Commands:")
        print("  c, count    - Show current count information")
        print("  e, estimate - Estimate the count and get feedback")
        print("  practice    - Toggle counting practice mode")
        print("  system      - Change counting system")
        print("  systems     - List all available counting systems")
        print("  accuracy    - Show counting accuracy statistics")
        print("\nSession Commands:")
        print("  session     - Show current session info")
        print("  save        - Save session with custom name")
        print("\nGame Control:")
        print("  n, new      - Start new hand")
        print("  q, quit     - Exit game (auto-saves session)")
        print("  help, ?     - Show this help")
        print("="*50)
    
    def _display_game_state(self) -> None:
        """Display current game state with optional count information."""
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
        
        # Show count information if not in practice mode
        if not self.counting_practice_mode and self.game.get_cards_seen() > 0:
            count_info = self.game.get_count_info()
            print(f"\nCount: RC={count_info['running_count']}, TC={count_info['true_count']:.1f} ({count_info['system']})")
        elif self.counting_practice_mode and self.game.get_cards_seen() > 0:
            print(f"\n🎯 Practice Mode: Count hidden (use 'e' to estimate)")
        
        print("-"*40)
    
    def _print_welcome(self) -> None:
        """Print welcome message with counting features."""
        print("="*70)
        print("🃏 WELCOME TO BLACKJACK COUNTING SIMULATOR 🃏")
        print("="*70)
        print("\nGame Rules:")
        print(f"  • {self.rules.num_decks} deck(s)")
        print(f"  • Dealer {'hits' if self.rules.dealer_hits_soft_17 else 'stands on'} soft 17")
        print(f"  • Blackjack pays {self.rules.blackjack_payout}:1")
        print(f"  • Double after split: {'Yes' if self.rules.double_after_split else 'No'}")
        print(f"  • Surrender allowed: {'Yes' if self.rules.surrender_allowed else 'No'}")
        print(f"\nCounting System: {self.counting_system.name()}")
        print("\nCounting Features:")
        print("  • Real-time count tracking")
        print("  • Count estimation practice")
        print("  • Multiple counting systems")
        print("  • Accuracy statistics")
        print("\nType 'help' or '?' for all commands.")
        print("Type 'practice' to enable counting practice mode.")
        print("="*70)
    
    def start(self) -> None:
        """Start the interactive CLI session with automatic session creation."""
        self.running = True
        self._create_session()
        self._print_welcome()
        self._new_hand()
        
        while self.running:
            try:
                self._game_loop()
            except KeyboardInterrupt:
                print("\n\nSaving session...")
                self._auto_save_session()
                print("Goodbye!")
                break
            except Exception as e:
                print(f"Error: {e}")
                print("Type 'help' for available commands.")
    
    def _create_session(self) -> None:
        """Create a new session for tracking gameplay."""
        session_id = self.session_manager.generate_session_id()
        metadata = SessionMetadata(
            session_id=session_id,
            name=f"Counting Session {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )
        
        stats = SessionStats(session_id=session_id)
        
        self.current_session = SessionData(
            session_id=session_id,
            metadata=metadata,
            rules=self.rules,
            stats=stats,
            counting_system=self.counting_system.name()
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
            running_count=self.game.get_running_count(),
            true_count=self.game.get_true_count(),
            result=result,
            bet_amount=1.0  # Default bet amount
        )
        
        # Add to session
        self.current_session.add_hand_record(hand_record)
        
        # Update session stats
        self.current_session.stats.update_hand_result(result, 1.0)
        
        # Update counting accuracy if we have estimates
        if self.count_estimates:
            latest_estimate = self.count_estimates[-1]
            self.current_session.stats.update_counting_accuracy(
                latest_estimate['user_rc'], 
                latest_estimate['actual_rc']
            )
    
    def _new_hand(self) -> None:
        """Start a new hand and record the previous one if completed."""
        # Record the previous hand if it was completed
        if self.game.is_game_over():
            self._record_hand()
        
        # Call parent method to start new hand
        super()._new_hand()
    
    def _quit(self) -> None:
        """Quit the game and save the session."""
        # Record the current hand if it's completed
        if self.game.is_game_over():
            self._record_hand()
        
        self._auto_save_session()
        self.running = False
        print("Session saved. Thanks for playing!")
    
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
    
    def _show_session_info(self) -> None:
        """Show current session information."""
        if not self.current_session:
            print("No active session.")
            return
        
        print(f"\n=== Current Session ===")
        print(f"Name: {self.current_session.metadata.name}")
        print(f"Hands Played: {len(self.current_session.hands_history)}")
        print(f"Counting System: {self.current_session.counting_system}")
        
        if self.current_session.stats.hands_played > 0:
            stats = self.current_session.stats
            print(f"Win Rate: {stats.win_rate():.1f}%")
            print(f"Counting Accuracy: {stats.counting_accuracy.accuracy_percentage():.1f}%")
            print(f"Net Result: {stats.net_result:+.2f} units")
        
        print()
    
    def _save_session(self) -> None:
        """Manually save the current session with a custom name."""
        if not self.current_session:
            print("No active session to save.")
            return
        
        name = input("Enter session name (or press Enter to keep current): ").strip()
        if name:
            self.current_session.metadata.name = name
        
        try:
            session_id = self.session_manager.save_session(self.current_session)
            print(f"💾 Session saved: {session_id[:8]}...")
        except Exception as e:
            print(f"⚠️ Failed to save session: {e}")


def main():
    """Main entry point for the counting CLI."""
    # Create default rules
    rules = GameRules()
    
    # Create and start counting CLI
    cli = CountingCLI(rules)
    cli.start()


if __name__ == "__main__":
    main()