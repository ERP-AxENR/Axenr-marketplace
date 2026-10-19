-- Audit de complétude d'un jeu de données de démo — 13 dimensions.
--
-- Pourquoi : un audit qui ne teste que les NULL laisse passer l'essentiel. Sur un chantier réel,
-- un rapport « 16 tables / 0 anomalie » a été suivi de 20+ défauts trouvés à l'œil par l'utilisateur.
--
-- Usage :
--   psql -h <hôte> -U <utilisateur> -d <base> -v tag=DEMO-XXX-2026 -f audit-completeness.sql
--
--   psql … -v tag=DEMO-XXX-2026 -f audit-completeness.sql 2>&1 | tee audit.txt
--   grep -c '^psql:.*ERROR:' audit.txt    # 0 attendu — chaque ligne = un contrôle SAUTÉ
--
-- Le paramètre :tag est la valeur d'import_origin posée sur les lignes créées.
-- Les dimensions 3 (cohérence inter-champs) et 6 (visibilité écran) ne sont pas automatisables
-- de façon générique : elles sont rappelées en fin de sortie comme checklist manuelle.

\pset pager off
\set ON_ERROR_STOP on
SELECT set_config('demo.tag', :'tag', false);

\echo ''
\echo '════════════════════════════════════════════════════════════'
\echo '  AUDIT DE COMPLÉTUDE — tag :tag'
\echo '════════════════════════════════════════════════════════════'

-- Tables portant le tag
DROP TABLE IF EXISTS _tagged;
CREATE TEMP TABLE _tagged(tbl text, lignes bigint);
DO $$
DECLARE r record; n bigint;
BEGIN
  FOR r IN
    SELECT c.table_name FROM information_schema.columns c
    WHERE c.column_name='import_origin' AND c.table_schema='public'
  LOOP
    BEGIN
      EXECUTE format('SELECT count(*) FROM %I WHERE import_origin = %L', r.table_name, current_setting('demo.tag')) INTO n;
      IF n > 0 THEN INSERT INTO _tagged VALUES (r.table_name, n); END IF;
    EXCEPTION WHEN OTHERS THEN NULL;
    END;
  END LOOP;
END $$;

\echo ''
\echo '── Périmètre : tables alimentées sous ce tag ────────────────'
SELECT tbl AS table_name, lignes FROM _tagged ORDER BY lignes DESC, tbl;

