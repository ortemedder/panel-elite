# Panel Elite v1.1 · parte 00: inicio y menus (lineas 1-371 del panel entero)
#!/usr/bin/env python3
# Panel tactil Elite Dangerous - Raspberry Pi 3 / 4, pantalla pequena y/o HDMI
import os, glob, json, socket, threading, time, queue, hashlib, base64, math, shutil, subprocess, wave, struct, bisect
from collections import deque
os.environ["SDL_VIDEODRIVER"] = "dummy"
import pygame
import numpy as np
PANEL_DIR = os.path.dirname(os.path.abspath(__file__))

UDP_PORT = 5005
W, H = 480, 320
SWAP_XY, INV_X, INV_Y = False, False, True   # ajustar si el tactil va cruzado
HOLD = 0.08                                     # segundos que se mantiene pulsada la tecla
CAL = os.environ.get("CAL") == "1"              # CAL=1 imprime coordenadas del tactil

# OBS (PC de streaming) - en OBS: Herramientas > Ajustes del servidor WebSocket
OBS_HOST = "192.168.0.XXX"   # <-- IP del PC de streaming
OBS_PORT = 4455
OBS_PASSWORD = ""            # <-- contrasena del servidor WebSocket de OBS
OBS_MIC = ""                 # nombre de la fuente del micro; vacio = el "Mic/Aux" de OBS

KEYS = {chr(c): 0x04 + i for i, c in enumerate(range(ord('a'), ord('z') + 1))}
KEYS.update({str(n): 0x1E + (n - 1) for n in range(1, 10)}); KEYS['0'] = 0x27
KEYS.update({'.': 0x37, 'Insert': 0x49, 'Home': 0x4A, 'PageUp': 0x4B, 'Delete': 0x4C, 'End': 0x4D,
             'PageDown': 0x4E, 'Tab': 0x2B, 'Space': 0x2C, 'Enter': 0x28, 'Esc': 0x29})
KEYS.update({f'F{i}': 0x3A + i - 1 for i in range(1, 13)})
KEYS.update({f'KP{n}': 0x59 + n - 1 for n in range(1, 10)}); KEYS['KP0'] = 0x62
MODS = {'Ctrl': 0x01, 'Shift': 0x02, 'Alt': 0x04, 'AltGr': 0x40}
KEYS.update({'-': 0x2D, '=': 0x2E, '[': 0x2F, ']': 0x30, '\\': 0x31, ';': 0x33, "'": 0x34, '`': 0x35, ',': 0x36,
             '/': 0x38, 'Backspace': 0x2A, 'Right': 0x4F, 'Left': 0x50, 'Down': 0x51, 'Up': 0x52, 'KPDiv': 0x54,
             'KPMul': 0x55, 'KPSub': 0x56, 'KPAdd': 0x57, 'KPEnter': 0x58, 'KPDec': 0x63})

def key_ok(k):
    *mods, kk = (k or "").split('+')
    return kk in KEYS and all(m in MODS for m in mods)

# ---------- contenido de los menus ----------
MENU = {1: "MANDOS", 2: "PIPS", 3: "NAVEGACIÓN", 4: "CARGA/MISIÓN", 5: "SRV / RHINO / A PIE", 6: "COMBATE", 7: "EXPLORACIÓN",
        8: "ESTACIÓN", 9: "CAZA", 10: "MINERÍA", 11: "RESUMEN DEL DÍA", 12: "LOG / STREAM", 121: "LOG", 122: "STREAM",
        71: "EXPLORACIÓN", 72: "SISTEMA", 73: "EXOBIOLOGÍA", 74: "YACIMIENTOS", 75: "DIARIO DE EXPLORACIÓN", 76: "ALIENÍGENAS", 100: "EN VIVO", 61: "REGISTRO DE COMBATE", 125: "MATERIALES", 126: "PORTANAVES", 127: "MERCADO", 1244: "PREFERENCIAS", 1245: "VERSIONES", 128: "NOTAS DE VIAJE", 129: "NOTA"}
MENU.update({123: "RANGOS", 124: "AJUSTES"})
PARENT = {0: 100, 71: 7, 72: 7, 73: 7, 74: 7, 75: 7, 76: 7, 121: 12, 122: 12, 123: 12, 124: 12, 1244: 124, 1245: 124, 125: 12, 126: 12, 127: 12, 128: 12, 129: 128}
CMDR_NAME = "ORTEM ED DER"

