from __future__ import annotations

import datetime as dt
import io
import random
import string
from typing import Any, Dict

import qrcode
from django.http import HttpRequest
from qrcode.image.svg import SvgPathImage


PREFIX_MAP = {
    "announcement": "ANNOUNCEMENT",
    "announcements": "ANNOUNCEMENT",
    "report": "REPORT CARD",
    "reportcard": "REPORT CARD",
    "receipt": "RECEIPT",
    "invoice": "INVOICE",
    "certificate": "CERTIFICATE",
    "payslip": "PAYSLIP",
    "admission": "ADMISSION",
    "broadsheet": "BROADSHEET",
    "attendance": "ATTENDANCE REPORT",
    "profile": "STUDENT PROFILE",
    "student": "STUDENT PROFILE",
}


def generate_document_reference(prefix: str, *, length: int = 8) -> str:
    """Generate a reusable document reference with a prefix and a short unique suffix."""
    prefix_key = (prefix or "document").strip().upper().replace(" ", "")
    date_part = dt.datetime.now().strftime("%Y%m%d")
    suffix = "".join(random.choices(string.digits, k=length))
    return f"{prefix_key}-{date_part}-{suffix}"


def resolve_document_prefix(request: HttpRequest | None, fallback: str = "document") -> str:
    """Infer a reusable document prefix from the request path when possible."""
    if not request:
        return fallback

    path = request.path.lower()
    for keyword, prefix in PREFIX_MAP.items():
        if f"/{keyword}/" in path or path.startswith(f"/{keyword}") or path.endswith(f"/{keyword}"):
            return prefix

    return fallback.upper()


def build_document_verification(request: HttpRequest | None, *, prefix: str | None = None, title: str | None = None) -> Dict[str, Any]:
    """Build the shared verification payload for printable documents."""
    document_url = request.build_absolute_uri(request.get_full_path()) if request else ""
    qr_image = qrcode.make(document_url or "", image_factory=SvgPathImage)
    buffer = io.BytesIO()
    qr_image.save(buffer)
    qr_svg = buffer.getvalue().decode("utf-8")

    resolved_prefix = prefix or resolve_document_prefix(request)

    return {
        "enabled": True,
        "reference": generate_document_reference(resolved_prefix),
        "document_url": document_url,
        "title": title or "Document",
        "qr_svg": qr_svg,
        "verification_text": "Scan this QR Code to verify this document online.",
    }
