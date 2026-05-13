"""Tedarikciye gonderilecek mail/SMS taslagi olusturucu.

SMTP/SMS gateway entegrasyonu opsiyonel — su an sadece text taslak donerek
admin kopyala-yapistir akisini hizlandiriyoruz.
"""

from datetime import date


def format_tr_amount(amount: float) -> str:
    """1234.5 -> '1.234,50 TL'"""
    return (
        f"{amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        + " TL"
    )


def draft_reorder_mail(
    *,
    supplier_name: str,
    product_name: str,
    order_qty: float,
    unit: str,
    last_unit_cost: float | None = None,
    lead_time_days: int | None = None,
    admin_name: str = "İşletme",
) -> dict:
    """Mail subject + body doner."""
    subject = f"{product_name} siparişi"
    today_str = date.today().strftime("%d.%m.%Y")
    qty_str = f"{int(order_qty)}" if order_qty == int(order_qty) else f"{order_qty}"
    lines = [
        f"Merhaba {supplier_name},",
        "",
        f"{product_name} ürününden {qty_str} {unit} sipariş etmek istiyoruz.",
    ]
    if last_unit_cost:
        total = last_unit_cost * order_qty
        lines.append(
            f"Son bilinen birim maliyet: {format_tr_amount(last_unit_cost)} "
            f"(tahmini toplam: {format_tr_amount(total)})."
        )
    if lead_time_days:
        lines.append(f"Tahmini teslim süresi: {lead_time_days} gün.")
    lines.extend(
        [
            f"Tarih: {today_str}",
            "",
            "İletişim için yanıtlayabilirsiniz.",
            "",
            f"İyi çalışmalar,",
            admin_name,
        ]
    )
    return {"subject": subject, "body": "\n".join(lines)}
