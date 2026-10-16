---
name: template-expert-catalog
description: Catalogue de reference pour axenr-template-expert - patterns XDocReport valides, pieges documentes, modeles racines, 77 champs dynamiques Project/Contract, 39 techniques (filtres, boucles, variables locales, conditionnels, substr, dates, fallback, Base64). Inclut le contournement Groovy pour chaines 3+ niveaux et les regles TemplateSettingsLine.
---

# Template Expert Catalog

> Knowledge base versionnee pour l'agent `axenr-template-expert`. Centralise patterns, pieges, modeles racines, catalogue complet des 77 champs et 39 techniques XDocReport.

## 1. PATTERNS XDOCREPORT VALIDES

### Champ simple

```
{d.name}                                -> nom du projet
{d.contractId}                          -> identifiant contrat
```

### Relations 1-2 niveaux (OK en direct)

```
{d.clientPartner.name}                  -> nom du client
{d.clientPartner.registrationCode}      -> SIRET
{d.clientPartner.firstName}             -> prenom
{d.clientPartner.siren}                 -> SIREN
{d.clientPartner.fixedPhone}            -> telephone
{d.clientPartner.partnerCategory.name}  -> forme juridique (2 niveaux OK)
```

### Relations 3+ niveaux (PIEGE - voir contournement)

```
{d.clientPartner.mainAddress.city.fullName}    -> VIDE silencieusement
```

**Contournement OBLIGATOIRE** : creer un champ Groovy derive au niveau racine.

### Filtre de liste

```
Syntaxe : [<champ>=<valeur>]

Exemples :
{d.clientPartner.partnerAddressList[isDefaultAddr=true].address.streetName}
{d.clientPartner.partnerAddressList[isInvoicingAddr=true].address.fullName}
{d.clientPartner.partnerAddressList[isDeliveryAddr=true].address.city.name}
```

Cas d'usage : isoler l'adresse du siege parmi N adresses d'un partenaire.

### Boucle sur liste (pattern [i]/[i+1])

```
Placer [i] sur la premiere ligne repetable, [i+1] sur la ligne fermante.

Exemple (tableau Word 2 lignes) :
Ligne 1 | {d.currentContractVersion.contractLineList[i].productName} | {d.currentContractVersion.contractLineList[i].exTaxTotal}
Ligne 2 | {d.currentContractVersion.contractLineList[i+1].productName} | {d.currentContractVersion.contractLineList[i+1].exTaxTotal}
```

### Variable locale (dans une boucle)

```
Syntaxe :
  {#nomVar = d.liste[i]}   <- declaration
  {$nomVar.champ}          <- acces

Exemple :
  {#eq = d.relatedEquipmentList[i]}
  Nom : {$eq.name}
  Puissance : {$eq.kwcPower} kWc
  Mise en service : {$eq.commissioningDate:formatD('L')}
  Site : {$eq.parentEquipment.name}
  {d.relatedEquipmentList[i+1].name}  <- balise de fin de boucle
```

Rend une boucle beaucoup plus lisible quand on accede plusieurs fois au meme element.

### Substring

```
:substr(0, N)     -> N premiers caracteres
:substr(N)        -> a partir de la position N

Exemple :
{d.realInverterDetails:substr(0, 2)}    -> "12" (quantite)
{d.realInverterDetails:substr(2)}       -> " SMA Sunny Tripower 50"
```

### Conditionnel

```
:ifEQ('valeur'):showBegin ... :showEnd   -> affiche SI egal
:ifNE('valeur'):showBegin ... :showEnd   -> affiche SI different

Exemple :
{d.clientPartner.partnerTypeSelect:ifEQ('Societe'):showBegin}Texte pour societes{d.clientPartner.partnerTypeSelect:showEnd}

{d.clientPartner.partnerTypeSelect:ifNE('Societe'):showBegin}Texte pour personnes physiques{d.clientPartner.partnerTypeSelect:showEnd}
```

### Date formatee

```
:formatD('L')                 -> format localise (ex: 17 avril 2026)
:formatD('dd/MM/YYYY')        -> format personnalise

Exemples :
{c.now:formatD('L')}                              -> date du jour
{d.currentContractVersion.fromDate:formatD('L')}  -> date de debut version contrat
{$eq.commissioningDate:formatD('L')}              -> date mise en service (dans boucle)
```

### Fallback ternaire

