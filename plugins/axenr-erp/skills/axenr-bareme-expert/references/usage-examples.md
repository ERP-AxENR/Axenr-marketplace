# /axenr-bareme-expert

Expert du moteur **Pricing** d'Axelor pour les clients AxENR. Va du besoin exprime en langage
naturel, ou d'un document tarifaire (BPU, bordereau, grille de prix), jusqu'aux scripts SQL
livrables et a leur recette.

Detecte automatiquement le client depuis le `cwd` (emeraude-solaire-app / systeko-app /
planeteenr-app / axenr-app) pour adapter la societe, les categories de tiers et les conventions.

## USAGE

```
/axenr-bareme-expert le client veut un tarif de maintenance qui depend de la puissance et du type de client
/axenr-bareme-expert paramétrer ce BPU | ~/Downloads/BPU-2026.pdf
/axenr-bareme-expert pourquoi mon bareme ne s'applique pas sur ce devis ?
```

## CE QU'IL PRODUIT

1. **Analyse de la grille** - axes reels, natures de lignes, incoherences a faire corriger
2. **Tableau de decision** - combien d'articles, quels axes de bareme, et pourquoi
3. **Inventaire de la cible** - prerequis, trous de couverture chiffres, champs a creer
4. **Parametrage** - articles, regles partagees, baremes, lignes de grille
5. **Cahier de recette** - via l'action reelle de l'application, jamais par simulation SQL
6. **Scripts SQL livrables** - numerotes, idempotents, sans identifiant en dur, avec garde-fou
   de prerequis qui interrompt l'integration si l'environnement cible ne convient pas

## POINTS DE VIGILANCE APPLIQUES SYSTEMATIQUEMENT

- `typeSelect` a `'Pricing'` et non `'Default'`, sinon le bareme est ignore en silence
- toute classification decimale retourne un `BigDecimal`, jamais `?: 0`
- prix catalogue a 0 sur les articles et leurs `ProductCompany`, pour eviter le prix fantome
- comportement decide et acte pour : valeur nulle, debordement du dernier palier, segment non couvert
- distinction stricte entre un **prix** et une **regle** (inclus, sur devis, coefficient, remise)

Reference : `references/catalog.md`.
