#!/usr/bin/env python3
"""form_coverage.py (v2) — ce qu'une fiche Axelor AFFICHE pour un enregistrement, et ce qui y reste vide.

Pourquoi : un audit table par table ne dit pas ce que voit la personne qui ouvre la fiche. Ce contrôle
rejoue ce que fait le client web, à partir de la vue que l'application SERT (extensions de tous les
modules fusionnées, gardes `if=` des options d'app déjà évaluées par le serveur) :
  1. la vue : POST /ws/meta/view ;
  2. l'enregistrement : POST /ws/rest/<modèle>/<id>/fetch, avec les champs de la vue et ceux que
     citent ses conditions ;
  3. l'onLoad de la vue : POST /ws/action, dont les `attrs` (hidden, readonly) et les valeurs priment ;
  4. les conditions showIf / hideIf / readonlyIf de chaque élément ET de ses ancêtres (onglet,
     panneau), évaluées par evalconds.js DEUX fois : en lecture (une fiche existante s'ouvre en
     lecture dans AOP 8) et en édition. Un élément compte s'il est visible dans l'un des deux modes ;
  5. chaque dashlet visible : son action (POST /ws/action) donne objet, filtre et contexte, puis
     POST /ws/rest/<objet>/search compte les lignes que l'écran afficherait. Un dashlet GRAPHIQUE
     (vue chart) n'est pas compté : son jeu de données a ses propres paramètres ; contrôler sa donnée
     source autrement (requête directe).

États d'un élément visible :
  plein               valeur présente (booléen : true ou false posé ; liste : au moins 1 ligne)
  vide                rien — à remplir, ou à justifier dans le rapport : sans objet pour ce type de
                      fiche, flux exclu par le contrat, ou commentaire ou note sans information propre à la fiche
  vide-calculé        vide ET en lecture seule : ne se saisit pas ; une formule ou un flux le remplit
  zéro                nombre saisissable à 0 : présent, mais souvent un « rempli » trompeur
  zéro-calculé        nombre en lecture seule à 0 (prix moyen, dernier prix…) : c'est un flux qui le pose
  sélection-invalide  valeur absente de la liste de sélection (inventée) — défaut franc
  graphique           dashlet graphique, hors calcul
  indécidable         l'action du dashlet n'a pas rendu de vue
Deux couvertures : toutes valeurs, et hors cases à cocher (un booléen posé à false compte « plein »).
Hors de l'écran, pour information seulement : `masque_mais_rempli` — champ que la fiche ne montre
dans AUCUN mode pour cet enregistrement et qui porte une valeur non par défaut.

Connexion : instance locale = --base, --user (ou AOS_USER) et le mot de passe de préférence en variable AOS_PASSWORD
(rien dans la commande) ; aucun identifiant n'est supposé par défaut.
Instance HÉBERGÉE = aucun mot de passe dans la commande : l'utilisateur ouvre lui-même une session REST
dans son terminal (curl avec un fichier de cookies, recette dans SKILL.md, § Prérequis), puis exporte
AOS_URL (URL de l'application), AOS_COOKIE_JAR (fichier de cookies au format curl/Netscape, avec JSESSIONID)
et AOS_CSRF (valeur du cookie CSRF-TOKEN). Le script ignore alors --base, --user et --password.

Usage :
  form_coverage.py --base http://<hôte>:<port>/<application> --model com.axelor.apps.base.db.Partner \
      --view partner-form --ids 12,13 [--user <login>] \
      [--json sortie.json] [--quiet] [--no-details] [--min-coverage 100] [--expect 47/108]
Code retour : 0 ; 1 si une fiche est sous --min-coverage ; 2 si --expect ne correspond pas
(témoin : « plein/visible » attendu pour la PREMIÈRE fiche).
Prérequis : python3, node. Passe complète : `--quiet --json`. Limites : évalue les conditions pour
l'utilisateur « admin » (un showIf sur $user ou un groupe n'est pas rejoué) ; `$moment().add()` et
`.subtract()` sont neutres ; les actions onChange ne sont pas jouées.
"""
import argparse
import hashlib
import http.cookiejar
import json
import os
import re
import subprocess
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
VERSION = "v2"
COND_KEYS = ("showIf", "hideIf", "hidden", "readonly", "readonlyIf")
JS_WORDS = set("""true false null undefined typeof in instanceof new this return if else var let const
function Math Date JSON Number String Boolean Array Object parseInt parseFloat isNaN NaN Infinity
length size""".split())
# Champs posés automatiquement par l'application ou purement techniques : jamais « suspects ».
AUTO = {"mainAddress", "fullName", "simpleFullName", "partnerSeq", "productCompanyList",
        "accountingSituationList", "companySet", "partnerStockSettingsList", "version"}
