# Diagnostiquer un refus d'accès

## Règle préalable

**Reproduis avec le compte concerné, jamais avec un administrateur.** Un compte `admin`, ou tout
compte du groupe de code `admins`, contourne le moteur de droits : il répondra toujours
« autorisé ». Le test serait faux.

Si tu ne peux pas emprunter le compte, crée un compte de test avec exactement le même groupe et les
mêmes rôles, et reconnecte-toi.

## Arbre de décision

```
Symptôme
│
├─ "Erreur d'accès" / "pas autorisé à lire cette ressource"
│   └─> C'est une PERMISSION. Va en A.
│
├─ Un menu n'apparaît pas
│   └─> C'est la VISIBILITÉ DES MENUS. Va en B.
│
├─ L'écran s'ouvre mais une liste est vide ou incomplète
│   └─> C'est une CONDITION JPQL. Va en C.
│
├─ Un champ est masqué ou en lecture seule
│   └─> C'est une META PERMISSION ou un attribut de vue. Va en D.
│
└─ Le changement de droits ne produit aucun effet
    └─> Reconnexion non faite, ou modification sur un autre rôle que celui utilisé. Va en E.
```

## A. Refus d'accès sur un objet

1. **Identifie le modèle refusé.** Ouvre les appels réseau du navigateur et repère l'appel en échec :
   `POST /ws/rest/<Modèle>/search`, `/fetch`, ou `/ws/action`. La réponse porte souvent un
   code HTTP 200 avec un corps `{"status":-1, ..., "title":"Erreur d'accès"}`.
   Le nom du modèle est dans l'URL : c'est lui qu'il faut chercher, pas celui de l'écran.
2. **Vérifie qu'une permission le cible.** Rappel de la règle d'or 1 : aucune permission sur un
   modèle vaut refus. Cherche le modèle exact **et** son joker de package.
3. **Vérifie que le joker est le bon.** Règle d'or 2 : `a.b.db.*` ne couvre pas `a.b.c.db.MonObjet`.
   C'est la cause la plus fréquente sur les objets spécifiques d'un module client.
4. **Vérifie le niveau de droit.** Une permission en lecture ne suffit pas pour un enregistrement
   que l'écran tente de modifier au chargement.
5. **Cas de la relation.** Si l'écran s'ouvre mais échoue en affichant un champ relationnel,
   le modèle refusé est celui **de la cible**, pas celui de l'écran. C'est le motif du socle commun.

## B. Menu absent

Dans l'ordre, sans sauter d'étape :

1. Le menu est-il `hidden`, ou porte-t-il une condition `moduleToCheck` ou `conditionToCheck` ?
   Ces filtres sont indépendants des droits.
2. Le menu porte-t-il un rôle ou un groupe ? S'il n'en porte aucun et qu'il est **racine**, seul
   l'administrateur le voit. S'il n'en porte aucun et qu'il a un parent, tout le monde le voit :
   le problème est alors ailleurs, probablement chez un ancêtre.
3. **Remonte toute la chaîne d'ancêtres.** Règle d'or 6 : un seul ancêtre non autorisé coupe tout
   le sous-arbre. C'est la cause n°1 des menus fantômes, et elle est invisible si on ne regarde que
   la feuille.
4. Le rôle qui porte le menu est-il bien dans un groupe de l'utilisateur, ou dans ses rôles directs ?

## C. Liste vide ou incomplète

Une condition JPQL filtre les lignes. Vérifie :

1. La condition est-elle syntaxiquement valide ? Une condition invalide peut vider la liste ou lever
   une erreur serveur.
2. Les paramètres correspondent-ils ? Un `?` par paramètre, dans l'ordre.
3. **Une autre permission sans condition sur le même modèle annulerait la restriction**
   (règle d'or 4). Si la liste est trop **large** au lieu d'être trop étroite, c'est là qu'il faut
   chercher : un rôle de dépannage ajouté au groupe suffit à tout ouvrir.

## D. Champ masqué ou en lecture seule

Trois mécanismes distincts, à départager avant de chercher :

| Mécanisme | Où | Contrôlé côté serveur |
|---|---|---|
| Meta permission | Administration | Oui |
| `hideIf` / `readonlyIf` de la vue | XML de vue ou attributs de vue | Non |
| `can-new`, `can-edit`, `can-delete`, `readonly` | XML de vue | Non |

Les deux derniers ne sont **pas** de la sécurité : ils pilotent l'interface et se contournent par
un appel direct à l'API. Si l'enjeu est la confidentialité, il faut une meta permission, ou mieux,
ne pas accorder la permission sur l'objet.

Vérifie aussi sur quel modèle le champ est réellement rendu : un prix affiché sur un écran peut
appartenir à un objet lié, et une règle champ posée sur le mauvais modèle n'a aucun effet.

## E. Aucun effet après modification

1. L'utilisateur s'est-il **déconnecté puis reconnecté** ? Les droits sont chargés en session.
2. La modification porte-t-elle sur un rôle réellement rattaché au groupe de l'utilisateur ?
3. Le compte de test appartient-il au groupe `admins` ? Alors il voit tout, quoi qu'on fasse.
4. La modification a-t-elle été faite sur le bon environnement ?

## Après correction

- Reconnexion complète, puis re-test.
- **Retire les rôles ajoutés pendant le diagnostic.** Un rôle de dépannage laissé en place est une
  faille durable, et il peut annuler une condition JPQL ailleurs.
- Note la cause racine, pas seulement la correction.
