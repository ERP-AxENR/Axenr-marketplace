# Format Redmine (projets encore sous Redmine)

Les projets AxENR sont passés sous Jira depuis l'été 2026. Ce format ne sert que pour un projet encore suivi dans un Redmine (instance d'un intégrateur, historique). La méthode (challenge, structure, passe anti-slop) reste celle du skill ; seule la syntaxe change.

## D'abord : quel formateur utilise ce Redmine ?

Redmine propose deux formateurs de texte, réglés par l'administrateur (Administration > Paramètres > Affichage > Formatage du texte) :

| Formateur | Syntaxe | Règle AxENR |
|---|---|---|
| **Markdown** (CommonMark) | `#`, `**gras**`, `` `code` ``, `- item`, `[texte](url)`, blocs ``` | **Par défaut** : les tickets Redmine AxENR s'écrivent en Markdown standard, jamais en Textile |
| **Textile** | `h2.`, `*gras*`, `@code@`, `* item`, `"texte":url`, `<pre>` | Seulement si le Redmine cible est configuré en Textile (vérifier sur un ticket existant) |

En cas de doute, ouvrir un ticket existant en édition : `h2.` et `@code@` signalent du Textile, `##` et backticks du Markdown.

## Structure du ticket Redmine

Mêmes sections que la structure Jira du skill (objectif métier, spécification, périmètre, recette, points ouverts, points techniques). Le titre commence par un verbe d'action, moins de 80 caractères.

## Antisèche Textile (Redmine configuré en Textile)

| Élément | Textile | Ne pas utiliser |
|---|---|---|
| Titres | `h1.` `h2.` `h3.` | `#` `##` |
| Gras / italique / souligné / barré | `*gras*` `_italique_` `+souligné+` `-barré-` | `**gras**` |
| Code inline | `@code@` | backticks |
| Liste à puces | `* item`, `** sous-item` | `- item` |
| Liste ordonnée | `# étape`, `## sous-étape` | `1. étape` |
| Lien | `"texte":https://exemple.com` | `[texte](url)` |
| Bloc de code | `<pre><code class="java">…</code></pre>` | triples backticks |
| Tableau | `|_. En-tête |_. En-tête |` puis `| cellule | cellule |` | tableau GFM |
| Image | `!image.png!`, `!{width: 300px}image.png!` | `![](…)` |

Liens Redmine utiles (les deux formateurs) : `#123` (ticket), `r1234` (révision), `[[Page]]` (wiki), `@login` (utilisateur).

Macros : `{{toc}}`, `{{collapse(Voir détails)}}…{{end}}`, `{{thumbnail(image.png, size=300)}}`.

## Schémas dans Redmine

| Format | Rendu |
|---|---|
| ASCII dans un bloc de code | Toujours |
| Mermaid, PlantUML, Graphviz | Seulement avec le plugin correspondant ; sinon le texte reste lisible |

## Checklist avant livraison (Textile)

- [ ] Titres en `h2.` / `h3.`
- [ ] Gras en `*gras*`, code inline en `@code@`
- [ ] Puces en `*`, listes ordonnées en `#`
- [ ] Liens en `"texte":url`
- [ ] Blocs de code en `<pre><code class="…">`
- [ ] En-têtes de tableau en `|_.`
