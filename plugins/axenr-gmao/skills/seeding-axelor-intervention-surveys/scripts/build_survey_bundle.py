#!/usr/bin/env python3
"""Construit un bundle ImportConfiguration (bind XML + ZIP de CSV) pour un
questionnaire d'intervention Axelor, à partir d'une spécification YAML.

    python3 build_survey_bundle.py spec.yaml --out ./bundle

Produit :
    <out>/intervention-survey-bind.xml     -> « fichier de liaison » de l'écran d'import
    <out>/intervention-survey-data.zip     -> « fichier de données »
    <out>/csv/*.csv                        -> les CSV en clair, pour relecture

Le script REFUSE de produire un bundle qui viole une contrainte du moteur : ces
contrôles n'existent nulle part sur le chemin d'import, et une violation donne un
journal vert et un questionnaire faux. Voir references/moteur-questionnaire.md.
"""

from __future__ import annotations

import argparse
import csv
import io
import re
import sys
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

try:
    import yaml
except ImportError:  # --help reste utilisable ; la lecture de la spécification, non
    yaml = None

BLOCKS = {"header", "equipment", "footer", "startup"}
RANGE_TYPES = {"standard", "equipment", "family"}


class SpecError(Exception):
    """Défaut de la spécification : message destiné à l'auteur du questionnaire."""


# --------------------------------------------------------------------------- #
# Grammaire du champ `answer`
# --------------------------------------------------------------------------- #

SIMPLE_TYPES = {
    "texte": "text",
    "text": "text",
    "date": "date",
    "photo": "picture",
    "picture": "picture",
    "signature": "signature",
    # Type très particulier : liste FIGÉE (domicile / agence / intervention
    # précédente / suivante) qui remplit automatiquement une adresse. Il n'a de
    # sens que dans une gamme de prise de poste (block: startup).
    "suivi_avance": "advancedMonitoring",
    "advancedmonitoring": "advancedMonitoring",
}


@dataclass
class AnswerSpec:
    """Un type de réponse tel que décrit dans la spécification."""

    kind: str                       # valeur de answerTypeSelect
    values: list[dict] = field(default_factory=list)   # pour `list`
    default_text: str = ""
    unit: str = ""
    checkbox_name: str = ""
    indication_text: str = ""
    label: str = ""                 # nom lisible de l'AnswerType

    def signature(self) -> tuple:
        """Deux questions qui rendent la même signature partagent un AnswerType.

        Les drapeaux entrent dans la signature : deux listes de mêmes libellés
        mais de remontées différentes sont bien deux types distincts."""
        return (
            self.kind,
            tuple((v["name"], v["nc"], v["follow"], v["default"]) for v in self.values),
            self.default_text,
            self.unit,
            self.checkbox_name,
            self.indication_text,
        )


def parse_answer(raw: str, question_title: str) -> AnswerSpec:
    raw = (raw or "").strip()
    if not raw:
        raise SpecError(f"question « {question_title} » : champ `answer` absent")

    low = raw.lower()
    if low in SIMPLE_TYPES:
        kind = SIMPLE_TYPES[low]
        return AnswerSpec(kind=kind, label=_default_label(kind))

    m = re.fullmatch(r"(liste|list)\s*\[(.*)\]", raw, re.S)
    if m:
        values = []
        for idx, chunk in enumerate(m.group(2).split(","), start=1):
            item = chunk.strip()
            if not item:
                continue
            nc = follow = default = False
            while item.endswith(("!nc", "!suivi", "!def")):
                if item.endswith("!nc"):
                    nc, item = True, item[:-3].strip()
                elif item.endswith("!suivi"):
                    follow, item = True, item[:-6].strip()
                else:
                    default, item = True, item[:-4].strip()
            item = item.strip('"').strip("'").strip()
            if not item:
                raise SpecError(f"question « {question_title} » : choix vide dans la liste")
            values.append({"name": item, "nc": nc, "follow": follow,
                           "default": default, "seq": idx})
        if not values:
            raise SpecError(f"question « {question_title} » : liste sans aucun choix")
        names = [v["name"] for v in values]
        dupes = {n for n in names if names.count(n) > 1}
        if dupes:
            # L'appariement d'une réponse conditionnelle se fait par le NOM du
            # choix : deux homonymes rendent le conditionnement indéterminé.
            raise SpecError(
                f"question « {question_title} » : choix en double {sorted(dupes)} — "
                "les libellés doivent être uniques dans une même liste"
            )
        return AnswerSpec(kind="list", values=values, label=_short("", " / ".join(names)))

    m = re.fullmatch(r"(texte|text)\s*\(\s*(.*?)\s*\)", raw, re.S)
    if m:
        txt = m.group(2).strip('"').strip("'")
        return AnswerSpec(kind="text", default_text=txt, label=_short("Texte", txt))

    m = re.fullmatch(r"(mesure|measure)\s*\(\s*(.*?)\s*\)", raw, re.S)
    if m:
        unit = m.group(2).strip('"').strip("'")
        return AnswerSpec(kind="measure", unit=unit, label=f"Mesure ({unit})")

    m = re.fullmatch(r"(case|checkbox)\s*\(\s*(.*?)\s*\)", raw, re.S)
    if m:
        name = m.group(2).strip('"').strip("'")
        return AnswerSpec(kind="checkbox", checkbox_name=name, label=_short("Case", name))

    m = re.fullmatch(r"(indication)\s*\(\s*(.*?)\s*\)", raw, re.S)
    if m:
        txt = m.group(2).strip('"').strip("'")
        return AnswerSpec(kind="indication", indication_text=txt,
                          label=_short("Indication", txt))

    raise SpecError(
        f"question « {question_title} » : type de réponse « {raw} » non reconnu. "
        "Formes acceptées : liste[...], texte, texte(\"défaut\"), date, photo, "
        "signature, mesure(unité), case(\"libellé\"), indication(\"texte\")"
    )


