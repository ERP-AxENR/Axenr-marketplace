---
name: error-learner
description: Analyse une erreur, normalise sa signature, delegue a lesson-deduplicator pour eviter les doublons, cree ou incremente la lecon dans LESSONS-LEARNED.md, declenche knowledge-updater si 3+ occurrences.
---

# Error Learner

> Analyse une erreur, delegue au lesson-deduplicator pour matching semantique, cree ou incremente une lecon dans LESSONS-LEARNED.md

## ROLE

Recevoir une erreur (message, fichier, contexte), chercher si un pattern similaire existe deja dans LESSONS-LEARNED.md, et soit incrementer le compteur d'une lecon existante, soit creer une nouvelle lecon.

## INPUTS

| Input | Format |
|-------|--------|
| error_message | Le message d'erreur complet (stacktrace, log, ou issue de validation) |
| error_file | Le fichier ou l'erreur a ete detectee |
| error_source | L'agent ou outil qui a detecte l'erreur (code-reviewer, build, xml-validator, enr-coherence-checker, axenr-dev-validator, etc.) |
| error_rule_id | Optionnel : ID de la regle violee (ENR-AP-01, DOM-01, VIEW-01, JAVA-01, etc.) |
| ticket_number | Le numero du ticket en cours |
| project | axenr-app ou axenr-mobile |
| marketplace_path | Chemin absolu vers le marketplace |

## CIBLE D'ECRITURE (CURATOR MODEL - Option A)

Par defaut, error-learner ecrit dans le fichier LOCAL du poste courant :

```
<marketplace_path>/plugins/axenr-dev/docs/lessons/LOCAL-LESSONS-<hostname>.md
```

Le fichier LOCAL est gitignore. Chaque developpeur accumule ses lecons localement.
La synchronisation vers le fichier partage `LESSONS-LEARNED.md` passe par `/axenr-dev:sync-lessons`
qui ouvre une PR reviewable par le curateur.

Si le fichier LOCAL n'existe pas, le creer avec l'entete :

```markdown
# Local Lessons - <hostname>

> Fichier local, non commite. Accumule les lecons de ce poste uniquement.
> Synchronise vers LESSONS-LEARNED.md via /axenr-dev:sync-lessons.

## LECONS
```

Les IDs locaux sont prefixes : `LESSON-LOCAL-NNN` pour eviter la collision avec les
IDs globaux (`LESSON-NNN`) du fichier partage.

## OUTPUTS

