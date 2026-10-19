#!/usr/bin/env python3
"""generate_visuals.py — visuels sobres pour les fiches Article (schéma + code + nom) et les logos de
société (initiales), téléversés par l'API et rattachés au champ `picture`.

Pourquoi : une fiche sans photo se voit au premier regard, et une base de démo n'a pas le catalogue
photo du client. Un visuel SOBRE — un pictogramme de la nature de l'article, son code et son nom ; des
initiales pour une société — remplit la fiche sans prétendre être une photo. Décision de l'utilisateur du
2026-09-27 (« générer des visuels ») : la photo est attendue sur les articles et les sociétés ; un
contact garde sa photo au choix.

Sûreté : ne remplace JAMAIS une image déjà posée (règle de sûreté du skill : ne pas toucher à ce qu'on
n'a pas créé) ; ne traite que les ids donnés. Téléversement : POST /ws/rest/com.axelor.meta.db.MetaFile/
upload (multipart : `request` = {"data": {"fileName", "fileType"}}, `file`), la réponse porte `data` en
TABLEAU (piège 87) ; rattachement : POST /ws/rest/<modèle>/<id> avec `picture: {id}`. Un enregistrement
d'article par l'API rejoue sa sauvegarde (n° de série, code-barres : piège du code-barres, fiche
`surface-tiers-articles.md` §7).

Usage :
  generate_visuals.py --base http://<hôte>:<port>/<app> --model product --ids 161,162 [--dry-run DIR]
  generate_visuals.py --base http://<hôte>:<port>/<app> --model partner --ids 78,83
  --dry-run DIR : dessine les PNG dans DIR sans rien envoyer (les regarder avant de téléverser).
Connexion : instance locale = --base, --user (ou AOS_USER) et le mot de passe de préférence en variable AOS_PASSWORD
(rien dans la commande) ; aucun identifiant n'est supposé par défaut.
Instance HÉBERGÉE = aucun mot de passe dans la commande : l'utilisateur ouvre lui-même une session REST
dans son terminal (curl avec un fichier de cookies, recette dans SKILL.md, § Prérequis), puis exporte
AOS_URL (URL de l'application), AOS_COOKIE_JAR (fichier de cookies au format curl/Netscape, avec JSESSIONID)
et AOS_CSRF (valeur du cookie CSRF-TOKEN). Le script ignore alors --base, --user et --password.
Prérequis : python3 avec Pillow (PIL), une police TrueType (DejaVu par défaut).
"""
import argparse
import hashlib
import http.cookiejar
import io
import json
import os
import re
import sys
import textwrap
import urllib.request
import uuid

from PIL import Image, ImageDraw, ImageFont

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
INK, PAPER, ACCENT = (52, 64, 84), (246, 248, 251), (41, 98, 173)
PALETTE = [(41, 98, 173), (18, 120, 105), (156, 86, 22), (120, 60, 150), (170, 50, 60),
           (60, 110, 60), (90, 90, 110), (20, 110, 140)]


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
            self.req("/callback", {"username": user, "password": password}, raw=True)
            self.csrf = next((c.value for c in self.jar if c.name == "CSRF-TOKEN"), "")

    def req(self, path, body=None, raw=False, data=None, ctype="application/json"):
        payload = data if data is not None else (None if body is None else json.dumps(body).encode())
        r = urllib.request.Request(self.base + path, data=payload,
                                   headers={"Content-Type": ctype, "X-CSRF-Token": self.csrf})
        with self.op.open(r, timeout=120) as resp:
            txt = resp.read().decode("utf-8", "replace")
        return txt if raw else json.loads(txt)

    def upload_png(self, name, png):
        boundary = uuid.uuid4().hex
        meta = json.dumps({"data": {"fileName": name, "fileType": "image/png"}})
        parts = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"request\"\r\n"
                 f"Content-Type: application/json\r\n\r\n{meta}\r\n").encode()
        parts += (f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; "
                  f"filename=\"{name}\"\r\nContent-Type: image/png\r\n\r\n").encode() + png
        parts += f"\r\n--{boundary}--\r\n".encode()
        d = self.req("/ws/rest/com.axelor.meta.db.MetaFile/upload", data=parts,
                     ctype=f"multipart/form-data; boundary={boundary}")
        if d.get("status") != 0 or not d.get("data"):
            raise RuntimeError(f"téléversement refusé : {str(d)[:300]}")
        data = d["data"]
        return (data[0] if isinstance(data, list) else data)["id"]  # piège 87 : un tableau


def font(size, bold=False):
    try:
        return ImageFont.truetype(FONT_B if bold else FONT, size)
    except OSError:
        return ImageFont.load_default()


def glyph_kind(text, is_service):
    t = text.lower()
    rules = [("service", is_service), ("convoyeur", re.search(r"convoy|rouleau|bande", t)),
             ("levage", re.search(r"pont roulant|potence|palan|levage|élingue|elingue", t)),
             ("table", re.search(r"table élév|table elev|ciseau", t)),
             ("rotation", re.search(r"arbre|axe|galet|bague|roulement|poulie|pignon", t)),
             ("fluide", re.search(r"huile|graisse|colle|solvant|lubrif|peinture|dégraiss", t)),
             ("electrique", re.search(r"moteur|variateur|automate|armoire|capteur|câble|cable", t)),
             ("matiere", re.search(r"tôle|tole|barre|profil|tube|plat |cornière|corniere", t)),
             ("visserie", re.search(r"vis |visserie|écrou|ecrou|boulon|rondelle|goujon", t))]
    return next((k for k, hit in rules if hit), "caisse")


