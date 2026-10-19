# Entités — CRM (lead, opportunité, pipeline, événements)

> **Couche UI-critical uniquement.** Ce que ni le schéma (`scripts/shape-fiche.sh`, `introspect.sh`)
> ni un enregistrement modèle ne donnent. Les NOT NULL, les FK et les taux de remplissage ne sont
> PAS ici : ils s'introspectent au moment de produire (règle 1).
>
> **Établie empiriquement le 2026-09-07** sur `<base>` — AOS 9.1.6 / module local
> `axelor-construction` 9.1.0-SNAPSHOT. Protocole : lecture d'un dossier
> d'hypothèses (10 items, produit en lecture seule sans écran ni REST), réfutation de chacun
> contre la base réelle, lecture directe des sources Java/XML (`axelor-crm`) pour les mécanismes de
> boutons et de contraintes de vue, tests via REST authentifié (`/ws/rest`, `/ws/action`) —
> **navigateur non disponible** dans cette session (même contrainte que le protocole achats du
> même jour).
>
> **Marquage de chaque item** : `[prouvé REST]` = appel HTTP authentifié réellement exécuté sur
> le serveur, réponse observée (recherche, dataset REST, sauvegarde) ; `[prouvé écran]` —
> **aucun item de cette fiche ne porte ce marquage**, voir « Ce que ce protocole n'a PAS couvert » ;
> `[SCHEMA]` = compté en SQL ou lu dans un domaine de menu ; `[INFERE]` = lu en source Java/XML,
> non exécuté mais non ambigu ; `[SUPPOSE]` = ni l'un ni l'autre.

**Pièges déjà existants que cette fiche concerne** (numéros inchangés) :

- 5 / 71. `full_name` ne se calcule pas en SQL, et une concaténation nue rend NULL dès qu'un
  composant est NULL — appliqué sur les 3 leads créés : `COALESCE(enterprise_name,'') || ', ' ||
  COALESCE(first_name,'') || ' ' || COALESCE(name,'')`, format confirmé par coïncidence avec le
  socle (lead id=1 : `'123 Services, Jean-Marc ROGER'`).
- 10. Aucun nom au hasard — 1 prospect BTP créé (`OPH Résidences de la Sambre`, bailleur
  social), 3 leads BTP créés (bailleur social, cabinet d'architecture, promoteur), aucun des
  10 tiers réels du portefeuille BTP existant n'étant un prospect *pas encore* client — les
  10 sont déjà des clients avec affaire en cours, réutiliser l'un d'eux comme « nouveau
  prospect » aurait été une incohérence narrative.
- 73 / 12. Consommer la séquence après insertion, jamais avant — `crm_lead_seq`,
  `base_partner_seq`, `base_function_seq`, `crm_lost_reason_seq`, `base_industry_sector_seq`,
  `message_email_address_seq`, `ical_event_seq` avancés par `setval(..., max(id))` en fin de
  script. `crm_opportunity_seq` **non touché** : l'opportunité 958007 est née d'un vrai appel
  moteur (REST `/ws/rest/.../Opportunity`), qui a déjà consommé la séquence PK et le compteur
  métier (`opportunity_seq='O0040'`) correctement — aucune désynchronisation à corriger,
  contrairement au cas `purchase_order_seq` documenté dans `entites-achats.md` §6.
- Nouveau piège **93** : **un test REST volontaire pour trancher une hypothèse peut créer un
  enregistrement réel qu'aucune règle du skill n'autorise à supprimer.** Voir §0.
- Nouveau piège **115** : **il n'existe PAS de table `crm_event`** — les événements CRM (rendez-vous,
  appels, réunions, sur Lead ET Opportunité) vivent tous dans `ical_event` avec `dtype='Event'`
  (prolonge le piège 42, `entites-tiers-contacts.md` : même mécanisme d'héritage à discriminant que
  pour les événements sur `Partner`). Chercher `crm_event` en introspection renvoie « table
  inexistante » et peut faire conclure à tort que les événements CRM sont hors périmètre SQL — ils
  sont au contraire directement scriptables (§0, ligne « bouton Planifier RDV »), à condition de
  cibler la bonne table.

---

## 0. Ce que le protocole a établi de transverse