| Output | Format |
|--------|--------|
| lesson_id | LESSON-XXX (nouveau ou existant) |
| is_new | true si nouvelle lecon, false si existante |
| occurrence_count | Nombre total d'occurrences |
| fix_suggestion | La correction suggeree (issue d'une lecon existante ou a determiner) |

## LOGIQUE

```
0. RESOUDRE les chemins :
   local_file = <marketplace_path>/plugins/axenr-dev/docs/lessons/LOCAL-LESSONS-<hostname>.md
   shared_file = <marketplace_path>/plugins/axenr-dev/docs/lessons/LESSONS-LEARNED.md
   Creer local_file s'il n'existe pas.

1. NORMALISER l'erreur -> signature structuree :
   - Retirer chemins de fichiers absolus (garder le nom de fichier)
   - Retirer numeros de ligne (LINE 42 -> LINE N)
   - Remplacer noms d'entites du ticket par <ENTITY>
   - Remplacer noms de champs specifiques par <FIELD>
   - Retirer numeros de ticket
   - Normaliser casse et espaces

2. DELEGUER au skill lesson-deduplicator CONTRE LES DEUX fichiers :
   Inputs: error_signature, rule_id, type, source, project,
           lessons_files: [local_file, shared_file]
   Output: decision (increment | new | review), match_id, match_scope (local|shared),
           similarity_score

3. APPLIQUER la decision (ecriture TOUJOURS dans local_file) :

   SI decision == increment ET match_scope == local :
     - Incrementer Occurrences dans local_file
     - Ajouter le ticket dans la liste Tickets (union)
     - Mettre a jour Date

   SI decision == increment ET match_scope == shared :
     - Ne PAS toucher shared_file directement
     - Creer/incrementer une entree "mirror" dans local_file qui pointe vers le match :
       LESSON-LOCAL-NNN (mirror of LESSON-NNN, shared_occurrences+M)
     - /axenr-dev:sync-lessons propagera l'incrementation au shared

   SI decision == review :
     - Ecrire en section REVIEW QUEUE de local_file
       avec top-3 candidates et statut=pending
     - Retourner pointeur vers REVIEW-LOCAL-YYY

   SI decision == new :
     - Generer un nouveau LESSON-LOCAL-NNN (compteur specifique au local_file)
     - Remplir tous les champs obligatoires
     - Ecrire dans local_file

4. NE PAS declencher knowledge-updater ici.
   La promotion est deferee jusqu'a /axenr-dev:sync-lessons : si apres merge une lecon
   atteint 3 occurrences dans shared_file, le hook post-merge ou la prochaine
   /axenr-dev:consolidate-lessons declenche knowledge-updater.

5. Retourner lesson_id (LESSON-LOCAL-NNN), scope=local, fix suggere.
```

## FORMAT D'UNE LECON

```markdown
### LESSON-XXX : titre court et descriptif
- **Date** : YYYY-MM-DD
- **Projet** : axenr-app | axenr-mobile
- **Ticket** : #750, #760
- **Type** : domain | view | action | java | mobile | build | version | naming | i18n | rest | migration | enr
- **Source** : code-reviewer | code-analyzer | xml-validator | build | enr-coherence-checker | axenr-dev-validator | etc.
- **Rule ID** : ENR-AP-01 | DOM-01 | VIEW-01 | JAVA-01 | etc. (optionnel, lie a la regle du skill)
- **Erreur** : description exacte de ce qui a echoue
- **Symptome** : le message d'erreur ou le comportement observe
- **Cause** : pourquoi ca a echoue
- **Fix** : ce qui a ete fait pour corriger
- **Regle** : la regle generale a retenir
- **Occurrences** : 1
- **Promu** : false
```

## MAPPING SOURCE → TYPE

Quand l'erreur vient d'un skill de validation AxENR, utiliser ce mapping :

| Source | Rule ID prefix | Type |
|--------|---------------|------|
| enr-coherence-checker | ENR-AP-* | enr |
| axenr-dev-validator | DOM-* | domain |
| axenr-dev-validator | VIEW-* | view |
| axenr-dev-validator | ACT-* | action |
| axenr-dev-validator | JAVA-* | java |
| axenr-dev-validator | I18N-* | i18n |
| axenr-dev-validator | EXT-* | naming |
| axenr-dev-validator | GIT-* | build |

## BOUCLE DE RENFORCEMENT (BIDIRECTIONNELLE)

```
Les skills de validation (enr-coherence-checker, axenr-dev-validator) LISENT
les lecons avant de valider → les lecons avec 2+ occurrences renforcent
la severite des regles.

Quand une violation est detectee, error-learner ECRIT une nouvelle lecon
ou incremente une existante.

Au prochain run, le skill RELIT les lecons et la regle renforcee est
encore plus stricte.

RESULTAT : Les erreurs repetees deviennent de plus en plus difficiles
a ignorer, jusqu'a promotion automatique dans CLAUDE.md.
```

## EXEMPLES

### Input : erreur de validation XML

```
error_message: "CRITICAL: missing form-view on relational field 'partner'"
error_file: "modules/axenr/src/main/resources/views/opportunity-views.xml"
error_source: "code-reviewer"
ticket_number: "#750"
project: "axenr-app"
```

### Output : nouvelle lecon

```
lesson_id: "LESSON-013"
is_new: true
occurrence_count: 1
fix_suggestion: "Add form-view='partner-form' grid-view='partner-grid' to the field"
```

### Input : erreur deja connue

```
error_message: "CRITICAL: @Transactional missing on method with save()"
error_source: "code-reviewer"
ticket_number: "#760"
```

### Output : lecon existante incrementee

```
lesson_id: "LESSON-010"
is_new: false
occurrence_count: 3
fix_suggestion: "Add @Transactional(rollbackOn = {Exception.class}) to the method"
```
