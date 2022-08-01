DROP TABLE IF EXISTS chunks;
DROP TABLE IF EXISTS turns;
DROP TABLE IF EXISTS tasks;
DROP TABLE IF EXISTS sessions;
DROP TABLE IF EXISTS speakers;



CREATE TABLE speakers (
    spk_id    INTEGER NOT NULL,
    gender    TEXT NOT NULL,
    PRIMARY KEY (spk_id)
);



CREATE TABLE sessions (
    -- sessions between pairs of speakers
    ses_id      INTEGER NOT NULL,
    spk_id_a    INTEGER NOT NULL,
    spk_id_b    INTEGER NOT NULL,
    -- topic (never populated, only for consistency with switchboard corpus)
    top_id      INTEGER DEFAULT 0,
    -- unnecessary column, only for code consistency across corpora
    type        TEXT DEFAULT "GAME",
    PRIMARY KEY (ses_id),
    FOREIGN KEY (spk_id_a) REFERENCES speakers (spk_id),
    FOREIGN KEY (spk_id_b) REFERENCES speakers (spk_id)
);



CREATE TABLE tasks (
    -- tasks with mturk annotation data
    -- note: for each pair of opposing questions (yes/no; prefer speaker1/2)
    --       only one side is stored (yes; speaker1)
    --       other side = 5 - stored value (5 annotators, forced choice)
    --       also: speaker1 = describer, speaker2 = follower
    tsk_id                                                INTEGER NOT NULL,
    ses_id                                                INTEGER NOT NULL,
    task_index                                            INTEGER NOT NULL,
    -- who is describer for this task, a or b; other speaker is follower
    -- find specific speaker index in sessions table
    a_or_b                                                TEXT NOT NULL, 
    believes_is_better_than_partner_describer_yes         INTEGER NOT NULL,
    believes_is_better_than_partner_follower_yes          INTEGER NOT NULL,
    bored_with_game_describer_yes                         INTEGER NOT NULL,
    bored_with_game_follower_yes                          INTEGER NOT NULL,
    difficult_for_partner_to_speak_describer_yes          INTEGER NOT NULL,
    difficult_for_partner_to_speak_follower_yes           INTEGER NOT NULL,
    directs_the_conversation_describer_yes                INTEGER NOT NULL,
    directs_the_conversation_follower_yes                 INTEGER NOT NULL,
    contributes_to_successful_completion_describer_yes    INTEGER NOT NULL,
    contributes_to_successful_completion_follower_yes     INTEGER NOT NULL,
    frustrated_with_partner_describer_yes                 INTEGER NOT NULL,
    frustrated_with_partner_follower_yes                  INTEGER NOT NULL,
    frustrated_with_game_describer_yes                    INTEGER NOT NULL,
    frustrated_with_game_follower_yes                     INTEGER NOT NULL,
    engaged_in_game_describer_yes                         INTEGER NOT NULL,
    engaged_in_game_follower_yes                          INTEGER NOT NULL,
    gives_encouragement_describer_yes                     INTEGER NOT NULL,
    gives_encouragement_follower_yes                      INTEGER NOT NULL,
    making_self_clear_describer_yes                       INTEGER NOT NULL,
    making_self_clear_follower_yes                        INTEGER NOT NULL,
    planning_what_to_say_describer_yes                    INTEGER NOT NULL,
    planning_what_to_say_follower_yes                     INTEGER NOT NULL,
    polite_describer_yes                                  INTEGER NOT NULL,
    polite_follower_yes                                   INTEGER NOT NULL,
    dislikes_partner_describer_yes                        INTEGER NOT NULL,
    dislikes_partner_follower_yes                         INTEGER NOT NULL,
    trying_to_be_liked_describer_yes                      INTEGER NOT NULL,
    trying_to_be_liked_follower_yes                       INTEGER NOT NULL,
    trying_to_dominate_describer_yes                      INTEGER NOT NULL,
    trying_to_dominate_follower_yes                       INTEGER NOT NULL,
    conversation_awkward_yes                              INTEGER NOT NULL,
    flow_naturally_yes                                    INTEGER NOT NULL,
    hard_time_understanding_each_other_yes                INTEGER NOT NULL,
    like_more_describer                                   INTEGER NOT NULL,
    rather_have_as_a_partner_describer                    INTEGER NOT NULL,
    directing_the_conversation_describer                  INTEGER NOT NULL,
    dominates_the_conversation_describer                  INTEGER NOT NULL,
    likes_the_other_person_more_describer                 INTEGER NOT NULL,
    acting_superior_describer                             INTEGER NOT NULL,
    more_polite_describer                                 INTEGER NOT NULL,
    more_frustrated_describer                             INTEGER NOT NULL,
    PRIMARY KEY (tsk_id),
    FOREIGN KEY (ses_id) REFERENCES sessions (ses_id)
);



