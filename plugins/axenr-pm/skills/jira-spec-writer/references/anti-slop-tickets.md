# Anti-slop : purger les marqueurs d'écriture IA d'un ticket

Portage du skill `humanizer` (blader/humanizer, v2.8.2, MIT : basé sur *Wikipedia: Signs of AI writing*) au contexte **spécification fonctionnelle Jira**.

## Périmètre : ce qu'on garde, ce qu'on jette

Le skill d'origine vise la prose (billets de blog, essais, écriture personnelle). Un ticket Jira est un **texte technique de référence**. La section « PERSONALITY AND SOUL » du skill d'origine est donc **explicitement écartée** : pas d'opinion, pas de première personne, pas de « laisser entrer un peu de désordre », pas de variation de rythme travaillée. Dans un ticket, le ton neutre et plat *est* le ton humain correct.

| Section d'origine | Statut ici |
|---|---|
| §1 à §5, §7 à §9, §11 à §15, §17 à §25, §27 à §33 | Appliquées, adaptées au FR |
| §10 (règle de trois) | Appliquée en prose, **pas** aux listes factuelles (3 cas de test = 3 cas de test) |
| §16 (listes à en-tête gras) | Appliquée en prose, **pas** aux tableaux de champs ni aux listes de règles |
| §19 (guillemets courbes) | Adaptée : `« »` légitimes en FR, mais valeurs et libellés techniques en guillemets droits |
| §26 (paires avec trait d'union) | Sans objet en français |
| PERSONALITY AND SOUL | **Non appliquée** |

## Passe D : check-list de purge

À exécuter sur le ticket rédigé, avant livraison. Chaque ligne est un pass/fail.

### D.1 Ponctuation et typographie

- [ ] Zéro tiret cadratin `—` et demi-cadratin `–`. Remplacer par un point, une virgule, deux-points ou des parenthèses. Le tiret cadratin est le marqueur IA le plus fiable : contrainte dure, pas une préférence.
- [ ] Zéro emoji, y compris dans les titres et les puces.
- [ ] Zéro gras décoratif. Le gras sert à un libellé de champ ou à un nom d'entité, pas à souligner une idée.
- [ ] Titres en casse phrase (`## Règles de gestion`), pas en Title Case (`## Règles De Gestion`).
- [ ] Valeurs, libellés et sélections entre guillemets droits ou en `code`, jamais en guillemets courbes.

### D.2 Vocabulaire à bannir (équivalents FR des tells)

Emphase et promotion : « joue un rôle clé », « s'inscrit dans une démarche », « constitue une avancée », « robuste », « riche », « puissant », « incontournable », « au cœur de », « véritable », « à forte valeur ajoutée ».

Analyses en participe présent collées en fin de phrase : « permettant ainsi de », « garantissant une meilleure », « assurant la cohérence », « favorisant », « offrant la possibilité de ». Couper la phrase et énoncer la règle.

Remplissage : « il est important de noter que », « à noter que », « dans le but de », « afin de pouvoir », « du fait que », « à l'heure actuelle », « a la capacité de », « il convient de ».

Autorité et signalisation : « la vraie question est », « fondamentalement », « en substance », « entrons dans le détail », « voici ce qu'il faut retenir », « passons maintenant à ».

Conversationnel : « Voici le ticket », « J'espère que cela répond », « N'hésite pas à », « Souhaites-tu que… ». Aucun résidu de dialogue dans le corps du ticket.

### D.3 Fautes structurelles propres aux specs

- [ ] **Un objet, un nom.** Pas de variation élégante. `SaleOrder` reste `SaleOrder` sur tout le ticket, jamais « la commande », puis « le bon de commande », puis « le document de vente ». C'est la règle la plus coûteuse à violer : un développeur qui lit trois noms cherche trois objets.
- [ ] **Un acteur par règle.** Bannir le passif et les fragments sans sujet. « Le champ est renseigné automatiquement » → « Le batch `X` renseigne le champ `Y` ». « Aucune configuration nécessaire » → « L'utilisateur n'a rien à paramétrer ».
- [ ] **Copule assumée.** « `estimatedDate` est la date d'arrivée estimée », pas « `estimatedDate` constitue / représente / fait office de ».
- [ ] **Zéro hedging.** Une règle est vraie ou fausse. « pourrait éventuellement être bloqué » n'est pas une spec. Si l'arbitrage n'est pas tranché, écrire `TODO : arbitrage à confirmer par [nom]` et rien d'autre.
- [ ] **Zéro comblement spéculatif.** Le tell le plus dangereux ici (§21 d'origine) : quand un nom de champ, une entité ou une règle métier est inconnu, l'IA invente un nom plausible. Interdit. Écrire `À confirmer` ou poser la question. Ne jamais présenter une hypothèse comme un existant.
- [ ] **Attribution nommée.** Pas de « certains utilisateurs remontent », « les retours terrain montrent ». Nommer : le client, la personne, le ticket source, la date de la réunion.
- [ ] **Pas de section « Enjeux », « Perspectives » ou « Conclusion ».** Un ticket se termine sur les cas de test.
- [ ] **Pas de narration du diff.** La spec décrit l'état cible. « Cette action remplace l'ancien traitement qui bouclait sur tous les enregistrements » va dans le contexte (section 1), pas dans la spec (section 3).
- [ ] **Pas de phrase de chauffe sous un titre.** `### Règles de gestion` suivi de « Les règles de gestion sont les suivantes : » → supprimer la phrase.
- [ ] **Pas de rythme staccato ni de punchline.** « Le stock ne bouge pas. Aucun mouvement. Rien. » → une phrase, factuelle.

### D.4 Faux positifs : ne pas corriger

Ne pas casser une prose légitime au nom de la purge :

- Un tableau de champs avec libellés en gras est la bonne forme, pas un tell.
- Trois cas de test (nominal, limite, erreur) est une structure imposée, pas une règle de trois.
- Le vocabulaire technique précis (`@Transactional`, « idempotent », « nomenclature douanière ») reste tel quel.
- Une phrase courte isolée pour trancher un point est humaine. Le tell, c'est la rafale.
- Ne jamais réécrire un extrait cité : verbatim client, message d'erreur, libellé existant en base, nom de menu. Ces textes sont des données, pas de la rédaction.

## Boucle de production

1. Rédiger le **brouillon** du ticket selon la structure en 4 sections.
2. Se poser explicitement la question : **« qu'est-ce qui, dans ce texte, sonne encore généré ? »** et lister les tells restants en 2 à 4 puces internes.
3. Produire la **version finale** qui les corrige.
4. Scanner une dernière fois `—`, `–`, les emojis et les participes présents en fin de phrase. Un seul hit signifie que la version finale n'est pas prête.

Ne livrer que la version finale à l'utilisateur. Le brouillon et les puces de diagnostic restent internes, sauf demande explicite.

## Exemples avant / après

**Avant**
> Cette évolution s'inscrit dans une démarche globale de fiabilisation du flux logistique et constitue un jalon clé du projet, permettant ainsi de garantir une meilleure traçabilité des réceptions — tout en offrant aux utilisateurs une expérience plus fluide.

**Après**
> Aujourd'hui la date d'arrivée en stock est saisie à la main, ce qui produit des écarts avec le transitaire. L'objectif est de la calculer à partir des dates renvoyées par l'API SIFA.

**Avant**
> - **Performance :** Les temps de traitement ont été significativement améliorés.
> - **Sécurité :** La sécurité a été renforcée.
> - **Ergonomie :** L'ergonomie a été repensée.

**Après**
> Le batch traite 10 000 lignes en moins de 2 minutes. L'accès à l'écran est restreint au rôle `ChargéAffaires`.

**Avant**
> Le champ pourrait éventuellement être rendu obligatoire selon le statut, ce qui devrait probablement couvrir la majorité des cas.

**Après**
> `dateMiseEnService` est obligatoire au passage au statut `In Progress`. Aucune autre condition.

## Source

Adapté de [blader/humanizer](https://github.com/blader/humanizer) (licence MIT), lui-même fondé sur [Wikipedia: Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing), maintenu par WikiProject AI Cleanup.