```
Syntaxe : {d.champ != null ? d.champ : d.champDeSecours}

Exemple :
{d.clientPartner.registrationCode != null ? d.clientPartner.registrationCode : d.clientPartner.siren}
   -> SIRET s'il existe, sinon SIREN
```

### Image Base64 (dans TemplateSettingsLine)

```
Syntaxe Groovy : __tools__.toBase64Uri(champ)

Exemple dans la colonne field :
__tools__.toBase64Uri(picture)

-> utilisable ensuite dans le Word comme image embarquee.
```

### Expression Groovy (TemplateSettingsLine field)

```
Regles :
- Toujours ?. (safe navigation)
- Toujours ?: '' (fallback)
- Syntaxe Groovy, pas XDocReport

Exemples :
clientPartner?.mainAddress?.city?.fullName ?: ''          -> contournement 3+ niveaux
listAnswer?.name?.contains('Conforme')                    -> booleen derive
realInverterDetails?.replaceAll('^[0-9]+\\s*', '') ?: ''  -> retire prefixe numerique
```

## 2. PIEGES DOCUMENTES

### P1 - Chaines 3+ niveaux (CRITIQUE)

**Symptome** : `{d.a.b.c.d}` revient vide meme si le parametrage est correct.

**Cas confirme** (Emeraude) :
- `{d.clientPartner.mainAddress.streetName}` OK
- `{d.clientPartner.mainAddress.city.fullName}` VIDE

**Cause** : defaut de chargement recursif XDocReport quand le 3eme niveau est relationnel.

**Solution** : creer `clientCityFullName` au niveau racine avec Groovy `clientPartner?.mainAddress?.city?.fullName ?: ''`. Utiliser ensuite `{d.clientCityFullName}`.

### P2 - mainAddress inexistant directement

Le Partner n'expose pas directement `mainAddress` dans toutes les versions. Utiliser `partnerAddressList[isDefaultAddr=true]` avec adresses validees (liees a City et Country, pas texte libre).

### P3 - numberFormat absent

Pas de fonction `:numberFormat(...)` dans cette version. Passer par Groovy `new java.text.DecimalFormat('#,##0.00').format(champ)` dans TemplateSettingsLine.

### P4 - Groovy dans Word ne s'execute pas

Le Word ne connait que la syntaxe XDocReport. Tout Groovy DOIT etre dans TemplateSettingsLine.field, jamais dans le .docx.

### P5 - Word coupe les balises

Correction auto Word peut couper `{d.name}` en `{d.` et `name}` (runs XML separes). Desactiver correction auto avant edition, ou reparer via unzip/edit/rezip.

### P6 - Guillemets typographiques

Word remplace `"` par `"` et `"`. Casse les filtres `[isDefaultAddr=true]` si la valeur est entre guillemets. Desactiver la correction auto des guillemets.

### P7 - Filtres M2O/O2M necessitent metaField

Les filtres `[x=true]` peuvent echouer si le metaField de la navigation n'est pas defini dans l'UI Axelor. Verifier dans Parametrages > Meta si le filtre echoue silencieusement.

### P8 - Images liees vs embarquees

Axelor genere cote serveur. Images liees (reference externe) = placeholder casse. Seules les images embarquees (PNG/JPEG dans le .docx) fonctionnent.

### P9 - PurchaseOrderLine : productCode vs productName vs product.fullName

- `productCode` = code fournisseur fige au moment de la commande
- `productName` = code article interne fige
- `product.fullName` = designation live du catalogue

Ne pas confondre.

### P10 - Racine non-interchangeable

`d.clientPartner` inexistant sur `d = Contract`. Utiliser `d.invoicedPartner`. Toujours verifier la racine en premier.

### P11 - Pas de Studio

Contrainte AxENR : aucun champ custom via Studio. Tout champ derive passe par TemplateSettingsLine + Groovy.

### P12 - Balise de fin boucle

Boucle `[i]` sans `[i+1]` de fin = boucle infinie ou mauvais rendu. Toujours fermer.

### P13 - NPE sur chaines Groovy

`clientPartner.mainAddress.city.name` sans safe navigation = NPE si un intermediaire est null. Toujours `?.` et `?: ''`.

## 3. MODELES RACINES ET CHEMINS