| Constat | Preuve |
|---|---|
| **Le kanban « Opportunités ouvertes » et le kanban « Leads ouverts » n'ont PAS de vue kanban pour leur pendant « fermé/clos ».** `crm.opened.opportunity`/`crm.opened.lead` portent les 3 vues (kanban+grid+form) ; `crm.closed.opportunity`/`crm.closed.lead` ne portent que grid+form. Une opportunité/lead au statut terminal (Fermée gagnée/perdue, Converti/Perdu) **ne peut jamais apparaître dans un kanban**, quel que soit son contenu — ce n'est pas un défaut de données, c'est la conception de l'écran. | `[SCHEMA]` lecture directe de `meta_action` (ids 3654/3656/3659 pour Opportunity, 3627/3628/3630 pour Lead) : `<view type="kanban">` présente uniquement sur les actions "opened"/"my", absente sur les "closed". |
| **Les deux kanbans (`columnBy="opportunityStatus"` / `columnBy="leadStatus"`) étaient DÉJÀ montrables avant cette mission** — chaque colonne ouverte non vide, plusieurs statuts représentés, distribution non uniforme (Opportunités : 9/10/7/3 ; Leads : 5/9/12/3). La mission n'a donc PAS eu besoin d'ajouter du volume pour atteindre le seuil d'écran : le travail réel était la **crédibilité** (vocabulaire 100 % ESN/IT avant cette mission, 0 opportunité/lead au vocabulaire BTP visible dans un pipeline « ouvert », hors les 3 lignes `demo-c4` déjà en statut ouvert). | `[prouvé REST]` `POST /ws/rest/.../Opportunity/search` avec `_domain:"self.opportunityStatus.isOpen = true"` → `Counter({'Qualification': 10, 'Nouveau': 9, 'Proposition': 7, 'Négociation': 3})` avant l'ajout de 958007 ; idem Lead avant ajout des 3 leads : `1=5,2=9,3=12,4=3`. |
| **Après cette mission, le kanban Opportunités ouvertes sert 30 lignes** (`Qualification` passe de 10 à 11 avec l'ajout de 958007), **le kanban Leads ouverts sert 32 lignes** (5→6, 9→10, 12→13 après les 3 leads BTP, statuts À traiter/Qualification marketing/Qualification commerciale). | `[prouvé REST]` mêmes appels rejoués après écriture : `Counter({'Qualification': 11, 'Nouveau': 9, 'Proposition': 7, 'Négociation': 3})` (total 30) ; Lead `Counter({'Qualification commerciale': 13, 'Qualification marketing': 10, 'À traiter': 6, 'Nurturing': 3})` (total 32). |
| Attention : **Le pipeline du socle AOS est statistiquement incohérent sur le couple statut↔probabilité, ET ce n'est pas un défaut introduit par une campagne de données** — c'est ce qu'AOS 9.1.6 livre nativement sur les 32 opportunités génériques (`import_origin IS NULL`, ids 1-32). 8 lignes sur 32 violent la relation attendue (Fermée perdue avec probabilité > 0, Fermée gagnée ≠ 100 %, Négociation ≥ 95 %). Voir §3 pour la mesure complète et la décision. | `[SCHEMA]` mesuré par agrégation directe (`GROUP BY opportunity_status`) : `Fermée perdue` min/max probabilité 0/93 ; `Fermée gagnée` min/max 47/100 ; `Négociation` (statut ouvert) jusqu'à 100 %. Détail des 8 lignes en §3. |
| **`crm_opportunity` ne porte AUCUNE colonne `address`.** Le raffinement suggéré par le dossier d'hypothèses (H-CRM-02 : « comparer les adresses exactes des sites ») est donc structurellement non testable, pas seulement non testé faute de budget. | `[SCHEMA]` introspection complète de la table (34 colonnes) : aucune FK vers `base_address`. |
| **Le bouton « Planifier RDV » (Lead et Opportunité) est un `action-view` pur, sans `action-method`.** Le SQL direct sur `ical_event` (rendez-vous, appels, réunions) est donc sûr sans risque de simulation de transition moteur — confirme et clôt H-CRM-06. | `[INFERE]` lecture directe de `action-lead-view-schedule-event` et `action-opportunity-view-schedule-event` dans `meta_action` : `<action-view>` ouvrant `event-form`/`event-grid`, contexte `_eventLead`/`_opportunity` pré-rempli, aucune logique serveur. |
| **`crm_opportunity.company` est `required="true"` en VUE (`views/Opportunity.xml:228`) mais nullable en base ET non contraint côté JPA** (`domains/Opportunity.xml:27`, simple `many-to-one` sans `required`). Testé en direct, pas seulement lu : une sauvegarde REST sans `company` réussit. | `[prouvé REST]` `POST /ws/rest/com.axelor.apps.crm.db.Opportunity {"data":{"name":"TEST H-CRM-09 sans company"}}` → `status:0`, opportunité 958007 créée avec `company:null`, `opportunityStatus` par défaut "Nouveau", `orderByState:0` (0, PAS 1 — la valeur par défaut du moteur à la création ne suit pas la séquence du statut par défaut, cf. piège 93 ci-dessous). |
| **Un contact d'opportunité (`crm_opportunity.contact`) est TOUJOURS un contact du `partner` de cette même opportunité** — vérifié à 100 % (7/7), pas seulement sur l'échantillon initial. | `[SCHEMA]` `SELECT c.main_partner, o.partner FROM crm_opportunity o JOIN base_partner c ON c.id=o.contact WHERE o.contact IS NOT NULL` sur les 7 lignes qui renseignent `contact` (958001-958007) : 0 exception. |
| **Le chaînage CRM→Ventes existe et est prouvable via une FK native, jamais via une conversion simulée.** `sale_sale_order.opportunity` (existante, 0/26 utilisée avant cette mission) est le seul point d'ancrage fiable : `crm_opportunity` n'a **aucune** colonne `lead`, donc toute « conversion » Lead→Opportunité posée en SQL serait indétectable et invérifiable. | `[SCHEMA]` `\d crm_opportunity` : pas de colonne `lead`. `[prouvé REST]` après écriture : `GET .../SaleOrder/952001` → `opportunity:{id:958005,...}`. |

---

## 1. `crm_lead`

**Casse à NULL / structurel**

- `industry_sector`, `type`, `agency`, `company`, `company_department` — NULL sur les 30 leads
  socle (référentiels vides ou concept non pertinent) ET sur les 3 leads BTP créés pour
  `type`/`agency`/`company`/`company_department` (aucun de ces 4 concepts n'a de valeur
  pertinente pour un lead pré-conversion — `type` catégorise un `Partner`, pas encore attribué).
  `industry_sector`, lui, **est** rempli sur les 3 nouveaux (référentiel créé, voir §0/§4). `[SCHEMA]`
- `partner` — reste `NULL` sur les 3 leads créés, **par doctrine, pas par oubli** : le socle ne
  porte `partner` rempli que sur 1/30 (le lead converti). Un lead pré-conversion sans `partner`
  est la norme observée, pas un trou. `[SCHEMA]`
- `lead_status` — posé explicitement en SQL sur les 3 créations, jamais laissé au filet de
  sécurité moteur (`LeadManagementRepository.save()` ne pose un statut par défaut qu'au premier
  save moteur — un lead SQL non resauvé resterait NULL et invisible des deux menus principaux).
  `[INFERE, non re-testé, mécanisme documenté dans le dossier d'hypothèses]`

**Domaine filtrant qui exclut le NULL**

| Menu / vue | Prédicat | Conséquence |
|---|---|---|
| `crm.opened.lead` (kanban+grid+form, `home="true"`) | `self.leadStatus.isOpen = true` | Statuts 1-4 seulement. Confirmé en direct : total 29→32 après ajout des 3 leads (statuts 1, 2, 3). `[prouvé REST]` |
| `crm.closed.lead` (grid+form **seul**, pas de kanban) | `self.leadStatus.isOpen = false` | Un lead « Converti »/« Perdu » ne s'affiche JAMAIS en kanban — conception de l'écran, pas un défaut. `[SCHEMA]` |
| `crm.my.lead` | `self.user.id = :_internalUserId` | Les 3 leads créés portent `user_id=10` (un utilisateur de démo commercial), même propriétaire que les 6 opportunités `demo-c4` — cohérence de portefeuille commercial. `[SCHEMA]` |

**namecolumn — `full_name`, format `<enterprise_name>, <first_name> <name>`**

Confirmé par coïncidence sur le socle (`'123 Services, Jean-Marc ROGER'`) et reproduit à
l'identique sur les 3 leads créés, `[prouvé REST]` (`GET .../Lead/search` →
`fullName:"OPH Résidences de la Sambre, Sophie LEROY"`, etc.). `simple_full_name` = `<first_name>
<name>`.