def _short(prefix: str, text: str, limit: int = 90) -> str:
    """Libellé d'AnswerType lisible : le nom sert de libellé dans les sélecteurs,
    une coupure au milieu d'un mot s'y voit."""
    text = " ".join(text.split())
    if len(text) > limit:
        cut = text[:limit].rsplit(" ", 1)[0]
        text = f"{cut}…"
    return f"{prefix} — {text}" if prefix else text


def _default_label(kind: str) -> str:
    return {"text": "Texte", "date": "Date", "picture": "Photo",
            "signature": "Signature",
            "advancedMonitoring": "Suivi avancé de prise de poste"}.get(kind, kind.capitalize())


# --------------------------------------------------------------------------- #
# Modèle intermédiaire
# --------------------------------------------------------------------------- #

@dataclass
class Row:
    import_id: str
    data: dict


class Bundle:
    def __init__(self, code: str):
        if not re.fullmatch(r"[A-Z0-9][A-Z0-9-]{0,15}", code or ""):
            raise SpecError(
                "`code` absent ou invalide : 1 à 16 caractères en majuscules, "
                "chiffres ou tiret. Il préfixe tous les importId et c'est ce qui "
                "empêche le bundle d'écraser les données de démo AOS (importId 1..13)."
            )
        self.code = code
        self.answer_types: dict[tuple, str] = {}     # signature -> importId
        self.at_rows: list[Row] = []
        self.av_rows: list[Row] = []
        self.q_rows: list[Row] = []
        self.rt_rows: list[Row] = []
        self.r_rows: list[Row] = []
        self.rq_rows: list[Row] = []
        self.rq_cond_rows: list[Row] = []
        self.or_rows: list[Row] = []
        self.cat_rows: list[Row] = []
        self.it_rows: list[Row] = []
        self._counters: dict[str, int] = {}
        self._seen_at: set[str] = set()

    def nid(self, prefix: str, key: str | None = None) -> str:
        """Identifiant d'import STABLE.

        Dérivé du libellé, pas d'un compteur : un importId positionnel se
        re-mappe sur d'autres lignes dès qu'on insère, retire ou déplace un
        élément de la spécification, et le ré-import RENOMME alors des lignes
        existantes au lieu de les mettre à jour. Avec un identifiant dérivé du
        libellé, réordonner ne change rien ; seul un renommage crée une ligne
        neuve, ce qui est prévisible et visible."""
        if key is None:
            self._counters[prefix] = self._counters.get(prefix, 0) + 1
            return f"{self.code}-{prefix}{self._counters[prefix]}"
        base = f"{self.code}-{prefix}-{slug(key)}"
        n = self._counters.get(base, 0) + 1
        self._counters[base] = n
        return base if n == 1 else f"{base}-{n}"

    # -- catalogue ---------------------------------------------------------- #

    def answer_type(self, spec: AnswerSpec) -> str:
        sig = spec.signature()
        if sig in self.answer_types:
            return self.answer_types[sig]
        at_id = self.nid("at", spec.label or spec.kind)
        if at_id in self._seen_at:
            at_id = self.nid("at", (spec.label or spec.kind) + "-x")
        self._seen_at.add(at_id)
        self.answer_types[sig] = at_id
        self.at_rows.append(Row(at_id, {
            "importId": at_id,
            "name": spec.label or _default_label(spec.kind),
            "answerTypeSelect": spec.kind,
            "defaultTextValue": spec.default_text,
            "checkboxName": spec.checkbox_name,
            "indicationText": spec.indication_text,
            "desiredUnit": spec.unit,
        }))
        for v in spec.values:
            # Dérivé de l'identifiant du type PLUS le libellé du choix : ainsi
            # ajouter un choix ne renumérote pas les autres.
            av_id = f"{at_id.replace('-at-', '-av-')}-{slug(v['name'], 28)}"
            v["import_id"] = av_id
            self.av_rows.append(Row(av_id, {
                "importId": av_id,
                "answerType.importId": at_id,
                "name": v["name"],
                # Numéroté systématiquement : la liste des réponses est triée sur
                # ce champ à l'écran, et le jeu de démo AOS le laisse à 0 partout.
                "sequence": str(v["seq"]),
                "isDefault": _b(v["default"]),
                "nonConforming": _b(v["nc"]),
                "following": _b(v["follow"]),
            }))
        return at_id


