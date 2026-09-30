"""Abre el dashboard para que Streamlit Community Cloud no lo ponga a dormir.

Si la app ya está dormida, aprieta el botón para despertarla.
Lo ejecuta .github/workflows/keep-awake.yml cada pocas horas.
Las URLs se configuran en la variable de entorno APP_URLS (separadas por coma).
"""
import os
import sys

from playwright.sync_api import sync_playwright

URLS = [u.strip() for u in os.environ.get("APP_URLS", "").split(",") if u.strip()]
WAKE_TEXT = "Yes, get this app back up"


def visit(page, url: str) -> None:
    page.goto(url, wait_until="domcontentloaded", timeout=90_000)
    page.wait_for_timeout(8_000)
    button = page.get_by_role("button", name=WAKE_TEXT)
    if button.count():
        print(f"{url}: estaba dormida, despertando…")
        button.first.click()
        page.wait_for_timeout(60_000)
    else:
        print(f"{url}: activa")


def main() -> int:
    if not URLS:
        print("APP_URLS vacío: nada para hacer")
        return 0
    failures = 0
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        for url in URLS:
            try:
                visit(page, url)
            except Exception as exc:  # noqa: BLE001
                failures += 1
                print(f"{url}: error {type(exc).__name__}: {exc}")
        browser.close()
    return 1 if failures == len(URLS) else 0


if __name__ == "__main__":
    sys.exit(main())
