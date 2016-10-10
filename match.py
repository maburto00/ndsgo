#from board import Board
from gomill.boards import Board
from player import HumanPlayer
from lookup_players import MCPlayerQ

class Match:
    def __init__(self, board, p1, p2,verbose=False):
        # TODO: p1 should be the player with black unless there is a handicap
        # TODO: implement handicap
        self.board = board
        self.p1 = p1
        self.p2 = p2
        self.verbose = verbose
        self.steps=0

    def update_boards(self, mov, color):
        print(mov)
        (x, y) = mov
        try:
            self.board.play(x, y, color)
            if (self.p1.color == color): # p1 already played the move
                self.p2.ko = self.p2.board.play(x, y, color)
            else:
                self.p1.ko = self.p1.board.play(x, y, color)
        except Exception:
            print('exception in update boards match')

    def play_match(self):
        """ alternate play bw black and white until both pass"""

        num_pass = 0
        i = -1
        self.steps=0
        players = [self.p1, self.p2]
        while num_pass < 2:
            i += 1
            self.steps += 1
            current_player = players[i % 2]
            color = current_player.color
            mov = current_player.genmove(color)

            if mov is not None:
                self.update_boards(mov, color)
                num_pass = 0
            else:
                num_pass += 1
            if(self.verbose):
                print('Move by {}: {}'.format('BLACK' if color == 'b' else 'WHITE', mov))
                print(self.board)
                print('')

        print('end of match')
        print('Score: {}'.format(self.board.area_score()))

    # def mc_selfplay_update(self):
    #     score=self.board.area_score()
    #     if(self.p1.color=='b'):
    #         self.p1.update_Q(int(score > 0))
    #         self.p2.update_Q(int(score < 0))
    #     else:
    #         self.p2.update_Q(int(score > 0))
    #         self.p1.update_Q(int(score < 0))


# def main():
#     """test for match"""
#     board = Board(4)
#     p1 = RandomPlayer(board.copy(), 'b')
#     p2 = HumanPlayer(board.copy(), 'w')
#     match = Match(board.copy(), p1, p2)
#     match.play_match()

def test_mcplayer_vs_humanplayer():
    """
    test against human player
    :return:
    """
    board=Board(2)
    p1 = MCPlayerQ(board.copy(), 'b',epsilon=0)
    p1.load_Q('Q_n2_N100.npy')
    p2 = HumanPlayer(board.copy(), 'w')
    match= Match(board.copy(),p1,p2,verbose=True)
    match.play_match()

def test_mcplayer_vs_humanplayer_3x3():
    """
    test against human player
    :return:
    """
    board=Board(3)
    p1 = HumanPlayer(board.copy(), 'b')
    p2 = MCPlayerQ(board.copy(), 'w',epsilon=0)
    p2.load_Q('Q_n3_N1000K.npy')
    match= Match(board.copy(),p1,p2,verbose=True)
    match.play_match()

def test_human_vs_human():
    board = Board(2)
    p1 = HumanPlayer(board.copy(), 'b')
    p2 = HumanPlayer(board.copy(), 'w')

def test_mc_vs_mc():
    board = Board(2)
    seed=4
    verbose=True
    p1 = MCPlayerQ(board.copy(), 'b', seed=seed, verbose=verbose)
    p2 = MCPlayerQ(board.copy(), 'w', seed=seed, verbose=verbose)

    p1.new_game(board.copy(), 'b')
    p2.new_game(board.copy(), 'w')

    match = Match(board.copy(), p1, p2, verbose=verbose)
    match.play_match()

    p1.new_game(board.copy(), 'b')
    p2.new_game(board.copy(), 'w')

    match = Match(board.copy(), p1, p2, verbose=verbose)
    match.play_match()

    pass

    #print("N")
    #print(match.p1.N)
    #print("Q")
    #print(match.p1.Q)
    #match.p1.update_Q(1)
    #print("after Q")
    #print(match.p1.Q)
    print ("steps:{}".format(match.steps))
    pass

    #board = Board(2)
    #p1 = MCPlayer(board.copy(), 'b')
    #p2 = MCPlayer(board.copy(), 'w')
    #match = Match(board.copy(), p1, p2)
    #match.play_match()



#def multiple_match():


if __name__ == '__main__':
    # test_mc_vs_mc()
    #test_mcplayer_vs_humanplayer()
    test_mcplayer_vs_humanplayer_3x3()
