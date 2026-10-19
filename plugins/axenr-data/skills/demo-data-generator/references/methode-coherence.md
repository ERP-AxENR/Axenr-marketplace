# Méthode — cohérence

**Pièges couverts par cette fiche :**

- 44. Cohérence inter-champs — créer la valeur manquante plutôt que prendre au hasard
- 45. Cohérence sémantique du libellé
- 46. Données satellites génériques = non crédibles
- 47. Cohérence arithmétique interne d'une ligne
- 48. Une FK vers une période doit pointer la granularité métier
- 49. Répartir les enfants sur TOUS les parents
- 50. Un `jsonb attrs` peut porter des données MÉTIER dont les clés viennent d'une formule
- 51. Une même table peut servir DEUX rôles via un `typeSelect`
- 77. Ne rien redire dans un champ que la fiche affiche déjà à deux centimètres
- 78. Un préfixe de séquence à soi est une couture visible
- 88. Une valeur de mesure sans son unité est pire qu'un champ vide
- 89. Ne pas remplir un champ qui n'a pas de sens pour le type de l'enregistrement
- 93. Une note, un score, une étoile : vérifier QUI l'écrit avant de la remplir — ou de la vider
- 95. Renommer un tiers ne suffit pas : les COORDONNÉES sont un axe à part, et les noms inventés peuvent être réels
- 74. `crm_opportunity.order_by_state` — copie de la séquence du statut, tri et kanban cassés

Piège 74 rattaché ici : désynchronisation d'une colonne dénormalisée, même famille que 70-72 (voir `entites-tiers-contacts.md`).

## Session sur une base de démo ESN (2026-08-11) — préambule

## Pièges 70 à 91 — session sur une base de démo ESN (2026-08-11)

Ces vingt-deux entrées viennent d'un seul chantier, et il faut lire d'abord ce qu'elles ont en
commun : **elles ne sont pas vingt-deux erreurs indépendantes, ce sont trois fautes répétées.**
Le même agent a oublié de recalculer un champ dérivé **trois fois**, a redit dans un champ ce que
la fiche affichait déjà **trois fois**, et a supposé une convention au lieu de la relever **deux
fois** — à chaque fois sur un objet différent, donc sans reconnaître le motif. Reconnaître le motif
coûte moins cher que corriger les vingt-deux symptômes.

*(Préambule thématique déplacé ici, hors de son emplacement d'origine — c'est la meilleure généralisation du fichier. Les 22 pièges qu'il introduisait d'origine — 70 à 91 — sont répartis entre `entites-tiers-contacts.md`, `methode-audit.md`, `methode-rejouabilite.md`, `entites-autres.md` et ce fichier ; voir `references/index-pieges.md` pour chacun.)*

## Cohérence : ce qui décrédibilise une démo


### 44. Cohérence inter-champs — créer la valeur manquante plutôt que prendre au hasard
Remplir un FK avec la première valeur disponible produit des absurdités quand le référentiel vient
d'un autre métier : un référentiel de secteurs hérité d'un clone BTP a fait afficher « Administration
publique » sur une société au code NAF **6202A** (conseil en systèmes informatiques), et classé un
consultant Cloud en « Eau & environnement ». **Si aucune valeur n'est pertinente, créer la valeur.**
Vérifier les paires : `mainActivity (NAF) ↔ industrySector`, `industrySectorSet ↔ employeurs du CV`,
`description ↔ NAF`.

### 45. Cohérence sémantique du libellé
Une tournée « Île-de-France » doit contenir des adresses en 75/77/78/91-95 — pas Nice, Marseille et
Shanghai. Sélectionner les enregistrements **dynamiquement** sur le critère que porte le libellé.

