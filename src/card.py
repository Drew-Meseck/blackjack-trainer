class Card:
    def __init__(self, v, s):
        self.value = v
        self.suit = s
        self.worth = self.get_worth(v)

    def get_worth(self, v):
        if isinstance(v, int):
            return v
        elif v == 'A':
            return (1, 11)
        else:
            return 10                            

    def __str__(self):
        return f'{str(self.value)}{self.suit}'
        
