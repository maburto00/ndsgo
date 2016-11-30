# PARAMETERS: path to the folder containing the sgf files
# GENERATE: a file containing the shuffled dataset
#           a file containing some meta-data (boardsize, numberofplanes,numberofregisters)
from board import Board, NUM_CHANNELS
import os
import utils
from utils import Color, sgfxy2p, color2c, eprint
import numpy as np
import random
import struct
import gzip
import time

DEFAULT_SIZE = 9
LABEL_SIZE=2


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

def process_game(fullpath_fn, boardsize):

    with open(fullpath_fn) as f:
        sgf_data = f.read()

    # remove all white space
    sgf_data.replace(' ', '')

    split_data = sgf_data.split(';')
    #print(split_data)

    sgf_properties = split_data[1]
    sgf_moves = split_data[2:]

    # GET SIZE
    if 'SZ' in sgf_properties:
        try:
            sgf_size = int(get_property_value('SZ', sgf_properties))
            if sgf_size != boardsize:
                print('sizes differ in {}. sgf_size:{} dataset_boardsize:{}'.format(fullpath_fn, sgf_size, boardsize))
                return 0,''

        except:
            print('error converting size property to int. file:{}'.format(fullpath_fn))
            return 0,''

    size = boardsize

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
                    exit()
                # index_ab = sgf_data.find('AB', index_ab + 1)
                # print(board)

    # Play move by move
    i = 0

    # registers for this game
    game_registers = bytearray([])
    num_reg = 0
    for move in sgf_moves:
        # get colors and positions
        #print(move)
        try:
            color = move[0].lower()
            c = color2c(color)
            xy = move[move.find('[') + 1:move.find(']')]
            if xy == '':
                print('PASS MOVE. move:{} filename:{}'.format(move,fullpath_fn))
                continue
            p = sgfxy2p(xy, size)

            # first, store current position and predicted move as a register
            reg = board.create_register(c, p)
            #print('len of reg:{}'.format(len(reg)))

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


def generate_bin_dataset(dirname,boardsize):
    f = open(dirname + '.bin', 'wb')

    total_num_reg = 0

    files=os.listdir(dirname)
    total_files=len(files)

    i = 0
    for fn in files:
        i += 1
        (num_reg, reg) = process_game(dirname + '/' + fn,boardsize)
        f.write(reg)
        total_num_reg += num_reg
        print('{}/{} games processed. BIN FILE.'.format(i,total_files))

    f.close()


    return total_num_reg


def generate_idx_dataset9(dirname):
    generate_idx_dataset(dirname,9)

def generate_idx_dataset19(dirname):
    generate_idx_dataset(dirname,19)

def generate_idx_dataset(dirname,boardsize):
    # iterate over the files in directory
    print(dirname)

    VECTOR_SIZE = boardsize*boardsize*NUM_CHANNELS

    EXAMPLE_SIZE = VECTOR_SIZE + LABEL_SIZE

    # we will store the dataset in this file
    # f=open(dirname+'.bin','wb')

    total_time=0
    start_time = time.time()

    num_examples = generate_bin_dataset(dirname,boardsize)
    elapsed_time=time.time()-start_time
    start_time=time.time()
    total_time+=elapsed_time
    print('bin file created. Time to create {} s'.format(elapsed_time))

    # shuffle and get num_exmaples
    shuffle_dataset(dirname ,boardsize)
    elapsed_time = time.time() - start_time
    start_time = time.time()
    total_time += elapsed_time
    print('shuffled bin file created. Time to create {} s'.format(elapsed_time))

    # 5 separate bin files
    num_examples_each_file=separate_dataset(dirname,boardsize,num_examples,5)

    #generate prop file
    g = open(dirname + '.prop', 'w')
    for i in range(len(num_examples_each_file)):
        if i==len(num_examples_each_file)-1:
            g.write(str(num_examples_each_file[i]) +'\n')
        else:
            g.write(str(num_examples_each_file[i]) +',')

    g.write('{}\n'.format(NUM_CHANNELS))
    g.write('{}\n'.format(boardsize))
    g.write('{}\n'.format(boardsize))
    g.close()



    index = int(num_examples * .85)
    num_train_examples = index
    num_test_examples = num_examples - index

    # generate heading of idx file

    # SEE README for idx format
    # 8 is for ubyte and 11 for short(2bytes), 4 and 1 are the number of dimensions
    magic_number_vectors = bytearray([0, 0, 8, 4])
    magic_number_labels = bytearray([0, 0, 11, 1])

    header_train_vectors = magic_number_vectors + struct.pack('>I', num_train_examples) \
                           + struct.pack('>I', NUM_CHANNELS) \
                           + struct.pack('>I', boardsize) \
                           + struct.pack('>I', boardsize)

    header_test_vectors = magic_number_vectors + struct.pack('>I', num_test_examples) \
                          + struct.pack('>I', NUM_CHANNELS) \
                          + struct.pack('>I', boardsize) \
                          + struct.pack('>I', boardsize)

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
    print_interval=int(num_examples/100)
    for line in records_from_file('shuffled_' + dirname + '.bin',boardsize):
        if i < index:
            train_labels.write(line[0:LABEL_SIZE])
            train_vectors.write(line[LABEL_SIZE:])
        else:
            test_labels.write(line[0:LABEL_SIZE])
            test_vectors.write(line[LABEL_SIZE:])
        i += 1
        if (i-1) % print_interval==0 or i==num_examples:
            print('{}/{} lines processed. GZ FILE'.format(i,num_examples))


    train_vectors.close()
    test_vectors.close()
    train_labels.close()
    test_labels.close()
    elapsed_time = time.time() - start_time
    total_time += elapsed_time
    print('gz file created. Time to create {} s'.format(elapsed_time))
    print('Total time {} s'.format(total_time))


