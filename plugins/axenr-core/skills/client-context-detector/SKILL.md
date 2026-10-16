---
name: client-context-detector
description: Detecte le client AxENR courant a partir du cwd ou d'un argument. Mappe cwd (ex: systeko-app, planeteenr-app, emeraude-solaire-app) vers le code client et charge les ressources specifiques (TemplateSettingsLine export, conventions de nommage, chemins standards). Utilise par import-export-agent et axenr-template-expert.
---

# Client Context Detector

> Identifie le client AxENR courant pour que les agents adaptent leur comportement (ressources, conventions, outputs).

## POURQUOI

AxENR implemente Axelor pour plusieurs clients (Systeko, Planete, Emeraude Solaire, etc.). Chaque instance a :
- Son propre parametrage TemplateSettingsLine
- Ses propres templates metier
- Ses propres conventions de nommage (codes fournisseur, structure societes)
- Ses propres particularites techniques

Un agent qui ignore le client melange les configs, utilise les mauvais champs, ou livre des outputs non compatibles avec l'instance cible.

## MAPPING cwd -> CLIENT

Convention basee sur la structure locale du poste AxENR :

| cwd contient | Client | Code | Instance Axelor |
|--------------|--------|------|-----------------|
| `axenr-app` | AxENR (equipe interne) | `axenr` | instance dev maison |
| `axenr-mobile` | AxENR Mobile | `axenr-mobile` | - (mobile RN) |
| `emeraude-solaire-app` | Emeraude Solaire | `emeraude` | emeraude.erp-axenr.fr |
| `planeteenr-app` | Planete ENR | `planete` | planete.erp-axenr.fr |
| `systeko-app` | Systeko | `systeko` | systeko.erp-axenr.fr |
| `synambu` | Synambu | `synambu` | synambu.erp-axenr.fr |
| `energ-ia` | Energ-IA | `energia` | energia.erp-axenr.fr |
| `yooz` | Yooz | `yooz` | yooz.erp-axenr.fr |

## INPUTS

| Input | Format |
|-------|--------|
| cwd | Chemin absolu du repertoire courant (auto-detecte par l'agent) |
| client_hint | Optionnel : code client fourni explicitement (ex: `systeko`, `planete`) |

## OUTPUTS

```
{
  "client_code": "systeko",
  "client_name": "Systeko",
  "project_path": "/Users/macbook/Desktop/Projects/systeko-app",
  "project_exists": true,
  "resources": {
    "tsl_export_expected": "/Users/macbook/Downloads/export-templatesettingsline-systeko.xlsx",
    "tsl_export_fallback": "/Users/macbook/Downloads/export-18305243113295820288.xlsx",
    "templates_dir": "/Users/macbook/Desktop/Projects/systeko-app/modules/*/src/main/resources/templates/",
    "data_init_dir": "/Users/macbook/Desktop/Projects/systeko-app/modules/*/src/main/resources/data-init/"
  },
  "conventions": {
    "partner_prefix": "F",
    "account_prefix": "SYS-F",
    "template_naming": "<Type>_Systeko_V<N>.docx"
  },
  "aop_version": "7.4.8",
  "aos_version": "8.4.9"
}
```

## LOGIQUE

```
1. Extraire le dernier segment significatif du cwd :
   /Users/macbook/Desktop/Projects/systeko-app -> "systeko-app"
   /Users/macbook/Desktop/Projects/systeko-app/modules/foo -> remonter jusqu'a trouver un dossier matchant le mapping

2. Si client_hint fourni, il prime sur l'auto-detection cwd

3. Chercher dans la table MAPPING :
   - systeko-app -> systeko
   - planeteenr-app -> planete
   - emeraude-solaire-app -> emeraude
   - axenr-app -> axenr
   - axenr-mobile -> axenr-mobile
   - synambu -> synambu
   - energ-ia -> energia
   - yooz -> yooz

4. Si match :
   - Construire project_path
   - Lister les ressources attendues (conventions)
   - Lire gradle.properties pour aop_version / aos_version
   - Chercher un export TSL avec le nom du client (tsl_export_expected)
   - Fallback : export TSL generique dans ~/Downloads

5. Si pas de match :
   - Retourner client_code=null, demander a l'utilisateur
   - L'agent doit alors demander explicitement "Pour quel client travailles-tu ?"
```

## RESOLUTION DES RESSOURCES CLIENT

Pour chaque client, les chemins attendus sont :

### TemplateSettingsLine export

Ordre de recherche :
1. `~/Desktop/Projects/<client>-app/resources/tsl-export.xlsx` (convention AxENR a mettre en place)
2. `~/Downloads/export-templatesettingsline-<client>.xlsx` (nommage explicite)
3. `~/Downloads/export-tsl-<client>.xlsx` (nommage court)
4. `~/Downloads/export-18305243113295820288.xlsx` (fallback historique Planete/Emeraude)

Si aucun n'est trouve -> demander l'export frais a l'utilisateur.

### Catalogue des champs dynamiques

Partage entre clients (c'est la base de connaissances commune AxENR) :
- `~/Downloads/Champs_dynamiques_templates (2).xlsx`

### Templates existants

Dans le projet client :
- `<project_path>/modules/*/src/main/resources/templates/*.docx`

Permet a l'agent de s'inspirer de templates deja validees.

### Data-init / imports existants

Dans le projet client :
- `<project_path>/modules/*/src/main/resources/data-init/*.csv`

Permet de valider les ordres d'import et les conventions importId.

## CONVENTIONS PAR CLIENT (A COMPLETER AU FIL DU TEMPS)

### Emeraude Solaire (`emeraude`)

- Partner prefix : `F` (fournisseur), `C` (client)
- Account prefix : `EMS-F<7digits>`, `EMS-C<7digits>`
- Parent account fournisseurs : `AXENR0070`
- Societe par defaut : code `101`

### Planete ENR (`planete`)

- Racine SIRET : 522 168 350
- Societe : SAS PLANETE ENR
- Adresse : ZA La Croix, 85700 Menomblet

### Systeko (`systeko`)

- Client recent (parametrage en cours)
- Demarre de zero (peu de templates existants)

### Synambu (`synambu`)

- a documenter

## INTEGRATION AGENTS

Les agents suivants DOIVENT appeler ce skill en PHASE 0 (ou equivalent) avant toute action :
- import-export-agent
- axenr-template-expert
- axenr-bi-architect

```
PHASE 0 : CLIENT DETECTION

1. Appeler client-context-detector avec cwd actuel
2. Si client_code null :
   - Demander explicitement a l'utilisateur :
     "Sur quel client travailles-tu ? (systeko / planete / emeraude / axenr / synambu / energia / yooz / autre)"
   - Ne pas continuer sans reponse
3. Afficher un banner :
   "Client detecte : Systeko (systeko-app)"
   "Ressources :"
   "  - TSL export : <chemin>"
   "  - Template catalog : <chemin>"
   "  - Project path : <chemin>"
4. Si le TSL export est manquant pour ce client :
   - Prevenir : "Je n'ai pas trouve d'export TSL pour Systeko."
   - "Exporte-le depuis <url client> > Parametrages > Templates"
   - "Puis relance avec | <chemin-vers-export>"
5. Charger les conventions client
6. PHASE 1 commence avec ce contexte
```

## QUAND L'UTILISATEUR N'EST PAS DANS UN PROJET CLIENT

Si le cwd est dans `Axenr-marketplace`, `Downloads`, `Desktop` ou autre :
- Pas de detection automatique
- Demander a l'utilisateur explicitement
- Possibilite de forcer via argument `--client=<code>`