### 46. Données satellites génériques = non crédibles
Mettre le même diplôme et le même employeur à tous les candidats est un défaut de démo visible.
Individualiser chaque parcours **et** le rendre cohérent avec les attributs déclarés (niveau d'étude,
années d'expérience, ville de résidence, salaire, poste visé) ; ancrer les employeurs dans la région.
Garde : `GROUP BY employeur HAVING count(DISTINCT personne) > 1`.
Corollaire — **vérifier les dates dérivées** : une formule `DATE '1990-01-01' + offset jours` a produit
des candidats de **9 à 20 ans**, dont un « chef de projet, 10 ans d'expérience » né en 2010.

### 47. Cohérence arithmétique interne d'une ligne
Sur un titre-restaurant : `papier + carte` doit égaler le nombre de titres (une répartition qui met le
total dans *chacun* donne le double), lui-même égal à
`jours travaillés − invitations − cantine − jours à l'étranger`. Écrire la garde correspondante.

### 48. Une FK vers une période doit pointer la granularité métier
L'unique période de l'année de paie couvrait **12 mois** → inutilisable pour illustrer une campagne
mensuelle. Créer les périodes mensuelles manquantes et affecter chaque campagne à *son* mois.

### 49. Répartir les enfants sur TOUS les parents
Des relevés de mesure n'existaient que sur 1 contrôle sur 4 (filtre de statut trop restrictif) :
l'utilisateur ouvre un autre contrôle et ne voit rien. Garde : `NOT EXISTS (enfant)` sur chaque parent.

### 50. Un `jsonb attrs` peut porter des données MÉTIER dont les clés viennent d'une formule
`ControlType.conformityFormula` est un script qui lit `$planAttrs.<clé>` (valeurs **attendues**) et
`$entryAttrs.<clé>` (valeurs **relevées**) : *Attribut* → `acceptedColor` vs `currentColor` ;
*Dimension* → `mesuredDim` entre `acceptedDimension ± min/maxTolerance` (noter la faute d'origine
« **mesured**Dim » — recopier la clé exacte du code). Laisser ces jsonb à NULL rend le calcul de
conformité inopérant, sans aucune erreur. **Chercher les scripts qui consomment un `attrs` avant de le
laisser vide.**

### 51. Une même table peut servir DEUX rôles via un `typeSelect`
`ControlEntryPlanLine` : type 1 = ligne de **plan** (rattachée au `controlPlan`, porte `controlType` +
`planAttrs`) ; type 2 = ligne d'**échantillon** (rattachée au `sample` et **obligatoirement** à
`controlPlanLine`, car `getFormula()` remonte par là). Ne créer que des lignes type 2 sans
`controlPlanLine` casse la chaîne silencieusement. Lire le service (`createEntryWithPlan`, `getFormula`)
pour comprendre la parenté avant d'insérer.

### 74. `crm_opportunity.order_by_state` — copie de la séquence du statut, tri et kanban cassés

30 des 62 affaires l'avaient à NULL. Le champ n'est ni saisi ni affiché : c'est une dénormalisation
de `crm_opportunity_status.sequence` sur laquelle repose l'ordonnancement. Invisible à l'audit
« champs vides » parce que personne ne le cherche.

```sql
UPDATE crm_opportunity o SET order_by_state = s.sequence
  FROM crm_opportunity_status s WHERE s.id = o.opportunity_status
   AND o.order_by_state IS DISTINCT FROM s.sequence;
```

Corollaire général : **chercher les colonnes qui dupliquent une valeur d'une table liée** et les
recalculer. Elles ne lèvent jamais d'erreur, elles faussent des écrans.

### 77. Ne rien redire dans un champ que la fiche affiche déjà à deux centimètres

Trois occurrences dans une session, sur trois objets :

```
FAUX : opportunité  : « Refonte du SI métier — Nordeq Industries »   (le client est une COLONNE)
FAUX : description  : « Affaire « Audit de cybersécurité ». Besoin… » (le nom est en haut de la fiche)
FAUX : catalogue    : « Ordinateur portable 14 pouces (TOP Components) » (le fournisseur est une colonne)
```

