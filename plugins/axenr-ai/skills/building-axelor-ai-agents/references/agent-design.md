# Concevoir l'agent : prompt, droits, skills, modèle

## Un agent par métier, pas un agent par module

Découper selon **qui parle à l'agent et ce qu'il attend**, pas selon les écrans. Exemple PV :
- *Technicien de maintenance* : le généraliste qui connaît le parc, priorise, diagnostique et **écrit** (journal,
  état, création de matériel) ;
- *Expert onduleurs*, *Expert modules* : lecture seule, réponses techniques profondes, renvoient vers le technicien
  pour écrire.

Un agent qui écrit = un seul, clairement nommé. Les experts restent en lecture seule.

## Structure du prompt système (dans cet ordre)

1. **Rôle et interlocuteur** en 3 lignes : qui il est (un nom aide en démo), pour qui il travaille, à qui il parle,
   tutoiement ou non.
2. **Ce qu'il fait**, numéroté, chaque item avec l'outil ou la skill à utiliser : « Point du matin :
   `pv_alarmes_arrets` + `pv_parc_synthese`, puis 3 à 5 priorités classées par impact ».
3. **Carte des skills** : code + une ligne. Le catalogue natif disparaît après le premier `use_skill`.
4. **Règle d'or** (bloc commun à tous les agents d'une famille) :
   - les faits sur les données viennent des outils, qui calculent ; l'agent cite, il ne recalcule pas ;
   - les faits techniques viennent des skills, chargées **avant** de répondre ;
   - avant toute réponse technique, charger la skill « méthode » (elle contient les pièges) ;
   - sources citées en fin de phrase : (fiche CPV02-OND2), (journal 09/10/2026), (base Huawei – alarmes) ;
   - « ce n'est pas dans ma base » plutôt qu'inventer un code, un seuil, une référence de pièce ou un n° de série ;
   - syntaxe exacte : `use_skill({skill: "<code>", reference: "<nom>"})`.
5. **Désigner un enregistrement** : quel outil accepte quoi, que faire sur `ambigu` (`ask_to_select`) et sur
   `introuvable`.
6. **Écritures** : charger la référence des formats d'abord ; « quand les valeurs sont réunies, appelle directement
   l'outil d'écriture, sans annoncer avant » (un message sans appel d'outil termine le tour et rien n'est écrit) ;
   jamais de suppression ; si l'utilisateur refuse la carte, ne pas réessayer autrement.
7. **Sécurité et limites** propres au métier (consignation électrique, données personnelles, conseil juridique).
8. **Forme** : langue, vocabulaire du métier, longueur, pas de tableau de plus de 8 lignes, terminer par une action
   proposée (ouvrir la fiche, consigner, préparer la liste de pièces).

Pourquoi les sources : l'enquête terrain EnergIA (26 réponses B2B ENR) montre que 10 répondants sur 26 « doivent
tout revérifier » avec les IA généralistes. Une source courte leur permet de vérifier.

## Paramètres

| Paramètre | Valeur conseillée | Raison |
|---|---|---|
| `toolPolicy` | `AUTO` | |
| `maxSteps` | 20 (expert) à 30 (agent qui écrit) | Un diagnostic complet fait 6 à 10 étapes |
| `maxOutputTokens` | 8000 | Vide = 1024 : réponses coupées puis vides |
| `model` | Le meilleur modèle **réellement utilisé avec succès** sur l'instance | Sonnet 5 validé sur PV ; Haiku trop léger pour du diagnostic |
| `audience` | `BUSINESS` | |
| `groups` | Les groupes qui doivent voir l'agent | Sinon l'agent n'apparaît pas dans le chat |
| `suggestions` | 4 questions validées en test | Ce sont les questions de démo |

## Écritures bornées

- Donner `create_record` / `update_record` seulement à l'agent qui écrit, avec `allowedModels` restrictif
  (voir `ai-data-model.md`). Ces outils ont `requiresApproval` : l'utilisateur voit et valide chaque écriture.
- Ne jamais donner `delete_record`.
- Mettre dans une référence de skill les **formats exacts** (`ecrire-dans-le-parc.md` de l'exemple) :
  M2O en `{"id": N}`, champs personnalisés à plat, `version` lue avant `update_record`, corps HTML d'un message.
- Un outil SCRIPT ne peut pas écrire (JPA interdit) : ne pas chercher à contourner, passer par les outils système.

## Ce qui ne marche pas

- Un prompt qui recopie la connaissance métier : il grossit à chaque tour et le modèle n'en lit qu'une partie.
  La connaissance va dans les références, chargées à la demande.
- Laisser le modèle compter ou additionner une liste rendue par un outil : il se trompe (constaté : 9 au lieu de 10,
  « toute la centrale » au lieu d'une tranche). L'outil rend les totaux et les regroupements.
- Des sous-agents (`subAgents`) pour remplacer des skills : non testé, et chaque appel coûte un tour complet.
  Préférer un agent qui possède les skills des experts.
