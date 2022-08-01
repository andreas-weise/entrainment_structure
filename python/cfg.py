# paths within the project 
SQL_PATH = '../sql/'
LMN_PATH_GC = '../../data/gc/lm_ngrams/'
LMN_PATH_SB = '../../data/sb/lm_ngrams/'
DUMP_PATH_GC = '../../data/gc/dumps/'
DUMP_PATH_SB = '../../data/sb/dumps/'

# corpus identifiers
CORPUS_ID_GC  = 'GC'
CORPUS_ID_SB = 'SB'
CORPUS_IDS = [CORPUS_ID_GC, CORPUS_ID_SB]

# external paths (corpora directories and temporary file directory)
# comment back in and point to corpora 
# CORPUS_PATH_GC = ''
# CORPUS_PATH_SB = ''
META_PATH_SB = CORPUS_PATH_SB + 'meta/'
# set as needed
TMP_PATH = ''

# database filenames
DB_FNAME_GC = '../../gc.db'
DB_FNAME_SB = '../../sb.db'

# praat and sql scripts
PRAAT_SCRIPT_FNAME = '../praat/extract_features.praat'
SQL_INIT_FNAME_GC = 'gc_init.sql'
SQL_INIT_FNAME_SB = 'sb_init.sql'
SQL_DM_FNAME = 'del_missing_ses.sql'
SQL_CU_FNAME = 'cleanup.sql'
SQL_AT_FNAME = 'aux_tables.sql'
SQL_BT_FNAME = 'big_table.sql'
SQL_SP_FNAME = 'speaker_pairs.sql'

# language model vocabulary filenames (contents computed in fio.store_texts)
VOCAB_FNAME_GC = LMN_PATH_GC + 'vocab.txt'
VOCAB_FNAME_SB = LMN_PATH_SB + 'vocab.txt'

# normalization types
NRM_SPK = 'SPEAKER'
NRM_GND = 'GENDER'
NRM_RAW = 'RAW'
NRM_TYPES = [NRM_SPK, NRM_GND, NRM_RAW]

# entrainment measure identifiers
MEA_GSIM = 'gsim'
MEA_GCON = 'gcon'
MEA_LSIM = 'lsim'
MEA_LCON = 'lcon'
MEA_SYN  = 'syn'
MEA_KLD  = 'kld'
MEA_PPL  = 'ppl'
MEA_HFW  = 'hfw'
MEASURES = [
    MEA_GSIM, MEA_GCON, MEA_LSIM, MEA_LCON, MEA_SYN, MEA_KLD, MEA_PPL, MEA_HFW]

# how to group data for entrainment measurement
GRP_BY_SES_TYPE = 'ses_type'
GRP_BY_SES = 'ses'
GRP_BY_SES_SPK = 'ses_spk'
GRP_BY_TSK = 'tsk'
GRP_BY_TSK_SPK = 'tsk_spk'
GRP_BYS = [
    GRP_BY_SES_TYPE, 
    GRP_BY_SES, 
    GRP_BY_SES_SPK, 
    GRP_BY_TSK, 
    GRP_BY_TSK_SPK
]

# IDs for memoization of token distributions (see lex.get_dist)
TYPES_ID_MF = 'MOST_FREQUENT'

# all features computed by praat and those actually analyzed
FEATURES_ALL = [
    'intensity_mean',
    'intensity_std',
    'intensity_min',
    'intensity_max',
    'pitch_mean',
    'pitch_std',
    'pitch_min',
    'pitch_max',
    'jitter',
    'shimmer',
    'nhr',
    'rate_syl',
    'rate_vcd'
]
FEATURES = [
    'intensity_mean',
#    'intensity_max',
    'pitch_mean',
#    'pitch_max',
#    'jitter',
#    'shimmer',
#    'nhr',
    'rate_syl'
]


def check_corpus_id(corpus_id):
    assert corpus_id in CORPUS_IDS, 'unknown corpus id'


def check_mea_id(mea_id):
    assert mea_id in MEASURES, 'unknown entrainment measure'


def get_db_fname(corpus_id):
    check_corpus_id(corpus_id)
    return DB_FNAME_GC if corpus_id == CORPUS_ID_GC else DB_FNAME_SB


def get_dump_path(corpus_id):
    check_corpus_id(corpus_id)
    return DUMP_PATH_GC if corpus_id == CORPUS_ID_GC else DUMP_PATH_SB


def get_corpus_path(corpus_id):
    check_corpus_id(corpus_id)
    return CORPUS_PATH_GC if corpus_id == CORPUS_ID_GC else CORPUS_PATH_SB


def get_lmn_path(corpus_id):
    check_corpus_id(corpus_id)
    return LMN_PATH_GC if corpus_id == CORPUS_ID_GC else LMN_PATH_SB


def get_vocab_fname(corpus_id):
    check_corpus_id(corpus_id)
    return VOCAB_FNAME_GC if corpus_id == CORPUS_ID_GC else VOCAB_FNAME_SB


def check_grp_by(grp_by, supported=GRP_BYS):
    assert len(grp_by) > 0, 'at least one grp_by value needed'
    for g in grp_by:
        assert g in GRP_BYS, 'unknown grp_by value found'
        assert g in supported, 'unsupported grp_by value found'


