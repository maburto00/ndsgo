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
import time

LABEL_SIZE=2
NUM_PRINTS=100
SKIP_FILE_GENERATION=False
PAUSE_BEFORE_SHUFFLING=True


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

def process_game(fullpath_fn, boardsize,num_channels,aug_data=False):

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
            if xy == '' or xy=='tt':
                eprint('PASS MOVE. move:{} filename:{}'.format(move,fullpath_fn))
                continue
            p = sgfxy2p(xy, size)

            # first, store current position and predicted move as a register

            reg = board.create_board_move_register(c, p,num_channels)
            game_registers += reg
            num_reg += 1

            #utils.a2p()

                #generate all 8-fold rotations and reflections

            #print('len of reg:{}'.format(len(reg)))

            # write to file or append to something and then write

            # then, play next position
            board.play(c, p)
            # print(board)
        except:
            eprint('except while playing')
            eprint('move:{} pos:{} fn:{}'.format(move,utils.p2cd(p,boardsize),fullpath_fn))
            eprint(board)


    return num_reg, game_registers


def generate_bin_dataset(dirname,boardsize,num_channels,aug_data):
    f = open(os.path.join(dirname + '.bin'), 'wb')

    total_num_reg = 0

    files=os.listdir(dirname)
    total_files=len(files)

    i = 0
    for fn in files:
        i += 1
        (num_reg, reg) = process_game(dirname + '/' + fn,
                                      boardsize=boardsize,
                                      num_channels=num_channels,
                                      aug_data=aug_data)
        f.write(reg)
        total_num_reg += num_reg
        print('{}/{} games processed. BIN FILE fn:{}.'.format(i,total_files,fn))

    f.close()

    return total_num_reg

def create_prop_file(dirname,num_examples_each_file,num_channels,boardsize):
    g = open(dirname + '.prop', 'w')
    for i in range(len(num_examples_each_file)):
        if i == len(num_examples_each_file) - 1:
            g.write(str(num_examples_each_file[i]) + '\n')
        else:
            g.write(str(num_examples_each_file[i]) + ',')

    g.write('{}\n'.format(num_channels))
    g.write('{}\n'.format(boardsize))
    g.write('{}\n'.format(boardsize))
    g.close()

def separate_into_train_test(dirname,boardsize,num_channels,num_examples):
    #The first ~10% of the bin file will be the test set
    #define the exact number in order to have all the train files of the

    interval_sep=int(0.1*num_examples)
    size_train= ((num_examples-interval_sep)/5)*5
    interval_sep=num_examples-size_train



    f = open(dirname + '.bin', 'rb')
    chunksize = boardsize * boardsize * num_channels + LABEL_SIZE
    num_examples_train=0
    num_examples_test = 0
    i=0
    with open(dirname+'_test'+'.bin','wb') as g:
        for j in range(interval_sep):
            chunk = f.read(chunksize)
            if chunk:
                g.write(chunk)
                num_examples_test+=1
            i += 1
            if (i - 1) % PRINT_INTERVAL== 0 or i == num_examples:
                print('{}/{} lines processed. SEPARATE TRAIN TEST FILE'.format(i, num_examples))

    with open(dirname+'_train'+'.bin','wb') as g:
        while True:
            chunk = f.read(chunksize)
            if chunk:
                g.write(chunk)
                num_examples_train += 1
            else:
                break
            i += 1
            if (i - 1) % PRINT_INTERVAL == 0 or i == num_examples:
                print('{}/{} lines processed. SEPARATE TRAIN TEST FILE'.format(i, num_examples))
    return num_examples_test,num_examples_train


def separate_train_dataset(dirname,num_examples,num_channels,boardsize, num_sep):

    #we sum +1 since there will be a test set also
    interval_sep = num_examples / (num_sep)

    chunksize = boardsize * boardsize * num_channels + LABEL_SIZE
    f=open(dirname+'_train_shuffled.bin','rb')
    filenames=[dirname+'_{}.bin'.format(i+1) for i in range(num_sep)]
    num_examples_each_file=[0 for _ in range(num_sep)]
    i=0
    for sep in range(num_sep):
        with open(filenames[sep],'wb') as g:
            for j in range(interval_sep):
                chunk=f.read(chunksize)
                if chunk:
                    g.write(chunk)
                    num_examples_each_file[sep] += 1
                else:
                    break
                i += 1
                if (i - 1) % PRINT_INTERVAL == 0 or i == num_examples:
                    print('{}/{} lines processed. SEPARATE INDIVIDUAL TRAIN FILES'.format(i, num_examples))

    return num_examples_each_file




def find_games_with_property(dirname, property):
    for fn in os.listdir(dirname):
        f = open(dirname + '/' + fn, 'r')
        sgf_data = f.read()
        f.close()
        if property in sgf_data:
            print(fn)