| Modele | d= | Client | Adresse(s) | Version active | Specificites |
|--------|-----|--------|------------|----------------|--------------|
| Project | d=Project | `d.clientPartner` | `d.customerAddress` | - | Enedis, attestations, mandats, fiches |
| Contract | d=Contract | `d.invoicedPartner` | via tiers/equipements | `d.currentContractVersion` | Lignes : `.contractLineList[i]`, Equipements : `d.relatedEquipmentList[i]` |
| PurchaseOrder | d=PurchaseOrder | `d.supplierPartner` | via fournisseur | - | Lignes : `.purchaseOrderLineList[i]` |
| Umr | d=Umr | variable | - | - | Unite fonciere, contexte Enedis |
| Context (sans modele) | c | - | - | - | `c.now`, `c.user`, etc. |

### Project - champs courants

```
{d.name}                                                                 -> nom du projet / site de production
{d.gRDReference}                                                         -> reference GRD (n raccordement Enedis)
{d.inverterPowerKVADR}                                                   -> puissance onduleurs DR (kVA)
{d.moduleRealPowerKWcQuote}                                              -> puissance reelle modules (kWc)
{d.realInverterDetails}                                                  -> details onduleurs installes
{d.customerAddress.streetName}                                           -> rue chantier
{d.customerAddress.city.fullName}                                        -> ville + CP chantier
{d.customerAddress.city.inseeCode}                                       -> code INSEE commune chantier
{d.clientPartner.name}                                                   -> raison sociale client
{d.clientPartner.firstName}                                              -> prenom si physique
{d.clientPartner.titleSelect}                                            -> civilite (valeur brute select)
{d.clientPartner.partnerTypeSelect}                                      -> type (1=morale, 2=physique)
{d.clientPartner.partnerCategory.name}                                   -> forme juridique
{d.clientPartner.registrationCode}                                       -> SIRET
{d.clientPartner.siren}                                                  -> SIREN
{d.clientPartner.mainActivity.fullName}                                  -> activite NACE
{d.clientPartner.mainContactLastName}                                    -> nom contact
{d.clientPartner.mainContactFirstName}                                   -> prenom contact
{d.clientPartner.mainContactFunction.name}                               -> fonction contact
{d.clientPartner.fixedPhone}                                             -> telephone fixe
{d.clientPartner.emailAddress.address}                                   -> email
{d.clientPartner.taxNbr}                                                 -> TVA intracommunautaire
{d.clientPartner.shareCapital}                                           -> capital social
{d.clientPartner.rcsCity.name}                                           -> ville RCS
```

### Project - siege social (via filtre)

```
{d.clientPartner.partnerAddressList[isDefaultAddr=true].address.streetName}       -> rue siege
{d.clientPartner.partnerAddressList[isDefaultAddr=true].address.city.fullName}    -> ville + CP siege
{d.clientPartner.partnerAddressList[isDefaultAddr=true].address.city.name}        -> ville seule
{d.clientPartner.partnerAddressList[isDefaultAddr=true].address.city.inseeCode}   -> INSEE siege
```

### Contract - champs courants

```
{d.contractId}                                                         -> identifiant contrat (M26-015, etc.)
{d.integer154}                                                         -> champ custom entier (surface m2)
{d.string155}                                                          -> champ custom texte (puissance kWc)
{d.currentContractVersion.yearlyExTaxTotalRevalued}                    -> montant HT annuel revise
{d.currentContractVersion.fromDate}                                    -> date debut version
{d.invoicedPartner.name}                                               -> raison sociale partenaire facture
{d.invoicedPartner.shareCapital}                                       -> capital social facture
{d.invoicedPartner.registrationCode}                                   -> SIRET partenaire facture
{d.invoicedPartner.mainContactLastName}                                -> nom contact facture
{d.invoicedPartner.mainContactFirstName}                               -> prenom contact facture
```

### Contract - siege social partenaire facture

```
{d.invoicedPartner.partnerAddressList[isDefaultAddr=true].address.streetName}     -> rue siege facture
{d.invoicedPartner.partnerAddressList[isDefaultAddr=true].address.city.fullName}  -> ville + CP siege facture
```

### Contract - boucle sur lignes

```
Tableau 2 lignes :
Ligne 1 : {d.currentContractVersion.contractLineList[i].productName}      | {d.currentContractVersion.contractLineList[i].exTaxTotal}      | {d.currentContractVersion.contractLineList[i].periodicity.name}
Ligne 2 : {d.currentContractVersion.contractLineList[i+1].productName}    | {d.currentContractVersion.contractLineList[i+1].exTaxTotal}    | {d.currentContractVersion.contractLineList[i+1].periodicity.name}
```

### Contract - boucle sur equipements avec variable locale

