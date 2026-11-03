from decimal import Decimal, InvalidOperation

from kivy.utils import platform
from kivy.core.clipboard import Clipboard


def format_money(value):
    amount = Decimal(str(value)).quantize(Decimal("0.01"))
    return f"{amount:.2f}".replace(".", ",") + " zł"


def format_area(value):
    area = Decimal(str(value)).normalize()
    return str(area).replace(".", ",")


def generate_estimate_text(calculator):
    items = calculator.db.get_estimate()

    if not items:
        raise ValueError("Kosztorys jest pusty.")

    lines = [
        "KOSZTORYS PRAC",
        "",
    ]

    for index, item in enumerate(items, start=1):
        name = item["nazwa_uslugi"]
        area = item["ilosc_metrow"]
        price = item["cena_za_jednostke"]
        total = item["wartosc_razem"]

        lines.extend([
            f"{index}. {name}",
            f"Powierzchnia: {format_area(area)} m²",
            f"Cena jednostkowa: {format_money(price)}/m²",
            f"Wartość: {format_money(total)}",
            "",
        ])

    total_value = calculator.get_total()

    lines.extend([
        "-------------------------",
        f"RAZEM: {format_money(total_value)}",
    ])

    return "\n".join(lines)


def share_text(text):
    if platform == "android":
        from jnius import autoclass

        PythonActivity = autoclass(
            "org.kivy.android.PythonActivity"
        )
        Intent = autoclass("android.content.Intent")
        String = autoclass("java.lang.String")

        activity = PythonActivity.mActivity

        intent = Intent(Intent.ACTION_SEND)
        intent.setType("text/plain")
        intent.putExtra(
            Intent.EXTRA_TEXT,
            String(text)
        )

        chooser = Intent.createChooser(
            intent,
            String("Udostępnij kosztorys")
        )

        activity.startActivity(chooser)

    else:
        Clipboard.copy(text)