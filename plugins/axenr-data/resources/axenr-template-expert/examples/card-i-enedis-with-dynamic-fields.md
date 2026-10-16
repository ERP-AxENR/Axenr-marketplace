# Exemple - CARD-I Enedis (racine Project)

> Transcription partielle d'une fiche CARD-I BT/HTA.
> Illustre la racine `d = Project` avec filtres sur adresses du client.

## Racine

`d = Project`

## Titulaire du contrat

```
Raison Sociale                 : {d.clientPartner.name}
Adresse du siege social        :
  {d.clientPartner.partnerAddressList[isDefaultAddr=true].address.streetName}
  {d.clientPartner.partnerAddressList[isDefaultAddr=true].address.city.fullName}
Pays                           : FRANCE

Forme juridique                : {d.clientPartner.partnerCategory.name}
Capital Social (en euros)      : {d.clientPartner.shareCapital}
Lieu d'immatriculation RCS     : {d.clientPartner.rcsCity.name}
Code NAF                       : {d.clientPartner.mainActivity.code}
SIRET Etablissement principal  : {d.clientPartner.registrationCode}
TVA intracommunautaire         : {d.clientPartner.taxNbr}
```

## Interlocuteur

```
Nom        : {d.clientPartner.mainContactLastName}
Prenom     : {d.clientPartner.mainContactFirstName}
Fonction   : {d.clientPartner.mainContactFunction.name}
Telephone  : {d.clientPartner.fixedPhone}
Email      : {d.clientPartner.emailAddress.address}
```

## Site de production

```
Nom du site de production   : {d.name}
Adresse N / Rue              : {d.customerAddress.streetName}
CP / Commune                 : {d.customerAddress.city.fullName}
Pays                         : FRANCE
SIRET du site                : {d.clientPartner.registrationCode}
  (SIRET etablissement secondaire si localisation differente)
```

## Accord prealable facturation electronique

```
Par le present accord, nous, {d.clientPartner.name} code SIREN {d.clientPartner.siren},
demandons a recevoir des factures electroniques pour l'execution de notre contrat
CARD I n Site de {d.name}.

Fait a {d.customerAddress.streetName} {d.customerAddress.city.fullName},
le {c.now:formatD('L')}

Nom       : {d.clientPartner.mainContactLastName}
Prenom    : {d.clientPartner.mainContactFirstName}
Fonction  : {d.clientPartner.mainContactFunction.name}
```

## Champs utilises

| Nom metier | Forme technique | Source |
|------------|-----------------|--------|
| Raison sociale client | `{d.clientPartner.name}` | Catalogue |
| Rue siege social | `{d.clientPartner.partnerAddressList[isDefaultAddr=true].address.streetName}` | Catalogue (filtre) |
| Ville + CP siege | `{d.clientPartner.partnerAddressList[isDefaultAddr=true].address.city.fullName}` | Catalogue (filtre) |
| Forme juridique | `{d.clientPartner.partnerCategory.name}` | Catalogue |
| Capital social | `{d.clientPartner.shareCapital}` | Catalogue |
| Ville RCS | `{d.clientPartner.rcsCity.name}` | Catalogue |
| Code NAF (APE) | `{d.clientPartner.mainActivity.code}` | Catalogue |
| SIRET | `{d.clientPartner.registrationCode}` | Catalogue |
| SIREN | `{d.clientPartner.siren}` | Catalogue |
| TVA intracommunautaire | `{d.clientPartner.taxNbr}` | Catalogue |
| Nom contact | `{d.clientPartner.mainContactLastName}` | Catalogue |
| Prenom contact | `{d.clientPartner.mainContactFirstName}` | Catalogue |
| Fonction contact | `{d.clientPartner.mainContactFunction.name}` | Catalogue |
| Telephone | `{d.clientPartner.fixedPhone}` | Catalogue |
| Email | `{d.clientPartner.emailAddress.address}` | Catalogue |
| Nom site production | `{d.name}` | Catalogue |
| Rue chantier | `{d.customerAddress.streetName}` | Catalogue |
| Ville + CP chantier | `{d.customerAddress.city.fullName}` | Catalogue |
| Date du jour | `{c.now:formatD('L')}` | Contexte |

## Points de vigilance

- Toutes les references au siege social utilisent le filtre `[isDefaultAddr=true]` - verifier que chaque Partner a bien une partnerAddress avec cette valeur a TRUE
- `{d.customerAddress}` est une reference directe (1 niveau) - OK
- `{d.customerAddress.city.fullName}` est 2 niveaux apres `customerAddress` - OK
- En cas de champ vide sur une chaine 3+ niveaux, creer un champ derive Groovy au niveau Projet (voir skill `template-expert-catalog` section pieges P1)
