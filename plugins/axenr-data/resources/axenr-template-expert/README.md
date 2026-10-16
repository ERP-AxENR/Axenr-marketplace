# Resources - axenr-template-expert

Ce dossier contient les ressources auxiliaires pour l'agent `axenr-template-expert`.

## Fichiers attendus (cote utilisateur)

Les 3 fichiers de reference sont proprietaires AxENR (contiennent du parametrage client reel). Ils ne sont PAS committes dans le marketplace. L'agent les lit directement depuis les emplacements locaux de l'utilisateur.

### 1. Catalogue des champs dynamiques

Chemin par defaut : `/Users/macbook/Downloads/Champs_dynamiques_templates (2).xlsx`

Contenu : 77 champs + 39 techniques, catalogues en 3 feuilles (Champs dynamiques, Fonctions & techniques, Legende).

Mise a jour : a re-exporter depuis la source interne AxENR a chaque evolution majeure du parametrage.

### 2. Template de reference Contrat de maintenance

Chemin par defaut : `/Users/macbook/Downloads/f1ce984f6635a4e9d046b4f89566c992fec7088d324566fe7de44adc5d554bde (1).docx`

Ou n'importe quel template Contrat de maintenance en production (ex: Planete M26-015).

Contenu : exemple avance avec racine Contract, boucles, variables locales, champs custom.

### 3. Export TemplateSettingsLine du client

Chemin par defaut : `/Users/macbook/Downloads/export-18305243113295820288.xlsx`

Contenu : source de verite absolue sur les champs autorises. Varie d'un client AxENR a l'autre (Systeko, Planete, Emeraude Solaire) - chaque mission peut utiliser son propre export.

Mise a jour : re-exporter depuis l'instance Axelor du client via Parametrages > Templates > TemplateSettings > Export.

## Pourquoi pas dans le repo ?

Ces fichiers contiennent :
- Les noms de clients reels
- Les valeurs exemples reelles (SIRET, adresses, etc.)
- Le parametrage technique des instances Axelor des clients

Ils sont consideres comme PROPRIETAIRES AxENR / NDA client. L'agent les lit en lecture seule depuis le disque local de chaque membre de l'equipe AxENR.

## Examples

Le sous-dossier `examples/` contient des transcriptions anonymisees / partielles des templates en production, utiles comme reference pour l'agent. Elles ne contiennent pas le texte metier integral (trop long + copyright client) mais capturent la structure des champs dynamiques.