# Menu 1 - (texto, tecla, bit de Flags o None)
BUTTONS = [
    ("TREN", ".", 2), ("LUCES", "l", 8), ("VISIÓN NOC", "n", 28), ("RECOGEDOR", "c", 9),
    ("SUPERCRUC.", "m", 4), ("SILENCIO", "Shift+y", 10), ("DISIPADOR", "e", None), ("CHAFF", "Shift+r", None),
    ("SALTO FSD", "h", 17), ("ESCUDO", "Shift+e", None), ("MAPA GAL", "g", None), ("MAPA SIS", "s", None),
]
# Menu 2 - pips
PIP_COLS = [("SISTEMAS", "y"), ("MOTORES", "u"), ("ARMAS", "i")]
PIP_PRESETS = [("RESET", ["j"]), ("MAX SIS", ["j", "y", "y", "y", "y"]),
               ("MAX MOT", ["j", "u", "u", "u", "u"]), ("MAX ARM", ["j", "i", "i", "i", "i"])]
# Menu 5 - (texto, tecla, bit de Flags o None)
SRV_BTNS = [("FAROS", "l", 8), ("TORRETA", "t", 13), ("RECOGER", "c", 9),
            ("NAVE", "h", None), ("MAPA GAL", "g", None), ("MAPA SIS", "s", None)]
PIE_BTNS = [("LINTERNA", "l", None), ("VISIÓN NOC", "n", None), ("ESCUDO", "c", None),
            ("BOTIQUÍN", "F1", None), ("BATERÍA", "F2", None), ("RECARGAR", "r", None)]

# Menu 6 - combate (texto, tecla)
COMBAT_BTNS = [("OBJETIVO", "Shift+f"), ("SIGUIENTE", "Shift+q"), ("ANTERIOR", "Shift+w"), ("PELIGROSO", "Shift+p"),
               ("SU OBJ.", "0"), ("SUBSIST.", "Shift+a"), ("ALA 1", "7"), ("ALA 2", "8"),
               ("ALA 3", "9"), ("CHAFF", "Shift+r"), ("DISIPADOR", "e"), ("ESCUDO", "Shift+e")]
# Menu 9 - ordenes del caza (texto, tecla, grupo: los del mismo grupo se excluyen)
FIGHTER_BTNS = [("DEFENSIVO", "KP1", "b"), ("AGRESIVO", "KP2", "b"), ("ATACAR", "KP3", "a"), ("ALTO FUEGO", "KP4", "a"),
                ("POSICIÓN", "KP5", "m"), ("SEGUIRME", "KP6", "m"), ("VOLVER", "KP0", "m"), ("ÓRDENES", "KP7", None)]

ALERTS = [(20, "SOBRECALENTADO"), (23, "INTERDICCION"), (22, "PELIGRO"), (19, "COMBUSTIBLE BAJO"), (16, "MASS LOCK")]
SCOOPABLE = set("KGBFOAM")

ORANGE = (255, 140, 0); DIM = (120, 66, 0); BLACK = (0, 0, 0); RED = (230, 40, 30)
WHITE = (230, 230, 230); BLUE = (90, 170, 255); GREEN = (90, 220, 120)

state = {"data": None, "rx": 0.0, "log": deque(maxlen=300)}
ui = {"view": 100, "pause": False, "tab4": 0, "page4": 0, "orders": {}, "page7": 0, "confirm": (None, 0),
      "start": time.time(), "idle_skip": 0, "idle_on": False, "note_seq": None, "gui": 0, "alert": None}

# ---------- ajustes (se guardan en la Pi) ----------
SETTINGS_FILE = os.path.join(PANEL_DIR, "panel_ajustes.json")
THEMES = [("NARANJA", (255, 140, 0)), ("AZUL", (80, 160, 255)), ("VERDE", (60, 220, 110)),
          ("MORADO", (190, 110, 255)), ("ROJO", (255, 80, 60)), ("BLANCO", (225, 225, 225))]
cfg = {"sharp": True, "auto": True, "alerts": True, "sound": True, "theme": 0, "cmdr": CMDR_NAME}

