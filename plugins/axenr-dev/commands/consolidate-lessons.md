---
description: Consolide les lecons LESSONS-LEARNED.md : detecte les doublons semantiques, fusionne, depile la REVIEW QUEUE, declenche les promotions.
argument-hint: [--auto] [--dry-run]
---

# /axenr-dev:consolidate-lessons

> `<marketplace_path>` : clone de travail de la marketplace (depot git dont l'origin est
> `ERP-AxENR/Axenr-marketplace`), par exemple `/Users/macbook/Desktop/Projects/Axenr-marketplace`.
> Jamais la copie d'installation `~/.claude/plugins/marketplaces/...`. Si introuvable, demander le chemin.

Nettoie la base de lecons : fusionne les doublons accumules avant l'arrivee de lesson-deduplicator, depile la REVIEW QUEUE, promeut les lecons qui atteignent 3 occurrences apres fusion.

## POURQUOI

Quand ce skill est execute pour la premiere fois, il est typique d'avoir des dizaines de lecons semantiquement identiques mais a 1 occurrence chacune (cas actuel : 55 lecons toutes a 1, 0% promu).

## ETAPES

### Etape 1 : Lire LESSONS-LEARNED.md

Chemin : `<marketplace_path>/plugins/axenr-dev/docs/lessons/LESSONS-LEARNED.md`

Parser tous les blocs LESSON-XXX avec tous leurs champs.

### Etape 2 : Construire les clusters semantiques

Pour chaque paire de lecons du MEME type :
- Calculer score via la logique de lesson-deduplicator
- Si score >= 0.85 -> meme cluster

Presenter les clusters :

```
CLUSTER A (type=domain, 4 lecons, total occurrences 4) :
  LESSON-001 : Reference relationnelle sans package complet (1)
  LESSON-014 : ref sans FQN (1)
  LESSON-022 : many-to-one ref="Company" (1)
  LESSON-033 : package manquant sur ref (1)
  -> Fusion proposee : LESSON-001 (4 occurrences apres fusion)
```

### Etape 3 : Mode interactif vs auto

Si --auto : fusionner automatiquement tous les clusters de score >= 0.90
Si --dry-run : afficher les clusters, ne rien ecrire
Sinon : demander confirmation par cluster

### Etape 4 : Fusion

Pour chaque cluster confirme :
1. Garder LESSON avec le plus petit ID comme "survivante"
2. Additionner Occurrences
3. Merger Tickets (union)
4. Merger Date (la plus recente)
5. Supprimer les autres lecons du cluster
6. Ecrire LESSONS-LEARNED.md

### Etape 5 : Depiler REVIEW QUEUE

Pour chaque REVIEW-XXX dans la queue :
- Afficher les candidates a l'utilisateur
- Demander : fusionner avec LESSON-XXX / nouvelle lecon / ignorer

### Etape 6 : Declencher promotions

Apres fusion, iterer sur toutes les lecons :
- Si Occurrences >= 3 ET Promu=false :
  -> Invoquer le skill knowledge-updater

Reporter :

```
Fusions : N clusters, M lecons fusionnees
Review queue traitees : K
Promotions : P lecons promues dans CLAUDE.md marketplace
```

### Etape 7 : Mise a jour STATS

Mettre a jour en-tete de LESSONS-LEARNED.md :

```markdown
## STATS

| Metrique | Valeur |
|----------|--------|
| Total lecons | <new_total> |
| Promues dans CLAUDE.md | <new_promoted> |
| En attente | <new_pending> |
| Taux de promotion | <pct>% |
| Derniere consolidation | YYYY-MM-DD |
```

## CAS NOMINAL PREMIERE EXECUTION

Sur les 55 lecons actuelles, s'attendre a :
- Entre 15 et 25 clusters reels (beaucoup de doublons)
- 5 a 10 lecons atteignant 3+ occurrences -> promotion
- Base ramenee a ~25-30 lecons distinctes

## RISQUES

- Fusion incorrecte : fournir --dry-run avant --auto
- Perte d'info : conserver un backup `LESSONS-LEARNED.md.bak-YYYY-MM-DD`

## BACKUP AUTO

Avant toute ecriture, creer automatiquement :

```
cp LESSONS-LEARNED.md LESSONS-LEARNED.md.bak-$(date +%Y-%m-%d-%H%M%S)
```
