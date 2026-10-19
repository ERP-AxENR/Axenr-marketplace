# Exemple de spécification remplie

Spécification réelle du produit GMAO (facturation depuis l'intervention), dans la structure arbitrée le 08/08/2026.

```markdown
## Objectif métier
Les clients qui facturent leur maintenance à la visite doivent aujourd'hui quitter l'intervention,
retrouver le contrat ou la commande, et déclencher la facturation à la main, sans voir ce qui a
déjà été facturé. Résultat : oublis de facturation et doubles facturations.

S'ajoute le cas de l'intervention qui a donné lieu à une vente (devis créé depuis le mobile,
cf. GMAO-94, puis transformé en commande) : c'est cette commande qu'il faut facturer, pas le contrat.

Aujourd'hui                          Cible
Intervention validée                 Intervention validée
   │                                    │
   └─> sortir de l'intervention         └─> bouton « Facturer »
       chercher le contrat                     │
       facturer à la main                      ├─> commande si confirmée
       (aucune visibilité)                     └─> contrat sinon

## Spécification fonctionnelle

### Configurations initiales
Nouveau champ sur l'intervention : Non facturé / Facturé, valeur par défaut « Non facturé »,
filtrable et affichable en colonne dans la liste des interventions.

### Process
1. Le bouton « Facturer » est visible sur l'intervention seulement si statut = Validé et
   flag = Non facturé : [capture : emplacement du bouton dans la barre d'actions]
2. Au clic, le système facture la commande client de l'intervention si elle est au statut
   « Commande confirmée » et non facturée ; sinon il facture le contrat de maintenance rattaché.
   Les actions de facturation existantes (commande, contrat) sont réutilisées.
3. La facture générée est rattachée à l'intervention et consultable depuis celle-ci.
4. À la ventilation de la facture, le flag passe à « Facturé », quelle que soit l'origine.

## Périmètre
Facturation totale de la commande ou du contrat. La facturation partielle à la visite est
renvoyée en V3.5 (GMAO-93).

## Recette
- Intervention non validée : pas de bouton.
- Intervention validée et déjà facturée : pas de bouton.
- Commande confirmée non facturée : la facture reprend la commande, même si un contrat est rattaché.
- Commande déjà facturée et contrat : la facture reprend le contrat.
- Ventilation de la facture : l'intervention passe à « Facturé ».

## Points ouverts
1. Ni commande facturable ni contrat : bouton masqué, ou visible avec un message bloquant ?
   Position par défaut : masqué. À trancher.
2. Commande à un autre statut que « Commande confirmée » : on bascule sur le contrat. À confirmer.
3. Commande partiellement facturée : traitée comme déjà facturée (repli sur le contrat). À trancher.

## Points techniques
- Injection règle de droit : sans objet (aucun nouvel objet).
- Injection configuration init : sans objet.
- Script de migration : initialiser le flag à « Facturé » pour les interventions dont une facture
  ventilée existe déjà.
```
