import importlib.util, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy"); os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import capturar as C
def cargar(panel):
    sys.argv = [panel]
    spec = importlib.util.spec_from_file_location("panel", panel)
    P = importlib.util.module_from_spec(spec); spec.loader.exec_module(P)
    pg = P.pygame; pg.init(); P.load_fonts()
    P.fac_watch = lambda now: None
    P.time.time = lambda: C.T0
    C.fijar(P)
    return P
