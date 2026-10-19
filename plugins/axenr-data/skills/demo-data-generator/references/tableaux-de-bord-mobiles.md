# Tableaux de bord de l'application mobile (graphiques, indicateurs, accueil du téléphone, vues web)

> Établi le 05/10/2026 sur une démo client (AOS 9.1.8 / AOM 9.1.x) : code 9.1.8 qui tourne, sources AOM 9.1.7 et
> écran des relevés au tag 9.1.8, exécution.

**Pièges couverts par cette fiche :**

- 217. `isCustomChart` lu à l'envers : coché = requête exécutée par le serveur (§2)
- 218. Trois tableaux de bord sur l'accueil du téléphone : affichés côte à côte, illisibles ; un seul, un graphique
  par ligne (§2)
- 219. Indicateurs descriptifs (comptages par statut) jugés sans valeur décisionnelle par le demandeur le 05/10/2026 :
  partir des décisions à prendre (§3)
- 220. Graphique regroupé vide = masqué, sans message ; un indicateur sans regroupement affiche 0 (§2)
- 221. Vue web et « accès ERP » en « erreur 500 » au téléphone sans 500 serveur : contexte non sûr
  (`crypto.randomUUID`) (§2)

## 1. Modèles et ordre de création
`MobileChart` (graphique) → `MobileDashboard` (tableau de bord, `appName` = app mobile, `isCustom` + `menuTitle` pour une
entrée de menu) → `MobileDashboardLine` (une ligne, `mobileChart1` à `mobileChart4`) ; vue web : `MobileWebView`
(`isAosWebView` + `metaAction`, ou `url`). Par l'API de l'application, étiquette dédiée, script rejouable (second passage
= 0 écriture). Pour refaire des graphiques, **les reprendre en place** (renommer, changer la requête) plutôt que supprimer :
identifiants et lignes restent valides.

## 2. Faits de code (9.1.8)
- `isCustomChart` **coché = le serveur exécute la requête** (`MobileChartServiceImpl`, `JPA.em().createQuery`) ; décoché =
  action graphique AOP.
- Requête JPQL/HQL à **deux colonnes** (libellé, valeur), sans paramètre ; refus au texte de `\bUPDATE\b`, `\bDELETE\b`,
  `\bFUNCTION\b` (mot entier). Valeur : nombre (Long, BigDecimal, Integer, Double) ou texte.
- **Essai sans écriture** : `POST /ws/action` `{action: "action-mobile-dashboard-method-run-query", model:
  "com.axelor.apps.mobilesettings.db.MobileChart", data: {context: {query, isCustomChart: true}}}` (bouton « Run » du
  formulaire) : rend le résultat ou le message d'erreur, rien n'est enregistré (le contexte ne porte aucune fiche : à la
  différence du cas général du piège 97, `methode-ecriture-sql.md`).
- Éprouvé dans les requêtes : `CURRENT_DATE`, `CURRENT_TIMESTAMP`, `CURRENT_DATE + 7 DAY`, `(d - CURRENT_DATE) BY DAY`,
  `FORMAT(d AS 'dd/MM')`, `CASE … END` répété dans `GROUP BY`, `ORDER BY MIN(…)`, sous-requêtes scalaires, `ROUND(x, n)`,
  libellés accentués.
- Affichage (AOM) : un graphique dont la liste de valeurs est vide est **masqué** ; un indicateur **sans regroupement** rend
  toujours une ligne, donc **affiche 0** (utile pour « 0 livraison en retard ») ; un graphique seul sur sa ligne prend
  toute la largeur ; les lignes s'affichent dans l'ordre de leurs identifiants.
- **Accueil du téléphone** = tous les tableaux de bord rattachés au paramétrage mobile (`appMobileSettings`), **côte à
  côte** à 85 % de largeur : n'en rattacher qu'un, un graphique par ligne.
- Le téléphone relit réglages, champs personnalisés et tableaux de bord **à la connexion** seulement.
- Vue web de l'ERP : l'appli ouvre `<adresse de connexion>#/ds/<action>`, sans contexte. En http par une IP (téléphone),
  le client web EE 8.2.3 plante (« Oups ! … Code erreur : 500 ») : `crypto.randomUUID` absent hors contexte sûr (HTTPS ou localhost requis).

## 3. Méthode : des indicateurs de décision, pas des comptages
- Avant d'écrire une requête, demander **quand** le tableau de bord sera montré : une base de départ (J0) sans commande ni OF rend vides
  tous les indicateurs de flux ; montrés après les séquences de la séance, ils lisent ce qui vient d'être fait.
- Préférer : retards (date promise dépassée), engagements par échéance (sous 7 jours, au-delà), couverture (stock + OF
  prévus contre reste à livrer), couverture matière des OF planifiés, alertes à échéance dépassée, taux de non-conformité
  par contrôle ou fournisseur. Éviter les « nombre par statut ».
- Vérifier chaque valeur : requête servie (`/ws/aos/mobilechart/<id>`) contre SQL sur la base de séance, et la logique
  sur une copie de base qui porte des données de séance (dump d'un rejeu restauré à part).
