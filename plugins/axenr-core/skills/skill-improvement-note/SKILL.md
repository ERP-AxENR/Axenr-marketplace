---
name: skill-improvement-note
description: >
  Transforme un apprentissage du jour en fiche d'amelioration de skill et la
  depose en ticket Jira dans le projet AxENR MARKETPLACE, pour integration le
  vendredi. Declencheurs : « note-le pour le skill », « on a appris quelque
  chose », « ajoute ca au skill », « le skill s'est trompe », « il manque un
  skill pour ca », « Claude n'a pas utilise le bon skill ». PAS pour : modifier
  un skill directement (jamais), creer un ticket de developpement ERP
  (organisateur-jira).
metadata:
  owner: axenr
  process: on apprend, on note, on publie le vendredi
---

# Note-le pour le skill

Personne ne modifie un skill directement. Chaque apprentissage devient une
fiche, deposee dans Jira, que l'integration du vendredi reprend
(`weekly-skill-integration`, plugin axenr-dev).

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
5. **Creer le ticket** avec le connecteur Atlassian :
   - trouver le projet par son nom : recherche des projets visibles avec
     « MARKETPLACE », retenir celui nomme « AxENR MARKETPLACE » et sa cle ;
   - type : Tache (ou le premier type standard disponible) ;
   - resume : `[<skill cible>] <titre court>` ;
   - etiquette : `amelioration-skill` ;
   - description : la fiche, en Markdown.
6. **Donner le lien du ticket** a l'utilisateur.

Si le connecteur Atlassian n'est pas disponible, ou si le projet est
introuvable : le dire, et rendre la fiche en Markdown pour que l'utilisateur
la colle lui-meme dans Jira.

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
