---
name: lesson-deduplicator
description: Semantic dedup for LESSONS-LEARNED.md. Matches a new error pattern against existing lessons using rule_id, type, signature and fuzzy pattern matching. Returns match_id or no_match so error-learner can increment instead of duplicating.
---

# Lesson Deduplicator

> Evite l'explosion de lecons dupliquees. Appele par error-learner AVANT toute ecriture.

## POURQUOI

Le loop d'auto-apprentissage etait casse : 55 lecons, toutes a 1 occurrence, 0% promues. Cause : error-learner comparait trop strictement (texte exact d'erreur) au lieu du PATTERN. Chaque ticket creait une nouvelle lecon meme pour une erreur deja vue.

## ROLE

Prendre une signature d'erreur normalisee, la matcher contre LESSONS-LEARNED.md par score de similarite multi-axes, retourner une decision.

## INPUTS

| Input | Format |
|-------|--------|
| error_signature | Signature normalisee produite par error-learner (voir section NORMALISATION) |
| rule_id | ID de regle si dispo (ENR-AP-01, DOM-01, VIEW-01, JAVA-01, etc.) |
| type | domain / view / action / java / mobile / build / version / naming / i18n / rest / migration / enr |
| source | Agent/outil ayant detecte (code-reviewer, xml-validator, enr-coherence-checker, axenr-dev-validator, build) |
| project | axenr-app / axenr-mobile / both |
| lessons_files | Liste de chemins a scanner. Typiquement [LOCAL-LESSONS-<hostname>.md, LESSONS-LEARNED.md]. Le dedup se fait sur l'UNION des deux fichiers en priorisant le LOCAL pour l'incrementation. |

## OUTPUTS

| Output | Format |
|--------|--------|
| decision | `increment` / `new` / `review` |
| match_id | LESSON-XXX si decision=increment ou review, null sinon |
| match_scope | `local` / `shared` - indique dans quel fichier le match a ete trouve |
| similarity_score | 0.0 a 1.0 |
| match_reason | Axe de match (rule_id / signature / fuzzy) |
| candidates | Liste top-3 si decision=review (score>=0.6 mais <0.85) |

## NORMALISATION DE SIGNATURE

Avant match, l'error-learner doit produire une signature en appliquant :

```
1. Retirer chemins de fichiers absolus (garder le nom de fichier)
2. Retirer numeros de ligne (LINE 42 -> LINE N)
3. Retirer noms d'entites specifiques au ticket (Opportunity, SaleOrder, etc.)
   -> remplacer par <ENTITY>
4. Retirer noms de champs specifiques (isProjectNotMandatory, grid_power_kva)
   -> remplacer par <FIELD>
5. Retirer numeros de ticket (#750, #761)
6. Normaliser casse et espaces
```

## SCORING MULTI-AXES

Score = max des axes suivants :

| Axe | Poids | Condition |
|-----|-------|-----------|
| rule_id exact | 1.00 | Meme ENR-AP-01 ou DOM-01 etc. |
| type + source + signature exacte | 0.95 | Apres normalisation |
| type + signature fuzzy (Levenshtein ratio >= 0.85) | 0.85 | |
| type + keywords communs (>= 3 mots-cles significatifs) | 0.75 | |
| type seul + source | 0.40 | (trop faible, ne match pas) |

## DECISIONS

```
score >= 0.85 -> decision=increment (incremente la lecon matchee)
0.60 <= score < 0.85 -> decision=review (retourne top-3, laisse l'humain trancher)
score < 0.60 -> decision=new (nouvelle lecon)
```

## LOGIQUE

```
1. Parser LESSONS-LEARNED.md : extraire tous les blocs LESSON-XXX avec leurs champs
   (Type, Rule ID, Source, Erreur, Regle, Occurrences)

2. Construire la signature normalisee de l'erreur recue

3. Pour chaque lecon existante du MEME type :
   a) Si rule_id match exactement -> score = 1.00, stop
   b) Sinon, normaliser la lecon existante et comparer signature
   c) Calculer Levenshtein ratio sur Erreur + Regle concatenees
   d) Calculer overlap de keywords (minuscule, stopwords retires, longueur >= 4)

4. Retourner la meilleure lecon + son score + decision

5. Si decision=review, retourner aussi top-3 candidates pour que l'humain
   ou l'agent puisse trancher via /axenr-dev:consolidate-lessons
```

## EXEMPLES

### Match exact par rule_id

```
Input:
  rule_id: DOM-03
  type: domain
  signature: "boolean field without default attribute"

Output:
  decision: increment
  match_id: LESSON-004
  similarity_score: 1.00
  match_reason: "rule_id exact: DOM-03"
```

### Match fuzzy sur signature

```
Input:
  type: java
  signature: "missing @Transactional on method calling save"

Output:
  decision: increment
  match_id: LESSON-010
  similarity_score: 0.91
  match_reason: "signature fuzzy: 0.91 Levenshtein ratio"
```

### Ambigu -> review

```
Input:
  type: view
  signature: "field without form-view attribute"

Output:
  decision: review
  candidates:
    - LESSON-013 (0.72) : "form-view missing on relational field"
    - LESSON-017 (0.68) : "grid-view missing on many-to-one"
    - LESSON-022 (0.61) : "default views absent on relationnel"
  match_reason: "multiple similar lessons, human review recommended"
```

## INTEGRATION AVEC error-learner

L'error-learner doit desormais :

```
1. Normaliser l'erreur -> signature
2. APPELER lesson-deduplicator avec signature + metadata
3. Selon decision :
   - increment : incrementer Occurrences et Tickets de match_id
   - review : logger dans LESSONS-LEARNED.md section REVIEW-QUEUE
     (human via /axenr-dev:consolidate-lessons tranche plus tard)
   - new : creer LESSON-NNN
4. Si Occurrences >= 3 apres incrementation, appeler knowledge-updater
```

## REVIEW QUEUE

Format dans LESSONS-LEARNED.md :

```markdown
## REVIEW QUEUE

### REVIEW-001 : <signature normalisee>
- **Date** : YYYY-MM-DD
- **Ticket** : #NNN
- **Candidates** :
  - LESSON-013 (0.72)
  - LESSON-017 (0.68)
- **Statut** : pending
```

La commande `/axenr-dev:consolidate-lessons` depile cette queue.