def records_from_file(filename, boardsize,num_channels):
    chunksize=boardsize*boardsize*num_channels+LABEL_SIZE
    with open(filename, "rb") as f:
        while True:
            chunk = f.read(chunksize)
            if chunk:
                yield chunk
            else:
                break


# def shuffle_dataset(dirname,num_examples,boardsize,num_channels):
#
#     pos_examples=np.array([i for i in range(num_examples)])
#     np.random.shuffle(pos_examples)
#     chunksize = boardsize * boardsize * num_channels + LABEL_SIZE
#     #print(pos_examples)
#     i=0
#     with open(dirname+'_shuffled.bin','wb') as g:
#         with open(dirname+'.bin','rb') as f:
#             for pos in pos_examples:
#                 f.seek(pos*chunksize)
#                 chunk = f.read(chunksize)
#                 if chunk:
#                     g.write(chunk)
#                 else:
#                     eprint('error while writing shuffled file')
#                     eprint('dirname:{} num_examples:{}'.format(dirname,num_examples))
#                 i += 1
#                 if (i - 1) % PRINT_INTERVAL == 0 or i == num_examples:
#                     print('{}/{} lines processed. SHUFFLE FILE {}'.format(i, num_examples,dirname))


def shuffle_dataset_in_memory(dirname,num_examples,boardsize,num_channels):
    """
    shuffles the examples inside the file
    also, returns the number of examples in the file
    in order to use it in generate_idx_dataset()"""
    # TODO: do efficient memory shuffling, we don't need to read everything to memory
    # f=open(filename,'r')
    lines = []
    chunksize = boardsize * boardsize * num_channels + LABEL_SIZE
    i=0
    with open(dirname+'.bin','rb') as f:
        while True:
            chunk=f.read(chunksize)
            if chunk:
                lines.append(chunk)
            else:
                break
            i += 1
            if (i - 1) % PRINT_INTERVAL == 0 or i == num_examples:
                print('{}/{} lines read to memory. SHUFFLING FILE {}'.format(i, num_examples, dirname))

    # shuffle to get a uniform random order in linear time
    N = len(lines)

    for i in range(N):
        r = random.randint(i, N-1)
        temp = lines[i]
        lines[i] = lines[r]
        lines[r] = temp

        if (i) % PRINT_INTERVAL == 0 or i == num_examples-1:
            print('{}/{} lines ordered in memory. SHUFFLING FILE {}'.format(i+1, num_examples, dirname))

    i=0
    with open(dirname +'_shuffled.bin', 'wb') as f:
        for line in lines:
            f.write(line)
            i += 1
            if (i - 1) % PRINT_INTERVAL == 0 or i == num_examples:
                print('{}/{} lines written to memory. SHUFFLING FILE {}'.format(i, num_examples, dirname))


def generate_gz_files(dirname,num_examples,num_channels,boardsize):

    #first shuffle total dataset
    shuffle_dataset_in_memory(dirname, num_examples, boardsize, num_channels)

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
                           + struct.pack('>I', boardsize) \
                           + struct.pack('>I', boardsize)

    header_test_vectors = magic_number_vectors + struct.pack('>I', num_test_examples) \
                          + struct.pack('>I', num_channels) \
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

    for line in records_from_file(dirname + '_shuffled.bin',boardsize,num_channels):
        if i < index:
            train_labels.write(line[0:LABEL_SIZE])
            train_vectors.write(line[LABEL_SIZE:])
        else:
            test_labels.write(line[0:LABEL_SIZE])
            test_vectors.write(line[LABEL_SIZE:])
        i += 1
        if (i-1) % PRINT_INTERVAL==0 or i==num_examples:
            print('{}/{} lines processed. GZ FILE'.format(i,num_examples))

    train_vectors.close()
    test_vectors.close()
    train_labels.close()
    test_labels.close()

def generate_idx_dataset9(dirname,num_channels,aug_data=True):
    generate_idx_dataset(dirname,9,num_channels,aug_data)

def generate_idx_dataset19(dirname,num_channels,aug_data=False):
    generate_idx_dataset(dirname,19,num_channels,aug_data)