def _b(value) -> str:
    return "true" if value else "false"


# --------------------------------------------------------------------------- #
# Construction
# --------------------------------------------------------------------------- #

def slug(text: str, limit: int = 40) -> str:
    """Fragment d'identifiant stable et lisible, ASCII seulement."""
    import unicodedata
    t = unicodedata.normalize("NFKD", text)
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = re.sub(r"[^A-Za-z0-9]+", "-", t).strip("-").lower()
    return (t[:limit].rstrip("-")) or "x"


_titles: dict[str, str] = {}


def build(spec: dict) -> Bundle:
    _titles.clear()
    b = Bundle(str(spec.get("code", "")).strip())

    ranges = spec.get("ranges") or []
    if not ranges:
        raise SpecError("`ranges` vide : un questionnaire a au moins une gamme")

    it = spec.get("intervention_type")
    it_id = None
    if it:
        cat = it.get("category") or {}
        if not cat.get("code") or not cat.get("name"):
            raise SpecError("`intervention_type.category` doit porter `code` et `name` "
                            "(la catégorie est obligatoire sur un type d'intervention)")
        # Ni la catégorie ni le type ne portent d'importId : ils sont identifiés par
        # leur CODE métier. Poser un importId sur une ligne préexistante la re-marque,
        # et le bundle d'origine qui la cherchait par SON importId en créerait un
        # doublon au prochain passage.
        cat_id = b.nid("ic")
        b.cat_rows.append(Row(cat_id, {"code": cat["code"], "name": cat["name"]}))
        if not it.get("code") or not it.get("name"):
            raise SpecError("`intervention_type` doit porter `code` et `name`")
        it_id = b.nid("it")
        it_code = it["code"]
        b.it_rows.append(Row(it_id, {
            "code": it["code"],
            "name": it["name"],
            "interventionCategory": cat["code"],
        }))

    it_code = it["code"] if it else None
    order_in_type = 0
    seen_titles: set[str] = set()

    for r in ranges:
        title = (r.get("title") or "").strip()
        if not title:
            raise SpecError("une gamme sans `title` — le titre est obligatoire")
        if title in seen_titles:
            raise SpecError(f"deux gammes portent le titre « {title} »")
        seen_titles.add(title)

        rtype = (r.get("type") or "standard").strip()
        if rtype not in RANGE_TYPES:
            raise SpecError(f"gamme « {title} » : `type` doit valoir {sorted(RANGE_TYPES)}")
        block = (r.get("block") or "header").strip()
        if block not in BLOCKS:
            raise SpecError(f"gamme « {title} » : `block` doit valoir {sorted(BLOCKS)}")

        families = [str(f).strip() for f in (r.get("families") or []) if str(f).strip()]
        # P4 : sans famille, la gamme disparaît du questionnaire généré, en silence.
        if rtype == "family" and not families:
            raise SpecError(
                f"gamme « {title} » : type `family` sans `families`. Le générateur ne "
                "produira AUCUN bloc et rien ne le signalera."
            )
        if rtype == "equipment":
            if len(families) != 1:
                raise SpecError(
                    f"gamme « {title} » : type `equipment` attend exactement UNE famille "
                    "(le moteur lit un champ simple, pas la liste)."
                )
        if rtype == "standard" and families:
            raise SpecError(f"gamme « {title} » : type `standard` n'accepte pas de `families`")

        rt_id = b.nid("rt", title)
        b.rt_rows.append(Row(rt_id, {
            "importId": rt_id,
            "name": f"{title} ({rtype})"[:100],
            "rangeTypeSelect": rtype,
            "equipmentFamily": families[0] if rtype == "equipment" else "",
            "equipmentFamilySet": "|".join(families) if rtype == "family" else "",
        }))

        r_id = b.nid("r", title)
        b.r_rows.append(Row(r_id, {
            "importId": r_id,
            "title": title,
            "description": r.get("description", "") or "",
            "isPrivate": _b(r.get("private")),
            "rangeType.importId": rt_id,
        }))

        questions = r.get("questions") or []
        if not questions:
            raise SpecError(f"gamme « {title} » : aucune question")

        # 1er passage : les questions, dans l'ordre déclaré.
        by_title: dict[str, dict] = {}
        for order, q in enumerate(questions, start=1):
            qt = (q.get("title") or "").strip()
            if not qt:
                raise SpecError(f"gamme « {title} » : une question sans `title`")
            if qt in by_title:
                raise SpecError(f"gamme « {title} » : deux questions « {qt} »")

            answer = parse_answer(q.get("answer"), qt)
            if answer.kind == "indication" and q.get("required"):
                # P9 : `indication` est absent de isAnswered, l'état ne bascule jamais.
                raise SpecError(
                    f"question « {qt} » : une indication ne peut pas être obligatoire, "
                    "le moteur ne la considère jamais comme répondue."
                )
            at_id = b.answer_type(answer)

            q_id = b.nid("q", f"{title}-{qt}")
            b.q_rows.append(Row(q_id, {
                "importId": q_id,
                "title": qt,
                "indication": q.get("indication", "") or "",
                "answerType.importId": at_id,
            }))

            rq_id = b.nid("rq", f"{title}-{qt}")
            seq = rq_id.upper()[:250]
            _titles[rq_id] = qt
            b.rq_rows.append(Row(rq_id, {
                "importId": rq_id,
                # Séquence fournie explicitement : c'est la clé de rattachement des
                # questions déjà générées (P5). Laissée vide, elle serait posée par
                # le compteur AOP et changerait d'une base à l'autre.
                "sequence": seq,
                "rangeVal.importId": r_id,
                "question.importId": q_id,
                # Ordre imposé : à 0, l'affichage devient non déterministe (P1).
                "orderSeq": str(order * 10),
                "isRequired": _b(q.get("required")),
                "isPrivate": _b(q.get("private")),
                "summary": _b(q.get("summary")),
                "isConditional": _b(bool(q.get("if"))),
            }))
            by_title[qt] = {"rq_id": rq_id, "order": order * 10,
                            "answer": answer, "spec": q}

        # 2e passage : le conditionnement. Il vit dans un fichier SÉPARÉ parce que
        # le binder CSV ne voit pas les lignes écrites plus tôt dans le même input
        # (piège du binder CSV, cf. skill axelor-import-export) : une auto-référence dans le
        # même fichier ne se résout jamais.
        for qt, info in by_title.items():
            cond = info["spec"].get("if")
            if not cond:
                continue
            pilot_title = (cond.get("question") or "").strip()
            if pilot_title not in by_title:
                raise SpecError(
                    f"question « {qt} » : la question pilote « {pilot_title} » n'est pas "
                    f"dans la gamme « {title} ». Le moteur n'autorise le conditionnement "
                    "qu'à l'intérieur d'une même gamme."
                )
            pilot = by_title[pilot_title]
            if pilot["answer"].kind != "list":
                raise SpecError(
                    f"question « {qt} » : la pilote « {pilot_title} » est de type "
                    f"`{pilot['answer'].kind}`. Seule une question à choix peut conditionner."
                )
            if pilot["order"] >= info["order"]:
                raise SpecError(
                    f"question « {qt} » : elle doit être déclarée APRÈS sa pilote "
                    f"« {pilot_title} » (l'écran refuse l'ordre inverse)."
                )
            wanted = [str(a).strip() for a in (cond.get("answers") or [])]
            if not wanted:
                raise SpecError(f"question « {qt} » : `if.answers` vide — sans réponse "
                                "déclarée, la question reste inactive pour toujours : affichée, "
                                "jamais obligatoire, réponse en lecture seule.")
            index = {v["name"]: v["import_id"] for v in pilot["answer"].values}
            missing = [a for a in wanted if a not in index]
            if missing:
                raise SpecError(
                    f"question « {qt} » : réponses {missing} absentes des choix de "
                    f"« {pilot_title} » ({sorted(index)})"
                )
            # UNE LIGNE PAR RÉPONSE DÉCLENCHANTE, et non une ligne à valeurs
            # séparées par « | ». Vérifié au code (com.axelor.data ne découpe
            # JAMAIS sur « | » : CSVBinder.findAll lie la chaîne brute) et à
            # l'écran le 2026-09-14 : une liaison m2m à plusieurs valeurs pipées
            # importe ZÉRO membre, en silence. Chaque ligne ajoute son membre à
            # la collection déjà persistée (Property.addAll n'écrase pas).
            for a in wanted:
                b.rq_cond_rows.append(Row(info["rq_id"], {
                    "importId": info["rq_id"],
                    "conditionalRangeQuestion.importId": pilot["rq_id"],
                    "conditionalAnswerValueSet": index[a],
                }))

        if it_id:
            column = {"header": "interventionTypeHeader",
                      "equipment": "interventionTypeEquipment",
                      "footer": "interventionTypeFooter"}.get(block)
            # Le bloc `startup` n'est pas un OrderedRange : il ne consomme pas de
            # numéro d'ordre, sinon la numérotation saute.
            if column:
                order_in_type += 1
            or_id = b.nid("or", title)
            row = {"importId": or_id, "sequence": str(order_in_type),
                   "rangeVal.importId": r_id,
                   "interventionTypeHeader": "", "interventionTypeEquipment": "",
                   "interventionTypeFooter": ""}
            if column:
                # Le CODE du type, pas son importId : le type peut préexister dans
                # la base cible (donc porter un autre importId, ou aucun) et la
                # relation non résolue ne produirait aucun message.
                row[column] = it_code
                b.or_rows.append(Row(or_id, row))
            else:
                # bloc `startup` : c'est un champ du type d'intervention, pas un
                # OrderedRange. On le pose sur la ligne du type.
                for r_it in b.it_rows:
                    r_it.data["advancedStartupMonitoringRange.importId"] = r_id
        elif block != "header":
            raise SpecError(
                f"gamme « {title} » : `block` est déclaré mais aucun `intervention_type` "
                "n'est défini — la gamme ne serait rattachée à rien."
            )

    return b


