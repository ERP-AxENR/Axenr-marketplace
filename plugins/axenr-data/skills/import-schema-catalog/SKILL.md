---
name: import-schema-catalog
description: Catalogue de reference des schemas d'import Axelor/AxENR - structure des 10 feuilles type fournisseurs, AccountType FRA_PCG mapping, conventions chart-config.xml, ordre d'import par type de relation. Consomme par import-export-agent.
---

# Import Schema Catalog

> Base de connaissances versionnee pour l'agent import-export-agent. Schemas concrets + mappings critiques.

## TYPES DE RELATIONS

| Type | Tables | Ordre | Syntaxe colonne |
|------|--------|-------|-----------------|
| Champs simples | T1 | T1 | `champSimple` |
| M2O | T1 + T2 | T2 -> T1 | `champ.importId` |
| O2M | T1 + T2 | T1 -> T2 | `parent.importId` (dans T2) |
| M2M | T1 + T2 + T3 | T2 -> T1 -> T3 | Nom onglet T3 = nom champ Java |

## CATALOGUE - IMPORT FOURNISSEURS (reference AxENR)

Base : `Import_Fournisseurs_COMPLET.xlsx` (1 034 fournisseurs, 10 feuilles).

### Feuille 1 : Account (plan comptable fournisseur)

```
importId                     : EMS-F0000001
company.code                 : 101
parentAccount.importId       : AXENR0070
code                         : F0000001
name                         : ABDE DEROUBAIX
accountType.importId         : FRA_PCG240
reconcileOk                  : TRUE
useForPartnerBalance         : TRUE
commonPosition               : 1
statusSelect                 : 1
isRetrievedOnPaymentSession  : TRUE
```

Lignes : 1 033. Nommage : `EMS-F<7digits>` (prefixe societe + numero fournisseur).

### Feuille 2 : City

```
importId       : city-new-1 (nouvelle) | city-31761 (existante)
name           : METZINGEN
zip            : 72555
country.importId : 67
country.name   : FRANCE
```

Lignes : 120.

### Feuille 3 : Bank

```
code                    : AGRIFRPP866
bankName                : CREDIT AGRICOLE
country.importId        : 67
country.name            : FRANCE
businessPartyPrefix     : AGRI
businessPartySuffix     : PP
branchIdentifier        : 866
```

Lignes : 127. Le code = BIC/SWIFT (pivot pour BankDetails.bank.code).

### Feuille 4 : Address

```
importId             : addr-F0000001
floor                : (optionnel)
addressL2..L6        : (lignes postales)
streetName           : RUE DES RIBAUX
zip                  : 35420
city.importId        : city-31761
country.importId     : 67
fullName             : RUE DES RIBAUX 35420 LOUVIGNE DU DESERT
formattedFullName    : (avec sauts de ligne)
```

Lignes : 786.

### Feuille 5 : EmailAddress

```
importId  : email-F0000001
address   : sarl-abde@abde-deroubaix.com
name      : ABDE DEROUBAIX
```

Lignes : 344.

### Feuille 6 : Partner (tiers fournisseur - PIVOT)

```
importId                   : partner-F0000001
name                       : SARL ABDE DEROUBAIX
partnerSeq                 : T00001
partnerTypeSelect          : 1 (personne morale) ou 2 (personne physique)
isSupplier                 : TRUE
isCustomer                 : FALSE
registrationCode           : 80782892600012 (SIRET)
siren                      : 807828926
nic                        : 00012
taxNbr                     : FR87807828926
mainAddress.importId       : addr-F0000001
currency.codeISO           : EUR
fixedPhone                 : +33299980124
mobilePhone                : +33299980124
webSite                    : (optionnel)
emailAddress.importId      : email-F0000001
outPaymentCondition.code   : 30JRNET
outPaymentMode.code        : DEC_VIR
mainActivity.importId      : (optionnel)
shipmentMode.importId      : (optionnel)
partnerCategory.code       : LOC
fiscalPosition.importId    : fiscal-position-3
```

Lignes : 1 033.

### Feuille 7 : PartnerAddress (relation Partner <-> Address)

```
importId             : pa-F0000001
isDefaultAddr        : TRUE
partner.importId     : partner-F0000001
isDeliveryAddr       : TRUE
isInvoicingAddr      : TRUE
address.importId     : addr-F0000001
```