def load_cfg():
    try:
        cfg.update(json.load(open(SETTINGS_FILE)))
    except Exception:
        pass
    apply_theme()

def save_cfg():
    try:
        json.dump(cfg, open(SETTINGS_FILE, "w"))
    except Exception as e:
        print("No guardo ajustes:", e)

def apply_theme():
    global ORANGE, DIM
    ORANGE = THEMES[cfg["theme"] % len(THEMES)][1]
    DIM = tuple(c * 47 // 100 for c in ORANGE)

# ---------- sonidos ----------
SOUNDS = {}

def make_sounds():
    def tone(path, parts):
        import os as _os
        if _os.path.exists(path) and _os.path.getsize(path) > 1000:
            return
        with wave.open(path, "w") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(22050)
            frames = b""
            for f0, f1, dur in parts:
                n = int(22050 * dur)
                for k in range(n):
                    f = f0 + (f1 - f0) * k / n
                    env = min(1, k / 300, (n - k) / 300)
                    frames += struct.pack("<h", int(9000 * env * math.sin(2 * math.pi * f * k / 22050)))
            w.writeframes(frames)
    try:
        SOUNDS["alarm"] = "/tmp/panel_alarma.wav"; tone(SOUNDS["alarm"], [(880, 880, .15), (0, 0, .05), (660, 660, .15)] * 2)
        SOUNDS["jump"] = "/tmp/panel_salto.wav"; tone(SOUNDS["jump"], [(200, 1200, 1.2)])
        SOUNDS["ok"] = "/tmp/panel_ok.wav"; tone(SOUNDS["ok"], [(660, 990, .18)])
    except Exception as e:
        print("Sin sonidos:", e)

def play(name):
    if XA_K[0] and (not ev_on(XA_K[0]) or not snd_on(XA_K[0])):
        return
    if cfg["sound"] and name in SOUNDS and shutil.which("aplay"):
        try:
            subprocess.Popen(["aplay", "-q", SOUNDS[name]], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except OSError:
            pass

# --- sonido al encender y al apagar el panel (sonido_inicio.wav junto a panel.py) ---
SND_INICIO = os.path.join(PANEL_DIR, "sonido_inicio.wav")

def play_inicio(wait=False):
    """Suena al arrancar y al SALIR / REINICIAR / APAGAR. Se quita en SONIDO Y VOZ > ENCENDER / APAGAR."""
    if not (cfg.get("sound", True) and ev_on("inicio") and snd_on("inicio")) or not os.path.exists(SND_INICIO) \
            or not shutil.which("aplay"):
        return
    try:
        p = subprocess.Popen(["aplay", "-q", SND_INICIO], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if wait:
            p.wait(timeout=9)
    except Exception:
        pass

# ---------- avisos: alertas y cambio automatico de menu ----------
AUTO_VIEW = {"embark": 100, "market": 127, "interdicted": 6, "underattack": 6, "docking": 8, "prospector": 10, "srv": 5, "foot": 100, "fighter": 9}

# avisos uno a uno: cfg["ev"][clave] = False lo apaga (lo que no esta en la lista sale siempre)
EV_LIST = [("jump", "SALTO"), ("interdicted", "INTERDICCIÓN"), ("underattack", "TE ATACAN"),
           ("shields_down", "ESCUDOS CAÍDOS"), ("shields_up", "ESCUDOS ARRIBA"), ("hull", "CASCO DAÑADO"),
           ("heat", "SOBRECALENTAMIENTO"), ("rebuy", "CASCO CRÍTICO"), ("died", "HAS CAÍDO / DESTRUIDA"),
           ("hplow", "SALUD BAJA (A PIE)"), ("oxy", "POCO OXÍGENO"), ("temp", "FRÍO / CALOR"),
           ("srvfuel", "COMBUSTIBLE SRV"), ("gravity", "GRAVEDAD ALTA"), ("fuelroute", "RUTA COMBUSTIBLE"),
           ("jetcone", "FSD SOBREALIMENT."), ("jetdmg", "DAÑO EN EL FSD"), ("arrive", "LLEGADA / SEÑAL"),
           ("newsys", "SIN EXPLORAR"), ("honk", "ESCANEO SISTEMA"), ("find", "HALLAZGO VALIOSO"),
           ("codex", "CÓDICE"), ("risk", "DATOS EN RIESGO"), ("matfull", "MATERIAL AL MÁX."),
           ("alien", "SEÑALES ALIEN"), ("tgwar", "GUERRA THARGOIDE"), ("shutdown", "APAGÓN THARGOIDE"),
           ("wanted", "OBJETIVO BUSCADO"), ("cmdrtarget", "CMDR FIJADO"), ("kill", "BAJA / DERRIBO"),
           ("escaped", "ESCAPADO"), ("submitted", "SOMETIDO"), ("crime", "DELITO"),
           ("dropship", "TRANSPORTE ZONA"), ("deploy", "DESPLEGADO"), ("thrown", "GRANADA LANZADA"),
           ("pickup", "RECOGIDO"), ("usecons", "CONSUMIBLE USADO"), ("lowcons", "QUEDAN POCOS"),
           ("redeem", "COBRADO"), ("opstart", "OPERACIÓN INICIADA"), ("opend", "OPERACIÓN TERMINADA"),
           ("missionexp", "MISIÓN CADUCA"), ("missionhere", "ENTREGA AQUÍ"), ("taxi", "TAXI"),
           ("settle", "ASENTAMIENTO"), ("sessend", "FIN DE SESIÓN"), ("friend", "AMIGOS"),
           ("wing", "ALA"), ("cg", "OBJ. COMUNITARIO"), ("galnet", "NOTICIA GALNET"), ("power", "BAJA TENSIÓN"),
           ("keys", "TECLAS SIN ASIGNAR"), ("elink", "RECARGA CON ENLACE"),
           ("thargmusic", "MÚSICA THARGOIDE"), ("shipswap", "CAMBIO DE NAVE"), ("shipxfer", "TRANSFERENCIA NAVE"),
           ("shiparrived", "NAVE TRANSFERIDA"), ("moddmg", "MÓDULOS DAÑADOS"),
           ("scanned", "TE ESCANEAN"), ("engbase", "BASE DE INGENIERO"), ("engsys", "INGENIERO EN EL SISTEMA"), ("opmega", "MEGA NAVE 15 MIN")]
# cambio automatico de menu uno a uno: cfg["autoev"][clave] = False
AUTO_LIST = [("docking", "ATRAQUE > ESTACIÓN"), ("market", "MERCADO"), ("interdicted", "INTERDICCIÓN > COMBATE"),
             ("underattack", "TE ATACAN > COMBATE"), ("arrsig", "SEÑAL PELIGROSA > COMBATE"),
             ("arrst", "LLEGADA > ESTACIÓN"), ("prospector", "PROSPECTOR > MINERÍA"), ("srv", "SRV"),
             ("fighter", "CAZA"), ("embark", "EMBARCAR > EN VIVO"), ("foot", "A PIE > EN VIVO"),
             ("fss", "FSS > SISTEMA"), ("combatmusic", "MÚSICA COMBATE > COMBATE"),
             ("ppmenu", "MENÚ POWERPLAY > POWERPLAY"), ("sqmenu", "MENÚ ESCUADRÓN > ESCUADRÓN")]
XA_K = [None]          # aviso que se esta procesando (para apagarlo y silenciarlo)

SND_DEF = {"kill": False}      # de entrada en silencio: bajas y derribos (con sus creditos)

def snd_on(k):
    return not k or (cfg.get("snd") or {}).get(k, SND_DEF.get(k, True))

def ev_on(k):
    return cfg.get("alerts", True) and (cfg.get("ev") or {}).get(k, True)

def auto_on(k):
    return cfg.get("auto", True) and (cfg.get("autoev") or {}).get(k, True)

def ev_migrate():
    # antes ALERTAS / CAMBIO AUTO eran un solo interruptor: si estaba apagado, se apagan todos
    for master, store, L in (("alerts", "ev", EV_LIST), ("auto", "autoev", AUTO_LIST), ("sound", "snd", EV_LIST)):
        if not cfg.get(master, True):
            cfg[store] = {k: False for k, _ in L}
            cfg[master] = True
            save_cfg()

class XaDict(dict):
    def __setitem__(self, k, v):
        if k == "a" and v is not None and XA_K[0] and not ev_on(XA_K[0]):
            return
        if k == "a" and isinstance(v, dict):
            v.setdefault("ev", XA_K[0])
        dict.__setitem__(self, k, v)

def set_alert(text, sub="", col=None, secs=3.0, kind="red"):
    ui["alert"] = {"text": text, "sub": sub, "col": col or RED, "until": time.time() + secs, "kind": kind,
                   "ev": XA_K[0] or (kind if kind in ("galnet",) else None)}

def _nota_base(kind, text):
    if kind == "combatmusic" and auto_on("combatmusic"):
        foot = (state.get("data") or {}).get("Flags2", 0) & 1
        if ui["view"] not in ((100, 150) if foot else (6, 61)):
            ui["view"] = 100 if foot else 6
    elif kind == "ppmenu" and auto_on("ppmenu"):
        ui["view"] = 3; ui["navtab"] = 2
    elif kind == "sqmenu" and auto_on("sqmenu"):
        ui["view"] = 165; ui["sqpage"] = 0
    elif kind == "mainmenu":
        ui["view"] = 100; ui["idle_skip"] = 0
    elif kind == "loadgame":
        track.update(body=None, pts=[], kills=[], items=[], last=None, raw=None, fast=False)
    if kind in AUTO_VIEW and auto_on(kind):
        ui["view"] = AUTO_VIEW[kind]
        if kind in ("underattack", "interdicted") and ((state.get("data") or {}).get("Flags2", 0) & 1):
            ui["view"] = 100
    if not ev_on(kind):
        return
    if kind == "jump":
        sysname, cls = (text.split("|") + [""])[:2]
        set_alert("SALTO AL HIPERESPACIO", f"> {sysname}" + (f"  (estrella {cls})" if cls else ""), BLUE, 45, "jump")
        play("jump")
    elif kind == "jumpend":
        if ui["alert"] and ui["alert"]["kind"] == "jump":
            ui["alert"] = None
    elif kind == "interdicted":
        nm_, pl_ = ((text or "") + "|0").split("|")[:2]
        set_alert("¡INTERDICCIÓN!", (nm_ + ("  ·  ¡COMANDANTE!" if pl_ == "1" else "  ·  NPC")) if nm_ else "", secs=6 if pl_ == "1" else 4)
        play("alarm")
    elif kind == "underattack":
        set_alert("¡TE ATACAN!", "", secs=2); play("alarm")
    elif kind == "shields_down":
        set_alert("ESCUDOS CAÍDOS", "", secs=3); play("alarm")
    elif kind == "shields_up":
        set_alert("ESCUDOS ARRIBA", "", GREEN, 1.5, "ok"); play("ok")
    elif kind == "hull":
        set_alert(f"CASCO {text}%", "", secs=3); play("alarm")
    elif kind == "heat":
        set_alert("SOBRECALENTAMIENTO", "", secs=3); play("alarm")

FIGHT_SECS = 60
fight = {"t": 0.0}
FIGHT_KINDS = ("underattack", "shields_down", "kill", "deploy", "interdicted", "hull", "combatmusic")

def in_fight(d, now=None):
    return bool(d) and bool(d.get("Flags2", 0) & 1) and (now or time.time()) - fight["t"] < FIGHT_SECS

def process_notes(d):
    notes = d.get("notes") or []
    top = max([n[0] for n in notes], default=0)
    if ui["note_seq"] is None or top < ui["note_seq"]:     # arranque o sender reiniciado
        ui["note_seq"] = top
    for seq, kind, text in notes:
        if seq > ui["note_seq"]:
            ui["note_seq"] = seq
            if (kind in FIGHT_KINDS and not (kind == "hull" and star_kind(d.get("curstar")) in ("neu", "wd"))) or \
                    (kind == "scanned" and (text or "").split("|")[3:4] == ["0"]):
                fight["t"] = time.time()
            battle_note(kind, text, d)
            if kind == "kill":
                track_kill()
            if kind == "pickup":
                nm_ = (text.split("|") + [""])[0]
                track_item(ITEM_KIND.get(nm_, "gren"))
            if kind == "deploy":                       # el mapa empieza al bajar del transporte
                track.update(pts=[], kills=[], items=[], last=None)
            XA_K[0] = kind
            try:
                handle_note(kind, text)
            finally:
                XA_K[0] = None
    gui = d.get("gui", 0)
    if gui == 9 and ui["gui"] != 9 and auto_on("fss"):          # FSS abierto
        ui["view"] = 72
    ui["gui"] = gui
    cm = (d.get("ranks") or {}).get("cmdr")
    if cm and cm.upper() != cfg.get("cmdr"):
        cfg["cmdr"] = cm.upper(); save_cfg()
flash = {}
lock = threading.Lock()

# ---------- framebuffer ----------
ROT = False

def find_fb():
    global ROT
    cands = []
    for p in sorted(glob.glob('/sys/class/graphics/fb*')):
        try:
            name = open(p + '/name').read().strip()
            w, h = map(int, open(p + '/virtual_size').read().strip().split(','))
            bpp = int(open(p + '/bits_per_pixel').read())
            stride = int(open(p + '/stride').read())
        except Exception:
            continue
        print("Encontrado", p, name, w, h, bpp)
        cands.append((name, w, h, bpp, stride, '/dev/' + os.path.basename(p)))
    for name, w, h, bpp, stride, dev in cands:
        if 'vc4' not in name.lower() and (min(w, h) == min(W, H) or 'ili' in name.lower() or 'piscreen' in name.lower()):
            ROT = w == 320
            return dev, bpp, stride
    return '/dev/null', 16, W * 2   # sin pantalla pequena: solo la HDMI

_FB16 = {}

def to_fb_bytes(surf, bpp, stride):
    if ROT:
        surf = pygame.transform.rotate(surf, 90)
    if bpp == 16:
        w_, h_ = surf.get_size()
        t = _FB16.get((w_, h_))
        if t is None:
            t = _FB16[(w_, h_)] = pygame.Surface((w_, h_), 0, 16, (0xF800, 0x07E0, 0x001F, 0))
        t.blit(surf, (0, 0))
        raw, pitch = t.get_buffer().raw, t.get_pitch()
        if pitch != stride:
            n = min(pitch, stride)
            raw = b"".join(raw[y * pitch:y * pitch + n].ljust(stride, b"\0") for y in range(h_))
        return raw
    a = pygame.surfarray.array3d(surf).swapaxes(0, 1)
    hh, ww = a.shape[:2]
    if bpp == 16:
        r = (a[:, :, 0].astype(np.uint16) >> 3) << 11
        g = (a[:, :, 1].astype(np.uint16) >> 2) << 5
        b = a[:, :, 2].astype(np.uint16) >> 3
        px = np.ascontiguousarray(r | g | b).view(np.uint8).reshape(hh, ww * 2)
    else:
        alpha = np.full(a.shape[:2] + (1,), 255, np.uint8)
        px = np.concatenate([a[:, :, 2:3], a[:, :, 1:2], a[:, :, 0:1], alpha], axis=2).reshape(hh, ww * 4)
    if stride > px.shape[1]:
        px = np.pad(px, ((0, 0), (0, stride - px.shape[1])))
    return px.tobytes()

# ---------- teclado USB ----------
hid_lock = threading.Lock()

def _press(f, key):
    *mods, k = key.split('+')
    code, mod = KEYS[k], sum(MODS[m] for m in mods)
    f.write(bytes([mod, 0, 0, 0, 0, 0, 0, 0])); time.sleep(0.02)
    f.write(bytes([mod, 0, code, 0, 0, 0, 0, 0])); time.sleep(HOLD)
    f.write(bytes([mod, 0, 0, 0, 0, 0, 0, 0])); f.write(bytes(8))

def press_seq(keys):
    if not all(key_ok(k) for k in keys):
        set_alert("SIN TECLA EN EL JUEGO", "mira AJUSTES > OPCIONES > TECLAS", ORANGE, 3)
        return
    if not hid_ok():
        pc = pc_addr()
        if not pc:
            set_alert("NO SÉ LA IP DEL PC", "el sender no está enviando", RED, 3)
            return
        try:
            so = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            so.sendto(("ELITEPANEL-KEYS|" + ",".join(keys)).encode(), (pc, 5006))
            so.close()
        except OSError as e:
            print("Error teclas por red:", e)
        return
    def run():
        with hid_lock:
            try:
                with open('/dev/hidg0', 'wb', buffering=0) as f:
                    for k in keys:
                        _press(f, k); time.sleep(0.12)
            except OSError as e:
                print("Error HID:", e)
    threading.Thread(target=run, daemon=True).start()