**`nextScheduledEventDateT` — champ calculé, servi par le serveur, PAS posé en SQL**

Ce champ (visible dans le payload REST du Lead) reflète le **prochain** événement `Planned`
rattaché via `ical_event.event_lead` — vérifié en direct : le lead lié à un événement futur
(`Planned`, 2026-09-10) le sert (`"2026-09-10T09:00Z"`), le lead lié uniquement à un événement
passé (`Realized`, 2026-07-10) le sert à `null`. **Ne jamais poser ce champ directement en SQL**
— il découle exclusivement d'`ical_event`. `[prouvé REST]`

## 2. `crm_opportunity`

**Deux populations pré-existantes, une créée**

- **32 lignes socle** (`import_origin IS NULL`, ids 1-32) — thème générique ESN, **intouchées**
  par cette mission, à l'exception du couple statut/probabilité documenté §3 (mesuré, pas
  corrigé).
- **6 lignes `demo-c4`** (ids 958001-958006, campagne antérieure) — échelle de statut complète,
  vocabulaire BTP réaliste. **1 complétée** (958006 : motif de perte posé, satellite resté vide,
  voir §4) ; **1 rattachée à une commande** (958005, voir §5) ; les 4 autres non touchées.
- **1 ligne créée par cette mission** (958007, `import_origin='demo-c5-crm'`) — voir §0 pour
  l'origine (test REST de H-CRM-09) et §5 pour le contenu final.

