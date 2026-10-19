# Méthode — audit

**Pièges couverts par cette fiche :**

- 38. « Menu non vide » ≠ « exploitable »
- 39. Prendre le record ID 1 du clone comme MODÈLE DE SHAPE
- 40. Une FK NOT NULL vers `MetaFile` signifie « c'est un document à téléverser »
- 52. Cache Hibernate de second niveau — piège de vérification n°1
- 96. Le cache L2 ne masque pas un `UPDATE` SQL : le prochain save moteur le RÉVERTIT
- 106. Un échec fonctionnel AOS peut arriver en `info`, pas en `error` — un audit qui ne lit qu'`error` le compte pour un succès
- 107. Un périmètre de tag VIDE rend les dimensions vertes sur RIEN — l'audit doit échouer, pas se taire
- 169. Un peuplement par l'API ne porte d'étiquette d'import que si le script la pose — la poser à chaque création, sauf là où une vue l'affiche
- 188. L'audit écrit dans la base qu'il audite — et un `BEGIN` sans point-virgule devant `\i` ne le met pas en transaction
- 114. Un rapport d'exécutant peut affirmer un fait faux — re-mesurer avant d'écrire une vague qui en dépend
- 140. Une valeur uniforme PAR FAMILLE est un copier-coller que la dimension 4 ne voit pas
- 141. Un rechargement de module ne supprime JAMAIS ce qui a disparu du XML
- 142. `current_date + 15` sans unité échoue sur Hibernate 6 — et un domaine se teste avant d'être livré
- 149. Écrit dans un rapport n'est pas annoncé — et un attendu d'UAT se relève à l'écran, pas par raisonnement
- 53. État runtime = preuve applicative
- 54. `ClassNotFoundException` dans les logs = méta morte d'un module retiré
- 55. Les angles morts d'un audit de couverture par les menus
- 56. Relire `studio_app.active` au moment d'agir
- 75. `count()` MENT SUR LES ZÉROS
- 76. `= false` EXCLUT LES NULL — un booléen non initialisé rend l'enregistrement invisible
- 81. Borner ses assertions à son périmètre
- 82. Auditer contre le CONTRAT, pas contre son propre script
- 91. Vérifier dans l'UI : lire le panneau ACTIF, pas `document.body`
- 92. Le piège 70 n'a pas UN niveau, il en a QUATRE — et l'audit ne regardait que le premier
- 94. Vérifier par l'API REST : omettre la clé `data` désactive le filtre `archived`
- 18. Vérification REST : `criteria` + `operator:"like"` échoue silencieusement — utiliser `_domain`
- 90. `meta_action` / `meta_view` peuvent porter des DOUBLONS de nom

Pièges 18 et 90 rattachés ici : vérification runtime / REST, même famille que 91 et 94.

## Complétude : le header ne suffit jamais


### 38. « Menu non vide » ≠ « exploitable »
Croiser l'audit de couverture des menus avec un audit de **relations** (O2M/M2M via `meta_field`) avant
de déclarer une table faite. Une session de formation sans inscrits, un appel d'offres sans besoin ni
fournisseur ni offre, un modèle d'échéancier sans lignes : « remplis » et inutilisables.

### 39. Prendre le record ID 1 du clone comme MODÈLE DE SHAPE
Il révèle les satellites attendus et le **format réel** d'un champ. Deux cas vécus : une description
de trame d'entretien est un **document HTML complet** (grille d'en-tête + tableaux de notation), pas
une phrase ; un profil de numéro de suivi porte **4 formules de calcul** liées en M2M.

### 40. Une FK NOT NULL vers `MetaFile` signifie « c'est un document à téléverser »
`hr_employment_contract_template.meta_file`, `crm_catalog.pdf_file` : l'enregistrement **est** le
fichier. Fabriquer un `MetaFile` bidon produit une fiche incohérente → classer « justifié vide ».

## Vérification : pourquoi l'UI « mentait »


### 52. Cache Hibernate de second niveau — piège de vérification n°1
Un UPDATE SQL exécuté pendant que l'app **tourne** n'apparaît pas en UI : les entités déjà chargées
sont servies depuis le cache. L'utilisateur voit des champs « toujours vides » alors qu'ils sont
remplis en base. → prouver par requête SQL, puis **redémarrer** l'application. Ne jamais conclure
« pas rempli » depuis l'UI seule, ni rejouer le SQL.