CREATE TABLE turns (
    -- turn = "maximal sequence of inter-pausal units from a single speaker"
    -- (Levitan and Hirschberg, 2011)
    tur_id            INTEGER NOT NULL,
    tsk_id            INTEGER NOT NULL,
    turn_type         TEXT NOT NULL,
    -- index of the turn within its task
    turn_index        INTEGER NOT NULL,
    -- index of the turn within its session
    turn_index_ses    INTEGER,
    -- whether "d"(escriber) or "f"(ollower) is speaking
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
    start_time        NUMERIC NOT NULL,
    end_time          NUMERIC NOT NULL,
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
    -- whether to include this chunk in the analysis, true by default 
    -- (intended to exclude utterances in woz sessions that are readings of 
    --  prompts for 50 percent or more of the syllables, but named generically 
    --  in case it is later needed for other reasons to exclude as well)
    do_include        NUMERIC DEFAULT 1,
    PRIMARY KEY (chu_id),
    FOREIGN KEY (tur_id) REFERENCES turns (tur_id)
);



CREATE UNIQUE INDEX spk_pk ON speakers (spk_id);
CREATE UNIQUE INDEX ses_pk ON sessions (ses_id);
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



--------------------------------------------------------------------------------
--------------------------------------------------------------------------------
--                      POPULATE TABLES FROM "BIG TABLE"                      --
--------------------------------------------------------------------------------
--------------------------------------------------------------------------------

INSERT INTO speakers
SELECT DISTINCT 
       speaker1_id spk_id, 
       speaker1_gender gender
FROM   _bt
UNION
SELECT DISTINCT 
       speaker2_id spk_id, 
       speaker2_gender gender
FROM   _bt
ORDER BY spk_id;



INSERT INTO sessions
SELECT DISTINCT 
       CAST(session_number AS INTEGER) ses_id, 
       speaker1_id spk_id_a,
       speaker2_id spk_id_b,
       -- unused, only for consistency with switchboard corpus
       0 top_id
FROM   _bt
WHERE  speaker1 == 'A'
AND    speaker2 == 'B'
ORDER BY ses_id;



