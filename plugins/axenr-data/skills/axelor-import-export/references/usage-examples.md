# /axelor-import-export

Assistant expert operations sur la donnee Axelor. Travaille **en lecture seule** sur le projet (`axenr-app` ou autre), produit des livrables dans `~/Downloads/`.

**Le fichier n'est pas obligatoire.** Beaucoup de besoins se traitent en pur conseil / methodologie / generation depuis zero. L'agent s'adapte : avec fichier il prepare / corrige / modifie, sans fichier il conseille / genere un modele.

## USAGE

### Sans fichier (mode conseil / advice)

```
/axelor-import-export quels sont les pieges quand on importe des Partner ?
/axelor-import-export comment boucler sur les equipements d'un contrat en XDocReport ?
/axelor-import-export genere-moi un modele vierge de Mandat ENEDIS
/axelor-import-export ordre d'import pour fournisseurs complets
```

### Avec fichier (preparation, modification, debug)

```
/axelor-import-export prepare un import fournisseurs | /Users/macbook/Downloads/donnees-brutes.xlsx
/axelor-import-export convertis "Emeraude Solaire" en champ dynamique | /Users/macbook/Downloads/mandat.docx
/axelor-import-export mon import echoue avec Column not found | /tmp/error.log
```

### Mode debug

```
/axelor-import-export mon import echoue avec "Column not found: partner.importId" | /tmp/error.log
```

### Mode CORE MODEL

```
/axelor-import-export duplique la config comptable de societe 101 vers societe 102 | /Users/macbook/Downloads/databackup-101/
```

## DETECTION AUTOMATIQUE DU CLIENT

L'agent detecte le client AxENR depuis le `cwd` pour adapter ses conventions (codes, codes societe, imports existants, versions AOP/AOS) :

| cwd | Client detecte |
|-----|----------------|
| `~/Desktop/Projects/axenr-app` | AxENR (interne) |
| `~/Desktop/Projects/systeko-app` | Systeko |
| `~/Desktop/Projects/planeteenr-app` | Planete ENR |
| `~/Desktop/Projects/emeraude-solaire-app` | Emeraude Solaire |
| `~/Desktop/Projects/synambu` | Synambu |
| `~/Desktop/Projects/energ-ia` | Energ-IA |
| `~/Desktop/Projects/yooz` | Yooz |
| `~/Desktop/Projects/axenr-mobile` | AxENR Mobile (RN) |
| Autre | Demandera explicitement |

Lance la commande depuis le dossier du client pour beneficier de la detection automatique :

```bash
cd ~/Desktop/Projects/systeko-app
/axelor-import-export prepare un import fournisseurs pour la societe principale
# -> client = Systeko detecte
# -> conventions Systeko appliquees (prefixes, societe)
```

## PARSING DES ARGUMENTS

Format : `<besoin libre en francais> [| <chemin-fichier-optionnel>]`

Le caractere `|` separe le besoin du chemin de fichier.

Detection du mode automatique :
- `fournisseur / client / partenaire / article` -> MODE PREPARE
- `CORE MODEL / duplication societe / plan comptable / databackup` -> MODE CORE-MODEL
- `creer societe / nouvelle societe / societe 10X` (sans databackup) -> MODE COMPANY-CREATE
- `erreur / echec / echoue / Column not found / Record not found` -> MODE DEBUG
- Ambigu -> l'agent demande

## ETAPES

### Etape 1 : Resoudre le contexte projet

```
Detecter cwd.
Si cwd contient "axenr-app" ou "axenr-mobile" -> project_path = cwd
Sinon -> demander confirmation a l'utilisateur
```

### Etape 2 : Parser le fichier si fourni

```bash
# Si le chemin pointe sur un Excel : lister onglets via openpyxl
# Si le chemin pointe sur un CSV : afficher header + 3 premieres lignes
# Si le chemin pointe sur un dossier : lister les CSV dedans
```

### Etape 3 : Deleguer a l'agent

```
subagent_type: axelor-import-export
prompt: |
  Besoin : <besoin-parse>
  Fichier : <chemin ou "aucun">
  Project path : <detecte>
  Output dir : ~/Downloads/
  Mode hint : <detecte ou "auto">

  Applique ton workflow (PHASE 1 -> 5).
  RAPPEL : READ-ONLY sur le projet. Tous les livrables vont dans ~/Downloads/.
```

### Etape 4 : Presenter les livrables

L'agent retourne :
- Chemin du ou des fichiers produits
- Checklist markdown de verification
- Prochaines etapes recommandees

Afficher en clair + proposer les suivis :
```
Actions disponibles :
1. Lancer une iteration V2 si retour de l'utilisateur
2. Passer en MODE DEBUG apres execution dans Axelor
3. Preparer le fichier suivant dans le workflow multi-import
```

## EXEMPLES

### Exemple 1 : import fournisseurs simple

```
/axelor-import-export prepare un import des 150 fournisseurs du fichier ci-joint pour la societe 102 | /Users/macbook/Downloads/fournisseurs-bruts.xlsx
```

L'agent :
1. Detecte project_path = axenr-app
2. Parse fournisseurs-bruts.xlsx -> 150 lignes, 8 colonnes
3. Charge le catalogue references/catalog.md (10 feuilles fournisseurs)
4. Propose un mapping colonnes source -> colonnes Axelor
5. Attend validation
6. Genere `~/Downloads/Import_Fournisseurs_V1.xlsx` (10 onglets) + `CHECKLIST-Fournisseurs.md`

### Exemple 2 : CORE MODEL

```
/axelor-import-export duplique la config comptable 101 vers 102 | /Users/macbook/Downloads/databackup-101/
```

L'agent :
1. Valide la presence des 9 CSV requis dans le dossier
2. Applique les mappings AccountType numerique -> FRA_PCG
3. Transforme les `_importId` -> `_code` via les CSV de reference
4. Produit `~/Downloads/core-model-101-to-102.zip` (10 fichiers) + `CHECKLIST-CORE-MODEL.md`
5. Rappelle que les comptes C000/F000 + AccountingSituation sont a importer separement

### Exemple 3 : debug

```
/axelor-import-export import refuse avec "Record not found for partner.importId=F0042"
```

L'agent :
1. Demande le fichier concerne
2. Verifie si F0042 existe dans l'onglet Partner
3. Verifie l'ordre d'import applique
4. Propose la correction (re-ordonner les imports, ou ajouter la ligne manquante)

## GARDE-FOUS (rappel)

- L'agent ne modifie JAMAIS un fichier du projet axenr-app
- L'agent ne fait JAMAIS de git commit / push
- Tous les outputs vont dans `~/Downloads/` ou `/tmp/axenr-import/` ou le chemin fourni
- L'agent valide AVANT de generer (confirmation utilisateur)
- Sauvegarde fortement recommandee avant import en base
