import hyphenate
import math
import nltk
from nltk.corpus import wordnet
import pandas as pd
import scipy

import cfg

cmu_dict = nltk.corpus.cmudict.dict()



def preprocess_sb_token(in_token):
    ''' prepocessing of individual tokens for switchboard transcript parsing
    
    removes different kinds of markup etc. that can cause issues downstream
    note that markups can be combined, as in '[laughter-pro[bably]-] '''
    out_token = in_token.replace('\n', '')
    if out_token in ['[noise]', '[silence]', 
                    '[vocalized-noise]', '[laughter]']:
        out_token = ''
        return out_token
    if len(out_token) > 10 and out_token[:10] == '[laughter-':
        # words said while laughing transcribed with markup; remove markup
        out_token = out_token[10:-1]
    if out_token[0] == '[' and out_token.find('/') != -1:
        # incorrect pronunciations marked like '[burgalies/burglaries]';
        # extract only what speaker actually said
        index = out_token.find('/')
        out_token = out_token[1:index]
    if out_token[-2:] == ']-':
        # incomplete words are marked like 'th[is]-'; cut off markup
        index = out_token.find('[')
        out_token = out_token[:index]
    if out_token[:2] == '-[':
        # incomplete words are also marked like '-[th]is'; cut off markup
        index = out_token.find(']') + 1
        out_token = out_token[index:]
    if out_token.find('n\'t') != -1:
        # marytts does not handle n't words properly, remove the apostrophe
        out_token = out_token.replace('n\'t', 'nt')
    if out_token.find('_1') != -1:
        # some words are marked with '_1'; remove that
        out_token = out_token.replace('_1', '')
    if out_token == 'um-hum':
        out_token = 'mhm'
    
    return out_token


def count_syllables(in_str):
    ''' counts the number of syllables in a given string '''
    syll_count = 0
    for word in in_str.split(' '):
        ### PREPROCESSING
        # remove whitespace and convert to lowercase for dictionary lookup
        word = word.strip().lower()
        # '-' marks incomplete words; remove it
        if len(word) > 0 and word[-1] == '-':
            word = word[:-1]
        # remove trailing "'s" if word with it is not in dictionary
        # (does not change syllable count) 
        if len(word) > 1 and word[-2:] == "'s" and word not in cmu_dict:
            word = word[:-2]

        ### SPECIAL CASES
        # there are no syllables in an empty string
        if len(word) == 0:
            syll_count += 0
        # unintelligible speech transcribed as '?'; treat as one syllable
        elif '?' in word:
            syll_count += sum([1 if c == '?' else 0 for c in word])
        ### STANDARD METHOD (dictionary lookup; fallback: automatic hyphenation)
        elif word in cmu_dict:
            # word is in the dictionary, extract number of vowels in primary
            # pronunciation as syllable count; vowels are recognizable by their 
            # stress markers (final digit), for example:
            #     cmu_dict["natural"][0] = ['N', 'AE1', 'CH', 'ER0', 'AH0', 'L']
            syll_count += sum([1 for p in cmu_dict[word][0] if p[-1].isdigit()])
        else:
            # fall back to the hyphenate library for a best guess (imperfect)
            syll_count += len(hyphenate.hyphenate_word(word))
    return syll_count


def get_df(data, index_names):
    ''' creates pandas dataframe from given data with given index names '''
    df = pd.DataFrame(data)
    df.index.set_names(index_names, inplace=True)
    return df


def default_lem(text):
    ''' default lemmatizer, runs nltk tokenizer, pos tagger, and lemmatizer 
    
    lemmatization only works on nouns, verbs, adjectives and adverbs;
    incomplete tokens are excluded from output
    
    args:
        text: original input text
    returns:
        list of lemmata of complete words in text
    '''
    # remove unknown words and punctuation and tokenize
    text = text.lower().replace('?', '').replace('.', '').replace(',', '')
    tokens = nltk.word_tokenize(text)
    # determine part of speech tags
    tokens_tags = nltk.pos_tag(tokens)
    # lemmatize
    lemmata = []
    wnl = nltk.stem.WordNetLemmatizer()
    for token, ptb_tag in tokens_tags:
        # process only complete tokens, skip incomplete ones
        if token[-1] != '-':
            # translate tagset from penn treebank to wordnet
            # (works only for nouns, verbs, adjectives, and adverbs)
            if ptb_tag[0] == 'N':
                wn_tag = wordnet.NOUN
            elif ptb_tag[0] == 'V':
                wn_tag = wordnet.VERB
            elif ptb_tag[0] == 'J':
                wn_tag = wordnet.ADJ
                # adjective satellites (wn.ADJ_SAT) can be ignored
            elif ptb_tag[0] == 'R':
                wn_tag = wordnet.ADV
            else:
                wn_tag = None
            # lemmatize token if pos_tag falls into wordnet's categories
            lemma = wnl.lemmatize(token, wn_tag) if wn_tag else token
            lemmata.append(lemma)
    return lemmata


def ttest_ind(a, b):
    ''' scipy.stats.ttest_ind(a, b) with degrees of freedom also returned '''
    return scipy.stats.ttest_ind(a, b) + (len(a) + len(b) - 2,)


def ttest_rel(a, b):
    ''' scipy.stats.ttest_rel(a, b) with degrees of freedom also returned '''
    return scipy.stats.ttest_rel(a, b) + (len(a) - 1,)


def pearsonr(x, y):
    ''' scipy.stats.pearsonr(x, y) with degrees of freedom also returned '''
    return scipy.stats.pearsonr(x, y) + (len(x) - 2,)


def r2z(r):
    ''' fisher z-transformation of a pearson correlation coefficient '''
    return 0.5 * (math.log(1 + r) - math.log(1 - r))



           


































