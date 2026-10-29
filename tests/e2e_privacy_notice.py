"""Verifica o bloqueio de primeiro uso: só libera após rolar até o fim e confirmar."""
import os
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
PORT = 8797
BASE = f"http://127.0.0.1:{PORT}"
DATA = Path('/tmp/mc-privacy-notice')
shutil.rmtree(DATA, ignore_errors=True)
srv = subprocess.Popen([sys.executable, str(ROOT / 'tests' / 'dev_server.py'), '--port', str(PORT), '--data', str(DATA), '--site', str(ROOT / 'site')], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
try:
    for _ in range(50):
        try:
            urllib.request.urlopen(BASE + '/', timeout=1)
            break
        except Exception:
            time.sleep(.1)
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH') or None)
        ctx = browser.new_context(viewport={'width': 390, 'height': 844})
        page = ctx.new_page()
        page.goto(BASE)
        gate = page.locator('#privacy-gate')
        gate.wait_for(state='visible')
        assert page.locator('#privacy-read-check').is_disabled()
        assert page.locator('#privacy-continue').is_disabled()
        # tentar fechar pelo Escape não pode dispensar o aviso
        page.keyboard.press('Escape')
        assert gate.is_visible()
        page.locator('#privacy-content').evaluate('(el) => { el.scrollTop = el.scrollHeight; el.dispatchEvent(new Event("scroll")); }')
        page.wait_for_function("!document.querySelector('#privacy-read-check').disabled")
        page.locator('#privacy-read-check').check()
        assert not page.locator('#privacy-continue').is_disabled()
        page.locator('#privacy-continue').click()
        gate.wait_for(state='hidden')
        assert page.evaluate("localStorage.getItem('mc_privacy_ack_v1')") == 'accepted'
        print('OK: aviso bloqueia a primeira abertura até o final e a confirmação.')
        browser.close()
finally:
    srv.terminate()
    srv.wait(timeout=5)
