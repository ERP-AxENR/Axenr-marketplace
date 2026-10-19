  var t = trouver(input && input.equipement);
  if (!t.equipement) { return t; }
  var e = t.equipement, a = attrsDe(e);
  var enfants = Q.of(EqCls).filter("self.parentEquipment.id = :id").bind("id", e.getId()).order("code").fetch(200);
  var listeEnfants = [];
  for (var i = 0; i < enfants.size(); i++) { listeEnfants.push(resume(enfants.get(i))); }
  var c = centraleDe(e), ac = attrsDe(c);
  var fin = e.getCustomerWarrantyOnPartEndDate() ? String(e.getCustomerWarrantyOnPartEndDate()) : null;
  return {
    date_du_jour: AUJ,
    fiche: {
      id: Number(e.getId()), code: s(e.getCode()), sequence: s(e.getSequence()), nom: s(e.getName()),
      type: s(e.getTypeSelect()) === "place" ? "Lieu" : "Matériel",
      famille: e.getEquipmentFamily() ? s(e.getEquipmentFamily().getName()) : null,
      client: e.getPartner() ? s(e.getPartner().getFullName()) : null,
      emplacement: chemin(e) || "(racine)",
      mise_en_service: e.getCommissioningDate() ? String(e.getCommissioningDate()) : null,
      en_service: e.getInService() !== false,
      garantie_pieces: statutGarantie(fin),
      commentaire: s(e.getComments()),
      calendrier_fonctionnement: s(e.getScheduleOfOperation()),
      acces: s(e.getSpecificAccessSchedule()),
      caracteristiques: a
    },
    centrale: c.getId() === e.getId() ? null : {
      code: s(c.getCode()), nom: s(c.getName()), adresse: ac.pvAdresseSite || null, contact: ac.pvContactSite || null,
      acces: s(c.getSpecificAccessSchedule())
    },
    sous_elements: listeEnfants,
    historique_interventions: historique(e, 30),
    ecran: { action: "assets.management.root.equipment", model: EQ_MODEL, id: Number(e.getId()) }
  };
