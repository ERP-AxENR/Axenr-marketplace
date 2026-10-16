# LESSONS-LEARNED.md

> Base de connaissances auto-alimentee par le ticket-solver-agent
> Derniere mise a jour : 2026-09-09

---

## STATS

| Metrique | Valeur |
|----------|--------|
| Total lecons | 110 |
| Lecons promues dans CLAUDE.md | 0 |
| Lecons en attente | 110 |
| Taux de promotion | 0% |

---

## FORMAT

```
### LESSON-XXX : <titre court>
- **Type** : domain | view | action | java | build | version | mobile | naming | i18n | rest | migration | enr | config | diagnostic | process
- **Projet** : axenr-app | axenr-mobile | both
- **Erreur** : description du pattern d'erreur
- **Correction** : comment corriger
- **Occurrences** : N
- **Tickets** : #XXX, #YYY
- **Promu** : false | true
```

---

## ERREURS DOMAINS

### LESSON-001 : Reference relationnelle sans package complet
- **Type** : domain
- **Projet** : axenr-app
- **Erreur** : Utiliser `ref="Company"` au lieu du chemin complet dans many-to-one/one-to-many
- **Correction** : Toujours utiliser `ref="com.axelor.apps.base.db.Company"` avec le package complet
- **Occurrences** : 1
- **Tickets** : initial-seed
- **Promu** : false

### LESSON-002 : One-to-many sans mappedBy
- **Type** : domain
- **Projet** : axenr-app
- **Erreur** : Declarer un one-to-many sans `mappedBy`, ce qui cree une table de jointure inutile
- **Correction** : Toujours ajouter `mappedBy="parentField"` et creer le many-to-one inverse dans l'entite enfant
- **Occurrences** : 1
- **Tickets** : initial-seed
- **Promu** : false

### LESSON-003 : Boolean avec title
- **Type** : domain
- **Projet** : axenr-app
- **Erreur** : Mettre `title="..."` sur un champ boolean. Axelor ignore le title et genere le label depuis le nom du champ
- **Correction** : Ne JAMAIS mettre de title sur un boolean. Bien nommer le champ (ex: `isProjectNotMandatory`) et utiliser `./gradlew i18n` pour generer la cle
- **Occurrences** : 1
- **Tickets** : initial-seed
- **Promu** : false

### LESSON-004 : Boolean sans default
- **Type** : domain
- **Projet** : axenr-app
- **Erreur** : Declarer un boolean sans `default="false"` ou `default="true"` explicite
- **Correction** : Toujours mettre `default="false"` (ou `default="true"`) sur les champs boolean
- **Occurrences** : 1
- **Tickets** : initial-seed
- **Promu** : false

### LESSON-005 : Selection sans extra-code constantes
- **Type** : domain
- **Projet** : axenr-app
- **Erreur** : Declarer un champ `selection="xxx.select"` sans definir les constantes correspondantes dans `extra-code`
- **Correction** : Toujours ajouter un bloc `<extra-code>` avec `public static final int STATUS_XXX = N;` pour chaque valeur de la selection
- **Occurrences** : 1
- **Tickets** : initial-seed
- **Promu** : false

### LESSON-006 : Repository cree manuellement
- **Type** : domain
- **Projet** : axenr-app
- **Erreur** : Creer manuellement un fichier Repository Java. Les repositories sont auto-generes par `./gradlew generateCode`
- **Correction** : Ne jamais creer de repository manuellement. Utiliser `./gradlew generateCode` et le fichier sera dans `build/src-gen/`
- **Occurrences** : 1
- **Tickets** : initial-seed
- **Promu** : false

### LESSON-007 : Panel principal avec title
- **Type** : domain
- **Projet** : axenr-app
- **Erreur** : Mettre `title="Main"` sur le panel principal d'un formulaire
- **Correction** : Le panel principal (`mainPanel`) ne doit PAS avoir de title
- **Occurrences** : 1
- **Tickets** : initial-seed
- **Promu** : false

---

## ERREURS VIEWS

### LESSON-008 : Champ relationnel sans form-view/grid-view
- **Type** : view
- **Projet** : axenr-app
- **Erreur** : Declarer un champ many-to-one ou many-to-many sans `form-view` et `grid-view`
- **Correction** : Toujours specifier `form-view="xxx-form" grid-view="xxx-grid"` sur les champs relationnels
- **Occurrences** : 1
- **Tickets** : initial-seed
- **Promu** : false

### LESSON-009 : Elements XML sans name
- **Type** : view
- **Projet** : axenr-app
- **Erreur** : Declarer des panels ou boutons sans attribut `name`, ce qui empeche les extensions
- **Correction** : TOUJOURS nommer les panels (`name="xxxPanel"`), boutons (`name="xxxBtn"`) et autres elements
- **Occurrences** : 1
- **Tickets** : initial-seed
- **Promu** : false

### LESSON-010 : O2M affiche avec field au lieu de panel-related
- **Type** : view
- **Projet** : axenr-app
- **Erreur** : Utiliser `<field name="lineList"/>` pour afficher un one-to-many
- **Correction** : Utiliser `<panel-related field="lineList" form-view="xxx-form" grid-view="xxx-grid"/>` pour les O2M
- **Occurrences** : 1
- **Tickets** : initial-seed
- **Promu** : false

### LESSON-011 : Extension sans id="axenr-..." et extension="true"
- **Type** : view
- **Projet** : axenr-app
- **Erreur** : Etendre une vue sans le pattern AxENR : `id="axenr-xxx"` + `extension="true"`
- **Correction** : Toujours utiliser `<form id="axenr-xxx-form" name="xxx-form" ... extension="true">`
- **Occurrences** : 1
- **Tickets** : initial-seed
- **Promu** : false

### LESSON-012 : SchemaLocation sur 2 lignes
- **Type** : view
- **Projet** : axenr-app
- **Erreur** : Ecrire `xsi:schemaLocation` sur 2 lignes dans les fichiers XML de vues
- **Correction** : Toujours mettre le schemaLocation sur 1 seule ligne
- **Occurrences** : 1
- **Tickets** : initial-seed
- **Promu** : false

### LESSON-013 : Combiner move et insert dans un seul extend
- **Type** : view
- **Projet** : axenr-app
- **Erreur** : Combiner `<move>` et `<insert>` dans un seul `<extend>`, ce qui fait que l'element insere se retrouve apres les elements deplaces
- **Correction** : Separer en 2 extends distincts : un pour les moves, un pour les inserts
- **Occurrences** : 1
- **Tickets** : initial-seed
- **Promu** : false

---

## ERREURS ACTIONS

### LESSON-014 : Expression sans eval:
- **Type** : action
- **Projet** : axenr-app
- **Erreur** : Ecrire `expr="__date__"` sans le prefixe `eval:` dans les action-record
- **Correction** : Toujours ecrire `expr="eval: __date__"`, `expr="eval: __repo__(Model).CONSTANT"`, etc.
- **Occurrences** : 1
- **Tickets** : initial-seed
- **Promu** : false

### LESSON-015 : Caracteres speciaux non echappes dans XML
- **Type** : action
- **Projet** : axenr-app
- **Erreur** : Utiliser `&&`, `>`, `<` dans les attributs XML au lieu de `&amp;&amp;`, `&gt;`, `&lt;`
- **Correction** : Toujours echapper : `&amp;` pour &, `&lt;` pour <, `&gt;` pour >, `&quot;` pour "
- **Occurrences** : 1
- **Tickets** : initial-seed
- **Promu** : false

### LESSON-016 : Null safety manquante dans expressions
- **Type** : action
- **Projet** : axenr-app
- **Erreur** : Ecrire `partner.address.city` sans `?.` dans les expressions XML, causant NullPointerException
- **Correction** : Toujours utiliser `partner?.address?.city` avec l'operateur null-safe
- **Occurrences** : 1
- **Tickets** : initial-seed
- **Promu** : false

### LESSON-017 : Action-view admin avec mauvais nommage
- **Type** : action
- **Projet** : axenr-app
- **Erreur** : Nommer une action-view admin `action.xxx` au lieu de `admin.xxx`
- **Correction** : Utiliser le format `admin.xxx` pour les action-views d'administration
- **Occurrences** : 1
- **Tickets** : initial-seed
- **Promu** : false

### LESSON-018 : onChange ecrase sans preserver l'existant
- **Type** : action
- **Projet** : axenr-app
- **Erreur** : Remplacer un onChange existant au lieu de l'etendre
- **Correction** : Ne jamais ecraser un onChange. Ajouter la nouvelle action dans le group existant ou en creer un nouveau qui inclut l'ancien
- **Occurrences** : 1
- **Tickets** : initial-seed
- **Promu** : false

---

## ERREURS JAVA