INSERT INTO tasks (
    ses_id,
    task_index,
    a_or_b, 
    believes_is_better_than_partner_describer_yes,
    believes_is_better_than_partner_follower_yes,
    bored_with_game_describer_yes,
    bored_with_game_follower_yes,
    difficult_for_partner_to_speak_describer_yes,
    difficult_for_partner_to_speak_follower_yes,
    directs_the_conversation_describer_yes,
    directs_the_conversation_follower_yes,
    contributes_to_successful_completion_describer_yes,
    contributes_to_successful_completion_follower_yes,
    frustrated_with_partner_describer_yes,
    frustrated_with_partner_follower_yes,
    frustrated_with_game_describer_yes,
    frustrated_with_game_follower_yes,
    engaged_in_game_describer_yes,
    engaged_in_game_follower_yes,
    gives_encouragement_describer_yes,
    gives_encouragement_follower_yes,
    making_self_clear_describer_yes,
    making_self_clear_follower_yes,
    planning_what_to_say_describer_yes,
    planning_what_to_say_follower_yes,
    polite_describer_yes,
    polite_follower_yes,
    dislikes_partner_describer_yes,
    dislikes_partner_follower_yes,
    trying_to_be_liked_describer_yes,
    trying_to_be_liked_follower_yes,
    trying_to_dominate_describer_yes,
    trying_to_dominate_follower_yes,
    conversation_awkward_yes,
    flow_naturally_yes,
    hard_time_understanding_each_other_yes,
    like_more_describer,
    rather_have_as_a_partner_describer,
    directing_the_conversation_describer,
    dominates_the_conversation_describer,
    likes_the_other_person_more_describer,
    acting_superior_describer,
    more_polite_describer,
    more_frustrated_describer
)
SELECT DISTINCT 
       CAST(session_number AS INTEGER) ses_id,
       CAST(SUBSTR(mturk_hitid, INSTR(mturk_hitid, 't') + 1) AS NUMERIC) task_index,
       speaker1 a_or_b,
       believes_is_better_than_partner_speaker1_yes,
       believes_is_better_than_partner_speaker2_yes,
       bored_with_game_speaker1_yes,
       bored_with_game_speaker2_yes,
       difficult_for_partner_to_speak_speaker1_yes,
       difficult_for_partner_to_speak_speaker2_yes,
       directs_the_conversation_speaker1_yes,
       directs_the_conversation_speaker2_yes,
       contributes_to_successful_completion_speaker1_yes,
       contributes_to_successful_completion_speaker2_yes,
       frustrated_with_partner_speaker1_yes,
       frustrated_with_partner_speaker2_yes,
       frustrated_with_game_speaker1_yes,
       frustrated_with_game_speaker2_yes,
       engaged_in_game_speaker1_yes,
       engaged_in_game_speaker2_yes,
       gives_encouragement_speaker1_yes,
       gives_encouragement_speaker2_yes,
       making_self_clear_speaker1_yes,
       making_self_clear_speaker2_yes,
       planning_what_to_say_speaker1_yes,
       planning_what_to_say_speaker2_yes,
       polite_speaker1_yes,
       polite_speaker2_yes,
       dislikes_partner_speaker1_yes,
       dislikes_partner_speaker2_yes,
       trying_to_be_liked_speaker1_yes,
       trying_to_be_liked_speaker2_yes,
       trying_to_dominate_speaker1_yes,
       trying_to_dominate_speaker2_yes,
       conversation_awkward_yes,
       flow_naturally_yes,
       hard_time_understanding_each_other_yes,
       like_more_speaker1,
       rather_have_as_a_partner_speaker1,
       directing_the_conversation_speaker1,
       dominates_the_conversation_speaker1,
       likes_the_other_person_more_speaker1,
       acting_superior_speaker1,
       more_polite_speaker1,
       more_frustrated_speaker1
FROM   _bt
WHERE  speaker1_role == 'd'
ORDER BY ses_id, task_index;



INSERT INTO turns (
    tsk_id,
    turn_type,
    turn_index,
    speaker_role
)
SELECT DISTINCT
       tsk.tsk_id tsk_id,
       bt.tt_label turn_type,
       CAST(bt.turn_number_in_task AS NUMERIC) turn_index,
       bt.speaker1_role speaker_role
FROM   _bt bt
JOIN   tasks tsk
ON     bt.mturk_hitid == 'g' || tsk.ses_id || 't' || tsk.task_index
ORDER BY tsk_id, turn_index;



UPDATE turns
SET turn_index_ses = (
    SELECT COUNT(tur2.tur_id) + 1 
    FROM   turns tur2
    JOIN   tasks tsk2
    ON     tur2.tsk_id == tsk2.tsk_id
    WHERE  tsk2.ses_id = (
        SELECT ses_id FROM tasks WHERE tsk_id = turns.tsk_id
    )
	-- assumes that tsk_id is sorted by task_index within ses_id
	AND   (   tur2.tsk_id < turns.tsk_id
	       OR (    tur2.tsk_id = turns.tsk_id 
               AND tur2.turn_index < turns.turn_index
           )
	)
);



INSERT INTO chunks (
    tur_id,
    chunk_index,
    duration,
    start_time,
    end_time,
    words
)
SELECT tur_id,
       chunk_number_in_turn chunk_index,
       chunk_duration / 1000.0 duration,
       CAST(SUBSTR(token_id, 17) AS NUMERIC) start_time, 
       CAST(SUBSTR(token_id, 17) AS NUMERIC) + chunk_duration / 1000.0 end_time,
       chunk_words words
FROM   _bt
JOIN  (
       SELECT tur.tur_id,
              tur.turn_index,
              tsk.task_index,
              tsk.ses_id
       FROM   turns tur
       JOIN   tasks tsk
       ON     tur.tsk_id == tsk.tsk_id
      ) tur
ON     CAST(session_number AS INTEGER) == tur.ses_id
AND    SUBSTR(_bt.mturk_hitid, INSTR(_bt.mturk_hitid, 't') + 1) == tur.task_index
AND    _bt.turn_number_in_task == tur.turn_index
ORDER BY tur_id, start_time;