Une affaire porte une **dénomination** — mission + périmètre —, pas l'identité de son client. La
répétition encombre listes, graphes et impressions, ampute la place du contenu utile, et rend deux
enregistrements du même client **indiscernables**. Vérifier la convention de la donnée d'origine :
ici les libellés BTP nommaient l'ouvrage et son lieu, jamais le donneur d'ordre.

### 78. Un préfixe de séquence à soi est une couture visible

Reclasser dix tiers sous `CLT0001..CLT0010` dans une base qui numérote `T0001..T0079` annonce
« ces dix-là ne sont pas comme les autres » dans chaque sélecteur — exactement ce que faisait le
préfixe hérité du jeu d'origine qu'on venait de retirer. S'aligner sur la convention existante, à la suite.

### 88. Une valeur de mesure sans son unité est pire qu'un champ vide

Renseigner `length`/`width`/`height` sans `length_unit`, ou `net_mass`/`gross_mass` sans
`mass_unit`, affiche « 2,4 » sans dire si ce sont des kilos ou des livres. Poser l'unité **dans le
même UPDATE** que la valeur. Asserter aussi la cohérence métier : `gross_mass > net_mass`
(l'emballage pèse).

### 89. Ne pas remplir un champ qui n'a pas de sens pour le type de l'enregistrement

Dimensions, masses, pays d'origine, règles de stock sur un **service** : non-sens qui se voit plus
que le vide. Écotaxe et homologation produit renseignées uniformément : inventent une fiscalité et
un processus que la démonstration ne montre pas. **Asserter dans les deux sens** — complet sur les
matériels, ET absent sur les services. Un audit qui ne mesure que le remplissage pousse au
remplissage aveugle.

### 93. Une note, un score, une étoile : vérifier QUI l'écrit avant de la remplir — ou de la vider

Un champ de notation ressemble à une saisie. Il peut être **calculé par un service du moteur**, et
alors le remplir en SQL ne produit pas une donnée : ça produit une **affirmation d'historique**.

Vécu le 2026-08-24 sur une base de démo ESN. Une passation signalait « 15 fournisseurs sur 18 ont
`supplier_quality_rating_select = 0` alors que 3 sont notés », et invitait à compléter les 15.
L'énoncé était **inversé**. `PartnerProductQualityRatingServiceImpl.updateSupplier()`
(axelor-stock) dérive cette note de la moyenne des notes qualité par produit **pondérée par les
quantités réceptionnées**, au moment de la réalisation d'un mouvement de stock d'entrée. Les 15 à 0
étaient donc l'état NORMAL — rien reçu, rien à noter. Les 3 notés étaient l'anomalie : 3, 4 et
2 étoiles avec `supplier_quality_rating` à 0.00, `supplier_arrival_product_qty` à 0.00 et **zéro
ligne** dans `stock_partner_product_quality_rating` (table vide pour toute la base). Des notes
venues de l'import du socle AOS, jamais passées par l'UI — l'action-record
`action-record-set-supplier-quality-rating`, qui propage `select` vers la colonne brute au
`onChange`, n'avait jamais tourné sur elles.

**Le réflexe** : avant de toucher un champ `*_rating`, `*_scoring`, `*_score`, `*_select` de
notation, `grep` le setter dans les sources.

```bash
grep -rn "setSupplierQualityRating\|setLeadScoring" --include=*.java .
```

- Un **setter appelé par un service** ⇒ champ calculé ⇒ frontière SQL/UI, et surtout : la valeur
  n'a de sens que si sa **source** existe.
- Aucun setter hors mapper ⇒ champ saisi ⇒ SQL légitime (cas de `crm_lead.lead_scoring_select`).

**Le corollaire, plus important que le piège** : un champ calculé ne se remplit pas, mais il ne se
regarde pas seul non plus. Le moteur écrit ici **trois colonnes d'un seul geste** — la note
affichée, la moyenne brute, la quantité qui a servi de pondération — plus un panneau de détail. Une
note posée seule crée une incohérence VISIBLE à l'écran : des étoiles au-dessus d'un zéro. Repérer
le **groupe** de colonnes qu'un service écrit ensemble, et le traiter comme un tout.

**Converger vers le résultat du moteur n'est pas le simuler.** Remettre ces 3 notes à 0 (vague 16
de cette base) ne viole PAS la frontière SQL/UI, parce que la source de calcul est vide : la valeur
que le moteur produirait EST 0. Une future réception écrira 0, puis la vraie note. Le test qui
distingue les deux cas : **le SQL écrit-il ce que le moteur aurait écrit, ou ce qu'on aurait voulu
qu'il écrive ?**

