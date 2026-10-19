# Construire la base de connaissance de l'agent

## Où la mettre

| Besoin | Support | Pourquoi |
|---|---|---|
| Méthode, règles, pièges de raisonnement | `AiSkill.instructions` d'une skill « méthode » | Court, chargé avant chaque réponse technique |
| Connaissance longue (codes d'alarme, procédures, normes, cas terrain) | `AiSkillReference.content`, 10 à 15 000 caractères | Chargée à la demande, en entier, de façon déterministe |
| Données de l'ERP | Outils SCRIPT | Fraîches, calculées |
| Gros corpus documentaire (centaines de PDF) | `AiKnowledgeBase` + `search_knowledge` | Seulement si l'indexation est `INDEXED` sur l'instance |

Une skill par domaine (constructeur, famille de matériel, réglementation), avec une `description` qui liste les
déclencheurs réels : c'est elle que le modèle lit pour choisir.

## Produire la connaissance

1. **Recherche web en parallèle**, un sous-agent par domaine, consigne : français, tableaux denses, identifiants
   **vérifiés** sur la source primaire (manuel constructeur, norme, note du gestionnaire de réseau), « (à vérifier) »
   sinon, 6 à 15 cas terrain de forums (symptôme, cause, résolution, URL), section « Sources » en fin de fichier.
2. **Relire les incertitudes** remontées par chaque sous-agent et les garder visibles dans le texte : le prompt
   impose de citer une valeur « (à vérifier) » avec cette réserve.
3. **Recouper avec les données de démo** (`grep` des codes et seuils des fiches dans la base). Sur PV, la recherche
   a corrigé six erreurs des données : Huawei 61440 n'est pas un ventilateur (2086 / 2087), seuil d'isolement
   Huawei ≥ 1 MΩ et non 50 kΩ, SMA 8001 absent du manuel CORE1 (ventilateur = 8003 puis 6502), Fronius 567 n'est pas
   un ventilateur (326 / 327), Huawei 2070 = îlotage et non batterie, compteur DDSU666-H (monophasé) et non
   DTSU666-H pour un onduleur L1. Une référence de pièce inventée a aussi été retirée.
4. **Ajouter à la skill « méthode » les pièges** vus en test (exemple PV : mesurer une Voc sans lumière, confondre
   « 1/3 de Voc module » et « 1/3 de Voc string »). Le modèle lit bien la base mais raisonne parfois de travers ;
   une règle explicite corrige mieux qu'un exemple.

## Forme d'une référence

- Titre, périmètre (modèles, versions, date du document source), règles de lecture.
- Tableaux : identifiant, libellé, gravité, causes classées, actions pas à pas.
- Procédures numérotées avec la consignation de sécurité.
- Cas terrain avec niveau de fiabilité ([Constructeur], [Forum], [Forum, extrait]).
- « Sources » avec URL. Pas d'emoji (règle du dépôt), pas de donnée personnelle.

## Volume

L'exemple PV : 11 références, 130 000 caractères, 6 skills. Un tour de diagnostic charge 2 à 3 références
(environ 40 000 caractères) : rester sous 15 000 caractères par référence et découper par usage
(alarmes / procédures / cas terrain) plutôt que par constructeur seul.