### LESSON-019 : @Transactional manquant sur methode avec save
- **Type** : java
- **Projet** : axenr-app
- **Erreur** : Methode qui appelle `repo.save()` sans `@Transactional`, pas de rollback si exception
- **Correction** : Ajouter `@Transactional(rollbackOn = {Exception.class})` sur toute methode qui fait un save
- **Occurrences** : 1
- **Tickets** : initial-seed
- **Promu** : false

### LESSON-020 : Controller sans try-catch + TraceBackService
- **Type** : java
- **Projet** : axenr-app
- **Erreur** : Controller sans `try-catch` avec `TraceBackService.trace(response, e)`, retourne erreur 500 brute
- **Correction** : Toujours wrapper le corps du controller dans `try { ... } catch (Exception e) { TraceBackService.trace(response, e); }`
- **Occurrences** : 1
- **Tickets** : initial-seed
- **Promu** : false

### LESSON-021 : Objet contexte sauvegarde directement
- **Type** : java
- **Projet** : axenr-app
- **Erreur** : Sauvegarder directement l'objet obtenu via `request.getContext().asType()` sans le recharger depuis la base
- **Correction** : Toujours recharger avec `repo.find(obj.getId())` avant de sauvegarder. L'objet contexte n'est pas attache a Hibernate
- **Occurrences** : 1
- **Tickets** : initial-seed
- **Promu** : false

### LESSON-022 : Messages non traduits avec I18n.get()
- **Type** : java
- **Projet** : axenr-app
- **Erreur** : Utiliser des strings en dur dans les exceptions/messages au lieu de `I18n.get(ExceptionMessage.XXX)`
- **Correction** : Creer des constantes dans `ExceptionMessage` avec le pattern `/*$$(*/  "text" /*)*/` et utiliser `I18n.get()`
- **Occurrences** : 1
- **Tickets** : initial-seed
- **Promu** : false

### LESSON-023 : @Inject inutile pour methodes statiques
- **Type** : java
- **Projet** : axenr-app
- **Erreur** : Injecter via `@Inject` une classe dont on utilise uniquement des methodes statiques (ex: `MetaFiles.getPath()`)
- **Correction** : Appeler directement les methodes statiques sans injection : `MetaFiles.getPath(metaFile).toFile()`
- **Occurrences** : 1
- **Tickets** : initial-seed
- **Promu** : false

### LESSON-024 : Commentaires dans le code genere
- **Type** : java
- **Projet** : axenr-app
- **Erreur** : Ajouter des commentaires dans le code genere. Le code doit etre auto-documente
- **Correction** : ZERO commentaire dans le code. Si le code a besoin d'un commentaire, il doit etre refactorise pour etre plus clair
- **Occurrences** : 1
- **Tickets** : initial-seed
- **Promu** : false

### LESSON-025 : Beans.get() dans un Service
- **Type** : java
- **Projet** : axenr-app
- **Erreur** : Utiliser `Beans.get(Service.class)` dans un service au lieu de `@Inject`
- **Correction** : `Beans.get()` est OK dans les Controllers uniquement. Dans les Services, utiliser `@Inject` sur champ ou constructeur
- **Occurrences** : 1
- **Tickets** : initial-seed
- **Promu** : false

### LESSON-026 : Wildcard imports
- **Type** : java
- **Projet** : axenr-app
- **Erreur** : Utiliser `import com.axelor.xxx.*;` (wildcard imports)
- **Correction** : Toujours utiliser des imports explicites, un par classe
- **Occurrences** : 1
- **Tickets** : initial-seed
- **Promu** : false

### LESSON-027 : Noms francais dans le code
- **Type** : java
- **Projet** : both
- **Erreur** : Utiliser des mots francais dans les noms de code (panels, actions, champs, variables)
- **Correction** : ENGLISH ONLY pour tous les noms techniques
- **Occurrences** : 1
- **Tickets** : initial-seed
- **Promu** : false

### LESSON-028 : SecurityCheck avec ID
- **Type** : java
- **Projet** : axenr-app
- **Erreur** : Utiliser `new SecurityCheck().readAccess(Class, id)` avec un parametre ID
- **Correction** : Utiliser `new SecurityCheck().writeAccess(Class).createAccess(Class).check()` avec Class seulement, pas (Class, id)
- **Occurrences** : 1
- **Tickets** : initial-seed
- **Promu** : false

---

## ERREURS BUILD

### LESSON-029 : generateCode en minuscules
- **Type** : build
- **Projet** : axenr-app
- **Erreur** : Ecrire `generatecode` ou `copywebapp` en minuscules dans la commande gradle
- **Correction** : Respecter la casse : `generateCode` et `copyWebapp` (camelCase)
- **Occurrences** : 1
- **Tickets** : initial-seed
- **Promu** : false

### LESSON-030 : Version Java modifiee dans build.gradle
- **Type** : build
- **Projet** : axenr-app
- **Erreur** : Modifier `languageVersion` dans `build.gradle`. Le projet DOIT rester en Java 11
- **Correction** : Ne JAMAIS modifier `JavaLanguageVersion.of(11)` dans build.gradle
- **Occurrences** : 1
- **Tickets** : initial-seed
- **Promu** : false

---

## ERREURS VERSION

### LESSON-031 : Versions enterprise modules non individuelles
- **Type** : version
- **Projet** : axenr-app
- **Erreur** : Supposer que tous les modules enterprise ont la meme version AOS. Chaque module peut avoir une version differente
- **Correction** : Lire `libs.versions.toml` et verifier la version INDIVIDUELLE de chaque module (axelor-intervention=8.5.11, axelor-business-support=8.5.5, etc.)
- **Occurrences** : 1
- **Tickets** : initial-seed
- **Promu** : false

### LESSON-032 : XSD version non alignee avec AOP
- **Type** : version
- **Projet** : axenr-app
- **Erreur** : Utiliser une version XSD qui ne correspond pas a la version AOP
- **Correction** : AOP 7.x → XSD 7.1, AOP 8.x → XSD 8.0. Verifier dans gradle.properties pour aopVersion
- **Occurrences** : 1
- **Tickets** : initial-seed
- **Promu** : false

---

## ERREURS NAMING

### LESSON-033 : Menuitem admin avec prefixe axenr-
- **Type** : naming
- **Projet** : axenr-app
- **Erreur** : Nommer un menuitem admin `axenr-xxx-admin` au lieu de `xxx-admin`
- **Correction** : Les menuitems admin ne prennent PAS le prefixe `axenr-`
- **Occurrences** : 1
- **Tickets** : initial-seed
- **Promu** : false

### LESSON-034 : Element existant renomme
- **Type** : naming
- **Projet** : axenr-app
- **Erreur** : Renommer un panel, action ou champ existant (ex: `extraPanel` → `technicalSpecsPanel`)
- **Correction** : Ne JAMAIS renommer un element existant. Les extensions qui y font reference par nom seront cassees
- **Occurrences** : 1
- **Tickets** : initial-seed
- **Promu** : false

---

## ERREURS I18N

### LESSON-035 : Cle ajoutee dans messages.csv manuellement
- **Type** : i18n
- **Projet** : axenr-app
- **Erreur** : Ajouter manuellement une cle dans `messages.csv`. Ce fichier est GENERE par `./gradlew i18n`
- **Correction** : Ajouter le title en anglais dans le domain, lancer `./gradlew i18n`, puis ajouter la traduction FR dans `messages_fr.csv`
- **Occurrences** : 1
- **Tickets** : initial-seed
- **Promu** : false

### LESSON-036 : Doublon de traductions
- **Type** : i18n
- **Projet** : axenr-app
- **Erreur** : Creer 2 cles similaires (`"View Equipment"` ET `"View Equipments"`) au lieu d'une seule
- **Correction** : Verifier les cles existantes dans les fichiers i18n AVANT de creer une nouvelle cle. Harmoniser sur un seul libelle
- **Occurrences** : 1
- **Tickets** : initial-seed
- **Promu** : false

### LESSON-037 : custom_fr.csv pour cle presente dans le code
- **Type** : i18n
- **Projet** : axenr-app
- **Erreur** : Ajouter dans `custom_fr.csv` une cle qui est deja dans le code source
- **Correction** : `custom_fr.csv` est UNIQUEMENT pour les cles NON presentes dans le code (labels dynamiques, donnees importees). Les cles du code vont dans `messages_fr.csv`
- **Occurrences** : 1
- **Tickets** : initial-seed
- **Promu** : false

