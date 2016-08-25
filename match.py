from boards import Board
from player import RandomPlayer, HumanPlayer


class Match:
    def __init__(self, board, p1, p2):
        self.board = board
        self.p1 = p1
        self.p2 = p2

    def update_boards(self, mov, color):
        (x, y) = mov
        try:
            self.board.play(x, y, color)
            self.p1.board.play(x, y, color)
            self.p2.board.play(x, y, color)
        except Exception:
            print('exception in update boards match')

    def play_match(self):
        """ alternate play bw black and white until both pass"""
        num_pass = 0

        i = -1
        players = [self.p1, self.p2]
        while num_pass < 2:
            i += 1
            current_player = players[i % 2]
            mov = current_player.make_move()
            color = current_player.color
            if mov is not None:
                self.update_boards(mov, color)
                num_pass = 0
            else:
                num_pass += 1
            print('Move by {}: {}'.format('black' if color == 'b' else 'white', mov))
            print(self.board)
            print('')

        print('end of match')


def main():
    """test for match"""
    board = Board(4)
    p1 = RandomPlayer(board.copy(), 'b')
    p2 = HumanPlayer(board.copy(), 'w')
    match = Match(board.copy(), p1, p2)
    match.play_match()


if __name__ == '__main__':
    main()
