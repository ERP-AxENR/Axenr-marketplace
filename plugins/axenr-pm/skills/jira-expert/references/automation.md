# Jira Automation

Moteur no-code natif : **Trigger → Conditions → Actions**. Accessible en *Paramètres du projet → Automation* (règles projet) ou admin global (règles multi-projets).

## Structure

- **Trigger** (1 par règle) : Issue created, Issue updated, Field value changed, Issue transitioned, Scheduled (cron/JQL), On sprint, Webhook, Manual…
- **Conditions** : JQL condition, Field condition, User condition, « If/else » blocks…
- **Actions** : Edit issue, Assign issue, Transition issue, Comment, Send email, Create sub-tasks, Send web request, Log action, Lookup issues…
- **Smart values** : `{{issue.key}}`, `{{issue.assignee.displayName}}`, `{{issue.fixVersions.name}}`, `{{now}}`, `{{triggerIssue}}`, `{{initiator.displayName}}`… (templating puissant).

## Portée & limites (repères — vérifier le plan de l'instance)

- Règle **single-project** (team ou company) vs **multi-project / global** (nécessite droit admin).
- Les **exécutions** sont comptées selon le plan (Free/Standard/Premium) — les règles multi-projets consomment le quota global. Sur gros volume, préférer des conditions JQL early-exit pour ne pas gaspiller.
- Une règle peut être déclenchée par une autre (« Allow rule trigger ») — risque de boucles ; désactiver si non voulu.

## Recettes AxENR

### Auto-assigner le créateur à la création (AC-27)
Trigger *Issue created* → (option : Condition « assignee is empty ») → Action *Assign issue* = `{{issue.reporter}}` (ou `{{initiator}}`). Permet « le ticket s'assigne à celui qui le crée », modifiable ensuite manuellement.
Attention : Ne PAS combiner avec une règle « auto-assign Component Lead » qui écraserait ce choix (piège vécu — voir `versions-components.md`). Une seule règle d'assignation, sinon elles se marchent dessus.

### « Champ requis au passage En cours » sans app (repli natif)
Trigger *Issue transitioned* TO catégorie/statut « En cours » → Condition : un champ requis `IS EMPTY` → Actions : *Transition* retour au statut précédent + *Comment* « Merci de renseigner Version cible / Parent avant de passer En cours ». Moins ergonomique qu'un validateur (le blocage arrive après coup) mais 100 % natif. Le validateur reste préférable si une app (JSU/JMWE) est dispo.

### Poser la résolution automatiquement
Trigger *Issue transitioned* TO « Terminé » → Action *Edit issue* : Resolution = Terminé. Symétrique à la réouverture (Resolution = vide). Alternative à la post-fonction de workflow.

### Fermeture auto des vieux tickets / relances
Trigger *Scheduled* (JQL `statusCategory != Done AND updated <= -30d`) → Comment/relance ou transition. Utile pour l'hygiène de backlog.

## Bonnes pratiques
- **Nommer** clairement les règles + activer le **log d'audit** (onglet Audit log de la règle) pour déboguer.
- Tester sur 1 ticket avant d'activer en masse (cohérent avec R-Idempotence).
- Documenter les règles actives : une automation invisible qui « bouge » les tickets est un cauchemar de diagnostic.
- Toute règle qui **écrit en masse** (transition/édition de plusieurs tickets) = action à valider (GO manager) avant activation.
