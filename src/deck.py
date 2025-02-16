from card import Card
import random as rand

HEARTS   = '♥️'
DIAMONDS = '♦️'
CLUBS    = '♣️'
SPADES   = '♠️'

class Deck:
    def __init__(self, dc):
        self.deck_count = dc
        self.cards = self.create_deck(dc)
        self.discards = []

    def create_deck(self, dc):
        cards = []
        specs = [2, 3, 4, 5, 6, 7, 8, 9, 10, 'J', 'Q', 'K', 'A']
        for _ in range(dc):
            d = []
            for c in specs:
                d.append(Card(c, HEARTS))
                d.append(Card(c, DIAMONDS))
                d.append(Card(c, CLUBS))
                d.append(Card(c, SPADES))
            cards = cards + d
        
        return cards    
            

    def shuffle(self):
        rand.shuffle(self.cards)

    def deal(self):
        player = []
        dealer = []

        for _ in range(1):
            dealer.append(self.cards.pop())
            player.append(self.cards.pop())

        return player, dealer
        
    def __str__(self):
        top_5 = ', '.join(map(str, self.cards[:5]))
        return f"Remaining Cards in Shoe: {len(self.cards)}\n {top_5}"
        
