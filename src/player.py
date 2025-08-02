class Player():

    def __init__(self, br):
        self.bankroll = br
        self.cards = []


    def bet(self):
        while(True):
            try:
                bet = int(input('Please Place a bet: '))
            except TypeError as e:
                print('Please enter an Integer Value Less than Your total bankroll')
                continue

            if bet > self.bankroll:
                print('Your bet is too large! Please Input a bet lower than your total bankroll.')
                continue
            self.bankroll = self.bankroll - bet
            return bet

    def decide(self):
        while(True):
            decision = input("What would you like to do? (Type 'help' to see all options)")
            if decision.lower() == 'help':
                print('''Player Decisons:\n
                       1: Hit - type h or 1\n
                       2: Stand - type s or 2\n
                       3: Double Down - type d or 3\n
                       4: Split - type / or 4\n
                       5: Surrender - type g or 5''')

            match decision.lower():
                case x if x == '1' or x == 'h':
                    return 'HIT'
                    break
                case x if x =='2' or x == 's':
                    return 'STAND'
                    break
                case x if x == '3' or x == 'd':
                    return 'DOUBLE'
                    break
                case x if x == '4' or x == '/':
                    return 'SPLIT'
                    break
                case x if x == '5' or x == 'g':
                    return 'SURRENDER'
                    break
                case _:
                    print('Please enter a valid input, or type "help" to see the list of valid options')
                    break

    def discard(self):
        self.cards = []

    def __str__
