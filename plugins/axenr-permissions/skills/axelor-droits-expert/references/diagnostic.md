# Diagnostiquer un refus d'accès

## Règle préalable

**Reproduis avec le compte concerné, jamais avec un administrateur.** Un compte `admin`, ou tout
compte du groupe de code `admins`, contourne le moteur de droits : il répondra toujours
« autorisé ». Le test serait faux.

Si tu ne peux pas emprunter le compte, crée un compte de test avec exactement le même groupe et les
mêmes rôles, et reconnecte-toi.

## Paliers d'investigation

Ordre général face à un problème : droits, puis configuration, puis documentation, puis code.
Pour les droits eux-mêmes, monte les paliers dans l'ordre, sans en sauter :

| Palier | Outil | Ce qu'on cherche | Accord requis |
|---|---|---|---|
| 1 | DevTools du navigateur, onglet Réseau | L'appel en échec et le modèle refusé (voir A) | Non |
| 2 | SQL en lecture seule sur `auth_group`, `auth_role`, `auth_permission` et leurs tables de jointure | Qui porte quoi, réellement, en base | Non (lecture seule) |
| 3 | Logs serveur en DEBUG | La décision du moteur, ligne par ligne | **Oui, feu vert explicite** |

Pour le palier 3 : logger `com.axelor.auth=TRACE` pour voir les refus d'écriture ; l'exception à
chercher dans les logs est `com.axelor.auth.AuthSecurityException`. La configuration se fait dans
`axelor-config.properties` (pas dans un `application.properties`). Remets le niveau de log
d'origine après le diagnostic.

> Compléments ci-dessous marqués « [partenaire] » : apport d'un chef de projet Axelor (paquet du
> 15/10/2026), éprouvé sur AOS 9.1.6 / AOP EE 8.2.3. AxENR tourne sur AOP 7.4 / AOS 8.x : à
> vérifier sur la version cible.

**Lire le journal sans passer en DEBUG [partenaire].** L'interface dit seulement « Vous n'êtes pas
autorisé(e) à lire / modifier / créer cette ressource », sans nommer l'objet. Le journal serveur
le nomme, avec le login, au niveau par défaut :

```bash
grep -a 'Authorization Error' <CATALINA_BASE>/logs/catalina.out | tail -20
```
```
ERROR … ResponseInterceptor : Authorization Error:
  [Message=Vous n'êtes pas autorisé(e) à créer cette ressource.,
   User=<login>, Detail=com.axelor.apps.purchase.db.PurchaseOrderLineTax]
```

C'est la seule source qui nomme l'entité refusée : le corps de la réponse réseau porte le message
sans la classe. Lire ce journal est une lecture (palier 1 ou 2) ; passer un logger en TRACE reste
le palier 3, avec feu vert. Injecte la classe trouvée dans la requête Q4 de `recettes-sql.md` :
neuf fois sur dix, il n'existe aucune ligne, l'objet n'a jamais été énuméré.

### Classer le refus avant d'ajouter un droit [partenaire]

Plusieurs « problèmes de droits » n'en sont pas. Élargir une permission masque alors la vraie
cause.

| Symptôme | Cause possible | Vérification |
|---|---|---|
| Menu absent | Portée de menu ou chaîne d'ancêtres, `hidden`, condition, module à vérifier | B, puis Q1 / Q2 |
| « Non autorisé » à l'ouverture ou à l'enregistrement | Permission objet, **ou une valeur imbriquée** de l'enregistrement (création ou écriture sur sa cible) | Journal, puis Q4 ; section A, point 7 |
| Le même bundle marche sur une instance et échoue sur une autre | Réglages `application.permission.disable-relational-field` / `disable-action` différents (simples avertissements quand ils valent `true`) | `axelor-config.properties` des deux instances |
| Connexion refusée, « mot de passe erroné » | Compte `blocked` (vrai par défaut en AOS 9.1.6 pour un compte créé par API), sièges Guardian de l'édition entreprise (code 1021), session périmée | `auth_user.blocked`, journal serveur, vraie reconnexion |
| Liste plus courte que prévu | Condition de la permission de lecture (voir `permissions-conditionnelles.md`), filtre enregistré, vue personnalisée par utilisateur (`meta_view_custom` servie en premier), enregistrements archivés exclus d'une recherche REST filtrée | Q4, filtres, `meta_view_custom` |
| Flux refusé faute d'employé | Utilisateur sans `Employee` dans la bonne société | Fiche utilisateur |
| Erreur dans une action | Bug applicatif ou action résiduelle, pas un droit | Trace de pile |

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
6. **Accès au menu ne veut pas dire lecture des données.** Un utilisateur peut voir et ouvrir un
   menu, puis tomber sur l'erreur juste après : l'écran interroge d'autres modèles (par exemple un
   planning qui lit les employés). Le menu est accordé, la donnée ne l'est pas. Repars de l'appel
   réseau, jamais du libellé du menu.
