import itertools
import math
import matplotlib as mpl
mpl.use('nbagg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy
import sklearn
import sklearn.cluster
import time

import aux
import cfg

# this module implements functions for the analysis of entrainment results



def _filter(df, tsk_or_ses, symm):
    ''' filters given df for task/session and symmetric/asymmetric results '''
    if symm: 
        # symmetric, speaker-independent results only (spk_id = 0)
        df = df.xs(0, level=3)
    else:
        # asymmetric, speaker-specific results only (spk_id != 0)
        df.reset_index(level=3, inplace=True)
        df = df[df['spk_id'] != 0]
        df.set_index(['spk_id'], append=True, inplace=True)
    if tsk_or_ses == 'ses':
        # session results only (tsk_id = 0)
        df = df.xs(0, level=2)
    else:
        # task results only (tsk_id != 0)
        df.reset_index(level=2, inplace=True)
        df = df[df['tsk_id'] != 0]
        df.set_index(['tsk_id'], append=True, inplace=True)
    return df


def _add_chi_col(df, col, mea_id):
    ''' adds new column to df indicating entrainment based on values in col '''
    # entrainment present for syn, lcon, gcon if > 0; for all other measures, 
    # depends on whether partner sim (sim_p) > than non-partner sim (sim_x)
    # (sims always negative, closer to 0 means greater sim; 
    #  normalization as -sim_p / sim_x, negated so greater values = greater sim; 
    #  value greater -1 iff sim_p > sim_x)
    thresh = 0 if mea_id in [cfg.MEA_SYN, cfg.MEA_LCON, cfg.MEA_GCON] else -1
    # mark rows based on whether entrainment is present or not
    # does not check for nan (results in -1), filtered out later
    chi_func = lambda x: 1 if x[col] > thresh else -1
    df[col + '_chi'] = df.apply(chi_func, axis=1)
    return df


def get_samples(df_bt, dict_df_meas, tsk_or_ses='ses', symm=True, nrm=True):
    ''' gets session/task samples with values for given measures

    for all measures given as dataframes, joins values per session/task 

    args:
        df_bt: "big table" pandas dataframe as returned by ap.load_data, with
            'gender_paired' as an extra column
        dict_df_meas: dictionary indexed by cfg.MEASURES, containing dataframes
            with values per measure (indexed by ses_id, tsk_id, spk_id);
            dfs as returned by ap.lsim, ap.syn, ap.lcon, ap.gsim, ap.gcon, 
            lex.kld, lex.ppl, lex.dist_sim functions
        tsk_or_ses: whether to use task ('tsk') or session ('ses') results
        symm: whether to use symmetric results (True) or asymmetric (False)
        nrm: whether to z-score normalize (True) or not (False)
    returns:
        pandas dataframe with various measure values, indexed with ses_id/tsk_id 
    '''
    # load samples for all measures and features
    # start with nothing and keep joining values for all measures
    df_samples = None
    for mea_id, df_mea in dict_df_meas.items():
        cfg.check_mea_id(mea_id)
        
        # for gsim and the lexical measures, partner values are normalized by
        # the non-partner baseline here; local similarity at turn exchanges is 
        # normalized by similarity between non-adjacent chunks in ap.lsim;
        # only symmetric values and only session/task values are used, as needed
        # (spk_id == 0; tsk_id == 0 or tsk_id != 0 depending on tsk_or_ses);
        # all measures are z-score normalized across sessions
        
        if mea_id in (cfg.MEA_KLD, cfg.MEA_PPL, cfg.MEA_HFW):
            # lexical measure, normalize by non-partner baseline and z-score
            col = 'kld' if mea_id == cfg.MEA_KLD \
                else 'ppl' if mea_id == cfg.MEA_PPL \
                else 'dsim'
            df = (-df_mea[col + '_wgh_p'] / df_mea[col + '_wgh_x'])
            df = _filter(df.to_frame(col), tsk_or_ses, symm)
            df = _add_chi_col(df, col, mea_id)
            if nrm:
                df[col] = (df[col] - df[col].mean()) / df[col].std()
            df_samples = df if df_samples is None else df_samples.join(df)
        else: 
            # acoustic-prosodic measure, process for all features
            for f in cfg.FEATURES:
                # shorthand for current measure and feature
                # (abbreviation only works if only one of mean/max/min is used)
                col = mea_id + '_' + f[0]
                if mea_id == cfg.MEA_GSIM:
                    df = (-df_mea[f + '_sim_p'] / df_mea[f + '_sim_x'])
                    df = _filter(df.to_frame(col), tsk_or_ses, symm)
                elif mea_id == cfg.MEA_GCON:
                    df = _filter(
                        df_mea[[f + '_con']], tsk_or_ses, symm)
                    df = df.rename(columns={f + '_con': col})
                else: 
                    # local measure, mea_id in [MEA_LSIM, MEA_LCON, MEA_SYN]
                    df = _filter(df_mea[[f]], tsk_or_ses, symm)
                    df[col] = [
                        v[3] if mea_id == cfg.MEA_LSIM else aux.r2z(v[0])
                        for v in df[f]]
                    df.drop(f, axis=1, inplace=True)
                df = _add_chi_col(df, col, mea_id)
                if nrm:
                    df[col] = (df[col] - df[col].mean()) / df[col].std()
                df_samples = df if df_samples is None else df_samples.join(df)
    # remove all rows that contain a nan value for any measure
    for col in df_samples.columns:
        df_samples = df_samples[pd.notna(df_samples[col])]
    # separate main columns and chi columns into two dataframes 
    chi_cols = []
    for col in df_samples.columns:
        if col[-4:] == '_chi':
            chi_cols += [col]
    df_chi = df_samples[chi_cols].astype({col: int for col in chi_cols})
    df_samples.drop(chi_cols, axis=1, inplace=True)
    # add gender pair info to dataframe index
    fltr = df_bt['p_or_x'] == 'p'
    loc_cols = [tsk_or_ses+'_id', 'gender', 'gender_paired']
    df_gp = df_bt[fltr].loc[:,loc_cols].groupby(tsk_or_ses+'_id').first()
    func = lambda x: x['gender'] if x['gender'] == x['gender_paired'] else 'x'
    df_gp['gp'] = df_gp.apply(func, axis=1)
    df_gp.drop(['gender', 'gender_paired'], axis=1, inplace=True)
    df_samples = \
        df_samples.join(df_gp, on=tsk_or_ses+'_id').set_index('gp', append=True)

    return df_samples, df_chi


def correlate_columns(df):
    ''' computes correlations between columns of given dataframe '''
    res = []
    for i, col1 in enumerate(df.columns):
        for col2 in df.columns[(i+1):]:
            r, p = scipy.stats.pearsonr(df[col1], df[col2])
            res += [(col1, col2, r, p)]
    return res


def chisquare(df, vals1=[-1,1], vals2=[-1,1], verbosity=0, min_obs=5):
    ''' runs chisquare for pairs of columns of df, grouped by given values '''
    assert verbosity in [0,1], 'verbosity must be 0 or 1'
    res = []
    for i, col1 in enumerate(df.columns):
        for col2 in df.columns[(i+1):]:
            if col1 == '_' or col2 == '_':
                continue
            # get observed frequencies
            # 1) count co-occurrences for current pair of measures
            df_cnts = df.groupby([col1, col2]).count().iloc[:,0]
            # 2) reindex in case some combination did not occur
            df_cnts = df_cnts.reindex(
                itertools.product(vals1, vals2), fill_value=0)
            obs = np.array(df_cnts).reshape(len(vals1), -1)
            # run chisquare if enough observations of each combination exist
            if min(obs.reshape(-1, 1)) < min_obs:
                res += [(col1, col2) + (float('nan'), float('nan'))]
            else:
                chi2 = scipy.stats.contingency.chi2_contingency(obs) 
                res += [
                    (col1, col2) + chi2[:(verbosity+1)*2] + (obs,) * verbosity]
    return res


def bh(res, p_id=3, alpha1=0.05, alpha2=0.1):
    ''' benjamini hochberg on given results, based on p value in given id '''
    assert alpha1 < alpha2, 'alpha1 needs to be less than alpha2'
    res = sorted(res, key=lambda x: 1.0 if math.isnan(x[p_id]) else x[p_id])
    k1 = 0
    k2 = 0
    for i in range(len(res)):
        if res[i][p_id] <= (i+1) / len(res) * alpha1:
            k1 = i+1
        if res[i][p_id] <= (i+1) / len(res) * alpha2:
            k2 = i+1
    return res[:k1], res[k1:k2], res[k2:]


def kmeans(df, max_k, n_init):
    """ computes k-means score for given dataframe and controls for varying k
    
    args:
        df: dataframe with data for clustering, 
            one sample per row, one dimension per column
        max_k: maximum k to try, 2 up to max_k (inclusive) will be tried
        n_init: number of initializations per value of k
    returns:
        list of three dicts with best results
    """
    def __run_clustering(X, max_k, n_init):
        X = sklearn.preprocessing.StandardScaler().fit_transform(X)
        results = {'kmeans': [], 'dist': [], 'sil': [], 'ch': []}
        for k in range(2, max_k+1):
            print('starting k=%d at %s' % (k, time.ctime()))
            kmeans = sklearn.cluster.KMeans(n_clusters=k, n_init=n_init).fit(X)
            results['kmeans'].append(kmeans)
            results['dist'].append(-kmeans.score(X))
            results['sil'].append(
                sklearn.metrics.silhouette_score(X, kmeans.predict(X)))
            results['ch'].append(
                sklearn.metrics.calinski_harabasz_score(X, kmeans.predict(X)))
        return results
    
    def __shuffle_columns(df):
        rng = np.random.default_rng(0)
        return list(zip(*[rng.permutation(df.iloc[:,i].values)
                          for i in range(len(df.columns))]))
    
    def __gen_random_data_like(df):
        means = df.mean().values
        stds = df.std().values
        out_data = []
        rng = np.random.default_rng(0)
        for i in range(len(df)):
            sample = []
            for j in range(len(means)):
                sample.append(rng.normal(means[j], stds[j]))
            out_data.append(sample)
        return out_data
    
    res = []
    print('clustering real data')
    res.append(__run_clustering(df.values, max_k, n_init))
    print('clustering shuffled data')
    res.append(__run_clustering(__shuffle_columns(df), max_k, n_init))
    print('clustering random data')
    res.append(__run_clustering(__gen_random_data_like(df), max_k, n_init))
    return res


def plot_kmeans_scores(scores, col):
    ''' produces plot of given column in given kmeans scores '''
    if col == 'dist':
        y_label = 'sum of distances'
    elif col == 'sil':
        y_label = 'silhouette score'
    elif col == 'ch':
        y_label = 'calinski harabasz score'
    else:
        y_label = 'unknown'

    x = range(2, len(scores[0][col]) + 2)
    fig, ax = plt.subplots()
    ax.plot(x, scores[0][col], 'b', label='real')
    ax.plot(x, scores[1][col], '--r', label='shuffled')
    ax.plot(x, scores[2][col], 'xg', label='random')
    
    fig.set_size_inches(5, 5)
    plt.tick_params(
        axis='both', which='major', labelsize=17)
    plt.xlabel('K', fontsize=16)
    plt.ylabel(y_label, fontsize=16)
    plt.legend(prop={'size': 15})

    plt.grid()
    plt.tight_layout()
    plt.show()
    plt.close()


def pca(df):
    ''' runs pca on given dataframe of samples, produces 3d plot '''
    X = sklearn.preprocessing.StandardScaler().fit_transform(df.values)
    pca = sklearn.decomposition.PCA().fit(X)
    print('explained variance ratio per dimension:\n %s'
          % (pca.explained_variance_ratio_,))
    for ratio_goal in (0.9, 0.95, 0.99):
        for i in range(len(pca.explained_variance_ratio_)):
            if sum(pca.explained_variance_ratio_[:i+1]) >= ratio_goal:
                print('dimensions required to retain %.2f of variance: %d'
                      %(ratio_goal, i+1))
                break
    X = pca.transform(X)
    x = [x[0] for x in X]
    y = [x[1] for x in X]
    z = [x[2] for x in X]
    print('fraction of variance retained in 3D:', 
          sum(pca.explained_variance_ratio_[:3]))
    fig = plt.figure()
    fig.set_size_inches(10.5, 7.5)
    ax = fig.add_subplot(111, projection='3d')
    ax.tick_params(axis='both', which='major', labelsize=17)
    ax.scatter(x, y, z)
    plt.xlim(-3.5, 3.5)
    plt.ylim(-3.5, 3.5)
    ax.set_zlim(-3.5, 3.5)
    plt.show()
    plt.close()