### LESSON-061 : Editer messages_fr.csv AVANT d'avoir lance ./gradlew i18n
- **Type** : i18n
- **Projet** : axenr-app
- **Erreur** : Editer `messages_fr.csv` pour ajouter une traduction SANS avoir lance `./gradlew i18n` d'abord. La nouvelle cle n'existe pas encore dans le fichier
- **Correction** : Workflow OBLIGATOIRE : 1) Ajouter le champ/message avec cle EN dans le code 2) Lancer `./gradlew i18n -p modules/axenr` 3) Verifier que la cle apparait dans `messages.csv` 4) PUIS editer `messages_fr.csv` pour la traduction FR
- **Occurrences** : 1
- **Tickets** : confirmed-by-dev
- **Promu** : false

---

## ERREURS SCOPE TICKET

### LESSON-062 : Supprimer du code existant (doublons inclus)
- **Type** : view
- **Projet** : both
- **Erreur** : Supprimer du code existant lors d'un ticket, meme s'il semble inutile ou en doublon (ex: supprimer un `<field>` en double, supprimer une action obsolete, supprimer un import inutilise)
- **Correction** : Ne JAMAIS supprimer du code existant. Le ticket doit contenir UNIQUEMENT les ajouts/modifications demandes. Les doublons existants sont laisses en l'etat. Seul un ticket de nettoyage dedie peut supprimer du code
- **Occurrences** : 1
- **Tickets** : confirmed-by-dev
- **Promu** : false

### LESSON-063 : Modifier du code non demande par le ticket
- **Type** : view
- **Projet** : both
- **Erreur** : Profiter d'un ticket pour renommer des elements, corriger des doublons, refactorer du code voisin, nettoyer des imports, harmoniser des conventions dans des fichiers non concernes par le ticket
- **Correction** : Le commit doit contenir STRICTEMENT ce que le ticket demande. Aucun renommage, aucun nettoyage, aucune correction hors scope. Si un probleme est detecte, le signaler au dev sans le corriger
- **Occurrences** : 1
- **Tickets** : confirmed-by-dev
- **Promu** : false

---

## ERREURS REST

### LESSON-038 : @Path sans slash initial
- **Type** : rest
- **Projet** : axenr-app
- **Erreur** : Ecrire `@Path("aos/xxx/")` sans slash initial et avec trailing slash
- **Correction** : Toujours `@Path("/aos/xxx")` avec slash initial, sans trailing slash
- **Occurrences** : 1
- **Tickets** : initial-seed
- **Promu** : false

### LESSON-039 : ResponseConstructor pour HTML
- **Type** : rest
- **Projet** : axenr-app
- **Erreur** : Utiliser `ResponseConstructor.build()` pour retourner du HTML
- **Correction** : Utiliser `Response.ok(content).header("Content-Type", "text/html; charset=UTF-8").build()` pour HTML. `ResponseConstructor` est pour JSON
- **Occurrences** : 1
- **Tickets** : initial-seed
- **Promu** : false

---

## ERREURS MOBILE

### LESSON-040 : Hook dans une condition
- **Type** : mobile
- **Projet** : axenr-mobile
- **Erreur** : Utiliser un hook React (`useSelector`, `useState`, etc.) a l'interieur d'une condition ou boucle
- **Correction** : Les hooks doivent TOUJOURS etre au top level du composant, jamais dans des conditions ou boucles
- **Occurrences** : 1
- **Tickets** : initial-seed
- **Promu** : false

### LESSON-041 : Fonctions inline dans les props
- **Type** : mobile
- **Projet** : axenr-mobile
- **Erreur** : Passer des fonctions anonymes inline dans les props (`renderItem={({ item }) => ...}`)
- **Correction** : Utiliser `useCallback` pour memoiser les fonctions et les passer par reference
- **Occurrences** : 1
- **Tickets** : initial-seed
- **Promu** : false

### LESSON-042 : Texte en dur sans i18n
- **Type** : mobile
- **Projet** : axenr-mobile
- **Erreur** : Ecrire `<Text>Validate</Text>` avec du texte en dur
- **Correction** : Utiliser `const I18n = useTranslator(); <Text>{I18n.t('Hr_Validate')}</Text>` avec le format `{Module}_{Action}`
- **Occurrences** : 1
- **Tickets** : initial-seed
- **Promu** : false

---

## ERREURS MIGRATION

### LESSON-043 : Script SQL non idempotent
- **Type** : migration
- **Projet** : axenr-app
- **Erreur** : Ecrire un script SQL qui echoue s'il est execute 2 fois (ex: `ALTER TABLE ADD COLUMN` sans `IF NOT EXISTS`)
- **Correction** : Toujours ecrire des scripts idempotents : `ADD COLUMN IF NOT EXISTS`, `ON CONFLICT DO NOTHING`, `WHERE NOT EXISTS`
- **Occurrences** : 1
- **Tickets** : initial-seed
- **Promu** : false

### LESSON-044 : Champ Studio supprime au lieu de transforme
- **Type** : migration
- **Projet** : axenr-app
- **Erreur** : Supprimer un champ Studio (`DELETE FROM meta_json_field`) au lieu de le transformer
- **Correction** : RENOMMER le champ avec UPDATE, garder `model_field='attrs'`, renommer la cle dans le JSON attrs, mettre a jour meta_view_custom
- **Occurrences** : 1
- **Tickets** : initial-seed
- **Promu** : false

---

## ERREURS CODE SENIOR

### LESSON-045 : Switch verbeux remplacable par expression
- **Type** : java
- **Projet** : axenr-app
- **Erreur** : Ecrire un switch de 20 lignes pour convertir un enum en string quand une expression directe suffit
- **Correction** : Utiliser `dayOfWeek.name().toLowerCase(Locale.ROOT)` au lieu d'un switch. Exploiter les APIs Java natives
- **Occurrences** : 1
- **Tickets** : initial-seed
- **Promu** : false

### LESSON-046 : if/else imbrique au lieu de stream
- **Type** : java
- **Projet** : axenr-app
- **Erreur** : Boucle for + if/else imbrique pour chercher dans une liste et extraire une valeur
- **Correction** : Utiliser `list.stream().filter(...).findFirst().map(...).orElse(default)` avec Optional
- **Occurrences** : 1
- **Tickets** : initial-seed
- **Promu** : false

### LESSON-047 : Locale.ROOT manquant sur toLowerCase/toUpperCase
- **Type** : java
- **Projet** : axenr-app
- **Erreur** : Appeler `str.toLowerCase()` sans `Locale.ROOT`, causant des bugs potentiels en locale turque
- **Correction** : Toujours utiliser `str.toLowerCase(Locale.ROOT)` ou `str.toUpperCase(Locale.ROOT)`
- **Occurrences** : 1
- **Tickets** : initial-seed
- **Promu** : false

---

## ERREURS GIT

### LESSON-048 : Branche creee depuis mauvaise base
- **Type** : build
- **Projet** : both
- **Erreur** : Creer une branche sans verifier qu'on est sur la bonne branche de base (ex: creer depuis une branche de ticket au lieu de dev)
- **Correction** : Toujours `git checkout <base> && git pull origin <base>` AVANT de creer la nouvelle branche
- **Occurrences** : 1
- **Tickets** : initial-seed
- **Promu** : false

### LESSON-049 : Submodule et parent sur branches differentes
- **Type** : build
- **Projet** : axenr-app
- **Erreur** : Le submodule `modules/axenr` et le repo parent `axenr-app` ne sont pas sur la meme branche
- **Correction** : Les 2 repos DOIVENT avoir la meme branche. Synchroniser le submodule PUIS le parent, dans cet ordre
- **Occurrences** : 1
- **Tickets** : initial-seed
- **Promu** : false

### LESSON-050 : Action existante supprimee
- **Type** : view
- **Projet** : axenr-app
- **Erreur** : Supprimer une action existante pour la remplacer par une nouvelle
- **Correction** : GARDER l'ancienne action ET ajouter la nouvelle. D'autres boutons/menus peuvent referencer l'ancienne
- **Occurrences** : 1
- **Tickets** : initial-seed
- **Promu** : false

---

## ANTI-PATTERNS ENR (coherence metier)

### LESSON-051 : Nommage PV-specifique (ENR-AP-01)
- **Type** : enr
- **Projet** : axenr-app
- **Erreur** : Nommer un champ/classe avec des termes PV-specifiques (`solar`, `panel`, `module`, `onduleur`, `string`) sans contexte generique. Ex: `PvInstallationService`, `numberOfModules`, `inverterCapacity`
- **Correction** : Utiliser des termes generiques (`EnrInstallationService`, `numberOfEquipments`, `mainEquipmentCapacity`) ou ajouter un qualifieur de type ENR
- **Occurrences** : 1
- **Tickets** : initial-seed
- **Promu** : false