STATUS_KEYS = ("statusSelect", "stageSelect", "opportunityStatus", "ticketStatus")
DATE_KEYS = ("orderDate", "invoiceDate", "creationDate", "startDateTime", "startDate", "estimatedDate",
             "dueDate", "expectedCloseDate", "confirmationDateTime", "commissioningDate", "startDateT",
             "date", "realDate", "validationDate")
AMOUNT_KEYS = ("exTaxTotal", "inTaxTotal", "amount", "amountRemaining", "totalAmount", "price",
               "purchasePrice", "salePrice", "expectedRevenue")
QTY_KEYS = ("currentQty", "futureQty", "qty", "realQty", "minQty", "maxQty", "reOrderQty", "quantity")


def cookies_session_aos(chemin):
    """Cookies d'une session REST (fichier curl/Netscape produit par `curl -c`), prêts pour un CookieJar.

    Lu à la main : curl note les cookies HttpOnly (JSESSIONID) « #HttpOnly_<hôte> » (les Python
    avant 3.10 les prennent pour des commentaires) et ceux de session « expires 0 » (MozillaCookieJar
    les croit expirés et n'envoie rien). Dans les deux cas la session serait vide, sans erreur."""
    cookies = []
    with open(chemin, encoding="utf-8") as f:
        for ligne in f:
            ligne = ligne.rstrip("\r\n")
            if ligne.startswith("#HttpOnly_"):
                ligne = ligne[len("#HttpOnly_"):]
            elif not ligne or ligne.startswith("#"):
                continue
            c = ligne.split("\t")
            if len(c) == 7:
                cookies.append(http.cookiejar.Cookie(
                    0, c[5], c[6], None, False, c[0], c[1] == "TRUE", c[0].startswith("."), c[2], True,
                    c[3] == "TRUE", None, True, None, None, {}))
    if not any(c.name == "JSESSIONID" for c in cookies):
        raise SystemExit("session REST : pas de JSESSIONID dans AOS_COOKIE_JAR (session absente ou "
                         "expirée) : l'utilisateur doit rouvrir sa session (recette curl de SKILL.md)")
    return cookies


