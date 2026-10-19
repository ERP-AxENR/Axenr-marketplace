# Fermeture des dépendances de vues et d'actions

> Apport d'un chef de projet Axelor (paquet du 15/10/2026). Éprouvé sur AOS 9.1.6 / AOP EE 8.2.3.
> AxENR tourne sur AOP 7.4 / AOS 8.x : à vérifier sur la version cible.

À utiliser quand un menu est visible mais que son ouverture, l'ouverture d'une fiche, un onglet,
un bouton d'information ou une action native renvoie une erreur d'accès. Sert aussi d'audit avant
livraison pour toute liste blanche restrictive. Prolonge le « socle commun » de `conception.md` :
le socle couvre les référentiels lus partout, cette méthode couvre les dépendances propres à
chaque écran et à chaque geste.

## Méthode

Pour chaque menu accordé et chaque profil :

1. **Résoudre l'action du menu.** Une `action-view` expose son modèle directement. Pour une
   `action-method`, lire le contrôleur ou le service et le modèle qu'il renvoie : le XML du menu
   ne suffit pas.
2. **Inspecter le formulaire et toutes ses extensions actives** : objets enfants (x-to-many),
   formulaires référencés, `mail-messages`, widgets de pièces jointes et de GED, dashlets, boutons
   d'information. Une configuration de module peut rendre une extension visible seulement à
   l'exécution.
3. **Inspecter chaque geste métier autorisé**, pas seulement le chargement : Enregistrer, Valider,
   Réaliser, Facturer, Générer, assistants. Le but est de savoir ce que le formulaire recharge et
   renvoie (valeurs imbriquées) et quels modèles d'action s'exécutent, pas d'accorder les écritures
   propres au service : la plupart des services écrivent sans contrôle.
4. **Parent filtré par ligne** : trouver un chemin stable de l'enfant vers le parent, et appliquer
   le prédicat équivalent à la lecture, l'écriture et la suppression de l'enfant. Une lecture
   globale de l'enfant annule le filtre d'agence, de société ou de propriétaire du parent.
5. **Création à part** : la condition est revérifiée sur l'enregistrement principal après
   insertion, mais pas sur les nouveaux enregistrements imbriqués ni sur ceux créés par des
   services (`permissions-conditionnelles.md`). Accorde la création seulement si le flux en a
   besoin, note la limite, et teste un parent ou une portée volontairement faux.
6. **Tester avec un vrai compte** pour chaque profil, caches rechargés, et lire le journal serveur
   pour la classe exacte refusée (`diagnostic.md`). Un test en admin ne prouve rien.
7. **Lire la forme de chaque enregistrement**, pas seulement les modèles. Un éditeur en ligne, un
   `canNew` ou un M2O / O2M modifiable envoient des valeurs imbriquées : sans identifiant, elles
   demandent la création sur la cible ; avec identifiant et version, l'écriture
   (`moteur-evaluation.md`, section 11). Répéter sur le formulaire imbriqué (la ville dans
   l'adresse). Une trace complète de chaque scénario avec un compte tous droits liste ces paires
   en une passe (`cadrage-profils.md`, L13).

## Le mobile est une surface à part

Un profil complet côté menus peut rester inutilisable dans l'application mobile Axelor : le client
mobile appelle directement des ressources REST et des contrôleurs d'action, absents d'un inventaire
fait par les menus. Pour chaque population mobile :

1. Lire les `auth_role.csv` et `auth_permission.csv` livrés dans `axelor-mobile-settings` de la
   version cible (le JAR du WAR déployé si possible). `role.mobile.base` sert de socle, et chaque
   application mobile activée a son rôle.
2. Inspecter le contrôleur ou le service mobile des gestes autorisés. Pour la saisie des temps,
   cela ajoute couramment `AppMobileSettings`, les métadonnées mobiles, `Currency`, l'`Employee`
   courant, le `Product` d'activité, le `Project` personnel, `ProjectTask`, `TSTimer`, `Timesheet`,
   `TimesheetLine` et `AppTimesheet`. Avec la navigation Projet, fermer aussi le jeu de
   dépendances de `role.mobile.project` (statut et priorité de projet, lien et catégorie de tâche,
   statut, version, étiquette, sprint, `AppProject`).
3. **Ne pas attacher un rôle mobile standard à l'aveugle** : ils sont volontairement larges (par
   exemple `role.mobile.hr` accorde aussi des droits globaux sur les notes de frais, congés et
   temps). Reconstruire le sous-ensemble utile avec le prédicat du profil quand le périmètre est
   plus étroit.
