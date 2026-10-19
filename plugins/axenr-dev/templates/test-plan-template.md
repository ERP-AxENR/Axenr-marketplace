# TEST PLAN - Ticket #{{ticket_number}}

> {{ticket_title}}

---

## CONTEXTE

| Info | Valeur |
|------|--------|
| Ticket | #{{ticket_number}} |
| Projet | {{project}} |
| Branche | {{branch}} |
| Type | {{change_type}} |
| Date | {{date}} |

## FICHIERS MODIFIES

| Fichier | Type | Action |
|---------|------|--------|
| {{file_path}} | {{file_type}} | {{created/modified}} |

## TESTS A EFFECTUER

### 1. Verification de base

- [ ] L'application demarre sans erreur
- [ ] Pas de stacktrace dans les logs au demarrage
- [ ] La page principale charge correctement

### 2. Tests fonctionnels

- [ ] {{test_description_1}}
- [ ] {{test_description_2}}
- [ ] {{test_description_3}}

### 3. Tests de regression

- [ ] Les fonctionnalites existantes ne sont pas impactees
- [ ] Les extensions de vues existantes fonctionnent toujours
- [ ] Les traductions s'affichent correctement

### 4. Tests de validation

- [ ] Les champs obligatoires sont valides
- [ ] Les messages d'erreur s'affichent correctement
- [ ] Les permissions sont respectees

### 5. Compatibilite versions

| Module | Version | Compatible |
|--------|---------|------------|
| AOP | {{aop_version}} | {{yes/no}} |
| AOS | {{aos_version}} | {{yes/no}} |

## RESUME

| Metrique | Valeur |
|----------|--------|
| Code reutilise | {{reused_count}} fichiers |
| Code cree | {{created_count}} fichiers |
| Agents de validation passes | {{validation_status}} |
| Build | {{build_status}} |