def find_games_with_property(dirname, property):
    for fn in os.listdir(dirname):
        f = open(dirname + '/' + fn, 'r')
        sgf_data = f.read()
        f.close()
        if property in sgf_data:
            print(fn)


def records_from_file(filename, boardsize):
    chunksize=boardsize*boardsize*NUM_CHANNELS+LABEL_SIZE
    with open(filename, "rb") as f:
        while True:
            chunk = f.read(chunksize)
            if chunk:
                yield chunk
            else:
                break

def separate_dataset(dirname,boardsize,num_examples, num_sep):

    #we sum +1 since there will be a test set also
    interval_sep = num_examples / (num_sep+1) + 1

    chunksize = boardsize * boardsize * NUM_CHANNELS + LABEL_SIZE
    f=open('shuffled_'+dirname+'.bin','rb')
    filenames=[dirname+'_{}.bin'.format(i+1) for i in range(num_sep)]
    filenames.append(dirname+'_test_batch.bin')
    num_examples_each_file=[0 for _ in range(num_sep+1)]
    for i in range(num_sep+1):

        with open(filenames[i],'wb') as g:
            for j in range(interval_sep):
                chunk=f.read(chunksize)
                if chunk:
                    g.write(chunk)
                    num_examples_each_file[i] += 1
                else:
                    break

    return num_examples_each_file
def shuffle_dataset(dirname,boardsize):
    """
    shuffles the examples inside the file
    also, returns the number of examples in the file
    in order to use it in generate_idx_dataset()"""
    # TODO: do efficient memory shuffling, we don't need to read everything to memory
    # f=open(filename,'r')
    lines = []
    for line in records_from_file(dirname+'.bin',boardsize):
        # print(line)
        lines.append(line)

    # shuffle to get a uniform random order in linear time
    N = len(lines)
    for i in range(N):
        r = random.randint(0, N - i - 1)
        temp = lines[i]
        lines[i] = lines[r]
        lines[r] = temp
    f = open('shuffled_' + dirname +'.bin', 'wb')


    for line in lines:
        f.write(line)
    f.close()

    return len(lines)

if __name__ == '__main__':
    # find_handicap_games(dirname)
    # process_game('2001-12-08-3.sgf')
    # generate_dataset('9x9_10games')

    # shuffle_dataset('9x9_10games.bin')
    # generate_idx_dataset_9x9('9x9_10games')

    #generate_idx_dataset9('gogod_9x9_games')
    #generate_idx_dataset9('9x9_10games')
    #generate_idx_dataset19('KGS2001')
    generate_idx_dataset19('KGS_10games')
    #generate_idx_dataset19('KGS_100games')
