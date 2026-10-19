> Apport d'un chef de projet Axelor (paquet du 15/10/2026). Éprouvé sur AOS 9.1.6 / AOP EE 8.2.3. AxENR tourne sur AOP 7.4 / AOS 8.x : chaque piège est une hypothèse à vérifier sur la version cible.
> Rattaché au skill `axelor-import-export` : voir le tableau de routage de son `SKILL.md`.

# Le moteur d'import / export AOP EE — ce qui est prouvé

Faits prouvés au runtime sur AOP EE 8.2.3 / AOS 9.1.6 (essais des 06-07/09/2026 et du 25/09/2026), sauf
mention « lu dans le code » ou « non rejoué ». **Re-vérifie sur la version de l'env cible** tout ce dont tu
dépends : une version testée est ce qui a été éprouvé, rien de plus.

## La chaîne d'API

```
POST /callback                         {"username","password"} en JSON → cookie ; en-tête X-CSRF-Token = cookie CSRF-TOKEN
                                       (instance hébergée : session ouverte par l'utilisateur, voir import-ee-templates.md « Se connecter »)
POST /ws/files/upload                  corps binaire ; Content-Type application/octet-stream ; X-File-Name ;
                                       X-File-Size = taille exacte (sinon pas de MetaFile) ; X-File-Offset 0 ; X-File-Type
                                       → le MetaFile (clé id)
POST /ws/data/import                   {"model":<classe>, "file":{"id"}, "parse":false,
                                        "options":{"compute":{"<Onglet>":true}, "flat":false}}
                                       → {"fileName"} du rapport (Statistics, Errors, lignes en échec)
GET  /ws/data/download?fileName=…      le rapport ou l'export
POST /ws/data/export                   {"model","format":"xlsx","filter":{"_domain"},
                                        "options":{"fields":[…],"technical":true,"flat":false}}
```
`parse:true` n'écrit rien mais **annonce « resolved » pour des colonnes qui resteront vides**. Plafonds :
`data.upload.maxSize` (Mo, affiché par `ee_api.py info`), `data.import.max-size` (Ko, côté serveur). Droit
`canImport` explicite pour un non-administrateur.

## Structure d'un classeur

- **Un onglet par modèle**, nommé par le nom simple ; un onglet dont le nom n'est pas un modèle est
  ignoré.
- **Listes** : onglet de liaison `Modèle.champ` (`importId` du parent + `champ.<clé>` de la cible) ; dans
  cet onglet dédié, la cible se désigne par n'importe quelle clé métier ; son rejeu est idempotent,
  contrairement au moteur classique. Le mode plat (`flat:true`) retire les listes : ne pas l'utiliser.
- **Un appel par classeur** : le modèle passé est la racine ; tous les onglets-modèles sont importés,
  dépendances d'abord, et un lien vers un onglet du même classeur se résout. `compute` ne vaut que pour les
  onglets listés.
- **Recherche de la fiche existante** : champ requis-unique d'abord, puis `importId`, puis `id` ; la clé
  d'import de la fiche trouvée est **réécrite**. Conséquence : une ligne à clé d'import neuve mais au login
  (ou code unique) déjà pris **écrase** la fiche existante, rapport vert — `ee_api.py plan` l'annonce avant
  l'import. Rejouer met à jour sans doublon.

## Les liens (la limite la plus coûteuse)

Une colonne `<rel>.<champ>` dans l'onglet d'une entité ne se résout que si `<champ>` est `id`,
`importId` ou **la clé requise ET unique de la cible** (préférence `code`, `email`, `emailAddress`,
`…Seq`). Sur tout autre champ : relation vide, rapport vert.

