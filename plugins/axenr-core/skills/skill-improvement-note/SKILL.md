---
name: skill-improvement-note
description: >
  Transforme un apprentissage ou une demande d'amelioration de la marketplace
  AxENR en fiche, puis cree le ticket Jira dans le projet « AxENR Marketplace -
  Notre cerveau », assigne a Fadel, echeance le vendredi, pour integration
  hebdomadaire. Declencheurs : « note-le pour le skill », « on a appris quelque
  chose », « ajoute ca au skill », « ameliore la marketplace », « il manque un
  skill pour ca », « le skill s'est trompe », « Claude n'a pas utilise le bon
  skill ». PAS pour : modifier un skill directement (jamais), creer un ticket de
  developpement ERP (organisateur-jira).
metadata:
  owner: axenr
  process: on apprend, on note, on publie le vendredi
---

# Note-le pour le skill

Personne ne modifie un skill directement. Chaque apprentissage devient une
fiche, deposee dans Jira, que l'integration du vendredi reprend
(`weekly-skill-integration`, plugin axenr-dev).

## Ce qui merite une fiche

Tout ce qui ameliore la marketplace AxENR : un skill a corriger ou a
completer, un skill a creer, un declenchement rate, une regle de
l'architecture a revoir.

## Quand faire une fiche

| Situation | Type de fiche |
|---|---|
| Claude a du etre corrige sur un point (surtout deux fois) | correction |
| Un piege a ete decouvert chez un client | piege-client |
| Une manipulation a ete validee et doit etre refaite a l'identique | procedure |
| Le bon skill ne s'est pas declenche, ou un autre s'est declenche a sa place | declenchement |
| Aucun skill ne couvre le sujet | nouveau-skill |

## Etapes

1. **Identifier le skill cible** : son nom exact (celui qui a servi, ou qui
   aurait du servir). Si aucun ne convient : `nouveau-skill` et un nom propose.
2. **Determiner la portee** :
   - generique AxENR -> plugin `axenr-*` du domaine ;
   - propre a un client -> plugin `client-<nom>`. Ne jamais melanger.
3. **Rediger la fiche** avec le gabarit ci-dessous, a partir de la
   conversation en cours. Le texte propose doit etre pret a coller dans le skill.
4. **Montrer la fiche a l'utilisateur** et demander son accord.
5. **Creer le ticket** avec le connecteur Atlassian (site `erp-axenr.atlassian.net`) :

   | Champ | Valeur par defaut |
   |---|---|
   | Projet | `AMNC` (« AxENR Marketplace - Notre cerveau ») |
   | Type | Tache (sinon le premier type standard disponible) |
   | Resume | `[<skill cible>] <titre court>` |
   | Responsable | **Toujours** Fadel Benomar, relecteur de la marketplace (recherche d'utilisateur « fadel benomar ») |
   | Echeance (`duedate`) | le **prochain vendredi** : du lundi au jeudi, le vendredi de la semaine ; le vendredi, samedi ou dimanche, le vendredi suivant. Format AAAA-MM-JJ |
   | Etiquette | `amelioration-skill` |
   | Description | la fiche, en Markdown |

   Le ticket est toujours assigne a Fadel : c'est lui qui fait la revue de
   toute modification de la marketplace. Ne jamais le laisser non assigne ni
   l'assigner a son auteur. L'utilisateur peut changer l'echeance : sa demande
   prime sur la valeur par defaut. Un ticket qui accompagne une PR deja prete a
   relire passe directement au statut « En review ».
6. **Donner le lien du ticket** a l'utilisateur, avec le responsable et
   l'echeance retenus.

Si le connecteur Atlassian n'est pas disponible, ou si la creation est
refusee (compte sans acces au projet AMNC) : le dire, et rendre la fiche en
Markdown pour que l'utilisateur la colle lui-meme dans Jira. Ne jamais creer
le ticket depuis un compte qui n'est pas celui de l'utilisateur.

## Gabarit de fiche

```markdown
## Skill cible
<nom du skill> (plugin <axenr-xxx | client-xxx>) | nouveau-skill : <nom propose>

## Type
correction | piege-client | procedure | declenchement | nouveau-skill

## Ce qu'on a appris
<2 a 5 lignes, factuelles>

## Preuve
<ce qui le demontre : message d'erreur, ecran, fichier:ligne, resultat obtenu>

## Texte propose pour le skill
<le paragraphe, la ligne de tableau ou la regle a ajouter, pret a coller>

## Section du skill concernee
<titre de section existante, ou "nouvelle section">
```

## Regles

- Une fiche par apprentissage : jamais de fiche fourre-tout.
- Aucun secret (mot de passe, cle, jeton) ni donnee personnelle (nom, e-mail,
  telephone d'un contact client) dans la fiche : anonymiser.
- Ne pas inventer de preuve : si l'apprentissage n'est pas verifie, l'ecrire.
- Ne jamais proposer de modifier le skill dans claude.ai, ni d'en faire une
  copie personnelle.
