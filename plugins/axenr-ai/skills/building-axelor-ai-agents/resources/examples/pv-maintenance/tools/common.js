  var Q = Java.type("com.axelor.db.Query");
  var EqCls = Java.type("com.axelor.apps.intervention.db.Equipment");
  var MsgCls = Java.type("com.axelor.mail.db.MailMessage");
  var EQ_MODEL = "com.axelor.apps.intervention.db.Equipment";

  function s(v) { return (v === null || v === undefined) ? null : String(v); }
  function normaliser(x) {
    return String(x).normalize("NFD").replace(/[̀-ͯ]/g, "")
        .toLowerCase().replace(/[-'_\/]/g, " ").replace(/\s+/g, " ").trim();
  }
  function attrsDe(e) {
    var a = e.getAttrs();
    if (!a) { return {}; }
    try { return JSON.parse(String(a)); } catch (err) { return {}; }
  }
  var now = new Date();
  var AUJ = now.getUTCFullYear() + "-" + (now.getUTCMonth() < 9 ? "0" : "") + (now.getUTCMonth() + 1) + "-" + (now.getUTCDate() < 10 ? "0" : "") + now.getUTCDate();
  function jours(dateStr) { return dateStr ? Math.round((Date.parse(dateStr) - Date.parse(AUJ)) / 86400000) : null; }
  function statutGarantie(fin) {
    if (!fin) { return { fin: null, statut: "non renseignée" }; }
    var j = jours(fin);
    if (j < 0) { return { fin: fin, jours_restants: j, statut: "EXPIRÉE depuis " + (-j) + " jours" }; }
    if (j <= 90) { return { fin: fin, jours_restants: j, statut: "EXPIRE dans " + j + " jours" }; }
    return { fin: fin, jours_restants: j, statut: "valide (" + Math.round(j / 365 * 10) / 10 + " ans restants)" };
  }
  function centraleDe(e) {
    var c = e, guard = 0;
    while (c.getParentEquipment() && guard++ < 10) { c = c.getParentEquipment(); }
    return c;
  }
  function chemin(e) {
    var parts = [], c = e.getParentEquipment(), guard = 0;
    while (c && guard++ < 10) { parts.unshift(s(c.getCode()) + " " + s(c.getName())); c = c.getParentEquipment(); }
    return parts.join(" > ");
  }
  function resume(e) {
    var a = attrsDe(e);
    var fin = e.getCustomerWarrantyOnPartEndDate() ? String(e.getCustomerWarrantyOnPartEndDate()) : null;
    return {
      id: Number(e.getId()), code: s(e.getCode()), nom: s(e.getName()),
      type: s(e.getTypeSelect()) === "place" ? "Lieu" : "Matériel",
      famille: e.getEquipmentFamily() ? s(e.getEquipmentFamily().getName()) : null,
      fabricant: a.pvFabricant || null, modele: a.pvModele || null, numero_serie: a.pvNumeroSerie || null,
      puissance: a.pvPuissance || null, en_service: e.getInService() !== false,
      derniere_alarme: a.pvDerniereAlarme || null,
      garantie: statutGarantie(fin)
    };
  }
  function historique(e, limite) {
    var msgs = Q.of(MsgCls).filter("self.relatedModel = :m AND self.relatedId = :id AND self.type = 'comment'")
        .bind("m", EQ_MODEL).bind("id", e.getId()).order("-createdOn").fetch(limite || 20);
    var out = [];
    for (var i = 0; i < msgs.size(); i++) {
      var m = msgs.get(i);
      out.push({ sujet: s(m.getSubject()), texte: s(m.getBody()).replace(/<[^>]+>/g, " ").replace(/\s+/g, " ").trim(),
                 saisi_le: s(m.getCreatedOn()).substring(0, 10) });
    }
    return out;
  }
  function trouver(saisie) {
    var brut = String(saisie || "").trim();
    if (!brut) { return { erreur: "paramètre vide : donner un code (CPV02-OND2), un n° de série, un nom ou un client." }; }
    var tous = Q.of(EqCls).fetch(2000);
    var n = normaliser(brut), mots = n.split(" "), exacts = [], partiels = [];
    for (var i = 0; i < tous.size(); i++) {
      var e = tous.get(i), a = attrsDe(e);
      var code = normaliser(s(e.getCode())), sn = a.pvNumeroSerie ? normaliser(a.pvNumeroSerie) : "";
      if (code === n || (sn && sn.indexOf(n) !== -1 && n.length >= 6) || String(e.getId()) === brut) { exacts.push(e); continue; }
      var hay = normaliser([e.getCode(), e.getName(), e.getPartner() ? e.getPartner().getFullName() : "",
                            a.pvFabricant || "", a.pvModele || "", a.pvAdresseSite || ""].join(" "));
      var ok = true;
      for (var k = 0; k < mots.length; k++) { if (hay.indexOf(mots[k]) === -1) { ok = false; break; } }
      if (ok) { partiels.push(e); }
    }
    var res = exacts.length ? exacts : partiels;
    if (res.length > 1 && !exacts.length) {
      // departage : nombre de mots presents comme mots entiers dans le nom (ex. "onduleur 2" ne doit pas matcher "SUN2000")
      var best = -1, bestList = [];
      for (var b = 0; b < res.length; b++) {
        var nomMots = (" " + normaliser(s(res[b].getName()) + " " + s(res[b].getCode())) + " ");
        var sc = 0;
        for (var w = 0; w < mots.length; w++) { if (nomMots.indexOf(" " + mots[w] + " ") !== -1) { sc++; } }
        if (sc > best) { best = sc; bestList = [res[b]]; } else if (sc === best) { bestList.push(res[b]); }
      }
      if (bestList.length === 1 && best > 0) { return { equipement: bestList[0], resolu_depuis: brut }; }
      res = bestList;
    }
    if (res.length === 1) { return { equipement: res[0] }; }
    if (res.length === 0) { return { introuvable: true, conseil: "essayer le code (CPV01…CPV05), le client, la marque ou le n° de série" }; }
    // privilegier un lieu de niveau centrale si la saisie designe un client ou une centrale
    var c = [];
    for (var j = 0; j < Math.min(res.length, 25); j++) { c.push({ code: s(res[j].getCode()), nom: s(res[j].getName()) }); }
    return { ambigu: true, candidats: c };
  }
