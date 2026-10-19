# Écrire dans le parc PV (toujours avec la carte d'approbation)

Règle : quand toutes les valeurs sont réunies, **appelle directement l'outil d'écriture**, sans message d'annonce avant
(un message sans appel d'outil termine ton tour et rien ne serait écrit). L'utilisateur approuve ou refuse sur la carte.
Après approbation : une phrase qui dit ce qui a été écrit, avec le code de la fiche. S'il refuse : tu ne réessaies pas.
Tu ne supprimes jamais rien.

## 1. Consigner une intervention / une observation dans le journal
`create_record` sur `com.axelor.mail.db.MailMessage` :
```json
{"model": "com.axelor.mail.db.MailMessage",
 "data": {"type": "comment", "subject": "<objet court : Diagnostic, Remplacement, Visite préventive…>",
          "body": "<p>JJ/MM/AAAA - <technicien si connu> : constat, mesures (valeurs + unités), cause, action, pièces, suite à donner.</p>",
          "relatedModel": "com.axelor.apps.intervention.db.Equipment", "relatedId": <id de la fiche>, "relatedName": "<nom de la fiche>"}}
```
L'id se lit par `pv_fiche_equipement`. Le texte reprend la date du jour (rendue par les outils : `date_du_jour`).

## 2. Mettre à jour l'état d'un matériel (mise à l'arrêt, remise en service, nouvelle alarme, nouveau firmware)
1. `read_record` sur la fiche pour obtenir `version` (obligatoire).
2. `update_record` avec uniquement les champs changés, champs personnalisés à plat :
```json
{"model": "com.axelor.apps.intervention.db.Equipment", "id": <id>, "version": <version>,
 "data": {"inService": false, "pvDerniereAlarme": "Alarme 2062 … - mis à l'arrêt le 19/10/2026"}}
```
Puis consigne la raison dans le journal (geste 1).

## 3. Créer un matériel (ex. onduleur de remplacement, batterie ajoutée, nouvel équipement)
1. Retrouve le parent (centrale ou tranche) par `pv_fiche_equipement` → son `id` et son client (`partner`).
2. Demande les valeurs manquantes par `ask_to_input` (n° de série, date de mise en service, fin de garantie). N'invente jamais un n° de série.
3. `create_record` :
```json
{"model": "com.axelor.apps.intervention.db.Equipment",
 "data": {"code": "<code parent>-<suffixe ex. OND6>", "name": "<Onduleur 6 - modèle>", "typeSelect": "equipment",
          "partner": {"id": <id client du parent>}, "parentEquipment": {"id": <id parent>}, "equipmentFamily": {"id": 3},
          "commissioningDate": "AAAA-MM-JJ", "customerWarrantyOnPartEndDate": "AAAA-MM-JJ", "inService": true,
          "pvFabricant": "Huawei", "pvModele": "SUN2000-50KTL-M3", "pvNumeroSerie": "…", "pvPuissance": 50,
          "pvGarantieConstructeur": "…", "pvNbMppt": 4}}
```
**Ne jamais envoyer un objet `attrs`** : l'outil le refuse (« argument type mismatch »). Les champs pv… se passent au même niveau que `name`.
Pour un remplacement : passe l'ancien matériel `inService: false`, note l'ancien S/N dans le journal des deux fiches.
