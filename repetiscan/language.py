import json
import os
import sys

def load_translations():
    if getattr(sys, 'frozen', False):
        # PyInstaller: el archivo está junto al ejecutable en _MEIPASS
        base_path = sys._MEIPASS
        lang_path = os.path.join(base_path, "lang.json")
    else:
        # Ejecución normal: el archivo está en el proyecto, un nivel arriba
        base_path = os.path.abspath(os.path.dirname(__file__))
        lang_path = os.path.join(base_path, "../lang.json")
    with open(lang_path, "r", encoding="utf-8") as f:
        return json.load(f)

def t(key, lang="es", translations=None):
    if translations is None:
        return key
    return translations.get(lang, {}).get(key, key)
