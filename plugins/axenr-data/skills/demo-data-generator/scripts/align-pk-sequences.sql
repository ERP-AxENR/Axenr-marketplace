-- align-pk-sequences.sql — realigne les sequences PK Postgres en retard sur max(id).
--
-- Le correctif de la dimension 7e d'audit-completeness.sql, qui detecte le probleme.
-- Une sequence PK en retard fait echouer TOUTE creation d'enregistrement par le moteur
-- (REST comme UI) en `duplicate key ..._pkey`, avec un message trompeur qui annonce
-- « ne peut pas etre mis a jour » pour une creation et ne parle jamais de sequence.
--
-- Usage :
--   psql -d <base> -f align-pk-sequences.sql
--
-- Il affiche l'avant/apres et GENERE le SQL de retour arriere. Conserver cette sortie.
--
-- Innocuite : `setval(<seq>, max(id))` ne fait qu'AVANCER un compteur en retard. Il ne peut
-- pas provoquer de collision, meme sur une app en cours d'execution qui aurait pre-alloue un
-- bloc au-dessus de max(id) : ce cas n'est pas « en retard » et n'est pas touche.
--
-- `last_value` NULL = sequence JAMAIS appelee, donc `nextval` rendra 1. C'est le cas d'un jeu
-- seede en SQL avec des ids hauts et sans `setval` derriere — et aussi celui de l'import de
-- demo AOS sur ses tables de reference.
--
-- Balayage de 17 bases de demo le 2026-09-07 : 51 sequences realignees sur 5 de ces bases.

\set ON_ERROR_STOP on
\pset pager off
CREATE TEMP TABLE _seqfix(tbl text, seqname text, max_id bigint, avant text, apres bigint);
DO $$
DECLARE r record; mx bigint; lv bigint;
BEGIN
  FOR r IN SELECT c.table_name, s.sequencename FROM information_schema.columns c
            JOIN pg_sequences s ON s.schemaname='public' AND s.sequencename = c.table_name||'_seq'
           WHERE c.table_schema='public' AND c.column_name='id'
  LOOP
    EXECUTE format('SELECT max(id) FROM %I', r.table_name) INTO mx;
    SELECT last_value INTO lv FROM pg_sequences WHERE sequencename = r.sequencename;
    IF mx IS NOT NULL AND (lv IS NULL OR lv < mx) THEN
      INSERT INTO _seqfix VALUES (r.table_name, r.sequencename, mx, coalesce(lv::text,'NULL'), mx);
      EXECUTE format('SELECT setval(%L, %s)', r.sequencename, mx);
    END IF;
  END LOOP;
END $$;
SELECT tbl, seqname, avant AS avant, apres FROM _seqfix ORDER BY tbl;
\echo '-- retour arriere pour cette base :'
SELECT '  SELECT setval('''||seqname||''', '||avant||', false);' AS revert FROM _seqfix WHERE avant <> 'NULL' ORDER BY tbl;
SELECT '  -- '||seqname||' etait JAMAIS APPELEE (ALTER SEQUENCE '||seqname||' RESTART; pour y revenir)' AS revert FROM _seqfix WHERE avant = 'NULL' ORDER BY tbl;
SELECT count(*) AS realignees FROM _seqfix;
