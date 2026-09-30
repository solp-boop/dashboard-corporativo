"""Lectura de la fuente de datos, sin lógica de negocio.

Dos implementaciones con la misma interfaz:

- GoogleSheetsSource: producción. Usa gspread con una service account.
  Lee todo en 2 llamadas por planilla: una para los encabezados y otra
  (batch) solo con las columnas que el dashboard necesita.
- LocalExcelSource: desarrollo y tests. Lee un .xlsx exportado de la planilla.

Los valores se devuelven "crudos" (UNFORMATTED_VALUE + fechas como número de
serie), así no dependemos del formato regional con que se muestra la planilla.
"""
from __future__ import annotations

import datetime as dt
from typing import Protocol

from utils.data_cleaning import fold
from utils.logger import get_logger

log = get_logger("sheets")

Grid = list[list]  # filas x columnas; la fila 0 son los encabezados


class SourceError(RuntimeError):
    """Error de conexión o lectura con un mensaje apto para el usuario."""


class SheetSource(Protocol):
    name: str

    def tab_titles(self, book: str) -> list[str]: ...

    def read_headers(self, book: str, tabs: list[str]) -> dict[str, list]: ...

    def read_tables(self, book: str, request: dict[str, list[int] | None]) -> dict[str, Grid]: ...

    def last_modified(self, book: str) -> dt.datetime | None: ...


def find_tab(titles: list[str], wanted: str) -> str | None:
    """Busca una solapa ignorando mayúsculas, acentos y espacios."""
    key = fold(wanted)
    for t in titles:
        if fold(t) == key:
            return t
    # Excel recorta los nombres de solapa a 31 caracteres (exportes locales).
    for t in titles:
        if len(t) == 31 and key.startswith(fold(t)):
            return t
    return None


def col_letter(idx: int) -> str:
    """0 -> A, 25 -> Z, 26 -> AA."""
    s, n = "", idx + 1
    while n:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


def _pad(rows: list[list], width: int) -> Grid:
    return [list(r) + [None] * (width - len(r)) for r in rows]


