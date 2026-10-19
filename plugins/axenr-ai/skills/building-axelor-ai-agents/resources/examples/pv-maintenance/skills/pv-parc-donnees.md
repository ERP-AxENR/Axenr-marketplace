# Parc PV : données et gestes
Charge la référence utile :
- `donnees-parc` : modèle Equipment, arborescence centrale > tranche > matériel, champs standard et personnalisés, familles, journal, écran.
- `ecrire-dans-le-parc` : consigner une intervention, mettre à jour l'état d'un matériel, créer un matériel (formats exacts de create_record / update_record).
`use_skill({skill: "pv-parc-donnees", reference: "ecrire-dans-le-parc"})` avant toute écriture.
