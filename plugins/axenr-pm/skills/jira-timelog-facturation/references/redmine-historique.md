# Historique Redmine : temps passés vers facturation

Pour une période antérieure à la bascule vers Jira (juillet 2026) ou un client encore
sur Redmine. Redmine porte nativement l'auteur réel de chaque saisie. Les TJM ne sont
pas dans ce skill : ils viennent du Projet client ou de l'utilisateur.

## Entrées

### `issues.csv` : postes budgétaires parents

| Colonne | Rôle |
|---|---|
| `#` | Numéro du ticket parent |
| `Sujet` | Libellé du poste, avec son préfixe (`[REGIE]`, `[FORFAIT]`, `[MAI]`…) |
| `Temps estimé total` | Budget en heures (optionnel, pour le % consommé) |
| `Temps passé total` | Total Redmine, pour le contrôle de cohérence |

L'utilisateur précise les postes à facturer.

### `timelog.csv` : saisies de temps

| Colonne | Rôle |
|---|---|
| `Date` | `DD/MM/YYYY` |
| `Auteur` | Collaborateur |
| `Demande` | Ticket de la saisie (ex. `Module #922: [REGIE] - …`) |
| `Tracker` | Type de ticket |
| `Tâche parente` | **Clé de rattachement** quand le temps est sur un sous-ticket |
| `Commentaire` | Activité |
| `Heures` | Virgule décimale (`1,50`) |

Séparateur `;`, encodage UTF-8 avec BOM possible (`utf-8-sig`).

## Rattachement aux postes

```
Pour chaque saisie :
  1. numéro du ticket de « Demande » (regex #\d+)
  2. s'il est dans les postes à facturer → rattachement direct
  3. sinon, numéro de « Tâche parente » : s'il est dans les postes → rattachement par sous-ticket
  4. sinon → hors périmètre (compté et signalé en note, jamais retiré en silence)
```

```python
import re

def parse_heures(val):
    return float(val.replace(',', '.')) if val else 0.0

def extract_ticket_id(champ):
    m = re.search(r'#(\d+)', champ or '')
    return int(m.group(1)) if m else None

def rattacher(rows, postes):  # postes : {id: libellé}
    ok, hors = [], []
    for r in rows:
        pid = r['ticket_id'] if r['ticket_id'] in postes else (
              r['parent_id'] if r['parent_id'] in postes else None)
        (ok if pid else hors).append({**r, 'poste_id': pid})
    return ok, hors
```

## TJM par ligne

Le TJM combine le **profil du collaborateur** et le **type de poste** (régie, forfait,
formation). La grille et la liste des profils sont fournies par l'utilisateur au
lancement. Collaborateur sans profil connu : demander avant de calculer.

## Contrôle de cohérence

Pour chaque poste : somme des heures rattachées comparée au `Temps passé total` de
`issues.csv`. Un écart supérieur à 0,01 h signale des saisies manquantes ou en double.

## Sortie

Mêmes règles que le bordereau Jira : analyse textuelle d'abord ; XLSX sur demande,
formules Excel pour les jours (`=E/7`) et les montants, sous-totaux par poste, total
général, note de bas de page pour les heures hors périmètre, charte `axenr-brand`.
Postes `[MAI]` (maintenance non facturée) : toujours hors périmètre.