# ---------------------------------------------------------------------------
class GoogleSheetsSource:
    name = "Google Sheets"
    SCOPES = [
        "https://www.googleapis.com/auth/spreadsheets.readonly",
        "https://www.googleapis.com/auth/drive.metadata.readonly",
    ]
    RENDER = {"valueRenderOption": "UNFORMATTED_VALUE", "dateTimeRenderOption": "SERIAL_NUMBER"}

    def __init__(self, credentials_info: dict, books: dict[str, str]):
        import gspread  # import diferido: los tests locales no lo necesitan

        self._gspread = gspread
        try:
            self._client = gspread.service_account_from_dict(dict(credentials_info), scopes=self.SCOPES)
        except Exception as exc:  # credenciales mal formadas
            log.exception("Credenciales inválidas")
            raise SourceError(
                "Las credenciales de Google (service account) no son válidas. Revisá secrets.toml."
            ) from exc
        self._books_ids = books
        self._books: dict = {}

    def _book(self, book: str):
        if book not in self._books:
            sid = self._books_ids.get(book)
            if not sid:
                raise SourceError(f"No hay ID configurado para la planilla '{book}'.")
            try:
                self._books[book] = self._client.open_by_key(sid)
            except self._gspread.exceptions.SpreadsheetNotFound as exc:
                raise SourceError(
                    f"No se pudo abrir la planilla '{book}'. Verificá que esté compartida con la "
                    "cuenta de servicio (lector)."
                ) from exc
            except self._gspread.exceptions.APIError as exc:
                log.exception("APIError abriendo %s", book)
                raise SourceError(f"Google rechazó el acceso a la planilla '{book}' ({exc.response.status_code}).") from exc
            except Exception as exc:
                log.exception("Error de conexión abriendo %s", book)
                raise SourceError(f"No se pudo conectar con Google Sheets ({type(exc).__name__}).") from exc
        return self._books[book]

    def tab_titles(self, book: str) -> list[str]:
        return [ws.title for ws in self._book(book).worksheets()]

    def read_headers(self, book: str, tabs: list[str]) -> dict[str, list]:
        if not tabs:
            return {}
        ranges = [f"'{t}'!1:1" for t in tabs]
        resp = self._book(book).values_batch_get(ranges, params=self.RENDER)
        out = {}
        for tab, vr in zip(tabs, resp.get("valueRanges", [])):
            vals = vr.get("values", [[]])
            out[tab] = vals[0] if vals else []
        return out

    def read_tables(self, book: str, request: dict[str, list[int] | None]) -> dict[str, Grid]:
        ranges, owners = [], []
        for tab, cols in request.items():
            if cols is None:
                ranges.append(f"'{tab}'")
                owners.append((tab, None))
            else:
                for c in cols:
                    L = col_letter(c)
                    ranges.append(f"'{tab}'!{L}:{L}")
                    owners.append((tab, c))
        if not ranges:
            return {}
        resp = self._book(book).values_batch_get(
            ranges, params={**self.RENDER, "majorDimension": "ROWS"}
        )
        value_ranges = resp.get("valueRanges", [])
        whole: dict[str, Grid] = {}
        columns: dict[str, dict[int, list]] = {}
        for (tab, c), vr in zip(owners, value_ranges):
            vals = vr.get("values", [])
            if c is None:
                width = max((len(r) for r in vals), default=0)
                whole[tab] = _pad(vals, width)
            else:
                columns.setdefault(tab, {})[c] = [r[0] if r else None for r in vals]
        for tab, cols in columns.items():
            length = max((len(v) for v in cols.values()), default=0)
            order = request[tab] or []
            max_idx = max(order) if order else -1
            grid = [[None] * (max_idx + 1) for _ in range(length)]
            for c, vals in cols.items():
                for i, v in enumerate(vals):
                    grid[i][c] = v
            whole[tab] = grid
        return whole

    def last_modified(self, book: str) -> dt.datetime | None:
        try:
            raw = self._book(book).get_lastUpdateTime()
            return dt.datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        except Exception:  # requiere scope de Drive; es opcional
            log.info("No se pudo leer la fecha de modificación de %s", book)
            return None


# ---------------------------------------------------------------------------
class LocalExcelSource:
    """Lee uno o más .xlsx exportados de las planillas (desarrollo y tests)."""

    name = "Archivo local"

    def __init__(self, paths: dict[str, str]):
        self._paths = paths
        self._cache: dict[tuple[str, str], Grid] = {}
        self._titles: dict[str, list[str]] = {}

    def _path(self, book: str) -> str:
        import os

        path = self._paths.get(book)
        if not path:
            raise SourceError(f"No hay archivo local configurado para la planilla '{book}'.")
        if not os.path.exists(path):
            raise SourceError(f"No se encontró el archivo local {path}.")
        return path

    def tab_titles(self, book: str) -> list[str]:
        if book not in self._titles:
            import pandas as pd

            with pd.ExcelFile(self._path(book), engine=_excel_engine()) as xf:
                self._titles[book] = list(xf.sheet_names)
        return self._titles[book]

    def _grid(self, book: str, tab: str) -> Grid:
        key = (book, tab)
        if key not in self._cache:
            import pandas as pd

            df = pd.read_excel(self._path(book), sheet_name=tab, header=None, dtype=object,
                               engine=_excel_engine())
            df = df.astype(object).where(df.notna(), None)
            self._cache[key] = df.values.tolist()
        return self._cache[key]

    def read_headers(self, book: str, tabs: list[str]) -> dict[str, list]:
        return {t: (self._grid(book, t)[0] if self._grid(book, t) else []) for t in tabs}

    def read_tables(self, book: str, request: dict[str, list[int] | None]) -> dict[str, Grid]:
        return {t: self._grid(book, t) for t in request}

    def last_modified(self, book: str) -> dt.datetime | None:
        import os

        path = self._paths.get(book)
        if path and os.path.exists(path):
            return dt.datetime.fromtimestamp(os.path.getmtime(path), tz=dt.timezone.utc)
        return None


