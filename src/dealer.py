from card import Card

class Dealer():

    def __init__(self):
        self.cards = []

    def check_value(self):
        value = 0
        count_aces = 0
        for card in self.cards:
            value += card.worth
            if card.value == 'A':
                count_aces += 1
        while(True):
            if value > 21:
                if count_aces > 0:
                    value = value - 10
                    count_aces = count_aces - 1
                    continue
        return value

    def decide(self):
        pass