class Client:
    def __init__(self, base, user, password, proxy=None):
        session = os.environ.get("AOS_COOKIE_JAR")  # session REST (recette curl de SKILL.md) : voir plus bas
        if session:  # l'URL de la session l'emporte : le cookie ne vaut que pour elle
            if not os.environ.get("AOS_URL"):
                raise SystemExit("session REST : AOS_COOKIE_JAR est défini mais pas AOS_URL "
                                 "(URL de l'application, sans slash final)")
            if base and base.rstrip("/") != os.environ["AOS_URL"].rstrip("/"):
                print(f"session REST : --base ignoré, la session vaut pour {os.environ['AOS_URL']}", file=sys.stderr)
            base = os.environ["AOS_URL"]
        self.base = base.rstrip("/")
        self.jar = http.cookiejar.CookieJar()
        # proxy : --proxy, sinon HTTP_PROXY s'il existe (bac à sable où localhost passe par le proxy)
        proxy = proxy if proxy is not None else os.environ.get("HTTP_PROXY", "")
        if proxy:  # proxy retenu : urllib appliquerait sinon NO_PROXY (localhost) quand même
            os.environ.pop("no_proxy", None)
            os.environ.pop("NO_PROXY", None)
        proxies = {"http": proxy, "https": proxy} if proxy else {}
        self.op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.jar),
                                              urllib.request.ProxyHandler(proxies))
        self.csrf = ""
        if session:  # cookies et CSRF de la session ; identifiant et mot de passe ignorés, pas de /callback
            for c in cookies_session_aos(session):
                self.jar.set_cookie(c)
            self.csrf = os.environ.get("AOS_CSRF", "")
        else:
            if not user or not password:
                raise SystemExit("connexion : ni session REST (AOS_URL + AOS_COOKIE_JAR, recette curl de SKILL.md) ni "
                                 "identifiants (--user ou AOS_USER, et AOS_PASSWORD) : aucun défaut n'est supposé")
            self._req("/callback", {"username": user, "password": password}, raw=True)
            self.csrf = next((c.value for c in self.jar if c.name == "CSRF-TOKEN"), "")
        self._fields = {}

    def _req(self, path, body=None, raw=False):
        data = None if body is None else json.dumps(body).encode()
        req = urllib.request.Request(self.base + path, data=data,
                                     headers={"Content-Type": "application/json",
                                              "X-CSRF-Token": self.csrf})
        with self.op.open(req, timeout=180) as r:
            txt = r.read().decode("utf-8", "replace")
        return txt if raw else json.loads(txt)

    def view(self, model, name):
        d = self._req("/ws/meta/view", {"model": model, "data": {"type": "form", "name": name}})
        if d.get("status") != 0:
            raise SystemExit(f"vue introuvable : {name} ({str(d)[:300]})")
        return d["data"]

    def fields(self, model):
        """Métadonnées des champs d'un modèle (titres de sélection des lignes de liste)."""
        if model not in self._fields:
            try:
                d = self._req(f"/ws/meta/fields/{model}")
                fl = (d.get("data") or {}).get("fields") or []
                self._fields[model] = {f["name"]: f for f in fl} if isinstance(fl, list) else fl
            except Exception:
                self._fields[model] = {}
        return self._fields[model]

    def fetch(self, model, rid, fields):
        d = self._req(f"/ws/rest/{model}/{rid}/fetch", {"fields": sorted(fields)})
        if d.get("status") != 0 or not d.get("data"):
            raise SystemExit(f"enregistrement introuvable : {model}#{rid} ({str(d)[:300]})")
        return d["data"][0]

    def action(self, name, model, context):
        return self._req("/ws/action", {"action": name, "model": model,
                                        "data": {"context": context}})

    def search(self, model, domain, ctx, limit):
        body = {"offset": 0, "limit": limit, "data": {"_domain": domain, "_domainContext": ctx}}
        d = self._req(f"/ws/rest/{model}/search", body)
        if d.get("status") != 0:
            return None, []
        return d.get("total"), d.get("data") or []


def walk_items(view):
    fmeta = view["fields"]
    if isinstance(fmeta, list):
        fmeta = {f["name"]: f for f in fmeta}
    out = []

    def walk(node, trail, chain):
        t = node.get("type")
        own = {k: node[k] for k in COND_KEYS if node.get(k) not in (None, False, "")}
        here = chain + [{"name": node.get("name"), **own}]
        title = node.get("title") or node.get("autoTitle")
        trail2 = trail + ([title] if t in ("panel", "panel-related", "dashlet") and title else [])
        if t in ("field", "panel-related", "dashlet"):
            name = node.get("name")
            meta = fmeta.get(name, {}) if name else {}
            out.append({"kind": t, "name": name, "title": title or meta.get("title"),
                        "serverType": node.get("serverType") or meta.get("type"),
                        "target": node.get("target") or meta.get("target"),
                        "action": node.get("action"), "path": trail, "chain": here,
                        "json": (node.get("jsonFields") if "jsonFields" in node else None),
                        "metaReadonly": bool(meta.get("readonly"))})
        kids = node.get("items") or []
        if t == "include" and isinstance(node.get("view"), dict):
            kids = node["view"].get("items") or []
        for c in kids:
            walk(c, trail2, here)

    walk(view["view"], [], [])
    return out, fmeta


def idents(expr):
    for m in re.finditer(r"(?<![\w$.'\"])([A-Za-z_][\w]*(?:\.[A-Za-z_][\w]*)*)", expr or ""):
        tok = m.group(1)
        if tok.split(".")[0] in JS_WORDS or tok.startswith("__"):
            continue
        yield tok


def evaluate(record, exprs, readonly):
    if not exprs:
        return {}
    p = subprocess.run(["node", os.path.join(HERE, "evalconds.js")],
                       input=json.dumps({"record": record, "exprs": exprs, "readonly": readonly}),
                       capture_output=True, text=True, timeout=60)
    if p.returncode != 0:
        raise SystemExit("evalconds.js : " + p.stderr[:500])
    return dict(zip(exprs, json.loads(p.stdout)))