def draw_glyph(d, kind, box):
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
    lw = max(3, w // 45)
    if kind == "convoyeur":
        d.line([(x0, cy - h // 8), (x1, cy - h // 8)], fill=INK, width=lw)
        for i in range(6):
            x = x0 + w * (i + 0.5) / 6
            d.ellipse([x - w / 16, cy - h / 8, x + w / 16, cy - h / 8 + w / 8], outline=INK, width=lw)
        d.line([(x0 + w // 10, cy + h // 8), (x0 + w // 10, y1)], fill=INK, width=lw)
        d.line([(x1 - w // 10, cy + h // 8), (x1 - w // 10, y1)], fill=INK, width=lw)
    elif kind == "levage":
        d.line([(x0, y0 + h // 6), (x1, y0 + h // 6)], fill=INK, width=lw * 2)
        d.line([(x0 + w // 8, y0 + h // 6), (x0 + w // 8, y1)], fill=INK, width=lw)
        d.line([(x1 - w // 8, y0 + h // 6), (x1 - w // 8, y1)], fill=INK, width=lw)
        d.line([(cx, y0 + h // 6), (cx, cy + h // 8)], fill=INK, width=lw)
        d.arc([cx - w // 12, cy + h // 12, cx + w // 12, cy + h // 4], 0, 200, fill=ACCENT, width=lw)
    elif kind == "table":
        d.rectangle([x0, y0 + h // 5, x1, y0 + h // 5 + lw * 2], fill=INK)
        d.rectangle([x0, y1 - lw * 2, x1, y1], fill=INK)
        d.line([(x0 + w // 6, y0 + h // 5), (x1 - w // 6, y1)], fill=ACCENT, width=lw)
        d.line([(x1 - w // 6, y0 + h // 5), (x0 + w // 6, y1)], fill=ACCENT, width=lw)
    elif kind == "rotation":
        r = min(w, h) // 3
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=INK, width=lw)
        d.ellipse([cx - r // 3, cy - r // 3, cx + r // 3, cy + r // 3], outline=ACCENT, width=lw)
        d.line([(x0, cy), (cx - r, cy)], fill=INK, width=lw)
        d.line([(cx + r, cy), (x1, cy)], fill=INK, width=lw)
    elif kind == "fluide":
        d.rounded_rectangle([cx - w // 4, y0 + h // 6, cx + w // 4, y1], radius=w // 20,
                            outline=INK, width=lw)
        for k in (0.4, 0.7):
            y = y0 + h * k
            d.line([(cx - w // 4, y), (cx + w // 4, y)], fill=INK, width=lw)
        d.polygon([(cx, y0), (cx - w // 14, y0 + h // 8), (cx + w // 14, y0 + h // 8)], fill=ACCENT)
    elif kind == "electrique":
        d.rounded_rectangle([x0 + w // 8, y0 + h // 8, x1 - w // 8, y1], radius=w // 25,
                            outline=INK, width=lw)
        d.line([(cx + w // 12, y0 + h // 4), (cx - w // 12, cy), (cx + w // 12, cy),
                (cx - w // 12, y1 - h // 6)], fill=ACCENT, width=lw)
    elif kind == "matiere":
        for i in range(3):
            y = y0 + h * (0.25 + 0.25 * i)
            d.rectangle([x0 + i * w // 12, y, x1 - (2 - i) * w // 12, y + h // 10], outline=INK,
                        width=lw)
    elif kind == "visserie":
        d.regular_polygon((cx, y0 + h // 4, w // 6), 6, outline=INK, width=lw)
        d.rectangle([cx - w // 20, y0 + h // 4 + w // 6, cx + w // 20, y1], outline=INK, width=lw)
        for k in range(5):
            y = y0 + h // 4 + w // 6 + (k + 1) * (y1 - y0 - h // 4 - w // 6) / 6
            d.line([(cx - w // 14, y), (cx + w // 14, y - h // 40)], fill=ACCENT, width=max(2, lw // 2))
    elif kind == "service":
        r = min(w, h) // 3
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=INK, width=lw)
        for a in range(8):
            import math
            ang = a * math.pi / 4
            d.line([(cx + r * math.cos(ang), cy + r * math.sin(ang)),
                    (cx + (r + w // 12) * math.cos(ang), cy + (r + w // 12) * math.sin(ang))],
                   fill=INK, width=lw * 2)
        d.ellipse([cx - r // 3, cy - r // 3, cx + r // 3, cy + r // 3], outline=ACCENT, width=lw)
    else:
        d.polygon([(x0 + w // 6, y0 + h // 3), (cx, y0 + h // 6), (x1 - w // 6, y0 + h // 3),
                   (cx, y0 + h // 2)], outline=INK, width=lw)
        d.line([(x0 + w // 6, y0 + h // 3), (x0 + w // 6, y1 - h // 6), (cx, y1),
                (x1 - w // 6, y1 - h // 6), (x1 - w // 6, y0 + h // 3)], fill=INK, width=lw)
        d.line([(cx, y0 + h // 2), (cx, y1)], fill=INK, width=lw)


def product_png(code, name, category, is_service):
    img = Image.new("RGB", (512, 512), PAPER)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 511, 511], outline=(214, 220, 228), width=2)
    draw_glyph(d, glyph_kind(f"{name} {category or ''}", is_service), (116, 70, 396, 330))
    d.text((24, 22), code or "", fill=ACCENT, font=font(24, True))
    lines = textwrap.wrap(name or "", width=30)[:3]
    for i, line in enumerate(lines):
        d.text((256, 372 + i * 34), line, fill=INK, font=font(24), anchor="mt")
    return img


def logo_png(name):
    words = [w for w in re.split(r"[\s\-'’]+", re.sub(r"^T\d+\s*-\s*", "", name or "")) if w]
    stop = {"de", "du", "des", "la", "le", "les", "et", "sa", "sas", "sarl", "gmbh", "nv", "d", "l"}
    sig = [w for w in words if w.lower() not in stop] or words or ["?"]
    initials = "".join(w[0] for w in sig[:2]).upper()
    color = PALETTE[int(hashlib.md5((name or "").encode()).hexdigest(), 16) % len(PALETTE)]
    img = Image.new("RGB", (512, 512), (255, 255, 255))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([56, 56, 456, 456], radius=90, fill=color)
    d.text((256, 256), initials, fill=(255, 255, 255), font=font(190, True), anchor="mm")
    return img


def png_bytes(img):
    b = io.BytesIO()
    img.save(b, "PNG", optimize=True)
    return b.getvalue()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=not os.environ.get("AOS_COOKIE_JAR"),
                    help="URL de l'application (ignorée si AOS_COOKIE_JAR est défini)")
    ap.add_argument("--user", default=os.environ.get("AOS_USER"),
                    help="instance locale : identifiant (défaut : variable AOS_USER) ; ignoré sous session REST")
    ap.add_argument("--password", default=os.environ.get("AOS_PASSWORD"),
                    help="instance locale : mot de passe (défaut : variable AOS_PASSWORD, à préférer) ; ignoré sous session REST")
    ap.add_argument("--proxy")
    ap.add_argument("--model", required=True, choices=("product", "partner"))
    ap.add_argument("--ids", required=True)
    ap.add_argument("--dry-run", metavar="DIR")
    a = ap.parse_args()
    model = ("com.axelor.apps.base.db.Product" if a.model == "product"
             else "com.axelor.apps.base.db.Partner")
    fields = (["code", "name", "productCategory", "productTypeSelect", "picture"] if a.model == "product"
              else ["fullName", "name", "partnerTypeSelect", "isContact", "picture"])
    cli = Client(a.base, a.user, a.password, a.proxy)
    done = skipped = failed = 0
    for rid in (int(x) for x in a.ids.split(",") if x.strip()):
        try:
            r = cli.req(f"/ws/rest/{model}/{rid}/fetch", {"fields": fields + ["version"]})["data"][0]
            if r.get("picture"):
                print(f"{rid}\tIGNORÉ\timage déjà posée (jamais remplacée)")
                skipped += 1
                continue
            if a.model == "product":
                cat = (r.get("productCategory") or {}).get("name")
                img = product_png(r.get("code"), r.get("name"), cat,
                                  r.get("productTypeSelect") == "service")
                fname = f"article-{r.get('code') or rid}.png"
            else:
                if r.get("isContact") or r.get("partnerTypeSelect") == 2:
                    print(f"{rid}\tIGNORÉ\tpersonne : photo au choix, pas de logo")
                    skipped += 1
                    continue
                img = logo_png(r.get("name") or r.get("fullName"))  # name : sans la séquence du tiers
                fname = f"logo-{rid}.png"
            fname = re.sub(r"[^\w.\-]", "_", fname)
            if a.dry_run:
                os.makedirs(a.dry_run, exist_ok=True)
                img.save(os.path.join(a.dry_run, fname))
                print(f"{rid}\tDESSINÉ\t{os.path.join(a.dry_run, fname)}")
                done += 1
                continue
            fid = cli.upload_png(fname, png_bytes(img))
            u = cli.req(f"/ws/rest/{model}/{rid}", {"data": {"id": rid, "version": r.get("version"),
                                                             "picture": {"id": fid}}})
            ok = u.get("status") == 0
            print(f"{rid}\t{'POSÉ' if ok else 'ÉCHEC'}\tfichier #{fid}" + ("" if ok else f" {str(u)[:200]}"))
            done += ok
            failed += not ok
        except Exception as e:  # une fiche en erreur n'arrête pas le lot
            print(f"{rid}\tERREUR\t{str(e)[:200]}")
            failed += 1
    print(f"— {done} visuel(s), {skipped} ignoré(s), {failed} en échec")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
