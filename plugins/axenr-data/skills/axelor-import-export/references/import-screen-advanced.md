# Ecran d'import Excel : regles avancees capitalisees

Source : Projet claude.ai « Import / Export Axelor Avance » d'AxENR (missions 2025-2026 : reprises
fournisseurs depuis un ERP tiers, articles et tiers multi-societes, patrimoine GMAO, contrats,
gammes d'intervention, duplication comptable). Constate sur AOS 8.4.9 / 8.5 (AOP 7.3-7.4) : une regle
venue d'une seule instance est marquee « a verifier sur la version cible ».

Complete les sections BASE DE CONNAISSANCES et PIEGES CAPITALISES du `SKILL.md` ; ne les repete pas.

## 1. importId

| Regle | Pourquoi |
|---|---|
| Un importId **cree** n'a jamais de suffixe purement numerique (`partner-123`) : format `<type>-<cleMetier>` (`partner-F0000310`, `obj2026-<matricule>-<spec>`) | Axelor peut interpreter le suffixe numerique comme une cle primaire : collisions. Les importId deja presents en base (ex. `city-829` issus d'un export) restent utilisables tels quels |
| Ne jamais mettre la colonne `id` (cle primaire Hibernate) dans un fichier d'import | Exception « identifier of an instance was altered », rollback complet de la transaction |
| L'importId n'est pas toujours necessaire : un champ cle unique (`code`, `nbr`) permet la recherche directe | Evite de poser des importId inutiles sur des referentiels |
| Jamais de texte provisoire (« A RENSEIGNER », « A completer ») dans une colonne `*.importId` : laisser **vide** | Le texte est lu comme une reference : « Relation not found » |
| Pour un M2O critique, fournir `champ.id` **et** `champ.importId` (ex. `year.id` + `year.importId`) | Robustesse quand l'un des deux n'est pas pose |
| Quand les importId ont derive entre deux environnements (prod / recette), dedoublonner par une **cle metier stable** (`(modele, name)`, `(modele, SIREN)`) et generer de nouveaux importId prefixes | Reimporter avec les anciens importId cree des doublons ou ecrase la mauvaise fiche |
| Lire les `import_id` dans la **base reelle** (SQL), jamais dans un vieil export | Les fiches a `import_id` NULL se traitent a la main ou par code, jamais en leur inventant un importId (doublon) |

## 2. Resolution des M2O

- Sur certaines instances, un M2O **ne se resout que par `.importId`** : `.code`, `.name`, `.zip` laissent le
  champ vide ou donnent « Relation not found ». Pour un referentiel sans importId (villes, secteurs), lui
  poser d'abord un importId par un import dont les colonnes de recherche sont `name` (+ `zip`). A verifier
  sur la version cible.
- Les cles uniques restent legitimes : `company.code`, `currency.codeISO`, `analyticAxis.name`,
  `companySet.code`, `partnerCategory.code`. « Toujours `.importId` » vaut pour les objets sans cle unique.
- Les M2O **ne se mappent pas automatiquement** dans la configuration d'import : les mapper explicitement
  dans « Correspondance », sinon la colonne est ignoree sans message.
- Code douanier : `customsCodeNomenclature.importId` (le `.code` importe « sans erreur » mais ne met rien a
  jour), avec `usedInDEB = TRUE`.
- Categorie d'intervention : par l'importId du referentiel livre (seed), pas par le code.

## 3. M2M

- Onglet de liaison nomme `<Classe>.<champ>` (ex. `Partner.companySet`). Au-dela de 31 caracteres
  (limite Excel), le **nom du champ seul** (`productCategorySet`) est accepte.
- Mecanisme `__config__` pour les noms longs : nom d'onglet tronque = **24 premiers caracteres + « - » + 6
  premiers caracteres hexadecimaux du SHA-256** du chemin complet, et un onglet `__config__` (`name` =
  `sheet.<nom tronque>`, `value` = chemin complet). Verifie sur un export :
  `InterventionType.exclusiveInterventionSet` -> `InterventionType.exclusi-08fb12`. **SHA-256, pas MD5**
  (une ancienne note disait MD5 : elle est fausse). Sans ce mecanisme, l'onglet est ignore sans message.
- Axelor **ajoute** les liens M2M, il ne remplace pas : vider les liens existants avant un reimport qui doit
  en retirer.
