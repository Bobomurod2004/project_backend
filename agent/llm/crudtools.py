"""
CRUD taklif tool'lari — korxona uchun.

MUHIM: bu tool'lar DB'ga HECH NARSA YOZMAYDI. Ular faqat foydalanuvchiga
ko'rsatiladigan "taklif" (proposal) qaytaradi. Haqiqiy yozish/o'zgartirish/
o'chirish foydalanuvchi frontend'da tasdiqlaganidan keyin, mavjud Django
API orqali amalga oshadi.

Bu — "human-in-the-loop" yondashuvi: agent hech qachon to'g'ridan-to'g'ri
o'zgartirmaydi, faqat taklif qiladi.
"""

from llm.datatools import _get, _unpack


def _korxona_topish(args: dict) -> dict | None:
    """korxona_id yoki nomi/inn bo'yicha korxonani topadi."""
    kid = args.get("korxona_id")
    nomi = (args.get("nomi") or "").strip().lower()
    inn = (args.get("inn") or "").strip()

    _, results = _unpack(_get("/korxonalar/"))

    if kid:
        for k in results:
            if k["id"] == kid:
                return k
    if inn:
        for k in results:
            if k.get("inn") == inn:
                return k
    if nomi:
        for k in results:
            if nomi in (k.get("nomi") or "").lower():
                return k
    return None


# ── Create ───────────────────────────────────────────────────────────────────

def korxona_yaratish_taklifi(args: dict) -> dict:
    """Yangi korxona qo'shish taklifi. Majburiy: nomi, inn."""
    nomi = (args.get("nomi") or "").strip()
    inn = (args.get("inn") or "").strip()

    kerak = []
    if not nomi:
        kerak.append("nomi")
    if not inn:
        kerak.append("inn")
    if kerak:
        return {
            "ok": False,
            "kerak": kerak,
            "xabar": (
                "Korxona qo'shish uchun majburiy maydonlar yetishmayapti. "
                "Foydalanuvchidan so'rang: " + ", ".join(kerak)
            ),
        }

    # Qo'shimcha maydonlar
    extra = {}
    for f in ("manzil", "rahbar", "telefon", "email"):
        v = (args.get(f) or "").strip()
        if v:
            extra[f] = v

    # HIMOYA: shu INN bilan korxona allaqachon bormi?
    # Bir xil INN bilan create MUMKIN EMAS (INN unikal). Demak bu
    # aslida tahrirlash — avtomatik update taklifiga aylantiramiz.
    mavjud = _korxona_topish({"inn": inn})
    if mavjud:
        if extra:
            return {
                "ok": True,
                "proposal": {
                    "type": "korxona_update",
                    "label": f"'{mavjud['nomi']}' ni tahrirlash",
                    "target_id": mavjud["id"],
                    "current": {
                        "nomi": mavjud.get("nomi"),
                        "inn": mavjud.get("inn"),
                        "telefon": mavjud.get("telefon"),
                    },
                    "data": extra,
                },
                "xabar": (
                    f"'{mavjud['nomi']}' korxonasi (INN {inn}) allaqachon "
                    "mavjud — yangi qo'shish o'rniga TAHRIRLASH taklif "
                    "qilindi."
                ),
            }
        return {
            "ok": False,
            "xabar": (
                f"'{mavjud['nomi']}' korxonasi (INN {inn}) allaqachon "
                "mavjud. Qayta qo'shish shart emas."
            ),
        }

    data = {"nomi": nomi, "inn": inn, **extra}
    return {
        "ok": True,
        "proposal": {
            "type": "korxona_create",
            "label": "Yangi korxona qo'shish",
            "data": data,
        },
        "xabar": (
            f"'{nomi}' korxonasini qo'shishni taklif qildim. "
            "Foydalanuvchi tasdiqlashi kerak."
        ),
    }


# ── Update ───────────────────────────────────────────────────────────────────

