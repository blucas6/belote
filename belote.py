import copy
import itertools
import enum
import time
from datetime import timedelta
import numpy

class PrintLevel(enum.IntEnum):
    NONE = 0
    ERROR = 1
    WARNING = 2
    INFO = 3
    EXTRA_INFO = 4

def cardPoints(card, trump):
    pointDict = {
            'A': 11,
            'K': 4,
            'Q': 3,
            'J': 2,
            '10': 10,
            '9': 0,
            '8': 0,
            '7': 0
            }
    trumpDict = {
            'A': 11,
            'K': 4,
            'Q': 3,
            'J': 20,
            '10': 10,
            '9': 14,
            '8': 0,
            '7': 0
            }
    if len(card) == 3:
        if card[2] == trump:
            return trumpDict[card[:2]]
        else:
            return pointDict[card[:2]]
    else:
        if card[1] == trump:
            return trumpDict[card[:1]]
        else:
            return pointDict[card[:1]]

def get_card_suit(card):
    if len(card) == 3:
        return card[2]
    else:
        return card[1]

class Table:
    def __init__(self):
        self.cards = [['','','',''] for _ in range(8)]

class Player:
    def __init__(self, id):
        self.id = id + 1
        self.hand = []
        self.handrounds = [[] for _ in range(8)]

