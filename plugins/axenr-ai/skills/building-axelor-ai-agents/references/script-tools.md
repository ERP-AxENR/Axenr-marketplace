# Outils SCRIPT : lire et calculer côté serveur

## Bac à sable (constaté sur AOP 8.x)

- Langage : JavaScript GraalJS. Le champ `script` est **une expression** évaluée : l'envelopper dans
  `(function () { ... })()` et `return` un objet JSON-isable. `deploy_ai_spec.py` fait l'enveloppe et concatène les
  fichiers `prelude_files` (fonctions communes) devant le corps.
- Entrée : variable `input` (objet conforme à `inputSchema`). Toujours tester les paramètres absents.
- Accès Java : `Java.type("com.axelor.db.Query")` et les classes d'entité (`com.axelor.apps...db.Equipment`,
  `com.axelor.mail.db.MailMessage`) **autorisés**. `Java.type("com.axelor.db.JPA")` **refusé** :
  « TypeError: Access to host class com.axelor.db.JPA is not allowed or does not exist ». Donc **lecture seule**.
- Requêtes : `Q.of(Cls).filter("self.x = :p").bind("p", v).order("-createdOn").fetch(n)`. Un `fetch()` sans
  filtre sur une table de quelques milliers de lignes reste rapide ; au-delà, filtrer.
- Les dates Java se convertissent par `String(d)` (format `AAAA-MM-JJ`) ; les `BigDecimal` par `Number(v)`.
- Champs personnalisés : `JSON.parse(String(e.getAttrs()))` dans un `try`.

## Contrat de sortie d'un bon outil

| Élément | Pourquoi |
|---|---|
| `date_du_jour` | Le modèle ne connaît pas la date du serveur ; tous les « dans N jours » en dépendent |
| Valeurs **déjà calculées** : totaux, jours restants, statut (« EXPIRÉE depuis 487 jours »), regroupements | Le modèle recompte mal une liste |
| `definition` : d'où vient chaque chiffre (« fin de garantie = champ standard ... ») | Il la cite, l'utilisateur vérifie |
| `{ambigu: true, candidats: [...]}` / `{introuvable: true, conseil}` | Jamais de choix au hasard ; le prompt dit quoi faire |
| Identifiants (`id`, `code`) et nom de l'action d'écran | Pour `open_view` et les écritures qui suivent |
| Textes nettoyés (HTML retiré du journal) | Moins de jetons, moins de bruit |

## Recherche tolérante (désigner un enregistrement en langage naturel)

`resources/examples/pv-maintenance/tools/common.js`, fonction `trouver(saisie)` :
1. correspondance exacte sur le code, l'id ou un n° de série (au moins 6 caractères) ;
2. sinon tous les mots normalisés (sans accents, sans casse) doivent se retrouver dans un texte composé
   (code, nom, client, marque, modèle, adresse) ;
3. plusieurs résultats : départager par le nombre de mots trouvés **comme mots entiers** dans le nom
   (« onduleur 2 » ne doit pas trouver « SUN2000 ») ; égalité : rendre `ambigu` avec les candidats.

## Description de l'outil (ce que lit le modèle)

Quatre paragraphes : ce que l'outil calcule et qu'il est en lecture seule ; **quand l'appeler** avec des
formulations réelles (« point du matin », « quelles garanties expirent ») ; l'entrée exacte avec un exemple ;
la forme de la réponse, `ambigu` et `introuvable` compris. Préfixer le `name` par le domaine
(« Parc PV : synthèse de toutes les centrales ») : il apparaît dans l'interface.

## Squelette

```javascript
// prelude commun (common.js) : Q, classes, normaliser(), attrsDe(), AUJ, jours(), trouver()
var t = trouver(input && input.equipement);
if (!t.equipement) { return t; }                      // ambigu / introuvable / erreur
var e = t.equipement, a = attrsDe(e);
return {
  date_du_jour: AUJ,
  fiche: { id: Number(e.getId()), code: String(e.getCode()), nom: String(e.getName()), caracteristiques: a },
  historique_interventions: historique(e, 30),
  ecran: { action: "assets.management.root.equipment", model: EQ_MODEL, id: Number(e.getId()) }
};
```

## Tester un outil seul

Pas d'endpoint d'exécution directe repéré : le tester par le chat avec une consigne explicite
(« Appelle pv_garanties avec horizon 30 et donne le résultat brut ») via `chat_test.py`. Une erreur de script
remonte en `tool-output-error` avec le message GraalJS.
