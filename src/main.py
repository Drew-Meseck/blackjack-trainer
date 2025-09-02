"""Main entry point for the blackjack simulator."""

from src.cli import GameCLI
from src.models import GameRules


def main():
    """Main entry point for the blackjack simulator."""
    # Create default game rules
    rules = GameRules()
    
    # Create and start the CLI
    cli = GameCLI(rules)
    cli.start()


if __name__ == "__main__":
    main()