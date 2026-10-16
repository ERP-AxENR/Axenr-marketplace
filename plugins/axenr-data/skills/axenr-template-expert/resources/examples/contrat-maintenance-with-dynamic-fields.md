# Exemple - Contrat de maintenance (racine Contract)

> Transcription partielle du template Planete ENR en production.
> Illustre la racine `d = Contract`, les boucles, les variables locales, les champs custom.

## Racine

`d = Contract`

## En-tete

```
Contrat n° : {d.contractId}

ENTRE :

Le PRESTATAIRE : MAINTENANCE ENR SAS, ... (texte fixe)

ET

Le CLIENT : {d.invoicedPartner.name},
au capital de {d.invoicedPartner.shareCapital} euros,
dont le siege social est
{d.invoicedPartner.partnerAddressList[isDefaultAddr=true].address.streetName}
{d.invoicedPartner.partnerAddressList[isDefaultAddr=true].address.city.fullName},
immatriculee sous le numero {d.invoicedPartner.registrationCode},
representee par M. {d.invoicedPartner.mainContactLastName} {d.invoicedPartner.mainContactFirstName},
en sa qualite de gerant.
```

## Caracteristiques installation

```
Puissance crete installee totale : {d.string155} kWc
Surface                          : {d.integer154} m2
```

Note : `string155` et `integer154` sont des champs custom Axelor (meta-fields).

## Boucle sur equipements avec variable locale

```
Liste des installations :

- {d.relatedEquipmentList[i].name} {#eq = d.relatedEquipmentList[i]}
  Onduleurs : {$eq.integer29} * {$eq.manyToOne28.name}
  Date de mise en service : {$eq.commissioningDate:formatD('L')}
  Puissance crete : {$eq.kwcPower} kWc
  Puissance : {$eq.kvaPower} kVa
  Adresse du site de production : {$eq.parentEquipment.name}
- {d.relatedEquipmentList[i+1].name}
```

Points :
- `{#eq = d.relatedEquipmentList[i]}` declare la variable locale pointant sur l'element courant
- Les acces suivants utilisent `{$eq.champ}` au lieu de repeter le chemin complet
- `{d.relatedEquipmentList[i+1].name}` est la balise de fin de boucle

## Boucle sur lignes de contrat (tableau)

```
| Prestations                                                               | Cout HT                                                               | Periodicite                                                               |
| {d.currentContractVersion.contractLineList[i].productName}                | {d.currentContractVersion.contractLineList[i].exTaxTotal} EUR HT      | {d.currentContractVersion.contractLineList[i].periodicity.name}           |
| {d.currentContractVersion.contractLineList[i+1].productName}              | {d.currentContractVersion.contractLineList[i+1].exTaxTotal} EUR HT    | {d.currentContractVersion.contractLineList[i+1].periodicity.name}         |

Total HT (Annuel) : {d.currentContractVersion.yearlyExTaxTotalRevalued} EUR HT
```

Points :
- Tableau Word 2 lignes avec `[i]` sur la 1ere et `[i+1]` sur la 2eme
- XDocReport repete la 1ere ligne pour chaque `contractLineList`

## Date de signature

```
Fait en deux exemplaires : a ANTIGNY, le {c.now:formatD('L')},
```

Le `c.now` avec format localise `'L'` produit par exemple "17 avril 2026".

## Champs utilises dans cet exemple

| Nom metier | Forme technique | Source |
|------------|-----------------|--------|
| Identifiant contrat | `{d.contractId}` | Catalogue |
| Nom partenaire facture | `{d.invoicedPartner.name}` | Catalogue |
| Capital social facture | `{d.invoicedPartner.shareCapital}` | Catalogue |
| SIRET partenaire facture | `{d.invoicedPartner.registrationCode}` | Catalogue |
| Nom contact facture | `{d.invoicedPartner.mainContactLastName}` | Catalogue |
| Prenom contact facture | `{d.invoicedPartner.mainContactFirstName}` | Catalogue |
| Rue siege facture | `{d.invoicedPartner.partnerAddressList[isDefaultAddr=true].address.streetName}` | Catalogue (filtre) |
| Ville + CP siege facture | `{d.invoicedPartner.partnerAddressList[isDefaultAddr=true].address.city.fullName}` | Catalogue (filtre) |
| Puissance crete totale (kWc) | `{d.string155}` | Custom field `string155` |
| Surface totale (m2) | `{d.integer154}` | Custom field `integer154` |
| Liste equipements | `{d.relatedEquipmentList[i].name} ... [i+1]` | Boucle |
| Variable locale equipement | `{#eq = d.relatedEquipmentList[i]}` puis `{$eq.X}` | Variable locale |
| Nombre onduleurs equipement | `{$eq.integer29}` | Custom equipment |
| Produit lie equipement | `{$eq.manyToOne28.name}` | Custom M2O |
| Date mise en service equipement | `{$eq.commissioningDate:formatD('L')}` | Date + format |
| kWc equipement | `{$eq.kwcPower}` | Catalogue |
| kVA equipement | `{$eq.kvaPower}` | Catalogue |
| Site equipement | `{$eq.parentEquipment.name}` | Catalogue |
| Ligne contrat - produit | `{d.currentContractVersion.contractLineList[i].productName}` | Boucle |
| Ligne contrat - montant HT | `{d.currentContractVersion.contractLineList[i].exTaxTotal}` | Boucle |
| Ligne contrat - periodicite | `{d.currentContractVersion.contractLineList[i].periodicity.name}` | Boucle |
| Total HT annuel revise | `{d.currentContractVersion.yearlyExTaxTotalRevalued}` | Catalogue |
| Date du jour | `{c.now:formatD('L')}` | Contexte |