**Domaine filtrant qui exclut le NULL/le fermé**

| Menu / vue | Prédicat | Conséquence |
|---|---|---|
| `crm.opened.opportunity` (kanban+grid+form, `home="true"`) | `self.opportunityStatus.isOpen = true` | Statuts 1-4 seulement (Nouveau/Qualification/Proposition/Négociation). Une opportunité `opportunity_status IS NULL` serait exclue des DEUX buckets (3 valeurs logiques SQL : `NULL = true` et `NULL = false` sont tous deux indéterminés) — raisonnement structurel, confirmé par analogie testée côté Lead (H-CRM-10). `[SCHEMA + INFERE]` |
| `crm.closed.opportunity` (grid+form **seul**, pas de kanban) | `self.opportunityStatus.isOpen = false` | Une opportunité Fermée gagnée/perdue ne s'affiche JAMAIS dans le kanban `opportunity-kanban` — conception de l'écran. Confirme et généralise H-CRM-10. `[SCHEMA]` |
| kanban `columnBy="opportunityStatus"`, `sequenceBy="orderByState"` | — | `order_by_state` pilote l'**ordre d'affichage** des colonnes/cartes, pas leur appartenance (`opportunityStatus` seul décide de la colonne). Une désynchronisation `order_by_state ≠ opportunityStatus.sequence` ne fait PAS disparaître la carte, mais la place au mauvais endroit dans l'ordre — piège 70/92 confirmé une 2ᵉ fois cette mission (958007 créé par REST avec `order_by_state=0` alors que son statut par défaut "Nouveau" porte `sequence=1` — **nouveau piège 93**, voir ci-dessous). `[prouvé REST]` |

**Piège 93 — un enregistrement créé par le moteur peut lui-même naître désynchronisé**

