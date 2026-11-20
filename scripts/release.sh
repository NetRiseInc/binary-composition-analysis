#!/usr/bin/env bash
# Cut a release from the current main tip using git + gh.
# Prerequisite: latest release commit is already pushed to origin/main.
#
# Interactive (recommended):
#   make release
#
# Non-interactive:
#   VERSION=v1.0.8 UPDATE_MAJOR=1 make release
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

VERSION="${VERSION:-}"
UPDATE_MAJOR="${UPDATE_MAJOR:-}"
SKIP_CHECK="${SKIP_CHECK:-0}"
REMOTE="${REMOTE:-origin}"
BRANCH="${BRANCH:-main}"

usage() {
  cat <<'EOF'
Usage:
  make release
      Detect latest release, suggest minor (default) or major, confirm, then ship.

  VERSION=v1.0.8 make release
  VERSION=v1.0.8 UPDATE_MAJOR=1 make release
      Non-interactive; skip prompts when VERSION is set.

Environment:
  VERSION         Optional. If set, skip version prompts (e.g. v1.0.8).
  UPDATE_MAJOR    If 1/0, skip the floating-tag prompt. If unset interactively, you will be asked.
  SKIP_CHECK      If 1, skip make check before tagging.
  REMOTE          Git remote (default: origin).
  BRANCH          Expected branch (default: main).
EOF
}

die() {
  echo "error: $*" >&2
  exit 1
}

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "'$1' is required"
}

prompt() {
  local reply
  local message="$1"
  local default="${2:-}"
  if [[ -n "$default" ]]; then
    read -r -p "$message [$default]: " reply
    reply="${reply:-$default}"
  else
    read -r -p "$message: " reply
  fi
  printf '%s' "$reply"
}

confirm_yes() {
  local message="$1"
  local default="${2:-y}"
  local reply
  reply="$(prompt "$message" "$default")"
  case "$(printf '%s' "$reply" | tr '[:upper:]' '[:lower:]')" in
    y|yes) return 0 ;;
    n|no) return 1 ;;
    *)
      echo "Please answer y or n."
      confirm_yes "$message" "$default"
      ;;
  esac
}

extract_changelog() {
  local ver="$1"
  local out="$2"
  awk -v ver="$ver" '
    BEGIN { keep=0 }
    $0 ~ "^## " ver "$" { keep=1; next }
    keep && $0 ~ /^## / { exit }
    keep { print }
  ' CHANGELOG.md >"$out"
}

# Latest semver tag like v1.2.3 (ignores floating v1 / legacy v.1.0.1).
latest_release_tag() {
  local tag
  tag="$(git tag -l 'v*.*.*' --sort=-v:refname | grep -E '^v[0-9]+\.[0-9]+\.[0-9]+$' | head -n1 || true)"
  if [[ -z "$tag" ]]; then
    tag="$(gh release list --limit 20 --json tagName --jq '.[].tagName' 2>/dev/null | grep -E '^v[0-9]+\.[0-9]+\.[0-9]+$' | head -n1 || true)"
  fi
  printf '%s' "$tag"
}

parse_semver() {
  local tag="$1"
  local bare="${tag#v}"
  MAJOR="${bare%%.*}"
  local rest="${bare#*.}"
  MINOR="${rest%%.*}"
  PATCH="${rest#*.}"
  [[ "$MAJOR" =~ ^[0-9]+$ && "$MINOR" =~ ^[0-9]+$ && "$PATCH" =~ ^[0-9]+$ ]] \
    || die "could not parse semver from '$tag'"
}

bump_version() {
  local kind="$1"
  case "$kind" in
    minor) printf 'v%s.%s.0' "$MAJOR" "$((MINOR + 1))" ;;
    major) printf 'v%s.0.0' "$((MAJOR + 1))" ;;
    patch) printf 'v%s.%s.%s' "$MAJOR" "$MINOR" "$((PATCH + 1))" ;;
    *) die "unknown bump kind '$kind'" ;;
  esac
}

