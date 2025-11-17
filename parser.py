import io
import re
import requests
import pdfplumber
from bs4 import BeautifulSoup
import urllib3

# отключаем предупреждения SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

NUM_RE = re.compile(r"([0-9\s,.]+)\s*(млн|млрд|тыс)?", re.IGNORECASE)
LABEL_RE = re.compile(r"(Нормативн[а-я]+|Нарматыўн[а-я]+)\s+капитал", re.IGNORECASE)
DATE_RE = re.compile(r"(?:на|по состоянию на)\s+([0-9]{1,2}\s+[А-Яа-яA-Za-zЁё]+(?:\s+20[0-9]{2})?)", re.IGNORECASE)


def _mult(word: str | None) -> float:
    if not word:
        return 1.0
    w = word.lower()
    if "млрд" in w:
        return 1_000_000_000
    if "млн" in w:
        return 1_000_000
    if "тыс" in w:
        return 1_000
    return 1.0


def _extract_value(text: str) -> tuple[float | None, str | None]:
    match = NUM_RE.search(text)
    if not match:
        return None, None
    num_str = match.group(1).replace(" ", "").replace("\u00A0", "")
    try:
        val = float(num_str.replace(",", "."))
    except:
        return None, None
    val *= _mult(match.group(2))
    return val, match.group(0)


def _extract_from_text(text: str) -> tuple[float | None, str | None, str | None]:
    value = None
    raw = None
    as_of = None
    for line in text.split("\n"):
        if LABEL_RE.search(line):
            v, r = _extract_value(line)
            if v is not None:
                value = v
                raw = r
            d = DATE_RE.search(line)
            if d:
                as_of = d.group(1)
            if value is not None:
                break
    return value, raw, as_of


def _extract_from_pdf(pdf_bytes: bytes) -> tuple[float | None, str | None, str | None]:
    value = None
    raw = None
    as_of = None
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                text = page.extract_text() or ""
                v, r, d = _extract_from_text(text)
                if v is not None:
                    value = v
                    raw = r
                    if d:
                        as_of = d
                    break
    except Exception:
        # на случай повреждённого PDF
        pass
    return value, raw, as_of


def get_bank_metrics(bank_name: str, bank_info: dict) -> dict:
    url = bank_info.get("disclosure_url")
    if not url:
        return {
            "bank": bank_name,
            "value_byn": None,
            "raw_value": None,
            "as_of": None,
            "source": None,
            "error": "Не задан URL"
        }

    headers = {"User-Agent": "Mozilla/5.0 (compatible; CapitalBot/1.0)"}

    try:
        resp = requests.get(url, headers=headers, timeout=40, verify=False)
        resp.raise_for_status()
        content_type = resp.headers.get("Content-Type", "").lower()

        # Определяем PDF или HTML
        if "application/pdf" in content_type or url.lower().endswith(".pdf"):
            value, raw, as_of = _extract_from_pdf(resp.content)
        else:
            soup = BeautifulSoup(resp.content, "html.parser")
            text = soup.get_text(separator="\n")
            value, raw, as_of = _extract_from_text(text)

        if value is None:
            return {
                "bank": bank_name,
                "value_byn": None,
                "raw_value": None,
                "as_of": as_of,
                "source": url,
                "error": "Нормативный капитал не найден"
            }

        return {
            "bank": bank_name,
            "value_byn": value,
            "raw_value": raw,
            "as_of": as_of,
            "source": url
        }

    except requests.exceptions.RequestException as e:
        return {
            "bank": bank_name,
            "value_byn": None,
            "raw_value": None,
            "as_of": None,
            "source": url,
            "error": f"Ошибка сети/SSL: {e}"
        }
    except Exception as e:
        return {
            "bank": bank_name,
            "value_byn": None,
            "raw_value": None,
            "as_of": None,
            "source": url,
            "error": f"Не удалось обработать документ: {e}"
        }
