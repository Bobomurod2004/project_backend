"""
Ma'lumot tool'lari — Django REST API'dan platforma ma'lumotlarini o'qiydi.
Bu tool'lar yordamida agent korxona/hisobotlarni sanaydi, ro'yxatlaydi
va tekshira oladi.
"""

import httpx
from config import DJANGO_API

_TIMEOUT = 10


def _get(path: str, params: dict | None = None) -> dict:
    """Django API'ga GET so'rovi. DRF pagination'ni hisobga oladi."""
    url = f"{DJANGO_API}{path}"
    resp = httpx.get(url, params=params or {}, timeout=_TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def _unpack(data) -> tuple[int, list]:
    """DRF javobidan (count, results) ajratadi."""
    if isinstance(data, dict) and "results" in data:
        return data.get("count", len(data["results"])), data["results"]
    if isinstance(data, list):
        return len(data), data
    return 0, []


# ── Korxonalar ────────────────────────────────────────────────────────────────

def korxonalar_royxati(args: dict) -> dict:
    """Barcha korxonalar soni va ro'yxati."""
    data = _get("/korxonalar/")
    count, results = _unpack(data)
    korxonalar = [
        {
            "id": k["id"],
            "nomi": k.get("nomi"),
            "inn": k.get("inn"),
            "faol": k.get("is_active", True),
        }
        for k in results
    ]
    return {"soni": count, "korxonalar": korxonalar}


# ── Hisobotlar ────────────────────────────────────────────────────────────────

def hisobotlar_royxati(args: dict) -> dict:
    """Hisobotlar soni va ro'yxati. Ixtiyoriy: yil, korxona_id filtri."""
    params = {}
    if args.get("yil"):
        params["yil"] = args["yil"]
    if args.get("korxona_id"):
        params["korxona"] = args["korxona_id"]

    data = _get("/hisobotlar/", params)
    count, results = _unpack(data)
    hisobotlar = [
        {
            "id": h["id"],
            "korxona": h.get("korxona_nomi"),
            "yil": h.get("yil"),
            "oy": h.get("oy_nomi"),
        }
        for h in results
    ]
    return {"soni": count, "hisobotlar": hisobotlar}


# ── Platforma statistikasi ────────────────────────────────────────────────────

def platforma_statistikasi(args: dict) -> dict:
    """Umumiy ko'rsatkichlar: korxonalar va hisobotlar soni."""
    k_count, _ = _unpack(_get("/korxonalar/"))
    h_count, _ = _unpack(_get("/hisobotlar/"))
    return {
        "korxonalar_soni": k_count,
        "hisobotlar_soni": h_count,
    }


# ── Tool schemas ──────────────────────────────────────────────────────────────

DATA_TOOLS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "korxonalar_royxati",
            "description": (
                "Platformadagi barcha korxonalar sonini va ro'yxatini "
                "qaytaradi. Foydalanuvchi 'nechta korxona bor', "
                "'korxonalar ro'yxati', 'qaysi korxonalar bor' deb "
                "so'raganda ishlat."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "hisobotlar_royxati",
            "description": (
                "Hisobotlar sonini va ro'yxatini qaytaradi. "
                "Foydalanuvchi 'nechta hisobot bor', 'hisobotlar "
                "ro'yxati' deb so'raganda ishlat. Ixtiyoriy filtrlar: "
                "yil (masalan 2025), korxona_id."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "yil": {
                        "type": "integer",
                        "description": "Yil bo'yicha filtr (ixtiyoriy)",
                    },
                    "korxona_id": {
                        "type": "integer",
                        "description": "Korxona ID bo'yicha filtr (ixtiyoriy)",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "platforma_statistikasi",
            "description": (
                "Platformaning umumiy ko'rsatkichlari: korxonalar va "
                "hisobotlar umumiy soni. 'Umumiy statistika', 'nechta "
                "narsa bor' kabi savollarga javob berishda ishlat."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
]

DATA_HANDLERS = {
    "korxonalar_royxati": korxonalar_royxati,
    "hisobotlar_royxati": hisobotlar_royxati,
    "platforma_statistikasi": platforma_statistikasi,
}