### 53. État runtime = preuve applicative
`ss`/`pgrep` peuvent être muets ou absents. Utiliser `curl -o /dev/null -w "%{http_code}"`.
De même, **le titre de l'application (`application.name`) est du texte libre** : il peut annoncer un
autre nom et une autre version que la réalité. La seule preuve d'identité d'un environnement est le
`db.default.url` du **WAR déployé**, pas des sources du worktree.

### 54. `ClassNotFoundException` dans les logs = méta morte d'un module retiré
Une table du clone dont la classe Java est absente du build fait planter le menu quoi qu'on y mette →
« justifié vide », ne jamais peupler. Et un **dashlet custom résiduel** (module retiré, méta
subsistante) avec du SQL **en dur** sur une table absente provoque un 500 à l'ouverture d'un écran :
le retrait est chirurgical — supprimer la vue **et l'extension de formulaire qui l'injecte** ; le
formulaire de base et les autres extensions restent intacts, et le cache de vues se rafraîchit sans
redémarrage. Indice de diagnostic : si une synchro de schéma au boot **ne crée pas** la table
manquante, c'est que le mapping Hibernate ne la connaît pas → la requête est écrite à la main.

### 55. Les angles morts d'un audit de couverture par les menus
Trois trous structurels dans `meta_menu → meta_action → meta_model → table_name` :
1. **Héritage single-table : `meta_model.table_name` est VIDE** → un filtre `table_name IS NOT NULL`
   exclut **silencieusement** ces entités. Vérifié : 8 modèles sur 870, dont **`Event`** (l'entité CRM
   la plus visible). Résoudre à la main via la table parente + le discriminant `dtype`.
2. **Les dépendances NOT NULL n'ont pas forcément de menu** → invisibles mais bloquantes.
3. **Classer les buckets par le MODULE DU MENU**, pas par un regex sur le nom de table : un regex
   d'exclusion a masqué `base_tag` (vide, alimentant 3 panneaux Tags) simplement parce qu'un module
   inactif y touchait aussi. Une table atteinte par plusieurs modules prend le bucket le **plus
   permissif**.

### 56. Relire `studio_app.active` au moment d'agir
La politique d'apps est une donnée **vivante** : des apps désactivées lors de l'audit initial étaient
actives quelques heures plus tard, changeant le périmètre « aucun écran vide ».

### 75. `count()` MENT SUR LES ZÉROS

```sql
-- FAUX : annonce « 30 leads notés » alors que les 30 valent 0
SELECT count(lead_scoring_select) FROM crm_lead;
-- JUSTE
SELECT count(*) FILTER (WHERE COALESCE(lead_scoring_select,0) BETWEEN 1 AND 5) FROM crm_lead;
```

`count(col)` compte les non-NULL. Un `0`, une chaîne vide, un `false` par défaut sont des
**absences déguisées** que `count()` compte comme des présences. Auditer les valeurs UTILES.
Ce piège a produit un faux « c'est rempli » dans la même session où il était déjà documenté :
le connaître ne suffit pas, il faut écrire l'audit en conséquence.

### 76. `= false` EXCLUT LES NULL — un booléen non initialisé rend l'enregistrement invisible

Le domaine de la vue Articles porte `self.expense = false`. Vingt produits avaient `expense` à
NULL : présents en base, sélectionnables ailleurs, **jamais affichés au catalogue**. Même classe
que `is_model`, `sellable`, `purchasable`.

Ne pas se contenter de « le booléen a une valeur » : vérifier que la valeur est celle que **le
domaine des vues** attend. Requête de détection générale :

```sql
SELECT count(*) FROM base_product WHERE expense IS NULL;   -- puis pour chaque booléen du domaine
```

### 81. Borner ses assertions à son périmètre

Une assertion « aucun libellé ne cite son client » a fait échouer la vague sur deux projets du
socle AOS, qui suivent cette convention depuis toujours. **Une vague n'a pas à échouer sur des
données qu'elle ne touche pas.** Nuance : quand l'écart révélerait un vrai défaut ailleurs, garder
l'assertion large et le signaler — mais alors le dire, pas le subir.

### 82. Auditer contre le CONTRAT, pas contre son propre script

Seize contrôles de complétude ont rendu « 0 anomalie » alors qu'un engagement du scénario n'était
pas tenu : `supplier_delivery_time` restait NULL sur les 13 matériels dont le contrat promettait
« un délai standard ». Les contrôles vérifiaient ce que le script **écrit**, jamais ce que le
scénario **promet** — un audit fermé sur lui-même, structurellement incapable de voir cette classe
de défaut. Relire le scénario ligne à ligne et en dériver les assertions.

