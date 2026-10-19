> Apport d'un chef de projet Axelor (paquet du 15/10/2026). Éprouvé sur AOS 9.1.6 / AOP EE 8.2.3. AxENR tourne sur AOP 7.4 / AOS 8.x : chaque piège est une hypothèse à vérifier sur la version cible.
> Rattaché au skill `axelor-import-export` : voir le tableau de routage de son `SKILL.md`.

# Faits établis (AOS 9.1.6 / AOP EE 8.2.3, 25/09/2026) et leurs preuves

Env jetable : package Industry 9.1.6 + facturation électronique 9.1.7 + guardian 3.1.1 +
axelor-construction 9.1.0, application nommée comme sur la source ; tous les modules de la recette sauf un,
aux mêmes versions. Les traces (journaux, comparaisons, empreintes) citées dans la colonne « Preuve » ont été conservées
par l'auteur ; elles ne sont pas livrées avec le skill.

## Lus dans le code (AOP 8.2.3, Studio 4.0.7, AOS 9.1.6)

- `ModuleManager.installOne` : `if (!module.isInstalled()) { dataLoader.load(module); … }` ; `resolve` marque
  installé tout module présent dans `meta_module`. Une mise à jour de version ne rejoue pas le data-init.
- `DataLoader` : `data-init/input-config.xml` (`csv-inputs` ou `xml-inputs`), données sous `data-init/input/`.
- `MetaScanner.findWithin` : le module application (`META-INF/axelor-module.properties` dans
  `WEB-INF/classes`, `application = true`) est un module comme un autre : son `data-init` est lu.
- `AppServerStartListener` : `initApps` puis `studio.apps.install` sur `StartupEvent`, donc **après** tous les
  data-init. Pendant le data-init : pas d'AppBase, pas de séquences (créées par l'init-data de l'app Base).
- `CSVImporter.importRow` : `binder.bind` → `call` → `JPA.manage` : **aucun `save()` de repository**.
  Erreur de ligne : « Error while importing <fichier> » / « Unable to import record #n » ; le moteur continue.
- `installApp` : l'init-data d'une app joue si `initDataLoaded` n'est pas vrai — une app Studio dédiée jouerait
  sur une base existante si quelqu'un l'installe à l'écran ou si `studio.apps.install = all`.

## Observés au runtime

| Fait | Preuve |
|---|---|
| L'application s'installe en dernier ; son data-init lit ses 15 fichiers entre « Installing package <application> » et la fusion des vues | journal `catalina-neuve.out` l.1563-1578 |
| Paquet complet, base neuve : 0 erreur d'import du paquet ; près de 200 000 valeurs comparées, 0 écart ; 0 case NULL ; société id 1 | `neuve/verif-journal.txt`, `neuve/comparaison/`, `neuve/controle-sql.txt` |
| Sonde générée par fermeture automatique des liens = sonde écrite à la main (octet pour octet) | test de non-régression du skill |
| Rejeu par configuration d'import : plus de 1 700 lignes, « Not null » égal au nombre de lignes, 0 anomalie, 0 octet modifié (md5 de chaque ligne, versions comprises) | `rejeu/importLog-rejeu.log`, `rejeu/diff-empreintes.txt` vide |
| Base déjà chargée, 5 fiches modifiées + 1 supprimée, redémarrée avec le paquet : paquet non lu, empreintes identiques (seule la ligne `meta_module` de l'application bouge) | `existante/` |
| Témoin (ligne `meta_module` de l'application retirée) : paquet rejoué, modifications écrasées, fiche supprimée recréée | `temoin/` |
| Base neuve EE sans licence : tout enregistrement par l'écran ou l'API refusé (code 1020) ; le data-init passe | appel REST refusé, `enterprise_app_license` vide |
| Licence chargée par l'API comme à l'écran : téléverser le certificat, `action-app-license-fill`, enregistrer `AppLicense` | env de preuve |
| Compteur de séquence réglé par une configuration d'import `SequenceVersion` (`update="true"`) : rejouable ; le tiers suivant porte le numéro attendu (valeur de la source, puis +1) | `geste/` |
| Configuration d'import par l'API : `user` obligatoire ; l'action de lancement exige l'enregistrement complet en contexte ; exécution asynchrone (« Computation in progress ») | `jouer_import_config.py` |
| Copie par `TEMPLATE` : ligne de licence emportée ; la retirer avant démarrage | procédure suivie |
| Erreurs d'autres modules au premier démarrage d'une base neuve (modèles d'impression BTP : app Template non configurée ; rôle `bi.admin` ; extensions de vues introuvables ; app collaboration) | journal, hors fichiers du paquet |

## Non établi

- Coexistence avec un `data-init` déjà présent dans l'application (fusion des inputs) : non testée.
- `xml-inputs` au lieu de `csv-inputs` : non testé dans ce cadre.
- Autres versions de plateforme : re-tester sur une instance jetable avant de s'y fier.