def onload(cli, view, model, record):
    """attrs posés par l'onLoad : {nom: {hidden, readonly}} ; ses valeurs sont reportées dans record."""
    name = view["view"].get("onLoad")
    attrs, values = {}, {}
    if not name:
        return attrs, None
    ctx = dict(record)
    ctx["_model"] = model
    try:
        r = cli.action(name, model, ctx)
    except Exception as e:
        return attrs, f"onLoad {name} : {e}"
    for item in r.get("data") or []:
        if not isinstance(item, dict):
            continue
        for fname, a in (item.get("attrs") or {}).items():
            if isinstance(a, dict):
                attrs.setdefault(fname, {}).update({k: v for k, v in a.items()
                                                    if k in ("hidden", "readonly")})
                if "value" in a:
                    values[fname] = a["value"]
        for fname, v in (item.get("values") or {}).items():
            values[fname] = v
    record.update({k: v for k, v in values.items() if v is not None})
    return attrs, None


TIMESTAMP = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}")
NAME_CACHE = {}  # (modèle, id) → nom lu, pour les relations servies sans leur nom

LABEL_KEYS = ("fullName", "name", "subject", "title", "label", "code", "saleOrderSeq",
              "purchaseOrderSeq", "invoiceId", "ticketSeq", "qiSeq", "contractId", "sequence",
              "reference", "serialNumber")


def label(v):
    """Libellé lisible d'un enregistrement lié. Jamais l'importId : un code technique d'import
    affiché comme un titre fait croire à un nom générique (vécu le 27/09 : un code d'import du type « XXX-E-012 » lu comme
    l'objet d'un rendez-vous qui s'appelait « Revue annuelle du parc installé »)."""
    if not isinstance(v, dict):
        return v
    for k in LABEL_KEYS:
        if v.get(k) not in (None, ""):
            return v[k]
    # Lignes sans nom propre (27/09, essai 1 : phrases de danger, catalogues fournisseurs,
    # complémentaires, lignes de nomenclature affichées par un horodatage ou un prix) :
    # on compose le libellé que l'écran montre.
    if v.get("phraseCode"):
        return " ".join(str(x) for x in (v["phraseCode"], v.get("phrase")) if x)
    if v.get("productSupplierCode") or v.get("productSupplierName"):
        who = label(v.get("supplierPartner")) if isinstance(v.get("supplierPartner"), dict) else None
        what = " ".join(str(x) for x in (v.get("productSupplierCode"), v.get("productSupplierName")) if x)
        return f"{who} — {what}" if who else what
    if isinstance(v.get("billOfMaterialParent"), dict):
        return f"dans {label(v['billOfMaterialParent'])}"
    for k in ("stockLocation", "product", "partner", "supplierPartner", "billOfMaterial"):
        if isinstance(v.get(k), dict) and not str(label(v[k])).startswith("#"):
            return label(v[k])
    rest = {k: x for k, x in v.items() if k not in ("id", "version", "$version", "importId",
                                                    "importOrigin") and x is not None
            and not isinstance(x, (bool, dict, list))
            and not k.endswith(("On", "By")) and not TIMESTAMP.match(str(x))}
    return next(iter(rest.values()), f"#{v.get('id')}")


def row_summary(cli, model, row):
    """Une ligne de liste ou de dashlet, lisible : libellé, statut, date, montant, quantité."""
    meta = cli.fields(model) if model else {}
    parts = [str(label(row))]
    for k in STATUS_KEYS:
        if row.get(k) is not None:
            sl = {str(s.get("value")): s.get("title")
                  for s in (meta.get(k, {}).get("selectionList") or [])}
            parts.append(f"statut {sl.get(str(row[k]), label(row[k]))}")
            break
    for k in DATE_KEYS:
        if row.get(k):
            parts.append(f"{k} {str(row[k])[:10]}")
            break
    for k in AMOUNT_KEYS:
        if row.get(k) not in (None, "", 0, "0"):
            parts.append(f"{k} {row[k]}")
            break
    for k in QTY_KEYS:
        if row.get(k) not in (None, ""):
            parts.append(f"{k} {row[k]}")
            break
    for k in ("address", "addressL4", "formattedFullName", "city", "zip"):
        v = row.get(k)
        if v:
            parts.append(f"{k} {label(v)}")
            break
    return " · ".join(parts)


def is_empty(v):
    return v is None or v == "" or v == [] or v == {}


def is_zero(v):
    try:
        return not isinstance(v, bool) and float(v) == 0.0
    except (TypeError, ValueError):
        return False


def same_value(a, b):
    try:
        return float(a) == float(b)
    except (TypeError, ValueError):
        return str(a) == str(b)