Contrairement à ce que suggérait le seul cas connu jusqu'ici (une désynchronisation causée par
un `UPDATE` qui ne touche qu'un des deux champs corrélés), **la création moteur elle-même** peut
produire un état incohérent dès l'origine : `POST /ws/rest/.../Opportunity` sans `orderByState`
explicite a créé 958007 avec `opportunityStatus` par défaut "Nouveau" (`sequence=1`) MAIS
`order_by_state=0` — aucun mécanisme serveur ne les a synchronisés au moment de la création.
Sur cette base, l'audit (`audit-completeness.sql`, dimension 7) le détecte (`crm_opportunity.
order_by_state ≠ statut.sequence`) : **toujours relancer ce contrôle après toute création via
REST/moteur, pas seulement après un `UPDATE` SQL.**

**namecolumn — `name` (NOT NULL en base), `opportunity_seq` auto-généré par le moteur au format `O00NN`**

`opportunity_seq` n'a pas besoin d'être posé en SQL sur une opportunité créée par le moteur
(REST ou action-method) : il est consommé au save, comme confirmé sur 958007 (`'O0040'`,
compteur métier `base_sequence_version` avancé à 41 par le moteur lui-même, **aucune**
désynchronisation contrairement au cas `purchaseOrder` de `entites-achats.md`). Pour une
opportunité posée intégralement en SQL (règle 12 : cas normal, aucune contrepartie
comptable), `opportunity_seq` resterait NULL sauf à le poser à la main — **non re-testé sur ce
chemin précis cette mission**, toute création faite ici est passée par le moteur (958007).

**`eventList` — panneau d'historique confirmé existant et servi**

Contrairement à ce que le dossier d'hypothèses ne pouvait pas établir (§5 du dossier d'hypothèses,
« aucune preuve d'un panneau dédié »), le payload REST de l'Opportunité **porte un champ
`eventList`** peuplé dès qu'un `ical_event.opportunity` pointe la ligne — vérifié après l'ajout
d'un événement sur 958007. `[prouvé REST]` `GET .../Opportunity/958007` →
`eventList:[{subject:"RDV de qualification — présentation de l'offre", id:64}]`,
`nextScheduledEventDateT:"2026-09-22T08:00Z"`.

## 3. Le couple statut ↔ probabilité — mesure, constat, décision proposée

**Mesure** (32 opportunités socle, `import_origin IS NULL`) :

| Statut | is_open | n | probabilité min | max | moyenne |
|---|---|---|---|---|---|
| Nouveau | true | 8 | 15 | 78 | — |
| Qualification | true | 9 | 34 | 94 | — |
| Proposition | true | 6 | 23 | 90 | — |
| Négociation | true | 3 | 54 | **100** | — |
| Fermée gagnée | false | 4 | **47** | 100 | — |
| Fermée perdue | false | 2 | 0 | **93** | — |

**8 lignes concrètement incohérentes** (`Fermée perdue` avec probabilité > 0, `Fermée gagnée`
≠ 100 %, `Négociation` ≥ 95 % — un stade non clos affichant une quasi-certitude) : ids 3, 16,
25, 26, 27, 28, 29, 30 — **toutes appartiennent aux 32 opportunités socle**, aucune au jeu
`demo-c4` ni aux créations de cette mission.

**Conséquence écran** : le kanban `opportunity-kanban` applique un `hilite` sur `probability`
(`danger` ≤25 %, `warning` <50 %, `info` ≥50 %, `success` ≥75 %) — une opportunité "Négociation"
à 100 % s'affiche en vert "success" dans une colonne qui n'est censée représenter aucune
certitude de gain. **Toute démo qui ouvre ce kanban et s'attarde sur les probabilités affiche
une incohérence visible au premier regard**, sur des lignes qui ne font PAS partie du jeu BTP
mis en avant (`demo-c4` + 958007), mais qui partagent le même écran.

**Décision proposée — PAS EXÉCUTÉE, réservée à l'arbitrage du propriétaire de la base** :

- **Option A — ne pas toucher** (retenue par défaut dans cette mission). Les 32 lignes sont un
  socle antérieur non créé par cette campagne ; aucun précédent n'autorise à les corriger en
  masse (contrairement à `demo-c4`, dont 958004 a déjà un précédent de correction ciblée et
  documentée). Risque : si un présentateur ouvre ce kanban en filtrant sur TOUTES les
  opportunités (pas seulement BTP), l'incohérence est visible.
- **Option B — corriger les 8 lignes** (`UPDATE crm_opportunity SET probability = CASE
  opportunity_status ... END WHERE id IN (3,16,25,26,27,28,29,30)`), en clampant chaque
  probabilité sur la borne cohérente de son statut (`Fermée perdue`→0, `Fermée gagnée`→100,
  `Négociation`→≤94 pour rester sous le seuil `success`). Coût : 8 lignes, aucune dépendance FK
  descendante identifiée (aucune des 32 n'a de `sale_sale_order` rattachée, vérifié en amont du
  dossier d'hypothèses : `sale_sale_order.opportunity IS NOT NULL` = 0 avant cette mission,
  toujours vrai sur ces 32 après). Un correctif serait donc **techniquement isolé**, sans
  effet de bord détecté — mais reste une décision sur des données qui n'appartiennent pas à
  cette mission.

**Cette question est documentée et laissée OUVERTE**, conformément à la frontière
FAITS/ARBITRAGES : la mesure et le risque sont établis, le choix d'y toucher ou non revient au
propriétaire de la base.

## 4. Référentiels créés

| Table | Avant | Créé | Valeurs |
|---|---|---|---|
| `base_function` | 6 (IT/génériques : Chef de projet, Responsable Achats, PDG, Consultant, Gérant, Acheteur) | +3 | Architecte, Maître d'ouvrage / Directeur de programmes, Conducteur d'opérations (immobilières) |
| `crm_lost_reason` | 0 | +3 | Budget non validé, Concurrent retenu, Projet abandonné ou ajourné |
| `base_industry_sector` | 0 | +2 | Bâtiment et travaux publics, Promotion immobilière et aménagement |
| `base_partner` (prospect + contact) | — | +2 | `OPH Résidences de la Sambre` (id 10227, bailleur social, Nord, `is_prospect=true`) + contact `LEROY Sophie` (id 10228, Maître d'ouvrage / Directrice de programmes) |
| `message_email_address` | — | +3 | 1 par lead créé |

Aucune valeur inventée hors référentiel (règle 4) : chaque FK résolue par sous-requête sur un
`name`/`code` réel, garde `RAISE EXCEPTION` en fin de script si une résolution échoue.

## 5. Ce qui a été écrit — récapitulatif

| Objet | Table | Action | Détail |
|---|---|---|---|
| 3 leads BTP | `crm_lead` | INSERT | `import_origin='demo-c5-crm'`, 1 par statut ouvert (À traiter/Qualification marketing/Qualification commerciale), tous complétés (job_title_function, industry_sector, adresse régionale réelle, source, équipe). |
| Opportunité 958007 | `crm_opportunity` | INSERT (REST) + UPDATE (complétion) | Née d'un test H-CRM-09, transformée en prospect légitime : "OPH Résidences de la Sambre — réhabilitation de 40 logements", Qualification, 35 %, 195 k€, contact = LEROY Sophie. |
| Motif de perte | `crm_opportunity` (958006) | Attention : **UPDATE sur pré-existant (demo-c4)** | `lost_reason`/`lost_reason_str` posés — satellite resté vide, jeu explicitement à étendre (voir justification en tête du script SQL). |
| Chaînage CRM→Ventes | `sale_sale_order` (952001) | Attention : **UPDATE sur pré-existant** | `opportunity=958005` — H-CRM-01 confirmée par triple coïncidence (date/tiers/libellé). |
| 8 événements | `ical_event` | INSERT | 6 rattachés aux opportunités demo-c4 + 958007, 2 rattachés aux leads BTP, répartis 2026-03 → 2026-09-22 (passé/présent/futur). |

Scripts SQL, dans l'ordre d'exécution : référentiels, leads, correctif d'un oubli de colonne
(`import_origin` des leads, attrapé par une vérification REST avant l'audit), complétion de
l'opportunité 958007, motif de perte de 958006, événements, rattachement à la commande, avancement
des séquences.

## 6. Ce que ce protocole n'a PAS couvert

- **Aucun écran ouvert au navigateur.** Même contrainte que le protocole achats du même jour
  (extension Chrome déconnectée, profil Playwright verrouillé). Tout ce qui est marqué
  `[prouvé REST]` est un appel HTTP authentifié réel contre le même endpoint que le front React
  (`/ws/rest`, `/ws/action`), réponse JSON observée — preuve solide du mécanisme serveur et de
  la donnée réellement servie, **pas** du rendu pixel (couleur du hilite, disposition du
  kanban, popover de description, icônes d'étoiles de notation).
- **`opportunity_seq` posé en SQL sur une opportunité créée intégralement en SQL** (sans passage
  moteur) n'a pas été testé cette mission — 958007 est passée par le moteur (REST), donc la
  question ne s'est pas posée. Le mécanisme documenté dans le dossier d'hypothèses (consommation au
  premier save) reste `[SUPPOSE]` pour ce chemin précis.
- **Le rendu visuel du panneau « Motif de perte »** sur 958006 n'a pas pu être vérifié à
  l'écran — seule la donnée servie par REST est prouvée (§0/H-CRM-08).
- **`crm_partner_status`** (porté par `base_partner`, distinct de `crm_lead_status`) : non
  creusé, même remarque que le dossier d'hypothèses initial — hors périmètre des deux têtes de
  domaine imposées.
- **Le bouton de conversion Lead → Opportunité** (`ConvertLeadWizardController.convertLead()`)
  n'a pas été exécuté — l'aurait été un test légitime pour enrichir H-CRM-04/06, mais aurait
  consommé un des 3 leads BTP créés et cassé la distribution de statuts visée sans garantie de
  pouvoir revenir en arrière (aucune suppression permise). Reste au statut `[INFERE]` du dossier
  initial (localisé en source, non exécuté).
- **Le couple statut↔probabilité des 32 opportunités socle** : mesuré et documenté (§3), **pas
  corrigé** — décision laissée au propriétaire de la base.
- **La cohérence géographique fine des 3 nouveaux leads** (adresse région ↔ équipe commerciale)
  suit la même logique que les équipes existantes (Nord/Sud/IDF-Exp) mais n'a pas été comparée
  à une répartition commerciale réelle de l'entreprise BTP simulée — plausible, non vérifiée
  au-delà de la cohérence interne.
