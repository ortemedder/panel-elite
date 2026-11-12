#!/bin/bash
# Prueba de sonido del Panel Elite v1.1 (vale para la Pi de Ortem y la de KORZO):
# 1) la musica de inicio, 2) la voz de la nave (Piper si esta, si no espeak-ng), 3) los tres pitidos de los avisos.
# Uso: bash ~/prueba_sonido.sh
D="$HOME/panel-v11"
echo "== Salida de audio:"; aplay -l 2>/dev/null | grep -m3 "^card" || echo "   (no veo tarjetas de sonido)"

echo "== 1) Musica de inicio"
if [ -f "$D/sonido_inicio.wav" ]; then aplay -q "$D/sonido_inicio.wav" && echo "   OK"
else echo "   FALTA $D/sonido_inicio.wav (instala la v1.1 con actualizar_v11.sh)"; fi

echo "== 2) Voz de la nave"
TXT="Panel Elite, versión uno punto uno, en línea. Prueba de voz correcta, comandante."
P="$D/piper"
if [ -x "$P/piper/piper" ] && [ -f "$P/es.onnx" ]; then
    echo "$TXT" | "$P/piper/piper" --model "$P/es.onnx" --output_file /tmp/prueba_voz.wav 2>/dev/null \
        && aplay -q /tmp/prueba_voz.wav && echo "   OK (Piper)" || echo "   Piper ha fallado"
    rm -f /tmp/prueba_voz.wav
elif command -v espeak-ng >/dev/null; then
    espeak-ng -v es -s 150 -a 130 --stdout "$TXT" | aplay -q && echo "   OK (espeak-ng; Piper no está en $P)" || echo "   espeak-ng no ha podido sonar"
else
    echo "   Sin voz: no está Piper en $P ni espeak-ng (sudo apt install espeak-ng)"
fi

echo "== 3) Pitidos de los avisos (alarma, salto, ok)"
n=0; hay=0
for f in /tmp/panel_alarma.wav /tmp/panel_salto.wav /tmp/panel_ok.wav; do
    [ -f "$f" ] || continue
    hay=$((hay+1))
    aplay -q "$f" && n=$((n+1)) && sleep 0.3
done
if [ $hay -eq 0 ]; then echo "   No están (los crea el panel al arrancar)"
elif [ $n -gt 0 ]; then echo "   OK ($n de 3)"
else echo "   No han podido sonar"; fi
if [ $n -eq 0 ]; then
    echo
    echo "== El audio por defecto no funciona. Prueba cada salida (con altavoces o cascos conectados):"
    for c in $(aplay -l 2>/dev/null | sed -n 's/^card \([0-9]*\):.*/\1/p' | sort -u); do
        nom=$(aplay -l | sed -n "s/^card $c: \([^ ]*\).*/\1/p" | head -1)
        if aplay -q -D plughw:$c,0 /tmp/panel_ok.wav 2>/dev/null || aplay -q -D plughw:$c,0 "$D/sonido_inicio.wav" 2>/dev/null; then
            echo "   card $c ($nom): SUENA  ->  para usarla siempre:  printf 'defaults.pcm.card $c\\ndefaults.ctl.card $c\\n' | sudo tee /etc/asound.conf"
        else
            echo "   card $c ($nom): no se puede abrir"
        fi
    done
fi
echo
echo "Si no se oye nada: revisa el volumen con  alsamixer  y que el panel tenga SONIDO activado en 12 AJUSTES > OPCIONES."