def cover(cli, model, view_name, rid, view=None, details=True):
    view = view or cli.view(model, view_name)
    items, fmeta = walk_items(view)
    fields = {i["name"] for i in items if i["kind"] in ("field", "panel-related") and i["name"]
              and not i["name"].startswith("$")}
    exprs = sorted({l[k] for i in items for l in i["chain"] for k in ("showIf", "hideIf", "readonlyIf")
                    if l.get(k)})
    for e in exprs:
        fields.update(idents(e))
    fields.discard("id")
    known = set(fmeta)
    # libellé de la fiche : nom complet même quand la vue ne l'affiche pas (fiche contact)
    known |= {n for n in ("fullName", "name", "code") if n in cli.fields(model)}
    fields |= {"fullName", "name", "code"}
    rec = cli.fetch(model, rid, {f for f in fields if f.split(".")[0] in known})
    attrs, onload_err = onload(cli, view, model, rec)
    res = {True: evaluate(rec, exprs, True), False: evaluate(rec, exprs, False)}
    undecidable = sorted({e for m in res.values() for e, r in m.items() if not r["ok"]})

    def truth(e, mode):
        r = res[mode].get(e)
        return None if (r is None or not r["ok"]) else r["value"]

    def level_visible(lvl, mode):
        # une condition indécidable laisse l'élément VISIBLE (showIf comme hideIf) : mieux vaut un
        # élément compté à tort qu'un faux « masqué mais rempli »
        a = attrs.get(lvl.get("name") or "", {})
        if "hidden" in a:
            return not a["hidden"]
        if lvl.get("showIf"):
            t = truth(lvl["showIf"], mode)
            return True if t is None else t
        if lvl.get("hideIf"):
            t = truth(lvl["hideIf"], mode)
            return True if t is None else not t
        return lvl.get("hidden") is not True

    def level_readonly(lvl, mode):
        a = attrs.get(lvl.get("name") or "", {})
        if "readonly" in a:
            return bool(a["readonly"])
        if lvl.get("readonlyIf"):
            return bool(truth(lvl["readonlyIf"], mode))
        return lvl.get("readonly") is True

    # regroupement par élément (un même champ peut apparaître deux fois dans la vue)
    groups = {}
    for i in items:
        key = (i["kind"] if i["kind"] == "dashlet" else "data", i["name"] or i["action"])
        g = groups.setdefault(key, {"item": i, "vis": set(), "ro_edit": True, "by_cond": False})
        if not g["vis"] and any(all(level_visible(l, m) for l in i["chain"]) for m in (True, False)):
            g["item"] = i  # un même champ peut porter deux titres (usedInDEB : « DES » sur un service,
            #                « DEB » sur un bien) : garder l'occurrence que l'écran affiche
        for mode in (True, False):
            if all(level_visible(l, mode) for l in i["chain"]):
                g["vis"].add("lecture" if mode else "édition")
                if not mode:
                    g["ro_edit"] = g["ro_edit"] and (i["metaReadonly"] or any(
                        level_readonly(l, False) for l in i["chain"]))
        g["by_cond"] = g["by_cond"] or any(
            (l.get("showIf") or l.get("hideIf") or (l.get("name") in attrs)) for l in i["chain"])

    rows, hidden_filled = [], []
    ctx_base = {k: v for k, v in rec.items()}
    ctx_base.update({"_model": model, "id": rid})
    for (kind, name), g in groups.items():
        i = g["item"]
        vis = bool(g["vis"])
        modes = "+".join(sorted(g["vis"])) if vis else ""
        ro = i["metaReadonly"] or ("édition" not in g["vis"]) or g["ro_edit"]
        if i["kind"] == "field" and name and str(name).startswith("$"):
            continue
        if i["kind"] == "field" and i.get("json") is not None and not i["json"]:
            continue
        if kind == "dashlet":
            if not vis:
                continue
            n, why, sample, target, state = None, None, [], None, None
            try:
                r = cli.action(i["action"], model, ctx_base)
                v = next((x.get("view") for x in r.get("data") or [] if isinstance(x, dict)
                          and x.get("view")), None)
                vtypes = {x.get("type") for x in (v or {}).get("views") or []}
                vtypes.add((v or {}).get("viewType"))
                if v and ({"chart", "custom"} & vtypes) \
                        and not ({"grid", "cards", "kanban", "calendar"} & vtypes):
                    state, target = "graphique", v.get("model")
                elif v and v.get("model"):
                    ctx = {"id": rid, "_id": rid, "_model": model}
                    ctx.update(v.get("context") or {})
                    n, data = cli.search(v["model"], v.get("domain"), ctx, 6 if details else 1)
                    target = v["model"]
                    sample = [row_summary(cli, target, x) for x in data] if details else []
                else:
                    why = "action sans vue"
            except Exception as e:
                why = f"erreur : {e}"
            if state is None:
                state = "indécidable" if n is None else ("plein" if n > 0 else "vide")
            rows.append({"kind": "dashlet", "name": i["name"], "title": i["title"], "path": i["path"],
                         "modes": modes, "target": target, "rows": n, "state": state, "note": why,
                         "sample": sample})
            continue
        val = rec.get(name)
        st = i["serverType"] or ""
        if not vis:
            dflt = fmeta.get(name, {}).get("defaultValue")
            if g["by_cond"] and name not in AUTO and not i["metaReadonly"] \
                    and not is_empty(val) and not isinstance(val, bool) and not is_zero(val) \
                    and not (dflt is not None and same_value(dflt, val)):
                hidden_filled.append({"name": name, "title": i["title"], "path": i["path"],
                                      "value": (len(val) if isinstance(val, list) else label(val))})
            continue
        if st in ("ONE_TO_MANY", "MANY_TO_MANY") or i["kind"] == "panel-related":
            n = len(val or [])
            sample = []
            if details and n and i["target"]:
                ids = [x.get("id") for x in val if isinstance(x, dict) and x.get("id")][:8]
                if ids:
                    _, data = cli.search(i["target"], "self.id in (:ids)", {"ids": ids}, 8)
                    sample = [row_summary(cli, i["target"], x) for x in data]
            if not sample:
                sample = [str(label(x)) for x in (val or [])[:8]]
            state = "plein" if n else ("vide-calculé" if ro else "vide")
            rows.append({"kind": "liste", "name": name, "title": i["title"], "path": i["path"],
                         "modes": modes, "target": i["target"], "rows": n, "state": state,
                         "sample": sample})
            continue
        sel_list = fmeta.get(name, {}).get("selectionList") or []
        sel = [str(x.get("value")) for x in sel_list]
        if is_empty(val):
            state = "vide-calculé" if ro else "vide"
        elif sel and not isinstance(val, bool) and str(val) not in sel:
            state = ("vide-calculé" if ro else "vide") if is_zero(val) else "sélection-invalide"
        elif is_zero(val) and not (sel and str(val) in sel):
            state = "zéro-calculé" if ro else "zéro"
        else:
            state = "plein"
        if sel and str(val) in sel:
            ttl = next((x.get("title") for x in sel_list if str(x.get("value")) == str(val)), None)
            shown = f"{val} ({ttl})" if ttl else val
        else:
            shown = label(val) if isinstance(val, dict) else val
            # Relation servie sans son nom (27/09 : « Configuration N° suivi : #4 » pour
            # « N° de série machine ») : on lit le nom de la cible, pour l'affichage seulement.
            if details and isinstance(val, dict) and val.get("id") and i.get("target") \
                    and str(shown).startswith("#"):
                key = (i["target"], val["id"])
                if key not in NAME_CACHE:
                    names = [f for f in ("fullName", "name", "code") if f in cli.fields(i["target"])]
                    NAME_CACHE[key] = shown
                    if names:
                        try:
                            NAME_CACHE[key] = label(cli.fetch(i["target"], val["id"], names))
                        except (Exception, SystemExit):
                            pass
                shown = NAME_CACHE[key]
        rows.append({"kind": "M2O" if st in ("MANY_TO_ONE", "ONE_TO_ONE") else "plat",
                     "name": name, "title": i["title"], "path": i["path"], "modes": modes,
                     "serverType": st, "state": state, "value": shown,
                     "raw": val if not isinstance(val, (dict, list)) else None,
                     "default": fmeta.get(name, {}).get("defaultValue")})
    counted = [r for r in rows if r["state"] != "graphique"]
    nb = [r for r in counted if r.get("serverType") != "BOOLEAN"]
    full = sum(1 for r in counted if r["state"] == "plein")
    full_nb = sum(1 for r in nb if r["state"] == "plein")
    return {"model": model, "view": view_name, "id": rid, "oracle": VERSION,
            "name": rec.get("fullName") or rec.get("name") or rec.get("code"),
            "visible": len(counted), "plein": full,
            "coverage": round(100.0 * full / len(counted), 1) if counted else None,
            "visible_hors_booleens": len(nb), "plein_hors_booleens": full_nb,
            "coverage_hors_booleens": round(100.0 * full_nb / len(nb), 1) if nb else None,
            "vides": [r for r in rows if r["state"] not in ("plein", "graphique")],
            "graphiques": [r["name"] for r in rows if r["state"] == "graphique"],
            "masque_mais_rempli": hidden_filled, "conditions_indecidables": undecidable,
            "onload_erreur": onload_err, "rows": rows}


