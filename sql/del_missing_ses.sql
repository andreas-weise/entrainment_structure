-- audio for a few switchboard sessions is missing; this deletes them
DELETE 
FROM   chunks 
WHERE  tur_id IN (
    SELECT tur_id 
    FROM turns 
    WHERE tsk_id IN (2289, 4361, 4379)
);

DELETE
FROM   turns
WHERE  tsk_id IN (2289, 4361, 4379);

DELETE
FROM   tasks
WHERE  tsk_id IN (2289, 4361, 4379);

DELETE
FROM   sessions
WHERE  ses_id IN (2289, 4361, 4379);