- Colonne cible de l'onglet de liaison : `<champ>.importId` ou `<champ>.code` selon la cle disponible.

## 4. Dependances et ordre

- O2O (ex. Partner <-> EmailAddress) : deux temps, EmailAddress d'abord, puis Partner avec
  `emailAddress.importId`.
- Contrats (dependance circulaire : `Contract.currentContractVersion` obligatoire, `ContractVersion.contract`
  facultatif) : 6 passes.
  1. EquipmentFamily
  2. ContractVersion sans contrat
  3. Contract (`statusSelect = 2` en cours, `currentContractVersion.importId`)
  4. ContractVersion, liaison `contract.importId` (`statusSelect = 3` en cours)
  5. ContractLine
  6. Equipment (`contract.importId`)
  Deux passes sur un meme objet = **deux fichiers** (Excel interdit deux onglets homonymes). A verifier sur
  la version cible.
- Planification des contrats : l'article de maintenance preventive doit avoir un type d'intervention
  rattache a une gamme, sinon la planification ne genere rien.
- Patrimoine maintenance : ProductCategory -> Address -> Partner -> Partner.companySet -> EquipmentFamily ->
  productCategorySet -> PartnerAddress -> Equipment.

## 5. Execution

- Importer **feuille par feuille**, dans l'ordre : tout importer en une passe donne une erreur 500
  (dependances non committees).
- Choisir le bon objet dans la configuration (ex. Product et non ProductCompany) : une colonne inconnue
  apparait en rouge. Les colonnes de lecture prefixees `_` sont volontairement non mappees.
- Archiver = fichier avec `importId` + `archived = TRUE` **uniquement** : une colonne obligatoire laissee
  vide est mise a null (erreur 500 NotNull). Comptes inutilises : `statusSelect = 0` et `archived = true`.
- Tester sur 3 a 10 lignes, puis lire le fichier `importstats` (onglets Statistics et Errors). Les
  compteurs succes / echec ne suffisent pas : recouper en base, y compris les **doublons par nom** actif.
- Un import peut annoncer « success » et creer 0 enregistrement si un `@NotNull` manque (rollback
  silencieux, constate sur Equipment).
- Le bouton **Fx** recalcule les champs calcules (ex. `fullName`) sur une fiche, mais il ne se declenche
  **pas** pendant un import en lot : pre-calculer dans le fichier.

## 6. Formats et outillage

- Decimaux >= 1000 ecrits comme nombres : echec en locale francaise (« Character , is neither a decimal
  digit... »). Ecrire les decimaux en **texte** avec le point.
- openpyxl : `data_only=True` pour lire les valeurs calculees ; forcer en texte (`number_format = '@'`) les
  importId, dates et codes postaux (le zero de tete de `02140` disparait sinon) ; booleens en chaines
  `TRUE` / `FALSE`, pas en booleens Python.
- DataBackup CSV : separateur `;`, guillemets, UTF-8, colonnes relationnelles suffixees `_importId` (contre
  `.importId` dans l'import standard). Exclure `nextNum` de `Sequence.csv` en migration (sinon versions de
  sequence avec une date de fin au 31/12).
- `chart-config.xml` : conventions mixtes underscore / point (`journalType_code`, `sequence_importId` contre
  `accountType.importId`) ; pas de bind pour `accountType` ni `statusSelect` sur Account : les corriger
  apres import.

## 7. Par objet