# --------------------------------------------------------------------------- #
# Rendu
# --------------------------------------------------------------------------- #

def write_csv(rows: list[Row]) -> str:
    if not rows:
        return ""
    headers: list[str] = []
    for r in rows:
        for k in r.data:
            if k not in headers:
                headers.append(k)
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=headers, delimiter=";",
                       quoting=csv.QUOTE_ALL, lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow({h: r.data.get(h, "") for h in headers})
    return buf.getvalue()


CHECK = ("com.axelor.utils.helpers.ImportHelper.isValuePresent({f})")

BIND_HEADER = """<?xml version="1.0" encoding="UTF-8"?>
<csv-inputs xmlns="http://axelor.com/xml/ns/data-import"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xsi:schemaLocation="http://axelor.com/xml/ns/data-import https://axelor.com/xml/ns/data-import/data-import_8.2.xsd">
"""


def bind_xml(b: Bundle) -> str:
    """Ordre des <input> = ordre de dépendance. Chaque input est commité avant le
    suivant : c'est ce qui rend les références entre fichiers résolubles."""
    out = [BIND_HEADER]
    P = "com.axelor.apps.intervention.db."

    def block(file, model, body="", search="self.importId = :importId"):
        s = f' search="{search}"' if search else ""
        if body:
            out.append(f'  <input file="{file}" separator=";" type="{model}"{s}>\n'
                       f'{body}  </input>\n')
        else:
            out.append(f'  <input file="{file}" separator=";" type="{model}"{s}/>\n')

    if b.at_rows:
        body = (
            '    <bind column="name" to="name"\n'
            f'      check="{CHECK.format(f="name")}" check-message="Name must not be null"/>\n'
            '    <bind column="answerTypeSelect" to="answerTypeSelect"\n'
            '      check="com.axelor.utils.helpers.ImportHelper.checkSelection('
            f"'{P}AnswerType', 'answerTypeSelect', answerTypeSelect)\"\n"
            '      check-message="Invalid answerTypeSelect"/>\n'
            '    <bind column="desiredUnit" to="desiredUnit" search="self.name = :desiredUnit"\n'
            '      if="desiredUnit"\n'
            '      check="com.axelor.utils.helpers.ImportHelper.isRecordPresent('
            "'com.axelor.apps.base.db.Unit', 'name', desiredUnit)\"\n"
            '      check-message="Unit doesn\'t exist"/>\n'
        )
        block("intervention_answerType.csv", f"{P}AnswerType", body)
    if b.av_rows:
        block("intervention_answerValue.csv", f"{P}AnswerValue")
    if b.q_rows:
        block("intervention_question.csv", f"{P}Question")
    if b.rt_rows:
        body = (
            '    <bind column="rangeTypeSelect" to="rangeTypeSelect"\n'
            '      check="com.axelor.utils.helpers.ImportHelper.checkSelection('
            f"'{P}RangeType', 'rangeTypeSelect', rangeTypeSelect)\"\n"
            '      check-message="Invalid rangeTypeSelect"/>\n'
            '    <bind column="equipmentFamily" to="equipmentFamily"\n'
            '      search="self.code = :equipmentFamily" if="equipmentFamily"\n'
            '      check="com.axelor.utils.helpers.ImportHelper.isRecordPresent('
            f"'{P}EquipmentFamily', 'code', equipmentFamily)\"\n"
            '      check-message="Equipment family doesn\'t exist"/>\n'
            '    <bind column="equipmentFamilySet" to="equipmentFamilySet"\n'
            '      search="self.code in :equipmentFamilySet" if="equipmentFamilySet"/>\n'
        )
        block("intervention_rangeType.csv", f"{P}RangeType", body)
    if b.r_rows:
        body = ('    <bind column="title" to="title"\n'
                f'      check="{CHECK.format(f="title")}" check-message="Title must not be null"/>\n')
        block("intervention_range.csv", f"{P}Range", body)
    if b.rq_rows:
        block("intervention_rangeQuestion.csv", f"{P}RangeQuestion")
    if b.cat_rows:
        # Recherche par CODE, pas par importId : la catégorie et le type portent un
        # code métier (unique pour le type). Chercher par importId sur une base qui
        # porte déjà ce code crée un doublon de catégorie, et VIOLE la contrainte
        # d'unicité du type. Par code, le bundle réutilise l'existant.
        block("intervention_interventionCategory.csv", f"{P}InterventionCategory",
              search="self.code = :code")
    if b.it_rows:
        body = ('    <bind column="interventionCategory" to="interventionCategory"\n'
                '      search="self.code = :interventionCategory"\n'
                '      check="com.axelor.utils.helpers.ImportHelper.isRecordPresent('
                f"'{P}InterventionCategory', 'code', interventionCategory)\"\n"
                '      check-message="Intervention category doesn\'t exist"/>\n')
        block("intervention_interventionType.csv", f"{P}InterventionType", body,
              search="self.code = :code")
    if b.or_rows:
        body = ""
        for col in ("interventionTypeHeader", "interventionTypeEquipment",
                    "interventionTypeFooter"):
            body += (f'    <bind column="{col}" to="{col}"\n'
                     f'      search="self.code = :{col}" if="{col}"\n'
                     '      check="com.axelor.utils.helpers.ImportHelper.isRecordPresent('
                     f"'{P}InterventionType', 'code', {col})\"\n"
                     '      check-message="Intervention type doesn\'t exist"/>\n')
        block("intervention_orderedRange.csv", f"{P}OrderedRange", body)
    if b.rq_cond_rows:
        # Seconde passe, volontairement en dernier : les RangeQuestion existent, la
        # recherche les trouve. Le fichier ne porte QUE les colonnes de
        # conditionnement — une colonne absente laisse la valeur en place.
        body = ('    <bind column="conditionalAnswerValueSet" to="conditionalAnswerValueSet"\n'
                '      search="self.importId = :conditionalAnswerValueSet"\n'
                '      check="com.axelor.utils.helpers.ImportHelper.isRecordPresent('
                f"'{P}AnswerValue', 'importId', conditionalAnswerValueSet)\"\n"
                '      check-message="Conditional answer value doesn\'t exist"/>\n')
        block("intervention_rangeQuestion_conditions.csv", f"{P}RangeQuestion", body)

    out.append("\n</csv-inputs>\n")
    return "".join(out)