7. **Refus à l'enregistrement d'une fiche pourtant autorisée [partenaire].** `Resource.save`
   contrôle l'enregistrement principal **et chaque valeur imbriquée** de la charge utile (AOP
   8.2.3) : sans identifiant, création sur le modèle cible ; avec identifiant et version,
   écriture. Exemple : `Partner` entièrement accordé, mais l'enregistrement échoue dès qu'un e-mail
   ou une nouvelle adresse est saisi, faute de création sur `EmailAddress` et `Address`. Les
   références existantes voyagent sans version et ne déclenchent pas d'écriture. Lis la charge
   utile de l'appel en échec.
8. **Bouton ou assistant sans effet [partenaire].** Chaque action contrôle la lecture sur son
   modèle (ou le modèle du contexte), et une `action-record` qui écrit un vrai champ contrôle la
   création ou l'écriture. Un assistant demande donc au minimum la lecture de
   `com.axelor.utils.db.Wizard`. Pour l'inventaire complet des dépendances par geste :
   `fermeture-dependances-vues.md`.

### Méthode courte en 8 étapes (refus d'accès sur un objet)

1. Reproduire avec le compte concerné, ou un compte de test identique, jamais un admin.
2. Repérer l'appel réseau en échec et noter le modèle exact de l'URL.
3. Lire son package réel dans `meta_model` (`package_name`, `full_name`).
4. Chercher dans Administration > Rôles le rôle `<Entité> Read`, et sa variante `(sans menu)`
   si elle existe.
5. Vérifier le contenu réel de ce rôle : une permission couvre-t-elle le modèle exact ou son
   joker de package exact ? Ne pas se fier au nom du rôle.
6. Attribuer au groupe la variante **sans menu** si l'utilisateur n'a besoin que des données ;
   si elle n'existe pas, la créer (voir `conception.md`) plutôt que d'attribuer le rôle complet.
7. Déconnexion, reconnexion, re-test de l'accès **et** des refus attendus.
8. Retirer les rôles de dépannage, puis documenter la cause racine et le correctif.

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
5. La modification a-t-elle été faite **en SQL** pendant que l'application tournait ? Voir
   ci-dessous.

### Caches et reconnexion : deux positions

| Position | Source et version | Ce qu'elle dit |
|---|---|---|
| Règle d'or 10 | Ce skill, niveau `[DOC]` et terrain, non vérifié dans le code | Les droits sont chargés en session : déconnexion puis reconnexion obligatoires |
| Apport partenaire | Lecture d'AOP 8.2.3 et mesures sur 8.2.2 | L'utilisateur courant est relu à chaque requête (`AuthUtils.getUser`). Une modification faite **par l'application** (import, interface, REST) passe par l'ORM et devrait s'appliquer à la requête suivante (non mesuré). Une modification faite **en SQL** n'est pas vue par le cache Hibernate de niveau 2 ni par le cache de métadonnées : il faut **redémarrer Tomcat**. Le navigateur garde l'arbre des menus en cache : rafraîchissement forcé (`Ctrl+Shift+R`), et `?_reset=true` pour le schéma des formulaires |

