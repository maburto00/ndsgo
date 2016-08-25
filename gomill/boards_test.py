from gomill.boards import Board
from gomill.ascii_boards import render_board

def main():
    board=Board(4)
    board.play(1, 0, 'b')
    board.play(1, 1, 'b')
    board.play(1, 2, 'b')
    board.play(1, 3, 'b')
    board.play(2, 0, 'w')
    board.play(2, 1, 'w')
    board.play(2, 2, 'w')
    board.play(2, 3, 'w')
    print(render_board(board))
    print(board.area_score())

    board=None
    board = Board(4)

    board = Board(4)
    board.play(0, 1, 'b')
    board.play(1, 1, 'b')
    board.play(1, 2, 'b')
    board.play(1, 3, 'b')
    board.play(2, 0, 'w')
    board.play(2, 1, 'w')
    board.play(2, 2, 'w')
    board.play(2, 3, 'w')

    print(render_board(board))
    print(board.area_score())

if __name__=='__main__':
    main()