Lignes : 786. O2M depuis Partner.

### Feuille 8 : BankDetails

```
importId         : bd-F0000001
partner.importId : partner-F0000001
ownerName        : ABDE DEROUBAIX
iban             : FR7616606100230013135815914
bank.code        : AGRIFRPP866
isDefault        : TRUE
active           : TRUE
```

Lignes : 719. M2O vers Partner et Bank (via Bank.code, pas importId).

### Feuille 9 : AccountingSituation

```
importId                  : accsit-F0000001
partner.importId          : partner-F0000001
company.code              : 101
supplierAccount.importId  : EMS-F0000001
vatSystemSelect           : 1
```

Lignes : 1 033.

Pour un tiers client, ajouter `customerAccount.importId`.

### Feuille 10 : Partner.companySet (M2M Partner <-> Company)

```
importId          : partner-F0000001
companySet.code   : 101
```

Lignes : 1 033. Structure 3e onglet M2M : 1 ligne = 1 affectation tiers/societe.

## ORDRE D'IMPORT POUR FOURNISSEURS COMPLETS

```
1. Country                     (si pays nouveaux)
2. City                        (refs Country)
3. Address                     (refs City, Country)
4. EmailAddress                (standalone)
5. Bank                        (refs Country)
6. Account                     (refs AccountType, parentAccount)
7. Partner                     (refs Address, EmailAddress, PaymentCondition, PaymentMode, PartnerCategory, FiscalPosition)
8. PartnerAddress              (refs Partner, Address)    - onglet O2M de Partner
9. BankDetails                 (refs Partner, Bank)       - onglet O2M de Partner
10. AccountingSituation        (refs Partner, Company, Account)
11. Partner.companySet         (refs Partner, Company)    - onglet M2M
```

## MAPPING AccountType NUMERIQUE -> FRA_PCG

Le DataBackup stocke des importId numeriques. L'import Axelor attend les codes FRA_PCG.

```
1  -> FRA_PCG0       VUES
2  -> FRA_PCG110     IMMOBILISATIONS
3  -> FRA_PCG120     ACTIF COURANT
4  -> FRA_PCG130     LIQUIDITES
5  -> FRA_PCG140     CLIENTS
6  -> FRA_PCG200     ACTIF
7  -> FRA_PCG210     CAPITAUX
8  -> FRA_PCG220     PROVISIONS
9  -> FRA_PCG230     DETTES
10 -> FRA_PCG240     FOURNISSEURS
11 -> FRA_PCG250     TAXES
12 -> FRA_PCG1000    PRODUITS
13 -> FRA_PCG2000    CHARGES
14 -> FRA_PCG9000    SPECIAUX
15 -> FRA_PCG9010    ENGAGEMENTS
```

## CONVENTIONS chart-config.xml (CORE MODEL)

| Champ | Convention |
|-------|------------|
| `journalType_code` | underscore |
| `tax_code` | underscore |
| `sequence_importId` (dans AccountManagement) | underscore |
| `accountType.importId` | point |
| `sequence.importId` (dans Journal) | point |

## TRANSFORMATIONS DataBackup -> IMPORT

| DataBackup (source) | Import (cible) | Source de verite |
|---------------------|----------------|------------------|
| `supplierAccount_importId` (numerique) | `supplierAccount_code` | Account.csv |
| `customerSalesJournal_importId` | `customerSalesJournal_code` | Journal.csv |
| `tax_importId` | `tax_code` | Tax.csv |
| `defaultTaxSet` (M2M) | Codes separes par `|` (ex: `N_D|N_C`) | Tax.csv |

## FORMAT CSV DE SORTIE (CORE MODEL)

- Separateur : `;`
- Guillemets doubles sur TOUS les champs
- UTF-8
- Filtrage strict par `company_importId` de la source

## ERREURS COURANTES

| Erreur | Cause | Solution |
|--------|-------|----------|
| `Record not found` | Objet reference n'existe pas encore | Respecter l'ordre d'import (T2 avant T1 pour M2O) |
| `Column not found` | Mauvais nom de colonne | Exporter un modele depuis Axelor pour avoir les noms exacts |
| `Sheet not found` | Mauvais nom d'onglet M2M | Nom onglet = nom EXACT du champ Java |
| `Invalid date format` | Pas YYYY-MM-DD | Transformer via formule |
| `Duplicate importId` | importId non unique | Verifier unicite avant import |
| `Foreign key violation` | FK pointe sur importId absent | Verifier que l'onglet ref est importe en premier |

