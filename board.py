# """
# Author: Mario Aburto
# Description: clases and methods for board representation. The most important metho
#
# IMPORTANT NOTE: DON'T USE YET. WE ARE USING THE GOMILL IMPLEMENTATION FOR THE MOMENT.
#
# """
# TODO: test for scoring 2x2 board in these possitions (compare with glGo for example
# TODO: ..    X.    O.    O.
# TODO: ..    .X    .O    OO  etc...

#
# def UP(pos):
#     return (pos[0]+1,pos[1])
#
# def DOWN(pos):
#     return (pos[0]-1,pos[1])
#
# def LEFT(pos):
#     return (pos[0] + 1, pos[1])
#
# def RIGHT(pos):
#     return (pos[0] + 1, pos[1])
#
# def OTHER_COLOR(col):
#     pass
#
# class KoError(Exception):
#     pass
# class SuicideError(Exception):
#     pass
# class NotEmptyError(Exception):
#     pass
#
# class Board:
#     def __init__(self, n):
#         self.n = n
#         self.board_points = [(i, j) for j in range(n) for i in range(n)]
#         self.board = [[None for _ in range(n)] for _ in range(n)]
#         #self.board = [[None] * n] * n (this is wrong, don't use it)
#         self.ko = None
#
#     def copy(self):
#         board = Board(self.n)
#         board.board = [[self.board[i][j] for j in range(self.n)] for i in range(self.n)]
#         board.ko = self.ko
#         return board
#
#     def _surrounded_groups(self):
#         pass
#
#     def is_legal(self,row,col,color):
#         if self.board[row][col] is None:
#             return True
#         #TODO: implement ko
#         # if self.ko is not None:
#         #     if (self.ko==(row,col)):
#         #         return False
#         #if self.is_suicide(row,col)
#
#     # def get_group(self,pos):
#     #     """
#     #     return list of positions adjacent to pos
#     #     :param pos:
#     #     :return:
#     #     """
#     #     group=[]
#     #
#     #     to_explore=set()
#     #     to_explore.add(pos)
#     #     while True:
#     #         current_pos=to_explore.pop()
#     #         if current_pos not in group: #maybe this validation is unnecessary
#     #             group.append(pos)
#     #         #explore up,down,left and right:
#     #         if UP(pos) not in group:
#
#     # def get_liberties(self,pos):
#     #     (row,col)=pos
#     #     color=self.board[row][col]
#     #
#     # def is_suicide(self,row,col):
#     #     pos=(row,col)
#     #     if (UP(pos) is None or DOWN(pos) is None or
#     #         LEFT(pos) is None or RIGHT(pos) is None):
#     #         return False
#     #     else:
#     #         lib=self.get_liberties(UP(pos))
#
#     def get_groups(self):
#         #hacer búsqueda por profundidad
#         to_explore=set()
#         to_explore.add(point)
#         already_in_group=[]
#         groups=[] #list of Groups
#
#         for (row,col) in self.board_points:
#             if (row,col) in already_in_group:
#                 continue
#             #initiate group
#             group=[(row,col)]
#
#
#
#
#     def get_surrounded(self,x,y):
#         """
#         get surrounded groups
#         :param x:
#         :param y:
#         :return:
#         """
#         pos=(x,y)
#         check_points=[pos,UP(),DOWN(pos),LEFT(pos),RIGHT(pos)]
#         for p in check_points:
#             group=get_group(p)
#
#
#
#
#     def play(self, x, y, color):
#         # TODO: manage captures
#         # DONE: illegal move (NotEmptyError)
#         # TODO: illegal move (suicide)
#         # TODO: manage illega molve (simple ko)
#         if self.board[x][y] is not None:
#             raise NotEmptyError
#         self.board[x][y] = color
#         surrounded=self.get_surrounded(x,y)
#         if surrounded:
#             #if len(surrounded)==1: #only one group is surrounded
#             #   pass
#             #    if len(surrounded[0])==1: #the group has only one stone (it could be a ko)
#             #else:
#             for group in surrounded: #capture stones
#                 for pos in group:
#                     (row,col)=pos
#                     self.board[row][col]=None
#         else:
#             #undo move
#             self.board[x][y] = None
#             raise SuicideError
#
#
#
#         #if surrounded=[] then it is an illegal move
#
#     def reset(self):
#         self.board = [[None for _ in range(n)] for _ in range(n)]
#         self.ko = None
#
#     def get_available_pos(self):
#         # TODO: manage the illegal moves (not empty)
#         # TODO: manage the illegal moves (suicide)
#         # TODO: manage the illegal moves (ko)
#         """ return valid moves....
#         :return:
#         """
#         list_pos = []
#         for i in range(self.n):
#             for j in range(self.n):
#                 if self.board[i][j] is None and self.ko != (i, j):
#                     list_pos.append((i, j))
#         return list_pos
#
#
#     def __str__(self):
#         """
#             'X' for black, 'O' for white and '.' for empty space
#         """
#         result = ''
#         for i in range(self.n):
#             for j in range(self.n):
#                 if self.board[i][j] is None:
#                     result += '.'
#                 elif self.board[i][j] == 'b':
#                     result += 'X'
#                 elif self.board[i][j] == 'w':
#                     result += 'O'
#             result += '\n'
#         return result
#
# def test1():
#     print('Test 1----------')
#     board = Board(5)
#     board.play(1,2,'b')
#     board.play(2, 3, 'b')
#     board.play(3, 2, 'b')
#     board.play(2, 2, 'w')
#     print(board)
#
# # used to test
# def main():
#     print('Test for board class')
#     board = Board(5)
#     board.play(0, 1, 'b')
#     print(board)
#
#
# if __name__ == '__main__':
#     test1()
