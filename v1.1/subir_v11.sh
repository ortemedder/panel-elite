#!/bin/bash
# Sube el proyecto v1.1 a GitHub, en la carpeta v1.1/ del repositorio de siempre (ortemedder/panel-elite):
# el codigo de ~/panel-v11 y el contenido del zip (senders, escucha del pueblo, scripts y herramientas).
# La b20 de la raiz del repositorio no se toca. Lo personal y las claves no se suben nunca.
# Uso:   bash ~/subir_v11.sh                      (busca el panel_v1.1*.zip mas nuevo en tu carpeta personal)
#        bash ~/subir_v11.sh ~/panel_v1.1.zip     (o el zip / carpeta que le digas)
set -u
REPO=~/panel-elite
URL=https://github.com/ortemedder/panel-elite
SRC="${1:-}"

if [ ! -d "$REPO/.git" ]; then
    echo "== No hay copia del repositorio en $REPO: la descargo"
    git clone -q "$URL" "$REPO" || { echo "No he podido clonar $URL"; exit 1; }
fi
cd "$REPO" || exit 1
git pull -q --rebase 2>/dev/null
mkdir -p v1.1 && cd v1.1 || exit 1                      # todo lo de la v1.1 va en esta carpeta

TMP=""
[ -z "$SRC" ] && SRC=$(ls -t ~/panel_v1.1*.zip 2>/dev/null | head -1)
if [ -n "$SRC" ] && [ -f "$SRC" ]; then
    TMP=$(mktemp -d)
    unzip -q "$SRC" -d "$TMP" || { echo "No puedo abrir $SRC"; exit 1; }
    SRC=$(find "$TMP" -mindepth 1 -maxdepth 1 -type d | head -1)
fi
if [ -n "$SRC" ] && [ -d "$SRC" ]; then
    echo "== Version: $(basename "$SRC")"
    mkdir -p pc_ortem pc_korzo escucha-pueblo desarrollo
    cp "$SRC"/pc_ortem/*.py pc_ortem/ 2>/dev/null
    cp "$SRC"/pc_korzo/*.py pc_korzo/ 2>/dev/null
    cp "$SRC"/escucha-pueblo/*.py escucha-pueblo/ 2>/dev/null
    cp -r "$SRC"/desarrollo/. desarrollo/ 2>/dev/null
    mkdir -p robot && cp "$SRC"/robot/*.ino robot/ 2>/dev/null
    cp "$SRC"/*.sh "$SRC"/*.py "$SRC"/LEEME.txt . 2>/dev/null
else
    echo "== Sin zip de version: subo solo el panel de esta Pi"
fi

# el panel de esta Pi: codigo e imagenes
mkdir -p panel-v11
rm -rf panel-v11/partes
cp -r ~/panel-v11/partes panel-v11/
cp ~/panel-v11/panel.py ~/panel-v11/panel_run.py ~/panel-v11/sonido_*.wav panel-v11/ 2>/dev/null
cp ~/panel-v11/fondo_*.jpg ~/panel-v11/logo_faccion.png ~/panel-v11/boton_*.png panel-v11/ 2>/dev/null
[ -d ~/naves ] && cp -r ~/naves .
[ -d ~/ingenieros ] && cp -r ~/ingenieros .
[ -n "$TMP" ] && rm -rf "$TMP"

# lo que NUNCA se sube (claves, ajustes y datos personales)
cat > .gitignore <<'EOS'
*clave*
*token*
*webhook*
*.log
*.log.1
*.bak*
__pycache__/
__cache__/
copias/
panel_ajustes.json
notas.json
viajes.json
naves.json
colonia.json
bonos_sin_cobrar.json
faccion_cache.json
faccion_estado.json
actividad_hoy.json
pc_ip.txt
avatares/
EOS
git rm -r -q --cached . >/dev/null 2>&1                  # solo dentro de v1.1/
git add -A .

# revision de seguridad: si algo parece una clave, no se sube
BAD=$(git diff --cached --name-only | grep -iE "clave|token|webhook|secret")
for f in ~/inara_clave.txt ~/github_token.txt ~/discord_webhook.txt ~/panel-v11/inara_clave.txt ~/panel-v11/github_token.txt; do
    if [ -s "$f" ]; then
        v=$(head -c 200 "$f" | tr -d '\r\n ')
        [ -n "$v" ] && git diff --cached -U0 | grep -qF -- "$v" && BAD="$BAD contenido de $(basename "$f")"
    fi
done
if git diff --cached -U0 | grep -qE "ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|discord(app)?\.com/api/webhooks/"; then
    BAD="$BAD algo con forma de token o webhook"
fi
if [ -n "$BAD" ]; then
    echo "¡OJO! Iba a subirse: $BAD. Cancelado, no se ha subido nada."
    git reset -q; exit 1
fi

if git diff --cached --quiet; then
    echo "Nada nuevo que subir."; exit 0
fi
VER=$(grep -ho 'PANEL_VER = "v[^ "]*' panel-v11/partes/*.py | head -1 | cut -d'"' -f2)
git diff --cached --name-only | grep -qv "^v1.1/" && { echo "¡OJO! Se iba a cambiar algo fuera de v1.1/. Cancelado."; git reset -q; exit 1; }
echo "== Cambios:"; git diff --cached --stat | tail -3
git commit -q -m "Panel $VER · $(date '+%d/%m/%Y %H:%M')" || { echo "Fallo al hacer el commit (¿falta git config user.name / user.email?)"; exit 1; }
git push -q || { echo "Fallo al subir (¿token caducado? Haz un git push a mano en $REPO y escribe el token solo en la Pi)"; exit 1; }
if ! git rev-parse -q --verify "refs/tags/$VER" >/dev/null; then
    git tag "$VER" && git push -q origin "$VER"
fi
echo "Subido a GitHub: $VER"