| Objet | Regles |
|---|---|
| Address | `fullName` et `formattedFullName` pre-calcules (voir `SKILL.md`, piege 1) ; `country.code` n'existe pas : `country.importId` (fiable), `country.name` ou `country.alpha2Code` ; `city.importId` plutot que `city.zip` (un code postal = plusieurs communes, communes fusionnees) ; matching ville : export City puis `zip` + nom normalise (sans accents, `-` `'` `.` remplaces par une espace, majuscules), repli sur un code postal a commune unique, non resolus listes dans un onglet a part ; complement d'adresse integre a `fullName`. Les champs reels varient selon l'instance (`streetName` / `zip` / `postBox` contre `addressL2..L6`) : verifier sur un export |
| Partner | `partnerTypeSelect` et `currency.codeISO` toujours ; telephone `+33XXXXXXXXX` sans espace ; SIRET decompose en `siren` (9) + `nic` (5) ; conditions et modes de paiement par code, activite NAF par importId |
| Contact | `partnerTypeSelect = 2`, `isContact = TRUE`, `mainPartner.importId` ; dedoublonnage flou (seuil a regler, ex. 0,86) ; prenom en casse normale, NOM en majuscules |
| Comptes entre societes | Mapper par **code** (stable entre societes), pas par importId (propre a l'instance) |
| AccountingSituation | `company.code`, compte par importId, `fiscalPosition.importId` ; le mapping du regime de TVA source vers `vatSystemSelect` est **propre au client** : le confirmer, ne pas l'inventer |
| Journal multi-societe | Sequences mappees par **prefixe** (ex. `ACD%YY`) ; `validAccountTypeSet` dans un onglet separe |
| CORE MODEL | Ne duplique ni les comptes tiers ni les AccountingSituation (voir `SKILL.md`, pieges 10 et 11) |
| Product / ProductCompany | Prix propres a une societe dans ProductCompany (stockee dans `base_product`, contrainte unique (product, company)) ; une creation exige `productTypeSelect = storable` et `sellable = TRUE` pour etre visible ; `lastPurchasePrice` et `avgPrice` sont en lecture seule, inutiles a importer |
| Code douanier | Referentiel (`stock_customs_code_nomenclature`, module stock) **non creable par import**, codes stockes avec espaces ; garder la position a 6 chiffres de la source et prendre la feuille a 8 chiffres existante ; laisser vide plutot qu'un code faux declare en DEB |
| MrpForecast | Le CBN ne retient que `statusSelect = 2`, une date >= aujourd'hui et un emplacement de stock de la liste ; une unite NULL fait planter tout le CBN ; `statusSelect` est en lecture seule dans l'ecran mais modifiable par import |
| Equipment | `typeSelect` est une **chaine** (`place` = site, `equipment` = installation) ; `address` pointe vers **PartnerAddress** ; `@NotNull` : `partner.importId`, `name`, `equipmentFamily.code`, `customerWarrantyOnPartEndDate`, `typeSelect` ; `comments` limite a 255 caracteres (texte long dans `description`) ; hierarchie par `parentEquipment.importId`, parents avant enfants dans l'onglet |
| EquipmentFamily | Familles generiques AxENR : OND (onduleur), PAN (panneau), STR (structure), CAB (cablage), MON (monitoring), CPT (compteur), COM (communication) ; liaison `productCategorySet` |
| ProductCategory | Prefixer code **et** nom par le contexte (ex. `<PFX>-CAT-PV` / « <PFX> Photovoltaique ») pour eviter les conflits avec les donnees livrees |

## 8. Gammes d'intervention (GMAO)

Pour produire un questionnaire complet en bundle, voir aussi le skill `seeding-axelor-intervention-surveys`.

- Ne **jamais** importer `RangeQuestion.sequence` : numerotation automatique (`RQ%`). L'imposer provoque un
  doublon de cle a l'ajout manuel suivant et casse les questions conditionnelles.
- Lignes meres avant leurs conditionnelles ; `orderSeq` par pas de 10, conditionnelles a +1, +2.
- « Texte + photo » = deux questions conditionnelles (texte, photo).
- Une Question est mutualisable entre gammes (cle : titre + indication + type de reponse).
- `rangeTypeSelect` : standard / equipment / family ; ordre header -> equipment -> footer.
- Ne jamais reimporter des InterventionQuestion : supprimer et recreer l'intervention.
- Le M2O de OrderedRange vers Range s'appelle `rangeVal` (pas `range`) ; InterventionType se relie aux
  gammes par trois listes via OrderedRange.
- `answerTypeSelect` (text, picture, signature, checkbox, measure, list) : constantes natives, rien a creer.

## 9. Diagnostic

- Erreurs en cascade (Address -> Partner.mainAddress -> Equipment.address) : chercher **la** cause racine ;
  V1 diagnostic, V2 correctif cible, V3 validation, chaque version etant un fichier **complet regenere**
  (`Import_<Objet>_V<n>.xlsx`), jamais un patch.
- Generateur d'indicateurs Axelor : SELECT uniquement (DELETE / UPDATE -> GenericJDBCException).
- NPE dans `XxxRepository.save()` : lire la methode `save()` du repository dans les sources AOS de la version
  installee (`axelor-base/src/main/java/com/axelor/apps/base/db/repo/`) pour trouver le champ null.
- Ordre de diagnostic : droits -> configuration low-code -> documentation -> code source.