4. Vérifier `MobileConfig.authorizedRoles` : les permissions peuvent être justes et la tuile de
   l'application rester masquée parce que le rôle n'est pas autorisé. Conserver l'ensemble
   existant en ajoutant un rôle : le remplacer peut couper l'accès mobile d'autres populations.
5. Jouer le démarrage, la liste, le détail et les modifications avec un compte non admin. Un test
   web réussi ne prouve rien côté mobile.

## Familles de dépendances connues

| Fonction visible / geste | Objets support couramment requis | Point de sécurité |
|---|---|---|
| Menu Calendrier (`calendar.root.menu.my.calendar`) | `ICalendarEvent`, `ICalendar`, `ICalendarUser`, `SharingSetting` ; des adresses e-mail peuvent aussi être rendues | Pour un calendrier personnel, inclure les chemins propriétaire, propriétaire du calendrier, organisateur et participant dans la condition |
| « Mon calendrier » CRM (`action-method`) | `com.axelor.apps.crm.db.Event` et `EventReminder` | Le contrôleur renvoie `Event`, pas l'objet de la racine Calendrier |
| Nouvel événement CRM (`event-form`) | Lecture **et création** sur `com.axelor.apps.base.db.ICalendarEvent` : la première action à l'ouverture est une `action-record` sur ce modèle | Sans elle : « non autorisé à créer », pas de dates par défaut. Une création conditionnée suffit pour l'action (sans identifiant, la condition n'est pas évaluée) ; l'enregistrement de l'événement est ensuite contrôlé avec son nouvel identifiant |
| `<mail-messages>` sur tiers, article, commande d'achat et autres | `MailMessage`, `MailAddress`, `MailFlags`, `MailFollower` ; pièces jointes `MetaAttachment` et `MetaFile` | Chemin du fil de discussion. Limiter la lecture des pièces jointes aux enregistrements autorisés : une lecture globale de `MetaFile` expose des fichiers sans rapport |
| Envoi d'e-mail, modèles d'e-mail, messages sortants | `com.axelor.message.db.Message`, `EmailAddress`, `Template`, `MultiRelated`, et selon le chemin `EmailAccount` | `Message` et `MailMessage` sont deux modèles de packages différents. Déduire les verbes du contrôleur ou du service déployé : générer un brouillon peut demander la création de `Message`, l'envoyer ou modifier un brouillon l'écriture |
| Formulaire, filtres et sélecteurs de tâches d'équipe | `TeamTask` et l'`Team` référencée ; catégories et statuts de tâche selon la version | Une permission sur `TeamTask` seule peut laisser le formulaire partiellement interdit |
| Commande d'achat | `PurchaseOrderLine`, `PurchaseOrderLineTax` | Filtrer par `self.purchaseOrder` ; le recalcul des taxes peut demander création ou écriture sur la taxe |
| Commande de vente | `SaleOrderLine`, `SaleOrderLineTax` | Filtrer par `self.saleOrder` ; pas de permission globale sur les lignes à côté d'une commande filtrée |
| Facture | `InvoiceLine`, `InvoiceLineTax`, parfois `InvoiceNote` / `InvoicePayment` | Filtrer par `self.invoice` |
| Demande d'achat | `PurchaseRequestLine` | Création de l'enfant nécessaire si le parent est modifiable |
| Feuilles de temps, notes de frais, relances | `TimesheetLine`, `ExpenseLine`, `TimesheetReminderLine` ; le menu chronomètre renvoie `TSTimer` | Les menus en `action-method` cachent le modèle renvoyé |
| Contrat | `ContractVersion`, `ContractLine`, `ConsumptionLine`, `InvoicePeriod` | Les lignes atteignent souvent le contrat par `contractVersion` : conserver la condition d'agence ou de société du contrat |
| Boutons d'information stock d'un article | `StockLocation`, `StockLocationLine`, parfois `StockRules` | La lecture suffit pour consulter ; réaliser un mouvement est un autre geste |
| Réaliser un mouvement de stock entrant | Création de `StockMoveLine`, `StockLocationLine` et, dans les flux AOS standard, écriture de `Product` | L'écriture sur `Product` est globale au niveau objet sauf prédicat sûr : à remonter comme arbitrage, pas à accorder en silence |
| Tout assistant | `com.axelor.utils.db.Wizard` : lecture pour toute action, création quand une `action-record` écrit un vrai champ | Un bouton visible peut échouer avant même l'appel du service |
| Création d'un tiers ou d'un contact (AOS 9.1.6) | Création d'`EmailAddress` (éditeur en ligne), création / écriture d'`Address` (`canNew`), création de `PartnerAddress` ; `City` en création seulement si autorisé, lecture de `Country`, `Department`, `Canton` ; `AccountingSituation` en lecture (écriture si l'onglet est modifié, non testé) | `Partner` seul ouvre le formulaire et échoue à l'enregistrement |
| Préférences de l'utilisateur (sa propre fiche) | Écriture sur son propre `User` (`self.id = ?`, `__user__.id`) ; création d'`ICalendar` (`canNew`) ; comptes mail connectés | Le formulaire expose `tradingName` : sur un profil filtré par agence, verrouiller le champ par une règle de champ (à tester) ou ne pas accorder l'écriture |
| Brique workflow AEP | `com.axelor.meta.db.MetaWorkflowTask` quand la classe existe dans la distribution | Vérifier la classe dans l'artefact EE / AEP réel avant d'importer la permission |

Le nom des classes et des actions vient d'AOS 9.1 : sur AOS 8.x, vérifie chaque classe dans
`meta_model.full_name` et chaque action dans `meta_action` avant de l'utiliser.

## La GED n'est pas une dépendance de lecture ordinaire

La GED du cœur crée des permissions conditionnelles à partir des enregistrements `DMSPermission`
et les attache aux utilisateurs ou aux groupes. Les droits s'additionnant, une permission de rôle
sans condition comme `DMSFile = lecture` contourne ces ACL et expose tous les fichiers. Ne l'ajoute
jamais pour faire taire une erreur de formulaire.

Pour les fichiers contextuels, distingue :
- les pièces jointes classiques (`MetaAttachment` + `MetaFile`), limitées à l'objet lié autorisé ;
  une pièce jointe sur `MailMessage`, une sur `com.axelor.message.db.Message` et une sur un objet
  métier sont trois chemins d'autorisation distincts ;
- les dossiers et fichiers de GED : configurer les `DMSPermission` voulues et vérifier les
  permissions conditionnelles générées ;
- un vrai administrateur de la GED : une permission large n'est acceptable que si le périmètre
  métier exige explicitement un accès transverse.

## Preuves minimales avant livraison

- Chaque modèle d'`action-view` accordé a une permission.
- Chaque `action-method` accordée a été inspectée pour le modèle qu'elle renvoie.
- Les enfants agrégés utilisés par les formulaires et les enregistrements sont présents.
- Aucun parent filtré n'a d'enfant lisible sans filtre, sauf raison documentée.
- Messagerie, pièces jointes et GED ont été évaluées séparément ; fil de discussion (`MailMessage`)
  et messages sortants (`Message`) chacun quand le flux les expose.
- Les modèles de relation rendus par les sélecteurs de tâches et d'équipes sont couverts.
- Chaque application mobile autorisée a son inventaire de dépendances, et sa porte
  `MobileConfig.authorizedRoles` a été vérifiée.
- Un parcours non admin a été joué pour chaque profil, journaux lus.
- Les valeurs imbriquées de chaque enregistrement du périmètre sont couvertes.
- Chaque permission est rattachée à un rôle existant : une permission orpheline se crée en
  silence, journal vert compris.
- Après chaque activation d'application, les menus enfants sans groupe ni rôle sous des parents
  visibles ont été revus (`GET /ws/action/menu/all` de chaque profil, avant et après).
- Chaque compte a sa société active et ses sociétés, `blocked = false`, une langue, un employé
  quand un flux RH ou de validation est concerné, et les sièges Guardian (édition entreprise)
  restants ont été vérifiés avant d'ouvrir des comptes.
