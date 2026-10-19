# /axenr-template-expert

Expert senior en templates Word XDocReport pour Axelor / AxENR. Travaille **en lecture seule** sur le projet, produit des .docx complets dans `~/Downloads/`, importables tels quels dans Axelor via Parametrages > Templates.

**Fichier d'entree optionnel.** Beaucoup de demandes se traitent en generation pure depuis les specs + le catalogue. Avec un template .docx existant, l'agent le modifie en preservant la mise en page.

## USAGE

### Creation pure (depuis besoin seul)

```
/axenr-template-expert cree un mandat ENEDIS pour <client>
/axenr-template-expert cree une fiche de collecte avec : nom projet, adresse chantier, SIRET client, puissance kWc
/axenr-template-expert genere un contrat de maintenance type base sur la racine Contract
```

### Modification d'un template existant

```
/axenr-template-expert convertis "SAS EXEMPLE SOLAIRE" en champ dynamique dans ce template | ~/Downloads/contrat-maintenance.docx
/axenr-template-expert ajoute une boucle sur les equipements | ~/Downloads/template-client.docx
/axenr-template-expert dynamise ces zones [SIRET] [adresse siege] [date] | ~/Downloads/mandat.docx
```

### Avec export TemplateSettingsLine client (source de verite)

```
/axenr-template-expert cree un CARD-I BT pour <client> | ~/Downloads/card-i-brut.docx | ~/Downloads/export-templatesettingsline-<client>.xlsx
```

### Debug d'un champ qui revient vide

```
/axenr-template-expert le champ {d.clientPartner.mainAddress.city.fullName} est vide dans mes renditions
```

### Debug sous Carbone (images, boucles)

```
/axenr-template-expert le log dit "Carbone (850ms)" et les photos du rapport d'intervention sortent grises | ~/Downloads/rapport-preventif.docx
/axenr-template-expert la boucle des non-conformites disparait depuis que j'ai ajoute un filtre Groovy
/axenr-template-expert "Cannot store template : InvalidPart" a l'import de mon .docx
```

## PARSING DES ARGUMENTS

Format : `<besoin libre>` [`|` `<chemin-docx>`] [`|` `<chemin-xlsx-TemplateSettingsLine>`]

Le caractere `|` separe les parties. Exemple :

```
/axenr-template-expert convertis ces zones en champs dynamiques | ~/Downloads/mandat.docx | ~/Downloads/export-tsl.xlsx
```

Si un seul chemin est fourni :
- Se termine par `.docx` -> c'est le template a modifier
- Se termine par `.xlsx` -> c'est l'export TemplateSettingsLine (source de verite)

## DETECTION AUTOMATIQUE DU CLIENT

L'agent detecte d'abord le client AxENR a partir du `cwd`, avec le skill `client-context-detector` (table des dossiers client et des ressources). Le client detecte determine :
- Quel export TemplateSettingsLine charger (`~/Downloads/export-tsl-<client>.xlsx` ou equivalent)
- Quel moteur attendre (XDocReport ou Carbone), a confirmer par le log de previsualisation
- Quelles conventions de nommage utiliser pour le livrable (`<Type>_<Client>_V<N>.docx`)

Lance l'agent **depuis le dossier du client** pour beneficier de la detection automatique :

```bash
cd ~/Desktop/Projects/<client>-app
/axenr-template-expert cree un mandat ENEDIS
# -> client detecte automatiquement
# -> livrable : ~/Downloads/Mandat_ENEDIS_<Client>_V1.docx
```

Si tu es ailleurs, l'agent demandera le client explicitement.

## DETECTION AUTOMATIQUE DE LA RACINE

L'agent deduit la racine probable selon les mots-cles du besoin :

| Mot-cle detecte | Racine | Exemple de chemin client |
|-----------------|--------|--------------------------|
| "contrat de maintenance", "contrat cession", "contrat autoconsommation" | Contract | `d.invoicedPartner.name` |
| "fiche de collecte", "mandat ENEDIS", "mandat GEREDIS", "lettre de cession", "changement demandeur", "CARD-I" | Project | `d.clientPartner.name` |
| "attestation unite fonciere", "unite fonciere" | Umr | variable |
| "bon de commande fournisseur" | PurchaseOrder | `d.supplierPartner` |
| Ambigu | - | demander |

## ETAPES

### Etape 1 : Chargement des ressources

L'agent lit obligatoirement au debut de chaque tache :

1. Catalogue des champs dynamiques (xlsx) :
   - Emplacement fourni par l'utilisateur (ou catalogue vivant Google Sheets du client)
   - Si absent : demander a l'utilisateur
2. Export TemplateSettingsLine (xlsx) - si fourni ou trouvable :
   - Export frais de l'instance concernee ; un export ne vaut que pour l'instance dont il provient

### Etape 2 : Deleguer a l'agent

```
subagent_type: axenr-template-expert
prompt: |
  Besoin : <besoin-parse>
  Template source : <chemin .docx ou "aucun">
  Export TemplateSettingsLine : <chemin .xlsx ou defaut catalogue>
  Output dir : ~/Downloads/
  Racine detectee : <Contract | Project | Umr | PurchaseOrder | a-determiner>

  Applique ta methodologie complete (4 etapes).
  Produis un .docx COMPLET pret a l'import Axelor.
  Ne JAMAIS inventer de champ absent du parametrage.
  Format de reponse obligatoire (Resume / Livrable / Champs / Techniques / Vigilance).
```

### Etape 3 : Presenter le livrable

L'agent retourne :

- Chemin absolu du .docx produit (dans `~/Downloads/`)
- Tableau des champs utilises avec source
- Techniques speciales employees
- Points de vigilance (champs manquants a creer cote Axelor)

### Etape 4 : Proposer les suivis

```
Actions disponibles :
1. Lancer une iteration V2 apres test dans Axelor
2. Generer un autre template dans la meme famille
3. Produire le SQL / Groovy des TemplateSettingsLine a creer
4. Exporter en PDF pour revue (via pandoc ou libreoffice)
```

## EXEMPLES DE SORTIES

Voir `resources/examples/` :
- `contrat-maintenance-with-dynamic-fields.md`
- `card-i-enedis-with-dynamic-fields.md`

## GARDE-FOUS (rappel)

- L'agent est READ-ONLY sur `axenr-app` et submodules
- L'agent ne fait JAMAIS de `git commit` / `git push`
- Tous les .docx produits vont dans `~/Downloads/` (ou chemin fourni)
- L'agent ne remplace JAMAIS un champ dynamique par une valeur finale (les templates sont dynamiques par definition)
- L'agent ne modifie JAMAIS la syntaxe d'un champ existant
- L'agent ne melange JAMAIS les chemins entre racines (`d.clientPartner` inexistant sur Contract)
- L'agent NE INVENTE JAMAIS un champ qui n'existe pas dans TemplateSettingsLine
- NO EMOJIS
