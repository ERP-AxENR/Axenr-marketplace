---
description: Montee de version des patchs Axelor (AOS/AOP) via l'agent axenr-montee-version. Parametre unique = version AOS cible. Resout la compatibilite enterprise, applique, teste la non-regression, prepare un ticket Jira.
argument-hint: <version-aos-cible>
---

# /axenr-dev:montee-version

Lance une montee de version Axelor autonome sur le projet courant (axenr-app ou gmao-app) via l'agent **axenr-montee-version**.

## USAGE

```
/axenr-dev:montee-version 8.5.22
```

Parametre unique : la version AOS cible. Tout le reste (AOP, modules enterprise, addons compatibles) est resolu automatiquement.

## ARGUMENTS

$ARGUMENTS

Format attendu : `<version-aos-cible>` (ex: `8.5.22`).

Si l'argument est absent ou ambigu, DEMANDER la version cible. Ne pas deviner.

## DELEGATION

Passer la version cible a l'agent **axenr-montee-version**. L'agent gere l'INTEGRALITE du workflow a gates de maniere autonome :

1. Contexte + table source (libs.versions.toml, gradle.properties)
2. Resolution de compatibilite (version-matcher.axelor.com + Nexus)
3. Analyse des changements AOS (delegue a la skill migration-validator)
4. Application auto des versions
5. Non-regression (compileJava, 3 casses recurrentes, build)
6. Coherence PR (GMAO <-> AxENR)
7. Ticket Jira + PR

NE PAS decrire ni repeter les phases ici. L'agent est la SEULE source de verite pour le workflow.
