  var horizon = (input && input.horizon_jours !== undefined && input.horizon_jours !== null) ? Number(input.horizon_jours) : 90;
  var expirees = !(input && input.inclure_expirees === false);
  var filtre = input && input.filtre ? normaliser(input.filtre) : null;
  var tous = Q.of(EqCls).filter("self.typeSelect = 'equipment' AND self.customerWarrantyOnPartEndDate IS NOT NULL")
      .order("customerWarrantyOnPartEndDate").fetch(2000);
  var exp = [], bientot = [];
  for (var i = 0; i < tous.size(); i++) {
    var e = tous.get(i), a = attrsDe(e), fin = String(e.getCustomerWarrantyOnPartEndDate()), j = jours(fin);
    var c = centraleDe(e);
    if (filtre) {
      var hay = normaliser([e.getCode(), e.getName(), a.pvFabricant, a.pvModele, c.getName(), e.getPartner() ? e.getPartner().getFullName() : "",
                            e.getEquipmentFamily() ? e.getEquipmentFamily().getName() : ""].join(" "));
      if (hay.indexOf(filtre) === -1) { continue; }
    }
    var l = { code: s(e.getCode()), nom: s(e.getName()), centrale: s(c.getCode()) + " " + s(c.getName()),
              client: e.getPartner() ? s(e.getPartner().getFullName()) : null,
              fabricant: a.pvFabricant || null, modele: a.pvModele || null, numero_serie: a.pvNumeroSerie || null,
              fin_garantie: fin, jours: j, conditions: a.pvGarantieConstructeur || null, en_service: e.getInService() !== false };
    if (j < 0 && expirees) { exp.push(l); } else if (j >= 0 && j <= horizon) { bientot.push(l); }
  }
  function parCentrale(liste) {
    var g = {};
    for (var q = 0; q < liste.length; q++) { var k = liste[q].centrale; (g[k] = g[k] || []).push(liste[q].code); }
    return g;
  }
  var valides = [];
  for (var v = 0; v < tous.size(); v++) {
    var ev = tous.get(v), fv = String(ev.getCustomerWarrantyOnPartEndDate()), jv = jours(fv);
    if (jv > horizon) {
      var av = attrsDe(ev), cv = centraleDe(ev);
      if (filtre) {
        var hv = normaliser([ev.getCode(), ev.getName(), av.pvFabricant, av.pvModele, cv.getName(), ev.getPartner() ? ev.getPartner().getFullName() : "",
                             ev.getEquipmentFamily() ? ev.getEquipmentFamily().getName() : ""].join(" "));
        if (hv.indexOf(filtre) === -1) { continue; }
      }
      valides.push({ code: s(ev.getCode()), centrale: s(cv.getCode()) + " " + s(cv.getName()), fin_garantie: fv });
    }
  }
  return { date_du_jour: AUJ, horizon_jours: horizon,
           totaux: { expirent_dans_horizon: bientot.length, deja_expirees: exp.length, encore_valides_au_dela: valides.length },
           deja_expirees_par_centrale: parCentrale(exp), encore_valides_par_centrale: parCentrale(valides),
           expirent_dans_horizon: bientot, deja_expirees: expirees ? exp : "non demandé",
           definition: "fin_garantie = champ standard « Fin de garantie client sur pièces » de la fiche équipement ; conditions = champ « Garantie constructeur »." };
