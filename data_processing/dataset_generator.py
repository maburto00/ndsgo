# PARAMETERS: path to the folder containing the sgf files
# GENERATE: a file containing the shuffled dataset
#           a file containing some meta-data (boardsize, numberofplanes,numberofregisters)
from board import Board
import os
import utils
from utils import Color, sgfxy2p, color2c, eprint
import numpy as np
import random
import struct
import gzip

DEFAULT_SIZE = 9


def get_property_value(property, sgf_properties, start_index=0):
    property_pos = sgf_properties.find(property)
    s = sgf_properties.find('[', property_pos)
    f = sgf_properties.find(']', property_pos)
    return sgf_properties[s + 1:f]


def get_property_multiple_values(property, sgf_properties, start_index=0):
    property_pos = sgf_properties.find(property)
    values = []
    s = sgf_properties.find('[', property_pos)
    f = sgf_properties.find(']', property_pos)
    while s != -1:
        values.append(sgf_properties[s + 1:f])
        s = sgf_properties.find('[', s + 1)
        f = sgf_properties.find(']', f + 1)
        # this happens if we already are in another property
        if sgf_properties[s - 1] != ']':
            break
    return values


def process_game(fullpath_fn):
    f = open(fullpath_fn)
    sgf_data = f.read()
    f.close()

    # remove all white space
    sgf_data.replace(' ', '')

    split_data = sgf_data.split(';')
    print(split_data)

    sgf_properties = split_data[1]
    sgf_moves = split_data[2:]

    # GET SIZE
    if 'SZ' in sgf_properties:
        try:
            size = int(get_property_value('SZ', sgf_properties))
        except:
            print('error converting size property to int')
    else:
        size = DEFAULT_SIZE

    #print('SIZE:{}'.format(size))
    # initialize board
    board = Board(size)

    # Manage handicap
    if 'HA' in sgf_properties:
        #print('there is handicap in this file: {}'.format(fullpath_fn))
        try:
            handicap = int(get_property_value('HA', sgf_properties))
        except:
            print('error while converting handicap to int')
            handicap = 0
        if handicap > 0:
            ab_values = get_property_multiple_values('AB', sgf_properties)
            #print('ab_values')
            #print(ab_values)
            for xy in ab_values:
                # add handicap black stones
                try:
                    p = sgfxy2p(xy, size)
                    board.add_black_handicap_stone(p)
                except:
                    print('except while putting handicap stones')
                    print('xy:{} ab_values:{} fn:{}'.format(xy,ab_values,fullpath_fn))
                # index_ab = sgf_data.find('AB', index_ab + 1)
                # print(board)

    # Play move by move
    i = 0

    # registers for this game
    game_registers = bytearray([])
    num_reg = 0
    for move in sgf_moves:
        # get colors and positions
        print(move)
        try:
            color = move[0].lower()
            c = color2c(color)
            xy = move[move.find('[') + 1:move.find(']')]
            if xy == '':
                print('PASS MOVE. filename:{}'.format(fullpath_fn))
                continue
            p = sgfxy2p(xy, size)

            # first, store current position and predicted move as a register
            reg = board.create_register(c, p)
            print('len of reg:{}'.format(len(reg)))

            # write to file or append to something and then write
            game_registers += reg
            num_reg += 1
            # then, play next position
            board.play(c, p)
            # print(board)
        except:
            print('except while playing')
            print('move:{} fn:{}'.format(move,fullpath_fn))


    return num_reg, game_registers


def generate_dataset(dirname):
    # iterate over the files in directory
    print(dirname)

    # we will store the dataset in this file
    f = open(dirname + '.bin', 'wb')

    total_num_reg = 0

    files=os.listdir(dirname)
    total_files=len(files)

    i = 0
    for fn in files:
        i += 1
        (num_reg, reg) = process_game(dirname + '/' + fn)
        f.write(reg)
        total_num_reg += num_reg

        print('{}/{} processed'.format(i,total_files))

        # print(data)
    f.close()

    g = open(dirname + '.prop', 'w')
    g.write('{} registers\n'.format(total_num_reg))
    g.close()
    return total_num_reg


def generate_idx_dataset9(dirname):
    generate_idx_dataset(dirname,9,4)

def generate_idx_dataset19(dirname):
    generate_idx_dataset(dirname,19,4)

