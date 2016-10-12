from utils import cd2xy, xy2cd
from utils import eprint


class GtpEngine:
    def __init__(self, player):
        self.player = player
        self.known_commands = ['protocol_version', 'name', 'version', 'known_command', 'list_commands', 'quit',
                               'boardsize',
                               'clear_board', 'komi', 'play', 'genmove']
        pass

    def gtp_session(self):
        while True:
            # read and respond
            # read command of the form:
            #   [id] command_name [arguments]\n
            line = raw_input().strip()
            if line == '':
                continue
            if line[0] == '#':
                continue
            line_list = line.split()
            # print(line)
            # print(line_list)
            try:
                int(line_list[0])
                id = line_list[0]
                cmd = line_list[1]
                args = line_list[2:]
            except ValueError:
                id = ''
                cmd = line_list[0]
                args = line_list[1:]
            eprint('line:{} command:{} args:{}'.format(line, cmd, args))

            # process command and return response of the form:
            #   =[id] result
            #   ?[id] error_message
            success = True
            result = ''
            if cmd == 'protocol_version':
                result = '2'
            elif cmd == 'name':
                result = 'ndsgo'
            elif cmd == 'version':
                result = ''
            # elif cmd == 'known_command':
            #     return gtpEn
            # elif cmd == 'list_commands':
            #     pass
            elif cmd == 'quit':
                break
            # elif cmd == 'boardsize':
            #     pass
            elif cmd == 'clear_board':
                self.player.clear_board()
            # elif cmd == 'komi':
            #     pass
            elif cmd == 'play':
                if len(args) < 2:
                    result = 'syntax error'
                    success = False
                else:
                    color = args[0].lower()
                    if color == 'black':
                        color = 'b'
                    if color == 'white':
                        color = 'w'
                    vertex = args[1]
                    try:
                        (x, y) = cd2xy(vertex,self.player.board.N)
                        # TODO: raise illegal move exception and handle it (success=False)
                        # TODO: implement as 'play' in gtp draft.
                        # TODO:   1) update board 2) update captured stones 3) add move to history
                        # TODO: all of this will be made in the board implementation
                        self.player.play(color, x, y)
                        result = ''
                    except(Exception):
                        # TODO: illegal move exception too.
                        success = False
                        result = 'syntax error'

            elif cmd == 'genmove':
                if len(args) < 1:
                    result = 'syntax error'
                    success = False
                else:
                    color = args[0].lower()
                    if color == 'black':
                        color = 'b'
                    if color == 'white':
                        color = 'w'

                    if color != 'b' and color != 'w':
                        success = False
                        result = 'syntax error'
                    else:
                        mov = self.player.genmove(color)
                        if mov is None:
                            result = 'pass'
                        else:
                            result = xy2cd(mov[0], mov[1],self.player.board.N)
            else:
                result = 'unknown command'
                success = False

            # Return response of the form
            #   =[id] result           (SUCCESS)
            #   ?[id] error_message    (FAILURE)
            print('{}{} {}\n'.format('=' if success else '?', id, result))


from lookup_players import MCPlayerQ
from gomill.boards import Board


def main():
    board = Board(3)
    player = MCPlayerQ(board, 'b', 0.2, None, True)
    player.load_Q('Q_n3_N1000K.npy')
    gtp = GtpEngine(player)
    gtp.gtp_session()


if __name__ == '__main__':
    main()
