# Méthode — cohérence temporelle d'un jeu de données de démo

Fichier de détail de la **règle cardinale 11** de SKILL.md (« le temps est une relation, pas un champ »).
SKILL.md en porte l'énoncé ; ici se trouvent le graphe de précédence, les délais par défaut, la
procédure de redatage et les requêtes d'audit temporel.

## 1. Pourquoi c'est la faute la moins pardonnée

Un prospect ne vérifie pas les montants ligne à ligne : il ouvre une facture et regarde si elle est
postérieure à sa commande. Une facture datée avant sa commande, un pointage un dimanche, une
opportunité « gagnée » dont la clôture est dans le futur, quarante enregistrements créés à la même
seconde : chacun est visible en un clic et coûte plus cher que dix champs vides. La frontière
UI / SQL (`socle-aos-baseline.md` §6) ne couvrait que les flux valorisés joués par le moteur puis
redatés ; on généralise ici à **toutes** les pièces qui se référencent.

---

## 2. Les trois familles de dates

L'exécutant reçoit du contrat une **horloge** (date pivot, fenêtre, jalons). Il ne la décide pas ; il
décide comment chaque colonne la consomme.

**2.1 Dates MÉTIER — posées depuis l'horloge.** Celles que l'utilisateur saisirait : date de devis, de
commande, de facture, début/fin de tâche, jour pointé, clôture prévue d'une opportunité. Offset
**dérivé de l'entité liée**, jamais constant (règle 11 de SKILL.md : `employee * 11 % 90` jours, pas
`+30 j` partout). Deux exigences cumulatives : rester dans la fenêtre, respecter le graphe de la partie 3.
Exception : la « date de commande » d'une commande client est écrite par AOS à la génération de sa 1re facture
(piège 195) — générer la facture sous la date simulée de son jour (piège 171).

**2.2 Dates TECHNIQUES — alignées ou étalées, jamais en rafale.** Trois points établis :

- Les patrons d'écriture posent `created_on = NOW(), updated_on = NOW()` (`methode-ecriture-sql.md`,
  et les patrons de volume de `mode-b-volume.md`).
  Correct pour du référentiel invisible, **faux pour toute pièce dont l'UI affiche le suivi** :
  quarante commandes créées à la même seconde, six mois après leur date de commande, se lisent comme
  un import.
- Ces colonnes ne sont **pas** un critère de tri socle/créations : « ne jamais trier via `import_id`,
  `import_origin` ou `created_on` : vérifié faux dans les deux sens » (règle zéro de SKILL.md). Elles n'ont
  aucune valeur d'audit, seulement de crédibilité.
- `created_by` / `updated_by` forment des cycles FK (piège 64, `methode-rejouabilite.md`) : NULL à l'insertion, `UPDATE` en
  seconde passe dans le même fichier.

Doctrine : **aligner `created_on` sur la date métier** (une commande du 12 mars a été créée le 12 mars,
à une heure ouvrée plausible), puis `updated_on = created_on + petit delta` selon le statut. Sans date
métier (référentiel), **étaler** sur la fenêtre plutôt que tout poser à `NOW()`.

*Coût payé le 2026-09-22 (9.1.3) : une passe avait correctement réparti `order_date` sur six mois sur
120 commandes de vente — et laissé `created_on` à la seconde de l'écriture. Mesure : **2 dates
distinctes sur 120**, dont **103 le jour même de la passe**. Toute grille triée sur la création, et
toute colonne « créé le » affichée, annonçaient un import. Poser l'heure ouvrée en la dérivant de
l'identifiant (§2.1), jamais une heure constante : 120 commandes créées à 9 h 00 pile se lisent aussi
mal que 120 créées à la même seconde.*

Nuance : le panneau de suivi d'AOS affiche ces colonnes et, pour certaines entités, ses propres lignes
d'historique — qu'un alignement de `created_on` ne réécrit pas. *À vérifier sur la base cible* :
quelles entités du périmètre ont un panneau de suivi peuplé et si les tables de message/audit
associées portent leurs propres horodatages à redater. Ne pas promettre un historique cohérent avant.

