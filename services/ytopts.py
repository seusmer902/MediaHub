"""Opciones comunes de yt-dlp: runtime JS y cookies (necesarios para YouTube)."""
import shutil

from config import COOKIES_FILE


def js_runtimes():
    """None = usar el comportamiento por defecto (deno en el PATH)."""
    if shutil.which("deno"):
        return None
    try:
        import deno  # paquete de PyPI que trae el binario
        return {"deno": {"path": deno.find_deno_bin()}}
    except Exception:
        pass
    if shutil.which("node"):
        return {"node": {}}
    return None


def common_opts(cookies_browser: str = "") -> dict:
    opts = {}
    runtimes = js_runtimes()
    if runtimes:
        opts["js_runtimes"] = runtimes
    if COOKIES_FILE.exists():
        opts["cookiefile"] = str(COOKIES_FILE)
    elif cookies_browser and cookies_browser != "Ninguno":
        opts["cookiesfrombrowser"] = (cookies_browser.lower(),)
    return opts


BOT_HINT = (
    "YouTube pidió verificar que no eres un bot. Solución: en «Cookies» elige el navegador donde "
    "tengas sesión de YouTube iniciada (Firefox es el que mejor funciona; cierra Chrome/Edge si usas "
    "esos), o guarda un cookies.txt en la carpeta data/. Luego vuelve a analizar."
)
