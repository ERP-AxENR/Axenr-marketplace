# Local Lessons - TEMPLATE

> Template pour les fichiers LOCAL-LESSONS-<hostname>.md.
> Chaque poste a son propre fichier qui suit ce format.
> Ce fichier-ci (LOCAL-LESSONS.template.md) est COMMITE a titre de reference.
> Les LOCAL-LESSONS-<hostname>.md reels sont gitignore.

## INFO

- Hostname : <sera rempli automatiquement par error-learner>
- Premiere lecon : <date>
- Derniere sync vers LESSONS-LEARNED.md : <date>

## STATS LOCAL

| Metrique | Valeur |
|----------|--------|
| Total lecons locales | 0 |
| En attente de sync | 0 |
| Mirror shared | 0 |

## LECONS

### LESSON-LOCAL-001 : exemple titre court
- **Date** : YYYY-MM-DD
- **Projet** : axenr-app | axenr-mobile
- **Ticket** : #NNN
- **Type** : domain | view | action | java | mobile | build | version | naming | i18n | rest | migration | enr
- **Source** : code-reviewer | axenr-dev-validator | enr-coherence-checker | build | etc.
- **Rule ID** : DOM-01 | VIEW-01 | JAVA-01 | ENR-AP-01 | etc.
- **Scope** : local
- **Erreur** : description du probleme
- **Symptome** : message d'erreur observe
- **Cause** : pourquoi ca a echoue
- **Fix** : correction appliquee
- **Regle** : regle generale a retenir
- **Occurrences** : 1
- **Mirror-of** : null | LESSON-NNN (si c'est une incrementation d'une lecon partagee)

## REVIEW QUEUE

(vide par defaut - populee par error-learner quand lesson-deduplicator retourne decision=review)

### REVIEW-LOCAL-001 : exemple
- **Date** : YYYY-MM-DD
- **Ticket** : #NNN
- **Signature** : signature normalisee
- **Candidates** :
  - LESSON-NNN (0.72 shared)
  - LESSON-LOCAL-NNN (0.68 local)
- **Statut** : pending