Corollaire mesurable : `79 des 85 produits du socle portaient ce champ`. Un champ vide sur les
créations alors que le socle le renseigne est un signal fort — **comparer au socle**, pas au vide.

### 18. Vérification REST : `criteria` + `operator:"like"` échoue silencieusement — utiliser `_domain`

Lors de la vérification de données de démo via l'endpoint REST `/search`, un bloc `data.criteria` avec `operator:"like"` renvoie `{"status":0,"offset":0}` (pas de `total`, pas de `data`) sur AOS 9.0.8 — un échec silencieux, pas une erreur. `operator:"="` fonctionne. Pour les filtres substring/like, utiliser `data._domain` : `{"data":{"_domain":"self.seq like 'PREFIX-%'"}}`. Les champs pointés M2M/M2O dans `fields` se résolvent dans la réponse (ex. `parentTrackingNumberSet` renvoie les lignes cibles) — pratique pour asserter des liens de généalogie.

### 90. `meta_action` / `meta_view` peuvent porter des DOUBLONS de nom

Lire une action avec `LIMIT 1` a donné une version obsolète, sans une clause `self.expense = false`
que portait la ligne réellement servie — d'où une demi-heure passée à chasser un faux défaut de
visibilité. Compter avant de lire :

```sql
SELECT name, count(*) FROM meta_action GROUP BY 1 HAVING count(*) > 1;
```

Et `meta_action` est servi depuis le cache MetaStore : **toute modification SQL exige un
redémarrage** pour être prise en compte. Une vue au nom NEUF, elle, n'est pas encore en cache.

### 91. Vérifier dans l'UI : lire le panneau ACTIF, pas `document.body`

AOS garde tous les onglets ouverts **montés dans le DOM**. Lire `document.body.innerText` ramène
les compteurs et les filtres d'un onglet précédent : un compteur « 45 sur 45 » venait du tableau de
bord RH resté ouvert, pas de la grille produits examinée. Cibler
`[role="tabpanel"]` et prendre le dernier, ou vérifier par l'API avec le jeton CSRF plutôt que par
le DOM. Corollaire : une mesure d'écran qui contredit la base est d'abord suspecte **comme mesure**.

### 92. Le piège 70 n'a pas UN niveau, il en a QUATRE — et l'audit ne regardait que le premier

Le piège 70 dit « renommer `name` sans recalculer `full_name` = renommage invisible ». Vérifié le
2026-08-11 sur une base de démo ESN : c'est un cas particulier d'une règle plus large, et la version courte
laisse passer l'essentiel. Renommer 95 projets a laissé du vocabulaire périmé sur **quatre**
niveaux de dénormalisation en cascade :

```
project_project.name                                    ← renommé par la vague 06
  └→ project_project_task.name                          ← resté BTP (190 tâches)
       └→ project_project_task.full_name  = '#'||id||' '||name
            └→ project_project_planning_time.title      = task.name (268) | task.full_name (2)
                 └→ …planning_time.description = 'Allocation <employé> sur <task.name>'
```

Et un CINQUIÈME, sans lien de parenté avec les tâches, qui était le plus visible de tous :
**95 lignes de plan de charge sans tâche** (`project_task IS NULL`) portant `'Pilotage — ' ||
<ancien nom du projet>` — donc l'ouvrage et la commune du métier précédent, en plein écran de
plan de charge.

Trois leçons, dans l'ordre où elles coûtent cher :

1. **Chercher les dénormalisations par la STRUCTURE, pas par la mémoire.** Avant de renommer une
   entité, énumérer les colonnes texte des tables qui la référencent et tester lesquelles
   contiennent effectivement une de ses valeurs :
   ```sql
   SELECT count(*) FROM <table_enfant> e JOIN <table_parent> p ON p.id = e.<fk>
    WHERE e.<col_texte> LIKE '%' || p.name || '%';
   ```
   Un renommage n'est terminé que lorsque ce compte est nul sur toutes les colonnes candidates.
2. **Les enfants ORPHELINS de la relation évidente sont les plus exposés.** Les 95 lignes sans
   tâche étaient invisibles à tout contrôle passant par `project_task`. Balayer aussi les lignes
   où la FK attendue est NULL.