```
- {d.relatedEquipmentList[i].name} {#eq = d.relatedEquipmentList[i]}
  Onduleurs : {$eq.integer29} * {$eq.manyToOne28.name}
  Mise en service : {$eq.commissioningDate:formatD('L')}
  kWc : {$eq.kwcPower}
  kVA : {$eq.kvaPower}
  Site : {$eq.parentEquipment.name}
- {d.relatedEquipmentList[i+1].name}
```

### Contexte (c=)

```
{c.now:formatD('L')}                 -> date du jour localisee (17 avril 2026)
{c.now:formatD('dd/MM/YYYY')}        -> format personnalise
{c.now:formatD('yyyy-MM-dd')}        -> ISO
```

## 4. TEMPLATES AXENR RECENSES

| Template | Racine | Nb champs | Usage |
|----------|--------|-----------|-------|
| Contrat de maintenance | Contract | 23 | Contrat AxENR / client |
| Changement demandeur | Project | 16 | Changement titulaire PRM Enedis |
| Mandat ENEDIS | Project | 13 | Mandat representation ENEDIS |
| Fiche de collecte | Project | 10 | Collecte d'infos chantier |
| Lettre de cession | Project | 9 | Cession creance / facture |
| Mandat GEREDIS | Project | 9 | Mandat GRD GEREDIS |
| Attestation | Project | 4 | Attestation generique |
| Attestation unite fonciere | Project (ou Umr) | 1 | Justificatif foncier |
| CARD-I BT | Project | 20+ | Contrat acces reseau distribution BT |
| CARD-I HTA | Project | 25+ | Contrat acces reseau distribution HTA |

## 5. LECTURE D'UN EXPORT TemplateSettingsLine

### Structure de la feuille

| Colonne | Role | Exemple |
|---------|------|---------|
| importId | identifiant unique | `template-settings-line-64` |
| templateSettings.name | template rattache | `Projet`, `Contrat`, `Partner`, `Address` |
| nameInTemplate | nom a utiliser apres `d.` dans le Word | `clientCityFullName` |
| field | expression Axelor (champ simple OU Groovy) | `clientPartner?.mainAddress?.city?.fullName ?: ''` |
| metaModel | modele cible | `com.axelor.apps.project.db.Project` |
| ... | autres colonnes de metadata | - |

### Rules de validation

Avant d'utiliser `{d.clientCityFullName}` dans un template `Projet` :

1. Verifier qu'il existe une ligne avec `templateSettings.name = "Projet"` ET `nameInTemplate = "clientCityFullName"`
2. Si oui : OK, utiliser tel quel
3. Si non : signaler dans "Points de vigilance" du rapport

Format de signalement :

```markdown
### Champs a creer dans Axelor

A ajouter dans Parametrages > Templates > Projet > TemplateSettingsLine :

| nameInTemplate | field (Groovy suggere) | Raison |
|----------------|------------------------|--------|
| clientCityFullName | clientPartner?.mainAddress?.city?.fullName ?: '' | contournement chaine 3+ niveaux |
```

## 6. CONVENTIONS DE NOMMAGE DES LIVRABLES

```
<TypeDoc>_<Client>_V<N>.docx

Exemples :
- Mandat_ENEDIS_Systeko_V1.docx
- Contrat_Maintenance_Planete_V2.docx
- Fiche_Collecte_Emeraude_V3.docx
- CARD-I_BT_Planete_V1.docx
- Attestation_UF_Systeko_V1.docx
```

Destination : `~/Downloads/` par defaut, jamais dans `axenr-app`.

## 7. CHECKLIST DE VALIDATION AVANT LIVRAISON

- [ ] Toutes les zones `[...]` / `{...}` utilisateur remplacees par la syntaxe XDocReport
- [ ] Racine `d =` declaree et coherente dans tout le document
- [ ] Tous les champs utilises verifies dans TemplateSettingsLine
- [ ] Champs manquants listes dans "Points de vigilance" avec Groovy suggere
- [ ] Boucles fermees avec `[i+1]`
- [ ] Variables locales declarees avant usage (`{#var = ...}`)
- [ ] Mise en page preservee (si template source fourni)
- [ ] Chaines 3+ niveaux remplacees par champs Groovy derives au niveau racine
- [ ] Images embarquees (pas de liens)
- [ ] Guillemets droits preserves dans les filtres
- [ ] NO EMOJIS
- [ ] Fichier sauvegarde dans `~/Downloads/` avec nommage standard
- [ ] Tableau recapitulatif des champs remis avec le livrable
