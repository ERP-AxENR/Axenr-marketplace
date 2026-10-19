# Index des pièges — lookup par numéro

223 entrées (n° 1 à 221, plus 6.bis et 11.bis). Chaque `methode-*.md` / `entites-*.md` ouvre en plus par la liste de ses propres pièges — cet index sert celui qui connaît déjà le numéro (ex. un rapport ou un message d'erreur qui cite `piège 76`).

| # | Titre | Fichier |
|---|---|---|
| 1 | Un produit créé avec `product_family` / `sale_currency` / `purchase_currency` / `cost_type_select` à NULL casse silencieusement l'interface | `references/entites-produits.md` |
| 2 | `is_activity` n'est PAS « toujours false » | `references/entites-produits.md` |
| 3 | Les séquences doivent être relevées au-dessus de la plage d'ID de démo | `references/methode-ecriture-sql.md` |
| 4 | Idempotence : `WHERE NOT EXISTS` plutôt que `ON CONFLICT DO UPDATE` | `references/methode-ecriture-sql.md` |
| 5 | Les unités produit doivent être alignées (stock / vente / achat) | `references/entites-produits.md` |
| 6 | `base_partner` n'a pas de colonne `is_individual` — utiliser `partner_type_select` | `references/entites-tiers-contacts.md` |
| 6.bis | Employee contact_partner — la forme canonique à 4 booléens | `references/entites-tiers-contacts.md` |
| 7 | Motif d'illustration fournisseur : tiers par défaut + catalogue multi-lignes | `references/entites-tiers-contacts.md` |
| 8 | Valeurs par défaut du tiers : s'aligner sur la forme d'un tiers existant, pas seulement sur les champs obligatoires | `references/entites-tiers-contacts.md` |
| 9 | Panneaux du tiers vides sur un insert minimal — 4 relations à peupler | `references/entites-tiers-contacts.md` |
| 10 | `type_select = NULL` rend une nomenclature (BoM) / gamme (ProdProcess) invisible dans les domaines de liste standard | `references/entites-produits.md` |
| 11 | Produits : `product_family` est OBLIGATOIRE pour la comptabilité (prolonge les pièges 1 et 5) | `references/entites-produits.md` |
| 11.bis | « Le produit est créé » ne veut pas dire « le produit est vendable » : sans FAMILLE **et** CATÉGORIE, l'ajout à une commande échoue | `references/entites-produits.md` |
| 12 | TrackingNumberConfiguration + Sequence : `full_name` (namecolumn) doit être renseigné | `references/entites-autres.md` |
| 13 | Tiers clients : `account_accounting_situation` est obligatoire pour la facturation (prolonge les pièges 8 et 9) | `references/entites-tiers-contacts.md` |
| 14 | Les champs de coût du poste de charge (WorkCenter) dépendent de `work_center_type_select` | `references/entites-production-btp.md` |
| 15 | Un ordre de fabrication TERMINÉ créé en SQL pur n'a AUCUNE chaîne de stock — la construire explicitement (les liens sont des FK, pas des M2M) | `references/entites-production-btp.md` |
| 16 | `__config__.date` à NULL → NPE à l'ouverture des vues stock (binding de configuration manquant) | `references/methode-introspection.md` |
| 17 | Les totaux d'en-tête du SaleOrder ne sont PAS auto-sommés depuis les lignes sur un insert/clone brut | `references/methode-ecriture-sql.md` |
| 18 | Vérification REST : `criteria` + `operator:"like"` échoue silencieusement — utiliser `_domain` | `references/methode-audit.md` |
| 19 | Lignes composant de nomenclature (BoM) : l'O2M `billOfMaterialLineList` se mappe par `bill_of_material_parent`, PAS par `bill_of_material` | `references/entites-production-btp.md` |
| 20 | La gamme (ProdProcess) doit être liée à un produit OU partagée | `references/entites-production-btp.md` |
| 21 | La ligne de gamme (ProdProcessLine) dénormalise les champs du poste de charge à la création — mettre à jour le poste de charge NE resynchronise PAS les lignes existantes | `references/entites-production-btp.md` |
| 22 | La machine a besoin de `machine_type` (FK) + `stock_location` | `references/entites-production-btp.md` |
| 23 | Contacts (individus) : séparer prénom / NOM + civilité + localisation | `references/entites-tiers-contacts.md` |
| 24 | `registration_code` du tiers doit être un SIREN/SIRET VALIDE (Luhn) + renseigner les modes de paiement | `references/entites-tiers-contacts.md` |
| 25 | Selects de valorisation de production du produit | `references/entites-produits.md` |
| 26 | Ne pas rendre `real_*` identique à `planned_*` sur un OF/OperationOrder terminé | `references/entites-production-btp.md` |
| 27 | Mouvement de stock de production : renseigner aussi le `manuf_order` générique (pas seulement in_/out_manuf_order) | `references/entites-production-btp.md` |
| 28 | Numéro de lot (TrackingNumber) produit : renseigner les champs d'origine | `references/entites-production-btp.md` |
| 29 | La généalogie des lots (TN) se construit à partir des TN CONSOMMÉS — consommer le lot source, ne pas se contenter d'affirmer le M2M | `references/entites-production-btp.md` |
| 30 | Une `meta_select` existante ne garantit PAS la colonne sur cette table | `references/methode-introspection.md` |
| 31 | `meta_field` ne contient ni `selection` ni `name_column` (AOP 8.2) | `references/methode-introspection.md` |
| 32 | Fetcher le TYPE réel : des champs « évidents » sont des VARCHAR | `references/methode-introspection.md` |
| 33 | PostgreSQL tronque tout identifiant à 63 caractères | `references/methode-introspection.md` |
| 34 | Le rattachement d'une ligne n'est pas toujours la FK au nom évident | `references/methode-introspection.md` |
| 35 | Deux référentiels homonymes coexistent | `references/methode-introspection.md` |
| 36 | Une colonne « integer » peut être une FK | `references/methode-introspection.md` |
| 37 | Une FK résolue par sous-requête écrit NULL EN SILENCE | `references/methode-introspection.md` |
| 38 | « Menu non vide » ≠ « exploitable » | `references/methode-audit.md` |
| 39 | Prendre le record ID 1 du clone comme MODÈLE DE SHAPE | `references/methode-audit.md` |
| 40 | Une FK NOT NULL vers `MetaFile` signifie « c'est un document à téléverser » | `references/methode-audit.md` |
| 41 | `base_address` : les champs structurés sont obligatoires | `references/methode-introspection.md` |
| 42 | Événements CRM sur un tiers : trois liaisons à remplir ensemble | `references/entites-tiers-contacts.md` |
| 43 | Ne pas confondre deux entités de noms proches | `references/methode-introspection.md` |
| 44 | Cohérence inter-champs — créer la valeur manquante plutôt que prendre au hasard | `references/methode-coherence.md` |
| 45 | Cohérence sémantique du libellé | `references/methode-coherence.md` |
| 46 | Données satellites génériques = non crédibles | `references/methode-coherence.md` |
| 47 | Cohérence arithmétique interne d'une ligne | `references/methode-coherence.md` |
| 48 | Une FK vers une période doit pointer la granularité métier | `references/methode-coherence.md` |
| 49 | Répartir les enfants sur TOUS les parents | `references/methode-coherence.md` |
| 50 | Un `jsonb attrs` peut porter des données MÉTIER dont les clés viennent d'une formule | `references/methode-coherence.md` |
| 51 | Une même table peut servir DEUX rôles via un `typeSelect` | `references/methode-coherence.md` |
| 52 | Cache Hibernate de second niveau — piège de vérification n°1 | `references/methode-audit.md` |
| 53 | État runtime = preuve applicative | `references/methode-audit.md` |
| 54 | `ClassNotFoundException` dans les logs = méta morte d'un module retiré | `references/methode-audit.md` |
| 55 | Les angles morts d'un audit de couverture par les menus | `references/methode-audit.md` |
| 56 | Relire `studio_app.active` au moment d'agir | `references/methode-audit.md` |
| 57 | `v.xxx` absent de la liste `VALUES` | `references/methode-ecriture-sql.md` |
| 58 | `AND EXISTS(...)` protège de la FK NULL mais crée un échec SILENCIEUX sur base vierge | `references/methode-rejouabilite.md` |
| 59 | Un jeu de données tagué n'est PAS un jeu de données rejouable | `references/methode-rejouabilite.md` |
| 60 | Le skill sait « comment », pas « quoi » : exiger un contrat de scénario | `references/methode-rejouabilite.md` |
| 61 | SIREN valide ≠ SIRET valide | `references/methode-rejouabilite.md` |
| 62 | Remplir « les booléens principaux » ne suffit pas — il faut TOUS les booléens | `references/methode-rejouabilite.md` |
| 63 | `quote_nullable(NULL)` renvoie le TEXTE `'NULL'` — un override en `NULL` nu vide la ligne | `references/methode-rejouabilite.md` |
| 64 | Cycles FK via `created_by` / `updated_by` | `references/methode-rejouabilite.md` |
| 65 | Cycles FK « vers l'avant » entre fichiers | `references/methode-rejouabilite.md` |
| 66 | Cycles à deux tables | `references/methode-rejouabilite.md` |
| 67 | L'ordre FK-safe réel diverge de l'ordre « logique métier » | `references/methode-rejouabilite.md` |
| 68 | Tables de jonction M2M : pas de colonne `id` | `references/methode-rejouabilite.md` |
| 69 | Nuance sur « aucune sélection NULL » : les champs CONDITIONNELS | `references/methode-rejouabilite.md` |
| 70 | Renommer `name` sans recalculer `full_name` = renommage INVISIBLE | `references/entites-tiers-contacts.md` |
| 71 | `full_name` à NULL rend l'enregistrement INVISIBLE — pire que le libellé périmé | `references/entites-tiers-contacts.md` |
| 72 | La convention d'un contact inclut le PRÉNOM | `references/entites-tiers-contacts.md` |
| 73 | Prendre un numéro de séquence sans avancer le compteur = collision au `onSave` | `references/methode-ecriture-sql.md` |
| 74 | `crm_opportunity.order_by_state` — copie de la séquence du statut, tri et kanban cassés | `references/methode-coherence.md` |
| 75 | `count()` MENT SUR LES ZÉROS | `references/methode-audit.md` |
| 76 | `= false` EXCLUT LES NULL — un booléen non initialisé rend l'enregistrement invisible | `references/methode-audit.md` |
| 77 | Ne rien redire dans un champ que la fiche affiche déjà à deux centimètres | `references/methode-coherence.md` |
| 78 | Un préfixe de séquence à soi est une couture visible | `references/methode-coherence.md` |
| 79 | Les archives ne se réécrivent pas | `references/methode-rejouabilite.md` |
| 80 | Sélectionner par motif de libellé rend la vague non rejouable | `references/methode-rejouabilite.md` |
| 81 | Borner ses assertions à son périmètre | `references/methode-audit.md` |
| 82 | Auditer contre le CONTRAT, pas contre son propre script | `references/methode-audit.md` |
| 83 | Configuration de suivi : `purchase_qty_by_tracking` NULL → NPE en réception | `references/entites-autres.md` |
| 84 | `purchase_supplier_catalog` : la référence est celle du FOURNISSEUR | `references/entites-tiers-contacts.md` |
| 85 | Table de couple : renseigner les DEUX côtés | `references/entites-tiers-contacts.md` |
| 86 | FK attendant un `id`, alimentée par un code métier | `references/methode-rejouabilite.md` |
| 87 | `MetaFile` par l'API : la réponse porte `data` sous forme de TABLEAU | `references/entites-tiers-contacts.md` |
| 88 | Une valeur de mesure sans son unité est pire qu'un champ vide | `references/methode-coherence.md` |
| 89 | Ne pas remplir un champ qui n'a pas de sens pour le type de l'enregistrement | `references/methode-coherence.md` |
| 90 | `meta_action` / `meta_view` peuvent porter des DOUBLONS de nom | `references/methode-audit.md` |
| 91 | Vérifier dans l'UI : lire le panneau ACTIF, pas `document.body` | `references/methode-audit.md` |
| 92 | Le piège 70 n'a pas UN niveau, il en a QUATRE — et l'audit ne regardait que le premier | `references/methode-audit.md` |
| 93 | Une note, un score, une étoile : vérifier QUI l'écrit avant de la remplir — ou de la vider | `references/methode-coherence.md` |
| 94 | Vérifier par l'API REST : omettre la clé `data` désactive le filtre `archived` | `references/methode-audit.md` |
| 95 | Renommer un tiers ne suffit pas : les COORDONNÉES sont un axe à part, et les noms inventés peuvent être réels | `references/methode-coherence.md` |
| 96 | Le cache L2 ne masque pas un `UPDATE` SQL : le prochain save moteur le RÉVERTIT | `references/methode-audit.md` |
| 97 | Appeler une `action-method` en REST SAUVEGARDE l'enregistrement — séquences consommées, namecolumns recalculés, lignes satellites créées | `references/methode-ecriture-sql.md` |
| 98 | Un tag technique peut être AFFICHÉ à l'écran : `import_origin` est rendu en badge dans l'en-tête de la Commande client | `references/entites-ventes.md` |
| 99 | Une nomenclature qui porte une gamme et AUCUNE ligne de composant échoue sur un NullPointerException | `references/entites-production-btp.md` |
| 100 | Une nomenclature SANS gamme rend un ordre de production VIDE : zéro OF, en succès, sans un message | `references/entites-production-btp.md` |
| 101 | Générer un OF depuis une commande exige `sale_supply_select` ∈ {3,4} sur le produit ET `qty_to_produce > 0` sur la ligne | `references/entites-production-btp.md` |
| 102 | Configurateur : une formule sans indicateur correspondant est ignorée EN SILENCE, et éditer une formule périme toutes les instances | `references/entites-production-btp.md` |
| 103 | Attributs de configurateur seedés par API : cinq colonnes `context_field*`, un `on_change`, et parfois un redémarrage | `references/entites-production-btp.md` |
| 104 | Créer une commande de vente par API : quatre champs seulement, dont `creation_date` que rien n'annonce | `references/entites-ventes.md` |
| 105 | Un utilisateur créé par REST naît BLOQUÉ, et son login répond en HTML | `references/entites-autres.md` |
| 106 | Un échec fonctionnel AOS peut arriver en `info`, pas en `error` — un audit qui ne lit qu'`error` le compte pour un succès | `references/methode-audit.md` |
| 107 | Un périmètre de tag VIDE rend les dimensions vertes sur RIEN — l'audit doit échouer, pas se taire | `references/methode-audit.md` |
| 108 | Un contact créé via `main_partner` n'alimente PAS la jonction `base_partner_contact_partner_set` — panneau Contacts vide | `references/entites-tiers-contacts.md` |
| 109 | Un domaine `:__user__`/`:_internalUserId` exige une FK utilisateur EXPLICITEMENT posée, sur CHAQUE tiers | `references/entites-tiers-contacts.md` |
| 110 | Comptes utilisateurs créés en SQL : `blocked=false` explicite ne suffit pas — compter les sièges nommés de la licence Guardian | `references/entites-autres.md` |
| 111 | Le correctif « pas de week-end » naïf empile tout sur le MÊME jour ouvré — allocateur avec plafonds | `references/methode-dates.md` |
| 112 | Engagement contractuel « aucun X ouvert sans Y futur » — non couvert par les dimensions numérotées existantes (F8) | `references/methode-dates.md` |
| 113 | Popup « Configurer Supply Chain » sur le devis même app `supplychain` inactive — garde `isApp()` manquante dans AOS | `references/entites-ventes.md` |
| 114 | Un rapport d'exécutant peut affirmer un fait faux — re-mesurer avant d'écrire une vague qui en dépend | `references/methode-audit.md` |
| 115 | Il n'existe PAS de table `crm_event` — les événements CRM vivent dans `ical_event` (`dtype='Event'`) | `references/entites-crm.md` |
| 116 | Un livrable qui pose des `MetaFile` réels n'est pas complet sans l'archive des fichiers physiques | `references/methode-rejouabilite.md` |
| 117 | Stock négatif sur un emplacement réel BLOQUE le moteur pour tout mouvement, même une réception — message trompeur « livraison » | `references/entites-stock.md` |
| 118 | Deuxième horloge : les compteurs de séquence MÉTIER (`base_sequence_version`) n'avancent qu'au save moteur — distincts des séquences PK du piège 73 | `references/methode-ecriture-sql.md` |
| 119 | Nomenclature et gamme INVISIBLES dans le sélecteur d'un ordre de fabrication : `statusSelect = 3` ET atelier vide | `references/entites-production-btp.md` |
| 120 | Une gamme qui consomme depuis un emplacement SANS stock ne lève rien — l'OF affiche tous ses composants manquants | `references/entites-production-btp.md` |
| 121 | `producedProductStockLocation` décide où atterrit le produit fini, et les sous-ensembles doivent atterrir là où le parent consomme | `references/entites-production-btp.md` |
| 122 | Une quantité NÉGATIVE en nomenclature passe l'import sans un mot et bloque au lancement de l'OF | `references/entites-production-btp.md` |
| 123 | Un tiers sans ligne `base_partner_company_set` est INVISIBLE dans les sélecteurs client et fournisseur | `references/entites-tiers-contacts.md` |
| 124 | `version` NULL sur une ligne seedée : lecture OK, NPE « current is null » au premier enregistrement du moteur (flush Hibernate) | `references/pieges-runtime-aos-9-1-7.md` |
| 125 | Démarrer puis Terminer un ordre de fabrication par script rend un coût réel de ZÉRO — et le correctif a trois temps, dont un redémarrage | `references/entites-production-btp.md` |
| 126 | « Démarrer » ne touche que l'en-tête : les opérations restent Planifiées, sans date réelle | `references/entites-production-btp.md` |
| 127 | `compute-cost-price` AJOUTE une feuille de coût, il ne remplace pas la précédente | `references/entites-production-btp.md` |
| 128 | Les lignes filles d'une feuille de coût ne portent PAS la référence à la feuille — la purge est récursive ou elle échoue | `references/entites-production-btp.md` |
| 129 | Une nomenclature auto-référencée rend un coût de zéro, sans erreur et sans feuille | `references/entites-production-btp.md` |
| 130 | Un prix à NULL (et non à zéro) échappe à toute passe écrite en `> 0` | `references/methode-ecriture-sql.md` |
| 131 | Un `POST /ws/rest` ne déclenche AUCUN `onChange` : la ligne sort sans prix ni taxe | `references/entites-ventes.md` |
| 132 | Une action de calcul d'en-tête appelée avec `{id}` rend `status: 0` et zéro clé — le contexte doit être l'enregistrement entier | `references/entites-ventes.md` |
| 133 | Le calcul d'en-tête d'achat ne fait que SOMMER : sans calcul par ligne, il somme des zéros | `references/entites-achats.md` |
| 134 | Le prix d'une ligne d'achat vient de `purchase_price`, jamais de `cost_price` | `references/entites-achats.md` |
| 135 | Le moteur refuse d'écrire sur une commande d'achat validée, en répondant `status: 0` | `references/entites-achats.md` |
| 136 | Supprimer une commande d'achat en SQL heurte trois tables filles aux noms non devinables — `/remove` le fait proprement | `references/entites-achats.md` |
| 137 | Générer une affaire depuis une commande exige deux clés de contexte non documentées, et un drapeau d'app pour le code | `references/entites-projet-temps.md` |
| 138 | Les indicateurs d'affaire lisent zéro tant que les QUATRE liens de rattachement ne sont pas posés — au niveau LIGNE | `references/entites-projet-temps.md` |
| 139 | Deux pièges PostgreSQL de rétro-datation : `make_interval(mins => bigint)` et la soustraction de deux `date` | `references/methode-dates.md` |
| 140 | Une valeur uniforme PAR FAMILLE est un copier-coller que la dimension 4 ne voit pas | `references/methode-audit.md` |
| 141 | Un rechargement de module ne supprime JAMAIS ce qui a disparu du XML — et la liste des résidus contient des faux positifs | `references/methode-audit.md` |
| 142 | `current_date + 15` sans unité échoue sur Hibernate 6 — et un domaine se valide sur deux critères, pas un | `references/methode-audit.md` |
| 143 | Pièces « reçues », « livrées » ou OF « démarrés » sans mouvement de stock : un statut de flux physique posé en SQL simule la transition, visible au premier clic | `references/entites-stock.md` |
| 144 | Un pointage d'atelier ne porte PAS l'affaire, et ne montre son OF que si l'employé est « imputé sur OF » (`timesheetImputationSelect = 2`) | `references/entites-projet-temps.md` |
| 145 | Une affaire issue d'une commande a des tâches (forme « SOxxxx - n - article ») et 6 statuts de tâche ; sa fin couvre la dernière tâche | `references/entites-projet-temps.md` |
| 146 | Le coût d'un pointage n'existe qu'après le calcul de l'affaire, et le déboursé du module `axelor-project-reporting` (hors standard) lit cette colonne — sinon « Main-d'œuvre 0,00 » | `references/entites-projet-temps.md` |
| 147 | Tâche sans priorité : obligatoire au formulaire si le projet affiche les priorités (défaut), nullable en base — la dimension 5 ne la voit pas | `references/entites-projet-temps.md` |
| 148 | Gamme à `operation_continuity` NULL : ordre de démarrage imposé ; le réglage d'app n'agit que sur les gammes nouvelles | `references/entites-production-btp.md` |
| 149 | Écrit dans un rapport n'est pas annoncé ; un attendu d'UAT se relève à l'écran, pas par raisonnement | `references/methode-audit.md` |
| 150 | Affaire seedée sans jeu de priorités de tâche : ne s'enregistre plus depuis l'écran (`projectTaskPrioritySet` requiredIf `isShowPriority`) — seeder aussi le jeu de statuts par défaut | `references/entites-projet-temps.md` |
| 151 | Une filiale se crée à l'écran : 17 prérequis (impressions, comptes par famille, « Générer BR », adresses…), jamais par duplication ni par script à `CURRENT_DATE` | `references/pieges-runtime-aos-9-1-7.md` |
| 152 | Le devis miroir intragroupe recopie la TVA d'achat : facture refusée, corriger la taxe au brouillon | `references/pieges-runtime-aos-9-1-7.md` |
| 153 | 9.1.7 : l'import de la démo Supply Chain ne réalise plus les réceptions d'achat (échec silencieux) | `references/pieges-runtime-aos-9-1-7.md` |
| 154 | Facture fournisseur payée par virement : RIB du fournisseur obligatoire, sinon « Valider » semble sans effet (bandeau fugace) ; RIB reporté seulement s'il est « par défaut » | `references/pieges-runtime-aos-9-1-7.md` |
| 155 | Un devis BTP créé par REST n'est BTP qu'avec son drapeau et son initialisation — et il naît hors sélection, en marché privé avec l'avance par défaut | `references/entites-production-btp.md` |
| 156 | « Créer le chantier » recopie l'en-tête du devis — tout poser AVANT, puis renommer chantier ET dépôt | `references/entites-production-btp.md` |
| 157 | « Planning du chantier » plante au premier clic — planning créé d'avance, APRÈS le renommage | `references/entites-production-btp.md` |
| 158 | Synthèse matière vide sans produit sur les sous-détails — réutiliser les produits BTP de la démo | `references/entites-production-btp.md` |
| 159 | La sauvegarde de l'arbre accepte tous les champs de complétude d'une ligne | `references/entites-production-btp.md` |
| 160 | Situation de travaux : quatre prérequis, un avancement en INCRÉMENT — et le marché-cadre ne rattache que le devis qui le crée | `references/entites-production-btp.md` |
| 161 | Les retenues du module pointent vers des produits vides — repointer par la retenue, par le code | `references/entites-production-btp.md` |
| 162 | Régler une facture de situation : hors retenue, et décider sur le reste dû | `references/entites-production-btp.md` |
| 163 | Paiement direct confirmé = journal DC4 obligatoire à la ventilation suivante | `references/entites-production-btp.md` |
| 164 | Circuit de sous-traitance : URSSAF « Valide » + Kbis sur la fiche du sous-traitant | `references/entites-production-btp.md` |
| 165 | Commande de sous-traitance repassée au prix d'achat du produit | `references/entites-production-btp.md` |
| 166 | Lots de pointage : salarié sans contrat ni utilisateur = feuille sans société = « Date invalide » | `references/entites-production-btp.md` |
| 167 | Devis perdu : envoyé, puis annulé avec un motif standard | `references/entites-production-btp.md` |
| 168 | Contrôler le montant d'avenant du chantier, pas le message de confirmation | `references/entites-production-btp.md` |
| 169 | Un peuplement par l'API ne porte d'étiquette d'import que si le script la pose — la poser à chaque création, sauf là où une vue l'affiche | `references/methode-audit.md` |
| 170 | Une pièce qui change le marché se confirme DANS la boucle chronologique, pas avant | `references/methode-dates.md` |
| 171 | Un geste utilisateur daté « du jour » se fait sous date simulée, script en pause | `references/methode-dates.md` |
| 172 | Un rejeu correctif de règlements après coup casse l'ordre du journal de banque | `references/methode-dates.md` |
| 173 | Une pièce à échéance se date par rapport au jour de la démo, pas au jour du geste | `references/methode-dates.md` |
| 174 | 9.1.7 : livraison ↔ devis par `StockMove.saleOrderSet` ; la démo ne crée aucune livraison à la confirmation | `references/pieges-runtime-aos-9-1-7.md` |
| 175 | Numérotation sans remise annuelle : une pièce datée AVANT la première version repart au n° 1 | `references/pieges-runtime-aos-9-1-7.md` |
| 176 | Avancement posé par l'API : chaque enregistrement crée une ligne d'historique datée du jour simulé — le poser sur les ouvrages, une fois par date | `references/entites-production-btp.md` |
| 177 | Réceptionner un chantier ne pose pas sa fin réelle : retard et pénalité provisoire continuent de courir | `references/entites-production-btp.md` |
| 178 | L'onglet Pilotage calcule ET ENREGISTRE à son ouverture : après un peuplement par l'API, rejouer son action sur chaque chantier | `references/entites-production-btp.md` |
| 179 | Un instantané de reste à faire enregistre l'état du moment ; sa date n'est qu'une étiquette | `references/entites-production-btp.md` |
| 180 | Achats d'un chantier : trois rattachements lus par trois écrans — sans celui de l'en-tête, la déduction du paiement direct vaut 0 € en silence | `references/entites-production-btp.md` |
| 181 | Lots de pointage et paie du module : préremplir par le bouton dédié, zone sur chaque demi-journée, paie par le chemin de l'écran | `references/entites-production-btp.md` |
| 182 | Réception d'achat : une unité de ligne différente de celle de l'article exige une conversion exacte, et inversible | `references/pieges-runtime-aos-9-1-7.md` |
| 183 | Feuilles de temps générées : ouvertes au fil des lignes, un jour ouvré vide refusé, et des fériés faux dans la démo | `references/pieges-runtime-aos-9-1-7.md` |
| 184 | Comptabilité fournisseur de la démo : SI l'app Paiement bancaire est inactive (le vérifier), le virement échoue ; l'acompte exige deux comptes absents | `references/pieges-runtime-aos-9-1-7.md` |
| 185 | Toutes les pièces comptables d'une société se jouent dans UNE boucle triée par date — AOS refuse de ventiler une facture antérieure à la dernière ventilée | `references/methode-dates.md` |
| 186 | Ce que l'écran dérive au changement d'un champ, l'API ne le fait jamais — relevé sur quatre champs | `references/pieges-runtime-aos-9-1-7.md` |
| 187 | L'API rend les dates-heures à fuseau en UTC : une clé d'idempotence sur l'heure doit convertir | `references/pieges-runtime-aos-9-1-7.md` |
| 188 | L'audit écrit dans la base qu'il audite — et un `BEGIN` sans point-virgule devant `\i` ne le met pas en transaction | `references/methode-audit.md` |
| 189 | L'ordre de création n'est pas une clé : deux rejeux identiques peuvent créer des homonymes dans un ordre différent | `references/methode-rejeu-controle.md` |
| 190 | Un essai factice ne prouve rien ; seul un essai à blanc qui lit la cible réelle renseigne | `references/methode-rejeu-controle.md` |
| 191 | Estimer la durée d'un rejeu distant par le nombre d'appels de la répétition et le débit mesuré, pas au jugé | `references/methode-rejeu-controle.md` |
| 192 | Un script modifié après sa répétition n'est plus répété | `references/methode-rejeu-controle.md` |
| 193 | Commande d'achat créée par l'API : la case « intragroupe » reste vide, aucune commande miroir ne naît | `references/pieges-runtime-aos-9-1-7.md` |
| 194 | Règlement par l'API sans ses échéances : validé sans écriture ni lettrage — en virement, une NullPointerException | `references/pieges-runtime-aos-9-1-7.md` |
| 195 | La « date de commande » d'une commande client est la date de sa première facture | `references/pieges-runtime-aos-9-1-7.md` |
| 196 | « Compte bloqué » ne se coche ni par un blocage, ni par un règlement | `references/pieges-runtime-aos-9-1-7.md` |
| 197 | « Produits par société » : des copies figées à l'enregistrement, et un approvisionnement à la vente commun | `references/pieges-runtime-aos-9-1-7.md` |
| 198 | « Qté de produits reçus du fournisseur » et la note qualité ne comptent que les lignes contrôlées | `references/pieges-runtime-aos-9-1-7.md` |
| 199 | Un produit complémentaire du TIERS s'ajoute seul à chaque devis — le saisir en plus le double | `references/pieges-runtime-aos-9-1-7.md` |
| 200 | Une AQ ne s'enregistre pas sans séquence propre à sa société (la séquence sans société n'est jamais trouvée) | `references/entites-qualite.md` |
| 201 | L'AQ créée depuis un relevé prend la société active de l'utilisateur | `references/entites-qualite.md` |
| 202 | AQ : la créer seule, le dépôt crée identification, résolution, analyse (imbriquées = refus) ; clé de rejeu = référence de document | `references/entites-qualite.md` |
| 203 | Les enfants d'une AQ se référencent entre eux : défauts d'abord ; règles de quantité, coût, forfait, acceptation | `references/entites-qualite.md` |
| 204 | Responsables « Employé » et « Détecté par (interne) » : il faut des contacts et des salariés (numérotation des tiers) | `references/entites-qualite.md` |
| 205 | Conformité d'un relevé calculée par une formule côté serveur : saisir les mesures puis le bouton | `references/entites-qualite.md` |
| 206 | Prélèvements créés par un bouton, numérotés à partir de 0 | `references/entites-qualite.md` |
| 207 | « Relié à » d'un relevé : non calculé depuis le menu en 9.1.8 (jar) ; bouton des onglets Qualité ; relevé sans id seul pour sa gamme = modèle | `references/entites-qualite.md` |
| 208 | Fréquence de contrôle : nom calculé en anglais, traduction à l'onSave, champ masqué | `references/entites-qualite.md` |
| 209 | Types de contrôle : champs de mesure = champs personnalisés à contexte | `references/entites-qualite.md` |
| 210 | Diffusions d'AQ : séquence de la configuration qualité, puis rejouer la requête de l'écran (contexte à la main = échec ou rien) | `references/entites-qualite.md` |
| 211 | Audit : pré-remplissage par bouton ; points facultatifs en attente sans audit | `references/entites-qualite.md` |
| 212 | Point de mesure de type Conformité : case ET note 5 / 0 | `references/entites-qualite.md` |
| 213 | Rapport qualité filtré sur la date de création ; calendriers ouverts sur le mois courant | `references/entites-qualite.md` |
| 214 | Créer une équipe crée un menu personnel par membre (+ une action) : écart attendu d'une empreinte de la base | `references/entites-qualite.md` |
| 215 | Le jar qui tourne prime sur les sources : appeler l'action (elle peut écrire, piège 97) ou lire le bytecode avant d'écrire | `references/methode-rejouabilite.md` |
| 216 | Rejeu : widgetAttrs réécrit clés triées ; références comparées par id | `references/methode-rejouabilite.md` |
| 217 | `isCustomChart` lu à l'envers : coché = requête exécutée par le serveur | `references/tableaux-de-bord-mobiles.md` |
| 218 | Trois tableaux de bord sur l'accueil du téléphone : affichés côte à côte, illisibles ; un seul, un graphique par ligne | `references/tableaux-de-bord-mobiles.md` |
| 219 | Indicateurs descriptifs (comptages par statut) jugés sans valeur décisionnelle : partir des décisions à prendre | `references/tableaux-de-bord-mobiles.md` |
| 220 | Graphique regroupé vide = masqué, sans message ; un indicateur sans regroupement affiche 0 | `references/tableaux-de-bord-mobiles.md` |
| 221 | Vue web et « accès ERP » en « erreur 500 » au téléphone sans 500 serveur : contexte non sûr (`crypto.randomUUID`) | `references/tableaux-de-bord-mobiles.md` |