3. **Un format dénormalisé peut être MULTIPLE.** Ici 268 lignes copiaient `task.name` et 2
   copiaient `task.full_name`. Réaligner tout le monde sur un seul format écrase une distinction
   produite par l'application. Le discriminant doit être **stable à travers le renommage** :
   `title <> t.full_name` est faux (à ce stade la tâche est déjà renommée, la ligne porte
   l'ANCIEN full_name et passe le test) ; `title LIKE '#'||t.id||' %'` est la signature du format
   et reste vraie.

Attention : **Le motif de détection produit des faux positifs qui détruisent des données saines.** Un
premier balayage avait signalé `planning_time.full_name` : faux positif, le motif `MOE` matchait
le nom d'un salarié (« DE**MOE**RP »). Cette colonne suit la formule `<employé> - <projet> - <date>` et
ne cite jamais la tâche — la « corriger » aurait cassé une convention correcte. De même, `travaux`
et `ouvrage` nus matchent des libellés du **plan comptable français**. Qualifier chaque écart
avant de l'annoncer (cf. Phase 4), et exclure des motifs les mots trop courants.

**Corollaire pour l'audit** : la dimension 7 de `audit-completeness.sql` ne couvrait que
`base_partner` et `project_project`. Elle est étendue aux tâches et au plan de charge. Le principe
est généralisable : tout champ `namecolumn` ou recopié doit avoir sa ligne dans la dimension 7,
sinon la désynchronisation vit indéfiniment sans qu'aucun contrôle ne la voie.


*(Renvoi résolu : piège 70 → `references/entites-tiers-contacts.md`.)*

### 94. Vérifier par l'API REST : omettre la clé `data` désactive le filtre `archived`

L'API REST est la bonne parade au DOM qui mente sur l'onglet actif (piège 91), et elle prouve en
prime que le cache L2 sert bien les nouvelles valeurs. Mais elle a un piège propre, et il annule
tout le bénéfice de la méthode : **la clé `data` du payload commande le filtre des archivés.**

Mesuré le 2026-08-24 sur une base de démo ESN, table `contract_contract` — 2 lignes dont 1 archivée :

```bash
# FAUX : clé "data" ABSENTE → 2 lignes. On mesure la BASE, pas l'écran.
-d '{"offset":0,"limit":10,"fields":["id"]}'
# JUSTE : clé "data" présente, même vide → 1 ligne. C'est ce que l'utilisateur voit.
-d '{"offset":0,"limit":10,"fields":["id"],"data":{}}'
# = case « Afficher les archivés » de l'UI
-d '{"offset":0,"limit":10,"fields":["id"],"data":{"_archived":true}}'
```

Un contrôle qui omet `data` reproduit donc **exactement** l'erreur que l'API devait éviter, et il
la reproduit en donnant l'illusion d'avoir interrogé le moteur. Le symptôme est traître : les
chiffres tombent juste tant que la table n'a aucun archivé, puis divergent silencieusement le jour
où il y en a — ici « 2 contrats visibles » au lieu d'un seul, ce qui a failli faire rouvrir un
arbitrage déjà tranché.

**Toujours passer `data`**, au minimum `{}`. Pour reproduire un écran précis, y mettre le `_domain`
lu dans l'`action-view` correspondante (`meta_action`) plutôt qu'un domaine inventé : c'est le seul
moyen de compter ce que le menu compte. Et se souvenir que le domaine du menu porte ses propres
filtres — sur AOS, le menu Commandes filtre `self.statusSelect = 3` STRICTEMENT, si bien qu'une
commande terminée (statut 4) n'y figure pas et manque à tout inventaire fait depuis cet écran.

*Dimensions de `scripts/audit-completeness.sql` : 10 dimensions numérotées (1, 1bis, 2..10) au moment de cette découpe — voir le script pour le détail de chacune.*

### 96. Le cache L2 ne masque pas un `UPDATE` SQL : le prochain save moteur le RÉVERTIT

Le piège 52 dit « l'UPDATE SQL n'apparaît pas en UI tant que l'application n'a pas redémarré ». C'est
plus grave : il peut être **détruit**. Mesuré le 2026-09-03 (AOS 9.1.6 / EE 8.2.3, base `<base>`) :

```
UPDATE project_project SET code = NULL WHERE id = 900010;   -- en base : code = NULL
save REST du projet, payload SANS la clé 'code'             -> status:0
en base : version = 4, code = 'ZSC3P'                       -- la valeur d'AVANT l'UPDATE, réécrite
```

`JPA.edit` n'applique que les clés du payload sur l'entité **trouvée** ; l'entité vient du cache de
second niveau avec l'ancienne valeur, et le flush la réécrit entière. Un `UPDATE` SQL joué pendant que
l'application tourne est donc invisible (52) **et** réversible par tout save ultérieur, sans trace, y
compris un simple enregistrement de la fiche pendant la démo.

Parade : sur une application qui tourne, le SQL de correction précède toute passe moteur sur les mêmes
enregistrements, ou repasse par le moteur (règle 12, ordonnancement en Phase 3) ; sinon redémarrer
l'application (avec l'accord de l'utilisateur) avant de démontrer.

### 106. Un échec fonctionnel AOS peut arriver en `info`, pas en `error` — un audit qui ne lit qu'`error` le compte pour un succès

Le motif `HTTP 200 + status:-1` est connu. Il en existe deux autres, plus discrets, et ils changent la façon d'écrire un contrôle :

- **`status:0` avec un objet `error` dans `data`** — l'échec fonctionnel classique des actions de chaîne.
- **`status:0` avec un objet `info`** — quand le contrôleur rattrape par la surcharge à deux arguments de `TraceBackService.trace(response, e)`, qui vaut `ResponseMessageType.INFORMATION`. Le message est souvent excellent et précis ; il est simplement classé information. À l'écran, l'utilisateur voit une popup d'information sur une opération qui n'a **rien** créé.

Vécu : un cas s'est d'abord lu « échec silencieux, rien créé, aucun message » ; le corps brut portait un `info` parfaitement explicite. Le contrôle avait transformé un échec en succès.

**Correctif** : tout contrôle par `/ws/action` extrait `error`, `info`, `alert` ET la présence de `causeStack`, et conclut sur la NATURE (explicite / classé information / muet) plutôt que sur un booléen. Et quand un résultat surprend, imprimer le corps brut avant d'en tirer une conclusion — c'est ce qui a réfuté la mauvaise lecture.

Complément du 2026-09-26 : « Merci de rentrer un planning des jours fériés pour l'employé… » (validation
d'un lot de pointage refusée) arrive sous `info` avec `status: 0` et ne contient aucun des mots d'échec
habituels ; la liste des marqueurs d'échec se tient à jour à chaque refus nouveau (« merci de » ajouté à celle du
client REST du rejeu de la démo BTP de référence). Même piège côté script : un avertissement que le script
écrit lui-même (réserve, échec avalé puis journalisé) doit figurer parmi les textes qui arrêtent le rejeu — relevé par
la relecture adverse du 26/09 (défaut 10), non corrigé
dans le lanceur du rejeu de la démo BTP de référence, où c'est le contrôle suivant qui l'aurait vu.

