# Où sont les données du parc PV dans Axelor

## Modèle unique : `com.axelor.apps.intervention.db.Equipment` (menu Gestion des actifs > Équipements)
- Arborescence par `parentEquipment` : **centrale** (lieu racine, famille PV-CENT) > éventuellement **tranche / zone** (lieu, PV-ZONE) > **matériels**.
- `typeSelect` : `place` = Lieu, `equipment` = Matériel. `code` : CPV01…CPV05 pour les centrales, CPV01-B-OND3 = centrale 1, tranche B, onduleur 3.
- Champs standard : `name`, `code`, `sequence` (EQ…), `partner` (client), `equipmentFamily`, `commissioningDate` (mise en service),
  `customerWarrantyOnPartEndDate` (« Fin de garantie client sur pièces » = fin de garantie pièces), `inService` (en service / à l'arrêt),
  `indicatorSelect` (calculé, lecture seule : 1 sous contrat opérationnel, 2 sous contrat non opérationnel, 3 hors contrat opérationnel, 4 hors contrat non opérationnel),
  `comments` (255 car. max), `scheduleOfOperation`, `specificAccessSchedule` (consignes d'accès).
- **Champs personnalisés** (stockés dans `attrs`, mais à lire et écrire **à plat** comme des champs normaux) :
  | Champ | Libellé | Sur |
  |---|---|---|
  | pvFabricant, pvModele | Fabricant, modèle | tous |
  | pvNumeroSerie | N° de série | matériel |
  | pvPuissance | Puissance nominale (kW / kVA / kWc) | tous |
  | pvGarantieConstructeur | Garantie constructeur (type, durée, extension) | tous |
  | pvDateDerniereMaintenance, pvDateProchaineMaintenance | dates de maintenance | tous |
  | pvDerniereAlarme | Dernière alarme / état technique | matériel |
  | pvFirmware, pvAdresseIp, pvNbMppt, pvConfigStrings | firmware, IP, nb MPPT, câblage strings | matériel |
  | pvAdresseSite, pvGps, pvPdl, pvPuissanceInjection, pvTypeContrat, pvContactSite, pvProductibleAnnuel | site | lieu |
  | pvFicheTechnique | fiche technique constructeur (texte long) | tous |
- **Journal d'intervention** = messages (`com.axelor.mail.db.MailMessage`, `type = comment`) rattachés à la fiche
  (`relatedModel = com.axelor.apps.intervention.db.Equipment`, `relatedId` = id de la fiche). Les dates réelles sont écrites dans le texte du message.

## Familles (id → code)
1 PV-CENT Centrale · 2 PV-ZONE Zone/tranche · 3 PV-OND Onduleur · 4 PV-MOD Champ de modules · 5 PV-STRU Structure · 6 PV-CDC Coffret DC ·
7 PV-TGBT TGBT/coffret AC · 8 PV-COMPT Comptage · 9 PV-SUPV Supervision · 10 PV-METEO Météo · 11 PV-BATT Batterie · 12 PV-OPTI Optimiseur · 13 PV-SECU Sécurité

## Lire
- Toujours d'abord les outils serveur : `pv_parc_synthese` (toutes les centrales), `pv_fiche_equipement` (une fiche complète + journal),
  `pv_garanties` (échéances), `pv_alarmes_arrets` (pannes et alarmes). Ils calculent les jours restants et les totaux : ne recalcule pas.
- `search_records` seulement pour un critère que ces outils ne couvrent pas ; ne jamais filtrer sur `archived`.

## Ouvrir une fiche à l'écran
`open_view({action: "assets.management.root.equipment", model: "com.axelor.apps.intervention.db.Equipment", id: <id>, viewType: "form"})`.
