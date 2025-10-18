import copy
import belote

def test1111():
    game = belote.Game()
    game.unit_testing = True
    game.print_level = belote.PrintLevel.ERROR
    game.trump = '♥'
    game.curr_turn = 0
    game.card_played = 0
    game.round = 7
    game.fulldeck = ['A♣','K♦','Q♥','J♠','10♦','9♣','8♠','7♥']
    game.deck_played = ['A♣','Q♥','10♦','8♠']
    game.players[0].hand = ['K♦']
    game.players[1].hand = ['J♠']
    game.players[2].hand = ['9♣']
    game.players[3].hand = ['7♥']
    for p in game.players:
        p.handrounds[game.round] = copy.copy(p.hand)
    final_points = game.search_futures()
    ans = [
        ['K♦','7♥','9♣','J♠'],
        ['K♦','7♥','J♠','9♣'],
        ['K♦','9♣','7♥','J♠'],
        ['K♦','9♣','J♠','7♥'],
        ['K♦','J♠','7♥','9♣'],
        ['K♦','J♠','9♣','7♥'],
    ]
    score = [-2]

    if game.check_sets != ans or final_points != score:
        print('\nGame Check Table:')
        print(game.check_sets)
        print(f'Final Points: {final_points}')
        return False
    return True

def test1112():
    game = belote.Game()
    game.unit_testing = True
    game.print_level = belote.PrintLevel.ERROR
    game.trump = '♥'
    game.lead = 'A♣'
    game.curr_turn = 3
    game.card_played = 3
    game.round = 6
    game.fulldeck = ['A♣','K♣','Q♥','J♠','10♦','9♣','8♠','7♥']
    game.deck_played = ['A♣','Q♥','10♦']
    game.table.cards[game.round] = ['A♣','Q♥','10♦','']
    game.players[0].hand = ['K♣']
    game.players[0].handrounds[7] = ['K♣']
    game.players[1].hand = ['J♠']
    game.players[1].handrounds[7] = ['J♠']
    game.players[2].hand = ['9♣']
    game.players[2].handrounds[7] = ['9♣']
    game.players[3].hand = ['8♠','7♥']
    game.players[3].handrounds[6] = ['8♠','7♥']
    final_points = game.search_futures()
    ans = [
        # p4
        ['A♣','Q♥','10♦','8♠'],
            ['K♣','9♣','J♠','7♥'],
        ['A♣','Q♥','10♦','7♥'],
            ['K♣','9♣','J♠','8♠'],
        ['A♣','Q♥','10♦','8♠'],
            ['K♣','J♠','9♣','7♥'],
        ['A♣','Q♥','10♦','7♥'],
            ['K♣','J♠','9♣','8♠'],
        ['A♣','Q♥','10♦','8♠'],
            ['J♠','9♣','K♣','7♥'],
        ['A♣','Q♥','10♦','7♥'],
            ['J♠','9♣','K♣','8♠'],
        ['A♣','Q♥','10♦','8♠'],
            ['J♠','K♣','9♣','7♥'],
        ['A♣','Q♥','10♦','7♥'],
            ['J♠','K♣','9♣','8♠'],
        ['A♣','Q♥','10♦','8♠'],
            ['9♣','J♠','K♣','7♥'],
        ['A♣','Q♥','10♦','7♥'],
            ['9♣','J♠','K♣','8♠'],
        ['A♣','Q♥','10♦','8♠'],
            ['9♣','K♣','J♠','7♥'],
        ['A♣','Q♥','10♦','7♥'],
            ['9♣','K♣','J♠','8♠'],
    ]
    score = [30, 26]

    if game.check_sets != ans or final_points != score:
        print('\nGame Check Table:')
        for s in game.check_sets:
            print(s)
        print(f'Final Points: {final_points}')
        return False
    return True


def generate_hands():
    game = belote.Game()
    game.unit_testing = False
    game.print_level = belote.PrintLevel.ERROR
    game.curr_turn = 2
    game.card_played = 2
    game.round = 6
    game.fulldeck = ['A♣','K♦','Q♥','J♠','10♦','9♣','8♥','7♠']
    game.players[game.curr_turn].handrounds[game.round] = ['10♦','9♣']
    game.deck_played.append('A♣')
    game.deck_played.append('Q♥')
    newplayers = [belote.Player(p.id-1) for p in game.players]
    newplayers[game.curr_turn].handrounds = copy.copy(game.players[game.curr_turn].handrounds)
    hand_sizes, rounds = game.get_hand_sizes(game.curr_turn, game.card_played, game.round)
    deck_played = copy.copy(game.deck_played)
    deck_played.extend(game.players[game.curr_turn].handrounds[game.round])
    for hands in game.get_all_hands(hand_sizes, deck_played):
        for ix,hand in enumerate(hands):
            newplayers[ix].handrounds[rounds[ix]] = list(hand)
        for p in newplayers:
            print(f'P{p.id} {p.handrounds}')
    return True

def test_valid_sets_must_follow_suit():
    game = belote.Game()
    card_played = 3
    turn = 3
    trump = '♥'
    lead = 'A♣'
    table = ['A♣','Q♥','10♦','']
    cards = ['10♦','9♣','8♥','7♠']
    valid = game.get_valid_set(cards, lead, trump, table, turn, card_played)
    ans = ['9♣']

    if ans != valid:
        print(f'Expected {ans} got {valid}')
        return False
    return True

def test_valid_sets_must_play_higher_trump():
    game = belote.Game()
    card_played = 3
    turn = 3
    trump = '♥'
    lead = '7♥'
    table = ['7♥','K♦','10♦','']
    cards = ['10♦','9♣','8♥','Q♥']
    valid = game.get_valid_set(cards, lead, trump, table, turn, card_played)
    ans = ['Q♥']

    if ans != valid:
        print(f'Expected {ans} got {valid}')
        return False
    return True

def test_valid_sets_partner_is_winning():
    game = belote.Game()
    card_played = 2
    turn = 0
    trump = '♥'
    lead = '10♦'
    table = ['','','10♦','K♦']
    cards = ['7♣','J♣','8♣','Q♥']
    valid = game.get_valid_set(cards, lead, trump, table, turn, card_played)
    ans = cards

    if ans != valid:
        print(f'Expected {ans} got {valid}')
        return False
    return True

def test_valid_sets_need_to_cut():
    game = belote.Game()
    card_played = 3
    turn = 2
    trump = '♥'
    lead = 'K♦'
    table = ['9♣','10♦','','K♦']
    cards = ['J♣','7♣','8♣','Q♥']
    valid = game.get_valid_set(cards, lead, trump, table, turn, card_played)
    ans = ['Q♥']

    if ans != valid:
        print(f'Expected {ans} got {valid}')
        return False
    return True

def run(func):
    print(f'{"Pass" if func() else "Fail"} - {func.__name__}')

if __name__ == '__main__':
    run(test1111)
    run(test1112)
    #run(generate_hands, True)
    run(test_valid_sets_must_follow_suit)
    run(test_valid_sets_must_play_higher_trump)
    run(test_valid_sets_partner_is_winning)
    run(test_valid_sets_need_to_cut)

