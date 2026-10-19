# Workflows, statuts & transitions

## Vocabulaire

- **Statut** : état d'un ticket (Ouvert, En cours, Terminé…). Chaque statut appartient à une **catégorie** : *À faire* (New / blue-gray), *En cours* (Indeterminate / yellow), *Terminé* (Done / green). Les catégories pilotent JQL (`statusCategory`), les couleurs et beaucoup de rapports.
- **Transition** : passage d'un statut à un autre. Peut porter des **règles**.
- **Résolution** : champ à part (Terminé, Rejeté, Won't Do…). Attention : « statut Terminé » n'implique PAS « résolu ». Poser la résolution à la clôture, la vider à la réouverture.

## Règles de transition (les 3 familles)

| Famille | Rôle | Exemple |
|---------|------|---------|
| **Condition** | Qui/quand peut voir/déclencher la transition | « seul l'assigné peut passer En cours » |
| **Validateur** | Bloque la transition si une exigence n'est pas remplie | « le champ X doit être renseigné » |
| **Post-fonction** | Action automatique après la transition | « poser la résolution », « assigner au reporter », « horodater » |

## Recette clé AxENR — « champ obligatoire uniquement au passage En cours » (AC-15, AC-17)

Besoin : à la **création**, seule l'échéance (et priorité) est requise ; les autres champs (Version cible, Parent, Composant…) ne deviennent obligatoires **qu'au passage dans un statut de catégorie *En cours***.

### Company-managed (projets clients)
Le champ requis **dans la Field Configuration** est requis PARTOUT (y compris à la création) — ce n'est pas ce qu'on veut. La bonne approche est un **validateur de transition** :
1. Éditer le **workflow** (via le workflow scheme du projet).
2. Sur **chaque transition qui entre dans un statut *En cours*** (ex. Ouvert→En cours, Planifié→En cours, Revue→En cours), ajouter un **validateur « champ requis »**.
   - Natif Jira Cloud : validateurs limités. Pour « ces champs doivent être non vides », on utilise en pratique une **app** : *Jira Suite Utilities (JSU)*, *JMWE (Jira Misc Workflow Extensions)* ou *Adaptavist ScriptRunner* → validateur « Fields Required » / « Field has been modified ».
   - Alternative sans app : une **règle d'automation** déclenchée sur la transition qui, si un champ requis est vide, **renvoie** le ticket au statut précédent + commente (voir `automation.md`). Moins ergonomique (le refus arrive après coup) mais natif.
3. Laisser ces champs **facultatifs dans la Field Configuration** (pour la création).
4. Attention : Mémoire projet : validateur « N'est pas vide » déjà posé sur les transitions 5/6/23 ; les **transitions de retour** ne sont pas couvertes → si on ajoute une transition entrante vers En cours, penser à y remettre le validateur. Field Config **dédiée par projet** (×7) mais **workflow partagé** (×1) : modifier le workflow impacte tous les projets qui le partagent.

### Team-managed (AC)
Dans l'éditeur de workflow du projet, sélectionner la **transition** entrante vers « En cours » et ajouter une **règle** de type validation de champ (« ce champ doit être renseigné pour cette transition »). Tout est local au projet AC, pas de scheme. Si la règle voulue n'est pas disponible dans l'éditeur team-managed de l'instance → repli sur **automation** (même principe que ci-dessus). Vérifier ce qui est réellement proposé dans l'UI avant de promettre.

## Poser / vider la résolution proprement

- Transition vers un statut terminal (Terminé, Rejeté) → **post-fonction** « Update Issue Field : Resolution = Terminé/Rejeté » (ou écran de transition demandant la résolution).
- Transition de réouverture → **post-fonction** « Clear Resolution ».
- Sans ça : les rapports « non résolus » et les gadgets sont faux.

## Ajouter / supprimer un statut

- **Company-managed** : éditer le workflow (attention scheme partagé), ajouter le statut + les transitions, publier. Vérifier l'impact sur les colonnes de board (mapping statut→colonne) et les cartes.
- **Team-managed** : *Paramètres du projet → Workflow* (ou tableau → colonnes selon la version d'UI), ajouter le statut, câbler les transitions.
- Éviter les **statuts orphelins** (non atteignables) et les doublons de libellé entre catégories.
- Cas AC-14 : « ajout du statut closed » → souvent déjà présent, vérifier avant de créer (anti-hallucination).

## Transitions globales & « All »

Une **transition globale** (« All → X ») permet d'atteindre un statut depuis n'importe où (utile pour « Rejeté » ou « Annulé »). Pratique mais à conditionner (sinon tout le monde peut tout court-circuiter).

## Diagnostic transition

- API `getTransitionsForJiraIssue(issueIdOrKey)` → liste les transitions **réellement offertes** à l'état courant pour l'utilisateur courant (tient compte des conditions). Si une transition manque : condition non remplie, ou statut non câblé.
- Une transition qui « échoue » silencieusement = souvent un **validateur** (champ requis) ou une **permission** de transition.