Pratique retenue tant que la règle 10 n'est pas instruite dans le code de la version cible :
appliquer les deux. Après une modification par l'application : déconnexion, rafraîchissement
forcé, reconnexion. Après une modification en SQL : redémarrage de Tomcat, puis la même chose. Ne
soupçonne un cache qu'après avoir vérifié en base (Q1 à Q4 de `recettes-sql.md`) que la
visibilité est correcte sur le papier.

**Attention à « Tout restaurer… » [partenaire].** Le bouton *Administration > Gestion des vues >
Les vues > Tout restaurer…* (action `action-meta-restore-all`) recharge les métadonnées sous
l'identité `admin`, et laisse environ une requête web sur dix répondre en `admin` jusqu'au
redémarrage de Tomcat (mesuré sur AOP 8.2.2 ; même code en 8.2.3). Un profil testé entre les deux
est testé en partie comme `admin`, ce qui ne prouve rien. Si tu l'utilises : **redémarrage de
Tomcat immédiatement après**, avant tout test ou démo. Sur une instance hébergée où tu ne peux pas
redémarrer, ne l'utilise pas. Il réapplique aussi les attributs XML de tous les menus et vues et
écrase les personnalisations : sauvegarde `meta_view`, `meta_menu` et `meta_action` avant.

### Voir ce que le serveur montre à un profil [partenaire]

Pour lire les menus réellement servis à un profil (`GET /ws/action/menu/all`, qui applique
groupes, rôles, chaîne d'ancêtres, `hidden`, module et condition) ou rejouer un geste, ouvre une
session REST **avec le compte du profil**, jamais en `admin`. Le mot de passe est saisi par la
personne qui possède le compte, dans son propre terminal : jamais dans la conversation, jamais en
argument de commande, jamais dans un fichier.

```bash
umask 077
read -rsp 'Password: ' PW; echo      # en zsh : read -rs 'PW?Password: '
printf '%s' "$PW" | curl -sS -c jar.txt -b jar.txt -o /dev/null \
  -X POST "<url>/callback?client_name=AxelorFormClient" \
  --data-urlencode "username=<login>" --data-urlencode "password@-"
unset PW
curl -sS -b jar.txt "<url>/ws/public/app/info"            # doit contenir une clé "user"
curl -sS -b jar.txt "<url>/ws/action/menu/all" -o menus-<login>.json
```

- `<url>` est la racine de l'application, chemin de contexte compris.
- `/ws/public/app/info` répond même sans session : la session n'est ouverte que si la réponse
  contient une clé `user` dont le `login` est le bon (avec `jq` : `jq -e '.user.login'`).
- Tout POST / PUT / DELETE doit porter l'en-tête `X-CSRF-Token`, valeur du cookie `CSRF-TOKEN` :
  `CSRF=$(awk '$6=="CSRF-TOKEN"{print $7}' jar.txt)`.
- Un appel peut répondre HTTP 200 avec `"status": -1` : lis toujours le champ `status`.
- `jar.txt` contient une session vivante : garde-le privé et supprime-le à la fin.

Usage clé : sauvegarder `menus-<login>.json` de chaque profil **avant** l'activation d'une
application, puis comparer après (L17 de `cadrage-profils.md`). La requête Q2 ne liste que les
racines.

## Après correction

- Reconnexion complète, puis re-test.
- **Retire les rôles ajoutés pendant le diagnostic.** Un rôle de dépannage laissé en place est une
  faille durable, et il peut annuler une condition JPQL ailleurs.
- Note la cause racine, pas seulement la correction.

## Avant toute modification en production

À cocher avant d'appliquer le correctif sur l'environnement de production (avec GO explicite) :

- [ ] Correctif validé sur recette avec un compte de test du même groupe, après reconnexion.
- [ ] Variante `(sans menu)` utilisée quand seules les données sont nécessaires : aucun menu
      inattendu n'apparaît pour le profil.
- [ ] Aucun rôle standard modifié : rôle dérivé créé si besoin.
- [ ] Aucune permission sans condition ajoutée sur un modèle déjà restreint par une condition
      JPQL dans le même groupe (règle d'or 4).
- [ ] Utilisateurs concernés prévenus de la reconnexion nécessaire.
- [ ] Ticket documenté avec la cause racine et le correctif.
