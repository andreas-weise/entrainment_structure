import sqlite3

import aux
import cfg
import db
import fio



def populate_speakers():
    ''' reads meta-data to populate speakers table '''
    for row in fio.read_csv(cfg.META_PATH_SB, 'caller_tab.csv', delimiter=','):
        gender = 'f' if row[3] == ' "FEMALE"' else \
                 'm' if row[3] == ' "MALE"' else None
        db.ins_spk(spk_id=row[0], gender=gender)
    db.commit()


def populate_topics():
    ''' reads meta-data to populate topics table '''
    for row in fio.read_csv(cfg.META_PATH_SB, 'topic_tab2.csv', delimiter=';'):
        db.ins_top(top_id=row[1], title=row[0], details=row[2])
    db.commit()


def populate_sessions():
    ''' reads meta-data to populate sessions table '''
    for row in fio.read_csv(cfg.META_PATH_SB, 'conv_tab.csv', delimiter=','):
        db.ins_ses(
            ses_id=row[0], spk_id_a=row[2], spk_id_b=row[3], top_id=row[4])
    db.commit()


def populate_tasks():
    ''' creates a task for each session, then adds rating data '''
    # tasks receive same id as ses (superfluous table, see sb_init.sql); 
    # rating_tab.csv is incomplete, so insert basic record first, then update
    for ses_id in db.get_ses_ids():
        db.ins_tsk(tsk_id=ses_id, ses_id=ses_id, task_index=1, a_or_b='A')
    for row in fio.read_csv(cfg.META_PATH_SB, 'rating_tab.csv', delimiter=','):
        # row contains, in this order: ses_id/tsk_id, difficulty, topicality, 
        # naturalness, echo_a & _b, static_a & _b, background_a & _b;
        db.upd_tsk(*row[:-1])
    db.commit()


def _get_intervals(ses_id, a_or_b):
    ''' reads relevant transcript, combines non-silent tokens into intervals '''
    fname = 'sw%d%s-ms98-a-word.text' % (ses_id, a_or_b)
    lines = fio.readlines_zip(cfg.META_PATH_SB, 'swb-trans.zip', fname)
    
    words = []
    chunk_start = None
    intervals = []
    for line in lines:
        token_start, token_end, token = line.split()[1:]
        token_start = float(token_start)
        token_end = float(token_end)
        word = aux.preprocess_sb_token(token)
        if word != '':
            # beginning or continuation of chunk 
            words += [word]
            if chunk_start is None:
                chunk_start = token_start
        else:
            if len(words) > 0:
                # previous chunk ended (when current token started)
                intervals += [
                    (ses_id, a_or_b, chunk_start, token_start, ' '.join(words))]
                chunk_start = None
                words = []
    # store last chunk (necessary if last token is not silent)
    if chunk_start is not None:
        intervals += [
            (ses_id, a_or_b, chunk_start, token_start, ' '.join(words))]
    return intervals


def populate_turns_and_chunks():
    ''' populates turns and chunks tables (without features) from transcripts

    turn indices in transcripts are insufficient '''

    # global ids for turns and chunks (one tur_id per speaker, see below)
    tur_ids = [0, 0]
    chu_id = 0

    for ses_cnt, ses_id in enumerate(db.get_ses_ids()):
        # parse intervals for both speakers from session transcript and merge
        intervalsA = _get_intervals(ses_id, 'A')
        intervalsB = _get_intervals(ses_id, 'B')
        intervals = sorted(intervalsA + intervalsB, key=lambda x: x[2])

        # end of last chunk, turn index, and chunk index markers per speaker
        ends = [0.0, 0.0]
        tur_cnts = [0, 0] 
        chu_cnts = [0, 0]

        # iterate intervals, create a chunk for each entry and turns as needed 
        for _, a_or_b, start, end, words in intervals:
            tsk_id = ses_id
            role = db.get_role(ses_id, a_or_b)
            idx = 0 if a_or_b == 'A' else 1
            
            # check whether this is a new turn
            if ends[1-idx] > ends[idx] \
            or tur_cnts[1-idx] > tur_cnts[idx] \
            or tur_cnts[idx] == 0:
                # new turn, update index and count
                tur_cnts[idx] = max(tur_cnts) + 1
                tur_ids[idx] = max(tur_ids) + 1
                chu_cnts[idx] = 1
            else:
                # continuation of old turn
                chu_cnts[idx] += 1
            ends[idx] = end

            if chu_cnts[idx] == 1:
                # first chunk in turn; insert turn first
                db.ins_tur(
                    tur_ids[idx], tsk_id, tur_cnts[idx], tur_cnts[idx], role)
            chu_id += 1
            db.ins_chu(chu_id, tur_ids[idx], chu_cnts[idx], 
                       start, end, end-start, words)
        db.commit()
        if (ses_cnt + 1) % 100 == 0:
            print('%d sessions done' % (ses_cnt+1))


def extract_features(ses_id):
    ''' runs feature extraction for all chunks in given session, updates db '''
    db.connect(cfg.CORPUS_ID_SB)
    path = cfg.get_corpus_path(cfg.CORPUS_ID_SB)
    for a_or_b in ['A', 'B']:
        fname = 'sw%05d.%s.wav' % (ses_id, a_or_b)
        all_features = {}
        for chu_id, words, start, end in db.find_chunks(ses_id, a_or_b):
            if end - start >= 0.04: # min duration for 75Hz min pitch
                all_features[chu_id] = fio.extract_features(
                    path, fname, ses_id, chu_id, words, start, end)
        # function is invoked in parallel, database might be locked;
        # keep trying to update until it works
        done = False
        while not done:
            try:
                for chu_id, features in all_features.items():
                    db.set_features(chu_id, features)
                db.commit()
                done = True
            except sqlite3.OperationalError:
                pass
    db.close()
            


