### LESSON-052 : Bouton/action sans garde de lifecycle (ENR-AP-02)
- **Type** : enr
- **Projet** : axenr-app
- **Erreur** : Bouton ou action visible a toutes les etapes du cycle commercial sans condition `hideIf`/`readonlyIf` basee sur `statusSelect`. Ex: bouton "Generer facture" visible en PROSPECTION
- **Correction** : Ajouter `hideIf="statusSelect &lt; N"` ou `readonlyIf="statusSelect != N"` selon l'etape appropriee du cycle ENR (PROSPECTION=1, QUALIFICATION=2, DEVIS=3, PASSATION_BE=4, ADMINISTRATIF=5, PLANIFICATION=6, APPROVISIONNEMENT=7, CHANTIER=8, MISE_EN_SERVICE=9, FACTURATION=10, DOE_SAV=11)
- **Occurrences** : 1
- **Tickets** : initial-seed
- **Promu** : false

### LESSON-053 : Seuil metier hardcode PV-specifique (ENR-AP-03)
- **Type** : enr
- **Projet** : axenr-app
- **Erreur** : Hardcoder des seuils PV-specifiques comme magic numbers : `9` (kWc autoconsommation), `36` (kWc seuil moyen), `100` (kWc seuil grande puissance). Ex: `if (power > 9)`
- **Correction** : Utiliser l'entite `AxenrConfig` avec une cle par type ENR. Ex: `axenrConfig.getThreshold(enrType)` au lieu du magic number
- **Occurrences** : 1
- **Tickets** : initial-seed
- **Promu** : false

### LESSON-054 : Acces donnees d'une etape future (ENR-AP-04)
- **Type** : enr
- **Projet** : axenr-app
- **Erreur** : Acceder a un champ qui n'existe pas encore a l'etape courante du cycle. Ex: lire `installationDate` en PROSPECTION (disponible seulement apres PLANIFICATION), lire `consuelRef` en DEVIS (disponible apres ADMINISTRATIF)
- **Correction** : Garder chaque acces par une verification de l'etape (`statusSelect >= N`) et ajouter du null-safety sur les champs dependants de l'etape
- **Occurrences** : 1
- **Tickets** : initial-seed
- **Promu** : false

### LESSON-055 : Service monolithique ENR (ENR-AP-05)
- **Type** : enr
- **Projet** : axenr-app
- **Erreur** : Un seul service qui gere tous les types ENR avec des if/else massifs. Ex: `if (type == PV) { ... } else if (type == PAC) { ... } else if (type == IRVE) { ... }`
- **Correction** : Utiliser le pattern Strategy avec une interface generique et une implementation par type ENR. Ou utiliser le polymorphisme avec une factory
- **Occurrences** : 1
- **Tickets** : initial-seed
- **Promu** : false

### LESSON-056 : Selection non extensible aux nouveaux types ENR (ENR-AP-06)
- **Type** : enr
- **Projet** : axenr-app
- **Erreur** : Selection hardcodee qui ne couvre que certains types ENR ou qui ne permet pas d'en ajouter. Ex: selection avec uniquement "Rooftop PV" et "Ground mount PV"
- **Correction** : Utiliser une table de reference configurable au lieu d'une selection hardcodee, ou inclure des options pour TOUS les types ENR (PV, PAC, IRVE, eolien, geothermie, biomasse, solaire thermique)
- **Occurrences** : 1
- **Tickets** : initial-seed
- **Promu** : false

### LESSON-057 : Calcul prime/subvention manquant (ENR-AP-07)
- **Type** : enr
- **Projet** : axenr-app
- **Erreur** : Code de facturation ou de devis qui ne prend pas en compte les subventions energetiques (MaPrimeRenov, CEE, prime autoconsommation)
- **Correction** : Ajouter un hook de calcul de prime/subvention dans le workflow de devis et facturation. Les primes varient par type ENR
- **Occurrences** : 1
- **Tickets** : initial-seed
- **Promu** : false

### LESSON-058 : Unite PV-specifique (ENR-AP-08)
- **Type** : enr
- **Projet** : axenr-app
- **Erreur** : Utiliser `kWc` (kilowatt-crete) comme unite universelle alors que c'est specifique au PV. Les PAC utilisent `COP`, l'IRVE utilise `kW`, le thermique utilise `kWth`
- **Correction** : Utiliser une unite generique avec conversion par type ENR, ou stocker l'unite dans une table de reference liee au type ENR
- **Occurrences** : 1
- **Tickets** : initial-seed
- **Promu** : false

### LESSON-059 : Contraintes site ignorees par type ENR (ENR-AP-09)
- **Type** : enr
- **Projet** : axenr-app
- **Erreur** : Pas de verification des contraintes specifiques au site pour chaque type ENR. Ex: PV necessite orientation/inclinaison toiture, PAC necessite distance voisins, IRVE necessite puissance electrique disponible
- **Correction** : Ajouter une validation de site parametree par type ENR dans l'etape QUALIFICATION
- **Occurrences** : 1
- **Tickets** : initial-seed
- **Promu** : false

### LESSON-060 : Planning sans consideration saisonniere (ENR-AP-10)
- **Type** : enr
- **Projet** : axenr-app
- **Erreur** : Planification de chantier sans prendre en compte les contraintes meteo/saison. Ex: installation PV en toiture en plein hiver, PAC geothermie avec sol gele
- **Correction** : Ajouter un hook de planification meteo-aware dans l'etape PLANIFICATION, avec des contraintes configurables par type ENR et region
- **Occurrences** : 1
- **Tickets** : initial-seed
- **Promu** : false

### LESSON-064 : Colonne NOT NULL fantome heritee d'un module AOS
- **Type** : migration
- **Projet** : axenr-app
- **Erreur** : Quand un module AOS (ex: axelor-template 2.6 -> 2.7) supprime un champ `required="true"` d'une entite, `db.ddl=update` ne supprime jamais la colonne ni la contrainte NOT NULL. Toute instance dont le schema precede la migration de cleanup voit ses inserts echouer avec `null value in column "X" violates not-null constraint` alors que le champ n'existe plus dans le code
- **Correction** : Ecrire une migration defensive idempotente qui (1) verifie l'existence de la colonne via `information_schema.columns`, (2) `ALTER COLUMN ... DROP NOT NULL`, puis (3) `DROP COLUMN IF EXISTS`. Encapsuler dans un bloc `DO $$ ... END $$` PostgreSQL pour la branchement conditionnel. Reproductible pour tout module AOS ayant subi un retrait de champ required
- **Occurrences** : 1
- **Tickets** : #1009
- **Promu** : false

### LESSON-065 : Scope-leak config/secret dans un bump de versions
- **Type** : build
- **Projet** : gmao-app
- **Erreur** : Lors d'une migration de versions (bump AOS/AOP dans `gradle.properties` + `libs.versions.toml`), la working tree embarque des modifications hors-perimetre non destinees au ticket, notamment `axelor-config.properties` avec un changement d'`encryption.password` et de port DB. Un `git add -A` les ferait partir dans le commit de bump : pollution d'historique et, pire, rotation d'`encryption.password` destructrice (les donnees chiffrees existantes deviennent illisibles) sans lien avec la migration
- **Correction** : Un commit de bump de versions ne stage QUE les fichiers de versionnage. Faire un staging selectif explicite `git add gradle.properties gradle/libs.versions.toml`, jamais `git add -A`. Tout changement sur `axelor-config.properties` (secret, port, datasource) appartient a un ticket dedie avec plan de migration des donnees chiffrees
- **Occurrences** : 1
- **Tickets** : #1045
- **Promu** : false

---

## DIAGNOSTIC ET IMPUTATION (AOS vs AxENR)

### LESSON-066 : Imputation AOS vs AxENR annoncee sans preuve
- **Type** : diagnostic
- **Projet** : both
- **Erreur** : Annoncer "c'est un bug AxENR" ou "c'est AOS" a partir du symptome, sans avoir etabli quel code s'execute reellement
- **Correction** : Prouver l'imputation avant d'annoncer : chercher le binding Guice dans AxEnrModule/GmaoModule, verifier le jar reellement charge, comparer le bytecode (`javap -constants`, md5 des .class extraits des jars du cache gradle) avec un TEMOIN connu pour valider que la methode de comparaison detecte bien un diff. Confirmer que les numeros de ligne de la stack prod matchent le binaire analyse
- **Occurrences** : 4
- **Tickets** : PE-27, PE-512, PE-523, #1074
- **Promu** : false

### LESSON-067 : Patcher ou forker du code AOS/AOP
- **Type** : diagnostic
- **Projet** : both
- **Erreur** : Quand la cause est dans AOS/AOP, proposer un patch, un fork, une surcharge Guice de contournement ou la reecriture d'un asset livre dans un jar
- **Correction** : On ne touche JAMAIS a AOS/AOP. Livrables autorises : ticket Axelor avec preuve factuelle, explication de la limite au client, solution a cote dans le module custom, remediation de DONNEE si l'etat est corrompu. Etendre une entite AOS via `<extend>` dans un domaine custom n'est PAS toucher a AOS et reste autorise
- **Occurrences** : 3
- **Tickets** : GMAO-91, PE-27, PE-523
- **Promu** : false