choose_version_interactive() {
  local current next_minor next_major next_patch kind reply
  current="$(latest_release_tag)"
  if [[ -z "$current" ]]; then
    echo "No existing vX.Y.Z release tag found."
    current="v0.0.0"
    echo "Treating current release as $current"
  else
    echo "Current release: $current"
  fi

  parse_semver "$current"
  next_minor="$(bump_version minor)"
  next_major="$(bump_version major)"
  next_patch="$(bump_version patch)"

  echo
  echo "Choose the next release type:"
  echo "  minor (default)  -> $next_minor"
  echo "  major            -> $next_major"
  echo "  patch            -> $next_patch"
  echo
  kind="$(prompt "Release type (minor/major/patch)" "minor")"
  kind="$(printf '%s' "$kind" | tr '[:upper:]' '[:lower:]')"
  case "$kind" in
    minor|n) VERSION="$(bump_version minor)" ;;
    major|m) VERSION="$(bump_version major)" ;;
    patch|p) VERSION="$(bump_version patch)" ;;
    *)
      die "expected minor, major, or patch (got '$kind')"
      ;;
  esac

  echo
  echo "Proposed release: $VERSION"
  if ! confirm_yes "Proceed with $VERSION?" "y"; then
    echo "Aborted."
    exit 0
  fi

  if [[ -z "$UPDATE_MAJOR" ]]; then
    local bare="${VERSION#v}"
    local major_tag="v${bare%%.*}"
    echo
    if confirm_yes "Update floating major tag $major_tag -> $VERSION?" "y"; then
      UPDATE_MAJOR=1
    else
      UPDATE_MAJOR=0
    fi
  fi
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

need_cmd git
need_cmd gh
need_cmd make

# Interactive TTY required when VERSION is not provided.
if [[ -z "$VERSION" ]]; then
  [[ -t 0 ]] || die "VERSION is unset and stdin is not a TTY; set VERSION=vX.Y.Z for non-interactive use"
fi

echo "==> Preflight"
current_branch="$(git branch --show-current)"
[[ "$current_branch" == "$BRANCH" ]] || die "must be on '$BRANCH' (currently on '$current_branch')"

git fetch "$REMOTE" "$BRANCH" --tags

[[ -z "$(git status --porcelain)" ]] || die "working tree is not clean; commit or stash first"

local_sha="$(git rev-parse HEAD)"
remote_sha="$(git rev-parse "$REMOTE/$BRANCH")"
[[ "$local_sha" == "$remote_sha" ]] || die "local $BRANCH ($local_sha) differs from $REMOTE/$BRANCH ($remote_sha); pull/push first"

gh auth status >/dev/null

if [[ -z "$VERSION" ]]; then
  choose_version_interactive
fi

[[ "$VERSION" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]] || die "VERSION must look like v1.2.3 (got '$VERSION')"

CHANGELOG_VERSION="${VERSION#v}"
MAJOR_TAG="v${CHANGELOG_VERSION%%.*}"
NOTES="$(mktemp)"
trap 'rm -f "$NOTES"' EXIT

if git rev-parse "$VERSION" >/dev/null 2>&1; then
  die "tag '$VERSION' already exists"
fi

extract_changelog "$CHANGELOG_VERSION" "$NOTES"
[[ -s "$NOTES" ]] || die "CHANGELOG.md has no '## $CHANGELOG_VERSION' section — add it before releasing"

# Non-interactive default: do not move floating tag unless asked.
if [[ -z "$UPDATE_MAJOR" ]]; then
  UPDATE_MAJOR=0
fi

if [[ "$SKIP_CHECK" != "1" ]]; then
  echo "==> make check"
  make check
else
  echo "==> Skipping make check (SKIP_CHECK=1)"
fi

echo "==> Creating tag $VERSION at $local_sha"
git tag -a "$VERSION" -m "Release $VERSION"
git push "$REMOTE" "$VERSION"

echo "==> Creating GitHub Release $VERSION"
gh release create "$VERSION" \
  --title "$VERSION" \
  --notes-file "$NOTES" \
  --verify-tag

if [[ "$UPDATE_MAJOR" == "1" ]]; then
  echo "==> Updating floating major tag $MAJOR_TAG -> $VERSION"
  git tag -f "$MAJOR_TAG" "$VERSION"
  git push "$REMOTE" "refs/tags/$MAJOR_TAG" --force
else
  echo "==> Skipping floating major tag update ($MAJOR_TAG)"
fi

echo
echo "Released $VERSION"
gh release view "$VERSION" --web 2>/dev/null || gh release view "$VERSION"