def generate_idx_dataset(dirname,boardsize,num_channels,aug_data=False):
    # iterate over the files in directory
    print(dirname)

    VECTOR_SIZE = boardsize*boardsize*num_channels

    EXAMPLE_SIZE = VECTOR_SIZE + LABEL_SIZE

    # we will store the dataset in this file
    # f=open(dirname+'.bin','wb')

    total_time=0
    elapsed_time=0

    #start_time = time.time()
    #num_examples = generate_bin_dataset(dirname,boardsize,num_channels)
    #elapsed_time=time.time()-start_time
    #total_time+=elapsed_time
    #print('bin file created. Time to create {} s'.format(elapsed_time))

    start_time = time.time()
    if SKIP_FILE_GENERATION==False or os.path.isfile(dirname+'.bin')==False:
        num_examples = generate_bin_dataset(dirname,boardsize,num_channels,aug_data)
        elapsed_time=time.time()-start_time
        print('bin file created. Time to create {} s'.format(elapsed_time))
    else:
        if os.path.isfile(dirname+'.prop'):
            with open(dirname+'.prop') as f:
                num_examples=sum([int(c) for c in f.readline().split(',')])
                num_channels_file=int(f.readline())
                if num_channels!=num_channels_file:
                    print('num_channels is different. Regenerating bin file')
                    start_time = time.time()
                    num_examples = generate_bin_dataset(dirname, boardsize, num_channels)

            print('Skipping this part. {} file already exists'.format(dirname+'.bin'))
            print('num_examples:{}'.format(num_examples))
        else:
            file_size=os.path.getsize(dirname+'.bin')
            chunksize=num_channels*boardsize*boardsize+LABEL_SIZE
            num_examples=file_size/chunksize
            print('Counted # of examples directly from file')

    elapsed_time = time.time() - start_time
    total_time+=elapsed_time
    print('bin file created.Time to create {} s'.format(elapsed_time))

    # UPDATE PRINT INTERVAL
    global PRINT_INTERVAL
    PRINT_INTERVAL = int(num_examples / NUM_PRINTS)

    start_time=time.time()
    #separate in train and test before shuffling
    if SKIP_FILE_GENERATION==True and  os.path.isfile(dirname + '_train.bin') and os.path.isfile(dirname+'_test.bin'):
        print('Skipping this part. train and test files already exist.')
        chunksize = num_channels * boardsize * boardsize + LABEL_SIZE
        num_examples_test= os.path.getsize(dirname + '_test.bin')/ chunksize
        num_examples_train= os.path.getsize(dirname + '_train.bin') / chunksize
        print('Counted # of examples directly from file')
    else:
        num_examples_test,num_examples_train= separate_into_train_test(dirname,boardsize,num_channels,num_examples)

    elapsed_time = time.time() - start_time
    total_time += elapsed_time
    print('test and train files created. Time to create {} s'.format(elapsed_time))

    start_time = time.time()
    if SKIP_FILE_GENERATION==False or os.path.isfile(dirname + '_train_shuffled.bin')==False:
        # shuffle complete dataset and shuffle training dataset
        shuffle_dataset_in_memory(dirname+'_train', num_examples_train,boardsize, num_channels)
    else:
        print('Skipping this part. shuffled train file already exists')
    elapsed_time = time.time() - start_time
    total_time += elapsed_time
    print('shuffled bin train file created. Time to create {} s'.format(elapsed_time))

    #SHUFFLE TEST SET
    start_time = time.time()
    if SKIP_FILE_GENERATION == False or os.path.isfile(dirname + '_test_shuffled.bin') == False:
        # shuffle complete dataset and shuffle training dataset
        shuffle_dataset_in_memory(dirname + '_test', num_examples_test, boardsize, num_channels)
    else:
        print('Skipping this part. shuffled test file already exists')
    elapsed_time = time.time() - start_time
    total_time += elapsed_time
    print('shuffled bin test file created. Time to create {} s'.format(elapsed_time))

    start_time = time.time()
    # 5 separate bin files
    num_sep=5
    num_examples_each_file=separate_train_dataset(dirname,num_examples_train,num_channels,boardsize,5)
    elapsed_time = time.time() - start_time
    total_time += elapsed_time
    print('INDIVIDUAL train files created. Time to create {} s'.format(elapsed_time))


    #generate prop file
    # create properties file
    num_examples_each_file.append(num_examples_test)
    create_prop_file(dirname,num_examples_each_file,num_channels,boardsize )

    #generate gz files
    #
    #generate_gz_files(dirname,num_examples,num_channels,boardsize)


    elapsed_time = time.time() - start_time
    total_time += elapsed_time
    print('gz file created. Time to create {} s'.format(elapsed_time))
    print('Total time {} s'.format(total_time))



if __name__ == '__main__':
    # find_handicap_games(dirname)
    # process_game('2001-12-08-3.sgf')
    # generate_dataset('9x9_10games')

    # shuffle_dataset('9x9_10games.bin')
    # generate_idx_dataset_9x9('9x9_10games')

    #generate_idx_dataset9('gogod_9x9_games',4)

    #9x9 DATASETS
    #generate_idx_dataset9('/home/mario/datasets/9x9_10games',4)
    generate_idx_dataset9('/home/mario/datasets/gogod_9x9_games', 4)

    #19x19 DATASETS
    #generate_idx_dataset19('/home/mario/datasets/KGS_10games',4)
    #generate_idx_dataset19('/tmp/datasets/KGS_100games', 4)
    #generate_idx_dataset19('/tmp/datasets/KGS2001',4)
    #generate_idx_dataset19('/home/mario/datasets/KGS2016', 4)
    #shuffle_dataset_in_memory('/tmp/datasets/KGS2016_train',3471228,19,4)
    #shuffle_dataset_in_memory('/tmp/datasets/KGS2016_train',3471228,19,4)