\set ON_ERROR_STOP off
-- ─────────────────────────────────────────────────────────────────────────────
-- DIMENSION 13 — invariants métier à cliquet  (ajoutée le 2026-09-23, retex d'une démo industrielle)
--
-- Pourquoi : les dimensions 1-9 ne voient que les lignes CRÉÉES sous :tag. Les trois défauts les plus
-- coûteux de la préparation d'une démo industrielle étaient des MISES À JOUR de lignes préexistantes, invisibles par
-- construction. Rejoué le 2026-09-23 sur le dump <base>-avant-harmonisation-20260922T2327 :
-- G1=40, G2=350, G3=145 (sur 159) ; sur la base corrigée : 0 / 0 / 0.
--
-- Pourquoi un CLIQUET et pas un RAISE NOTICE de plus : un avis de plus parmi 53 ne se lit pas.
-- 1er passage sur une base : les compteurs sont ENREGISTRÉS dans public.zz_audit_invariants, défauts
-- compris — d'où : lancer l'audit une fois AVANT la première écriture.
-- Passages suivants : un compteur qui MONTE lève une exception, soit UNE ligne « ERROR » (comptée par le
-- grep de fin) ; ON_ERROR_STOP étant off ici, l'audit continue et psql sort à 0 — ce n'est pas un échec
-- dur (vérifié le 2026-09-24). Il mord sur ce qu'on introduit sans bloquer sur les défauts hérités. Un
-- compteur qui baisse abaisse la référence.
-- Remise à zéro volontaire : DELETE FROM zz_audit_invariants WHERE code = 'G…';
--
-- Placée AVANT la garde « PÉRIMÈTRE VIDE » : une session qui ne fait que des UPDATE n'a aucune ligne
-- taguée, et la garde (ON_ERROR_STOP on) arrêtait l'audit avant ce contrôle — c'est ce qui s'est
-- produit la nuit du 22/09 (« PÉRIMÈTRE VIDE » deux fois).
-- Chaque contrôle affiche sa PORTÉE : un 0 sur une portée nulle ne prouve rien.
-- Formules : SaleOrderLineProductServiceImpl.fillCostPrice (l.168-192), MarginComputeServiceImpl
-- .computeSubMargin (l.68-103), SaleOrderMarginServiceImpl.computeMarginSaleOrder (l.56-82).
--
-- G4 à G9 (ajoutés le 2026-09-24, retex d'une démo industrielle, nuit du 23 au 24/09 — pièges 143 à 147) : un historique posé
-- en SQL portait des états sans leur transition. Mesuré sur <base> : G4 achats reçus sans mouvement
-- 27 (lot) contre 0 sur 6 natifs, G5 ventes livrées sans mouvement 7 contre 0 sur 7, G6 OF planifiés,
-- démarrés ou terminés sans consommation 42 (les 40 du lot et 2 OF posés en SQL) contre 0 sur 244 natifs ;
-- avant correction, G7 pointages d'OF portant l'affaire 128 (0 sur 363 natifs), G8 tâches sans priorité
-- 61, G9 affaires gérées par projet sans statuts de tâche 10 (0 sur les 26 autres non archivées).
-- Toute référence non nulle sur G4-G7 et G9 est un signal à qualifier (nuls sur les pièces natives de la démo).
\echo ''
\echo '── DIMENSION 13 — invariants métier à cliquet (toute la base, pas :tag) ─'
CREATE TABLE IF NOT EXISTS public.zz_audit_invariants(
  code text PRIMARY KEY, libelle text, anomalies bigint, portee bigint, maj timestamptz DEFAULT now());
DO $$
DECLARE r record; ref bigint; hausse text := ''; cout_par_societe boolean := false;
BEGIN
  DROP TABLE IF EXISTS _inv;
  CREATE TEMP TABLE _inv(code text, libelle text, anomalies bigint, portee bigint);
  IF to_regclass('public.sale_sale_order') IS NOT NULL THEN
    -- G1 : marge d'en-tête = CA comptabilisé − coût (commandes en devise société, hors archivées)
    INSERT INTO _inv SELECT 'G1', 'marge commande <> CA comptabilisé - coût',
      count(*) FILTER (WHERE abs(coalesce(o.total_gross_margin,0)
                                 - (coalesce(o.accounted_revenue,0) - coalesce(o.total_cost_price,0))) > 0.05),
      count(*)
    FROM sale_sale_order o
    WHERE o.archived IS NOT TRUE AND coalesce(o.ex_tax_total,0) <> 0
      AND o.currency = (SELECT c.currency FROM base_company c WHERE c.id = o.company);
    -- G2 : coût de ligne = quantité × prix de revient article. Exclus : coût saisi à la main (natif),
    -- article sans prix de revient (fillCostPrice n'écrit rien), lignes titre/pack, devise étrangère.
    -- Option « produits par société » (piège 197) : si costPrice est un champ par société, le prix qui fait
    -- foi est celui de la ligne de la société de la commande (faux positifs sinon : 3 lignes de l'essai 1 du
    -- 27/09, coût de la filiale 131 € contre 146 € au niveau de l'article ; 0 avec cette correction). Cette
    -- formule-là prend le code G2b, pour que le cliquet reparte d'une référence neuve (piège 188) ; sur une
    -- base où l'option est active, la ligne G2 de zz_audit_invariants reste alors orpheline (la supprimer
    -- est facultatif). Sans l'option, la formule et le code G2 sont inchangés.
    IF to_regclass('public.studio_app_base_company_specific_product_fields_set') IS NOT NULL
       AND (SELECT count(*) FROM information_schema.columns WHERE table_schema = 'public'
            AND ((table_name = 'base_product' AND column_name IN ('dtype', 'product', 'company'))
              OR (table_name = 'studio_app_base_company_specific_product_fields_set'
                  AND column_name = 'company_specific_product_fields_set'))) = 4 THEN
      SELECT EXISTS (SELECT 1 FROM studio_app_base_company_specific_product_fields_set s
                     JOIN meta_field mf ON mf.id = s.company_specific_product_fields_set
                     WHERE mf.name = 'costPrice') INTO cout_par_societe;
    END IF;
    IF cout_par_societe THEN
      INSERT INTO _inv SELECT 'G2b', 'coût de revient de ligne <> qté x prix de revient (article ou ligne par société)',
        count(*) FILTER (WHERE abs(coalesce(l.sub_total_cost_price,0) - l.qty * coalesce(
          (SELECT pc.cost_price FROM base_product pc WHERE pc.dtype = 'ProductCompany'
             AND pc.product = p.id AND pc.company = o.company ORDER BY pc.id LIMIT 1), p.cost_price)) > 0.05),
        count(*)
      FROM sale_sale_order_line l
      JOIN sale_sale_order o ON o.id = l.sale_order
      JOIN base_product p ON p.id = l.product
      WHERE l.archived IS NOT TRUE AND o.archived IS NOT TRUE
        AND l.is_sub_total_cost_price_manually_edited IS NOT TRUE
        AND coalesce(l.type_select,0) = 0
        AND coalesce((SELECT pc.cost_price FROM base_product pc WHERE pc.dtype = 'ProductCompany'
             AND pc.product = p.id AND pc.company = o.company ORDER BY pc.id LIMIT 1), p.cost_price, 0) <> 0
        AND o.currency = (SELECT c.currency FROM base_company c WHERE c.id = o.company);
    ELSE
      INSERT INTO _inv SELECT 'G2', 'coût de revient de ligne <> qté x prix de revient article',
        count(*) FILTER (WHERE abs(coalesce(l.sub_total_cost_price,0) - l.qty * p.cost_price) > 0.05),
        count(*)
      FROM sale_sale_order_line l
      JOIN sale_sale_order o ON o.id = l.sale_order
      JOIN base_product p ON p.id = l.product
      WHERE l.archived IS NOT TRUE AND o.archived IS NOT TRUE
        AND l.is_sub_total_cost_price_manually_edited IS NOT TRUE
        AND coalesce(l.type_select,0) = 0 AND coalesce(p.cost_price,0) <> 0
        AND o.currency = (SELECT c.currency FROM base_company c WHERE c.id = o.company);
    END IF;
  END IF;
  IF to_regclass('public.production_manuf_order') IS NOT NULL
     AND to_regclass('public.production_production_order') IS NOT NULL THEN
    -- G3 : l'article d'un ordre est vendu par son affaire, en direct ou comme composant de niveau 1
    INSERT INTO _inv SELECT 'G3', 'ordre de fabrication : article non vendu par son affaire',
      count(*) FILTER (WHERE NOT EXISTS (
        SELECT 1 FROM sale_sale_order_line l
        WHERE l.project = po.project AND l.archived IS NOT TRUE
          AND (l.product = mo.product OR EXISTS (
                SELECT 1 FROM base_product sp
                JOIN production_bill_of_material_line bl ON bl.bill_of_material_parent = sp.default_bill_of_material
                WHERE sp.id = l.product AND bl.product = mo.product)))),
      count(*)
    FROM production_manuf_order mo
    JOIN production_manuf_order_production_order_set s ON s.manuf_order_set = mo.id
    JOIN production_production_order po ON po.id = s.production_order_set
    WHERE mo.archived IS NOT TRUE AND po.project IS NOT NULL;
  END IF;
  -- G4/G5 : stock_stock_move_line.purchase_order_line / .sale_order_line et sale_sale_order.delivery_state
  -- viennent du module Supply chain (StockMoveLine.xml l.10-17, SaleOrder.xml l.15, 9.1.3) : sans lui,
  -- l'instruction échouerait et emporterait tout le bloc G1-G9.
  IF to_regclass('public.purchase_purchase_order') IS NOT NULL
     AND EXISTS (SELECT 1 FROM information_schema.columns
                  WHERE table_schema = 'public' AND table_name = 'stock_stock_move_line' AND column_name = 'purchase_order_line') THEN
    -- G4 : commande fournisseur reçue ou partiellement reçue sans AUCUNE ligne de mouvement (piège 143)
    INSERT INTO _inv SELECT 'G4', 'achat reçu ou partiel sans mouvement de stock',
      count(*) FILTER (WHERE NOT EXISTS (
        SELECT 1 FROM purchase_purchase_order_line ol JOIN stock_stock_move_line sml ON sml.purchase_order_line = ol.id
         WHERE ol.purchase_order = po.id)),
      count(*)
    FROM purchase_purchase_order po WHERE po.receipt_state IN (2, 3) AND po.archived IS NOT TRUE;
  END IF;
  IF EXISTS (SELECT 1 FROM information_schema.columns
              WHERE table_schema = 'public' AND table_name = 'sale_sale_order' AND column_name = 'delivery_state')
     AND EXISTS (SELECT 1 FROM information_schema.columns
                  WHERE table_schema = 'public' AND table_name = 'stock_stock_move_line' AND column_name = 'sale_order_line') THEN
    -- G5 : commande client livrée ou partiellement livrée sans AUCUNE ligne de mouvement (piège 143)
    INSERT INTO _inv SELECT 'G5', 'vente livrée ou partielle sans mouvement de stock',
      count(*) FILTER (WHERE NOT EXISTS (
        SELECT 1 FROM sale_sale_order_line sl JOIN stock_stock_move_line sml ON sml.sale_order_line = sl.id
         WHERE sl.sale_order = so.id)),
      count(*)
    FROM sale_sale_order so WHERE so.delivery_state IN (2, 3) AND so.archived IS NOT TRUE;
  END IF;
  IF to_regclass('public.production_manuf_order') IS NOT NULL AND to_regclass('public.stock_stock_move_line') IS NOT NULL THEN
    -- G6 : OF planifié, démarré, en pause ou terminé sans AUCUNE ligne de consommation (piège 143). La
    -- planification crée déjà les mouvements (ManufOrderPlanServiceImpl l.186-223, 9.1.3) ; un OF à
    -- consommation par opération les porte sur l'opération, pas sur l'OF (l.201 ;
    -- OperationOrderStockMoveServiceImpl l.141 : consumed_operation_order).
    INSERT INTO _inv SELECT 'G6', 'OF planifié, démarré ou terminé sans mouvement de consommation',
      count(*) FILTER (WHERE NOT EXISTS (SELECT 1 FROM stock_stock_move_line sml WHERE sml.consumed_manuf_order = mo.id)
                         AND NOT EXISTS (SELECT 1 FROM stock_stock_move_line sml
                                           JOIN production_operation_order oo ON oo.id = sml.consumed_operation_order
                                          WHERE oo.manuf_order = mo.id)),
      count(*)
    FROM production_manuf_order mo WHERE mo.status_select IN (3, 4, 5, 6) AND mo.archived IS NOT TRUE;
  END IF;
  IF EXISTS (SELECT 1 FROM information_schema.columns
              WHERE table_schema = 'public' AND table_name = 'hr_timesheet_line' AND column_name = 'manuf_order') THEN
    -- G7 : pointage sur OF portant aussi une affaire — le pointage créé depuis l'OF n'en pose pas (piège 144)
    INSERT INTO _inv SELECT 'G7', 'pointage sur OF portant une affaire (le natif n''en porte pas)',
      count(*) FILTER (WHERE tl.project IS NOT NULL), count(*)
    FROM hr_timesheet_line tl WHERE tl.manuf_order IS NOT NULL AND tl.archived IS NOT TRUE;
  END IF;
  IF to_regclass('public.project_project_task') IS NOT NULL THEN
    -- G8 : tâche sans priorité — obligatoire au formulaire, nullable en base (piège 147)
    INSERT INTO _inv SELECT 'G8', 'tâche sans priorité (bloque l''enregistrement si le projet affiche les priorités)',
      count(*) FILTER (WHERE t.priority IS NULL), count(*)
    FROM project_project_task t WHERE t.archived IS NOT TRUE;
  END IF;
  IF to_regclass('public.project_project_project_task_status_set') IS NOT NULL
     AND EXISTS (SELECT 1 FROM information_schema.columns
                  WHERE table_schema = 'public' AND table_name = 'project_project' AND column_name = 'task_status_management_select') THEN
    -- G9 : affaire à statuts de tâche gérés par projet, sans aucun statut lié (piège 145)
    INSERT INTO _inv SELECT 'G9', 'affaire à statuts gérés par projet sans statut de tâche',
      count(*) FILTER (WHERE NOT EXISTS (SELECT 1 FROM project_project_project_task_status_set j WHERE j.project_project = p.id)),
      count(*)
    FROM project_project p WHERE p.task_status_management_select = 2 AND p.archived IS NOT TRUE;
  END IF;
  FOR r IN SELECT * FROM _inv ORDER BY code LOOP
    SELECT anomalies INTO ref FROM public.zz_audit_invariants WHERE code = r.code;
    IF ref IS NULL THEN
      INSERT INTO public.zz_audit_invariants(code, libelle, anomalies, portee) VALUES (r.code, r.libelle, r.anomalies, r.portee);
      RAISE NOTICE '  % : % anomalie(s) sur une portée de % — RÉFÉRENCE ENREGISTRÉE (1er passage)', r.code, r.anomalies, r.portee;
    ELSIF r.anomalies > ref THEN
      hausse := hausse || format(' %s %s→%s (portée %s) ;', r.code, ref, r.anomalies, r.portee);
      RAISE NOTICE '  % : % anomalie(s) sur une portée de % — HAUSSE (référence %) : %', r.code, r.anomalies, r.portee, ref, r.libelle;
    ELSE
      UPDATE public.zz_audit_invariants SET anomalies = r.anomalies, portee = r.portee, maj = now() WHERE code = r.code;
      RAISE NOTICE '  % : % anomalie(s) sur une portée de % (référence %)%', r.code, r.anomalies, r.portee, ref,
        CASE WHEN r.portee = 0 THEN ' — PORTÉE NULLE : le 0 ne prouve rien' ELSE '' END;
    END IF;
  END LOOP;
  IF hausse <> '' THEN
    RAISE EXCEPTION 'DIMENSION 13 : invariant(s) métier dégradé(s) par rapport à la référence :% — une écriture a introduit des incohérences sur des lignes existantes', hausse;
  END IF;
END $$;
\set ON_ERROR_STOP on

-- GARDE (piège 107, methode-audit.md) : un périmètre vide ne veut PAS dire "rien à peupler" --
-- ça veut dire, le plus souvent, "le tag n'a pas été posé à l'écriture". Faire échouer plutôt que
-- rendre les dimensions vertes sur un périmètre nul. Testé le 2026-09-08 sur <base> :
-- passe avec -v tag=<tag>, lève avec un tag inexistant.
DO $$
BEGIN
  IF (SELECT count(*) FROM _tagged) = 0 THEN
    RAISE EXCEPTION 'PERIMETRE VIDE : aucune table ne porte import_origin = %. L''audit ne peut rien mesurer -- verifier que le tag a bien ete pose a l''ecriture (piege 107), pas que la base est vide.', current_setting('demo.tag');
  END IF;
END $$;

-- À partir d'ici, les contrôles ne doivent PLUS interrompre l'audit. Constaté le 2026-09-04 :
-- une colonne absente du schéma (`project_project_planning_time.title`, absent sur 2 des 16 bases
-- du parc — c'est le MODULE installé qui décide, pas la version d'AOS) faisait échouer la
-- dimension 7, et `ON_ERROR_STOP on` emportait les dimensions 8 à 11 sans le dire. Un contrôle
-- inapplicable doit se signaler et laisser passer les suivants.
\set ON_ERROR_STOP off

\echo ''
\echo '── DIMENSION 1 : booléens NULL (exclus des grids et pickers) ─'
DO $$
DECLARE r record; c record; n bigint; total int := 0;
BEGIN
  FOR r IN SELECT tbl FROM _tagged LOOP
    FOR c IN SELECT column_name FROM information_schema.columns
             WHERE table_name=r.tbl AND data_type='boolean' AND column_name <> 'archived'
    LOOP
      EXECUTE format('SELECT count(*) FROM %I WHERE import_origin=%L AND %I IS NULL', r.tbl, current_setting('demo.tag'), c.column_name) INTO n;
      IF n > 0 THEN
        RAISE NOTICE '  % . % → % ligne(s) à NULL', r.tbl, c.column_name, n;
        total := total + 1;
      END IF;
    END LOOP;
  END LOOP;
  IF total = 0 THEN RAISE NOTICE '  aucun booléen NULL'; END IF;
END $$;

\echo ''
\echo '── DIMENSION 1bis : sélections NULL (invisibles en UI) ───────'
DO $$
DECLARE r record; c record; n bigint; total int := 0;
BEGIN
  FOR r IN SELECT tbl FROM _tagged LOOP
    FOR c IN SELECT column_name FROM information_schema.columns
             WHERE table_name=r.tbl AND column_name LIKE '%\_select' AND data_type IN ('integer','character varying')
    LOOP
      EXECUTE format('SELECT count(*) FROM %I WHERE import_origin=%L AND %I IS NULL', r.tbl, current_setting('demo.tag'), c.column_name) INTO n;
      IF n > 0 THEN
        RAISE NOTICE '  % . % → % ligne(s) à NULL', r.tbl, c.column_name, n;
        total := total + 1;
      END IF;
    END LOOP;
  END LOOP;
  IF total = 0 THEN RAISE NOTICE '  aucune sélection NULL'; END IF;
END $$;

\echo ''
\echo '── DIMENSION 2 : ZÉROS et chaînes vides (count() les compte  ─'
\echo '                comme « rempli » — c''est le piège n°1)       '
DO $$
DECLARE r record; c record; n bigint; tot bigint; total int := 0;
BEGIN
  FOR r IN SELECT tbl, lignes FROM _tagged LOOP
    -- numériques intégralement à zéro
    FOR c IN SELECT column_name FROM information_schema.columns
             WHERE table_name=r.tbl AND data_type IN ('numeric','integer','bigint','double precision')
               AND column_name NOT IN ('id','version') AND column_name NOT LIKE '%\_select'
    LOOP
      EXECUTE format('SELECT count(*) FROM %I WHERE import_origin=%L AND %I = 0', r.tbl, current_setting('demo.tag'), c.column_name) INTO n;
      IF n > 0 AND n = r.lignes THEN
        RAISE NOTICE '  % . % → TOUTES les % lignes à 0', r.tbl, c.column_name, n;
        total := total + 1;
      END IF;
    END LOOP;
    -- textes intégralement vides
    FOR c IN SELECT column_name FROM information_schema.columns
             WHERE table_name=r.tbl AND data_type IN ('character varying','text')
               AND column_name NOT IN ('import_origin','import_id','process_instance_id')
    LOOP
      EXECUTE format('SELECT count(*) FROM %I WHERE import_origin=%L AND (%I = '''' )', r.tbl, current_setting('demo.tag'), c.column_name) INTO n;
      IF n > 0 THEN
        RAISE NOTICE '  % . % → % ligne(s) à chaîne vide', r.tbl, c.column_name, n;
        total := total + 1;
      END IF;
    END LOOP;
  END LOOP;
  IF total = 0 THEN RAISE NOTICE '  aucune colonne intégralement à zéro / vide'; END IF;
END $$;

\echo ''
\echo '── DIMENSION 4 : UNICITÉ — copier-coller entre enregistrements '
DO $$
DECLARE r record; c record; nd bigint; total int := 0;
BEGIN
  FOR r IN SELECT tbl, lignes FROM _tagged WHERE lignes >= 4 LOOP
    FOR c IN SELECT column_name FROM information_schema.columns
             WHERE table_name=r.tbl AND data_type IN ('character varying','text')
               AND column_name NOT IN ('import_origin','import_id','process_instance_id')
    LOOP
      EXECUTE format('SELECT count(DISTINCT %I) FROM %I WHERE import_origin=%L AND %I IS NOT NULL',
                     c.column_name, r.tbl, current_setting('demo.tag'), c.column_name) INTO nd;
      IF nd = 1 AND r.lignes >= 6 THEN
        RAISE NOTICE '  % . % → une SEULE valeur distincte sur % lignes (copier-coller ?)', r.tbl, c.column_name, r.lignes;
        total := total + 1;
      END IF;
    END LOOP;
  END LOOP;
  IF total = 0 THEN RAISE NOTICE '  aucune colonne texte uniforme suspecte'; END IF;
END $$;

\echo ''
\echo '── DIMENSION 4bis : TEXTES RÉPÉTÉS — la même phrase sur plusieurs lignes (règle 2) ─'
\echo '   (commentaire ou note recopié : pire qu’un vide ; description du modèle sur ses variantes).'
\echo '   À qualifier : une mention réglementaire commune (norme, éco-contribution) peut être légitime.'
\echo '   Mesuré le 27/09 : retrouve les gabarits notés bloquants à l’aveugle aux essais 0, 1 et 2.'
DO $$
DECLARE r record; c record; v record; total int := 0;
BEGIN
  -- Fiches saisies seulement (tiers, contacts, articles) : les pièces recopient ces textes par conception.
  FOR r IN SELECT tbl, lignes FROM _tagged WHERE lignes >= 2 AND tbl IN ('base_partner', 'base_product') LOOP
    FOR c IN SELECT column_name FROM information_schema.columns
             WHERE table_name=r.tbl AND data_type IN ('character varying','text')
               AND column_name NOT IN ('import_origin','import_id','process_instance_id')
    LOOP
      FOR v IN EXECUTE format(
        'SELECT left(%1$I, 70) AS extrait, count(*) AS n FROM %2$I WHERE import_origin=%3$L %4$s'
        'AND length(%1$I) >= 30 AND %1$I LIKE ''%% %%'' GROUP BY %1$I HAVING count(*) >= 2 '
        'ORDER BY count(*) DESC LIMIT 3', c.column_name, r.tbl, current_setting('demo.tag'),
        CASE WHEN r.tbl = 'base_product' THEN 'AND dtype = ''Product'' ' ELSE '' END)
      LOOP
        RAISE NOTICE '  % . % → la même phrase sur % lignes : « % »', r.tbl, c.column_name, v.n, v.extrait;
        total := total + 1;
      END LOOP;
    END LOOP;
  END LOOP;
  IF total = 0 THEN RAISE NOTICE '  aucune phrase répétée sur les lignes taguées'; END IF;
END $$;

\echo ''
\echo '── DIMENSION 5 : RELATIONS — FK obligatoires laissées à NULL ─'
\echo '   (une sous-requête sans résultat écrit NULL EN SILENCE)     '
DO $$
DECLARE r record; f record; n bigint; total int := 0;
BEGIN
  FOR r IN SELECT tbl FROM _tagged LOOP
    FOR f IN
      SELECT a.attname AS col FROM pg_constraint cf
      JOIN pg_attribute a ON a.attrelid=cf.conrelid AND a.attnum=ANY(cf.conkey)
      WHERE cf.contype='f' AND cf.conrelid = r.tbl::regclass
        AND a.attname NOT IN ('created_by','updated_by')
    LOOP
      EXECUTE format('SELECT count(*) FROM %I WHERE import_origin=%L AND %I IS NULL', r.tbl, current_setting('demo.tag'), f.col) INTO n;
      IF n > 0 THEN
        RAISE NOTICE '  % . % → % ligne(s) sans référence (à justifier ou combler)', r.tbl, f.col, n;
        total := total + 1;
      END IF;
    END LOOP;
  END LOOP;
  IF total = 0 THEN RAISE NOTICE '  toutes les FK sont résolues'; END IF;
END $$;

\echo ''
\echo '── DIMENSION 5bis : SATELLITES — headers sans enfants ────────'
DO $$
DECLARE r record; e record; n bigint; total int := 0;
BEGIN
  FOR r IN SELECT tbl FROM _tagged LOOP
    FOR e IN
      SELECT cf.conrelid::regclass::text AS enfant, a.attname AS col
      FROM pg_constraint cf
      JOIN pg_attribute a ON a.attrelid=cf.conrelid AND a.attnum=ANY(cf.conkey)
      WHERE cf.contype='f' AND cf.confrelid = r.tbl::regclass
    LOOP
      EXECUTE format('SELECT count(*) FROM %I p WHERE p.import_origin=%L AND NOT EXISTS (SELECT 1 FROM %s e WHERE e.%I = p.id)',
                     r.tbl, current_setting('demo.tag'), e.enfant, e.col) INTO n;
      IF n > 0 THEN
        RAISE NOTICE '  % → % ligne(s) sans aucun %', r.tbl, n, e.enfant;
        total := total + 1;
      END IF;
    END LOOP;
  END LOOP;
  IF total = 0 THEN RAISE NOTICE '  aucun header orphelin'; END IF;
END $$;

\echo ''
\echo '════════════════════════════════════════════════════════════'
\echo '  À VÉRIFIER À LA MAIN (non automatisable)'
\echo '════════════════════════════════════════════════════════════'
\echo '  DIMENSION 3 — cohérence inter-champs :'
\echo '     code NAF ↔ secteur d''activité · secteur ↔ parcours ·'
\echo '     libellé géographique ↔ adresses · description ↔ classification'
\echo '     + un attribut porté par l''enregistrement ET son parent'
\echo '       (address.country vs address.city.country)'
\echo ''
\echo '  DIMENSION 6 — visibilité écran (IRREMPLAÇABLE) :'
\echo '     ouvrir les écrans concernés. Les dashlets filtrent sur'
\echo '     statut, project au niveau LIGNE, utilisateur courant,'
\echo '     dates récentes, flags App* → une table pleine peut'
\echo '     donner un écran vide.'
\echo '     Attention : si l''application tourne, le cache Hibernate masque'
\echo '        les UPDATE SQL → redémarrer avant de conclure.'
\echo ''

-- ════════════════════════════════════════════════════════════════════════════
-- DIMENSION 7 — champs DÉRIVÉS désynchronisés  (ajoutée le 2026-08-11)
-- ════════════════════════════════════════════════════════════════════════════
-- Pourquoi mécanique et non documentaire : les règles cardinales 5 (« fullName ne se calcule pas
-- en SQL ») et 9 (« count() compte les zéros comme remplis ») étaient DÉJÀ écrites dans le skill,
-- et ont été violées quand même — trois fois pour la première. La prose n'a pas mordu ; ces
-- requêtes-ci le feront. Un champ dérivé ne lève jamais d'erreur : il fausse un écran en silence.

\echo ''
\echo '── DIMENSION 7 — champs dérivés désynchronisés ──────────────'

-- 7a. full_name qui ne suit plus son nom.
--
-- UNE SEULE FORMULE pour tous les tiers — organisations comme personnes. Une première version
-- branchait sur `is_contact` et signalait 5 faux positifs : des personnes physiques non marquées
-- contact, dont le full_name inclut légitimement le prénom. Le discriminant n'est ni `is_contact`
-- ni `partner_type_select`, c'est simplement que **les sociétés n'ont pas de prénom**, donc le
-- COALESCE ne concatène rien pour elles. Vérifié : la formule unique couvre 105 des 106 tiers.
-- Un contrôle par instruction, jamais d'`UNION ALL` entre deux tables : une colonne absente
-- ferait tomber tous les membres du même coup (cf. le commentaire sur ON_ERROR_STOP ci-dessus).
SELECT 'base_partner' AS entite, count(*) AS desynchronises
  FROM base_partner
 WHERE COALESCE(partner_seq,'') <> ''
   AND full_name IS DISTINCT FROM partner_seq || ' - ' || name
       || COALESCE(' ' || NULLIF(btrim(first_name), ''), '');

SELECT 'project_project' AS entite, count(*) AS desynchronises
  FROM project_project WHERE code IS NOT NULL
   AND full_name IS DISTINCT FROM code || ' - ' || name;

-- 7a-bis. La cascade AU-DELÀ du premier niveau (ajouté le 2026-08-11, cf. piège 92).
--
-- Ces contrôles manquaient, et leur absence a laissé vivre un vocabulaire périmé sur 190 tâches,
-- 270 titres de plan de charge et 95 lignes de pilotage — pendant que 7a annonçait « 0 désynchronisé »
-- sur les tiers et les projets. Un renommage se propage en CASCADE ; contrôler le premier maillon
-- ne prouve rien sur les suivants.
SELECT 'project_project_task.full_name' AS entite, count(*) AS desynchronises
  FROM project_project_task
 WHERE COALESCE(archived,false) = false AND COALESCE(name,'') <> ''
   AND full_name IS DISTINCT FROM '#' || id || ' ' || name;

-- Le titre du plan de charge recopie la tâche dans l'un OU l'autre de deux formats légitimes
-- (`name` ou `full_name`) : n'est en écart que la ligne qui ne correspond à AUCUN des deux.
-- Réaligner sur un format unique écraserait une distinction produite par l'application.
SELECT 'planning_time.title vs tâche' AS entite, count(*) AS desynchronises
  FROM project_project_planning_time pt JOIN project_project_task t ON t.id = pt.project_task
 WHERE COALESCE(pt.archived,false) = false AND pt.title IS NOT NULL
   AND pt.title <> t.name AND pt.title <> t.full_name;

-- Les lignes SANS tâche sont les plus exposées : aucun contrôle passant par la FK ne les voit.
-- Elles recopient le nom du PROJET, donc survivent à son renommage en gardant l'ancien libellé.
SELECT 'planning_time.title (sans tâche) vs projet' AS entite, count(*) AS desynchronises
  FROM project_project_planning_time pt JOIN project_project p ON p.id = pt.project
 WHERE pt.project_task IS NULL AND COALESCE(pt.archived,false) = false
   AND pt.title LIKE 'Pilotage — %'
   AND pt.title IS DISTINCT FROM 'Pilotage — ' || p.name;

-- Une description dérivée cite DEUX sources : l'écart peut venir de l'une ou de l'autre. Vécu :
-- 237 descriptions citaient un employé renommé depuis (la description gardait l'ancien nom du salarié)
-- EN PLUS d'un libellé de tâche périmé. Un contrôle mono-source en rate la moitié.
-- Attention : `hr_employee` n'a pas de `full_name` : le libellé est porté par `name`.
SELECT 'planning_time.description vs employé+tâche' AS entite, count(*) AS desynchronises
  FROM project_project_planning_time pt
  JOIN project_project_task t ON t.id = pt.project_task
  JOIN hr_employee e ON e.id = pt.employee
 WHERE COALESCE(pt.archived,false) = false AND pt.description LIKE 'Allocation %'
   AND pt.description IS DISTINCT FROM 'Allocation ' || e.name || ' sur ' || t.name;

-- 7b. full_name VIDE = enregistrement invisible dans les sélecteurs. Plus grave qu'un libellé
--     périmé : l'enregistrement disparaît de l'interface sans qu'aucune erreur ne soit levée.
SELECT 'base_partner à full_name vide (INVISIBLES)' AS anomalie, count(*) AS n
  FROM base_partner WHERE COALESCE(full_name, '') = '';

-- 7c. Dénormalisations d'une valeur portée par une table liée. order_by_state est le cas connu ;
--     en chercher d'autres avec : information_schema.columns sur des noms en order_*/*_state/*_code.
SELECT 'crm_opportunity.order_by_state ≠ statut.sequence' AS anomalie, count(*) AS n
  FROM crm_opportunity o JOIN crm_opportunity_status s ON s.id = o.opportunity_status
 WHERE o.order_by_state IS DISTINCT FROM s.sequence;

-- 7d. COMPTEURS DE SÉQUENCE EN RETARD SUR L'OCCUPÉ → collision au prochain onSave à l'écran.
--     Prendre un numéro libre ne suffit pas : il faut avancer le compteur. Générique sur toutes
--     les séquences dont le préfixe est littéral (sans %YY ni groovy).
SELECT s.code_select, s.prefixe, v.next_num AS compteur,
       'voir max occupé sur la table cible' AS controle_manuel
  FROM base_sequence s JOIN base_sequence_version v ON v.sequence = s.id
 WHERE s.prefixe IS NOT NULL AND s.prefixe NOT LIKE '%\%%'
 ORDER BY s.code_select;

-- 7e. SÉQUENCES PK POSTGRES EN RETARD SUR max(id) → la CRÉATION depuis l'écran plante
--     en `duplicate key ..._pkey`. Angle mort de 7d, qui ne regarde que les compteurs MÉTIER
--     (`base_sequence`, la numérotation SO0001) : ce sont deux mécanismes distincts.
--     `last_value` NULL = séquence JAMAIS appelée, donc `nextval` rendra 1 : le cas d'un jeu
--     seedé en SQL avec des ids hauts et sans `setval` derrière. Constaté le 2026-09-07 sur
--     <base> : 11 séquences en retard, dont les 8 tables du jeu de démo
--     (commande, ligne, opportunité, projet, feuille de temps, ligne, situation, ligne) —
--     l'audit d'acceptation avait déclaré ce jeu conforme sans le voir. Une démo où le prospect
--     demande « créez-moi une opportunité » plante à l'enregistrement.
--     Attention : Qualifier avant d'accuser : l'import de démo AOS pose lui aussi des ids explicites sans
--     `setval` — mesuré sur <base>, 16 tables de référence RH/talent en retard, sans
--     qu'aucun seed maison n'y soit pour rien. Le contrôle étiquette donc l'origine : `NOTRE SEED`
--     si la table porte le tag du jeu, `herite du socle` sinon. Les deux sont de vrais défauts
--     fonctionnels — seule la responsabilité change, et donc l'urgence.
--     Preuve du mécanisme (2026-09-07, crm_opportunity sur <base>) : séquence remise
--     à 5 → POST /ws/rest rend `status:-1` et `duplicate key ... crm_opportunity_pkey, Key (id)=(6)` ;
--     après `setval` au max, le même appel rend `status:0`. Le message affiché à l'utilisateur est
--     trompeur deux fois : il dit « ne peut pas être mis à jour » pour une CRÉATION et ne parle
--     jamais de séquence — il envoie chercher un doublon métier.
DO $$
DECLARE r record; mx bigint; lv bigint; n int := 0;
BEGIN
  FOR r IN SELECT c.table_name, s.sequencename FROM information_schema.columns c
            JOIN pg_sequences s ON s.schemaname='public' AND s.sequencename = c.table_name||'_seq'
           WHERE c.table_schema='public' AND c.column_name='id'
  LOOP
    EXECUTE format('SELECT max(id) FROM %I', r.table_name) INTO mx;
    SELECT last_value INTO lv FROM pg_sequences WHERE sequencename = r.sequencename;
    IF mx IS NOT NULL AND (lv IS NULL OR lv < mx) THEN
      RAISE NOTICE '  7e % : max(id)=%  sequence=%  → CREATION UI IMPOSSIBLE  [%]', r.table_name, mx, coalesce(lv::text,'JAMAIS APPELEE'),
        CASE WHEN EXISTS (SELECT 1 FROM _tagged WHERE tbl = r.table_name) THEN 'NOTRE SEED' ELSE 'herite du socle' END;
      n := n + 1;
    END IF;
  END LOOP;
  IF n = 0 THEN RAISE NOTICE '  7e aucune sequence PK en retard sur l occupe';
  ELSE RAISE NOTICE '  7e --> % sequence(s) a realigner : SELECT setval(''<table>_seq'', max(id)) FROM <table>', n; END IF;
END $$;

\echo '   Attention : 7d : comparer chaque compteur au max réellement occupé, ex. pour les tiers :'
\echo '      SELECT max(substring(partner_seq from ''[0-9]+$'')::int) FROM base_partner'
\echo '        WHERE partner_seq ~ ''^T[0-9]+$'';   -- doit être < compteur'

-- ════════════════════════════════════════════════════════════════════════════
-- DIMENSION 8 — booléens qui rendent invisible, et valeurs UTILES
-- ════════════════════════════════════════════════════════════════════════════
\echo ''
\echo '── DIMENSION 8 — booléens filtrants et valeurs utiles ───────'

-- 8a. Un domaine de vue écrit `self.x = false` EXCLUT LES NULL. Un booléen non initialisé rend
--     donc l'enregistrement absent de l'écran tout en restant sélectionnable ailleurs.
--     Cas rencontrés : base_product.expense (20 lignes invisibles au catalogue), is_model.
SELECT 'base_product.expense NULL' AS booleen_filtrant, count(*) AS invisibles
  FROM base_product WHERE expense IS NULL
UNION ALL SELECT 'base_product.is_model NULL', count(*) FROM base_product WHERE is_model IS NULL
UNION ALL SELECT 'base_product.sellable NULL', count(*) FROM base_product WHERE sellable IS NULL
UNION ALL SELECT 'base_product.purchasable NULL', count(*) FROM base_product WHERE purchasable IS NULL
UNION ALL SELECT 'base_partner.is_customer NULL', count(*) FROM base_partner WHERE is_customer IS NULL
UNION ALL SELECT 'base_partner.is_supplier NULL', count(*) FROM base_partner WHERE is_supplier IS NULL;

\echo '   Attention : méthode : lire le <domain> des action-view de l''entité et vérifier CHAQUE booléen'
\echo '      qui y figure. `= false` exclut NULL ; `= true` aussi. Attention : meta_action peut'
\echo '      porter des DOUBLONS de name — compter avant de lire avec LIMIT 1.'

-- 8b. Valeurs utiles, pas présence. count(col) compte 0, '' et false comme « rempli ».
SELECT 'notations à 0 (crm_lead.lead_scoring_select)' AS absence_deguisee, count(*) AS n
  FROM crm_lead WHERE COALESCE(lead_scoring_select, 0) NOT BETWEEN 1 AND 5
-- Attention : `archived` EXCLU (2026-08-24) : sans ce filtre, ce contrôle annonçait 32 affaires non
-- notées sur 68 dans une base de démo ESN. Les 32 étaient le lot du socle AOS, ARCHIVÉ donc invisible à
-- l'écran ; les 36 vivantes étaient toutes notées. Un audit qui compte des lignes que le moteur
-- n'affiche pas fabrique une charge de travail qui n'existe pas (piège 79). La ligne
-- « descriptions vides » ci-dessous filtrait déjà, elle : le script se contredisait.
UNION ALL SELECT 'crm_opportunity.opportunity_rating à 0 (vivantes)', count(*)
  FROM crm_opportunity WHERE COALESCE(archived,false) = false AND COALESCE(opportunity_rating, 0) = 0
UNION ALL SELECT 'descriptions vides après btrim (opportunités vivantes)', count(*)
  FROM crm_opportunity WHERE COALESCE(archived,false) = false AND COALESCE(btrim(description),'') = ''
-- Attention : CONTRÔLE INVERSÉ (2026-08-24) — piège 93. `supplierQualityRatingSelect` est CALCULÉ par
-- `PartnerProductQualityRatingServiceImpl.updateSupplier()` à partir des réceptions. Compter les
-- notes à 0 poussait à remplir un champ dérivé, donc à FABRIQUER un historique d'évaluation :
-- l'inverse de ce que l'audit doit produire. Le vrai défaut est la note SANS base de calcul —
-- 4 étoiles au-dessus d'une quantité reçue nulle et d'un panneau de détail vide.
UNION ALL SELECT 'notes qualité fournisseur SANS réception (note usurpée)', count(*)
  FROM base_partner p WHERE p.is_supplier
   AND COALESCE(p.supplier_quality_rating_select, 0) > 0
   AND NOT EXISTS (SELECT 1 FROM stock_partner_product_quality_rating r WHERE r.partner = p.id);

-- ════════════════════════════════════════════════════════════════════════════
-- DIMENSION 9 — configurations dans un état que l'UI n'autorise pas
-- ════════════════════════════════════════════════════════════════════════════
-- Le SQL peut écrire une configuration que l'écran natif refuserait, et qui fait planter le
-- moteur à l'exécution. Cas prouvé : suivi de stock → NPE en réception d'achat.
\echo ''
\echo '── DIMENSION 9 — configurations invalides (plantage moteur) ──'

SELECT 'suivi de stock : NPE garanti en réception' AS configuration_piegee,
       string_agg('config ' || id, ', ') AS lignes
  FROM stock_tracking_number_configuration
 WHERE is_purchase_tracking_managed AND generate_purchase_auto_tracking_nbr
   AND (sequence IS NULL OR COALESCE(purchase_qty_by_tracking, 0) <= 0)
HAVING count(*) > 0;

\echo '   (aucune ligne = sain. Sinon : StockMoveLineServiceImpl:402 lève un NPE sur la quantité'
\echo '    NULL, AVANT même le contrôle de séquence. Poser la quantité sur les TROIS axes.)'

-- 9b. Mesures sans unité : « 2,4 » sans dire si ce sont des kilos ou des livres.
--
-- Attention : `> 0` ET NON `IS NOT NULL` — correction faite le jour même où ces requêtes ont été écrites.
-- La première version testait `IS NOT NULL` et a signalé 45 produits « à corriger » dont TOUTES
-- les valeurs étaient à `0.000` : des champs vides par défaut, pas des données fausses. Leur poser
-- une unité aurait produit « 0 cm », strictement pire que le vide.
-- C'est le piège 75 — `count()` ment sur les zéros — reproduit DANS la requête écrite pour le
-- détecter. Connaître la règle ne suffit pas : il faut l'appliquer à son propre code.
SELECT 'dimensions renseignées sans length_unit' AS mesure_sans_unite, count(*) AS n
  FROM base_product
 WHERE (COALESCE(length,0) > 0 OR COALESCE(width,0) > 0 OR COALESCE(height,0) > 0)
   AND length_unit IS NULL
UNION ALL SELECT 'masses renseignées sans mass_unit', count(*)
  FROM base_product
 WHERE (COALESCE(net_mass,0) > 0 OR COALESCE(gross_mass,0) > 0) AND mass_unit IS NULL
UNION ALL SELECT 'masse brute <= masse nette (emballage sans poids)', count(*)
  FROM base_product
 WHERE COALESCE(net_mass,0) > 0 AND COALESCE(gross_mass,0) > 0 AND gross_mass <= net_mass;

-- 9c. Tables de couple dont un seul côté est renseigné → relation orpheline, invisible à l'écran.
SELECT 'sale_complementary_product sans original_product' AS relation_orpheline, count(*) AS n
  FROM sale_complementary_product WHERE original_product IS NULL OR product IS NULL;

\echo ''
\echo '  DIMENSION 10 — le CONTRAT, pas le script (NON AUTOMATISABLE) :'
\echo '     relire le scénario ligne à ligne et vérifier chaque engagement.'
\echo '     Un audit qui teste ce que le script ÉCRIT est fermé sur lui-même :'
\echo '     16 contrôles ont rendu « 0 anomalie » alors qu''un champ promis'
\echo '     par le contrat était NULL sur 100% des créations.'
\echo '     Signal fort : un champ vide sur les créations alors que le SOCLE'
\echo '     le renseigne (ici 79 des 85 produits d''origine le portaient).'
\echo ''

-- ════════════════════════════════════════════════════════════════════════════
-- DIMENSION 11 — cohérence temporelle  (ajoutée le 2026-09-03)
-- ════════════════════════════════════════════════════════════════════════════
-- Pourquoi mécanique et non documentaire : la règle 11 de SKILL.md (« le temps est une relation »,
-- cf. methode-dates.md §6) était déjà écrite et a quand même été violée — même schéma d'échec que
-- la règle 5 (full_name) avant l'écriture de la dimension 7. Seul un contrôle qui échoue dur change
-- l'issue.
--
-- Portée délibérément DIFFÉRENTE des dimensions 1-9 : celles-ci auditent les lignes CRÉÉES sous
-- :tag (nouveauté du peuplement). F1/F3/F5/F6/F7 ci-dessous vérifient un invariant MÉTIER
-- (précédence, week-end, statut/date, contenance, période comptable) qui doit tenir pour TOUTE
-- ligne, taguée ou héritée du socle AOS — une facture datée avant sa commande est un défaut qu'elle
-- porte le tag ou non. Ces 5 contrôles tournent donc sur la table entière. Seul F4 (rafale
-- d'insertion) reste borné à `_tagged` : une rafale de `created_on` identiques n'a de sens qu'au
-- moment d'un import, pas comme propriété générale de la base.
--
-- Tables et colonnes de dates NE SONT PAS supposées : introspectées le 2026-09-03 sur
-- <base> (information_schema.columns, data_type IN date/timestamp*) avant d'écrire
-- une seule requête. Chaque contrôle est gardé par un test d'existence (to_regclass + colonne) pour
-- rester jouable si `axelor-business-project`, `axelor-crm` ou le module construction manquent
-- (règle « colonnes fantômes » de methode-introspection.md §Colonnes fantômes).
--
-- F0 (introspection des colonnes) et F2 (fenêtre du contrat, `-v debut=/-v fin=`) restent des
-- OUTILS au sens de methode-dates.md §6, pas des contrôles numérotés : F0 a servi en amont pour
-- bâtir les requêtes ci-dessous ; F2 ne s'active QUE si `-v debut=` et `-v fin=` sont fournis, pour
-- ne pas casser l'appel minimal (`-v tag=<TAG>` seul).

\echo ''
\echo '── DIMENSION 11 — cohérence temporelle ───────────────────────'

-- F1 — chaîne ventes : une facture ne peut pas précéder la commande dont elle découle
-- (account_invoice.sale_order → sale_sale_order, edge déclarée pour ce chantier).
DO $$
DECLARE ok boolean; total bigint; n bigint; exemples text;
BEGIN
  SELECT to_regclass('account_invoice') IS NOT NULL AND to_regclass('sale_sale_order') IS NOT NULL
     AND EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='account_invoice' AND column_name='sale_order')
     AND EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='account_invoice' AND column_name='invoice_date')
     AND EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='sale_sale_order' AND column_name='order_date')
    INTO ok;
  IF NOT ok THEN
    RAISE NOTICE '  F1 facture/commande : non évaluable (table ou colonne absente — module vente/facturation manquant)';
    RETURN;
  END IF;
  SELECT count(*) INTO total
    FROM account_invoice av JOIN sale_sale_order am ON am.id = av.sale_order
   WHERE av.invoice_date IS NOT NULL AND am.order_date IS NOT NULL;
  SELECT count(*) FILTER (WHERE av.invoice_date::date < am.order_date::date),
         (SELECT string_agg(sub.id::text, ', ') FROM (
            SELECT av2.id FROM account_invoice av2 JOIN sale_sale_order am2 ON am2.id = av2.sale_order
             WHERE av2.invoice_date IS NOT NULL AND am2.order_date IS NOT NULL
               AND av2.invoice_date::date < am2.order_date::date
             ORDER BY av2.id LIMIT 3) sub)
    INTO n, exemples
    FROM account_invoice av JOIN sale_sale_order am ON am.id = av.sale_order
   WHERE av.invoice_date IS NOT NULL AND am.order_date IS NOT NULL;
  RAISE NOTICE '  F1 facture antérieure à sa commande : % violation(s) — portée : % ligne(s) auditée(s)%',
    COALESCE(n,0), total, CASE WHEN COALESCE(n,0) > 0 THEN ' — ex. facture(s) id ' || exemples ELSE '' END;
  IF total = 0 THEN
    RAISE NOTICE '  Attention : portée nulle : aucune facture de cette base ne référence de sale_order (account_invoice.sale_order toujours NULL) — le 0 ne prouve rien, il constate l''absence de lien exploitable';
  END IF;
END $$;

-- F6 — projet/temps : la tâche doit rester dans la fenêtre de son projet.
DO $$
DECLARE ok boolean; total bigint; n bigint; exemples text;
BEGIN
  SELECT to_regclass('project_project_task') IS NOT NULL AND to_regclass('project_project') IS NOT NULL
     AND EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='project_project_task' AND column_name='task_date')
     AND EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='project_project' AND column_name='from_date')
     AND EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='project_project' AND column_name='to_date')
    INTO ok;
  IF NOT ok THEN
    RAISE NOTICE '  F6 tâche/projet : non évaluable (table ou colonne absente)';
    RETURN;
  END IF;
  SELECT count(*) INTO total
    FROM project_project_task t JOIN project_project p ON p.id = t.project
   WHERE t.task_date IS NOT NULL AND p.from_date IS NOT NULL AND p.to_date IS NOT NULL;
  SELECT count(*) FILTER (WHERE t.task_date::date < p.from_date::date
                             OR (t.task_end_date IS NOT NULL AND t.task_end_date::date > p.to_date::date)),
         (SELECT string_agg(sub.id::text, ', ') FROM (
            SELECT t2.id FROM project_project_task t2 JOIN project_project p2 ON p2.id = t2.project
             WHERE t2.task_date IS NOT NULL AND p2.from_date IS NOT NULL AND p2.to_date IS NOT NULL
               AND (t2.task_date::date < p2.from_date::date
                    OR (t2.task_end_date IS NOT NULL AND t2.task_end_date::date > p2.to_date::date))
             ORDER BY t2.id LIMIT 3) sub)
    INTO n, exemples
    FROM project_project_task t JOIN project_project p ON p.id = t.project
   WHERE t.task_date IS NOT NULL AND p.from_date IS NOT NULL AND p.to_date IS NOT NULL;
  RAISE NOTICE '  F6 tâche hors fenêtre de son projet : % violation(s) — portée : % ligne(s) auditée(s)%',
    COALESCE(n,0), total, CASE WHEN COALESCE(n,0) > 0 THEN ' — ex. tâche(s) id ' || exemples ELSE '' END;
  IF total = 0 THEN
    RAISE NOTICE '  Attention : portée nulle : project_project.to_date est NULL sur les projets de cette base (contrôle non exploitable en l''état — pas une absence d''anomalie)';
  END IF;
END $$;

-- F6bis — ligne de feuille de temps dans la fenêtre de sa feuille (hr_timesheet.from_date/to_date).
DO $$
DECLARE ok boolean; total bigint; n bigint; exemples text;
BEGIN
  SELECT to_regclass('hr_timesheet_line') IS NOT NULL AND to_regclass('hr_timesheet') IS NOT NULL
     AND EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='hr_timesheet_line' AND column_name='date_val')
     AND EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='hr_timesheet' AND column_name='from_date')
    INTO ok;
  IF NOT ok THEN
    RAISE NOTICE '  F6bis ligne/feuille : non évaluable (table ou colonne absente — module RH temps manquant)';
    RETURN;
  END IF;
  SELECT count(*) INTO total
    FROM hr_timesheet_line l JOIN hr_timesheet h ON h.id = l.timesheet
   WHERE l.date_val IS NOT NULL AND h.from_date IS NOT NULL AND h.to_date IS NOT NULL;
  SELECT count(*) FILTER (WHERE l.date_val < h.from_date OR l.date_val > h.to_date),
         (SELECT string_agg(sub.id::text, ', ') FROM (
            SELECT l2.id FROM hr_timesheet_line l2 JOIN hr_timesheet h2 ON h2.id = l2.timesheet
             WHERE l2.date_val IS NOT NULL AND h2.from_date IS NOT NULL AND h2.to_date IS NOT NULL
               AND (l2.date_val < h2.from_date OR l2.date_val > h2.to_date)
             ORDER BY l2.id LIMIT 3) sub)
    INTO n, exemples
    FROM hr_timesheet_line l JOIN hr_timesheet h ON h.id = l.timesheet
   WHERE l.date_val IS NOT NULL AND h.from_date IS NOT NULL AND h.to_date IS NOT NULL;
  RAISE NOTICE '  F6bis pointage hors fenêtre de sa feuille : % violation(s) — portée : % ligne(s) auditée(s)%',
    COALESCE(n,0), total, CASE WHEN COALESCE(n,0) > 0 THEN ' — ex. ligne(s) id ' || exemples ELSE '' END;
  IF total = 0 THEN RAISE NOTICE '  aucune ligne hors fenêtre de sa feuille'; END IF;
END $$;

-- F6ter — ligne de feuille de temps dans la fenêtre de sa tâche (project_project_task.task_date/task_end_date).
-- Attention : réserve de nommage : `task_date` n'est pas documenté ailleurs comme date de DÉBUT plutôt que
-- date « de référence » de la tâche — retenu comme borne basse faute d'un champ `task_start_date`.
DO $$
DECLARE ok boolean; total bigint; n bigint; exemples text;
BEGIN
  SELECT to_regclass('hr_timesheet_line') IS NOT NULL AND to_regclass('project_project_task') IS NOT NULL
     AND EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='hr_timesheet_line' AND column_name='project_task')
     AND EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='project_project_task' AND column_name='task_date')
    INTO ok;
  IF NOT ok THEN
    RAISE NOTICE '  F6ter ligne/tâche : non évaluable (table ou colonne absente)';
    RETURN;
  END IF;
  SELECT count(*) INTO total
    FROM hr_timesheet_line l JOIN project_project_task t ON t.id = l.project_task
   WHERE l.date_val IS NOT NULL AND t.task_date IS NOT NULL;
  SELECT count(*) FILTER (WHERE l.date_val < t.task_date OR (t.task_end_date IS NOT NULL AND l.date_val > t.task_end_date)),
         (SELECT string_agg(sub.id::text, ', ') FROM (
            SELECT l2.id FROM hr_timesheet_line l2 JOIN project_project_task t2 ON t2.id = l2.project_task
             WHERE l2.date_val IS NOT NULL AND t2.task_date IS NOT NULL
               AND (l2.date_val < t2.task_date OR (t2.task_end_date IS NOT NULL AND l2.date_val > t2.task_end_date))
             ORDER BY l2.id LIMIT 3) sub)
    INTO n, exemples
    FROM hr_timesheet_line l JOIN project_project_task t ON t.id = l.project_task
   WHERE l.date_val IS NOT NULL AND t.task_date IS NOT NULL;
  RAISE NOTICE '  F6ter pointage antérieur à la date de sa tâche (ou postérieur à sa fin) : % violation(s) — portée : % ligne(s) auditée(s)%',
    COALESCE(n,0), total, CASE WHEN COALESCE(n,0) > 0 THEN ' — ex. ligne(s) id ' || exemples ELSE '' END;
END $$;

-- F3 — pointages posés un week-end.
DO $$
DECLARE ok boolean; total bigint; n bigint; exemples text;
BEGIN
  SELECT to_regclass('hr_timesheet_line') IS NOT NULL
     AND EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='hr_timesheet_line' AND column_name='date_val')
    INTO ok;
  IF NOT ok THEN
    RAISE NOTICE '  F3 week-ends : non évaluable (hr_timesheet_line absente — module RH temps manquant)';
    RETURN;
  END IF;
  SELECT count(*) INTO total FROM hr_timesheet_line WHERE date_val IS NOT NULL;
  SELECT count(*) FILTER (WHERE EXTRACT(dow FROM date_val) IN (0,6)),
         (SELECT string_agg(sub.id::text, ', ') FROM (
            SELECT id FROM hr_timesheet_line WHERE date_val IS NOT NULL AND EXTRACT(dow FROM date_val) IN (0,6)
             ORDER BY id LIMIT 3) sub)
    INTO n, exemples
    FROM hr_timesheet_line WHERE date_val IS NOT NULL;
  RAISE NOTICE '  F3 pointage un week-end (hr_timesheet_line.date_val) : % ligne(s) — portée : % ligne(s) auditée(s)%',
    COALESCE(n,0), total, CASE WHEN COALESCE(n,0) > 0 THEN ' — ex. ligne(s) id ' || exemples ELSE '' END;
END $$;

-- F5 — statut ↔ date contradictoires : commande, facture, opportunité, tâche.
DO $$
DECLARE n bigint; total bigint; exemples text;
BEGIN
  IF to_regclass('sale_sale_order') IS NOT NULL
     AND EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='sale_sale_order' AND column_name='status_select')
     AND EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='sale_sale_order' AND column_name='order_date') THEN
    SELECT count(*) INTO total FROM sale_sale_order;
    SELECT count(*) FILTER (WHERE status_select IN (3,4) AND order_date IS NULL),
           (SELECT string_agg(id::text, ', ') FROM (SELECT id FROM sale_sale_order
              WHERE status_select IN (3,4) AND order_date IS NULL ORDER BY id LIMIT 3) s)
      INTO n, exemples FROM sale_sale_order;
    RAISE NOTICE '  F5a commande confirmée/terminée (status 3/4) sans order_date : % ligne(s) — portée : % ligne(s)%',
      COALESCE(n,0), total, CASE WHEN COALESCE(n,0)>0 THEN ' — ex. commande(s) id ' || exemples ELSE '' END;

    SELECT count(*) FILTER (WHERE status_select = 1 AND confirmation_date_time IS NOT NULL),
           (SELECT string_agg(id::text, ', ') FROM (SELECT id FROM sale_sale_order
              WHERE status_select = 1 AND confirmation_date_time IS NOT NULL ORDER BY id LIMIT 3) s)
      INTO n, exemples FROM sale_sale_order;
    RAISE NOTICE '  F5b devis brouillon (status 1) portant une confirmation_date_time : % ligne(s) — portée : % ligne(s)%',
      COALESCE(n,0), total, CASE WHEN COALESCE(n,0)>0 THEN ' — ex. commande(s) id ' || exemples ELSE '' END;
  ELSE
    RAISE NOTICE '  F5a/b commande : non évaluable (sale_sale_order absente)';
  END IF;

  IF to_regclass('account_invoice') IS NOT NULL
     AND EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='account_invoice' AND column_name='status_select')
     AND EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='account_invoice' AND column_name='invoice_date') THEN
    SELECT count(*) INTO total FROM account_invoice;
    SELECT count(*) FILTER (WHERE status_select = 3 AND invoice_date IS NULL),
           (SELECT string_agg(id::text, ', ') FROM (SELECT id FROM account_invoice
              WHERE status_select = 3 AND invoice_date IS NULL ORDER BY id LIMIT 3) s)
      INTO n, exemples FROM account_invoice;
    RAISE NOTICE '  F5c facture ventilée (status 3) sans invoice_date : % ligne(s) — portée : % ligne(s)%',
      COALESCE(n,0), total, CASE WHEN COALESCE(n,0)>0 THEN ' — ex. facture(s) id ' || exemples ELSE '' END;

    SELECT count(*) FILTER (WHERE status_select = 1 AND validated_date_time IS NOT NULL),
           (SELECT string_agg(id::text, ', ') FROM (SELECT id FROM account_invoice
              WHERE status_select = 1 AND validated_date_time IS NOT NULL ORDER BY id LIMIT 3) s)
      INTO n, exemples FROM account_invoice;
    RAISE NOTICE '  F5d facture brouillon (status 1) portant une validated_date_time : % ligne(s) — portée : % ligne(s)%',
      COALESCE(n,0), total, CASE WHEN COALESCE(n,0)>0 THEN ' — ex. facture(s) id ' || exemples ELSE '' END;
  ELSE
    RAISE NOTICE '  F5c/d facture : non évaluable (account_invoice absente)';
  END IF;

  IF to_regclass('crm_opportunity') IS NOT NULL AND to_regclass('crm_opportunity_status') IS NOT NULL
     AND EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='crm_opportunity_status' AND column_name='is_open')
     AND EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='crm_opportunity' AND column_name='expected_close_date') THEN
    SELECT count(*) INTO total FROM crm_opportunity o JOIN crm_opportunity_status s ON s.id=o.opportunity_status
     WHERE o.expected_close_date IS NOT NULL;
    SELECT count(*) FILTER (WHERE NOT s.is_open AND o.expected_close_date > CURRENT_DATE),
           (SELECT string_agg(sub.id::text, ', ') FROM (
              SELECT o2.id FROM crm_opportunity o2 JOIN crm_opportunity_status s2 ON s2.id=o2.opportunity_status
               WHERE NOT s2.is_open AND o2.expected_close_date > CURRENT_DATE ORDER BY o2.id LIMIT 3) sub)
      INTO n, exemples
      FROM crm_opportunity o JOIN crm_opportunity_status s ON s.id=o.opportunity_status
     WHERE o.expected_close_date IS NOT NULL;
    RAISE NOTICE '  F5e opportunité fermée (statut terminal, is_open=false) avec expected_close_date dans le futur : % ligne(s) — portée : % ligne(s)%',
      COALESCE(n,0), total, CASE WHEN COALESCE(n,0)>0 THEN ' — ex. opportunité(s) id ' || exemples ELSE '' END;
    RAISE NOTICE '  Attention : réserve : expected_close_date est une date PRÉVISIONNELLE, pas une date de clôture réelle observée — absence de champ dédié dans ce schéma';
  ELSE
    RAISE NOTICE '  F5e opportunité : non évaluable (crm_opportunity/crm_opportunity_status absente)';
  END IF;

  IF to_regclass('project_project_task') IS NOT NULL AND to_regclass('project_task_status') IS NOT NULL
     AND EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='project_task_status' AND column_name='is_completed')
     AND EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='project_project_task' AND column_name='completed_on') THEN
    SELECT count(*) INTO total FROM project_project_task;
    SELECT count(*) FILTER (WHERE st.is_completed AND t.completed_on IS NULL),
           (SELECT string_agg(sub.id::text, ', ') FROM (
              SELECT t2.id FROM project_project_task t2 JOIN project_task_status st2 ON st2.id=t2.status
               WHERE st2.is_completed AND t2.completed_on IS NULL ORDER BY t2.id LIMIT 3) sub)
      INTO n, exemples
      FROM project_project_task t JOIN project_task_status st ON st.id = t.status;
    RAISE NOTICE '  F5f tâche au statut terminal (is_completed) sans completed_on : % ligne(s) — portée : % ligne(s)%',
      COALESCE(n,0), total, CASE WHEN COALESCE(n,0)>0 THEN ' — ex. tâche(s) id ' || exemples ELSE '' END;
  ELSE
    RAISE NOTICE '  F5f tâche : non évaluable (project_project_task/project_task_status absente)';
  END IF;
END $$;

-- F7 — pièce comptable datée hors de toute période existante (piège 48).
DO $$
DECLARE ok boolean; total bigint; n bigint; exemples text;
BEGIN
  SELECT to_regclass('account_invoice') IS NOT NULL AND to_regclass('base_period') IS NOT NULL
     AND EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='account_invoice' AND column_name='invoice_date')
    INTO ok;
  IF ok THEN
    SELECT count(*) INTO total FROM account_invoice WHERE invoice_date IS NOT NULL;
    SELECT count(*) FILTER (WHERE NOT EXISTS (SELECT 1 FROM base_period per WHERE i.invoice_date BETWEEN per.from_date AND per.to_date)),
           (SELECT string_agg(sub.id::text, ', ') FROM (
              SELECT i2.id FROM account_invoice i2 WHERE i2.invoice_date IS NOT NULL
                AND NOT EXISTS (SELECT 1 FROM base_period per WHERE i2.invoice_date BETWEEN per.from_date AND per.to_date)
              ORDER BY i2.id LIMIT 3) sub)
      INTO n, exemples FROM account_invoice i WHERE i.invoice_date IS NOT NULL;
    RAISE NOTICE '  F7a facture sans période comptable couvrante : % ligne(s) — portée : % ligne(s) auditée(s)%',
      COALESCE(n,0), total, CASE WHEN COALESCE(n,0)>0 THEN ' — ex. facture(s) id ' || exemples ELSE '' END;
  ELSE
    RAISE NOTICE '  F7a facture/période : non évaluable (table ou colonne absente)';
  END IF;

  SELECT to_regclass('account_move') IS NOT NULL AND to_regclass('base_period') IS NOT NULL
     AND EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='account_move' AND column_name='date_val')
    INTO ok;
  IF ok THEN
    SELECT count(*) INTO total FROM account_move WHERE date_val IS NOT NULL;
    SELECT count(*) FILTER (WHERE NOT EXISTS (SELECT 1 FROM base_period per WHERE m.date_val BETWEEN per.from_date AND per.to_date)),
           (SELECT string_agg(sub.id::text, ', ') FROM (
              SELECT m2.id FROM account_move m2 WHERE m2.date_val IS NOT NULL
                AND NOT EXISTS (SELECT 1 FROM base_period per WHERE m2.date_val BETWEEN per.from_date AND per.to_date)
              ORDER BY m2.id LIMIT 3) sub)
      INTO n, exemples FROM account_move m WHERE m.date_val IS NOT NULL;
    RAISE NOTICE '  F7b écriture sans période comptable couvrante : % ligne(s) — portée : % ligne(s) auditée(s)%',
      COALESCE(n,0), total, CASE WHEN COALESCE(n,0)>0 THEN ' — ex. écriture(s) id ' || exemples ELSE '' END;
  ELSE
    RAISE NOTICE '  F7b écriture/période : non évaluable (table ou colonne absente)';
  END IF;

  SELECT count(*) INTO total FROM base_period WHERE (to_date - from_date) > 40;
  IF total > 0 THEN
    RAISE NOTICE '  F7c % période(s) comptable(s) > 40 jours (n''illustre pas un mensuel)', total;
  ELSE
    RAISE NOTICE '  F7c aucune période > 40 jours';
  END IF;
END $$;

-- F4 — rafale d'insertion : > 5 lignes à la même seconde de created_on, sur les tables TAGUÉES
-- uniquement (une rafale n'a de sens qu'au moment d'un import, cf. préambule de la dimension).
DO $$
DECLARE r record; b record; total int := 0;
BEGIN
  IF (SELECT count(*) FROM _tagged) = 0 THEN
    RAISE NOTICE '  F4 rafales de created_on : aucune table taguée sous :tag sur cette base — contrôle non applicable (pas un 0 anomalie, une absence de périmètre à auditer)';
    RETURN;
  END IF;
  FOR r IN SELECT tbl FROM _tagged LOOP
    FOR b IN EXECUTE format(
      'SELECT date_trunc(''second'', created_on) AS sec, count(*) AS n FROM %I
        WHERE import_origin = %L GROUP BY 1 HAVING count(*) > 5 ORDER BY 2 DESC', r.tbl, current_setting('demo.tag'))
    LOOP
      RAISE NOTICE '  % → % ligne(s) créées à la même seconde (%)', r.tbl, b.n, b.sec;
      total := total + 1;
    END LOOP;
  END LOOP;
  IF total = 0 THEN RAISE NOTICE '  aucune rafale de created_on détectée sur les tables taguées'; END IF;
END $$;

-- F2 — fenêtre du contrat (`-v debut=... -v fin=...`) : optionnelle, pour ne pas casser l'appel
-- minimal qui ne passe que `-v tag=`. Sans ces deux variables, rappel manuel uniquement.
\if :{?debut}
\if :{?fin}
SELECT set_config('demo.debut', :'debut', false);
SELECT set_config('demo.fin', :'fin', false);
DO $$
DECLARE r record; n bigint; total int := 0;
BEGIN
  FOR r IN SELECT c.table_name, c.column_name FROM information_schema.columns c
            WHERE c.table_schema='public' AND c.table_name IN (SELECT tbl FROM _tagged)
              AND c.data_type IN ('date','timestamp without time zone','timestamp with time zone')
              AND c.column_name NOT IN ('created_on','updated_on')
  LOOP
    BEGIN
      EXECUTE format('SELECT count(*) FROM %I WHERE import_origin=%L AND %I IS NOT NULL
                        AND (%I::date < %L::date OR %I::date > %L::date)',
        r.table_name, current_setting('demo.tag'), r.column_name,
        r.column_name, current_setting('demo.debut'),
        r.column_name, current_setting('demo.fin')) INTO n;
      IF n > 0 THEN RAISE NOTICE '  F2 %.% : % ligne(s) hors fenêtre [% , %]', r.table_name, r.column_name, n, current_setting('demo.debut'), current_setting('demo.fin'); total := total + 1; END IF;
    EXCEPTION WHEN OTHERS THEN NULL;
    END;
  END LOOP;
  IF total = 0 THEN RAISE NOTICE '  F2 aucune colonne de date hors fenêtre [% , %]', current_setting('demo.debut'), current_setting('demo.fin'); END IF;
END $$;
\else
\echo '  F2 fenêtre du contrat : NON ÉVALUÉ — -v fin=... manquant (fournir -v debut=AAAA-MM-JJ -v fin=AAAA-MM-JJ)'
\endif
\else
\echo '  F2 fenêtre du contrat : NON AUTOMATISÉ sur cet appel — relancer avec -v debut=AAAA-MM-JJ -v fin=AAAA-MM-JJ'
\echo '     pour l''activer (checklist manuelle en attendant, cf. dimension 3/6/10)'
\endif

\echo ''
\echo '════════════════════════════════════════════════════════════'
\echo '  FIN DE L''AUDIT — les 13 dimensions ont été PARCOURUES.'
\echo '  Cette ligne est le seul témoin d''un parcours complet : si elle manque, psql'
\echo '  s''est arrêté avant la fin et l''audit ne couvre PAS ce qu''il annonce.'
\echo '  Parcourues n''est pas évaluées : un contrôle portant sur une colonne ou une'
\echo '  table absente de cette base est SAUTÉ, et il le dit sur sa propre ligne.'
\echo '  Les compter, 0 attendu :'
\echo '     … -f audit-completeness.sql 2>&1 | tee audit.txt'
\echo '     grep -c ''^psql:.*ERROR:'' audit.txt'
\echo '════════════════════════════════════════════════════════════'

-- ─────────────────────────────────────────────────────────────────────────────
-- DIMENSION 12 — colonne `version` NULL sur une ligne seedée  (ajoutée le 2026-09-15, piège 124)
--
-- Périmètre délibérément DIFFÉRENT des dimensions 1-9 : TOUTES les lignes de TOUTES les tables porteuses
-- d'une colonne `version` (pas seulement celles créées sous :tag), parce qu'une version NULL n'importe où
-- fait planter le premier enregistrement du moteur qui la touche — « Cannot invoke Integer.intValue()
-- because "current" is null », levé au flush Hibernate, sans nommer la table.
-- Seules les tables à CLÉ PRIMAIRE sont auditées : une table de sauvegarde créée par copie (CREATE TABLE AS)
-- n'en a pas et n'est pas une entité.
-- Placée APRÈS la ligne « FIN DE L'AUDIT » et volontairement DURE (RAISE EXCEPTION) : le témoin de
-- parcours complet est imprimé, puis `grep -c '^psql:.*ERROR:'` rend 1 et la porte se ferme.
-- Vérifié le 2026-09-15 sur <base> : 16 tables à version NULL, confirmation de commande en NPE ;
-- après UPDATE … SET version = 0, la même confirmation passe.
\echo ''
\echo '── DIMENSION 12 — colonne version NULL (NPE « current is null » au 1er save) ─'
DO $$
DECLARE r record; n bigint; total bigint := 0;
BEGIN
  FOR r IN
    SELECT c.table_name
    FROM information_schema.columns c
    WHERE c.column_name = 'version' AND c.table_schema = 'public'
      AND EXISTS (SELECT 1 FROM information_schema.table_constraints tc
                  WHERE tc.table_schema = c.table_schema AND tc.table_name = c.table_name
                    AND tc.constraint_type = 'PRIMARY KEY')
    ORDER BY 1
  LOOP
    EXECUTE format('SELECT count(*) FROM %I WHERE version IS NULL', r.table_name) INTO n;
    IF n > 0 THEN
      RAISE NOTICE '  % : % ligne(s) sans version → UPDATE % SET version = 0 WHERE version IS NULL;', r.table_name, n, r.table_name;
      total := total + n;
    END IF;
  END LOOP;
  IF total > 0 THEN
    RAISE EXCEPTION 'DIMENSION 12 : % ligne(s) à version NULL — le moteur plantera au premier enregistrement (piège 124)', total;
  END IF;
  RAISE NOTICE '  aucune ligne à version NULL';
END $$;

