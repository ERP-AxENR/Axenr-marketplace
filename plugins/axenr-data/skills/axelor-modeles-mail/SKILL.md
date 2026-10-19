---
name: axelor-modeles-mail
description: >
  Creation et depannage des modeles de mail Axelor (Template, moteur
  StringTemplate) sur une instance AxENR : variables, langues FR / EN, test,
  pieces jointes. Declencheurs : « modele de mail », « template de mail »,
  « Config applicative > Message > Modeles », « StringTemplate », « la variable
  ressort vide », « le mail affiche Partner{id=...} », « la piece jointe ne
  s'attache pas », « mail de relance », « mail de consultation », « Test
  template », « duplicate key template_print_model ». PAS pour : templates Word
  d'impression (axenr-template-expert), envoi ou campagne marketing, imports
  (axelor-import-export).
metadata:
  owner: axenr
  family: fonctionnel
---

# Modeles de mail Axelor (Template)

## Environnement d'execution

| Ou | Comportement |
|---|---|
| Claude Code | Lecture seule du projet (cwd) ; client detecte avec le skill `client-context-detector` ; livrables ecrits dans `~/Downloads`. |
| claude.ai et Cowork | Pas d'acces au code : demander l'instance concernee, l'objet Axelor et un enregistrement de test ; livrer le contenu du modele pret a coller. |

Objet Axelor : `com.axelor.message.db.Template`. Ecran : Config applicative > Message > Modeles (ou « Template » selon l'instance).

## 1. Identifier le bon objet Axelor avant de creer les modeles

Ne pas supposer qu'un usage metier correspond a un objet dedie. Exemple vecu : consultation fournisseurs, bon de commande et relances J-15 / J-8 etaient tous portes par le meme objet `PurchaseOrder` (la consultation etant une commande d'achat sur fournisseur fictif, la commande ferme la meme commande reaffectee au fournisseur reel). Verifier le modele metier reel du lot concerne avant de demarrer, sinon les modeles sont mal rattaches.

## 2. Syntaxe StringTemplate (ST4) : la regle de casse

La variable de contexte est le nom du modele avec majuscule initiale :

- Correct : `$PurchaseOrder.purchaseOrderSeq$`, `$StockMove.stockMoveSeq$`
- Faux : `$purchaseOrder.purchaseOrderSeq$`, `$stockMove.stockMoveSeq$`

Une casse incorrecte ne leve aucune erreur : Axelor renvoie une chaine vide. C'est la cause n°1 des « cette variable ressort toujours vide » alors que la donnee existe en base.

## 3. Champ objet utilise nu

Un champ de type entite (Partner ou autre) utilise sans sous-propriete affiche le `toString()` Java brut :

```
Partner{id=123, partnerSeq=XX-0001, name=..., firstName=..., ...}
```

Toujours ajouter un sous-champ concret : `.name`, `.fullName`, `.emailAddress.address`. Jamais `$PurchaseOrder.supplierPartner$` seul : `$PurchaseOrder.supplierPartner.emailAddress.address$` (champ A) ou `$PurchaseOrder.supplierPartner.name$` (corps).

## 4. FR et EN = deux Template distincts

Une version FR et une version EN d'un meme mail sont deux enregistrements Template, chacun avec :

- sa propre Localisation (`fr_FR` / `en_US`) ;
- son propre nom (ex. `<Prefixe> - Consultation fournisseur FR` / `... EN`) ;
- le meme Modele (objet Axelor).

La Localisation permet la selection automatique du bon Template selon la langue du partenaire (fiche Partner > langue). Sans automatisation prevue au perimetre, l'utilisateur choisit le Template a l'envoi.

## 5. Tester un modele

1. Ouvrir le Template, cliquer « Test template ».
2. Dans la modale « Reference », choisir le type d'objet puis un enregistrement reel.
3. Cliquer « Generer le message » (« OK » seul ne declenche rien).
4. Le message genere s'ouvre : verifier A, Sujet, Corps.
5. Tester un enregistrement par langue, et un enregistrement a un stade avance du workflow metier (les champs remplis tardivement sinon donnent de faux negatifs).