### 107. Un périmètre de tag VIDE rend les dimensions vertes sur RIEN — l'audit doit échouer, pas se taire

`scripts/audit-completeness.sql` scope toutes ses dimensions sur `_tagged` (les tables où
`import_origin = :tag` a au moins une ligne, cf. règle zéro de SKILL.md). Si le tag n'a jamais été posé
à l'écriture — faute de frappe, oubli sur une vague, tag différent de celui attendu — `_tagged` est
vide et les dimensions tournent sur un périmètre nul : **« FIN DE L'AUDIT », 0 erreur psql, 0
anomalie sur toutes les dimensions**, alors qu'aucune ligne n'a été mesurée. C'est un faux vert
structurellement indiscernable d'un vrai « tout est conforme », et il est apparu concrètement sur
le chantier package CRM : plusieurs tables créées (26 logos `meta_file` uploadés par API) n'avaient
jamais été taguées à l'écriture, et seule une passe dédiée (méthode delta
contre le socle : `id > max(id) socle`) les a rattrapées.

**Parade testée** (patch validé le 2026-09-08 sur `<base>` : passe avec `-v tag=<tag>`,
lève avec un tag inexistant) — juste après la construction de `_tagged`, avant la dimension 1 :

```sql
DO $$
BEGIN
  IF (SELECT count(*) FROM _tagged) = 0 THEN
    RAISE EXCEPTION 'PERIMETRE VIDE : aucune table ne porte import_origin = %. L''audit ne peut
rien mesurer -- verifier que le tag a bien ete pose a l''ecriture (piege 107), pas que la base
est vide.', current_setting('demo.tag');
  END IF;
END $$;
```

Un périmètre vide n'est presque jamais « il n'y avait rien à peupler » (le cas où le tag est
correct et le jeu réellement minuscule) : c'est presque toujours « le tag n'a pas été posé ». Faire
échouer dur ici coûte un faux positif rare et évite un audit qui ment par construction.

### 169. Un peuplement par l'API ne porte d'étiquette d'import que si le script la pose — la poser à chaque création, sauf là où une vue l'affiche