def _excel_engine() -> str:
    try:
        import python_calamine  # noqa: F401  (mucho más rápido que openpyxl)

        return "calamine"
    except ImportError:
        return "openpyxl"


# ---------------------------------------------------------------------------
class PublicCsvSource:
    """Lee las solapas por su exportación CSV pública (sin credenciales).

    Es el mismo acceso que usa hoy la app: requiere que la planilla esté
    compartida como "Cualquier persona con el enlace puede ver". Cada solapa se
    identifica por su gid (el número que aparece en la URL al abrirla).
    Las descargas se hacen en paralelo y una sola vez por ciclo de caché.
    """

    name = "Google Sheets (enlace público)"
    URL = "https://docs.google.com/spreadsheets/d/{sid}/export?format=csv&gid={gid}"
    TIMEOUT = 30

    def __init__(self, books: dict[str, str], gids: dict[str, dict[str, int]]):
        self._books = books
        self._gids = gids
        self._cache: dict[tuple[str, str], Grid] = {}

    # Separado para poder simularlo en los tests.
    def _download(self, url: str) -> str:
        import urllib.error
        import urllib.request

        req = urllib.request.Request(url, headers={"User-Agent": "dashboard-comex"})
        try:
            with urllib.request.urlopen(req, timeout=self.TIMEOUT) as resp:
                ctype = resp.headers.get("Content-Type", "")
                body = resp.read().decode("utf-8-sig", errors="replace")
        except urllib.error.HTTPError as exc:
            if exc.code in (401, 403, 404):
                raise SourceError(
                    "Google rechazó la descarga de la planilla. Verificá que esté compartida como "
                    "«Cualquier persona con el enlace» o configurá una cuenta de servicio (ver README)."
                ) from exc
            raise SourceError(f"Google Sheets respondió con error {exc.code}. Probá de nuevo en unos minutos.") from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise SourceError("No se pudo conectar con Google Sheets. Revisá la conexión e intentá de nuevo.") from exc
        if "text/html" in ctype or body.lstrip().lower().startswith("<!doctype html"):
            raise SourceError(
                "Google devolvió una página de inicio de sesión en lugar de datos: la planilla no es "
                "pública. Compartila como «Cualquier persona con el enlace» o configurá una cuenta de servicio."
            )
        return body

    def _fetch(self, book: str, tab: str) -> Grid:
        import csv
        import io

        key = (book, tab)
        if key not in self._cache:
            sid = self._books.get(book)
            gid = self._gids.get(book, {}).get(tab)
            if not sid or gid is None:
                raise SourceError(f"Falta el ID o el gid de la solapa '{tab}' en config/settings.py.")
            text = self._download(self.URL.format(sid=sid, gid=gid))
            rows = list(csv.reader(io.StringIO(text)))
            width = max((len(r) for r in rows), default=0)
            self._cache[key] = _pad(rows, width)
        return self._cache[key]

    def _prefetch(self, book: str, tabs: list[str]) -> None:
        from concurrent.futures import ThreadPoolExecutor

        pending = [t for t in tabs if (book, t) not in self._cache]
        if not pending:
            return
        with ThreadPoolExecutor(max_workers=min(6, len(pending))) as pool:
            list(pool.map(lambda t: self._fetch(book, t), pending))

    def tab_titles(self, book: str) -> list[str]:
        if book not in self._books:
            raise SourceError(f"No hay ID configurado para la planilla '{book}'.")
        return list(self._gids.get(book, {}))

    def read_headers(self, book: str, tabs: list[str]) -> dict[str, list]:
        self._prefetch(book, tabs)
        return {t: (self._fetch(book, t)[0] if self._fetch(book, t) else []) for t in tabs}

    def read_tables(self, book: str, request: dict[str, list[int] | None]) -> dict[str, Grid]:
        self._prefetch(book, list(request))
        return {t: self._fetch(book, t) for t in request}

    def last_modified(self, book: str) -> dt.datetime | None:
        return None  # la exportación pública no informa la fecha de edición
