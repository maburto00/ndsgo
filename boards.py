class KoError(Exception):
    pass


class SuicideError(Exception):
    pass


class NotEmptyError(Exception):
    pass


class Board:
    def __init__(self, n):
        self.n = n
        self.board_points = [(i, j) for j in range(n) for i in range(n)]
        # self.board = [[None for j in range(n)] for i in range(n)]
        self.board = [[None] * n] * n
        self.ko = None

    def copy(self):
        board = Board(self.n)
        board.board = [[self.board[i][j] for j in range(self.n)] for i in range(self.n)]
        board.ko = self.ko
        return board

    def play(self, x, y, color):
        # DONE: illegal move (NotEmptyError)
        # TODO: illegal move (suicide)
        # TODO: manage illega molve (simple ko)
        if self.board[x][y] is not None:
            raise NotEmptyError
        self.board[x][y] = color

    def get_available_pos(self):
        # TODO: manage the illegal moves (not empty)
        # TODO: manage the illegal moves (suicide)
        # TODO: manage the illegal moves (ko)
        """

        :return:
        """
        list_pos = []
        for i in range(self.n):
            for j in range(self.n):
                if self.board[i][j] is None and self.ko != (i, j):
                    list_pos.append((i, j))
        return list_pos

    def __str__(self):
        """
            'X' for black, 'O' for white and '.' for empty space
        """
        result = ''
        for i in range(self.n):
            for j in range(self.n):
                if self.board[i][j] is None:
                    result += '.'
                elif self.board[i][j] == 'b':
                    result += 'X'
                elif self.board[i][j] == 'w':
                    result += 'O'
            result += '\n'
        return result


# used to test
def main():
    print('Test for board class')
    board = Board(5)
    board.play(0, 1, 'b')
    print(board)


if __name__ == '__main__':
    main()