def oracle_hash():
    h = hashlib.md5()
    for f in ("form_coverage.py", "evalconds.js"):
        h.update(open(os.path.join(HERE, f), "rb").read())
    return h.hexdigest()[:10]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=not os.environ.get("AOS_COOKIE_JAR"),
                    help="URL de l'application, ex. http://<hôte>:<port>/<application> (ignorée si AOS_COOKIE_JAR est défini)")
    ap.add_argument("--user", default=os.environ.get("AOS_USER"),
                    help="instance locale : identifiant (défaut : variable AOS_USER) ; ignoré sous session REST")
    ap.add_argument("--password", default=os.environ.get("AOS_PASSWORD"),
                    help="instance locale : mot de passe (défaut : variable AOS_PASSWORD, à préférer) ; ignoré sous session REST")
    ap.add_argument("--model", required=True)
    ap.add_argument("--view", required=True)
    ap.add_argument("--ids", required=True, help="ids séparés par des virgules")
    ap.add_argument("--json")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--no-details", action="store_true")
    ap.add_argument("--min-coverage", type=float)
    ap.add_argument("--expect", help="« plein/visible » attendu pour la première fiche (témoin)")
    ap.add_argument("--proxy", help="proxy HTTP (défaut : HTTP_PROXY si défini, sinon aucun)")
    a = ap.parse_args()
    cli = Client(a.base, a.user, a.password, a.proxy)
    view = cli.view(a.model, a.view)
    res, failed = [], []
    for x in (x for x in a.ids.split(",") if x.strip()):
        try:
            res.append(cover(cli, a.model, a.view, int(x), view, details=not a.no_details))
        except (Exception, SystemExit) as e:  # un 403 ou une fiche supprimée n'arrête pas le lot
            failed.append((x, str(e)[:200]))
    for x, why in failed:
        print(f"{x}\tERREUR\t{why}")
    for r in res:
        r["oracle_hash"] = oracle_hash()
    if a.json:
        json.dump(res, open(a.json, "w"), ensure_ascii=False, indent=1)
    worst = 100.0
    for r in res:
        worst = min(worst, r["coverage"] or 0)
        print(f"{r['id']}\t{r['coverage']}%\t{r['plein']}/{r['visible']}\t"
              f"hors booléens {r['coverage_hors_booleens']}% "
              f"({r['plein_hors_booleens']}/{r['visible_hors_booleens']})\t{r['name']}")
        if a.quiet:
            continue
        for v in r["vides"]:
            where = " > ".join(p for p in v["path"] if p)[-60:]
            extra = f" ({v.get('target') or ''})" if v["kind"] in ("liste", "dashlet") else ""
            print(f"   [{v['state']:<18}] {v['kind']:<7} {(v['name'] or v.get('title') or '?'):<34} "
                  f"{where}{extra}")
        if r["graphiques"]:
            print("   graphiques (hors calcul) : " + ", ".join(str(g) for g in r["graphiques"]))
        if r["masque_mais_rempli"]:
            print("   masqués mais remplis (info) : "
                  + ", ".join(str(h["name"]) for h in r["masque_mais_rempli"]))
        if r["conditions_indecidables"]:
            print(f"   conditions indécidables : {len(r['conditions_indecidables'])}")
        if r["onload_erreur"]:
            print("   " + r["onload_erreur"])
    if a.expect and res and f"{res[0]['plein']}/{res[0]['visible']}" != a.expect:
        print(f"TÉMOIN KO : attendu {a.expect}, obtenu {res[0]['plein']}/{res[0]['visible']}")
        sys.exit(2)
    if a.min_coverage is not None and worst < a.min_coverage:
        sys.exit(1)


if __name__ == "__main__":
    main()
