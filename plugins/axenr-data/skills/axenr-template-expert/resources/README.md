# Resources - axenr-template-expert

Ce dossier contient les ressources auxiliaires pour l'agent `axenr-template-expert`.

## Fichiers attendus (cote utilisateur)

Les 3 fichiers de reference sont proprietaires AxENR (contiennent du parametrage client reel). Ils ne sont PAS committes dans le marketplace. L'agent les lit directement depuis les emplacements locaux de l'utilisateur.

### 1. Catalogue des champs dynamiques

Emplacement : fourni par l'utilisateur (ou catalogue vivant Google Sheets du client, a relire a chaque session)

Contenu : 77 champs + 39 techniques, catalogues en 3 feuilles (Champs dynamiques, Fonctions & techniques, Legende).

Mise a jour : a re-exporter depuis la source interne AxENR a chaque evolution majeure du parametrage.

### 2. Template de reference Contrat de maintenance

Emplacement : fourni par l'utilisateur (n'importe quel template Contrat de maintenance en production).

Contenu : exemple avance avec racine Contract, boucles, variables locales, champs custom.

### 3. Export TemplateSettingsLine du client

Emplacement : fourni par l'utilisateur (export frais de l'instance concernee)

Contenu : source de verite absolue sur les champs autorises. Varie d'un client AxENR a l'autre - chaque mission utilise l'export de l'instance concernee.

Mise a jour : re-exporter depuis l'instance Axelor du client via Parametrages > Templates > TemplateSettings > Export.

## Pourquoi pas dans le repo ?

Ces fichiers contiennent :
- Les noms de clients reels
- Les valeurs exemples reelles (SIRET, adresses, etc.)
- Le parametrage technique des instances Axelor des clients

Ils sont consideres comme PROPRIETAIRES AxENR / NDA client. L'agent les lit en lecture seule depuis le disque local de chaque membre de l'equipe AxENR.

## Examples

Le sous-dossier `examples/` contient des transcriptions anonymisees / partielles des templates en production, utiles comme reference pour l'agent. Elles ne contiennent pas le texte metier integral (trop long + copyright client) mais capturent la structure des champs dynamiques.
