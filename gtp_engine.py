import re

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
            if line[0]=='#':
                continue
            line_list=line.split()
            #print(line)
            #print(line_list)
            try:
                int(line_list[0])
                id = line_list[0]
                cmd = line_list[1]
                args = line_list[2:]
            except ValueError:
                id = ''
                cmd = line_list[0]
                args = line_list[1:]

            # process command and return response of the form:
            #   =[id] result
            #   ?[id] error_message
            success = True
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
            # elif cmd == 'clear_board':
            #     response = ''
            # elif cmd == 'komi':
            #     pass
            # elif cmd == 'play':
            #     pass
            # elif cmd == 'genmove':
            #     pass
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
    player = MCPlayerQ(board, 'b', 0.2, None, False)
    player.load_Q('Q_n3_N1000K.npy')
    gtp = GtpEngine(player)
    gtp.gtp_session()


if __name__ == '__main__':
    main()