## REGLE "AUTORISER LA REIMPORTATION"

Lors de l'export d'un modele depuis Axelor, toujours cocher **"Autoriser la reimportation"** pour chaque champ. Cela garantit que les importId sont presents dans l'export et permettent la reimportation / mise a jour.

## REGLES SPECIFIQUES PAR OBJET (CAPITALISEES)

### Address

- `fullName` et `formattedFullName` OBLIGATOIRES a pre-remplir (sinon NPE serveur)
- `fullName = "<streetName> <zip> <city.name>"`
- `formattedFullName = "<streetName>\n<zip> <city.name>\n<country.name>"` (sauts de ligne reels)
- Reference city via `city.importId` (pas par nom)

### Partner

- `partnerTypeSelect` obligatoire : `1` (personne morale) ou `2` (personne physique)
- `currency.codeISO` obligatoire meme si defaut societe (ex: `EUR`)
- `isSupplier` OU `isCustomer` au moins un des deux = `TRUE`
- Si SIRET : remplir `registrationCode` + `siren` + `nic` + `taxNbr` (TVA) de maniere coherente
- `partnerSeq` peut etre genere automatiquement par Axelor si non fourni (selon config)

### BankDetails

- `active=TRUE` OBLIGATOIRE (sinon IBAN invisible dans les modes de paiement)
- `isDefault=TRUE` pour le premier IBAN d'un tiers (au moins un defaut requis)
- `bank.code` utilise le BIC/SWIFT (ex: `AGRIFRPP866`) - PAS importId
- `ownerName` utile meme si identique a partner.name (edge case proprietaire different)

### AnalyticAccount (edge case)

- Reference l'axe via `analyticAxis.name` et NON `analyticAxis.importId`
- Seul cas connu a AxENR qui contredit la convention standard Axelor
- Verifier que l'AnalyticAxis existe avec ce nom exact avant import

### AccountingSituation

- `company.code` (pas importId)
- `supplierAccount.importId` ou `customerAccount.importId` selon isSupplier/isCustomer
- `vatSystemSelect` obligatoire (1=debit, 2=encaissement)

### Partner.companySet (M2M)

- Nom d'onglet EXACT : `Partner.companySet`
- Colonne 2 : `companySet.code` (pas importId)
- 1 ligne par affectation tiers/societe (un tiers sur 3 societes -> 3 lignes)

### Account (plan comptable fournisseur)

- `accountType.importId` = code FRA_PCG (ex: `FRA_PCG240` pour fournisseurs)
- `parentAccount.importId` = le compte racine (ex: `AXENR0070` = compte 401 agrege)
- `statusSelect=1` (actif), `commonPosition=1` (debit), selon le sens du compte
- `reconcileOk=TRUE` et `useForPartnerBalance=TRUE` pour les comptes F/C

## CONVENTION DE NOMMAGE importId AxENR

Format strict : `<type>-<cleMetier>` ou :
- `type` = prefixe court stable pour l'entite
- `cleMetier` = identifiant signifiant du domaine (jamais un auto-increment, toujours un code ou une cle metier)

Table complete :

| Objet | Prefixe | cleMetier | Exemple |
|-------|---------|-----------|---------|
| Partner | `partner-` | code fournisseur/client | `partner-F0000310` |
| Address | `addr-` | code fournisseur/client | `addr-F0000310` |
| PartnerAddress | `pa-` | code fournisseur/client | `pa-F0000310` |
| EmailAddress | `email-` | code fournisseur/client | `email-F0000310` |
| BankDetails | `bd-` | code fournisseur/client | `bd-F0000310` |
| AccountingSituation | `accsit-` | code fournisseur/client | `accsit-F0000310` |
| City | `city-` | geonameId | `city-31761` |
| Account (plan fournisseurs) | `EMS-` | code compte | `EMS-F0000310` |
| Account (plan clients) | `EMS-` | code compte | `EMS-C0000310` |

Pourquoi : reproductibilite absolue. Un meme `F0000310` aura le meme importId dans tous les onglets, donc les reimports / mises a jour fonctionnent sans recalcul.