**Effet sur une vague convergente** : quand l'état cible est l'absence de valeur, le ciblage porte
forcément sur une colonne que la vague modifie — ce que le piège 80 interdit d'ordinaire. C'est ici
l'exception qui **fait** l'idempotence : après application le motif ne matche plus, d'où `UPDATE 0`
au rejeu. Conséquence sur les préconditions : elles ne peuvent pas exiger « exactement N lignes »,
sinon le rejeu échoue sur son propre succès. Exiger que la cible soit un **sous-ensemble** de
l'arbitrage rendu — 0 ligne = déjà appliqué, une de plus = fait nouveau, on aborte.

**Effet sur l'audit** : le contrôle « notes à 0 » de la dimension 8 poussait à fabriquer un
historique. Il est **inversé** — il compte désormais les notes SANS base de calcul. Généralisable :
sur un champ dérivé, l'anomalie n'est pas le vide, c'est la **valeur sans sa source**.

**Et le discriminant que le SQL brut ne voit pas.** Le même jour, le même audit annonçait
32 opportunités non notées sur 68 : les 32 étaient le lot du socle AOS, `archived = true`, donc
invisibles partout (piège 79) — les 36 vivantes étaient **toutes** notées. Un contrôle de complétude
qui ne filtre pas `archived` (ni `dtype`, cf. l'héritage single-table de `base_product`) invente une
charge de travail. Avant de conclure qu'un champ est vide sur N lignes : **ces N lignes sont-elles
affichées ?**

**Et la volumétrie annoncée n'est pas la volumétrie visible.** Le corollaire coûte plus cher que
le piège, parce qu'il ne se voit pas : sur cette base de démo ESN, mesuré le 2026-08-24, **72 % des commandes
de vente étaient archivées** — 18 en base, **5** à l'écran. Idem opportunités 62 / 30, contrats
2 / 1. Toute passation qui recopie un `count(*)` surestime ce qu'un prospect verra, et une
préparation de démonstration bâtie là-dessus se découvre en séance. Ne citer que la colonne
VISIBLE, et **ne jamais désarchiver pour regagner du volume sans ouvrir les lignes** : 7 des
13 commandes archivées de cette base étaient des coquilles du socle AOS — aucun numéro, total à 0,
jamais passées par le repository qui calcule séquence, `full_name` et totaux d'un seul geste. Les
désarchiver aurait rempli la grille de lignes vides, l'inverse du but recherché.

Outil à écrire (non fourni avec ce skill) : un balayage de `information_schema` qui rend, par table métier
et par société, `en_base` / `visible` / `masquees`. Balayage dynamique et non liste figée — un inventaire
hérité est toujours en retard sur la base.

**Se l'appliquer à soi-même.** Ce piège a été écrit puis, trente minutes plus tard, non appliqué
par son auteur : un dossier complet a été monté sur 7 commandes « cassées » (cause identifiée,
domaine du menu vérifié) avant que l'API REST n'en serve 2, toutes saines. Le SQL brut et le
runtime ne répondent pas à la même question. Quand les deux divergent, **c'est la mesure SQL qui
est suspecte**, pas le moteur.

### 95. Renommer un tiers ne suffit pas : les COORDONNÉES sont un axe à part, et les noms inventés peuvent être réels

Deux défauts distincts, découverts le même jour sur cette base de démo ESN, tous deux invisibles à tous les
audits du chantier. Le premier est une fuite de données, le second un risque juridique.

**(a) Les coordonnées ne se détectent pas par un motif de vocabulaire.** Un clone de base client
avait vu ses 10 clients renommés en entreprises fictives — et gardé leurs coordonnées d'origine :
emails de domaines RÉELS d'organismes publics étrangers (`contact@<organisme>.<tld>`),
**adresses postales exactes** de ces organismes (l'adresse de leur siège), et 20 téléphones
jusqu'au standard réel.

Tous les balayages cherchaient du vocabulaire métier — « chantier », « ouvrage », les communes.
Or une adresse email n'en contient aucun, et le nom d'une rue n'est ni un ouvrage ni un
chantier. **Le résidu vivait dans un TYPE de donnée que le motif ne pouvait pas atteindre.**

Après tout renommage de tiers, balayer les coordonnées par **NATURE**, jamais par contenu :

```sql
-- domaine de premier niveau, indicatif, pays de l'adresse : trois axes, trois requêtes
SELECT count(*) FROM message_email_address WHERE address ILIKE '%.<tld>';
SELECT count(*) FROM base_partner WHERE fixed_phone LIKE '+<indicatif>%' OR mobile_phone LIKE '+<indicatif>%';
SELECT co.name, count(*) FROM base_address a JOIN base_country co ON co.id=a.country GROUP BY 1;
```

**Une correction partielle est pire qu'aucune** : ici `web_site` était déjà en `.fr` et
`street_name` déjà générique, mais `addressl4`, `addressl6`, `zip`, `town_name`, `city`, `country`,
`full_name` et `formatted_full_name` de la même adresse portaient encore le pays d'origine. Deux
colonnes traitées sur neuf donnent l'illusion que le sujet est clos.

**Numéros de téléphone : utiliser les tranches réservées à la fiction.** En France, l'Arcep
(décision n° 2019-0954 §2.5.12) alloue aux œuvres audiovisuelles les racines **01 99 00, 02 61 91,
03 53 01, 04 65 71, 05 36 49, 06 39 98**. Elles ne peuvent être ni attribuées, ni affectées à un
utilisateur final, ni appelées. Choisir la racine selon la zone géographique du tiers : le numéro
reste crédible ET ne peut joindre personne. Une assertion sur ces racines vaut mieux qu'une
relecture.

**(b) Un nom « inventé » peut être une entreprise réelle.** Sur les 10 clients fictifs de cette
base, **4** portaient un nom existant : l'un reprenait le nom ET le secteur d'une société réelle (un
prospect du métier le reconnaît), un autre le nom d'un grand groupe pharmaceutique, un troisième celui
d'une société de gestion adossée à un groupe bancaire, et le quatrième avait un homonyme dont le
domaine web est signalé **frauduleux** par un organisme de lutte contre la fraude. Aucun n'avait été
vérifié à la création.

Vérifier chaque nom en registre AVANT de le seeder, et se méfier des noms « qui sonnent
inventés » — c'est précisément l'intuition qui a produit les quatre. Écarter aussi les patronymes
de personnes physiques réelles (un candidat a été rejeté pour cela).

Attention : **Niveau de preuve à énoncer honnêtement** : une recherche web ne DÉMONTRE pas l'absence d'une
société, elle réduit le risque. Et un contrôle DNS ne prouve rien dans un conteneur sans
résolution — **toujours passer un témoin positif** (`host axelor.com`) avant de conclure « domaine
libre » : ici le témoin échouait, donc dix « domaines libres » ne valaient rien. Une vérification
formelle passe par l'INPI ou l'INSEE.

**Corollaire de méthode.** Le meilleur domaine email n'est pas inventé : il se **dérive de ce que
la base affiche déjà** (`base_partner.web_site`). Une précondition qui exige que le domaine du
mapping soit présent dans `web_site` interdit structurellement d'introduire un domaine nouveau —
le garde-fou est dans la vague, pas dans la vigilance.
