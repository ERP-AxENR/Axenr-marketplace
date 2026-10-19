> Apport d'un chef de projet Axelor (paquet du 15/10/2026). Éprouvé sur AOS 9.1.6 / AOP EE 8.2.3. AxENR tourne sur AOP 7.4 / AOS 8.x : chaque piège est une hypothèse à vérifier sur la version cible.
> Rattaché au skill `axelor-import-export` : voir le tableau de routage de son `SKILL.md`.

# Le passage unique sur la base de recette du client

La recette n'est pas un banc d'essai : on y importe **une fois**, ce qui a été prouvé ailleurs. Un
import raté ne s'annule pas, et un second essai à chaud mélange les traces des deux.

## Avant (tout doit être vrai)

- [ ] Le classeur de recette sort du **même générateur et des mêmes données** que le classeur prouvé sur
      l'env jetable, avec deux différences seulement : sans préfixe `TEST-`, et les clés de référentiels
      relues **sur la recette** (`keys` du jour). Toute autre différence = nouvelle preuve. La preuve elle-même
      (`verify_import.py` à 0 écart, rejeu sans doublon, postconditions) est acquise.
- [ ] L'env jetable portait la **même plateforme AOP** que la recette (`info` des deux côtés) ; les écarts de
      modules sont listés et sans effet sur les modèles importés.
- [ ] `check_templates.py … --fields-dir <relevé de la recette> --final` : 0 bloquant, aucune ligne `EXEMPLE-`,
      aucune clé locale d'une autre base.
- [ ] `ee_api.py plan` sur la recette (lecture seule) : chaque ligne annonce la création ou la mise à jour
      attendue ; **aucun « ECRASE »** qui ne soit voulu et listé (un login ou un code déjà pris écrase la fiche).
- [ ] Sauvegarde : dump si l'on a accès à la base ; sinon `ee_api.py export` des fiches que `plan` annonce en
      mise à jour, gardé avec la date.
- [ ] Utilisateurs : `ee_api.py info` (sièges libres) et `plan` — **condition bloquante** : les comptes à
      ouvrir tiennent dans les sièges libres, sinon aucun « prêt » ; la liste des comptes à ouvrir est fixée
      par le client. Redémarrage de l'instance planifié avec qui l'héberge.
- [ ] `ee_api.py links` sur la recette : 0 valeur de lien introuvable.
- [ ] Droit d'import (`canImport`) du compte utilisé, taille du fichier sous le plafond d'envoi (`info`).
- [ ] **Go de l'utilisateur**, avec l'heure : c'est une écriture sur une base partagée du client.

## Après le go, avant l'import

`ee_api.py parse` sur la recette (il dépose une pièce jointe, d'où sa place après le go) : mêmes onglets
et colonnes reconnus qu'en répétition.

## Pendant

`ee_api.py import <Modèle> <classeur> --compute <onglets principaux> --confirm-write <URL exacte de la recette>`
dans l'ordre des classeurs, un classeur à la fois, rapport lu et `verify_import.py` joué **avant** le
classeur suivant.

## Au premier écart

Arrêt. Pas de ré-essai, pas de « petit correctif » rejoué à chaud. On consigne (classeur, onglet, clé,
colonne, attendu, en base, message du rapport), on reproduit sur l'env jetable, on corrige là-bas, on
refait la preuve, et seulement ensuite on reprend en recette, à partir du classeur en cause.

## Après

Compte rendu à l'utilisateur : ce qui est passé (comptes par onglet, écarts à 0), ce qui reste (rejets, points
reportés), les actions post-import (mots de passe, redémarrage, dépôt de fichiers GED…), et les fichiers
envoyés sur l'instance (les `MetaFile` des envois restent en base).
