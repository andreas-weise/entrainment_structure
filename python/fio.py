import csv
import nltk
import os
import pickle
import subprocess
from zipfile import ZipFile

import aux
import cfg
import db



################################################################################
#                            GET PATH AND FILE NAMES                           #
################################################################################

def get_lmn_pfn(corpus_id, tsk_or_ses, tsk_ses_id, a_or_b):
    ''' returns path and file name (w/o extension) for lm/ngram files '''
    return cfg.get_lmn_path(corpus_id), \
        '%s_%d_%s' % (tsk_or_ses, tsk_ses_id, a_or_b)


def get_dump_pfn(corpus_id, mea_id):
    ''' returns path and two file names for pickle dumps '''
    cfg.check_corpus_id(corpus_id)
    cfg.check_mea_id(mea_id)
    return (cfg.get_dump_path(corpus_id),
            mea_id + '.pickle',
            mea_id + '_raw.pickle')



################################################################################
#                                 WRITE FILES                                  #
################################################################################

def remove_lmn_files(corpus_id, tsk_or_ses=None, extension='txt'):
    ''' removes lm/ngram files with given extension for tasks/sessions/both '''
    if tsk_or_ses is None:
        # if tsk_or_ses not specified, do both
        remove_lmn_files(corpus_id, 'tsk', extension)
        remove_lmn_files(corpus_id, 'ses', extension)
    else:
        for tsk_ses_id in db.get_tsk_ses_ids(tsk_or_ses):
            for a_or_b in ['A', 'B']:
                path, fname = get_lmn_pfn(
                    corpus_id, tsk_or_ses, tsk_ses_id, a_or_b) 
                fname = path + fname + '.' + extension
                if os.path.isfile(fname):
                    os.remove(fname)


def store_tokens(corpus_id, tsk_or_ses=None, lem=aux.default_lem):
    ''' writes tokens per speaker to txt file for each task/session '''
    if tsk_or_ses is None:
        store_tokens(corpus_id, 'tsk', lem)
        store_tokens(corpus_id, 'ses', lem)
    else:
        remove_lmn_files(corpus_id, tsk_or_ses, extension='txt')
        all_lemmata = []
        # iterate over all tasks/sessions
        for tsk_ses_id in db.get_tsk_ses_ids(tsk_or_ses):
            tur_id_prev = -1
            cnts = {'A': 0, 'B': 0}
            # iterate over all chunks in current task/session
            for tur_id, a_or_b, words in db.get_words(tsk_or_ses, tsk_ses_id):
                path, fname = get_lmn_pfn(
                    corpus_id, tsk_or_ses, tsk_ses_id, a_or_b) 
                with open(path + fname + '.txt', 'a') as txt_file:
                    if cnts[a_or_b] > 0:
                        if tur_id_prev != tur_id:
                            # new turn, start new line (if not very first turn)
                            txt_file.write('\n')
                        else:
                            txt_file.write(' ')
                    # lemmatize and write words of current chunk to file
                    words_lem = lem(words)
                    all_lemmata += words_lem
                    txt_file.write(' '.join(words_lem))
                cnts[a_or_b] += 1
                tur_id_prev = tur_id
        # store sorted vocabulary, i.e., distinct lemmata across all transcripts
        vocab = sorted(list(nltk.FreqDist(all_lemmata).keys()))
        with open(cfg.get_vocab_fname(corpus_id), 'w') as vocab_file:
            vocab_file.write('\n'.join(vocab))


def write_pickle_dumps(corpus_id, mea_id, data_main, data_raw=None):
    ''' writes given data for corpus and entrainment measure to pickle file '''
    path, fname1, fname2 = get_dump_pfn(corpus_id, mea_id)
    with open(path + fname1, 'wb') as pickle_file:
        pickle.dump(data_main, pickle_file)
    if data_raw is not None:
        with open(path + fname2, 'wb') as pickle_file:
            pickle.dump(data_raw, pickle_file)



################################################################################
#                                  READ FILES                                  #
################################################################################

def readlines(path, fname):
    ''' yields all lines in given file '''
    with open(path + fname) as file:
        for line in file.readlines():
            yield(line)


def readlines_zip(path, zip_fname, zipped_fname, encoding='utf-8'):
    ''' returns list of lines of given file within given zip file '''
    with ZipFile(path + zip_fname) as zip_file:
        with zip_file.open(zipped_fname) as zipped_file:
            return [line.decode(encoding) for line in zipped_file.readlines()]


def read_csv(path, fname, delimiter=",", quotechar='"', skip_header=False):
    ''' yields all rows in given file, interpreted as csv '''
    with open(path + fname, 'r') as csv_file:
        reader = csv.reader(csv_file, delimiter=delimiter, quotechar=quotechar)
        if skip_header:
            next(reader)
        for row in reader:
            yield(row)


def load_tokens(
        corpus_id, tsk_or_ses, tsk_ses_id, a_or_b, excl=[], func=lambda t: t):
    ''' loads tokens of given task/session & speaker, returns filtered list '''
    path, fname = get_lmn_pfn(corpus_id, tsk_or_ses, tsk_ses_id, a_or_b)
    if os.path.isfile(path + fname + '.txt'):
        tokens = '\n'.join(readlines(path, fname + '.txt')).replace('\n', ' ')
        tokens = [func(t) for t in tokens.split() if t not in excl]
    else:
        tokens = []
    return tokens


def load_all_tokens(corpus_id):
    ''' loads list of tokens for all sessions and speakers from files '''
    tokens = []
    for ses_id in db.get_ses_ids():
        for a_or_b in ['A', 'B']:
            path, fname = get_lmn_pfn(corpus_id, 'ses', ses_id, a_or_b)
            lines = readlines(path, fname + '.txt')
            tokens += '\n'.join(lines).replace('\n', ' ').split()
    return tokens


def load_pickle_dumps(corpus_id, mea_id):
    ''' loads data for given corpus and measure from pickle file(s) '''
    path, fname1, fname2 = get_dump_pfn(corpus_id, mea_id)
    res1 = None
    res2 = None
    if os.path.isfile(path + fname1):
        with open(path + fname1, 'rb') as pickle_file:
            res1 = pickle.load(pickle_file)
    if os.path.isfile(path + fname2):
        with open(path + fname2, 'rb') as pickle_file:
            res2 = pickle.load(pickle_file)
    return (res1, res2)



################################################################################
#                                     OTHER                                    #
################################################################################

def extract_features(in_path, in_fname, ses_id, chu_id, words, start, end):
    ''' runs feature extraction for given chunk section, returns features '''
    # determine tmp filenames
    cut_fname = '%d_%d.wav' % (ses_id, chu_id)
    out_fname = '%d_%d.txt' % (ses_id, chu_id)
    # extract audio and features
    subprocess.check_call(['sox', 
                           in_path + in_fname, 
                           cfg.TMP_PATH + cut_fname, 
                           'trim', str(start), '=' + str(end)])
    subprocess.check_call(['praat', '--run', 
                           cfg.PRAAT_SCRIPT_FNAME,
                           cfg.TMP_PATH + cut_fname, 
                           cfg.TMP_PATH + out_fname])
    # read output
    features = {}
    for line in readlines(cfg.TMP_PATH, out_fname):
        key, val = line.replace('\n', '').split(',')
        try:
            val = float(val)
        except:
            val = None
        features[key] = val
    features['rate_syl'] = aux.count_syllables(words) / (end - start)
    # clean up
    os.remove(cfg.TMP_PATH + cut_fname)
    os.remove(cfg.TMP_PATH + out_fname)
    
    return features





