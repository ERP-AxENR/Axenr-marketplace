#!/usr/bin/env bash
# Bump the single AxENR version across marketplace.json and every AxENR plugin.json.
# Every plugin except the partner plugin "axelor" shares the same version.
# Usage: ./scripts/bump-version.sh [patch|minor|major|auto]

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MARKETPLACE_JSON="$ROOT/.claude-plugin/marketplace.json"
PARTNER_PLUGIN="axelor"

if ! command -v jq >/dev/null 2>&1; then
  echo "jq is required (brew install jq)" >&2
  exit 2
fi

BUMP_TYPE="${1:-auto}"

current_version=$(jq -r '.version' "$MARKETPLACE_JSON")
echo "Current version: $current_version"

if [[ "$BUMP_TYPE" == "auto" ]]; then
  last_tag=$(git -C "$ROOT" describe --tags --abbrev=0 2>/dev/null || echo "")
  if [[ -n "$last_tag" ]]; then
    commits=$(git -C "$ROOT" log "${last_tag}..HEAD" --format="%s%n%b")
  else
    commits=$(git -C "$ROOT" log --format="%s%n%b")
  fi

  if echo "$commits" | grep -qE "(BREAKING CHANGE|^[a-z]+!:)"; then
    BUMP_TYPE="major"
  elif echo "$commits" | grep -qE "^feat(\([^)]*\))?:"; then
    BUMP_TYPE="minor"
  else
    BUMP_TYPE="patch"
  fi
  echo "Auto-detected bump: $BUMP_TYPE"
fi

IFS='.' read -r major minor patch <<<"$current_version"

case "$BUMP_TYPE" in
  major) major=$((major + 1)); minor=0; patch=0 ;;
  minor) minor=$((minor + 1)); patch=0 ;;
  patch) patch=$((patch + 1)) ;;
  *) echo "Unknown bump type: $BUMP_TYPE" >&2; exit 2 ;;
esac

new_version="${major}.${minor}.${patch}"
echo "New version: $new_version"

tmp=$(mktemp)
jq --arg v "$new_version" --arg partner "$PARTNER_PLUGIN" \
   '.version = $v
    | .plugins |= map(if .name == $partner then . else .version = $v end)' \
   "$MARKETPLACE_JSON" > "$tmp" && mv "$tmp" "$MARKETPLACE_JSON"

echo "Updated:"
echo "  $MARKETPLACE_JSON"
for source in $(jq -r --arg partner "$PARTNER_PLUGIN" '.plugins[] | select(.name != $partner) | .source' "$MARKETPLACE_JSON"); do
  plugin_json="$ROOT/${source#./}/.claude-plugin/plugin.json"
  tmp=$(mktemp)
  jq --arg v "$new_version" '.version = $v' "$plugin_json" > "$tmp" && mv "$tmp" "$plugin_json"
  echo "  $plugin_json"
done
echo ""
echo "Next steps:"
echo "  git add .claude-plugin/marketplace.json plugins/*/.claude-plugin/plugin.json"
echo "  GIT_COMMITTER_NAME=\"fbe-axenr\" GIT_COMMITTER_EMAIL=\"f.benomar@erp-axenr.fr\" \\"
echo "    git commit --author=\"fbe-axenr <f.benomar@erp-axenr.fr>\" \\"
echo "    -m \"chore(release): bump axenr plugins to v$new_version\""
echo "  git tag -a v$new_version -m v$new_version"
echo "  git push origin main v$new_version"
