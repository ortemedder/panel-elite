#!/bin/bash
# Cambia el panel que arranca: la b20 de siempre (tu carpeta personal) o la v1.1 (~/panel-v11).
# Uso: bash ~/cambiar_panel.sh v11      ·      bash ~/cambiar_panel.sh b20      ·      bash ~/cambiar_panel.sh   (dice cual esta)
set -u
DROP=/etc/systemd/system/elite-panel.service.d
CONF=$DROP/zz-panel-v11.conf      # "zz": se aplica despues de rapido.conf y fb.conf
sudo rm -f $DROP/panel-v11.conf 2>/dev/null     # nombre antiguo (lo tapaba rapido.conf)
case "${1:-}" in
    v11)
        [ -f "$HOME/panel-v11/panel_run.py" ] || { echo "No esta instalada la v1.1 (bash instalar_v11.sh)"; exit 1; }
        sudo mkdir -p "$DROP"
        printf '[Service]\nExecStart=\nExecStart=/usr/bin/python3 %s/panel-v11/panel_run.py\nWorkingDirectory=%s/panel-v11\n' "$HOME" "$HOME" | sudo tee "$CONF" >/dev/null
        sudo systemctl daemon-reload && sudo systemctl restart elite-panel && echo "Arrancado el panel v1.1. Log: ~/panel-v11/panel.log"
        ;;
    b20)
        sudo rm -f "$CONF"
        sudo systemctl daemon-reload && sudo systemctl restart elite-panel && echo "Arrancado el panel de siempre (b20). Log: ~/panel.log"
        ;;
    *)
        if [ -f "$CONF" ]; then echo "Ahora arranca: v1.1"; else echo "Ahora arranca: el de siempre (b20)"; fi
        ;;
esac