### LESSON-068 : Libelle d'erreur AOS pris au pied de la lettre
- **Type** : diagnostic
- **Projet** : both
- **Erreur** : Suivre la piste que suggere le message d'erreur AOS au lieu de lire le predicat reel du controle. `checkSpecialAccountAmount` parle de comptes Speciaux/Engagements alors qu'il remonte un simple desequilibre global ; `checkStockMin` parle de stocks insuffisants pour une livraison alors qu'il ne teste que `currentQty < 0` sans aucune notion de livraison
- **Correction** : Devant un message AOS, aller lire la methode qui le leve et son predicat exact AVANT de partir sur ce qu'il raconte. Un id present dans le message peut etre un id technique rollbacke, pas un numero de sequence
- **Occurrences** : 2
- **Tickets** : PE-512, PE-523
- **Promu** : false

### LESSON-069 : Fix code sur une erreur de flux AOS standard sans verifier la config
- **Type** : config
- **Projet** : both
- **Erreur** : Ecrire un correctif defensif (Optional, null-check) sur un NPE ou une erreur remontee en demo/prod dans un flux 100% standard, alors que la cause est une ligne de parametrage absente
- **Correction** : Config-first. Verifier dans l'ordre : sequences par societe (`base_sequence`), AppXxx et ses champs default, AccountManagement du mode de paiement ou du type de frais pour la societe, AxenrConfig de la company. Comparer une societe qui fonctionne avec celle qui echoue. Le fix defensif reste legitime, mais en SECONDE intention
- **Occurrences** : 4
- **Tickets** : #1011, PE-512, PE-173, PE-185
- **Promu** : false

### LESSON-070 : Version reelle du jar confondue avec la version declaree
- **Type** : version
- **Projet** : both
- **Erreur** : Raisonner sur `aopVersion` de gradle.properties ou sur `axelorOpenSuite` du libs.versions.toml alors que la resolution transitive charge une autre version (plugin com.axelor.app 7.4.11 resout axelor-core-enterprise 7.4.12)
- **Correction** : Verifier le jar REELLEMENT charge : `ls WEB-INF/lib | grep axelor-core`, ou `unzip -l` sur le jar du cache gradle. Verifier aussi `meta_module.module_version` en base, qui peut rester fige sur l'ancienne version en local
- **Occurrences** : 2
- **Tickets** : PE-518, GMAO-29
- **Promu** : false

### LESSON-071 : Batch qui affiche Reussi alors qu'il ne produit rien
- **Type** : java
- **Projet** : both
- **Erreur** : Conclure qu'un batch fonctionne parce qu'il finit en "Reussi" ou en `done=0 / anomaly=0`. Une exception avalee dans un catch remonte en succes : `NoSuchFileException` avalee cote EBICS, `IllegalArgumentException: Type specified for TypedQuery` avalee dans un fetch
- **Correction** : Un batch qui rapporte 0 traite alors que la donnee est eligible (verifie par le SQL exact du filtre) = chercher l'exception avant de suspecter les donnees. Grep `base_trace_back` du jour. Sur du code custom, ne jamais avaler une exception dans un catch qui laisse le compteur de succes s'incrementer
- **Occurrences** : 2
- **Tickets** : PE-521, GMAO-42
- **Promu** : false

### LESSON-072 : Conclusion tiree en comptant sur la mauvaise table
- **Type** : diagnostic
- **Projet** : both
- **Erreur** : Compter des lignes dans la table au nom evident et conclure que la donnee est absente. Les lignes de releve bancaire sont dans `bankpayment_bank_statement_line_afb120`, pas dans `bankpayment_bank_statement_line` qui est vide
- **Correction** : Avant de conclure a une absence de donnee, verifier que la table interrogee est bien celle qui est alimentee (tables de specialisation, prefixes AOS trompeurs : `bankpayment_bank_order` et non bank_payment_, `account_payment_mode` et non base_payment_mode)
- **Occurrences** : 1
- **Tickets** : PE-521
- **Promu** : false

---

## ENVIRONNEMENT ET BASES DE DONNEES

### LESSON-073 : Base de donnees supposee d'apres son nom
- **Type** : diagnostic
- **Projet** : both
- **Erreur** : Requeter `planeteenr-db` pour un ticket PE parce que le nom correspond, ou `gmao-db` sur le port 5432 alors que les donnees sont dans le conteneur du port 5433. Un vieux snapshot donne des conclusions fausses du type "la donnee est deja nettoyee" alors que la corruption n'y est pas encore
- **Correction** : Avant toute conclusion SQL : `SELECT current_database();` et `SELECT max(created_on) FROM mail_message;` pour verifier la fraicheur, et confirmer que l'affaire du ticket porte bien la donnee. Les dumps prod planeteenr charges en local sont dans `axenr-db`, base par defaut du conteneur `axenr-postgres`
- **Occurrences** : 2
- **Tickets** : PE-499, PE-508
- **Promu** : false

