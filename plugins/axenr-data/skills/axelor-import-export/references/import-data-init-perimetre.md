> Apport d'un chef de projet Axelor (paquet du 15/10/2026). Éprouvé sur AOS 9.1.6 / AOP EE 8.2.3. AxENR tourne sur AOP 7.4 / AOS 8.x : chaque piège est une hypothèse à vérifier sur la version cible.
> Rattaché au skill `axelor-import-export` : voir le tableau de routage de son `SKILL.md`.

# Format du périmètre (`perimetre.json`)

Un seul fichier décrit ce qu'on reprend ; tous les scripts le lisent. Exemple réel et prouvé :
`assets/perimetre-exemple.json`. Chemins relatifs au fichier.

| Clé | Rôle |
|---|---|
| `application` | nom du module application (`appName`), qui porte le paquet ; cherché au journal (« Installing package <nom> ») et dans `meta_module` |
| `contexte` | listes nommées utilisables dans les domaines (`:tiers`), lues dans un CSV : `{"tiers": {"csv": "tiers.csv", "colonne": "importId"}}` |
| `cles_cibles` | clé métier de chaque modèle **pointé** par un lien : sert à écrire la valeur (oracle) et à la rechercher (paquet). Une cible absente est liée par `importId` (le générateur le signale) |
| `modeles[]` | un objet par modèle repris (voir ci-dessous) |
| `ordre_paquet` | ordre des inputs : parents avant enfants, **un input par niveau** (un input ne voit pas les fiches qu'il vient de créer) |
| `tables_liaison` | tables plusieurs-à-plusieurs à inclure dans l'empreinte SQL |
| `base_neuve` | `"Modèle|champ": [valeurs]` présentes sur une base neuve **avant** le data-init de l'application (data-init des modules standard) — à vérifier sur une vraie base neuve |
| `sonde.garder` | clés retenues pour la sonde (`"*"` = toutes) ; le générateur ajoute la fermeture des liens |
| `sonde.enfants` | enfants à garder pour un parent retenu (lien inverse) : `{"PartnerAddress": {"champ": "partner", "parent": "Partner"}}` |

Objet `modeles[]` :

| Clé | Rôle |
|---|---|
| `nom`, `type` | nom court (fichiers) et nom complet du modèle |
| `domaine` | domaine JPQL qui isole les fiches à reprendre sur la source (et à relire sur la base recréée) |
| `cle` | champ clé de ligne dans l'oracle et la comparaison |
| `recherche` | recherche de l'input (défaut `self.<cle> = :<cle>`) — une clé **stable**, jamais un id |
| `non_ecrits` | champs relus mais **non écrits** par le paquet → écarts attendus (dire pourquoi dans `pourquoi_non_ecrits`) |
| `lignes_exclues` | lignes de l'oracle laissées à la plateforme (ex. groupe `admins`) |
| `table`, `filtre_sql` | pour `controle_sql.py` (env de preuve, accès PostgreSQL) |

Mettre dans `non_ecrits` : les côtés inverses (`mappedBy`), les champs calculés par un listener, les fiches de
démo accrochées que la décision exclut (configurations de société, rôles d'un groupe), les fichiers.