**2.3 Dates DÉRIVÉES — le SQL ne les écrit pas.** `estimated_date` d'un mouvement, échéance calculée
depuis les conditions de paiement, date de calcul d'une feuille de coût, période résolue depuis une
date de facture, durées d'opération issues de la gamme. Ce sont les produits d'un service applicatif :
frontière tranchée en `socle-aos-baseline.md` §6 et par la règle 12 — *seeder un état oui, simuler une transition non*.
Deux voies, jamais une troisième :

1. **Hériter** — saisir un maximum de dates *prévues* dans l'UI avant de jouer le flux. Les dates
   planifiées passées sont acceptées (avertissement modal non bloquant) et les `estimated_date` des
   mouvements **héritent** de ces dates : la cohérence se propage sans SQL.
2. **Rejouer puis redater** — ce que le moteur a horodaté à `NOW()` se corrige selon la partie 5.

Écrire une date dérivée directement en SQL produit un enregistrement d'apparence correcte et un
système incohérent : exactement ce que `socle-aos-baseline.md` §6 interdit.

---

## 3. Le graphe de précédence

Délais **par défaut, ordres de grandeur, à ajuster au secteur** (le négoce livre en jours, la
production en semaines, le public paie en 30 à 60 jours). Les noms de colonnes ne sont pas donnés : ils
s'introspectent (requête F0).

