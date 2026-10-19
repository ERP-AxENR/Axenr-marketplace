  var tous = Q.of(EqCls).filter("self.typeSelect = 'equipment'").order("code").fetch(2000);
  var arrets = [], alarmes = [];
  for (var i = 0; i < tous.size(); i++) {
    var e = tous.get(i), a = attrsDe(e), al = a.pvDerniereAlarme;
    var hs = e.getInService() === false;
    var active = al && !/^(aucune|ras)/i.test(al);
    if (!hs && !active) { continue; }
    var c = centraleDe(e), fin = e.getCustomerWarrantyOnPartEndDate() ? String(e.getCustomerWarrantyOnPartEndDate()) : null;
    var h = historique(e, 1);
    var l = { code: s(e.getCode()), nom: s(e.getName()), centrale: s(c.getCode()) + " " + s(c.getName()),
              client: e.getPartner() ? s(e.getPartner().getFullName()) : null, fabricant: a.pvFabricant || null, modele: a.pvModele || null,
              alarme: al || null, garantie: statutGarantie(fin), derniere_intervention: h.length ? h[0] : null };
    if (hs) { arrets.push(l); } else { alarmes.push(l); }
  }
  return { date_du_jour: AUJ, materiels_a_l_arret: arrets, alarmes_actives_en_fonctionnement: alarmes };
