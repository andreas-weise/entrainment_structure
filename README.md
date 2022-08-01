# Looking for structure in entrainment behavior

This is an updated version of the code for the following paper (with slightly different results):
Weise, A., & Levitan, R. (2018). Looking for structure in lexical and acoustic-prosodic entrainment behaviors. NAACL HLT 2018, 2, 297–302. http://www.aclweb.org/anthology/N18-2048

Five acoustic-prosodic and three lexical measures are computed and applied to the Switchboard Corpus and (some of them) the Columbia Games Corpus. Data for the corpora is not contained.
Analysis of the measures includes the search for: correlations between them, co-occurrences, k-means clusters, and redundant dimensions (through PCA).

## Directory Overview

<ul>
    <li>jupyter: a sequence of Jupyter notebooks that invoke all SQL/python code to process and analyze the corpora</li>
    <li>praat: single Praat script for feature extraction</li>
    <li>python: modules for data processing and analysis invoked from the Jupyter notebooks; file overview:
        <ul>
            <li>ana.py: functions for the analysis of all entrainment measures (correlations etc.)</li>
            <li>ap.py: implementation of five acoustic-prosodic entrainment measures</li>
            <li>aux.py: auxiliary functions</li>
            <li>cfg.py: configuration constants; if you received the corpus data (separately), configure the correct paths here</li>
            <li>db.py: interaction with the corpus databases</li>
            <li>fio.py: file i/o</li>
            <li>lex.py: implementation of three lexical entrainment measures</li>
            <li>sb.py: functions specific to the switchboard corpus</li>
        </ul>
    </li>
    <li>sql: core sql scripts that initialize the database files and are used during processing/analysis; file overview:
        <ul>
            <li>aux_tables.sql: creates chunk_pairs table with turn exchanges and non-adjacent IPU pairs for local entrainment measures</li>
            <li>big_table.sql: SELECT to flatten normalized, hierarchical schema into one wide, unnormalized table for analysis</li>
            <li>cleanup.sql: auxiliary script for cleanup after feature extraction</li>
            <li>del_missing_ses.sql: deletes all data relating to three switchboard session for which audio was unavailable</li>
            <li>init_gc.sql: creates, documents, and populates the hierarchical database schema for the columbia games corpus</li>
            <li>init_sb.sql: creates and documents the hierarchical database schema for the switchboard corpus</li>
            <li>speaker_pairs.sql: SELECT to determine partner and non-partner pairs of speakers for analysis</li>
        </ul>
    </li>
</ul>
