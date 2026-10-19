#!/usr/bin/env node
// Évalue des expressions showIf / hideIf / readonlyIf d'une vue AOP 8 contre UN enregistrement.
// Entrée (stdin) : {"record": {...}, "exprs": [...], "readonly": true|false}
// `readonly` = mode lecture (fiche existante ouverte : AOP 8 l'ouvre en lecture) ; $readonly() le rend.
// Sortie (stdout) : [{"ok": true, "value": true}, {"ok": false, "error": "..."}, ...]
//
// Sémantique reprise du client web : un identifiant inconnu vaut undefined (donc faux), les
// helpers $moment/$number/$get/$readonly/$popup existent. Un champ M2O arrive comme un objet
// {id, ...} ; une clé pointée "a.b" renvoyée à plat par /fetch est replacée sous record.a.b.
'use strict';

function nest(rec) {
  const out = {};
  for (const [k, v] of Object.entries(rec || {})) {
    if (!k.includes('.')) { if (!(k in out) || typeof out[k] !== 'object') out[k] = v; continue; }
    const parts = k.split('.');
    let cur = out;
    for (let i = 0; i < parts.length - 1; i++) {
      if (cur[parts[i]] == null || typeof cur[parts[i]] !== 'object') cur[parts[i]] = {};
      cur = cur[parts[i]];
    }
    cur[parts[parts.length - 1]] = v;
  }
  return out;
}

function momentStub(v) {
  const d = v == null ? new Date() : new Date(v);
  const t = d.getTime();
  return {
    valueOf: () => t, toString: () => d.toISOString(),
    isBefore: (o) => t < +momentStub(o), isAfter: (o) => t > +momentStub(o),
    isSame: (o) => t === +momentStub(o), diff: (o) => t - +momentStub(o),
    format: () => d.toISOString().slice(0, 10), startOf: () => momentStub(v), endOf: () => momentStub(v),
    add: () => momentStub(v), subtract: () => momentStub(v),  // neutres : limite connue
  };
}

function scopeFor(record, readonlyMode) {
  const base = nest(record);
  const helpers = {
    $moment: momentStub, $number: (x) => Number(x || 0), $readonly: () => !!readonlyMode, $popup: () => false,
    $get: (p) => String(p).split('.').reduce((a, k) => (a == null ? undefined : a[k]), base),
    $contains: (a, b) => Array.isArray(a) ? a.includes(b) : String(a || '').includes(b),
    $fmt: (n) => base[n], $user: 'admin', __user__: { code: 'admin', id: 1 },
    Math, Date, JSON, Number, String, Boolean, Array, Object, parseInt, parseFloat, isNaN,
    undefined: undefined, NaN: NaN, Infinity: Infinity,
  };
  const target = Object.assign({}, helpers, base);
  return new Proxy(target, {
    has: () => true,
    get: (t, k) => (k === Symbol.unscopables ? undefined : (k in t ? t[k] : undefined)),
  });
}

let raw = '';
process.stdin.on('data', (c) => { raw += c; });
process.stdin.on('end', () => {
  const { record, exprs, readonly } = JSON.parse(raw);
  const scope = scopeFor(record, readonly);
  const res = exprs.map((e) => {
    const run = (x) => {
      // eslint-disable-next-line no-new-func
      const f = new Function('scope', 'with (scope) { return (' + x + '); }');
      return !!f(scope);
    };
    try {
      return { ok: true, value: run(e) };
    } catch (err) {
      // relation vide : « lostReason.freeText » lève quand lostReason est null. On rejoue en accès
      // protégé (lostReason?.freeText vaut undefined) ; si ça lève encore, la condition est rendue
      // indécidable et l'appelant laisse l'élément visible.
      const safe = e.replace(/('[^']*'|"[^"]*")|([A-Za-z_$][\w$]*)\.(?=[A-Za-z_$])/g,
        (m, str, id) => (str ? str : id + '?.'));
      try { return { ok: true, value: run(safe), safe: true }; } catch (err2) {
        return { ok: false, error: String(err && err.message || err) };
      }
    }
  });
  process.stdout.write(JSON.stringify(res));
});
