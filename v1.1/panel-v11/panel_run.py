#!/usr/bin/env python3
# Arranque del panel v1.1: importa panel.py, que carga las partes de partes/.
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import panel
panel.main()
