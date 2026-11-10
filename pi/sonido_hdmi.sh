#!/bin/bash
# Saca el sonido (avisos y voz) por la HDMI que tiene la pantalla conectada. Guarda copia de /etc/asound.conf.
# Uso:   bash ~/sonido_hdmi.sh
CARDS=$(aplay -l 2>/dev/null | grep -o 'vc4hdmi[0-9]*' | sort -u)
[ -z "$CARDS" ] && { echo "No hay salida de sonido HDMI (vc4hdmi)"; exit 1; }
CARD=""
if [ "$(echo "$CARDS" | wc -l)" = 1 ]; then
    CARD=$CARDS
else
    for i in 1 2; do
        st=$(cat /sys/class/drm/card*-HDMI-A-$i/status 2>/dev/null | head -1)
        if [ "$st" = "connected" ]; then CARD="vc4hdmi$((i - 1))"; break; fi
    done
fi
[ -z "$CARD" ] && { echo "No veo ninguna pantalla conectada por HDMI"; exit 1; }
[ -f /etc/asound.conf ] && sudo cp /etc/asound.conf "/etc/asound.conf.bak$(date +%Y%m%d%H%M)"
printf 'pcm.!default {\n  type plug\n  slave.pcm "hw:%s,0"\n}\nctl.!default {\n  type hw\n  card "%s"\n}\n' "$CARD" "$CARD" | sudo tee /etc/asound.conf >/dev/null
echo "Sonido por $CARD. Prueba:  speaker-test -c2 -t wav -l1"
