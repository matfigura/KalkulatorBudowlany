#!/usr/bin/env bash
set -Eeuo pipefail

# Automatyczne pobranie kodu, zbudowanie APK i skopiowanie go do Windows.
# Użycie:
#   ./build_apk.sh
#   ./build_apk.sh /media/sf_KalkulatorBudowlany

PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
BRANCH="main"
REMOTE="origin"
DEST_DIR="${1:-${WINDOWS_APK_DIR:-/media/sf_KalkulatorBudowlany_Wspolny}}"
LOG_FILE="$PROJECT_DIR/buildozer-build.log"

error() {
    printf '\nBŁĄD: %s\n' "$*" >&2
    exit 1
}

printf '%s\n' "=== Automatyczne budowanie Kalkulatora Budowlanego ==="

command -v git >/dev/null 2>&1 || error "Nie znaleziono polecenia git."
if [[ -x "$PROJECT_DIR/.venv-buildozer/bin/buildozer" ]]; then
    BUILDOZER="$PROJECT_DIR/.venv-buildozer/bin/buildozer"
elif [[ -x "$PROJECT_DIR/venv_buildozer/bin/buildozer" ]]; then
    BUILDOZER="$PROJECT_DIR/venv_buildozer/bin/buildozer"
elif command -v buildozer >/dev/null 2>&1; then
    BUILDOZER="$(command -v buildozer)"
else
    error "Nie znaleziono Buildozera w środowiskach projektu ani w systemie."
fi

cd "$PROJECT_DIR"

git rev-parse --is-inside-work-tree >/dev/null 2>&1 ||
    error "Ten katalog nie jest repozytorium Git."

CURRENT_BRANCH="$(git branch --show-current)"
[[ "$CURRENT_BRANCH" == "$BRANCH" ]] ||
    error "Jesteś na gałęzi '$CURRENT_BRANCH', a skrypt wymaga '$BRANCH'. Niczego nie przełączam."

# Nie pozwalamy, aby pull nadpisał lokalne lub staged zmiany.
if [[ -n "$(git status --porcelain)" ]]; then
    printf '\nW repozytorium są niezapisane zmiany:\n'
    git status --short
    error "Najpierw zatwierdź i wypchnij potrzebne zmiany albo świadomie je uporządkuj. Skrypt nie usuwa zmian."
fi

printf '\n[1/5] Pobieranie informacji z GitHuba...\n'
git fetch "$REMOTE" ||
    error "Nie udało się pobrać danych z GitHuba."

git show-ref --verify --quiet "refs/remotes/$REMOTE/$BRANCH" ||
    error "Nie znaleziono gałęzi $REMOTE/$BRANCH."

printf '\n[2/5] Aktualizacja kodu z GitHuba (tylko fast-forward)...\n'
git pull --ff-only "$REMOTE" "$BRANCH" ||
    error "Nie można bezpiecznie zaktualizować gałęzi. Sprawdź historię Git; skrypt nie wykonuje resetu ani merge."

[[ -f "$PROJECT_DIR/buildozer.spec" ]] ||
    error "Brakuje pliku buildozer.spec."
[[ -f "$PROJECT_DIR/main.py" ]] ||
    error "Brakuje pliku main.py."

# Wymagamy rzeczywistego punktu montowania, aby nie skopiować APK
# do zwykłego katalogu w Ubuntu, gdy udział Windows nie jest podłączony.
[[ -d "$DEST_DIR" ]] ||
    error "Nie istnieje folder współdzielony: $DEST_DIR"
command -v mountpoint >/dev/null 2>&1 ||
    error "Nie znaleziono polecenia mountpoint."
mountpoint -q "$DEST_DIR" ||
    error "'$DEST_DIR' nie jest punktem montowania. Sprawdź, czy folder współdzielony VirtualBox jest podłączony."

[[ -w "$DEST_DIR" ]] ||
    error "Brak prawa zapisu do folderu współdzielonego: $DEST_DIR"

printf '\n[3/5] Budowanie APK przez Buildozera...\n'
printf 'Log budowania: %s\n' "$LOG_FILE"
cd "$PROJECT_DIR"
if ! "$BUILDOZER" android debug 2>&1 | tee "$LOG_FILE"; then
    error "Buildozer zakończył budowanie błędem. Szczegóły są w buildozer-build.log."
fi

printf '\n[4/5] Wyszukiwanie gotowego APK...\n'
mapfile -t APK_CANDIDATES < <(
    find "$PROJECT_DIR/bin" -maxdepth 1 -type f -name '*.apk' -printf '%T@ %p\n' 2>/dev/null |
        sort -nr
)

((${#APK_CANDIDATES[@]} > 0)) ||
    error "Buildozer nie utworzył żadnego pliku APK w katalogu bin/."

APK_PATH="${APK_CANDIDATES[0]#* }"
[[ -s "$APK_PATH" ]] ||
    error "Znaleziony plik APK jest pusty: $APK_PATH"

printf '\n[5/5] Kopiowanie APK do folderu Windows...\n'
TEMP_APK="$DEST_DIR/.kalkulator.apk.tmp.$$"
trap 'rm -f -- "$TEMP_APK"' EXIT
cp -- "$APK_PATH" "$TEMP_APK"
[[ -s "$TEMP_APK" ]] ||
    error "Kopiowanie APK nie powiodło się lub plik docelowy jest pusty."
mv -f -- "$TEMP_APK" "$DEST_DIR/kalkulator.apk"
trap - EXIT

printf '\nSUKCES!\n'
printf 'APK w Ubuntu: %s\n' "$APK_PATH"
printf 'APK dla Windows: %s/kalkulator.apk\n' "$DEST_DIR"
printf 'Log: %s\n' "$LOG_FILE"