def korxona_tahrirlash_taklifi(args: dict) -> dict:
    """Mavjud korxonani tahrirlash taklifi."""
    korxona = _korxona_topish(args)
    if korxona is None:
        return {
            "ok": False,
            "xabar": "Bunday korxona topilmadi. Avval korxonalar "
                     "ro'yxatini tekshiring.",
        }

    # O'zgartiriladigan maydonlar
    changes = {}
    for f in ("nomi", "inn", "manzil", "rahbar", "telefon", "email"):
        # nomi/inn — qidiruv uchun ham ishlatiladi, faqat 'yangi_' prefiks
        # bilan kelganlarni o'zgarish deb qabul qilamiz
        yangi = args.get(f"yangi_{f}")
        if yangi is not None and str(yangi).strip():
            changes[f] = str(yangi).strip()
    if "is_active" in args:
        changes["is_active"] = bool(args["is_active"])

    if not changes:
        return {
            "ok": False,
            "xabar": "Qaysi maydonni o'zgartirishni aniqlang "
                     "(masalan yangi_nomi, yangi_telefon).",
        }

    return {
        "ok": True,
        "proposal": {
            "type": "korxona_update",
            "label": f"'{korxona['nomi']}' ni tahrirlash",
            "target_id": korxona["id"],
            "current": {
                "nomi": korxona.get("nomi"),
                "inn": korxona.get("inn"),
                "telefon": korxona.get("telefon"),
            },
            "data": changes,
        },
        "xabar": "Tahrirlash taklifi tayyor. Foydalanuvchi tasdiqlashi kerak.",
    }


# ── Delete ───────────────────────────────────────────────────────────────────

def korxona_ochirish_taklifi(args: dict) -> dict:
    """Korxonani o'chirish taklifi (qaytarib bo'lmaydi)."""
    korxona = _korxona_topish(args)
    if korxona is None:
        return {
            "ok": False,
            "xabar": "Bunday korxona topilmadi.",
        }

    return {
        "ok": True,
        "proposal": {
            "type": "korxona_delete",
            "label": f"'{korxona['nomi']}' ni o'chirish",
            "target_id": korxona["id"],
            "data": {
                "nomi": korxona.get("nomi"),
                "inn": korxona.get("inn"),
            },
        },
        "xabar": "O'chirish taklifi tayyor. DIQQAT: bu amal qaytarib "
                 "bo'lmaydi. Foydalanuvchi tasdiqlashi kerak.",
    }


# ── Tool schemas ─────────────────────────────────────────────────────────────

CRUD_TOOLS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "korxona_yaratish_taklifi",
            "description": (
                "FAQAT YANGI korxona qo'shish uchun. Foydalanuvchi "
                "'yangi korxona qo'sh' desa ishlat. Majburiy: nomi va "
                "inn. DIQQAT: mavjud korxonaga telefon/manzil/email "
                "QO'SHISH yoki o'zgartirish YANGI qo'shish EMAS — buning "
                "uchun korxona_tahrirlash_taklifi ishlat."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "nomi": {"type": "string", "description": "Korxona nomi"},
                    "inn": {"type": "string", "description": "INN (unikal)"},
                    "manzil": {"type": "string"},
                    "rahbar": {"type": "string"},
                    "telefon": {"type": "string"},
                    "email": {"type": "string"},
                },
                "required": ["nomi", "inn"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "korxona_tahrirlash_taklifi",
            "description": (
                "MAVJUD korxonani tahrirlash uchun. 'Termiz korxonasiga "
                "telefon qo'sh', 'manzilini o'zgartir', 'nomini "
                "yangila' kabi so'rovlarda ishlat. Korxonani topish "
                "uchun nomi yoki inn bering. O'zgarishlar yangi_ "
                "prefiksi bilan: yangi_telefon, yangi_manzil, yangi_nomi."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "korxona_id": {"type": "integer"},
                    "nomi": {"type": "string"},
                    "inn": {"type": "string"},
                    "yangi_nomi": {"type": "string"},
                    "yangi_inn": {"type": "string"},
                    "yangi_manzil": {"type": "string"},
                    "yangi_rahbar": {"type": "string"},
                    "yangi_telefon": {"type": "string"},
                    "yangi_email": {"type": "string"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "korxona_ochirish_taklifi",
            "description": (
                "Korxonani o'chirish TAKLIFINI tayyorlaydi (qaytarib "
                "bo'lmaydi). korxona_id yoki nomi/inn bering."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "korxona_id": {"type": "integer"},
                    "nomi": {"type": "string"},
                    "inn": {"type": "string"},
                },
            },
        },
    },
]

CRUD_HANDLERS = {
    "korxona_yaratish_taklifi": korxona_yaratish_taklifi,
    "korxona_tahrirlash_taklifi": korxona_tahrirlash_taklifi,
    "korxona_ochirish_taklifi": korxona_ochirish_taklifi,
}
