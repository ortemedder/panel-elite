#!/usr/bin/env python3
# Parche v0.99: voz con Piper (carpeta piper/ junto a panel.py; si no esta, espeak-ng) con las frases guardadas,
# y el modo COMBATE de la pantalla grande en nave solo con las armas sacadas.
import re, shutil, sys, time
P = sys.argv[1] if len(sys.argv) > 1 else "/home/ortem/panel.py"
s = open(P, encoding="utf-8").read()
if "def piper_ok" in s:
    sys.exit("Ya estaba aplicado")
if 'PANEL_VER = "v0.98' not in s:
    sys.exit("Este parche es para la v0.98b")
shutil.copy(P, P + ".bak98b")

def rep(old, new):
    global s
    if old not in s:
        sys.exit("No encuentro: " + old[:70])
    s = s.replace(old, new, 1)

# COMBATE en nave: solo con las armas sacadas (no por el escaner ni justo tras escanear o lanzar drones)
rep('''    if not f2 & 1 and time.time() - fight["t"] < FIGHT_SECS:''',
    '''    if not f2 & 1 and hp_out(d, flags) and time.time() - fight["t"] < FIGHT_SECS:''')
rep('''    if d.get("target") or (flags & 64 and not flags & (1 << 27) and time.time() - (d.get("scan_t") or 0) > 20):''',
    '''    if hp_out(d, flags):''')

CODE = r'''
# ---------- v0.99: voz con Piper y combate solo con armas fuera ----------
def hp_out(d, flags):
    """Armas sacadas de verdad (no el escaner en modo analisis ni justo despues de escanear o lanzar drones)."""
    return bool(flags & 64) and not flags & (1 << 27) and time.time() - ((d or {}).get("scan_t") or 0) > 20

PIPER_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "piper")
PIPER_BIN = os.path.join(PIPER_DIR, "piper", "piper")
PIPER_MODEL = os.path.join(PIPER_DIR, "es.onnx")
PIPER_PRE = ["TE ATACAN", "ESCUDOS CAÍDOS", "ESCUDOS ARRIBA", "Voz de la nave activada"]

def piper_ok():
    return os.path.exists(PIPER_BIN) and os.path.exists(PIPER_MODEL)

def _piper_wav(t, low=False):
    d = os.path.join(PIPER_DIR, "cache")
    os.makedirs(d, exist_ok=True)
    f = os.path.join(d, hashlib.md5(t.encode("utf-8")).hexdigest()[:16] + ".wav")
    if not os.path.exists(f):
        cmd = (["nice", "-n", "19"] if low else []) + [PIPER_BIN, "--model", PIPER_MODEL, "--output_file", f + ".tmp"]
        subprocess.run(cmd, input=t.encode("utf-8"), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)
        os.replace(f + ".tmp", f)
    return f

def _piper_play(t):
    try:
        f = _piper_wav(t)
        voice["proc"] = subprocess.Popen(["aplay", "-q", f], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        log_exc("voz piper", e)
    finally:
        voice["busy"] = False

def _piper_pre():
    time.sleep(30)                                   # tras el arranque, sin prisa
    for t in PIPER_PRE:
        try:
            _piper_wav(t, low=True)
        except Exception:
            pass

_voice_ok0 = voice_ok

def voice_ok():
    return piper_ok() or _voice_ok0()

_voice_say0 = voice_say

def voice_say(text):
    if not cfg.get("voice") or not piper_ok():
        return _voice_say0(text)
    t = re.sub(r"[¡!¿?>|·_]", " ", text or "")
    t = re.sub(r"\s+", " ", t).strip(" .")
    if not t or time.time() - voice["last"].get(t, 0) < 30:
        return
    p_ = voice["proc"]
    if voice.get("busy") or (p_ and p_.poll() is None):
        return
    voice["last"][t] = time.time()
    voice["busy"] = True
    threading.Thread(target=_piper_play, args=(t,), daemon=True).start()

if piper_ok():
    threading.Thread(target=_piper_pre, daemon=True).start()

'''
rep("\ndef render(surf):", CODE + "\ndef render(surf):")
rep('''# Enlace energético''', '''# Novedades v0.99
- VOZ con Piper (voz natural): carpeta piper/ junto a panel.py con piper/piper y es.onnx. Las frases ya dichas se guardan en piper/cache y suenan al momento. Si no está Piper, se usa espeak-ng.
- La pantalla grande solo pasa a COMBATE en nave con las armas sacadas; al guardarlas se quita (los avisos siguen saliendo).
# Enlace energético''')
rep('    ("0.98b", "La HDMI táctil siempre responde; toques al LOG"),\n',
    '    ("0.98b", "La HDMI táctil siempre responde; toques al LOG"),\n'
    '    ("0.99", "Voz con Piper y COMBATE solo con las armas sacadas"),\n')
s = re.sub(r'PANEL_VER = "v0\.98[^"]*"', 'PANEL_VER = "v0.99 · ' + time.strftime("%d/%m/%Y %H:%M") + '"', s)
open(P, "w", encoding="utf-8").write(s)
print("OK v0.99  (copia en " + P + ".bak98b)")
