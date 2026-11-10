#!/bin/bash
# Sube TODO el proyecto a GitHub (ortemedder/panel-elite): el panel de esta Pi y el contenido del zip de la version
# (parches, scripts, imagenes, los dos senders y el escucha del pueblo). Lo personal y las claves no se suben nunca.
# Uso:   bash ~/subir_todo.sh                      (busca el panel_v*.zip mas nuevo en tu carpeta personal)
#        bash ~/subir_todo.sh ~/panel_v1.0b19b.zip (o el zip / carpeta que le digas)
set -u
REPO=~/panel-elite
URL=https://github.com/ortemedder/panel-elite
SRC="${1:-}"

# 1) el repositorio en la Pi
if [ ! -d "$REPO/.git" ]; then
    echo "== No hay copia del repositorio en $REPO: la descargo"
    git clone -q "$URL" "$REPO" || { echo "No he podido clonar $URL"; exit 1; }
fi
cd "$REPO" || exit 1
git pull -q --rebase 2>/dev/null

# 2) el zip (o carpeta) de la version
TMP=""
if [ -z "$SRC" ]; then
    SRC=$(ls -t ~/panel_v*.zip 2>/dev/null | head -1)
fi
if [ -n "$SRC" ] && [ -f "$SRC" ]; then
    TMP=$(mktemp -d)
    unzip -q "$SRC" -d "$TMP" || { echo "No puedo abrir $SRC"; exit 1; }
    SRC=$(find "$TMP" -mindepth 1 -maxdepth 1 -type d | head -1)
fi
if [ -n "$SRC" ] && [ -d "$SRC" ]; then
    echo "== Version: $(basename "$SRC")"
    mkdir -p pi pc_ortem pc_korzo escucha-pueblo
    cp -r "$SRC"/pi/. pi/ 2>/dev/null
    cp "$SRC"/pc_ortem/*.py pc_ortem/ 2>/dev/null
    cp "$SRC"/pc_korzo/*.py pc_korzo/ 2>/dev/null
    cp "$SRC"/escucha-pueblo/*.py escucha-pueblo/ 2>/dev/null
    cp "$SRC"/LEEME.txt . 2>/dev/null
else
    echo "== Sin zip de version: subo solo lo de esta Pi (copia panel_v*.zip a tu carpeta para subirlo todo)"
fi

# 3) lo de esta Pi
cp ~/panel.py .
cp ~/panel_run.py ~/instalar.sh ~/backup_panel.sh ~/subir_github.sh ~/subir_todo.sh . 2>/dev/null
cp ~/fondo_*.jpg ~/logo_faccion.png ~/boton_*.png . 2>/dev/null
[ -d ~/naves ] && cp -r ~/naves .
[ -d ~/ingenieros ] && cp -r ~/ingenieros .
[ -f ~/manual.html ] && cp ~/manual.html .
[ -n "$TMP" ] && rm -rf "$TMP"

# 4) lo que NUNCA se sube (claves, ajustes y datos personales)
cat > .gitignore <<'EOS'
*clave*
*token*
*webhook*
*.log
*.log.1
*.bak*
__pycache__/
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
git rm -r -q --cached . >/dev/null 2>&1
git add -A

# 5) revision de seguridad: si algo parece una clave, no se sube
BAD=$(git diff --cached --name-only | grep -iE "clave|token|webhook|secret")
for f in ~/inara_clave.txt ~/github_token.txt ~/discord_webhook.txt; do
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
VER=$(grep -m1 -o 'PANEL_VER = "v[^ "]*' panel.py | cut -d'"' -f2)
echo "== Cambios:"; git diff --cached --stat | tail -3
git commit -q -m "Panel $VER · $(date '+%d/%m/%Y %H:%M') · todo el proyecto" || { echo "Fallo al hacer el commit (¿falta git config user.name / user.email?)"; exit 1; }
git push -q || { echo "Fallo al subir (¿token caducado? Haz un git push a mano en $REPO y escribe el token solo en la Pi)"; exit 1; }
if ! git rev-parse -q --verify "refs/tags/$VER" >/dev/null; then
    git tag "$VER" && git push -q origin "$VER"
fi
echo "Subido a GitHub: $VER (todo el proyecto)"
