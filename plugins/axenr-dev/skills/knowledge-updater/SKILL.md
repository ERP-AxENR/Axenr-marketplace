---
name: knowledge-updater
description: Promeut automatiquement les lecons confirmees (3+ occurrences) dans CLAUDE.md du marketplace. Verifie les doublons et conflits avec les regles existantes avant insertion.
---

# Knowledge Updater

> Promeut automatiquement les lecons confirmees (3+ occurrences) dans le CLAUDE.md du marketplace

## ROLE

Verifier si une lecon dans LESSONS-LEARNED.md a atteint le seuil de promotion (3 occurrences). Si oui, formater la lecon en regle permanente et l'inserer dans le CLAUDE.md du marketplace, sans creer de doublon et sans contredire les regles existantes.

## INPUTS

| Input | Format |
|-------|--------|
| lesson_id | LESSON-XXX a verifier |
| occurrence_count | Nombre actuel d'occurrences |
| lessons_file_path | Chemin absolu vers LESSONS-LEARNED.md |
| claude_md_path | Chemin absolu vers CLAUDE.md du marketplace |

## OUTPUTS

| Output | Format |
|--------|--------|
| promoted | true si la lecon a ete promue, false sinon |
| reason | Pourquoi promue ou pas (seuil, doublon, conflit) |

## LOGIQUE

```
1. Verifier que occurrence_count >= 3
   SI NON → retourner promoted=false, reason="threshold not reached"

2. Lire LESSONS-LEARNED.md → extraire la lecon LESSON-XXX

3. Lire CLAUDE.md du marketplace

4. Verifier qu'une regle equivalente n'existe pas deja dans CLAUDE.md :
   - Comparer le type d'erreur
   - Comparer la regle
   SI DOUBLON → marquer la lecon comme "promu=true" dans LESSONS-LEARNED.md
              → retourner promoted=false, reason="already exists in CLAUDE.md"

5. Verifier que la nouvelle regle ne contredit pas une regle existante :
   SI CONFLIT → retourner promoted=false, reason="conflicts with existing rule"

6. Formater la lecon en regle CLAUDE.md :

   ```markdown
   ### <Type> : <titre de la lecon>
   - Erreur : <description>
   - Correction : <fix>
   - Source : auto-learning (LESSON-XXX, <N> occurrences)
   ```

7. Inserer dans la bonne section de CLAUDE.md :
   - Type domain → section "ERREURS DOMAINS"
   - Type view → section "ERREURS VIEWS"
   - Type java → section "ERREURS JAVA"
   - Type mobile → section "ERREURS MOBILE"
   - Type build → section "ERREURS BUILD"
   - Type version → section "ERREURS VERSION"

8. Marquer la lecon comme "promu=true" dans LESSONS-LEARNED.md

9. Retourner promoted=true
```

## EXEMPLES

### Promotion reussie

```
Input:
  lesson_id: LESSON-010
  occurrence_count: 3

Output:
  promoted: true
  reason: "Promoted to CLAUDE.md section ERREURS JAVA"

CLAUDE.md recoit :
  ### Java : @Transactional obligatoire sur les methodes avec save()
  - Erreur : methode qui appelle repo.save() sans @Transactional
  - Correction : ajouter @Transactional(rollbackOn = {Exception.class})
  - Source : auto-learning (LESSON-010, 3 occurrences)
```

### Promotion refusee (doublon)

```
Input:
  lesson_id: LESSON-015
  occurrence_count: 3

Output:
  promoted: false
  reason: "already exists in CLAUDE.md: rule about form-view on relational fields"
```