**Ventes** — opportunité → devis (5-15 j, qualification) → commande confirmée (10-30 j, cycle de
décision B2B) → livraison (3-15 j en négoce, délai d'appro) → facture (0-5 j, facturation à
l'expédition) → échéance (**dérivée** des conditions de paiement du tiers, cf. §2.3) → paiement
(−5 à +15 j autour de l'échéance : quelques retards rendent la démo crédible). Chaque arête est une
contrainte « aval ≥ amont ».
*À introspecter* : les colonnes de date de l'entête **et** des lignes (une ligne peut porter sa propre
date de livraison souhaitée) ; si la facture est reliée à la livraison ou seulement à la commande.

**Projet / temps** — début de tâche ≥ début d'affaire et fin ≤ fin d'affaire, tâches réparties sur la
durée et non toutes au début ; créneau de plan de charge inclus dans la tâche, ~40 % dans le futur
(« charge à venir ») ; jour pointé dans [début, fin] de la tâche **et** dans la période de la feuille,
jours ouvrés seulement.
Sourcé (constaté le 2026-08-28) : la feuille de temps n'a **pas** de FK période
en 9.0.11, elle se cadre par `from_date` / `to_date` + `status_select` ; la colonne de jour d'une ligne
est `date_val` (pas `date`), et l'unicité porte sur
`(timesheet, project, product, date_val, project_task)` — le jour en fait partie ; le plan de charge
est `project_project_planning_time` (`start_date_time` / `end_date_time`).
Le déboursé main-d'œuvre ne compte que si la feuille est **validée** (`status_select = 3`, constaté le 2026-07-28) : une feuille validée est donc entièrement dans le
passé. Ne pas s'appuyer sur `spent_time` / `total_real_hrs` pour contrôler une cohérence temporelle :
valeurs seedées sans lien avec les pointages (constaté le 2026-08-24).

**Achats / stock** — demande → PO (2-10 j) → réception (5-20 j) → mouvement validé (même jour) →
facture fournisseur (2-10 j).
*À introspecter* : la distinction date prévue / date réelle sur le mouvement, et le **type** de chaque
colonne (DATE et TIMESTAMP ne se décalent pas pareil, cf. partie 5).

**CRM** — lead → opportunité (3-20 j) → événements répartis entre création et clôture (1 tous les 1 à
3 semaines) ; clôture **passée** si statut terminal, **future** si en cours. Le CRM se seede en SQL :
une opportunité n'a pas de lignes et ses montants sont saisis (règle 12 de SKILL.md) — consommer la séquence (piège 73, `methode-ecriture-sql.md`), recopier `order_by_state`
(piège 74, `methode-coherence.md`).

**Production** — commande client → OF (0-10 j) → opérations enchaînées dans [début, fin] de l'OF,
durées issues de la gamme avec plancher 30 min → durées réelles en couple start/stop dont la durée
découle → mouvements (consommation = début, production = fin, jamais par arithmétique d'intervalle) →
feuille de coût après la fin réelle. La planification d'un OF est un produit du moteur (`socle-aos-baseline.md` §6) : elle
dérive les opérations, les durées, la charge machine et les dates. Ne pas l'écrire, la jouer.
*À introspecter* : quel bouton peuple quelle table, et s'il existe un bouton global avant de budgéter
N clics par ligne.

**Facturation / comptabilité** — la période affectée doit **exister** et couvrir la date (`base_period`
est livré peuplé, `socle-aos-baseline.md` §3) ; la ventilation et les écritures sont des produits du moteur (`socle-aos-baseline.md` §6), on n'en
écrit pas en SQL. Piège 48 (`methode-coherence.md`) : une FK vers une période doit pointer la **granularité métier**, pas
l'englobante — une période unique de 12 mois rend inutilisable toute démonstration mensuelle ; créer
les périodes mensuelles manquantes et affecter chaque pièce à *son* mois. *À vérifier sur la base
cible* : quelles périodes et exercices existent, et si la fenêtre du contrat en sort.

---

## 4. Crédibilité

**Jours ouvrés.** Aucun pointage le week-end sauf métier qui le justifie (astreinte, intervention,
transport), et alors en minorité assumée. Le patron volumétrique le fait déjà (« employés ×
jours ouvrés × projets, en filtrant les week-ends », `mode-b-volume.md` §2) : étendre le filtre aux dates de commande,
de livraison et de facture — personne ne facture un 25 décembre. `EXTRACT(dow FROM d) NOT IN (0,6)`
couvre les week-ends ; les jours fériés se posent en liste explicite pour le pays du contrat,
l'introspection ne les fournit pas.

Attention : **Piège 111 — le correctif « pas de week-end » naïf (décaler au jour ouvré le plus proche)
empile tout sur le MÊME jour.** Un correctif qui déplace chaque événement du week-end vers « le
lundi suivant » sans vérifier ce que ce lundi porte déjà produit l'inverse de l'objectif : mesuré
sur le chantier package CRM (2026-09-07), 16 événements se sont retrouvés sur le seul lundi 07/09
(le socle en portait déjà 11 ce jour-là, plus 4 décalés du week-end du 5-6), pendant que la
règle contractuelle explicite (3 à 8 événements par semaine) était violée d'un facteur 3. Le
correctif était juste sur SON critère (0 événement le week-end, vérifié) et empirait exactement ce
que le contrat cherchait — un calendrier crédible. « 0 week-end » n'est pas la seule contrainte à
tenir en même temps que le redatage ; la densité par jour et par semaine en est une autre, et un
décalage ponctuel ne la protège pas.

**Parade — allocateur avec plafonds, pas un simple décalage.** Choisir le jour cible parmi les
jours ouvrés de la fenêtre en respectant deux bornes simultanément, jamais le jour ouvré le plus
proche pris isolément :

```sql
-- Répartir n événements sur les jours ouvrés d'une fenêtre, ≤5/jour, en visant 3-8/semaine :
-- générer la série de jours ouvrés, compter ce qui y est déjà (existant + déjà réalloué dans le
-- même lot), exclure les jours déjà au plafond, choisir le jour le moins chargé de la semaine la
-- moins chargée — jamais "le jour ouvré suivant" sans relire l'état courant.
```

Vérifier ensuite par la requête de densité (partie 6, et non par le seul contrôle « 0 week-end ») :
un correctif qui ne casse aucun week-end peut quand même échouer sur la densité.

**Étalement (jitter).** Un offset constant produit huit rendez-vous le même jour : dériver l'offset de
l'entité liée et faire varier aussi l'**heure** (règle 11).
Vérifier les dates dérivées — une formule bâclée `DATE '1990-01-01' + offset` a produit des candidats
de 9 ans.

**Statut ↔ date.** Un brouillon n'a pas de date de validation ; une pièce confirmée a une date de
confirmation passée ; une pièce terminée a une date de fin passée ; une annulation est postérieure à la
création. Corollaire du piège 26 (`entites-production-btp.md`) : sur des enregistrements créés **purement en SQL**, `real_*` ne doit
pas être identique à `planned_*` — petits deltas variés, dérivés du prévu pour rester idempotent.

**Distribution.** Statuts en pyramide plausible (~60 % terminés, 20 % en cours, 15 % planifiés, 5 %
annulés), pas 50 terminés le même jour ; densité plus forte sur les périodes récentes ; saisonnalité si
le métier en a une (`mode-b-volume.md` §2).

**Passé / présent / futur proche.** Calendrier, Gantt et plan de charge s'ouvrent sur aujourd'hui :
une démo entièrement dans le passé y affiche un écran vide. Prévoir du futur proche — ~40 % du plan de
charge dans le futur, des tâches en cours qui chevauchent la date
pivot, des échéances à venir.

**Cache et fuseau.** Un `UPDATE` passé pendant que l'application tourne n'apparaît pas en UI (cache
Hibernate L2) : prouver par requête, puis redémarrer avec l'accord de l'utilisateur. Et un décalage **horaire**
appliqué à une colonne DATE la fait basculer au jour précédent (partie 5).

---

## 5. Redatage — généralisation

Procédure de référence en place pour les flux valorisés : `socle-aos-baseline.md` §6. Généralisée à toute pièce redatée, elle tient en cinq règles.

1. **Ordre : entête → lignes → dérivés.** Décaler la seule entête produit « un ordre de mai qui
   consomme du stock en août ». Couvrir tout le graphe : entête, lignes, satellites (durées,
   mouvements, lignes de mouvement, date de calcul de la feuille de coût), puis le technique (§2.2).
2. **Atomicité.** Un redatage est une transaction unique ; un redatage partiel laisse une incohérence
   silencieuse, aucune erreur ne se lève. La garde d'idempotence repose sur une **clé métier stable**
   (code, nom, séquence), jamais sur une valeur dérivée de `NOW()` — vécu : 6 doublons créés par un
   re-run.
3. **Un offset unique ne suffit pas.** Il garde la cohérence relative mais importe la durée du jeu
   (« 5 serveurs fabriqués en 11 minutes », opérations de 39 ms), et un décalage horaire fait basculer
   les colonnes DATE au jour précédent. Pattern correct : (a) dates réelles d'entête = dates prévues ;
   (b) dates réelles des lignes reconstruites depuis la gamme avec une durée plancher ; (c) colonnes de
   type DATE recalées **explicitement**, jamais par arithmétique d'intervalle.
4. **Aucun recalcul après redatage.** Vécu : une feuille de coût juste à 1 636,50 € est passée à
   537 862,50 € après un recalcul post-redatage. Ordre imposé : jouer le flux → laisser le moteur
   calculer → **puis** redater → ne plus rien recalculer. Vaut pour tout bouton de recalcul, y compris
   « Recompute » sur une affaire (écrase les financiers statiques).
5. **Vérifier après, pas supposer.** Gardes mesurables : durée d'entête > 1 h, aucune durée d'opération
   < 1 min, aucun mouvement hors fenêtre, aucune date aval < date amont. C'est la partie 6.

---

## 6. Audit temporel

Requêtes génériques paramétrées par table et colonne, à **écrire** dans le script d'audit — non
exécutées ici. Convention de `../scripts/audit-completeness.sql` (`\set tag`, `current_setting`, scan
dynamique via `information_schema`, table temporaire `_tagged`).

**F0 — introspecter les colonnes de date avant tout contrôle.** Aucune source ne dit quelles colonnes
de date porte une table : le découvrir, jamais le supposer.

```sql
SELECT table_name, column_name, data_type, is_nullable
  FROM information_schema.columns
 WHERE table_schema='public' AND table_name = :'tbl'
   AND data_type IN ('date','timestamp without time zone','timestamp with time zone')
 ORDER BY ordinal_position;
```

**F1 — ordre entre pièces liées.** Déclarer les arêtes de la partie 3, les évaluer dynamiquement. Seule
la liste d'arêtes est propre au chantier.

```sql
DROP TABLE IF EXISTS _aretes;
CREATE TEMP TABLE _aretes(t_aval text, c_aval text, fk text, t_amont text, c_amont text);
INSERT INTO _aretes VALUES   -- à remplir depuis le contrat, APRÈS F0
  ('<table_aval>','<col_date_aval>','<col_fk>','<table_amont>','<col_date_amont>');

DO $$
DECLARE a record; n bigint;
BEGIN
  FOR a IN SELECT * FROM _aretes LOOP
    BEGIN
      EXECUTE format(
        'SELECT count(*) FROM %I av JOIN %I am ON am.id = av.%I
          WHERE av.%I IS NOT NULL AND am.%I IS NOT NULL AND av.%I::date < am.%I::date',
        a.t_aval, a.t_amont, a.fk, a.c_aval, a.c_amont, a.c_aval, a.c_amont) INTO n;
      RAISE NOTICE '%.% avant %.% : % violation(s)', a.t_aval,a.c_aval,a.t_amont,a.c_amont,n;
    EXCEPTION WHEN OTHERS THEN
      RAISE NOTICE 'arête % non évaluable (colonne ou FK absente) — repasser par F0', a.t_aval;
    END;
  END LOOP;
END $$;
```

**F2 — dates hors fenêtre du contrat** (`-v debut=... -v fin=...`), sur toutes les colonnes de date des
tables taguées.

```sql
DO $$
DECLARE r record; n bigint;
BEGIN
  FOR r IN SELECT c.table_name, c.column_name FROM information_schema.columns c
            WHERE c.table_schema='public' AND c.table_name IN (SELECT tbl FROM _tagged)
              AND c.data_type IN ('date','timestamp without time zone','timestamp with time zone')
              AND c.column_name NOT IN ('created_on','updated_on')
  LOOP
    EXECUTE format('SELECT count(*) FROM %I WHERE import_origin=%L AND %I IS NOT NULL
                      AND (%I::date < %L::date OR %I::date > %L::date)',
      r.table_name, current_setting('demo.tag'), r.column_name,
      r.column_name, current_setting('demo.debut'),
      r.column_name, current_setting('demo.fin')) INTO n;
    IF n > 0 THEN RAISE NOTICE '%.% : % ligne(s) hors fenêtre', r.table_name, r.column_name, n; END IF;
  END LOOP;
END $$;
```

**F3 — week-ends sur une colonne qui n'en veut pas** (jours pointés, dates de commande, de facture, de
livraison).

```sql
SELECT count(*) AS lignes_week_end FROM <tbl>
 WHERE <col> IS NOT NULL AND EXTRACT(dow FROM <col>) IN (0,6);
```

**F4 — `created_on` en rafale, et décorrélé de la date métier.**

```sql
SELECT date_trunc('second', created_on) AS seconde, count(*) AS n
  FROM <tbl> WHERE import_origin = current_setting('demo.tag')
 GROUP BY 1 HAVING count(*) > 5 ORDER BY n DESC;

SELECT count(*) AS created_on_decorrele FROM <tbl>
 WHERE <col_date_metier> IS NOT NULL
   AND abs(EXTRACT(epoch FROM created_on - <col_date_metier>::timestamp)) > 86400*3;
```

> Attention : **Avant d'écrire une assertion temporelle, vérifier si la colonne est `DATE` ou `TIMESTAMP`**
> (piège 32 : le type réel s'introspecte, il ne se devine pas au nom du champ). F4 ne s'applique
> qu'aux colonnes à la seconde ; sur une `DATE`, plusieurs enregistrements le même jour sont
> normaux. *Coût payé le 2026-09-03 : `project_project_task.completed_on` supposée timestamp — la
> dispersion horaire écrite était silencieusement tronquée, et l'assertion anti-rafale se
> déclenchait sur des données justes (9 tâches d'un même chantier achevées le même jour).*

**F5 — statut ↔ date contradictoires.** À instancier par entité après F0 et après avoir lu les valeurs
valides de la sélection (`../scripts/introspect.sh` les sort).

```sql
-- a) statut terminal, date de fin dans le futur
SELECT count(*) FROM <tbl> WHERE <col_statut> IN (<terminaux>) AND <col_date_fin> > CURRENT_DATE;
-- b) brouillon portant une date de validation
SELECT count(*) FROM <tbl> WHERE <col_statut> = <brouillon> AND <col_date_validation> IS NOT NULL;
-- c) statut terminal sans date de fin
SELECT count(*) FROM <tbl> WHERE <col_statut> IN (<terminaux>) AND <col_date_fin> IS NULL;
```

**F6 — enfants hors fenêtre du parent** (tâche dans l'affaire, jour pointé dans la feuille, créneau
dans la tâche) : même patron que F1, avec deux comparaisons — `enfant.debut < parent.debut` et
`enfant.fin > parent.fin`.

**F7 — période comptable manquante ou trop grosse** (contrôle du piège 48).

```sql
SELECT count(*) AS pieces_sans_periode_couvrante FROM <tbl> p
 WHERE NOT EXISTS (SELECT 1 FROM base_period per
                    WHERE p.<col_date> BETWEEN per.from_date AND per.to_date);
SELECT id, from_date, to_date, (to_date - from_date) AS jours
  FROM base_period WHERE (to_date - from_date) > 40;  -- > ~1 mois n'illustre rien de mensuel
```

**F8 — piège 112 : engagement contractuel « aucune opportunité ouverte sans événement à venir »,
mesuré nulle part par défaut.** Un contrat de scénario peut porter une exigence de cohérence
temporelle qui n'est couverte par AUCUNE des dimensions numérotées ci-dessus (elle ne teste ni une
précédence entre deux dates d'une même ligne — F1 —, ni une fenêtre — F2 —, ni un statut — F5 — mais
l'existence d'au moins une ligne ENFANT future rattachée au parent). Vécu sur le chantier package
CRM : le contrat l'exigeait explicitement, aucun des rapports d'exécution ne l'a mesuré avant le
challenge adverse — qui a trouvé 36 opportunités ouvertes sur 38 sans événement à venir (35 sans
AUCUN événement du tout).

```sql
SELECT count(*) FROM <tbl_parent> p
 JOIN <tbl_statut> s ON s.id = p.<col_statut> AND s.is_open
 WHERE NOT EXISTS (SELECT 1 FROM <tbl_enfant> e
                    WHERE e.<fk_parent> = p.id AND e.<col_date> > CURRENT_DATE);
```

**Ce que ça généralise** : tout engagement contractuel de la forme « chaque X ouvert a au moins un Y
futur » (une opportunité et son prochain événement, une affaire ouverte et sa prochaine échéance)
n'est PAS couvert par les dimensions numérotées existantes — il doit être décliné en une requête `F8`
dédiée, dérivée du contrat ligne à ligne (règle 9 de SKILL.md), et ajouté explicitement à la checklist
de la dimension 11 pour ce chantier plutôt que supposé couvert par F1/F6.

**Intégration dans `../scripts/audit-completeness.sql`** (décrit, non édité) : ajouter une **dimension 11
— cohérence temporelle**, bâtie comme la dimension 7 (prose courte disant pourquoi elle est mécanique
et non documentaire, puis requêtes). Contenu : F1 (les arêtes déclarées sont la seule partie à
maintenir par chantier), F2, F3, F4, F5, F7 ; F0 et F6 restent des outils d'instanciation.
Justification du « mécanique » : la règle 11 est déjà écrite dans SKILL.md et a été violée quand même —
la prose n'a pas mordu.

---

## 7. Pièges réutilisés et points à vérifier

**Repris de SKILL.md** : règle 11 (le temps est une relation ; offset dérivé de l'entité liée) ;
règle 12 (le SQL pose un état, il ne simule pas une transition) ; règle zéro (ne jamais trier via
`created_on`) ; piège 26 (`real_*` ≠ `planned_*` sur un OF terminé, `entites-production-btp.md`) ;
piège 48 (FK vers une période = granularité métier, `methode-coherence.md`) ; piège 64 (cycles FK
via `created_by` / `updated_by`, `methode-rejouabilite.md`) ; piège 73 (séquence non avancée =
collision au `onSave`, `methode-ecriture-sql.md`) ; piège 74 (`crm_opportunity.order_by_state`,
`methode-coherence.md`) ; l'ancienne section « Transactionnel & redatage », désormais
`socle-aos-baseline.md` §6 (généralisée en partie 5, non dupliquée) ; `mode-b-volume.md` §2
(distribution des statuts et des dates, filtrage des week-ends) ; `socle-aos-baseline.md` §5
(crédibilité) et §6 (frontière UI/SQL).

**Nouveaux dans cette fiche** : piège 111 (correctif « pas de week-end » naïf qui empile sur le
prochain jour ouvré — parade par allocateur avec plafonds, partie 4) ; piège 112 (engagement
contractuel « aucun X ouvert sans Y futur », non couvert par les dimensions numérotées existantes —
F8, partie 6) ; piège 139 (deux pièges PostgreSQL de rétro-datation, après cette partie) ; pièges 170 à
173 et 185 (chronologie d'un rejeu piloté par l'API, partie 8).

**Faits datés cités** : feuille de temps sans FK période en 9.0.11 (2026-08-28), déboursé
main-d'œuvre sur feuille validée (2026-07-28), champs de temps natifs inexploitables (2026-08-24).

**Marqué « à vérifier sur la base cible »** :

1. Quelles entités du périmètre affichent un panneau de suivi peuplé, et si les tables de
   message/audit associées portent leurs propres horodatages à redater (§2.2).
2. Quelles périodes et quels exercices existent réellement, et si la fenêtre du contrat en sort (§3,
   facturation).
3. Les noms et types exacts des colonnes de date de chaque table du périmètre — jamais supposés,
   obtenus par F0 (parties 3 et 6).
4. Par chaîne : la présence d'une distinction date prévue / date réelle, et l'existence d'un bouton
   global de transition avant de budgéter N clics (§3, achats/stock et production).

**Non traité volontairement** : la construction de l'horloge elle-même (date pivot, fenêtre, jalons)
appartient au skill amont et arrive par le contrat.

---

### 139. Deux pièges PostgreSQL rencontrés dans les passes de rétro-datation

`[prouvé 2026-09-22]` Ni l'un ni l'autre n'est un piège Axelor : ce sont deux règles de typage
PostgreSQL qui ne se manifestent **que** dans les passes de redatage, parce que ce sont les seules qui
dérivent un intervalle d'une colonne de la base. Les deux arrêtent la passe en cours de transaction.

**1. `make_interval` n'accepte que des `integer`.** Une expression construite sur une colonne `bigint`
— un identifiant, une durée en secondes — lève :

```
ERROR:  function make_interval(mins => bigint) does not exist
```

Le message suggère que la fonction n'existe pas ; elle existe, c'est le **type de l'argument** qui ne
passe pas, et PostgreSQL ne remonte pas implicitement un `bigint` vers un `integer`. Caster
explicitement : `make_interval(mins => ((id * 37) % 480)::int)`.

**2. La soustraction de deux `date` rend un ENTIER de jours, pas un intervalle.**

```
ERROR:  function pg_catalog.extract(unknown, integer) does not exist
```

Là encore le message accuse `extract`, alors que la faute est en amont : `d1 - d2` sur deux colonnes
`DATE` a déjà produit un `integer`, et `EXTRACT(EPOCH FROM …)` n'a plus d'intervalle à lire. Sur deux
`TIMESTAMP` la même expression rend bien un intervalle — d'où l'expression qui « marche sur une table
et pas sur l'autre ». Écarts en jours : `(d1 - d2)` suffit, sans `EXTRACT`. Pour un écart en secondes
entre deux dates : `(d1 - d2) * 86400`, ou caster en `timestamp` d'abord.

**Rappel** : le type réel des colonnes de date s'introspecte, il ne se devine pas au nom du champ
(piège 32, et l'avertissement de F4 ci-dessus qui portait déjà sur la même confusion `DATE` /
`TIMESTAMP` — ici du côté écriture, là du côté assertion).

## 8. Chronologie d'un rejeu piloté par l'API — rejeu de la démo BTP de référence (2026-09-26)

Un rejeu par l'API joue les transitions du moteur sous date simulée (`pieges-runtime-aos-9-1-7.md` §6), date par date.
Les pièges ci-dessous portent sur l'ordre de ces transitions. Méthode du rejeu contrôlé : `methode-rejeu-controle.md`.

### 170. Une pièce qui change le marché se confirme DANS la boucle chronologique, pas avant

Confirmer avenant et travaux supplémentaires avant la boucle des situations fait porter leurs montants par les
situations ANTÉRIEURES à leur date (l'avancement s'applique au marché courant). Les cumuls restent justes, les dates
sont anachroniques pour un œil expert. *Constaté le 2026-09-26 : situations de mars de Jean-Macé calculées sur un
marché qui inclut l'avenant de mai. Limite connue, non
corrigée : le rejeu hébergé du même soir a gardé cet ordre (avenant confirmé avant la boucle).*

**À faire :** mettre la confirmation de chaque avenant et TS comme un **événement** de la boucle globale triée par date,
au même titre que les situations (pourquoi une boucle unique : piège 185).

### 171. Un geste utilisateur daté « du jour » se fait sous date simulée, script en pause

Certains boutons datent leur effet du jour (confirmation d'un paiement direct, commande générée par un assistant) :
joués après le rejeu, ils tombent à la date réelle, hors récit, et ne touchent aucune pièce passée. **À faire :**
arrêter le script à la date du geste SANS vider la date simulée (pause volontaire), faire le geste, puis reprendre
l'étape de façon idempotente ; la reprise vide la date. La date de l'application est alors celle du récit **pour tout
le monde** : personne d'autre sur l'instance pendant la pause. *Fait ainsi le 2026-09-26 sur l'instance hébergée
de la démo BTP de référence : pause au 31/03, geste de sous-traitance reproduit par script sous cette date, contrôle qui exige la date du
31/03 avant le geste, puis reprise (lignes 09a à 09b du déroulé).* Un geste
rejouable se scripte : `methode-rejeu-controle.md` §5.

### 172. Un rejeu correctif de règlements après coup casse l'ordre du journal de banque

Créer après coup des règlements datés de juin quand ceux de septembre existent donne une numérotation du journal de
banque non chronologique (contrôle FEC strict). Le moteur ne refuse rien. *Constaté le 2026-09-26.* **À faire :** si la numérotation compte, restaurer le palier et rejouer ; sinon
l'écrire comme limite connue.

### 173. Une pièce à échéance se date par rapport au jour de la démo, pas au jour du geste

Une attestation URSSAF « valable 6 mois » émise le 16/03 expire le 16/09 : le jour du salon (28/09), elle s'affiche
« Valide » avec une date dépassée. Les pièces à échéance (attestations, assurances,
cautions) se datent pour être valides le jour de la démo — ou volontairement échues quand le récit le veut (démo BTP de référence :
décennale du loueur expirée au 15/09, posée dans le référentiel de données du rejeu).
*Relevé le 2026-09-26 : statut « Valide », échéance passée depuis le 16/09 ; l'effet
le jour du salon est une projection.*

### 185. Toutes les pièces comptables d'une société se jouent dans UNE boucle triée par date — AOS refuse de ventiler une facture antérieure à la dernière ventilée

`[lu dans les sources 9.1.6 le 2026-09-24 ; refus jamais rencontré à l'exécution]` `VentilateState.checkInvoiceDate`
(axelor-account, l. 226-270) refuse de ventiler une facture si une facture déjà ventilée de la même société et du même
type d'opération porte une date postérieure (borné au mois ou à l'année si la numérotation s'y remet à zéro). Le rejeu de la démo BTP de référence a été écrit pour l'éviter. Deux conséquences :

1. un rejeu qui joue une affaire après l'autre bute sur la ventilation dès la deuxième : toutes les transitions de
   toutes les affaires se jouent dans **une seule boucle triée par date** (relecture adverse du 24/09,
   point B6 ; tri global dans la bibliothèque de dates du kit de rejeu) ;
2. la démo Supply Chain d'AOS ventile 7 factures clients **au jour de son import** : importée à la date réelle, elle
   bloque tout antidatage de la société. **Parade prouvée le 2026-09-25** sur l'instance hébergée de la démo BTP de référence (AOS 9.1.7 /
   AOP EE 8.2.4-SNAPSHOT) : premier démarrage sans démo, date simulée posée avant la fenêtre du récit (05/01/2026), puis import
   des démos app par app ; les 7 factures sont datées du 05/01 et tout l'historique postérieur reste ventilable.

Même relecture du 24/09, non éprouvé : ventiler chaque facture à son tour, pas en une passe finale —
l'avancement déjà facturé et les temps facturés ne se mettent à jour qu'à la ventilation, d'où une double facturation.
