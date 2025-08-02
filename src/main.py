import os
from dealer import Dealer
from deck import Deck
import json
import sys
from player import Player

def read_config():
    dir = os.path.dirname(os.path.abspath('__file__'))
    #try:
    dir = dir + '/config.json'
    with open(dir, 'r') as conf:
        data = json.load(conf)

    #except:
    #    print(f'Config File Not Found! Please check {dir}')
    #    sys.exit(0)
    return data

def setup():
    game_info = read_config()
    shoe = Deck(game_info['decks'])
    p_broll = game_info['bankroll']


def update():
    pass

def main():
    #initialize the game
    game_info = read_config()
    shoe = Deck(game_info['decks'])
    bankroll = game_info['bankroll']
    count = 0
    true_count = 0
    shoe.shuffle()
    print(shoe)
    player = Player(100)
    dealer = Dealer()
    player.cards, dealer.cards = shoe.deal()
    print(player.cards)
    print(dealer.cards)




    #while True:
    #    p_cards, d_cards = shoe.deal()









if __name__ == "__main__":
    main()