Exemples relevés en 9.1.6 : `productFamily.code`, `productCategory.code`, `group.code`,
`saleCurrency.codeISO` → résolus ; `unit.name` (l'unité n'a aucune clé unique), `currency.code` (code
d'impression, non unique), `product.code` (unique mais **pas requis**) → vides. `ee_api.py keys` calcule
la bonne clé à partir des métadonnées de l'env cible.

Une clé `<modèle-en-tirets>-<id>` (`unit-40`, `product-family-12` : `TypeUtils.makeImportId`) fabriquée par l'export est un **id local** : juste dans la base qui
l'a produite, fausse ailleurs. Idem `id` et `<rel>.id`.

## compute

`compute` fait repasser chaque fiche importée par le `save()` du repository AOS. **Indispensable** : sans
lui, un article n'a ni libellé complet ni n° de série (fiche invisible dans les sélecteurs), rapport vert.
Mais c'est une **seconde passe sur des fiches déjà créées** : la logique conditionnée à `id == null` et les
champs transitoires sont perdus. Avant de livrer un gabarit sur un modèle nouveau, lis le `save()` de son
repository dans les sources de la version cible (sources publiques au tag de la version, ou sources des jars
de l'instance) et fournis en colonne ce qu'il ne pose qu'à la création.

## Valeurs

| Règle | Version éprouvée |
|---|---|
| Colonne inconnue ou mal orthographiée : ignorée sans signal | AOP 8.2.3 / AOS 9.1.6 |
| Cellule vide = efface en mise à jour ; colonne absente = conserve | AOP 8.2.3 / AOS 9.1.6 |
| Booléen : seul `true` est vrai ; `1`, `oui` = faux ; vide = NULL | AOP 8.2.3 / AOS 9.1.6 |
| Dates et décimaux permissifs mais non pilotables | AOP 8.2.3 |
| Valeur de sélection hors liste acceptée | AOP 8.2.3 / AOS 9.1.6 |
| CSV à point-virgule : échec silencieux ; BOM UTF-8 non absorbé ; latin-1 corrompu | AOP 8.2.3 (le latin-1 aussi en AOS 9.1.6) |
| Dépassement de longueur : échec franc, sans troncature | AOP 8.2.3 / AOS 9.1.6 |
| xlsx : décimal ≥ 1000 en cellule NUMÉRIQUE relu « 1074,623 » (DataFormatter en locale applicative) → ligne rejetée ; en texte à point, il passe | AOP 8.2.3 / AOS 9.1.6 |
| Aucun rollback : ce qui est passé reste | AOP 8.2.3 |

Préférer le **xlsx** au CSV : il évite séparateur, BOM et encodage.

## Le rapport

`Statistics` (success / failed par onglet) et `Errors` (onglet, colonne, valeur, ligne, erreur), plus
les lignes en échec rejouables. **Il ne dit rien des colonnes ignorées ni des liens restés vides** : la preuve
est `verify_import.py`.

## L'export (ce qu'il faut défaire avant d'en faire un gabarit)

Relevé sur AOP EE 8.2.4-SNAPSHOT / AOS 9.1.7 (une instance de démonstration du secteur BTP, 25/09/2026, lecture seule) :

- Onglets liés créés **vides** dès que la racine a une fiche ; aucun si la racine est vide.
- Onglet principal : `<rel>.id`, `<rel>.importId` et une colonne d'affichage (`fullName`, `name`, `label`) ;
  vers une cible à clé requise-unique, `<rel>.<clé>` (`company.code`, `currency.codeISO`, `user.code`, `site.code`).
- Référentiels atteints : un onglet réduit à leur clé → à supprimer du gabarit.
- Liste many-to-many : onglet `Modèle.champ` (`importId`, `<champ>.importId`).
- Décimaux, dates, booléens en cellules typées → décimaux à réécrire en texte (voir « Valeurs », décimal ≥ 1000).
- Chemin inconnu → l'export échoue (`ExportParser.process`) : c'est un contrôle des noms de colonnes.
- Nom d'onglet > 31 caractères → `<24 car.>-<6 hexa SHA-256>` + onglet `__config__` (`name` / `value`,
  ligne `sheet.<nom court>` → nom complet), relu par `ExcelReader.loadSheetNames` (lu dans le code, non rejoué).
- Aucune écriture en base : fichier temporaire serveur (`TempFiles`), clés `<modèle>-<id>` calculées en mémoire.