FILES = [
    ("intervention_answerType.csv", "at_rows"),
    ("intervention_answerValue.csv", "av_rows"),
    ("intervention_question.csv", "q_rows"),
    ("intervention_rangeType.csv", "rt_rows"),
    ("intervention_range.csv", "r_rows"),
    ("intervention_rangeQuestion.csv", "rq_rows"),
    ("intervention_interventionCategory.csv", "cat_rows"),
    ("intervention_interventionType.csv", "it_rows"),
    ("intervention_orderedRange.csv", "or_rows"),
    ("intervention_rangeQuestion_conditions.csv", "rq_cond_rows"),
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec", help="fichier YAML de spécification du questionnaire")
    ap.add_argument("--out", default="bundle", help="dossier de sortie (défaut: ./bundle)")
    args = ap.parse_args()

    if yaml is None:
        print("PyYAML est requis pour lire la spécification : pip install pyyaml", file=sys.stderr)
        return 2
    try:
        spec = yaml.safe_load(Path(args.spec).read_text(encoding="utf-8"))
        if not isinstance(spec, dict):
            raise SpecError("le fichier ne contient pas un dictionnaire YAML")
        b = build(spec)
    except SpecError as exc:
        print(f"Spécification refusée : {exc}", file=sys.stderr)
        return 2

    out = Path(args.out)
    (out / "csv").mkdir(parents=True, exist_ok=True)

    produced = []
    for name, attr in FILES:
        rows = getattr(b, attr)
        if not rows:
            continue
        (out / "csv" / name).write_text(write_csv(rows), encoding="utf-8")
        produced.append(name)

    zip_path = out / "intervention-survey-data.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for name in produced:
            z.write(out / "csv" / name, arcname=name)

    bind_path = out / "intervention-survey-bind.xml"
    bind_path.write_text(bind_xml(b), encoding="utf-8")

    print(f"Bundle « {b.code} » écrit dans {out}/")
    print(f"  liaison : {bind_path}")
    print(f"  données : {zip_path}  ({len(produced)} fichiers)")
    print(f"  {len(b.at_rows)} types de réponse, {len(b.av_rows)} choix, "
          f"{len(b.q_rows)} questions, {len(b.r_rows)} gammes, "
          f"{len({r.import_id for r in b.rq_cond_rows})} conditionnements "
          f"({len(b.rq_cond_rows)} lignes de liaison)")
    for r_row in b.r_rows:
        n = sum(1 for q in b.rq_rows if q.data["rangeVal.importId"] == r_row.import_id)
        if n > 20:
            print(f"\nATTENTION : la gamme « {r_row.data['title']} » porte {n} questions.")
            print("  Au-delà de 20, l'ordre d'affichage CASSE — observé le 2026-09-14 :")
            print("  le générateur trie par paquets de 20 sur une requête sans ORDER BY,")
            print(f"  et les {n - 20} dernières questions se retrouvent en fin de bloc.")
            print("  Découper cette gamme en deux blocs de 20 au plus.")
    vague = sorted({r.data["importId"] for r in b.rq_cond_rows} &
                   {r.import_id for r in b.rq_rows
                    if not _titles.get(r.import_id, "").lower().startswith(("si ", "si:"))})
    if vague:
        print(f"\nAttention : {len(vague)} question(s) conditionnée(s) dont le libellé ne")
        print("  s'annonce pas comme conditionnel. Une question conditionnée reste AFFICHÉE")
        print("  quand sa condition n'est pas remplie : « Si écart : références concernées »")
        print("  se lit bien dans ce cas, « Références concernées » passe pour une erreur.")
    if not b.it_rows:
        print("\nAttention : aucun `intervention_type` déclaré. Les gammes seront créées\n"
              "  mais rattachées à rien : aucune intervention ne les affichera.")
    print("\nImport : Administration > Configurations d'import, type csv,")
    print("  fichier de liaison = le .xml, fichier de données = le .zip")
    return 0


if __name__ == "__main__":
    sys.exit(main())
