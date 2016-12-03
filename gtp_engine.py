import sys

from board import Board
from lookup_players import MCPlayerQ
from utils import p2cd, eprint, Color, c_cd2cp, color2c
from param_players import CNNPlayer


class GtpEngine:
    def __init__(self, N,Player_class, verbose=False):
        self.Player_class=Player_class
        self.player = self.Player_class(N)
        self.verbose = verbose
        self.last_move_pass = False #Used to finish the game when the other player passes

        # commented commands are not implemented yet
        self.administrative_commands = ['protocol_version', 'name', 'version', 'known_command', 'list_commands', 'quit']
        self.setup_commands = ['boardsize', 'clear_board', 'komi',
                               # 'fixed_handicap', place_free_handicap, set_free_handicap
                               ]
        self.core_play_commands = ['play', 'genmove',
                                   'undo',
                                   ]
        self.tournament_commands = [  # 'time_settings', 'time_left',
            #'final_score',
            # 'final_status_list'
        ]
        self.reggression_commands = [  # 'load_sgf', 'reg_genmove'
        ]
        self.debug_commands = ['showboard']

        self.known_commands = self.administrative_commands + self.setup_commands + self.core_play_commands \
                              + self.tournament_commands + self.reggression_commands + self.debug_commands

    def gtp_session(self):
        quit = False
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

            elif cmd == 'known_command':
                if len(args) < 1:
                    result = 'syntax error'
                    success = False
                else:
                    command = args[0]
                    if command in self.known_commands:
                        result = 'true'
                    else:
                        result = 'false'

            elif cmd == 'list_commands':
                result = ''
                for e in self.known_commands:
                    result += e + "\n"
                result = result[:-1]  # remove the last \n

            elif cmd == 'quit':
                result = ''
                quit = True

            elif cmd == 'boardsize':
                # TODO: test this code
                if len(args) < 1:
                    result = 'syntax error'
                    success = False
                else:
                    try:
                        size = int(args[0])

                        if self.player.player_file.has_key(size):
                            if self.Player_class is CNNPlayer:
                                #success = False
                                #result = 'unacceptable size'
                                #eprint('Cannot change size because this is not implmeneted for CNNPlayer. '
                                #       'It would cause an error')
                                success=True

                            elif self.Player_class is MCPlayerQ:
                                self.player = self.Player_class(size)
                                self.player.load_Q(self.player.player_file[size])
                        else:
                            success = False
                            result = 'unacceptable size'
                    except Exception as err:
                        if self.verbose:
                            eprint('Exception in gtp_engine.boardsize. Error:{}'.format(err))
                        success = False
                        result = 'syntax error'

            elif cmd == 'clear_board':
                # board.clear_board() function is called inside player.new_game()
                # we call new_game() since if we are learning we need to reset the episode_history for the game
                self.player.new_game()

            elif cmd == 'komi':
                if len(args) < 1:
                    result = 'syntax error'
                    success = False
                else:
                    try:
                        new_komi = float(args[0])
                        self.player.board.komi = new_komi
                    except Exception as err:
                        if self.verbose:
                            eprint('Exception in gtp_engine.komi. Error:{}'.format(err))
                        success = False
                        result = 'syntax error'

            elif cmd == 'play':
                # e.g. play black A1

                if len(args) < 2:
                    result = 'syntax error'
                    success = False
                else:
                    eprint('IN PLAY: {} {}'.format(args[0], args[1]))
                    if args[1] == 'PASS':
                        eprint('in play. Move is PASS.')
                        self.last_move_pass=True
                        success = True
                    else:
                        try:
                            (c, p) = c_cd2cp(args[0] + ' ' + args[1], self.player.board.N)
                            res = self.player.board.play(c, p)
                            if self.verbose:
                                eprint("args:{} c:{} p:{} res:{}".format(args, c, p, res))
                            if res < 0:
                                if self.verbose:
                                    eprint("Illegal move in gtp_engine. play. res:{}".format(res))
                                success = False
                                result = 'illegal move'
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
                    #FIRST VERIFY IF THE OTHER PLAYER HAS NOT PASSED
                    if self.last_move_pass==True:
                        eprint('Since the other program passed we also pass.')
                        eprint('This is trusting the other program knows better when the game has finished.')
                        self.last_move_pass=False
                        result='pass'
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
                            c = color2c(color)
                            mov = self.player.genmove(c)
                            if mov is None:
                                result = 'pass'
                            else:
                                result = p2cd(mov, self.player.board.N)

            elif cmd == 'undo':
                if len(self.player.board.move_history) == 0:
                    success = False
                    result = 'cannot undo'
                else:
                    self.player.board.undo()

            # elif cmd == 'final_score':
            #     score = self.player.board.final_score()
            #     if score > 0:
            #         result = "B+{}".format(score)
            #     elif score < 0:
            #         result = "W+{}".format(abs(score))
            #     else:
            #         result = '0'

            elif cmd == 'showboard':
                result = self.player.board.__str__()

            else:
                result = 'unknown command'
                success = False

            # Return response of the form
            #   =[id] result           (SUCCESS)
            #   ?[id] error_message    (FAILURE)
            print('{}{} {}\n'.format('=' if success else '?', id, result))
            sys.stdout.flush()


def main():
    #player = MCPlayerQ(3)
    #player.load_Q(player_file[3])
    #player=CNNPlayer(9)

    gtp = GtpEngine(9, CNNPlayer, verbose=True)
    #gtp = GtpEngine(3, MCPlayerQ, verbose=True)
    gtp.gtp_session()


if __name__ == '__main__':
    main()
