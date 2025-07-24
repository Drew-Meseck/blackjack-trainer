"""Full-featured CLI with configuration and session management."""

import sys
import os
from typing import Optional, Dict, Callable, List
from datetime import datetime, timedelta
from src.game import CountingBlackjackGame
from src.models import GameRules, Action, Outcome
from src.counting import CountingSystemManager, CountingSystem
from src.session import SessionManager, SessionData, SessionMetadata
from src.analytics import SessionStats, PerformanceTracker, SessionReport

class ConfigurationCLI:
    """CLI for managing game configuration and session management."""
    
    def __init__(self):
        """Initialize the configuration CLI."""
        self.session_manager = SessionManager()
        self.counting_manager = CountingSystemManager()
        self.current_rules = GameRules()  # Default rules
        self.current_session: Optional[SessionData] = None
        
        # Command mapping
        self.commands: Dict[str, Callable] = {
            'config': self._config_menu,
            'session': self._session_menu,
            'stats': self._stats_menu,
            'help': self._show_help,
            'quit': self._quit,
            'exit': self._quit
        }
    
    def run(self) -> None:
        """Run the main CLI loop."""
        print("=== Blackjack Simulator Configuration & Session Manager ===")
        print("Type 'help' for available commands or 'quit' to exit.")
        print()
        
        while True:
            try:
                command = input("blackjack> ").strip().lower()
                
                if not command:
                    continue
                
                if command in self.commands:
                    result = self.commands[command]()
                    if result == 'quit':
                        break
                else:
                    print(f"Unknown command: {command}")
                    print("Type 'help' for available commands.")
                
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"Error: {e}")
    
    def _show_help(self) -> None:
        """Show available commands."""
        print("\nAvailable Commands:")
        print("  config  - Configure game rules and counting systems")
        print("  session - Manage simulation sessions (save/load/delete)")
        print("  stats   - View session statistics and reports")
        print("  help    - Show this help message")
        print("  quit    - Exit the program")
        print()
    
    def _config_menu(self) -> None:
        """Handle configuration menu."""
        while True:
            print("\n=== Configuration Menu ===")
            print("1. View current rules")
            print("2. Configure dealer rules")
            print("3. Configure player options")
            print("4. Configure deck settings")
            print("5. Configure counting system")
            print("6. Reset to defaults")
            print("7. Back to main menu")
            
            choice = input("Select option (1-7): ").strip()
            
            if choice == '1':
                self._show_current_rules()
            elif choice == '2':
                self._configure_dealer_rules()
            elif choice == '3':
                self._configure_player_options()
            elif choice == '4':
                self._configure_deck_settings()
            elif choice == '5':
                self._configure_counting_system()
            elif choice == '6':
                self._reset_rules()
            elif choice == '7':
                break
            else:
                print("Invalid choice. Please select 1-7.")
    
    def _show_current_rules(self) -> None:
        """Display current game rules."""
        print("\n=== Current Game Rules ===")
        print(f"Dealer hits soft 17: {self.current_rules.dealer_hits_soft_17}")
        print(f"Double after split: {self.current_rules.double_after_split}")
        print(f"Surrender allowed: {self.current_rules.surrender_allowed}")
        print(f"Number of decks: {self.current_rules.num_decks}")
        print(f"Penetration: {self.current_rules.penetration:.1%}")
        print(f"Blackjack payout: {self.current_rules.blackjack_payout}:1")
        print()
    
    def _configure_dealer_rules(self) -> None:
        """Configure dealer-specific rules."""
        print("\n=== Dealer Rules Configuration ===")
        
        # Dealer hits soft 17
        current = "Yes" if self.current_rules.dealer_hits_soft_17 else "No"
        print(f"Current: Dealer hits soft 17 = {current}")
        
        while True:
            choice = input("Dealer hits soft 17? (y/n): ").strip().lower()
            if choice in ['y', 'yes']:
                self.current_rules.dealer_hits_soft_17 = True
                break
            elif choice in ['n', 'no']:
                self.current_rules.dealer_hits_soft_17 = False
                break
            else:
                print("Please enter 'y' or 'n'")
        
        print("Dealer rules updated!")
    
    def _configure_player_options(self) -> None:
        """Configure player option rules."""
        print("\n=== Player Options Configuration ===")
        
        # Double after split
        current = "Yes" if self.current_rules.double_after_split else "No"
        print(f"Current: Double after split = {current}")
        
        while True:
            choice = input("Allow double after split? (y/n): ").strip().lower()
            if choice in ['y', 'yes']:
                self.current_rules.double_after_split = True
                break
            elif choice in ['n', 'no']:
                self.current_rules.double_after_split = False
                break
            else:
                print("Please enter 'y' or 'n'")
        
        # Surrender allowed
        current = "Yes" if self.current_rules.surrender_allowed else "No"
        print(f"Current: Surrender allowed = {current}")
        
        while True:
            choice = input("Allow surrender? (y/n): ").strip().lower()
            if choice in ['y', 'yes']:
                self.current_rules.surrender_allowed = True
                break
            elif choice in ['n', 'no']:
                self.current_rules.surrender_allowed = False
                break
            else:
                print("Please enter 'y' or 'n'")
        
        print("Player options updated!")
    
    def _configure_deck_settings(self) -> None:
        """Configure deck and shoe settings."""
        print("\n=== Deck Settings Configuration ===")
        
        # Number of decks
        print(f"Current: {self.current_rules.num_decks} decks")
        
        while True:
            try:
                num_decks = int(input("Number of decks (1, 2, 4, 6, 8): "))
                if num_decks in [1, 2, 4, 6, 8]:
                    self.current_rules.num_decks = num_decks
                    break
                else:
                    print("Please enter 1, 2, 4, 6, or 8")
            except ValueError:
                print("Please enter a valid number")
        
        # Penetration
        print(f"Current: {self.current_rules.penetration:.1%} penetration")
        
        while True:
            try:
                penetration = float(input("Penetration percentage (10-90): ")) / 100
                if 0.1 <= penetration <= 0.9:
                    self.current_rules.penetration = penetration
                    break
                else:
                    print("Please enter a value between 10 and 90")
            except ValueError:
                print("Please enter a valid number")
        
        print("Deck settings updated!")
    
    def _configure_counting_system(self) -> None:
        """Configure counting system selection."""
        print("\n=== Counting System Configuration ===")
        
        systems = self.counting_manager.list_systems()
        
        print("Available counting systems:")
        for i, system_name in enumerate(systems, 1):
            print(f"{i}. {system_name}")
        
        while True:
            try:
                choice = int(input(f"Select system (1-{len(systems)}): "))
                if 1 <= choice <= len(systems):
                    selected_system = systems[choice - 1]
                    print(f"Selected counting system: {selected_system}")
                    # Note: This would be used when creating a game session
                    break
                else:
                    print(f"Please enter a number between 1 and {len(systems)}")
            except ValueError:
                print("Please enter a valid number")
    
    def _reset_rules(self) -> None:
        """Reset rules to defaults."""
        confirm = input("Reset all rules to defaults? (y/n): ").strip().lower()
        if confirm in ['y', 'yes']:
            self.current_rules = GameRules()
            print("Rules reset to defaults!")
        else:
            print("Reset cancelled.")
    
    def _session_menu(self) -> None:
        """Handle session management menu."""
        while True:
            print("\n=== Session Management ===")
            print("1. List sessions")
            print("2. Load session")
            print("3. Save current session")
            print("4. Delete session")
            print("5. Session details")
            print("6. Cleanup sessions")
            print("7. Back to main menu")
            
            choice = input("Select option (1-7): ").strip()
            
            if choice == '1':
                self._list_sessions()
            elif choice == '2':
                self._load_session()
            elif choice == '3':
                self._save_session()
            elif choice == '4':
                self._delete_session()
            elif choice == '5':
                self._show_session_details()
            elif choice == '6':
                self._cleanup_sessions()
            elif choice == '7':
                break
            else:
                print("Invalid choice. Please select 1-7.")
    
    def _list_sessions(self) -> None:
        """List all available sessions."""
        sessions = self.session_manager.list_sessions()
        
        if not sessions:
            print("\nNo sessions found.")
            return
        
        print(f"\n=== Available Sessions ({len(sessions)} total) ===")
        print(f"{'ID':<8} {'Name':<20} {'Created':<20} {'Hands':<8} {'Duration':<10}")
        print("-" * 70)
        
        for session in sessions:
            session_id = session.session_id[:8] if session.session_id else "Unknown"
            name = session.name or "Unnamed"
            created = session.created_time.strftime("%Y-%m-%d %H:%M") if session.created_time else "Unknown"
            hands = str(session.hands_played)
            
            # Calculate duration
            if session.created_time and session.last_modified:
                duration = session.last_modified - session.created_time
                duration_str = str(duration).split('.')[0]  # Remove microseconds
            else:
                duration_str = "Unknown"
            
            print(f"{session_id:<8} {name[:20]:<20} {created:<20} {hands:<8} {duration_str:<10}")
        
        print()
    
    def _load_session(self) -> None:
        """Load a session from storage."""
        sessions = self.session_manager.list_sessions()
        
        if not sessions:
            print("No sessions available to load.")
            return
        
        print("\nAvailable sessions:")
        for i, session in enumerate(sessions, 1):
            name = session.name or "Unnamed"
            created = session.created_time.strftime("%Y-%m-%d %H:%M") if session.created_time else "Unknown"
            print(f"{i}. {name} (Created: {created}, Hands: {session.hands_played})")
        
        while True:
            try:
                choice = int(input(f"Select session to load (1-{len(sessions)}): "))
                if 1 <= choice <= len(sessions):
                    selected_session = sessions[choice - 1]
                    try:
                        self.current_session = self.session_manager.load_session(selected_session.session_id)
                        print(f"Loaded session: {selected_session.name or 'Unnamed'}")
                        
                        # Update current rules from session
                        if self.current_session.rules:
                            self.current_rules = self.current_session.rules
                            print("Game rules updated from session.")
                        
                        break
                    except Exception as e:
                        print(f"Failed to load session: {e}")
                        break
                else:
                    print(f"Please enter a number between 1 and {len(sessions)}")
            except ValueError:
                print("Please enter a valid number")
    
    def _save_session(self) -> None:
        """Save current session."""
        if not self.current_session:
            print("No active session to save. Start a game session first.")
            return
        
        name = input("Enter session name (optional): ").strip()
        
        try:
            session_id = self.session_manager.save_session(self.current_session, name or None)
            print(f"Session saved with ID: {session_id[:8]}...")
        except Exception as e:
            print(f"Failed to save session: {e}")
    
    def _delete_session(self) -> None:
        """Delete a session."""
        sessions = self.session_manager.list_sessions()
        
        if not sessions:
            print("No sessions available to delete.")
            return
        
        print("\nAvailable sessions:")
        for i, session in enumerate(sessions, 1):
            name = session.name or "Unnamed"
            created = session.created_time.strftime("%Y-%m-%d %H:%M") if session.created_time else "Unknown"
            print(f"{i}. {name} (Created: {created})")
        
        while True:
            try:
                choice = int(input(f"Select session to delete (1-{len(sessions)}): "))
                if 1 <= choice <= len(sessions):
                    selected_session = sessions[choice - 1]
                    
                    confirm = input(f"Delete session '{selected_session.name or 'Unnamed'}'? (y/n): ").strip().lower()
                    if confirm in ['y', 'yes']:
                        try:
                            success = self.session_manager.delete_session(selected_session.session_id)
                            if success:
                                print("Session deleted successfully.")
                            else:
                                print("Session not found.")
                        except Exception as e:
                            print(f"Failed to delete session: {e}")
                    else:
                        print("Deletion cancelled.")
                    break
                else:
                    print(f"Please enter a number between 1 and {len(sessions)}")
            except ValueError:
                print("Please enter a valid number")
    
    def _show_session_details(self) -> None:
        """Show detailed information about a session."""
        sessions = self.session_manager.list_sessions()
        
        if not sessions:
            print("No sessions available.")
            return
        
        print("\nAvailable sessions:")
        for i, session in enumerate(sessions, 1):
            name = session.name or "Unnamed"
            print(f"{i}. {name}")
        
        while True:
            try:
                choice = int(input(f"Select session for details (1-{len(sessions)}): "))
                if 1 <= choice <= len(sessions):
                    selected_session = sessions[choice - 1]
                    
                    try:
                        full_session = self.session_manager.load_session(selected_session.session_id)
                        self._display_session_details(full_session)
                    except Exception as e:
                        print(f"Failed to load session details: {e}")
                    break
                else:
                    print(f"Please enter a number between 1 and {len(sessions)}")
            except ValueError:
                print("Please enter a valid number")
    
    def _display_session_details(self, session: SessionData) -> None:
        """Display detailed session information."""
        print(f"\n=== Session Details ===")
        print(f"ID: {session.session_id}")
        print(f"Name: {session.metadata.name or 'Unnamed'}")
        print(f"Created: {session.metadata.created_time}")
        print(f"Last Modified: {session.metadata.last_modified}")
        print(f"Hands Played: {session.metadata.hands_played}")
        
        if session.rules:
            print(f"\nGame Rules:")
            print(f"  Decks: {session.rules.num_decks}")
            print(f"  Penetration: {session.rules.penetration:.1%}")
            print(f"  Dealer hits soft 17: {session.rules.dealer_hits_soft_17}")
            print(f"  Double after split: {session.rules.double_after_split}")
            print(f"  Surrender allowed: {session.rules.surrender_allowed}")
        
        if session.stats:
            print(f"\nSession Statistics:")
            print(f"  Hands won: {session.stats.hands_won}")
            print(f"  Hands lost: {session.stats.hands_lost}")
            print(f"  Hands pushed: {session.stats.hands_pushed}")
            
            if session.stats.hands_played > 0:
                win_rate = (session.stats.hands_won / session.stats.hands_played) * 100
                print(f"  Win rate: {win_rate:.1f}%")
            
            print(f"  Counting accuracy: {session.stats.counting_accuracy.accuracy_percentage():.1f}%")
            print(f"  Strategy adherence: {session.stats.strategy_accuracy.adherence_percentage():.1f}%")
        
        print()
    
    def _cleanup_sessions(self) -> None:
        """Cleanup and maintenance operations."""
        print("\n=== Session Cleanup ===")
        print("1. Remove orphaned files")
        print("2. Validate all sessions")
        print("3. Remove corrupted sessions")
        print("4. Storage information")
        print("5. Back")
        
        choice = input("Select option (1-5): ").strip()
        
        if choice == '1':
            removed = self.session_manager.cleanup_orphaned_files()
            print(f"Removed {removed} orphaned files.")
        
        elif choice == '2':
            errors = self.session_manager.validate_all_sessions()
            if not errors:
                print("All sessions are valid.")
            else:
                print(f"Found {len(errors)} corrupted sessions:")
                for session_id, error in errors.items():
                    print(f"  {session_id[:8]}...: {error}")
        
        elif choice == '3':
            confirm = input("Remove all corrupted sessions? (y/n): ").strip().lower()
            if confirm in ['y', 'yes']:
                actions = self.session_manager.recover_corrupted_sessions(remove_corrupted=True)
                if actions:
                    print("Recovery actions taken:")
                    for session_id, action in actions.items():
                        print(f"  {session_id[:8] if len(session_id) > 8 else session_id}: {action}")
                else:
                    print("No corrupted sessions found.")
            else:
                print("Cleanup cancelled.")
        
        elif choice == '4':
            info = self.session_manager.get_storage_info()
            print(f"\nStorage Information:")
            print(f"  Directory: {info['sessions_directory']}")
            print(f"  Total sessions: {info['total_sessions']}")
            print(f"  Total size: {info['total_size_mb']:.2f} MB")
            print(f"  Metadata index exists: {info['metadata_index_exists']}")
    
    def _stats_menu(self) -> None:
        """Handle statistics and reporting menu."""
        while True:
            print("\n=== Statistics & Reports ===")
            print("1. Current session stats")
            print("2. Session comparison")
            print("3. Performance trends")
            print("4. Generate session report")
            print("5. Export session data")
            print("6. Back to main menu")
            
            choice = input("Select option (1-6): ").strip()
            
            if choice == '1':
                self._show_current_session_stats()
            elif choice == '2':
                self._compare_sessions()
            elif choice == '3':
                self._show_performance_trends()
            elif choice == '4':
                self._generate_session_report()
            elif choice == '5':
                self._export_session_data()
            elif choice == '6':
                break
            else:
                print("Invalid choice. Please select 1-6.")
    
    def _show_current_session_stats(self) -> None:
        """Show statistics for current session."""
        if not self.current_session or not self.current_session.stats:
            print("No active session or statistics available.")
            return
        
        stats = self.current_session.stats
        
        print(f"\n=== Current Session Statistics ===")
        print(f"Hands played: {stats.hands_played}")
        print(f"Hands won: {stats.hands_won}")
        print(f"Hands lost: {stats.hands_lost}")
        print(f"Hands pushed: {stats.hands_pushed}")
        
        if stats.hands_played > 0:
            win_rate = (stats.hands_won / stats.hands_played) * 100
            loss_rate = (stats.hands_lost / stats.hands_played) * 100
            push_rate = (stats.hands_pushed / stats.hands_played) * 100
            
            print(f"\nWin rate: {win_rate:.1f}%")
            print(f"Loss rate: {loss_rate:.1f}%")
            print(f"Push rate: {push_rate:.1f}%")
        
        print(f"\nCounting accuracy: {stats.counting_accuracy.accuracy_percentage():.1f}%")
        print(f"Strategy adherence: {stats.strategy_accuracy.adherence_percentage():.1f}%")
        
        if hasattr(stats, 'total_bet') and hasattr(stats, 'total_winnings'):
            net_result = stats.total_winnings - stats.total_bet
            print(f"\nNet result: {net_result:+.2f} units")
        
        print()
    
    def _compare_sessions(self) -> None:
        """Compare statistics between sessions."""
        sessions = self.session_manager.list_sessions()
        
        if len(sessions) < 2:
            print("Need at least 2 sessions for comparison.")
            return
        
        print("\nSelect sessions to compare:")
        for i, session in enumerate(sessions, 1):
            name = session.name or "Unnamed"
            print(f"{i}. {name} ({session.hands_played} hands)")
        
        try:
            choice1 = int(input("First session: ")) - 1
            choice2 = int(input("Second session: ")) - 1
            
            if 0 <= choice1 < len(sessions) and 0 <= choice2 < len(sessions) and choice1 != choice2:
                session1 = self.session_manager.load_session(sessions[choice1].session_id)
                session2 = self.session_manager.load_session(sessions[choice2].session_id)
                
                self._display_session_comparison(session1, session2)
            else:
                print("Invalid session selection.")
        except (ValueError, IndexError):
            print("Invalid input.")
    
    def _display_session_comparison(self, session1: SessionData, session2: SessionData) -> None:
        """Display comparison between two sessions."""
        name1 = session1.metadata.name or "Session 1"
        name2 = session2.metadata.name or "Session 2"
        
        print(f"\n=== Session Comparison ===")
        print(f"{'Metric':<25} {name1[:15]:<15} {name2[:15]:<15} {'Difference':<15}")
        print("-" * 70)
        
        # Basic stats
        if session1.stats and session2.stats:
            stats1, stats2 = session1.stats, session2.stats
            
            print(f"{'Hands played':<25} {stats1.hands_played:<15} {stats2.hands_played:<15} {stats2.hands_played - stats1.hands_played:+d}")
            
            if stats1.hands_played > 0 and stats2.hands_played > 0:
                win_rate1 = (stats1.hands_won / stats1.hands_played) * 100
                win_rate2 = (stats2.hands_won / stats2.hands_played) * 100
                print(f"{'Win rate (%)':<25} {win_rate1:<15.1f} {win_rate2:<15.1f} {win_rate2 - win_rate1:+.1f}")
            
            accuracy1 = stats1.counting_accuracy.accuracy_percentage()
            accuracy2 = stats2.counting_accuracy.accuracy_percentage()
            print(f"{'Counting accuracy (%)':<25} {accuracy1:<15.1f} {accuracy2:<15.1f} {accuracy2 - accuracy1:+.1f}")
            
            adherence1 = stats1.strategy_accuracy.adherence_percentage()
            adherence2 = stats2.strategy_accuracy.adherence_percentage()
            print(f"{'Strategy adherence (%)':<25} {adherence1:<15.1f} {adherence2:<15.1f} {adherence2 - adherence1:+.1f}")
        
        print()
    
    def _show_performance_trends(self) -> None:
        """Show performance trends across sessions."""
        sessions = self.session_manager.list_sessions()
        
        if len(sessions) < 2:
            print("Need at least 2 sessions to show trends.")
            return
        
        print(f"\n=== Performance Trends ({len(sessions)} sessions) ===")
        
        # Calculate averages
        total_hands = sum(s.hands_played for s in sessions)
        total_accuracy = sum(s.counting_accuracy if hasattr(s, 'counting_accuracy') else 0 for s in sessions)
        total_adherence = sum(s.strategy_adherence if hasattr(s, 'strategy_adherence') else 0 for s in sessions)
        
        if len(sessions) > 0:
            avg_hands = total_hands / len(sessions)
            avg_accuracy = (total_accuracy / len(sessions)) * 100
            avg_adherence = (total_adherence / len(sessions)) * 100
            
            print(f"Average hands per session: {avg_hands:.1f}")
            print(f"Average counting accuracy: {avg_accuracy:.1f}%")
            print(f"Average strategy adherence: {avg_adherence:.1f}%")
        
        # Show recent sessions trend
        recent_sessions = sessions[:5]  # Last 5 sessions
        if len(recent_sessions) >= 2:
            print(f"\nRecent trend (last {len(recent_sessions)} sessions):")
            
            first_session = recent_sessions[-1]  # Oldest of recent
            last_session = recent_sessions[0]   # Most recent
            
            if hasattr(first_session, 'counting_accuracy') and hasattr(last_session, 'counting_accuracy'):
                accuracy_trend = (last_session.counting_accuracy - first_session.counting_accuracy) * 100
                adherence_trend = (last_session.strategy_adherence - first_session.strategy_adherence) * 100
                
                print(f"Counting accuracy trend: {accuracy_trend:+.1f}%")
                print(f"Strategy adherence trend: {adherence_trend:+.1f}%")
        
        print()
    
    def _generate_session_report(self) -> None:
        """Generate a comprehensive session report."""
        if not self.current_session:
            print("No active session. Load a session first.")
            return
        
        # This would use the PerformanceTracker to generate a detailed report
        print(f"\n=== Session Report ===")
        print(f"Session: {self.current_session.metadata.name or 'Unnamed'}")
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Basic session info
        print(f"Session Duration: {self.current_session.metadata.created_time} to {self.current_session.metadata.last_modified}")
        print(f"Total Hands: {self.current_session.metadata.hands_played}")
        
        if self.current_session.stats:
            stats = self.current_session.stats
            print(f"\nPerformance Summary:")
            print(f"  Win Rate: {(stats.hands_won / max(stats.hands_played, 1)) * 100:.1f}%")
            print(f"  Counting Accuracy: {stats.counting_accuracy.accuracy_percentage():.1f}%")
            print(f"  Strategy Adherence: {stats.strategy_accuracy.adherence_percentage():.1f}%")
        
        if self.current_session.rules:
            print(f"\nGame Configuration:")
            print(f"  Decks: {self.current_session.rules.num_decks}")
            print(f"  Penetration: {self.current_session.rules.penetration:.1%}")
            print(f"  Dealer hits soft 17: {self.current_session.rules.dealer_hits_soft_17}")
        
        print("\nReport generated successfully!")
    
    def _export_session_data(self) -> None:
        """Export session data to file."""
        sessions = self.session_manager.list_sessions()
        
        if not sessions:
            print("No sessions available to export.")
            return
        
        print("\nSelect session to export:")
        for i, session in enumerate(sessions, 1):
            name = session.name or "Unnamed"
            print(f"{i}. {name}")
        
        try:
            choice = int(input(f"Select session (1-{len(sessions)}): ")) - 1
            if 0 <= choice < len(sessions):
                selected_session = sessions[choice]
                filename = f"session_export_{selected_session.session_id[:8]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                
                # Copy session file to export location
                session_data = self.session_manager.load_session(selected_session.session_id)
                
                with open(filename, 'w', encoding='utf-8') as f:
                    import json
                    json.dump(session_data.to_dict(), f, indent=2, ensure_ascii=False, default=str)
                
                print(f"Session exported to: {filename}")
            else:
                print("Invalid selection.")
        except (ValueError, IndexError):
            print("Invalid input.")
    
    def _quit(self) -> str:
        """Quit the application."""
        print("Goodbye!")
        return 'quit'


def main():
    """Main entry point for the configuration CLI."""
    cli = ConfigurationCLI()
    cli.run()


if __name__ == "__main__":
    main()