### LESSON-074 : Diagnostic a cheval sur deux environnements
- **Type** : diagnostic
- **Projet** : both
- **Erreur** : Melanger dans une meme analyse le SQL d'une base et les captures d'ecran d'une autre (recette vs prod). Les identifiants d'objets different d'un environnement a l'autre : une seance 40 en prod n'est pas la seance 40 en recette
- **Correction** : Verifier `current_database()` et la version du module AVANT de conclure. Cibler tout script de remediation de facon STRUCTURELLE (predicat sur l'etat), jamais sur des IDs en dur qui ne sont valides que dans un environnement
- **Occurrences** : 2
- **Tickets** : #1074, PE-169
- **Promu** : false

### LESSON-075 : Mutation de la base pour valider un script
- **Type** : process
- **Projet** : both
- **Erreur** : Valider un script SQL en mutant la base, meme en transaction annulee (`BEGIN; UPDATE ...; ROLLBACK;`), sur une base de recette ou partagee
- **Correction** : Valider UNIQUEMENT en lecture seule : rejouer les SELECT et agregats du script prouve deja le comportement. Pour tester une mutation, utiliser une base jetable dediee (copie `pg_dump`), jamais la base sur laquelle tourne l'app
- **Occurrences** : 1
- **Tickets** : #561
- **Promu** : false

### LESSON-076 : UPDATE SQL invisible pour l'application en cours
- **Type** : migration
- **Projet** : both
- **Erreur** : Modifier une donnee en SQL puis tester dans l'application qui tourne : le cache L2 Hibernate sert l'ancienne valeur, la fonctionnalite refuse en silence et on croit a un bug
- **Correction** : Apres tout UPDATE SQL sur des donnees deja chargees, redemarrer l'application ou choisir un enregistrement qui n'est pas en cache. Le noter explicitement dans toute remediation SQL livree
- **Occurrences** : 2
- **Tickets** : #1137, PE-169
- **Promu** : false

### LESSON-077 : encryption.password absent sur une instance locale
- **Type** : build
- **Projet** : both
- **Erreur** : Lancer une instance locale sur un dump AxENR sans `encryption.password` dans `axelor-config.properties` : l'AttributeConverter leve `PersistenceException`, la boucle d'installation des modules s'INTERROMPT, `meta_module` reste absent pour le module custom, aucune vue n'est importee. L'application repond quand meme en HTTP 200, donc le symptome ressemble a "mon code n'est pas deploye"
- **Correction** : Renseigner la cle locale dans `axelor-config.properties` de CHAQUE worktree (un worktree cree depuis origin repart de la valeur du depot). Ne JAMAIS committer ce fichier. Si les modules semblent absents, verifier `meta_module` avant de suspecter le code
- **Occurrences** : 2
- **Tickets** : AR-538, #561
- **Promu** : false

---

## BUILD ET CLASSLOADER (mode dev standalone)

### LESSON-078 : Test lance sur un build incremental
- **Type** : build
- **Projet** : both
- **Erreur** : Retester dans l'application apres une edition de source avec un build incremental. Les modules custom regenerent des entites AOS, donc des classes en double sur deux classloaders : `IllegalArgumentException: Type specified for TypedQuery [com.axelor.meta.db.MetaSelectItem] ... ParallelWebappClassLoader`. Vaut aussi pour une simple vue XML
- **Correction** : Apres TOUTE edition de source, clean rebuild avant de retester : supprimer physiquement les dossiers build puis `./gradlew clean generateCode copyWebapp build`. Verifier le boot propre : `grep "Type specified for TypedQuery" run.log` doit etre vide. Absent en prod (WAR = classloader unique), donc ne jamais remonter cette erreur comme un bug produit
- **Occurrences** : 4
- **Tickets** : #1143, #561, PE-508, GMAO-42
- **Promu** : false

### LESSON-079 : rm -rf annule par un glob zsh sans correspondance
- **Type** : build
- **Projet** : both
- **Erreur** : `rm -rf build modules/*/build .gradle modules/*/.gradle` n'efface RIEN si un seul glob n'a aucune correspondance : zsh applique `nomatch` et abandonne la commande entiere. Le build suivant est incremental et l'erreur classloader revient alors qu'on croit avoir clean. Indice : un clean anormalement rapide
- **Correction** : Utiliser une forme sure puis VERIFIER : `find . -maxdepth 3 -type d \( -name build -o -name .gradle \) -exec rm -rf {} + 2>/dev/null` suivi du meme `find` sans `-exec`, qui doit ne rien afficher. Ne jamais supposer qu'un `rm` est passe
- **Occurrences** : 1
- **Tickets** : AR-538
- **Promu** : false

### LESSON-080 : App BPM laissee active en local
- **Type** : build
- **Projet** : both
- **Erreur** : Chercher un correctif de code a l'erreur classloader alors que le declencheur deterministe est le listener `GlobalEntityListener.onPostPersistOrUpdate` du BPM studio, qui relance une requete sur un thread au contextClassLoader different apres chaque commit
- **Correction** : En local, `UPDATE studio_app SET active=false WHERE code='bpm';` + restart : le log affiche "BPM app is not installed or not active, skipping process engine initialization" et les saves passent. Reglage LOCAL et reversible, jamais pousse : en prod le BPM reste actif, le bug n'y existe pas
- **Occurrences** : 2
- **Tickets** : #1143, #561
- **Promu** : false

### LESSON-081 : Cle Guice deja bindee par AOS re-bindee
- **Type** : java
- **Projet** : both
- **Erreur** : Binder une classe deja bindee par un module AOS (ex `bind(ContractServiceImpl.class)` deja fait par axelor-intervention) : "binding already configured", crash au lancement
- **Correction** : Binder le MAILLON COURANT de la chaine d'heritage, pas une cle deja prise en amont. Sur un patch temporaire, cibler les sous-classes du module le plus specialise (bank-payment) plutot que les classes account deja bindees
- **Occurrences** : 2
- **Tickets** : GMAO, #1074
- **Promu** : false

---

## META, VUES ET I18N SUR BASE EXISTANTE

### LESSON-082 : Traduction corrigee dans le CSV et supposee appliquee au reboot
- **Type** : i18n
- **Projet** : both
- **Erreur** : Modifier une valeur dans `messages_fr.csv` et attendre qu'elle remplace la traduction existante au redemarrage. L'import i18n Axelor est insert-only et delta-tracke : il n'insere que les cles NOUVELLES. Piege supplementaire : DELETE des lignes `meta_translation` + restart ne force PAS le reimport
- **Correction** : Sur base fraiche et en prod le CSV s'importe correctement, ce n'est pas un bug de code. Sur un dump : UPDATE de la ligne existante, ou INSERT via `nextval('meta_translation_seq')`, puis restart SANS re-editer le CSV. Si le CSV doit changer, clean rebuild d'abord sinon le jar perime rejoue les vieilles valeurs
- **Occurrences** : 1
- **Tickets** : #561
- **Promu** : false

### LESSON-083 : Reimport des vues attendu d'un simple run ou d'un bump de version
- **Type** : view
- **Projet** : both
- **Erreur** : Attendre qu'un `./gradlew run` ou qu'un changement de `meta_module.module_version` reimporte les vues d'un module deja installe. Aucun des deux ne marche. DELETE des lignes `meta_view` seules ne les fait pas revenir non plus (0 ligne, formulaire casse)
- **Correction** : Seul trigger fiable en local : `DELETE FROM meta_module_depends; DELETE FROM meta_module;` + restart, ce qui declenche un install complet. Ajouter `DELETE FROM meta_view WHERE name IN (...)` pour les vues changees, l'install etant insert-only lui aussi. Attention a la bonne vue : les relabels Affaire vivent dans `business-project-form`, pas `project-form`
- **Occurrences** : 3
- **Tickets** : GMAO-26, #561, #1130
- **Promu** : false

### LESSON-084 : Script SQL de reimport de vues livre au client
- **Type** : migration
- **Projet** : both
- **Erreur** : Livrer un script SQL de reimport de vues (DELETE meta_view + DELETE meta_module) dans une PR. La procedure d'integration AxENR passe deja par Administration > Vues > Restaurer toutes les vues
- **Correction** : Livrer le code seul. `ViewLoader.importView` ignore une vue existante quand `update=false`, ce qui est le cas AU BOOT uniquement ; le bouton Restaurer appelle `ModuleManager.restoreMeta()` avec `update=true` et reecrit bien les vues. Une restauration ne perd pas les roles menu (`importMenu` ne touche pas aux roles). Si une etape base est vraiment necessaire, la livrer en disant explicitement pourquoi la regeneration manuelle ne suffit pas
- **Occurrences** : 1
- **Tickets** : AR-534
- **Promu** : false

### LESSON-085 : Vue d'extension sans attribut title
- **Type** : view
- **Projet** : both
- **Erreur** : Ecrire un `<form extension="true">` ou un `<grid>` d'extension sans attribut `title` : le XSD runtime rejette le fichier ENTIER au boot (`cvc-complex-type.4: Attribute 'title' must appear`), toutes les vues du fichier tombent, et AOP purge ensuite les computed views
- **Correction** : Toujours mettre `title` sur les `<form>` et `<grid>` d'extension. `./gradlew checkXmlViewsAttributes` ne detecte PAS ce manque : seul l'unmarshalling au demarrage le voit, donc verifier le log de boot
- **Occurrences** : 1
- **Tickets** : #1130
- **Promu** : false

### LESSON-086 : Selection etendue sans id unique
- **Type** : view
- **Projet** : both
- **Erreur** : Ajouter une `<selection>` portant le nom d'une selection existante d'un autre module sans lui donner d'`id` unique : "Duplicate Selection found without id" au boot
- **Correction** : Toute `<selection>` qui reprend le nom d'une selection existante (ex ajouter Minute a `base.duration.type.select`) DOIT porter un `id` unique
- **Occurrences** : 1
- **Tickets** : #1139
- **Promu** : false

---

## MONTEE DE VERSION

### LESSON-087 : Montee de version sans les trois controles obligatoires
- **Type** : version
- **Projet** : both
- **Erreur** : Bumper une version AOS sans verifier les 3 casses recurrentes : (1) constructeurs des `*Impl` AOS modifies alors que nos services appellent `super(...)` (axenr = 26 classes concernees, gmao = 3) ; (2) entite AOS renommee qui laisse des meta_menu/meta_action/meta_view orphelines (ClassNotFoundException au clic) ; (3) colonne ajoutee non creee en base (column does not exist a toute lecture de l'entite)
- **Correction** : Passer les 3 controles AVANT de livrer : `:modules:<mod>:compileJava` sur la nouvelle version ; `comm -23` des classes `/db/*.class` des jars avant/apres ; diff des colonnes `information_schema.columns` entre une base saine et la prod. Fixes : aligner les `super(...)` sur la nouvelle signature (`javap` sur le jar), script de nettoyage meta (ordre FK meta_menu_roles puis meta_menu, meta_action, meta_view), `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`. Bumper UN module enterprise cascade sur les autres
- **Occurrences** : 3
- **Tickets** : GMAO-29, AR-521, PE-511
- **Promu** : false

### LESSON-088 : meta_module.module_version fige apres un bump en local
- **Type** : version
- **Projet** : both
- **Erreur** : Croire qu'un bump est reellement pris en compte en local : apres `./gradlew run`, le code est en 8.5.22 mais `meta_module.module_version` reste a l'ancienne version, le pass `ModuleManager.update` ne tournant pas sur une base existante
- **Correction** : En prod ou en WAR le changement de version declenche le reimport automatique. Pour tester en local il faut FORCER : `DELETE FROM meta_module_depends; DELETE FROM meta_module;` + restart, puis verifier que `meta_module` porte la nouvelle version
- **Occurrences** : 1
- **Tickets** : GMAO-29
- **Promu** : false

### LESSON-089 : Ligne du version-matcher recopiee sans verifier le transitif
- **Type** : version
- **Projet** : both
- **Erreur** : Recopier une version proposee par version-matcher.axelor.com sans verifier ce que la chaine resout reellement. Sa ligne `file-generator = 8.2.8` est inexploitable en pratique : elle depend de base 8.1.0 / core 7.1.0, alors que facturx, cii et e-invoicing 8.10.4 exigent file-generator 8.10.4 en transitif
- **Correction** : Traiter le version-matcher comme une indication, pas comme une verite. Verifier les dependances transitives reelles des modules enterprise cibles. L'API JSON derriere la SPA est interrogeable : `/api/versions`, `/api/compatibility/<aos>`, `/api/modules`, `/api/reverse/`
- **Occurrences** : 1
- **Tickets** : AR-526
- **Promu** : false

### LESSON-090 : Release enterprise adoptee sans test en mode dev
- **Type** : version
- **Projet** : both
- **Erreur** : Integrer une release enterprise sans la booter en `./gradlew run`. La release 8.10.0 (e-invoicing, data-capture, file-generator) est cassee en mode dev sur AOP 7.4.10 : ses jars embarquent des entites `com.axelor.meta` compilees contre core 7.3.4, qui collisionnent sous le classloader splitte, plus une extension de vue ciblant un panel inexistant
- **Correction** : Booter la release en mode dev avant de l'annoncer integrable, et reproduire sur un second repo pour distinguer la version de l'environnement. Ne pas livrer une dependance SNAPSHOT en "integration image" : une release stable est exigee, meme si elle doit etre demandee a Axelor
- **Occurrences** : 1
- **Tickets** : #1127
- **Promu** : false

### LESSON-091 : Donnees de correspondance supposees livrees par data-init
- **Type** : version
- **Projet** : both
- **Erreur** : Supposer que des tables de reference d'un module enterprise arrivent par init-data ou demo-data a l'installation de l'app. Les modules Factur-X et CII ne sont pas des apps, n'ont aucun `apps/demo-data/`, et n'ont pas d'`apps/init-data/` avant la ligne 8.11.x : le chargement passe obligatoirement par les boutons d'import
- **Correction** : Verifier dans le JAR ce qu'il contient reellement (`apps/*.yml`, `apps/init-data/`, `apps/demo-data/`) avant de promettre un chargement automatique. Verifier aussi les prerequis d'activation (un champ peut rester readonly tant qu'une autre app n'est pas installee)
- **Occurrences** : 1
- **Tickets** : AR-526
- **Promu** : false

---

## PAGINATION ET BATCHS

### LESSON-092 : Consolidation et envoi a l'interieur de la boucle de pagination
- **Type** : java
- **Projet** : both
- **Erreur** : Consolider par client puis envoyer le mail DANS la boucle `query.fetch(FETCH_LIMIT, offset)` (FETCH_LIMIT=10) et sans `.order()`. Une page melange tous les clients : un client a cheval sur une frontiere de page recoit un mail par page. Le symptome ressemble a un double declenchement du scheduler, ce n'en est pas un
- **Correction** : Accumuler des IDs sur TOUTES les pages, puis envoyer apres la boucle. Ajouter `.order("id")` pour une pagination deterministe
- **Occurrences** : 1
- **Tickets** : PE-508
- **Promu** : false

### LESSON-093 : Entite detachee utilisee apres la boucle de pagination
- **Type** : java
- **Projet** : both
- **Erreur** : Reutiliser une entite chargee avant la boucle (template de mail, configuration) apres celle-ci : `JPA.clear()` entre les pages l'a detachee
- **Correction** : Re-fetch par id juste avant l'usage (`templateRepo.find(template.getId())`), comme le fait le batch de reference du meme module
- **Occurrences** : 1
- **Tickets** : PE-508
- **Promu** : false

### LESSON-094 : Offset qui avance sur un jeu de resultats qui retrecit
- **Type** : java
- **Projet** : both
- **Erreur** : Paginer avec `offset += size` sur un filtre que la boucle elle-meme modifie : chaque element traite quitte le filtre, le jeu retrecit, l'offset avance quand meme et des elements ne sont JAMAIS traites. Sur une session de paiement, des echeances cochees sont silencieusement sautees et l'ordre bancaire genere est incomplet
- **Correction** : Ne jamais paginer par offset sur un jeu que la boucle modifie : parcourir par seek (`id > :lastSeenId`), ou collecter d'abord tous les IDs puis traiter. Sur un flux AOS, le contournement fonctionnel est de rester sous le FETCH_LIMIT et d'ouvrir un ticket editeur
- **Occurrences** : 1
- **Tickets** : #1074
- **Promu** : false

### LESSON-095 : Batch custom qui perd les garde-fous du standard AOS
- **Type** : java
- **Projet** : both
- **Erreur** : Recopier un batch AOS dans le module custom en perdant ses garde-fous. Le batch de generation de feuilles de temps ne bornait plus sur [fromDate, toDate] et ne testait plus jour ouvre / conge / ferie : un element multi-jours a cheval sur deux semaines generait 12 jours calendaires, week-ends inclus, dans une seule feuille hebdomadaire
- **Correction** : Quand un batch custom double un batch AOS, comparer methode par methode avec le standard et reprendre ses garde-fous. Verifier la regle metier avec le fonctionnel : un total hebdomadaire est celui du planning propre a chaque employe, pas une constante
- **Occurrences** : 1
- **Tickets** : #1128
- **Promu** : false

### LESSON-096 : Planification pointant le service de batch AOS de base
- **Type** : config
- **Projet** : both
- **Erreur** : Une planification dont `meta_schedule.batch_service_select` designe le service AOS de base alors que le batch utilise une action custom : l'action tombe en `default` et le batch plante avec "Unknown action N", alors qu'il fonctionne parfaitement en manuel. Reflexe a tort : suspecter Quartz
- **Correction** : Pour toute planification d'un batch a action CUSTOM, `batch_service_select` doit pointer le service custom. Le run manuel marche car il resout le service via le registre par model class, alors que le job planifie fait `Class.forName(batch_service_select)`. Diagnostic : `base_trace_back` pour le message, les heures de demarrage dans `base_batch` comme proxy du scheduler (Quartz est en RAMJobStore, aucune table qrtz_*), et les logs de boot du JobRunner
- **Occurrences** : 1
- **Tickets** : PE-185
- **Promu** : false

### LESSON-097 : Requete SQL keyee sur un libelle accentue
- **Type** : migration
- **Projet** : both
- **Erreur** : Keyer un UPDATE ou un SELECT sur un libelle accentue : selon le `client_encoding` de psql, la requete matche 0 ligne SILENCIEUSEMENT et le script parait avoir tourne
- **Correction** : Keyer sur un code ASCII stable (`batch_code`, `code_select`, `name` technique), jamais sur un libelle affiche. Verifier le nombre de lignes touchees
- **Occurrences** : 1
- **Tickets** : PE-185
- **Promu** : false

---

## TRANSACTIONS ET MOBILE

### LESSON-098 : Proxy lazy lu apres une methode transactionnelle sur le chemin REST
- **Type** : java
- **Projet** : both
- **Erreur** : Lire un proxy paresseux (`stockMove.getCompany().getAxenrConfig()`) APRES l'appel a une methode AOS `@Transactional` qui possede l'unite de travail. Sur le chemin REST mobile (controleur non transactionnel, pas d'OSIV), la session est fermee : HTTP 500 "could not initialize proxy - no Session". Le desktop ne le voit pas. AOS evite le piege en ne lisant que des scalaires
- **Correction** : Envelopper le bloc concerne dans `JPA.runInTransaction(() -> ...)` avec rechargement de l'entite par id. Ne pas poser `@Transactional` sur la methode elle-meme (piege d'auto-invocation Guice). Repro : `StockMoveRepository.TYPE_INCOMING = 3`, pas 1
- **Occurrences** : 1
- **Tickets** : #1123
- **Promu** : false

### LESSON-099 : hideIf combine a un widget custom sur mobile
- **Type** : mobile
- **Projet** : axenr-mobile
- **Erreur** : Mettre un `hideIf` sur un champ `widget: 'custom'` dans `models/forms.ts` : redbox "Rendered more hooks than during the previous render". `Field.tsx` appelle le composant comme une simple fonction, donc ses hooks appartiennent a `Field`, et `Field` fait `if (isHidden) return null` AVANT de l'appeler. Le premier rendu se fait sur un objet vide, donc tout `hideIf` base sur le record bascule
- **Correction** : Isoler le composant derriere une vraie frontiere React : un wrapper `React.createElement(component, props)` declare dans `forms.ts`. Alternative : pas de `hideIf` et `return null` a la FIN du composant, apres ses hooks. Les widgets non custom sont sans risque
- **Occurrences** : 1
- **Tickets** : GMAO-66
- **Promu** : false

### LESSON-100 : Crash mobile impute au code ou aux permissions
- **Type** : mobile
- **Projet** : axenr-mobile
- **Erreur** : Chercher un bug de code ou un probleme de droits sur un crash "cannot read property 'x' of undefined". Un fetch reseau qui echoue SANS reponse HTTP est avale en `undefined` par `manageError`, le thunk se resout fulfilled avec un payload undefined, et l'ecran dereference sans garde
- **Correction** : Discriminant : "of undefined" = erreur sans response (reseau) ou data vide ; "of null" = 403 ou status -1 (permission, erreur serveur). Verifier la reproductibilite sur reseau stable avant de conclure a un bug. Le fix durable est un hardening upstream (`intervention?.statusSelect`), pas du code AxENR
- **Occurrences** : 1
- **Tickets** : GMAO-66
- **Promu** : false

### LESSON-101 : Repro d'un flux REST mobile tentee en Basic auth
- **Type** : rest
- **Projet** : axenr-mobile
- **Erreur** : Essayer de reproduire un appel REST mobile en Basic auth : refuse (302/401), et on conclut a tort a un probleme de droits
- **Correction** : Passer par session + CSRF : POST `/<context>/callback?client_name=AxelorFormClient` en form-urlencoded, recuperer le cookie et le header `X-CSRF-Token`, puis appeler l'endpoint. Ne pas oublier le context-path
- **Occurrences** : 1
- **Tickets** : #1123
- **Promu** : false

---

## LIVRAISON

### LESSON-102 : Depot de livraison choisi sans identifier le proprietaire du code
- **Type** : build
- **Projet** : axenr-app
- **Erreur** : Livrer via le depot `axenr` (ERP-AxENR/axenr) ou tenter de synchroniser un sous-module. `axenr-app` est un depot UNIQUE : `modules/axenr` y est versionne en fichiers ordinaires sur `dev`, `wip` et `main`, le sous-module ayant ete supprime le 2026-05-16 (commit `cbdcd94`). Une PR sur l'ancien depot ne remonte nulle part. Symetriquement, corriger dans axenr-app du code qui appartient a `fr.gmao` ne produit rien : gmao est la dependance amont `fr.gmao:gmao`, jar produit par le depot gmao-app
- **Correction** : Un seul checkout, un seul pull, un seul depot, dans un `git worktree` isole. Avant de coder, trancher le proprietaire du code fautif : package `fr.axenr` -> livraison axenr-app ; package `fr.gmao` -> livraison gmao-app, puis remontee par bump de la version gmao dans `gradle/libs.versions.toml` (elle differe par branche : wip 2.5.0-SNAPSHOT, dev 1.0.7-SNAPSHOT, donc la lire et ne pas la supposer). Seules des branches anterieures au 2026-05-16 portent encore un `.gitmodules` : sur celles-la, demander au dev
- **Occurrences** : 3
- **Tickets** : #1115, #1123, PE-508

### LESSON-103 : Fichier i18n CRLF edite avec un outil qui normalise les fins de ligne
- **Type** : i18n
- **Projet** : both
- **Erreur** : Editer `messages.csv`, `messages_en.csv` ou `messages_fr.csv` avec un outil qui convertit CRLF en LF : tout le fichier apparait modifie et le diff devient illisible
- **Correction** : Ces fichiers sont en CRLF. Inserer une ligne au `perl -i -pe` en gardant explicitement `\r\n`, jamais avec un outil d'edition qui normalise
- **Occurrences** : 1
- **Tickets** : #1115
- **Promu** : false

### LESSON-104 : Pull Request creee avec un body
- **Type** : process
- **Projet** : both
- **Erreur** : Rediger une description dans la PR (contexte, cause, correctif), meme structuree
- **Correction** : Les PR AxENR se creent SANS body : `gh pr create --base <branche> --title "fix(#TICKET): ..." --body ""`. Le detail va dans le ticket Redmine, coherent avec la regle 1 commit = 1 sous-ticket testable, message court
- **Occurrences** : 1
- **Tickets** : AR-518
- **Promu** : false

### LESSON-105 : Script SQL versionne suppose auto-execute
- **Type** : migration
- **Projet** : both
- **Erreur** : Croire qu'un `.sql` place dans `src/main/scripts/V<version>/` s'execute au demarrage de l'application. Il ne s'execute PAS : merger et deployer la PR ne lance pas le fix, et on conclut a tort que le correctif ne marche pas
- **Correction** : Annoncer explicitement que le script est a lancer A LA MAIN en psql contre la base cible, et fournir la requete de verification qui dit s'il a tourne. Convention : `NN__snake_case.sql` sous la version en cours, idempotent
- **Occurrences** : 1
- **Tickets** : #1059
- **Promu** : false

### LESSON-106 : Script de remediation sans ciblage structurel ni garde-fou
- **Type** : migration
- **Projet** : both
- **Erreur** : Ecrire un script de remediation cible sur des IDs en dur, ou avec un allowlist sur `current_database()` qui le fait refuser de tourner sur l'environnement reel, ou sans borne de volumetrie
- **Correction** : Cibler par PREDICAT sur l'etat, jamais par IDs (ils different par environnement). Garde-fou de volumetrie avant COMMIT, borne UNILATERALE (`IF v_target > N RAISE EXCEPTION`) pour rester idempotent au second passage. Prevoir une table de backup creee dans la meme transaction. Signaler le cache L2 dans la procedure
- **Occurrences** : 2
- **Tickets** : PE-169, #1059
- **Promu** : false

### LESSON-107 : Instance locale laissee tournante apres livraison
- **Type** : process
- **Projet** : both
- **Erreur** : Laisser tourner l'instance locale, le simulateur iOS et Metro apres qu'un test est valide ou qu'un ticket est livre. Huit instances Axelor accumulees sur les ports 8080 a 8087 ont sature la memoire et fait echouer un build iOS par collision sur le port 8081
- **Correction** : En fin de ticket, balayer 8080-8090 (pas seulement le port utilise) : `lsof -nP -iTCP:<port> -sTCP:LISTEN` puis `kill`, `xcrun simctl shutdown <udid>` pour le simulateur. Les daemons Gradle ne sont pas des instances, les laisser expirer. Si un test doit reprendre plus tard, le dire au lieu de laisser tourner
- **Occurrences** : 1
- **Tickets** : AR-573
- **Promu** : false

---

## PERMISSIONS ET DROITS

### LESSON-108 : Permissions analysees sur un garde qui n'en lit aucune
- **Type** : config
- **Projet** : both
- **Erreur** : Analyser le parametrage devant "Vous n'etes pas autorise a modifier cette ressource" sur une fiche Utilisateur. AOP 7.4.12 ajoute dans `Resource` un garde qui refuse 10 champs (code, group, blocked, activateOn, expiresOn, password, passwordUpdatedOn, roles, permissions, metaPermissions) a tout non-admin, SANS lire aucune permission et sans reglage possible. Toute analyse SQL du parametrage repond OK et fait perdre des heures
- **Correction** : Test discriminant en 30 secondes : en non-admin, modifier UNIQUEMENT une date sans lien (Autoriser jusqu'au) et enregistrer. Meme erreur = c'est ce garde. Contournement : passer par un compte admin. Ne PAS basculer les utilisateurs dans le groupe `admins`, ce qui court-circuite toute la securite
- **Occurrences** : 1
- **Tickets** : PE-518
- **Promu** : false

### LESSON-109 : Bouton absent impute a la vue, au cache ou a la donnee
- **Type** : view
- **Projet** : both
- **Erreur** : Chercher dans les vues, le cache serveur ou la donnee pourquoi un bouton n'apparait pas. La condition `hidden` d'un bouton AOS peut porter sur l'utilisateur connecte : `!__user__.employee?.hrManager || statusSelect != 3 || ventilated`. Un compte sans employe lie masque le bouton
- **Correction** : Avant de suspecter la vue ou le cache, lire la condition `hidden` de la meta_action et verifier QUI est connecte et ce que son employe porte. Verifier aussi le domaine du menu emprunte : un menu Mes X filtre sur `self.employee.user`, l'enregistrement d'un autre employe y est invisible
- **Occurrences** : 2
- **Tickets** : PE-512, #1128
- **Promu** : false

### LESSON-110 : Module sans permission data-init teste en admin
- **Type** : config
- **Projet** : both
- **Erreur** : Valider une fonctionnalite en admin alors que le controleur REST fait un `SecurityCheck().readAccess(X)`. AOP est deny-by-default pour les non-admin : si le module n'embarque aucune permission, tout non-admin est refuse (403) et celui qui configure, etant admin, ne voit jamais le bug
- **Correction** : Tester avec un compte du groupe reel de l'utilisateur final, jamais uniquement en admin. Creer les Permission can_read sur les entites exposees et les rattacher au groupe ou role concerne (lu a chaud, pas de reboot)
- **Occurrences** : 1
- **Tickets** : GMAO-mobile
- **Promu** : false
