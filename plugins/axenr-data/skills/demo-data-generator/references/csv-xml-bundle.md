# Peupler via un bundle CSV + XML (Import Configuration)

À lire quand la voie SQL n'est pas praticable : le partenaire ou le client **n'a pas d'accès à la base**,
ou le livrable doit être rejouable depuis l'UI (`Administration → Configurations d'import`).

Pour le **mécanisme d'import lui-même** (structure du bundle, binding, dépannage des imports
silencieux), s'appuyer sur le skill **`axelor-import-export`** : il traite le même moteur
(`ImporterCSV`) et documente notamment le cas « Réussi : N / Non vide : 0 », c'est-à-dire un import
qui rapporte un succès sans rien persister. Le présent document ne couvre que ce qui est **spécifique
aux données métier**.

## Quand cette voie est préférable

| Contexte | Voie |
|---|---|
| Pas d'accès DB chez le client / partenaire | **CSV+XML** |
| Livrable rejouable par un non-technicien | **CSV+XML** |
| Correctif ciblé (combler un NULL, aligner un flag) | SQL |
| Volume, ou dépendances fines entre tables | SQL |
| Données à faire valider/éditer par le métier avant chargement | **CSV+XML** (le CSV est relisible) |

## Structure

```
bundle-demo-<client>/
├── data-init/
│   ├── input-config.xml        ← le binding : fichier CSV → modèle, colonnes → champs
│   └── <ordre>-<entite>.csv    ← un CSV par entité, préfixé de son ordre FK-safe
└── README.md                   ← ordre d'import + prérequis
```

Nommer les CSV par ordre de dépendance (`10-partners.csv`, `20-addresses.csv`, `30-products.csv`) :
l'importeur ne réordonne pas, et une FK non encore importée reste vide **sans erreur** — le même piège
silencieux que la sous-requête SQL (règle cardinale 6).

## Les règles cardinales s'appliquent à l'identique

Le véhicule change, pas l'exigence. En particulier :

- **Booléens** : écrire `true` / `false` dans le CSV. Une cellule **vide devient NULL**, donc un
  enregistrement invisible dans les grids et les pickers. C'est le piège n°1 de cette voie, parce
  qu'une colonne vide dans un tableur ne se remarque pas.
- **Sélections** : écrire la **valeur** (`1`, `2`, `service`…), pas le libellé affiché. Récupérer les
  valeurs valides avec `scripts/introspect.sh` (section 4) avant de remplir le tableur.
- **`name` / `fullName`** : les écrire en colonne. L'importeur ne les calcule pas plus que le SQL.
- **FK** : les binder sur un **code métier** (`search="self.code = :code"`), jamais sur un id. C'est
  d'ailleurs le principal avantage de cette voie : le bundle est naturellement portable d'une base à
  l'autre, là où le SQL doit résoudre chaque FK par sous-requête.
- **Satellites O2M/M2M** : prévoir un CSV dédié pour chaque table fille et chaque jonction. Un header
  sans ses lignes reste inutilisable (règle cardinale 7).

## Ce que cette voie ne sait pas faire

- **Les flux valorisés.** Un import ne déclenche pas les services métier : totaux, taxes, marges,
  écritures et mouvements de stock resteront vides ou incohérents. Les devis chiffrés, factures et
  ordres de fabrication passent par le moteur (voir la règle cardinale 12 de SKILL.md).
- **Les correctifs de complétude.** Combler un champ NULL sur des enregistrements existants relève du
  SQL : un import créerait des doublons plutôt que de compléter.

## Vérification après import

Le rapport d'import ne prouve rien sur la qualité. Enchaîner avec l'audit des 6 dimensions
(`scripts/audit-completeness.sql`) : un import « réussi » peut avoir produit des booléens NULL, des
sélections invalides et des FK vides sans lever la moindre erreur.
