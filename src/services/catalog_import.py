"""CSV catalog import service.

Allows merchants to upload product catalogs via CSV
(sent as a file attachment in WhatsApp/Telegram).
"""

import csv
import io
from dataclasses import dataclass

from src.services.product_service import ProductService


@dataclass
class ImportResult:
    success: bool
    imported: int
    skipped: int
    errors: list[str]


async def import_catalog_from_csv(
    csv_content: str,
    merchant_id: int,
    product_service: ProductService,
) -> ImportResult:
    """Parse a CSV string and import products into the merchant's catalog.

    Expected CSV format:
    name_ar,name,price,category,stock
    شاورما دجاج,Chicken Shawarma,25000,ساندويشات,50
    فلافل,Falafel,15000,ساندويشات,30

    Headers are auto-detected. Minimum required columns: name_ar, price
    """
    errors = []
    products_to_create = []

    try:
        reader = csv.DictReader(io.StringIO(csv_content))
    except Exception as e:
        return ImportResult(success=False, imported=0, skipped=0, errors=[f"Invalid CSV: {e}"])

    # Normalize header names
    header_aliases = {
        "الاسم": "name_ar",
        "اسم_عربي": "name_ar",
        "اسم": "name_ar",
        "name_arabic": "name_ar",
        "السعر": "price",
        "سعر": "price",
        "التصنيف": "category",
        "تصنيف": "category",
        "الكمية": "stock",
        "كمية": "stock",
        "المخزون": "stock",
        "stock_quantity": "stock",
    }

    for row_num, row in enumerate(reader, start=2):
        # Normalize keys
        normalized = {}
        for key, value in row.items():
            if key is None:
                continue
            clean_key = key.strip().lower()
            mapped = header_aliases.get(clean_key, clean_key)
            normalized[mapped] = value.strip() if value else ""

        # Validate required fields
        name_ar = normalized.get("name_ar", "")
        price_str = normalized.get("price", "")

        if not name_ar:
            errors.append(f"Row {row_num}: missing Arabic name (name_ar)")
            continue

        if not price_str:
            errors.append(f"Row {row_num}: missing price")
            continue

        try:
            price = float(price_str.replace(",", ""))
        except ValueError:
            errors.append(f"Row {row_num}: invalid price '{price_str}'")
            continue

        stock = 0
        stock_str = normalized.get("stock", "0")
        try:
            stock = int(float(stock_str)) if stock_str else 0
        except ValueError:
            stock = 0

        products_to_create.append({
            "name": normalized.get("name", name_ar),
            "name_ar": name_ar,
            "price": price,
            "category": normalized.get("category"),
            "stock": stock,
            "description": normalized.get("description"),
        })

    if not products_to_create:
        return ImportResult(
            success=False,
            imported=0,
            skipped=len(errors),
            errors=errors or ["No valid products found in CSV"],
        )

    # Bulk create
    created = await product_service.bulk_create_from_list(merchant_id, products_to_create)

    return ImportResult(
        success=True,
        imported=len(created),
        skipped=len(errors),
        errors=errors,
    )


def format_import_result(result: ImportResult) -> str:
    """Format import result as an Arabic chat message."""
    if not result.success and result.imported == 0:
        error_text = "\n".join(f"  • {e}" for e in result.errors[:5])
        return f"❌ فشل استيراد المنتجات:\n{error_text}"

    msg = f"✅ تم استيراد {result.imported} منتج بنجاح!"
    if result.skipped > 0:
        msg += f"\n⚠️ تم تخطي {result.skipped} سطر بسبب أخطاء."
        if result.errors:
            msg += "\n" + "\n".join(f"  • {e}" for e in result.errors[:3])

    return msg