def generate_idx_dataset(dirname,board_size,num_channels):
    # iterate over the files in directory
    print(dirname)

    VECTOR_SIZE = board_size*board_size*num_channels
    LABEL_SIZE = 2
    EXAMPLE_SIZE = VECTOR_SIZE + LABEL_SIZE

    # we will store the dataset in this file
    # f=open(dirname+'.bin','wb')


    num_examples = generate_dataset(dirname)

    # shuffle and get num_exmaples
    shuffle_dataset(dirname + '.bin')

    index = int(num_examples * .85)
    num_train_examples = index
    num_test_examples = num_examples - index

    # generate heading of idx file

    # SEE README for idx format
    # 8 is for ubyte and 11 for short(2bytes), 4 and 1 are the number of dimensions
    magic_number_vectors = bytearray([0, 0, 8, 4])
    magic_number_labels = bytearray([0, 0, 11, 1])

    header_train_vectors = magic_number_vectors + struct.pack('>I', num_train_examples) \
                           + struct.pack('>I', num_channels) \
                           + struct.pack('>I', board_size) \
                           + struct.pack('>I', board_size)

    header_test_vectors = magic_number_vectors + struct.pack('>I', num_test_examples) \
                          + struct.pack('>I', num_channels) \
                          + struct.pack('>I', board_size) \
                          + struct.pack('>I', board_size)

    header_train_labels = magic_number_labels + struct.pack('>I', num_train_examples)
    header_test_labels = magic_number_labels + struct.pack('>I', num_test_examples)

    train_vectors = gzip.open(dirname + '-train-vectors-idx4-ubyte.gz', 'wb')
    train_labels = gzip.open(dirname + '-train-labels-idx1-ubyte.gz', 'wb')
    test_vectors = gzip.open(dirname + '-test-vectors-idx4-ubyte.gz', 'wb')
    test_labels = gzip.open(dirname + '-test-labels-idx1-ubyte.gz', 'wb')

    train_vectors.write(str(header_train_vectors))
    train_labels.write(str(header_train_labels))
    test_vectors.write(str(header_test_vectors))
    test_labels.write(str(header_test_labels))

    # write data
    i = 0
    for line in records_from_file('shuffled_' + dirname + '.bin'):
        if i < index:
            train_labels.write(line[0:2])
            train_vectors.write(line[2:])
        else:
            test_labels.write(line[0:2])
            test_vectors.write(line[2:])
        i += 1

    train_vectors.close()
    test_vectors.close()
    train_labels.close()
    test_labels.close()


def find_games_with_property(dirname, property):
    for fn in os.listdir(dirname):
        f = open(dirname + '/' + fn, 'r')
        sgf_data = f.read()
        f.close()
        if property in sgf_data:
            print(fn)


def records_from_file(filename, chunksize=81 * 4 + 2):
    with open(filename, "rb") as f:
        while True:
            chunk = f.read(chunksize)
            if chunk:
                yield chunk
            else:
                break


def shuffle_dataset(filename):
    """
    shuffles the examples inside the file
    also, returns the number of examples in the file
    in order to use it in generate_idx_dataset()"""

    # f=open(filename,'r')
    lines = []
    for line in records_from_file(filename):
        # print(line)
        lines.append(line)

    # shuffle to get a uniform random order in linear time
    N = len(lines)
    for i in range(N):
        r = random.randint(0, N - i - 1)
        temp = lines[i]
        lines[i] = lines[r]
        lines[r] = temp
    f = open('shuffled_' + filename, 'wb')
    for line in lines:
        f.write(line)
    f.close()

    return len(lines)


# def separate_dataset_train_test(fn):





if __name__ == '__main__':
    # dirname = '9x9_10games'
    # fn=''
    # dirname = 'gogod_9x9_games'
    # dirname = 'KGS2001'
    # find_handicap_games(dirname)
    # process_game('2001-12-08-3.sgf')
    # generate_dataset('9x9_10games')

    # shuffle_dataset('9x9_10games.bin')
    # generate_idx_dataset_9x9('9x9_10games')

    #generate_idx_dataset9('gogod_9x9_games')
    generate_idx_dataset9('9x9_10games')
    #generate_idx_dataset19('KGS2001')

# separate_dataset_train_test('9x9_10games.bin')




# generate_dataset('KGS2001')

# find_games_with_property('KGS2001', 'AB')
# print(get_property_value('HA','FF[00]HA[22]BA[33]'))
# print(get_property_multiple_values('AB', 'FF[00]HA[22]AB[cc][dd][ee]'))

# generate_dataset(dirname)
