# Mode B — générer du volume crédible

Quand l'utilisateur commande une volumétrie (« 50 OF », « 200 produits », « une affaire complète avec
5 commandes et 300 feuilles de temps »), deux exigences s'ajoutent : **produire le volume** sans
l'écrire à la main, et **tenir le métier** du client. Un volume incohérent est pire qu'un petit jeu
soigné : il se voit à la première question d'un expert du domaine.

## 1. Instruire le métier avant de générer

C'est l'étape que l'on saute et qui se paie. Si le client fabrique des microprocesseurs par
lithographie EUV, un jeu peuplé de « Produit 001 », « Poste de travail 1 », « Opération A » sonne faux
immédiatement. Il faut le vocabulaire, la séquence et les ordres de grandeur réels.

Chercher, dans cet ordre : ce que l'utilisateur sait (il connaît son client — demander la gamme, les
familles de produits, les étapes clés), puis les sources externes (site du client, documentation
sectorielle, recherche web) si le domaine est technique.

Ce qu'il faut en tirer, concrètement :
- **Nomenclature du vocabulaire** : familles et sous-familles de produits, références réalistes
  (`WFR-300-P1`, pas `PROD-001`), unités du métier (plaquette, lot, wafer, mètre linéaire, tonne).
- **La séquence du process** : les étapes réelles dans l'ordre, avec des durées plausibles. Pour la
  lithographie EUV par exemple : préparation de plaquette → dépôt de résine → exposition EUV →
  développement → gravure → métallisation → test électrique → découpe → mise en boîtier → test final.
  Ces étapes deviennent les lignes de gamme, donc les opérations des OF.
- **Les ordres de grandeur** : un prix unitaire, une durée d'opération, une quantité par lot, un taux
  de rebut. Un OF de 5 unités à 300 € n'a pas le même sens qu'un lot de 25 plaquettes à 40 k€.
- **La contrainte métier caractéristique** — c'est ce qui rend une démo convaincante : salle blanche et
  traçabilité par lot en semi-conducteur, DLU en agroalimentaire, retenue de garantie en BTP,
  taux journalier et intercontrat en ESN.

Restituer ces choix à l'utilisateur en quelques lignes avant de générer : c'est peu coûteux et cela
évite de produire 200 produits au mauvais vocabulaire.

## 2. Générer le volume sans l'écrire à la main

Au-delà d'une dizaine de lignes, les `VALUES` explicites ne tiennent plus. Générer — mais en gardant
de la **variété** : un volume uniforme est aussi peu crédible qu'un volume absent.

```sql
-- 200 produits : familles réelles × déclinaisons, références métier, prix cohérents
INSERT INTO base_product (id, version, created_on, updated_on, created_by, updated_by, import_origin,
       code, name, full_name, product_type_select, sellable, purchasable, is_model, is_prototype,
       unit, sale_currency, purchase_currency, cost_type_select, product_family, sale_price, cost_price)
SELECT nextval('base_product_seq'), 0, NOW(), NOW(), 1, 1, :org,
       f.prefixe || '-' || lpad(g.n::text, 3, '0'),
       f.libelle || ' ' || f.variantes[1 + (g.n % array_length(f.variantes, 1))],
       f.libelle || ' ' || f.variantes[1 + (g.n % array_length(f.variantes, 1))],
       f.type, true, true, false, false,
       (SELECT id FROM base_unit WHERE name = f.unite),
       (SELECT id FROM base_currency WHERE code = 'EUR'),
       (SELECT id FROM base_currency WHERE code = 'EUR'),
       1,
       (SELECT id FROM base_product_family WHERE name = f.famille),
       round((f.prix_base * (0.85 + (g.n % 30) * 0.01))::numeric, 2),   -- ±15 % de dispersion
       round((f.prix_base * 0.62 * (0.9 + (g.n % 20) * 0.01))::numeric, 2)
FROM generate_series(1, 40) AS g(n)
CROSS JOIN (VALUES
  ('WFR', 'Plaquette silicium 300 mm', ARRAY['P1','P2','test','pilote'], 'storable', 'Plaquette', 'Plaquettes',      4200.00),
  ('RSN', 'Résine photosensible EUV',  ARRAY['13,5 nm','haute sensibilité'], 'storable', 'Litre',  'Consommables',    1850.00),
  ('MSK', 'Masque EUV',                ARRAY['couche M1','couche M2','via'], 'storable', 'Unité',  'Outillage',      95000.00),
  ('DIE', 'Puce logique',              ARRAY['7 nm','5 nm','3 nm'],          'storable', 'Unité',  'Produits finis',   180.00),
  ('TST', 'Test électrique sous pointes', ARRAY['wafer','die'],              'service',  'Heure',  'Services',         420.00)
) AS f(prefixe, libelle, variantes, type, unite, famille, prix_base)
WHERE NOT EXISTS (SELECT 1 FROM base_product x WHERE x.code = f.prefixe || '-' || lpad(g.n::text, 3, '0'));
```

Les principes qui rendent ce volume crédible :
- **Croiser un référentiel métier réel** (familles × déclinaisons) plutôt que numéroter linéairement.
- **Disperser les valeurs** : prix, quantités et durées varient autour d'une base (`% 30 * 0.01`), au
  lieu d'être identiques ou strictement croissantes.
- **Distribuer les statuts et les dates** de façon réaliste : sur 50 OF, une pyramide plausible est
  ~60 % terminés, 20 % en cours, 15 % planifiés, 5 % annulés — pas 50 terminés le même jour.
  `CASE WHEN n % 20 = 0 THEN 'annulé' WHEN n % 5 = 0 THEN 'planifié' … END`.
- **Étaler dans le temps** avec une saisonnalité si le métier en a une, et une densité plus forte sur
  les périodes récentes (c'est ce qui donne des courbes lisibles).

Pour un croisement volumineux — 300 feuilles de temps par exemple — générer par produit cartésien
maîtrisé : employés × jours ouvrés × projets, en filtrant les week-ends et en variant les durées
imputées autour d'un taux d'occupation cible (85 % par exemple), plutôt que 300 lignes de 8 heures.

## 3. Le volume transactionnel ne se joue pas en UI

50 OF représentent plusieurs centaines d'interactions : c'est hors de portée et inutile. Le pattern est
celui décrit à la règle cardinale 12 de SKILL.md (SQL pose un état, le moteur joue la transition) :

**Jouer 1 ou 2 exemplaires complets en UI** (le moteur produit les opérations, les composants, les
mouvements de stock et les feuilles de coût cohérents), puis **cloner ce motif en SQL** avec un offset
de dates et des variations de quantités. On duplique une structure *déjà rendue cohérente par le
moteur* — c'est bien moins risqué que de la fabriquer.

Le clonage doit faire varier ce qui se voit : quantités, produit, dates, statut, et l'écart entre prévu
et réel. Cloner 50 fois à l'identique produit un volume qui ne trompe personne.

## 4. Auditer un jeu de données volumineux

Les 6 dimensions restent valables, avec deux contrôles supplémentaires propres au volume :

- **Volumétrie atteinte** : la commande était 50 OF — en compter 50, pas 47 (des lignes peuvent avoir
  été silencieusement ignorées par une garde `EXISTS`, cf. piège 58).
- **Distribution** : vérifier que les statuts, dates et montants sont effectivement dispersés.
  Un `GROUP BY statut`, un `min/max/avg` sur les montants et un `GROUP BY date_trunc('month', …)`
  révèlent immédiatement un volume uniforme — le défaut le plus fréquent en génération.
