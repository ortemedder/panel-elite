#!/bin/bash
# Instala el «oído» del robot en la Pi (v1.1.9): Vosk, que pasa la voz a texto en español SIN internet,
# y su modelo pequeño (~40 MB). Solo hace falta una vez. Vale para la Pi 4 y la Pi 3 (en la Pi 3 contesta más lento).
# Uso: bash ~/instalar_oido_robot.sh
set -u
D="$HOME/panel-v11"
M="$D/vosk-es"
URL="https://alphacephei.com/vosk/models/vosk-model-small-es-0.42.zip"
[ -d "$D/partes" ] || { echo "No encuentro el panel v1.1 en $D"; exit 1; }

echo "== 1) Vosk para Python"
if sudo python3 -c "import vosk" 2>/dev/null; then
    echo "   ya estaba instalado"
else
    sudo pip3 install vosk --break-system-packages 2>/dev/null || sudo pip3 install vosk \
        || { echo "   No se ha podido instalar vosk (¿hay internet? ¿está pip3?  sudo apt install python3-pip)"; exit 1; }
fi

echo "== 2) Modelo de voz en español"
if [ -f "$M/am/final.mdl" ]; then
    echo "   ya estaba en $M"
else
    T=$(mktemp -d)
    (wget -q --show-progress -O "$T/m.zip" "$URL" || curl -L -o "$T/m.zip" "$URL") \
        || { echo "   No he podido descargar el modelo"; rm -rf "$T"; exit 1; }
    unzip -q "$T/m.zip" -d "$T" || { echo "   El zip del modelo está mal"; rm -rf "$T"; exit 1; }
    rm -rf "$M"
    mv "$T"/vosk-model-small-es-* "$M" && echo "   instalado en $M"
    rm -rf "$T"
fi

echo "== 3) Prueba"
sudo python3 -c "import vosk; vosk.SetLogLevel(-1); vosk.Model('$M'); print('   el modelo se carga bien')" \
    || { echo "   El modelo no se carga"; exit 1; }
sudo systemctl restart elite-panel
echo
echo "Listo. Toca la pantalla del robot (sin foto), espera el pitido y pregunta, por ejemplo:"
echo "   ¿cuánto combustible queda?  ·  ¿cuántos saltos faltan?  ·  ¿qué hora es?  ·  ¿qué puedes hacer?"
echo "Lo que oye y contesta queda en ~/panel-v11/panel.log (líneas «ROBOT oye»)."