Le moteur n'étiquette rien : un enregistrement créé par REST, ou par une action du moteur (chantier généré, situation,
feuille de temps), n'a pas d'`import_origin`. L'audit s'arrête alors sur « PERIMETRE VIDE » (garde du piège 107) : les
dimensions 1 à 12 ne mesurent rien, seule la 13 (toute la base) parle. *Constaté le 2026-09-26 vers 1 h sur le rejeu
local de la démo BTP de référence.* `importOrigin` s'écrit par REST comme
un champ ordinaire (vérifié le 2026-09-26 sur `base_site`, relu en base).

**À faire :** poser `importOrigin: <tag>` dans chaque charge utile de création du script, et lancer l'audit avec ce
tag. *Appliqué à l'étape 10 du rejeu de la démo BTP de référence le 2026-09-26 : 13 tables étiquetées (commandes et lignes d'achat,
factures, historique d'avancement, lots de pointage, paie, conversions…), audit sur ses 13 dimensions, 0 erreur.* Deux limites :

- **pas sur une entité dont une vue affiche le champ** : la commande client le rend en badge dans son en-tête
  (piège 98) — une valeur par défaut du client REST l'y poserait sur chaque devis. Vérifier la vue de toute entité
  étiquetée par `/ws/meta/view` ;
- **ce que le moteur crée lui-même reste sans étiquette**, sauf à la poser après coup par une mise à jour : le couvrir
  par un contre-contrôle métier dédié (démo BTP de référence : un script SQL de contrôle propre au scénario).

### 188. L'audit écrit dans la base qu'il audite — et un `BEGIN` sans point-virgule devant `\i` ne le met pas en transaction