## 6. Un champ vide au test n'est pas toujours un bug de modele

Avant de corriger la syntaxe, verifier sur la fiche source que le champ est reellement rempli a ce stade du workflow (ex. date de livraison inconnue au stade consultation). Les champs propres a un client (prefixe `<client>_` en base) sont souvent regroupes dans un onglet dedie au nom du client sur le formulaire : les chercher la.

## 7. Trouver les vrais noms de champs sans acces au code

Avec un acces SQL en lecture seule (le plus fiable) :

```sql
-- 1. Nom exact de la table
SELECT table_name FROM information_schema.tables WHERE table_name ILIKE '%mot_cle%';

-- 2. Colonnes (snake_case en base -> camelCase dans StringTemplate)
SELECT column_name, data_type FROM information_schema.columns
WHERE table_name = 'nom_de_la_table' ORDER BY ordinal_position;

-- 3. Si meta_field est peuple pour ce modele : nom technique + libelle
SELECT name, title, type_name FROM meta_field
WHERE model = 'com.axelor.apps.xxx.db.NomDuModele' ORDER BY name;
```

Avec un acces navigateur ou API, sans SQL :

```
GET https://<host>/ws/rest/<FQN complet de la classe>/<id d'un enregistrement reel>
```

Le JSON brut donne les vrais noms de champs et leurs valeurs. FQN corrects : `com.axelor.apps.purchase.db.PurchaseOrder`, `com.axelor.apps.stock.db.StockMove` (jamais `com.axelor.stock.db.StockMove`, qui leve une `ClassNotFoundException`).

## 8. Pieces jointes : deux mecanismes distincts

**a) « Modele d'impression Template »** (champ avec loupe, en haut du formulaire)

- Pointe vers un rapport Studio (docx / xlsx / pdf).
- Relation strictement 1-a-1 en base (contrainte unique sur `template_print_model`) : un rapport Studio ne peut etre lie qu'a un seul Template. Le reutiliser leve `duplicate key value violates unique constraint` (HTTP 500 « Violation de contrainte unique »).
- Pour reutiliser un rapport identique sur plusieurs Template : le dupliquer dans Studio (bouton « New » dans la modale du champ), un exemplaire par Template.

**b) « Fichiers attaches > Modele d'impression »** (liste deroulante, plus bas)

- Pointe vers les rapports BIRT (`print.conf.printing.templates`).
- Relation many-to-many, reutilisable entre plusieurs Template.
- La case « Attacher » doit etre cochee. Elle ne garantit pas que la generation fonctionne : le rapport BIRT peut planter cote serveur (HTTP 500, `com.axelor.apps.base.web.MessageController`) et le mail part quand meme, sans piece jointe, en silence.
- Verification : ouvrir le message genere (Test template > Generer le message) et cliquer son bouton « Imprimer ». L'erreur serveur s'affiche si le rapport est casse.

## 9. Verifier le perimetre avant d'automatiser une piece jointe

Un ticket peut exclure explicitement la generation ou l'attachement automatique de la piece jointe. Le mail peut alors dire « vous trouverez ci-joint » alors que l'utilisateur attache le fichier a la main (trombone) a l'envoi : ce n'est pas un defaut du modele. Relire le perimetre avant de corriger un mecanisme d'attachement.

## 10. Checklist de livraison

- [ ] Objet Axelor confirme (pas suppose) pour chaque usage metier
- [ ] Toutes les variables en `$ModeleAvecMajuscule.champ$`
- [ ] Aucun champ objet utilise sans sous-propriete
- [ ] FR et EN = deux Template avec la bonne Localisation
- [ ] Teste via « Generer le message » sur un enregistrement par langue, a un stade avance du workflow
- [ ] Tout champ vide au test verifie sur la fiche source avant d'etre traite comme un bug
- [ ] Piece jointe : perimetre verifie ; si demandee, testee via « Imprimer » sur le message genere
