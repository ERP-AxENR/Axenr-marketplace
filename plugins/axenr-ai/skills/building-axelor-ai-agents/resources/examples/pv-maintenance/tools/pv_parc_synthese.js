  var racines = Q.of(EqCls).filter("self.parentEquipment IS NULL AND self.typeSelect = 'place'").order("code").fetch(500);
  var tous = Q.of(EqCls).fetch(2000);
  var out = [];
  for (var i = 0; i < racines.size(); i++) {
    var r = racines.get(i), a = attrsDe(r);
    var nb = 0, nbOnd = 0, hs = [], alarmes = [], expirees = 0, bientot = [];
    for (var j = 0; j < tous.size(); j++) {
      var e = tous.get(j);
      if (e.getId() === r.getId() || centraleDe(e).getId() !== r.getId()) { continue; }
      nb++;
      var ae = attrsDe(e);
      if (ae.pvModele && e.getEquipmentFamily() && s(e.getEquipmentFamily().getCode()) === "PV-OND") { nbOnd++; }
      if (s(e.getTypeSelect()) === "equipment" && e.getInService() === false) { hs.push(s(e.getCode()) + " " + s(e.getName())); }
      var al = ae.pvDerniereAlarme;
      if (al && !/^(aucune|ras)/i.test(al) && e.getInService() !== false) { alarmes.push(s(e.getCode()) + " : " + al); }
      var fin = e.getCustomerWarrantyOnPartEndDate() ? String(e.getCustomerWarrantyOnPartEndDate()) : null;
      if (fin && s(e.getTypeSelect()) === "equipment") {
        var jr = jours(fin);
        if (jr < 0) { expirees++; } else if (jr <= 90) { bientot.push(s(e.getCode()) + " le " + fin + " (" + jr + " j)"); }
      }
    }
    out.push({
      code: s(r.getCode()), centrale: s(r.getName()), client: r.getPartner() ? s(r.getPartner().getFullName()) : null,
      adresse: a.pvAdresseSite || null, puissance_crete_kwc: a.pvPuissance || null, puissance_injection_kva: a.pvPuissanceInjection || null,
      mise_en_service: r.getCommissioningDate() ? String(r.getCommissioningDate()) : null,
      contrat: a.pvTypeContrat || null, productible_kwh_an: a.pvProductibleAnnuel || null,
      nb_fiches: nb, nb_onduleurs: nbOnd, materiels_hors_service: hs, alarmes_actives: alarmes,
      nb_materiels_garantie_expiree: expirees, garanties_expirant_90j: bientot,
      prochaine_maintenance: a.pvDateProchaineMaintenance || null
    });
  }
  var totKwc = 0, totKva = 0, totKwh = 0;
  for (var z = 0; z < out.length; z++) { totKwc += Number(out[z].puissance_crete_kwc || 0); totKva += Number(out[z].puissance_injection_kva || 0); totKwh += Number(out[z].productible_kwh_an || 0); }
  return { date_du_jour: AUJ, nb_centrales: out.length,
           totaux: { puissance_crete_kwc: Math.round(totKwc * 10) / 10, puissance_injection_kva: Math.round(totKva * 10) / 10, productible_kwh_an: Math.round(totKwh) },
           centrales: out };