## REGLE @NotNull (mises a jour)

Pour toute **mise a jour** d'un objet existant, inclure TOUS les champs `@NotNull` de la classe Java, meme s'ils ne changent pas. Axelor applique une validation stricte sur chaque enregistrement importe - une mise a jour partielle sur un objet existant sans ces champs leve une contrainte.

Comment identifier les @NotNull ? Les asterisques `*` dans le formulaire Axelor indiquent les champs obligatoires. Les exporter en premier lors de la preparation du modele.

## CAS CLIENT DOCUMENTES

### EMERAUDE SOLAIRE (societe 101)

- Convention account : `EMS-F<numero>` et `EMS-C<numero>`
- Parent account fournisseurs : `AXENR0070`
- Volumes typiques : 1000+ fournisseurs, 500+ clients

### Migrations Divalto

- Source : ERP legacy Divalto avec export CSV custom
- Volumetrie : 1000+ fournisseurs par mission
- Pieges typiques : dates format DD/MM/YYYY a convertir, SIRET avec espaces, IBAN avec espaces
- Systematiquement : lancer un nettoyage / normalisation avant le mapping

---

## CATALOGUE CHAMPS DYNAMIQUES TEMPLATES AXENR

Base : `Champs_dynamiques_templates (2).xlsx` (77 champs + 39 techniques XDocReport).

### Racines modeles

| Racine | Usage | Syntaxe |
|--------|-------|---------|
| `d=Project` | Templates lies au projet / site de production | `{d.xxx}` |
| `d=Contract` | Templates de contrat de maintenance | `{d.xxx}` |
| `c` | Contexte independant du modele (date, user) | `{c.xxx}` |

### Templates AxENR recenses

| Template | Racine | Nb champs | Usage |
|----------|--------|-----------|-------|
| Contrat de maintenance | Contract | 23 | Contrat entre AxENR et le client |
| Changement demandeur | Project | 16 | Changement de titulaire PRM/PRM |
| Mandat ENEDIS | Project | 13 | Mandat de representation ENEDIS |
| Fiche de collecte | Project | 10 | Collecte d'infos chantier |
| Lettre de cession | Project | 9 | Cession de creance / facture |
| Mandat GEREDIS | Project | 9 | Mandat GRD GEREDIS |
| Attestation | Project | 4 | Attestation generique |
| Attestation unite fonciere | Project | 1 | Justificatif foncier |

### Champs Project (clientPartner / adresse chantier)

```
{d.name}                                                     -> nom du projet
{d.gRDReference}                                             -> reference GRD (n raccordement Enedis)
{d.inverterPowerKVADR}                                       -> puissance onduleurs DR kVA
{d.moduleRealPowerKWcQuote}                                  -> puissance reelle modules kWc
{d.realInverterDetails}                                      -> details onduleurs (texte)
{d.customerAddress.streetName}                               -> rue du chantier
{d.customerAddress.city.fullName}                            -> ville + CP chantier
{d.customerAddress.city.inseeCode}                           -> code INSEE commune
{d.clientPartner.name}                                       -> raison sociale client
{d.clientPartner.firstName}                                  -> prenom si personne physique
{d.clientPartner.titleSelect}                                -> civilite (selection brute)
{d.clientPartner.partnerTypeSelect}                          -> type tiers (1/2)
{d.clientPartner.partnerCategory.name}                       -> forme juridique
{d.clientPartner.registrationCode}                           -> SIRET
{d.clientPartner.siren}                                      -> SIREN
{d.clientPartner.mainActivity.fullName}                      -> activite principale NACE
{d.clientPartner.mainContactLastName}                        -> nom contact
{d.clientPartner.mainContactFirstName}                       -> prenom contact
{d.clientPartner.fixedPhone}                                 -> telephone
{d.clientPartner.emailAddress.address}                       -> email
```

### Siege social via clientPartner (filtre adresse par defaut)

```
{d.clientPartner.partnerAddressList[isDefaultAddr=true].address.streetName}        -> rue siege
{d.clientPartner.partnerAddressList[isDefaultAddr=true].address.city.fullName}     -> ville + CP siege
{d.clientPartner.partnerAddressList[isDefaultAddr=true].address.city.name}         -> ville seule
{d.clientPartner.partnerAddressList[isDefaultAddr=true].address.city.inseeCode}    -> code INSEE siege
```

