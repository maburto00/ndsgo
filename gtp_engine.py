from utils import p2cd,eprint,Color,c_cd2cp,color2c
from lookup_players import MCPlayerQ
from board import Board
import sys

player_file=['0','1',
        '/home/mario/Dropbox/PycharmProjects/ndsgo/saved_param/MC_Q_N2_G1000000_seed2.npy',
        '/home/mario/Dropbox/PycharmProjects/ndsgo/saved_param/MC_Q_N3_G1000000_seed2.npy',
        '4','5','6','7','8','9','10','11','12','13','14','15','16','17','18','19']

class GtpEngine:
    def __init__(self, player,verbose=False):
        self.player = player
        self.known_commands = ['protocol_version', 'name', 'version', 'known_command', 'list_commands', 'quit',
                               #'boardsize',
                               'clear_board',
                               #'komi',
                               'play', 'genmove']
        self.verbose = verbose

    def gtp_session(self):
        quit=False
        while not quit:
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
            if self.verbose:
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
            elif cmd == 'list_commands':
                result=''
                for e in self.known_commands:
                    result += e + "\n"

            elif cmd == 'quit':
                result=''
                quit = True
            elif cmd == 'boardsize':
                if len(args) < 1:
                    result = 'syntax error'
                    success = False
                size = int(args[0])
                board = Board(size)
                self.player = MCPlayerQ(board, self.player.color, self.player.epsilon, self.player.verbose)
                self.player.load_Q(player_file[size])
            elif cmd == 'clear_board':
                self.player.clear_board()
            # elif cmd == 'komi':
            #     pass
            elif cmd == 'play':
                # e.g. play black A1
                if len(args) < 2:
                    result = 'syntax error'
                    success = False
                else:
                    try:
                        #eprint("args:{} a0+a1:{}".format(args,args[0]+' '+args[1]))
                        (c, p) = c_cd2cp(args[0] + ' ' + args[1], self.player.board.N)
                        # TODO: implement as 'play' in gtp draft.
                        # TODO:   1) update board 2) update captured stones 3) add move to history
                        # TODO: all of this will be made in the board implementation
                        res = self.player.board.play(c, p)
                        if self.verbose:
                            eprint("args:{} c:{} p:{} res:{}".format(args,c,p,res))
                        if res < 0:
                            if self.verbose:
                                eprint("Illegal move in gtp_engine. play. res:{}".format(res))
                            result = 'illegal move'
                            success=False
                        else:
                            result = ''
                    except Exception as err:
                        if self.verbose:
                            eprint('Exception in gtp_engine.play(). Error:{}'.format(err))
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
                        c=color2c(color)
                        mov = self.player.genmove(c)
                        if mov is None:
                            result = 'pass'
                        else:
                            result = p2cd(mov, self.player.board.N)
            else:
                result = 'unknown command'
                success = False

            # Return response of the form
            #   =[id] result           (SUCCESS)
            #   ?[id] error_message    (FAILURE)
            print('{}{} {}\n'.format('=' if success else '?', id, result))
            sys.stdout.flush()



def main():
    board = Board(3)
    player = MCPlayerQ(board, Color.WHITE, epsilon=0,verbose=True)
    player.load_Q('/home/mario/Dropbox/PycharmProjects/ndsgo/MC_Q_N3_G1000000_seed2.npy')
    gtp = GtpEngine(player)
    gtp.gtp_session()


if __name__ == '__main__':
    main()
