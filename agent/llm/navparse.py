"""
Fallback navigatsiya parseri.

Ba'zi modellar (ayniqsa coder modellar) navigate tool'ni haqiqiy
tool_call sifatida emas, matn ichida yozib yuboradi, masalan:
    navigate('/korxonalar')
    <navigate url="/korxonalar">
    ```html\n<navigate url="/korxonalar"/>\n```

Bu modul shunday matnlarni topib:
  1. path'ni ajratib oladi
  2. matnni shu kodlardan tozalaydi
"""

import re
from llm.tools import PAGES, resolve_page

# Foydalanuvchi xabaridagi "harakat" fe'llari (navigatsiya niyati).
# DIQQAT: yolg'iz "bor" qo'shilmagan — u "mavjud" ma'nosini ham beradi
# ("nechta korxona bor" = navigatsiya emas, savol).
_NAV_CUE = re.compile(
    r"(\bo['‘’]?t\w*"
    r"|\bqayt\w*"
    r"|\bko['‘’]?rsat\w*"
    r"|\boch(ib|gin|ing|\b)"
    r"|olib\s+bor\w*|olib\s+kel\w*"
    r"|\bboshla\w*"
    r"|\bbor(gin|ing|aylik|amiz|aman)"      # borgin, boraylik (bare "bor" emas)
    r"|\bkel(gin|ing))",                    # kelgin (bare "kel" emas)
    re.IGNORECASE,
)

# Inkor — "o'tma", "ketmagin", "kerak emas". Bunda navigatsiya qilmaymiz.
_NEGATION = re.compile(
    r"(o['‘’]?t\w*ma\w*"        # o'tma, o'tmagin, o'tmang
    r"|ketma\w*"               # ketma, ketmagin
    r"|borma\w*"               # borma, bormagin
    r"|qaytma\w*"              # qaytma
    r"|kerak\s+emas"
    r"|shart\s+emas"
    r"|hojati\s+yo['‘’]?q"
    r"|\bemas\b)",
    re.IGNORECASE,
)

# Bosh sahifa uchun qo'shimcha iboralar
_HOME_HINTS = ("bosh sahifa", "asosiy sahifa", "bosh menyu")


def detect_user_navigation(text: str) -> dict | None:
    """
    Foydalanuvchi xabaridan to'g'ridan-to'g'ri navigatsiya niyatini aniqlaydi.
    Masalan: "korxonalar sahifasiga o't" -> {path: "/korxonalar", ...}
    "korxonalar haqida gapir" -> None (harakat fe'li yo'q)
    "nechta korxona bor" -> None ("bor" = mavjud, savol)
    "korxonalarga o'tma" -> None (inkor)
    """
    t = (text or "").lower()
    if not t.strip():
        return None

    # Inkor bo'lsa — navigatsiya qilmaymiz
    if _NEGATION.search(t):
        return None

    # Harakat fe'li bormi?
    if not _NAV_CUE.search(t):
        return None

    # Bosh sahifa iboralari
    if any(h in t for h in _HOME_HINTS):
        return resolve_page("/")

    # Sahifa kalit so'zlari bo'yicha
    for p in PAGES:
        if any(kw in t for kw in p["keywords"]):
            return p

    # "bosh"/"asosiy" yolg'iz kelsa
    if "bosh" in t or "asosiy" in t:
        return resolve_page("/")

    return None


# navigate('/path')  yoki  navigate("/path")
_RE_FUNC = re.compile(
    r"""navigate\s*\(\s*['"]([^'"]+)['"]\s*\)""", re.I
)

# <navigate url="/path">  yoki  <navigate url='/path' />
_RE_TAG = re.compile(
    r"""<\s*navigate\s+url\s*=\s*['"]([^'"]+)['"]\s*/?\s*>""", re.I
)

# ```...``` kod bloklari (tozalash uchun)
_RE_CODEBLOCK = re.compile(r"```[a-zA-Z]*\s*([\s\S]*?)```")


def extract_navigation(text: str) -> tuple[str, dict | None]:
    """
    Returns: (cleaned_text, page_or_none)
    page: {"path": ..., "label": ...} yoki None
    """
    if not text:
        return text, None

    found_path = None

    # 1) navigate('/path')
    m = _RE_FUNC.search(text)
    if m:
        found_path = m.group(1)

    # 2) <navigate url="/path">
    if not found_path:
        m = _RE_TAG.search(text)
        if m:
            found_path = m.group(1)

    if not found_path:
        return text, None

    page = resolve_page(found_path)
    if page is None:
        return text, None

    # Matnni navigatsiya kodlaridan tozalaymiz
    cleaned = _RE_FUNC.sub("", text)
    cleaned = _RE_TAG.sub("", cleaned)

    # Bo'sh qolgan kod bloklarini olib tashlaymiz
    def _strip_empty_block(match):
        inner = match.group(1).strip()
        return "" if not inner else match.group(0)

    cleaned = _RE_CODEBLOCK.sub(_strip_empty_block, cleaned)

    # Ortiqcha bo'sh qatorlarni yig'amiz
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()

    return cleaned, page
