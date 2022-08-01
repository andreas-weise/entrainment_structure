-- tables for switchboard corpus analysis
-- same format as for games corpus analysis (including superfluous tasks table)
--     allows for reuse of code


DROP TABLE IF EXISTS chunks;
DROP TABLE IF EXISTS turns;
DROP TABLE IF EXISTS tasks;
DROP TABLE IF EXISTS sessions;
DROP TABLE IF EXISTS speakers;
DROP TABLE IF EXISTS topics;



CREATE TABLE topics (
    -- conversation topics given to subjects
    top_id     INTEGER NOT NULL,
    title      TEXT,
    details    TEXT,
    PRIMARY KEY (top_id)
);



CREATE TABLE speakers (
    spk_id    INTEGER NOT NULL,
    gender    TEXT NOT NULL,
    PRIMARY KEY (spk_id)
);



CREATE TABLE sessions (
    -- session = complete phone conversation; not broken up as in games corpus
    ses_id      INTEGER NOT NULL,
    spk_id_a    INTEGER NOT NULL,
    spk_id_b    INTEGER NOT NULL,
    top_id      INTEGER NOT NULL,
    -- 0 = new; 1 = processed, file not found; 2 = done
    status      INTEGER DEFAULT 0,
    -- unnecessary column, only for code consistency across corpora
    type        TEXT DEFAULT "CONV",
    PRIMARY KEY (ses_id),
    FOREIGN KEY (spk_id_a) REFERENCES speakers (spk_id),
    FOREIGN KEY (spk_id_b) REFERENCES speakers (spk_id),
    FOREIGN KEY (top_id) REFERENCES topics (top_id)
);



CREATE TABLE tasks (
    -- unnecessary table, only to match games corpus structure
    -- task_index always set to 1, a_or_b always set to "A"
    tsk_id          INTEGER NOT NULL,
    ses_id          INTEGER NOT NULL,    
    task_index      INTEGER DEFAULT 1,
    a_or_b          TEXT DEFAULT "A",
	difficulty      NUMERIC(1),
	topicality      NUMERIC(1),
	naturalness     NUMERIC(1),
	echo_a          NUMERIC(1),
	echo_b          NUMERIC(1),
	static_a        NUMERIC(1),
	static_b        NUMERIC(1),
	background_a    NUMERIC(1),
	background_b    NUMERIC(1),
    PRIMARY KEY (tsk_id),
    FOREIGN KEY (ses_id) REFERENCES sessions (ses_id)
);



CREATE TABLE turns (
    -- turn = "maximal sequence of inter-pausal units from a single speaker"
    -- (Levitan and Hirschberg, 2011)
    tur_id            INTEGER NOT NULL,
    tsk_id            INTEGER NOT NULL,
    turn_type         TEXT,
    -- index of the turn within its task 
    turn_index        INTEGER NOT NULL,
    -- index of the turn within its session
    -- (same as for task, column only included for consistency)
    turn_index_ses    INTEGER NOT NULL,
    speaker_role      TEXT NOT NULL,
    PRIMARY KEY (tur_id),
    FOREIGN KEY (tsk_id) REFERENCES tasks (tsk_id)
);



CREATE TABLE chunks (
    -- inter-pausal units with acoustic-prosodic and lexical data
    -- "pause-free units of speech from a single speaker separated from one 
    --  another by at least 50ms" (Levitan and Hirschberg, 2011)
    chu_id            INTEGER NOT NULL,
    tur_id            INTEGER NOT NULL,
    chunk_index       INTEGER NOT NULL,
    start_time        NUMERIC,
    end_time          NUMERIC,
    -- duration redundant for consistency with games corpus structure
    duration          INTEGER,
    words             TEXT,
    pitch_min         NUMERIC,
    pitch_max         NUMERIC,
    pitch_mean        NUMERIC,
    pitch_std         NUMERIC,
    rate_syl          NUMERIC,
    rate_vcd          NUMERIC,
    intensity_min     NUMERIC,
    intensity_max     NUMERIC,
    intensity_mean    NUMERIC,
    intensity_std     NUMERIC,
    jitter            NUMERIC,
    shimmer           NUMERIC,
    nhr               NUMERIC,
    PRIMARY KEY (chu_id),
    FOREIGN KEY (tur_id) REFERENCES turns (tur_id)
);



CREATE UNIQUE INDEX top_pk ON topics (top_id);
CREATE UNIQUE INDEX spk_pk ON speakers (spk_id);
CREATE UNIQUE INDEX ses_pk ON sessions (ses_id);
CREATE INDEX ses_top_fk ON sessions (top_id);
CREATE INDEX ses_spk_a_fk ON sessions (spk_id_a);
CREATE INDEX ses_spk_b_fk ON sessions (spk_id_b);
CREATE UNIQUE INDEX tsk_pk ON tasks (tsk_id);
CREATE UNIQUE INDEX tsk_uk ON tasks (ses_id, task_index);
CREATE INDEX tsk_ses_fk ON tasks (ses_id);
CREATE UNIQUE INDEX tur_pk ON turns (tur_id);
CREATE UNIQUE INDEX tur_uk ON turns (tur_id, turn_index);
CREATE INDEX tur_tsk_fk ON turns (tsk_id);
CREATE UNIQUE INDEX chu_pk ON chunks (chu_id);
CREATE UNIQUE INDEX chu_uk ON chunks (chu_id, chunk_index);
CREATE INDEX chu_tur_fk ON chunks (tur_id);