### Champs Contract + ContractVersion

```
{d.contractId}                                               -> identifiant contrat
{d.integer154}                                               -> champ custom (surface m2)
{d.string155}                                                -> champ custom (puissance kWc)
{d.currentContractVersion.yearlyExTaxTotalRevalued}          -> montant HT annuel revise
{d.currentContractVersion.fromDate}                          -> date debut version
{d.invoicedPartner.name}                                     -> raison sociale partenaire facture
{d.invoicedPartner.shareCapital}                             -> capital social
{d.invoicedPartner.registrationCode}                         -> SIRET partenaire facture
{d.invoicedPartner.partnerAddressList[isDefaultAddr=true].address.streetName}      -> rue siege facture
{d.invoicedPartner.partnerAddressList[isDefaultAddr=true].address.city.fullName}   -> ville siege facture
```

### Boucles sur listes (ContractLine, Equipment)

```
# Boucle lignes de contrat (tableau Word, 2 lignes repetables) :
Ligne 1 : {d.currentContractVersion.contractLineList[i].productName} |
          {d.currentContractVersion.contractLineList[i].exTaxTotal} |
          {d.currentContractVersion.contractLineList[i].periodicity.name}
Ligne 2 : {d.currentContractVersion.contractLineList[i+1].productName} |
          {d.currentContractVersion.contractLineList[i+1].exTaxTotal} |
          {d.currentContractVersion.contractLineList[i+1].periodicity.name}

# Boucle equipements avec variable locale :
{#eq = d.relatedEquipmentList[i]}
  Equipement : {$eq.name}
  Nombre onduleurs : {$eq.integer29}
  Produit lie : {$eq.manyToOne28.name}
  Date mise en service : {$eq.commissioningDate:formatD('L')}
  kWc : {$eq.kwcPower}
  kVA : {$eq.kvaPower}
  Site : {$eq.parentEquipment.name}
{d.relatedEquipmentList[i+1].name}   -> balise de fin
```

### Contexte

```
{c.now:formatD('L')}          -> date du jour localisee (17 avril 2026)
{c.now:formatD('dd/MM/YYYY')} -> format personnalise
```

### Techniques XDocReport critiques

| Technique | Syntaxe | Exemple |
|-----------|---------|---------|
| Filtre liste | `[champ=valeur]` | `[isDefaultAddr=true]` |
| Boucle tableau | `[i]` / `[i+1]` | 2 lignes repetables |
| Variable locale | `{#var = expr}` puis `{$var.x}` | `{#eq = d.list[i]}` |
| Substr debut | `:substr(0, N)` | `{d.x:substr(0, 2)}` |
| Substr depuis | `:substr(N)` | `{d.x:substr(2)}` |
| Conditionnel egal | `:ifEQ('v'):showBegin ... :showEnd` | Bloc pour societe |
| Conditionnel diff | `:ifNE('v'):showBegin ... :showEnd` | Bloc pour perso physique |
| Date format | `:formatD('L')` / `:formatD('dd/MM/YYYY')` | Date localisee / custom |
| Fallback | `x != null ? x : y` | SIRET sinon SIREN |
| Image Base64 | `__tools__.toBase64Uri(champ)` | Logo, signature |

### Pieges templates Word AxENR

1. Word coupe `{d.name}` en morceaux a la correction auto -> unzip + inspect xml
2. Guillemets typographiques `"..."` cassent les filtres `[x=true]` -> desactiver correction auto
3. Balise de fin `[i+1]` obligatoire pour cloturer une boucle
4. Racine `d=Project` vs `d=Contract` -> un champ n'existe pas dans les deux
5. Liste sans filtre prend le premier element alphanumerique (pas forcement le bon)

### TemplateSettings Axelor (configuration reelle)

Base : `export-18305...xlsx` (61 TemplateSettings + 306 TemplateSettingsLine).

Permet de creer des **champs calcules Groovy** cote Axelor (avant rendu XDocReport) :

```groovy
// Exemple : booleen derive "isCompliant"
listAnswer?.name?.contains('Conforme')

// Exemple : remplacement regex
realInverterDetails.replaceAll('^[0-9]+\\s*', '')
```