class Game:
    def __init__(self):
        self.lead = ''
        '''Lead card in the round'''
        self.trump = ''
        '''Current trump suit'''
        self.curr_turn = 0
        '''Tracks the player index in the player list [0..3]'''
        self.card_played = 0
        '''Tracks the cards that have been played [0..3]'''
        self.round = 0
        '''Tracks the round [0..7]'''
        self.table = Table()
        '''Table object for the game'''
        self.players = [Player(x) for x in range(4)]
        '''Player list'''
        self.team_points = [0,0]
        '''Tracks the points per team'''
        self.fulldeck = ['A♣','K♦','Q♥','J♠','10♦','9♣','8♥','7♠']
        '''Full deck for the game'''
        self.deck_played = []
        '''List of cards that have been played'''
        self.print_level = PrintLevel.ERROR
        '''Log level for messages'''
        self.errors = 0
        '''Tracks how many errors occured'''

        # unit testing #
        self.unit_testing = False
        '''True will record sets, False will not'''
        self.check_sets = []
        '''Where to record solved sets'''

    def addCheckSet(self, cardset):
        '''For unit testing, record all sets solved during calculations'''
        if self.unit_testing:
            self.check_sets.append(list(cardset))

    def get_valid_set(self, cards, lead, trump, table, turn, card_played):
        if card_played == 0:
            return cards
        partner_played = ''
        if turn == 0:
            partner_played = table[2]
        elif turn == 1:
            partner_played = table[3]
        elif turn == 2:
            partner_played = table[0]
        elif turn == 3:
            partner_played = table[1]
        else:
            self.print(f'Sent invalid turn -> {turn}', print_level=PrintLevel.ERROR)
            return cards
        suits = [get_card_suit(card) for card in cards]
        valid = []
        lead_suit = get_card_suit(lead)
        # can follow suit
        if lead_suit in suits:
            # can follow suit trump - need to play higher
            if lead_suit == trump:
                for ix,suit in enumerate(suits):
                    if suit == lead_suit and cardPoints(cards[ix],trump) > cardPoints(lead,trump):
                        valid.append(cards[ix])
                # nothing higher
                if not valid:
                    valid = [cards[ix] for ix,suit in enumerate(suits) if suit == lead_suit]
            # can follow suit
            else:
                valid = [cards[ix] for ix,suit in enumerate(suits) if suit == lead_suit]
        else:
            # check partner is winning
            tp, wi = self.solveSet(trump, lead, table)
            # partner is winning - no need to play trump
            if table[wi] == partner_played:
                valid = cards
            # partner is not winning need to cut - play trump
            elif trump in suits:
                valid = [cards[ix] for ix,suit in enumerate(suits) if suit == trump]
            # throw off
            else:
                valid = cards
        return valid

    def solveSet(self, trump, lead, cards) -> tuple[list[int],int]:
        '''
        Given a card set with the lead and trump
        return the points per team and winning player
        '''
        if not lead:
            self.print(f'Lead card is empty!', print_level=PrintLevel.ERROR)
            return [0,0], -1
        totalPoints = 0
        for card in cards:
            if card:
                totalPoints += cardPoints(card, trump)
        if not lead in cards:
            self.print(f'Lead card {lead} is not in {cards}', print_level=PrintLevel.ERROR)
            return [0,0],-1
        leadidx = cards.index(lead)
        cardtobeat = lead
        for i in range(len(cards)):
            idx = (leadidx + i) % len(cards)
            if cards[idx] == cardtobeat:
                continue
            if cards[idx] == '':
                continue
            # current card is trump
            if cards[idx][-1] == trump: 
                # card to beat is also trump
                if cardtobeat[-1] == trump:
                    if cardPoints(cards[idx], trump) > cardPoints(cardtobeat, trump):
                        cardtobeat = cards[idx]
                # card to beat is not trump
                else:
                    cardtobeat = cards[idx]
            else:
                # current card is not trump and card to beat is not trump
                if cardtobeat[-1] != trump:
                    # check if matches lead
                    # check if higher points
                    if (lead[-1] == cards[idx][-1] and
                        cardPoints(cards[idx], trump) > cardPoints(cardtobeat, trump)):
                        cardtobeat = cards[idx]
        winningidx = cards.index(cardtobeat)
        teamPoints = [totalPoints, totalPoints]
        if cardtobeat == cards[0] or cardtobeat == cards[2]:
            teamPoints[1] = -1*totalPoints
        else:
            teamPoints[0] = -1*totalPoints
        self.print(f'Solving: {cards} {teamPoints} lead:{lead} trump:{trump} winner:{winningidx}'
                   , print_level=PrintLevel.EXTRA_INFO)
        return teamPoints, winningidx

    def print(self, msg, print_level: PrintLevel=PrintLevel.ERROR, newline=True):
        '''Utility print with different log levels'''
        if print_level <= self.print_level:
            if print_level == PrintLevel.ERROR:
                msg = 'ERROR: ' + msg
                self.errors += 1
            if print_level == PrintLevel.WARNING:
                msg = 'Warning: ' + msg
            if not newline:
                print(msg, end='')
            else:
                print(msg)

    def calculate(self, players, curr_turn, card_played, lead, trump, round, table, points, card_points, team):
        '''Run through all combinations with the players and their current hands'''
        if curr_turn < 0 or curr_turn >= len(players):
            self.print(f'Invalid index into player list! -> {curr_turn}',
                       print_level=PrintLevel.ERROR)
        curr_player = players[curr_turn]
        #print(f'P{curr_player.id} r:{round} t:{curr_turn} p:{card_played} {curr_player.handrounds}')
        # get valid cards to try
        valid_cards = self.get_valid_set(curr_player.handrounds[round], lead, trump,
                                         table.cards[round], curr_turn, card_played)
        for cardtoplay in valid_cards:
            if round + 1 < 8:
                curr_player.handrounds[round+1] = copy.copy(curr_player.handrounds[round])
                curr_player.handrounds[round+1].remove(cardtoplay)
            if card_played == 0:
                lead = cardtoplay
            table.cards[round][curr_player.id-1] = cardtoplay
            #print(table.cards)
            next_turn = curr_turn + 1 if curr_turn + 1 < 4 else 0
            next_played = card_played + 1
            nextround = copy.copy(round)
            if next_played > 3:
                nextround = round + 1
                next_played = 0
                teampoints, winningidx = self.solveSet(trump, lead, table.cards[round])
                self.addCheckSet(table.cards[round])
                points[round] = teampoints[team]
                if round >= 7:
                    card_points.append(sum(points))
                    continue
                else:
                    next_turn = winningidx
                    self.print(f'-Round {nextround}-', print_level=PrintLevel.EXTRA_INFO)
            self.calculate(players, next_turn, next_played, lead, trump, nextround, table, points, card_points, team)

    def get_hand_sizes(self, start_turn, start_played, start_round):
        '''Returns the correct hand sizes each player needs at this turn and round'''
        hand_sizes = [0,0,0,0]
        rounds = [0,0,0,0]
        for _ in range(3):
            start_turn = start_turn + 1 if start_turn + 1 < 4 else 0
            start_played += 1
            if start_played > 3:
                start_played = 0
                start_round += 1
            if start_round < 8:
                hand_sizes[start_turn] = 8 - start_round
                rounds[start_turn] = start_round
        return hand_sizes, rounds

    def get_all_hands(self, hand_sizes, deck_played):
        '''Returns a random unique hand per player'''
        if sum(hand_sizes) > len(self.fulldeck):
            print(f'Not enough cards in deck to distribute! {hand_sizes} {self.fulldeck}')
            return None
        deck = [c for c in self.fulldeck if c not in deck_played]
        for hand1 in itertools.combinations(deck, hand_sizes[0]):
            remaining1 = set(deck) - set(hand1)
            for hand2 in itertools.combinations(sorted(remaining1), hand_sizes[1]):
                remaining2 = remaining1 - set(hand2)
                for hand3 in itertools.combinations(sorted(remaining2), hand_sizes[2]):
                    remaining3 = remaining2 - set(hand3)
                    for hand4 in itertools.combinations(sorted(remaining3), hand_sizes[3]):
                        yield [hand1, hand2, hand3, hand4]
    
    def base_calculate(self, curr_player, card, newlead, newround, newplayers):
        '''Sets up the calculations and points per card dictionary'''
        card_points = [] # contains the points from the end of all calculations for this card
        points = [0 for _ in range(8)] # save all the points per round this card gets
        # if this is the first card played this round, make it lead
        if self.card_played == 0:
            newlead = copy.copy(card)
        # generate a new table
        newtable = Table()
        newtable.cards = copy.deepcopy(self.table.cards)
        # try the card picked
        newtable.cards[self.round][curr_player.id-1] = card
        team = (curr_player.id-1) % 2 # find out which team this player is on
        next_turn = self.curr_turn + 1 if self.curr_turn + 1 < 4 else 0
        next_card = self.card_played + 1
        # if this card played is the last of the round
        if next_card > 3:
            next_card = 0
            # solve the set since we are at the end of the round
            teampoints, winningidx = self.solveSet(self.trump, newlead, newtable.cards[self.round])
            self.addCheckSet(newtable.cards[self.round])
            # add points for this round into the list
            points[self.round] += teampoints[team]
            if self.round >= 7:
                # if this is the last round and the last player
                # no need to go through calculate()
                # just sum the points so far and iterate to the next card
                card_points.append(sum(points))
                return card_points
            # round is over, increment the round and start at the winning player
            next_turn = winningidx
            newround = self.round + 1
            self.print(f'=Round {newround}=', print_level=PrintLevel.EXTRA_INFO)
        if self.round + 1 < 8:
            # if there is a next round
            # add all cards except for the one we just played
            # into the next hand for that round
            newplayers[self.curr_turn].handrounds[self.round+1] = copy.copy(curr_player.handrounds[self.round])
            newplayers[self.curr_turn].handrounds[self.round+1].remove(card)
        #for p in newplayers:
        #    print(f'check P{p.id} {p.handrounds}')
        # run calculate
        self.calculate(newplayers, next_turn, next_card, newlead, self.trump, newround, newtable, points, card_points, team)
        return card_points

    def setup_calculate(self, curr_player, newlead, newround):
        '''Generates possible hands for calculations'''

        # check if player is valid
        if not curr_player.handrounds[self.round]:
            self.print(f'P{curr_player.id} has no cards {curr_player.handrounds}',
                       print_level=PrintLevel.ERROR)

        # each card has a list to dump points from possible futures in
        total_card_points = {card: [] for card in curr_player.handrounds[self.round]}

        # create the cards played deck with the current players hand
        deck_played = copy.copy(self.deck_played)
        deck_played.extend(curr_player.handrounds[self.round])

        #print(f'base P{curr_player.id} {curr_player.handrounds}')
        # create fake players to finish the game with
        newplayers = [Player(p.id-1) for p in self.players]

        # create possible hands for other players
        hand_sizes, rounds = self.get_hand_sizes(self.curr_turn, self.card_played, self.round)

        for hands in self.get_all_hands(hand_sizes,deck_played):
            # give each fake player their hand
            for ix,hand in enumerate(hands):
                newplayers[ix].handrounds[rounds[ix]] = list(hand)
            # filter out based on rules which cards are playable
            valid_cards = self.get_valid_set(curr_player.handrounds[self.round],
                                             newlead, self.trump, self.table.cards[self.round],
                                             self.curr_turn, self.card_played)
            # test all cards in current player's hand
            for card in valid_cards:
                card_points = self.base_calculate(curr_player, card, newlead, newround,
                                    newplayers)
                total_card_points[card].extend(card_points)
        return total_card_points

    def play_card(self, player: Player, cardtoplay: str, round: int, table: Table, deck_played):
        '''
        Plays a card onto the table and increments the players hand
        '''
        # copy previous hand to next round hand
        if round + 1 < 8:
            player.handrounds[round + 1] = copy.copy(player.handrounds[round])
            if not cardtoplay in player.handrounds[round + 1]:
                self.print(f'P{player.id} card played was not in hand! -> {cardtoplay} - ' \
                        f'{player.hand}\n{player.handrounds}', PrintLevel.ERROR)
            # remove card played from future rounds
            player.handrounds[round + 1].remove(cardtoplay)

        # play on table
        table.cards[round][player.id-1] = cardtoplay 
        deck_played.append(cardtoplay)
        self.print(f'R:{round} Playing: P{player.id}:{cardtoplay} Table:' \
                    f'{self.table.cards[self.round]}',
                   print_level=PrintLevel.INFO)

    def search_futures(self):
        '''Play a single turn'''

        # get the current player
        curr_player = self.players[self.curr_turn]

        # check amount of cards for this round
        if len(curr_player.handrounds[self.round]) > 8 - self.round:
            self.print(f'P:{curr_player.id} has more cards this round than expected',
                       print_level=PrintLevel.WARNING)
 
        self.print(f'-- start P{curr_player.id} --', print_level=PrintLevel.INFO)
        # run calculate and get back a dictionary of all points possible per card
        start = time.perf_counter()
        total_card_points = self.setup_calculate(curr_player, self.lead, self.round)
        end = time.perf_counter()
        self.print(f'Possible points: ', newline=False, print_level=PrintLevel.EXTRA_INFO) 
        futures = 0
        for idx,card in enumerate(curr_player.handrounds[self.round]):
            futures += len(total_card_points[card])
            self.print(f'{card}:{total_card_points[card]} ',
                       print_level=PrintLevel.EXTRA_INFO,
                       newline=False)
        self.print('', print_level=PrintLevel.EXTRA_INFO)
        self.print(f'Searched {futures} futures in {timedelta(seconds=end-start)}',
                   print_level=PrintLevel.INFO)

        # sum all possible points per card and average
        final_points = [sum(points)/len(points) for card,points in total_card_points.items()]
        return final_points

    def start(self):
        '''Starts the game'''
        self.print(f'Game Start', print_level=PrintLevel.INFO)
        self.print(f'  Starting turn: {self.curr_turn}', print_level=PrintLevel.INFO)
        self.print(f'  Starting cards played: {self.card_played}', print_level=PrintLevel.INFO)
        self.print(f'  Starting round: {self.round}', print_level=PrintLevel.INFO)
        self.print(f'  Starting trump: {self.trump}', print_level=PrintLevel.INFO)
        self.print(f'  Starting lead: {self.lead}', print_level=PrintLevel.INFO)
        self.print(f'  Starting table: {self.table.cards}', print_level=PrintLevel.INFO)
        self.print(f'  Starting players:', print_level=PrintLevel.INFO) 
        for p in self.players:
            self.print(f'    P{p.id} - {p.hand}', print_level=PrintLevel.INFO)
            self.print(f'    {p.handrounds}', print_level=PrintLevel.INFO)
        self.print(f'\n===Round {self.round}===', print_level=PrintLevel.INFO)

    def end(self):
        self.print(f'Game End: Team A [{self.team_points[0]}] Team B [{self.team_points[1]}]',
                   print_level=PrintLevel.INFO)
        if self.errors > 0:
            self.print(f'Errors that occured -> {self.errors}', print_level=PrintLevel.INFO)

    def play(self):
        '''Run through the entire game'''

        self.start()

        while self.round < 8:

            # play a turn
            final_points = self.search_futures()

            self.print(f'Final points: ', newline=False, print_level=PrintLevel.INFO)
            curr_player = self.players[self.curr_turn]
            for idx,card in enumerate(curr_player.handrounds[self.round]):
                self.print(f'{card}:{round(final_points[idx],3)} ', newline=False, print_level=PrintLevel.INFO)
            self.print('', print_level=PrintLevel.INFO)

            # choose the best card
            cardtoplay = curr_player.handrounds[self.round][final_points.index(max(final_points))]
            self.play_card(curr_player, cardtoplay, self.round, self.table, self.deck_played)
            self.print('-- end --', print_level=PrintLevel.INFO)

            # create lead if this is the first card in the round
            if self.card_played == 0:
                self.lead = cardtoplay

            # increment turn and cards played
            self.curr_turn = self.curr_turn + 1 if self.curr_turn + 1 < 4 else 0
            self.card_played += 1

            # if this is the last player in this round solve the set
            if self.card_played > 3:
                self.card_played = 0
                teampoints, winningidx = self.solveSet(self.trump, self.lead, self.table.cards[self.round])
                # add points to the corresponding team
                for ix,_ in enumerate(self.team_points):
                    self.team_points[ix] += teampoints[ix] if teampoints[ix] > -1 else 0

                # continue turn as the player who won
                self.curr_turn = winningidx
                self.round += 1
                if self.round < 8:
                    self.print(f'\n===Round {self.round}===', print_level=PrintLevel.INFO)
        self.end()

    def dealAllCards(self):
        if len(self.fulldeck) % len(self.players) != 0:
            self.print(f'Distrubuting cards will not be even!', print_level=PrintLevel.WARNING)
        for ix,card in enumerate(self.fulldeck):
            self.players[ix % len(self.players)].hand.append(card)

