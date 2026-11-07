#!/usr/bin/env python3
# Arranque rapido del panel: importa panel.py (Python guarda la traduccion en __pycache__ y no la repite).
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import panel
panel.main()