`scripts/audit-completeness.sql` crée et remplit `public.zz_audit_invariants` (référence du cliquet de la dimension 13)
au premier passage. La table reste : elle part dans tout dump de la base, et arrive chez qui le restaure. *Constaté le
2026-09-26 : `<base>` portait une `zz_audit_invariants` héritée du dump « démo importée » de départ
(suppression soumise à l'utilisateur) ; la copie de secours sauvegardée
le soir même la contient encore (table et données, lu par `pg_restore -l` sur cette copie).*

Pour auditer sans rien écrire, la transaction jamais validée marche, **à condition que le `BEGIN` parte avant
l'audit.** psql n'envoie une commande qu'à son point-virgule, et le reste du tampon en fin d'entrée : dans
`{ echo BEGIN; echo "\i …/audit-completeness.sql"; } | psql …`, le `BEGIN` part **après** l'audit, qui a tourné en
validation automatique. *Constaté le 2026-09-26 : la sortie de l'audit V5, annoncé « en transaction annulée », finit
par `BEGIN` (dernière ligne de sa sortie, ligne 602) ; les deux audits
de la nuit, eux, ouvrent sur `BEGIN` et finissent sur `ROLLBACK`. La commande de la passation V4 ajoutait un
`ROLLBACK` écrit de même, sans point-virgule : il est sorti en erreur de syntaxe
à l'essai suivant, tampon « BEGIN ROLLBACK », même cause. Mécanisme déduit des sorties, non rejoué. Sans dommage ce
jour-là : la référence existait déjà (9 lignes) et le script n'écrit que pour un code qui n'en a pas (lu dans le
script) ; ses tables de travail sont temporaires.*

**À faire :** `{ echo 'BEGIN;'; echo '\i …/audit-completeness.sql'; echo 'ROLLBACK;'; } | psql … -v tag=<tag>` ;
contrôler que la sortie commence par `BEGIN` et finit par `ROLLBACK`. Sans référence déjà enregistrée, une base
auditée ainsi n'en enregistre jamais : le cliquet ne mord pas, c'est le prix. Sinon, supprimer la table avant un dump
de référence, avec l'accord du propriétaire de la base.

### 114. Un rapport d'exécutant peut affirmer un fait faux — re-mesurer avant d'écrire une vague qui en dépend

Distinct du piège 82 (l'audit ne teste que ce que le script écrit) : ici c'est une **vague qui
consomme l'affirmation d'une vague précédente sans la re-vérifier en base**. Deux cas sur le même
chantier (package CRM, 2026-09-07/08), à deux endroits différents de la chaîne :

1. Le rapport du lot 1 (§5) affirme « hiérarchie du groupe de tiers posée » (`parent_partner` renseigné
   sur les 2 établissements). Vérifié FAUX par l'audit qui a suivi (§3 de son rapport, ligne 5) : la colonne était restée NULL. Corrigé en vague 16 — mais le lot 2 avait déjà pu
   construire des fils narratifs sur une hiérarchie qui n'existait pas encore en base.
2. Le contrat lui-même (repris sans re-mesure) affirmait « 24 opportunités sur 32 sans
   aucun client » — la vague qui devait les rattacher (§5 « décision n°4 ») a d'abord re-mesuré
   (rapport du lot 2A, §0) et trouvé **0** opportunité sans `partner` : la prémisse ne tenait pas,
   la décision qui en dépendait était sans objet.

**Règle de méthode** : un rapport — le sien ou celui d'un exécutant précédent — n'est jamais une
preuve suffisante pour fonder l'écriture d'une vague qui en dépend. Toujours rejouer la requête de
preuve citée (ou en écrire une si elle est absente) contre la base réelle avant de bâtir dessus.
Le premier cas coûte cher (correction a posteriori, incohérence temporaire pour le lot suivant) ;
le second, détecté à temps, évite une décision inutile. Corollaire du piège 39 (prendre un
enregistrement comme modèle de shape, jamais un rapport) et de la règle zéro de SKILL.md (vérifier
factuellement le socle avant de produire) : ici étendu à la production elle-même, pas seulement au
socle de départ.

### 149. Écrit dans un rapport n'est pas annoncé — et un attendu d'UAT se relève à l'écran, pas par raisonnement

`[constaté 2026-09-23/24, démo industrielle]` Deux fautes de livraison, pas de données :

1. La limite « aucun mouvement de stock » (piège 143) figurait dans le rapport du lot ; elle n'a jamais
   été dite à l'utilisateur comme **visible**, avec ses écrans. Il l'a découverte en naviguant la veille
   de la démo — exactement le cas que le client déclarait irrecevable (« une limite annoncée est
   recevable, une limite découverte à l'écran ne l'est pas »). **Tout raccourci volontaire d'un seed**
   (état posé sans sa transition, lien omis, champ laissé vide) **se livre dans le message de fin** :
   l'écart, les écrans où il se voit, la phrase à dire.
2. L'attendu d'UAT « les autres panneaux sont vides ou à zéro » était déduit. À l'écran, ces panneaux
   (module `axelor-project-reporting`, hors standard AOS) montraient 7 666,15 € d'achats engagés et une
   alerte « budget de temps dépassé » (piège 144). Un attendu se relève dans la requête de la vue ou à
   l'écran d'un banc : la dimension 6 vaut aussi pour les attendus qu'on écrit.
3. **Confirmé à la démo du 24/09** (retex de l'utilisateur) : la même limite (OF ouverts sans mouvement de stock,
   bilan d'affaire aux quantités livrées sans mouvement, piège 143) est retombée à l'écran au hasard des
   ouvertures — elle n'avait été annoncée que **si on la demandait**. Une limite « annoncée si on la
   demande » devient une limite découverte dès que le client ouvre un écran au hasard : un historique qui
   porte des statuts de flux physique se joue donc par le moteur, ou ses objets sont exclus des écrans de
   la démo, et la limite s'annonce d'office AVANT la séance, pas sur demande.

**À faire :** livrer tout raccourci dans le message de fin (écart, écrans, phrase à dire), annoncé
**d'office avant la séance**, pas seulement sur demande ; relever chaque attendu d'UAT dans la requête de
la vue ou à l'écran. **Garde :** aucune dans `scripts/audit-completeness.sql` — ce sont des fautes de
livraison, pas de données.

### 140. Une valeur uniforme PAR FAMILLE est un copier-coller que la dimension 4 ne voit pas

`[prouvé 9.1.3 / AOP 8.2.2, 2026-09-22]` Mesuré sur un catalogue d'articles : **114 articles de
tôlerie tous à 18,00 €**, **80 articles de débit tous à 12,00 €** — une seule valeur distincte par
famille. Au premier clic, le prospect ouvre deux fiches de la même famille et lit le même prix.

**Deux raisons pour lesquelles la dimension 4 de `scripts/audit-completeness.sql` laisse passer ce
cas** — vérifiées dans le script, lignes 137-155 au 22/09 (aujourd'hui : section DIMENSION 4) :

1. elle ne balaie que les colonnes `character varying` et `text`. Un prix est `numeric` : **il n'est
   jamais examiné** ;
2. elle ne lève que si `count(DISTINCT col) = 1` **sur toute la table taguée**. Ici il y a deux
   valeurs distinctes au global : **le contrôle serait vert même si la colonne était scannée**.

Le contrôle qui attrape le cas groupe par la colonne de famille :

```sql
SELECT p.product_family, count(*) AS articles, count(DISTINCT p.cost_price) AS prix_distincts
  FROM base_product p
 WHERE p.product_family IS NOT NULL
 GROUP BY p.product_family
HAVING count(*) >= 6 AND count(DISTINCT p.cost_price) = 1;
```

Attendu : **0 ligne**. Le même patron vaut pour toute colonne de valeur portée par une population
naturellement segmentée — prix par famille, durée par poste de charge, montant par type de pièce.

**Correction, pas écrasement** : disperser autour de la valeur de famille par un décalage
**déterministe tiré du code article** (même principe que l'offset dérivé de l'entité liée, règle 11
de SKILL.md, et que la formule du piège 26). Garder la valeur de famille comme centre préserve la
crédibilité métier ; c'est l'uniformité stricte qui est le défaut, pas le prix moyen.

Attention : **Fermer l'angle mort côté outil est une modification de `scripts/audit-completeness.sql`** —
colonnes numériques à balayer, et un `GROUP BY` sur une colonne de famille à déclarer par table. Le
script est le contrôle obligatoire de la Phase 4 : cette extension n'est pas écrite ici et appelle son propre arbitrage.

### 141. Un rechargement de module ne supprime JAMAIS ce qui a disparu du XML

`[prouvé 2026-09-22]` La méthode chirurgicale de rechargement — supprimer les lignes de
`meta_module_depends` puis de `meta_module` pour le module visé, redémarrer — réimporte bien les
métadonnées **présentes** dans le XML. Elle ne retire **rien** de ce qui en a été **retiré** : menus,
vues et actions supprimés du source restent en base et **restent visibles à l'écran**.

*Mesuré : **6 menus obsolètes survivants** après un rechargement pourtant réussi, dont 2 kanbans et
2 calendriers qu'on avait volontairement fusionnés dans d'autres entrées.* Le rechargement rend un
succès ; l'écran garde les doublons.

La suppression est donc **explicite**, et se pilote par comparaison : la liste des `menuitem name=`
du XML du module, confrontée à `meta_menu` filtré sur ce module.

Attention : **Piège corollaire vérifié le même jour, et il interdit l'automatisme.** Sur cette base, un menu du
corpus de démonstration (`<démo>-menu-couverture-commandes`) ressort de la comparaison comme
« résiduel » alors qu'il est **indispensable** : il vient d'une session antérieure et n'appartient à
aucun fichier du module. Une suppression en masse du résultat de la comparaison l'aurait emporté.

**Règle** : lister le résultat de la comparaison, puis ne retirer que **ce qu'on a soi-même retiré**.
C'est la règle de sûreté de SKILL.md (« ne pas toucher à ce qu'on n'a pas créé ») appliquée aux métas, où
elle est moins intuitive parce que la donnée y ressemble à du code. Voir aussi le piège 54 (méta morte
d'un module retiré) et le piège 90 (doublons de nom dans `meta_action` / `meta_view`) : même famille,
la couche méta ne se nettoie pas toute seule.

### 142. `current_date + 15` sans unité échoue sur Hibernate 6 — et un domaine se teste avant d'être livré

`[prouvé 2026-09-22]` Un domaine de vue écrit `self.endOfValidityDate <= current_date + 15` lève :

```
org.hibernate.query.SemanticException: Operand of + is of type 'java.lang.Integer'
which is not a temporal amount
```

La forme qui passe porte **l'unité** : `current_date + 15 day`. Rien ne le signale à la construction —
ni le build, ni l'import de la vue, ni un lint : **l'erreur ne sort qu'à l'ouverture de l'écran**, donc
potentiellement devant le client.

**Corollaire de méthode, qui vaut pour tout domaine neuf, pas seulement pour les dates** : tester le
domaine avant de le livrer, par

```
POST /ws/rest/<modèle>/search     {"data":{"_domain":"<le domaine>"}}
```

Quelques secondes, contre un écran mort découvert en démo. Attention à la forme de l'appel : c'est
`_domain` qu'il faut, pas `criteria` + `operator:"like"` (piège 18), et omettre la clé `data`
désactive le filtre `archived` (piège 94).

Attention : **Et un domaine qui ne lève pas n'est pas pour autant vivant.** Il se valide sur **deux** critères :
il ne lève pas, **et** il rend des lignes. *Mesuré le même jour : le domaine « commandes dont un ordre
de fabrication finit après la date de livraison promise » répondait `total=0` en toute rigueur, parce
que `estimatedDeliveryDate` était NULL sur les 120 commandes.* Le domaine était juste, l'écran était
mort-né, et aucune erreur n'a été levée nulle part. Avant de conclure « pas de cas », compter la
population de la colonne comparée — c'est le quatrième contrôle de la section « Un domaine s'appuie sur
un champ métier » de SKILL.md.
