"""Action enum for blackjack player decisions."""

from enum import Enum


class Action(Enum):
    """Possible player actions in blackjack."""
    HIT = "hit"
    STAND = "stand"
    DOUBLE = "double"
    SPLIT = "split"
    SURRENDER = "surrender"