if __name__ == '__main__':
    # Example set up
    game = Game()
    game.print_level = PrintLevel.INFO
    game.round = 5
    game.trump = '♥'
    game.curr_turn = 3
    game.card_played = 3
    game.lead = 'J♦'
    game.fulldeck = ['J♦','A♣','K♦','K♣','Q♥','J♠','9♠','10♦','7♠','A♠','8♠','7♥']
    game.players[0].hand = ['J♦','A♣','K♦']
    game.players[1].hand = ['K♣','Q♥','J♠']
    game.players[2].hand = ['9♠','10♦','7♠']
    game.players[3].hand = ['A♠','8♠','7♥']
    for p in game.players:
        p.handrounds[game.round] = copy.copy(p.hand)
    game.play_card(game.players[0], 'J♦', game.round, game.table, game.deck_played)
    game.play_card(game.players[1], 'K♣', game.round, game.table, game.deck_played)
    game.play_card(game.players[2], '9♠', game.round, game.table, game.deck_played)
    game.players[3].handrounds[game.round] = copy.copy(game.players[3].hand)
    game.play()

    '''
    game = Game()
    game.print_level = PrintLevel.INFO
    game.round = 4
    game.trump = '♥'
    game.curr_turn = 0
    game.card_played = 0
    game.fulldeck = ['A♠','A♣','K♦','K♣','Q♠','Q♥','J♠','J♦',
                     '10♦','10♠','9♠','9♥','8♠','8♥','7♥','7♠']
    game.dealAllCards()
    for p in game.players:
        p.handrounds[game.round] = copy.copy(p.hand)
    game.play()
    '''
