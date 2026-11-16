from kivy.metrics import dp
from kivy.utils import platform
from kivy.core.clipboard import Clipboard
from kivy.uix.scrollview import ScrollView

from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField

from theme import (
    BG, PRIMARY, WHITE, TEXT_DARK, make_card, make_popup, button_row,
    primary_button, tonal_button, danger_button, heading,
)


# -------------------------------------------------
# GENEROWANIE TEKSTU KOSZTORYSU
# -------------------------------------------------

def generate_estimate_text(calculator):
    items = calculator.db.get_estimate()

    if not items:
        raise ValueError(
            "Kosztorys jest pusty. Dodaj najpierw jakieś usługi."
        )

    lines = [
        "KOSZTORYS",
        "================================",
        "",
    ]

    for index, item in enumerate(items, start=1):
        name = item["nazwa_uslugi"]
        price = float(item["cena_za_jednostke"])
        area = float(item["ilosc_metrow"])
        value = float(item["wartosc_razem"])

        lines.extend([
            f"{index}. {name}",
            f"   Cena: {price:.2f} zł/m²".replace(".", ","),
            f"   Powierzchnia: {area:.2f} m²".replace(".", ","),
            f"   Wartość: {value:.2f} zł".replace(".", ","),
            "",
        ])

    total = float(calculator.get_total())

    lines.extend([
        "================================",
        f"RAZEM: {total:.2f} zł".replace(".", ","),
        "",
        "Kosztorys wygenerowany w aplikacji Kalkulator Budowlany.",
    ])

    return "\n".join(lines)


# -------------------------------------------------
# UDOSTĘPNIANIE TEKSTU
# -------------------------------------------------

def share_text(text):
    if platform == "android":
        from jnius import autoclass

        PythonActivity = autoclass(
            "org.kivy.android.PythonActivity"
        )
        Intent = autoclass("android.content.Intent")
        String = autoclass("java.lang.String")

        activity = PythonActivity.mActivity

        send_intent = Intent(Intent.ACTION_SEND)
        send_intent.setType("text/plain")
        send_intent.putExtra(
            Intent.EXTRA_TEXT,
            String(text),
        )

        chooser = Intent.createChooser(
            send_intent,
            String("Udostępnij kosztorys"),
        )

        activity.startActivity(chooser)

    else:
        # Na Windows podczas testowania kopiujemy tekst do schowka.
        Clipboard.copy(text)


# -------------------------------------------------
# EKRAN PODSUMOWANIA
# -------------------------------------------------

class SummaryScreen(MDBoxLayout):

    def __init__(self, calculator, **kwargs):
        super().__init__(**kwargs)

        self.calculator = calculator

        self.orientation = "vertical"
        self.md_bg_color = BG
        self.padding = dp(12)
        self.spacing = dp(10)

        # Łączna wartość kosztorysu - wyróżniona karta
        total_card = make_card(
            padding=dp(14),
            md_bg_color=PRIMARY,
        )

        total_caption = MDLabel(
            text="Łączna wartość kosztorysu",
            halign="center",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 0.8),
            size_hint_y=None,
            height=dp(22),
        )

        self.total_label = MDLabel(
            text="0,00 zł",
            font_style="H4",
            halign="center",
            theme_text_color="Custom",
            text_color=WHITE,
            size_hint_y=None,
            height=dp(48),
        )

        total_card.add_widget(total_caption)
        total_card.add_widget(self.total_label)
        self.add_widget(total_card)

        # Komunikaty dla użytkownika
        self.status_label = MDLabel(
            text="",
            halign="center",
            size_hint_y=None,
            height=dp(30),
        )
        self.add_widget(self.status_label)

        # Przewijana lista pozycji
        self.scroll = ScrollView(bar_width=dp(3))

        self.items_layout = MDBoxLayout(
            orientation="vertical",
            spacing=dp(12),
            padding=dp(4),
            size_hint_y=None,
        )

        self.items_layout.bind(
            minimum_height=self.items_layout.setter("height")
        )

        self.scroll.add_widget(self.items_layout)
        self.add_widget(self.scroll)

        # Przycisk udostępniania
        self.share_button = primary_button("Udostępnij kosztorys")
        self.share_button.bind(on_release=self.share_estimate)
        self.add_widget(self.share_button)

        # Przycisk czyszczenia całego kosztorysu
        self.clear_button = danger_button(
            "Wyczyść cały kosztorys", height=dp(46)
        )
        self.clear_button.bind(on_release=self.confirm_clear_estimate)
        self.add_widget(self.clear_button)

        self.refresh_summary()

    # -------------------------------------------------
    # ODŚWIEŻANIE PODSUMOWANIA
    # -------------------------------------------------

    def refresh_summary(self):
        self.items_layout.clear_widgets()

        items = self.calculator.db.get_estimate()

        for item in items:
            self.items_layout.add_widget(
                self.create_item_card(item)
            )

        total = self.calculator.get_total()

        self.total_label.text = (
            f"{total:.2f} zł".replace(".", ",")
        )

        if not items:
            self.items_layout.add_widget(
                MDLabel(
                    text="Kosztorys jest pusty.",
                    halign="center",
                    theme_text_color="Secondary",
                    size_hint_y=None,
                    height=dp(100),
                )
            )

    # -------------------------------------------------
    # KARTA POZYCJI KOSZTORYSU
    # -------------------------------------------------

    def create_item_card(self, item):
        card = make_card(padding=dp(16), spacing=dp(10))

        name = heading(item["nazwa_uslugi"], height=dp(30))

        price = float(item["cena_za_jednostke"])
        area = float(item["ilosc_metrow"])
        value = float(item["wartosc_razem"])

        details = MDLabel(
            text=(
                f"Cena: {price:.2f} zł/m²\n"
                f"Metraż: {area:.2f} m²\n"
                f"Wartość: {value:.2f} zł"
            ).replace(".", ","),
            theme_text_color="Custom",
            text_color=TEXT_DARK,
            size_hint_y=None,
            height=dp(75),
        )

        buttons_layout = button_row(height=dp(44), spacing=dp(6))

        edit_price_button = tonal_button(
            "Cena", size_hint=(1, 1), font_size="13sp"
        )
        edit_area_button = tonal_button(
            "Metraż", size_hint=(1, 1), font_size="13sp"
        )
        delete_button = danger_button(
            "Usuń", size_hint=(1, 1), font_size="13sp"
        )

        edit_price_button.bind(
            on_release=lambda instance: self.open_edit_popup(
                item, "price"
            )
        )

        edit_area_button.bind(
            on_release=lambda instance: self.open_edit_popup(
                item, "area"
            )
        )

        delete_button.bind(
            on_release=lambda instance: self.delete_item(item["id"])
        )

        buttons_layout.add_widget(edit_price_button)
        buttons_layout.add_widget(edit_area_button)
        buttons_layout.add_widget(delete_button)

        card.add_widget(name)
        card.add_widget(details)
        card.add_widget(buttons_layout)

        return card

    # -------------------------------------------------
    # EDYCJA CENY LUB METRAŻU
    # -------------------------------------------------

    def open_edit_popup(self, item, edit_type):

        if edit_type == "price":
            title = "Edytuj cenę za m²"
            current_value = str(item["cena_za_jednostke"])
            hint = "Nowa cena za m²"
        else:
            title = "Edytuj metraż"
            current_value = str(item["ilosc_metrow"])
            hint = "Nowy metraż w m²"

        content = MDBoxLayout(
            orientation="vertical",
            spacing=dp(12),
            padding=dp(16),
        )

        value_field = MDTextField(
            text=current_value,
            hint_text=hint,
            input_filter="float",
            mode="rectangle",
            line_color_focus=PRIMARY,
            size_hint_y=None,
            height=dp(56),
        )

        error_label = MDLabel(
            text="",
            theme_text_color="Error",
            size_hint_y=None,
            height=dp(30),
        )

        buttons = button_row(height=dp(46), spacing=dp(10))

        cancel_button = tonal_button(
            "Anuluj", height=dp(46), size_hint=(1, 1)
        )
        save_button = primary_button(
            "Zapisz", height=dp(46), size_hint=(1, 1)
        )

        content.add_widget(value_field)
        content.add_widget(error_label)

        buttons.add_widget(cancel_button)
        buttons.add_widget(save_button)

        content.add_widget(buttons)

        popup = make_popup(title, content, dp(250), align_top=True)

        def save_changes(instance):
            try:
                new_value = float(
                    value_field.text.replace(",", ".")
                )

                if edit_type == "price":
                    if new_value < 0:
                        raise ValueError(
                            "Cena nie może być ujemna."
                        )

                    new_price = new_value
                    new_area = float(item["ilosc_metrow"])

                else:
                    if new_value <= 0:
                        raise ValueError(
                            "Metraż musi być większy od zera."
                        )

                    new_price = float(
                        item["cena_za_jednostke"]
                    )
                    new_area = new_value

                self.calculator.edit_estimate_item(
                    item["id"],
                    new_price,
                    new_area,
                )

                popup.dismiss()
                self.refresh_summary()

            except ValueError as error:
                error_label.text = str(error)

            except Exception as error:
                error_label.text = f"Błąd zapisu: {error}"

        save_button.bind(on_release=save_changes)

        cancel_button.bind(
            on_release=lambda instance: popup.dismiss()
        )

        popup.open()

    # -------------------------------------------------
    # USUWANIE POJEDYNCZEJ POZYCJI
    # -------------------------------------------------

    def delete_item(self, item_id):
        self.calculator.delete_estimate_item(item_id)
        self.refresh_summary()

    # -------------------------------------------------
    # CZYSZCZENIE CAŁEGO KOSZTORYSU
    # -------------------------------------------------

    def confirm_clear_estimate(self, *args):
        items = self.calculator.db.get_estimate()

        if not items:
            return

        content = MDBoxLayout(
            orientation="vertical",
            spacing=dp(15),
            padding=dp(16),
        )

        content.add_widget(
            MDLabel(
                text=(
                    "Czy na pewno chcesz usunąć "
                    "wszystkie pozycje kosztorysu?"
                ),
                halign="center",
            )
        )

        buttons = button_row(height=dp(46), spacing=dp(10))

        popup = make_popup("Wyczyść kosztorys", content, dp(230))

        cancel_button = tonal_button(
            "Anuluj", height=dp(46), size_hint=(1, 1)
        )
        confirm_button = danger_button(
            "Usuń wszystko", height=dp(46), size_hint=(1, 1)
        )

        cancel_button.bind(
            on_release=lambda instance: popup.dismiss()
        )

        confirm_button.bind(
            on_release=lambda instance:
                self.clear_estimate_confirmed(popup)
        )

        buttons.add_widget(cancel_button)
        buttons.add_widget(confirm_button)

        content.add_widget(buttons)

        popup.open()

    def clear_estimate_confirmed(self, popup):
        self.calculator.clear_estimate()

        popup.dismiss()

        self.refresh_summary()

        self.status_label.text = "Kosztorys został wyczyszczony."
        self.status_label.theme_text_color = "Primary"

    # -------------------------------------------------
    # UDOSTĘPNIANIE KOSZTORYSU
    # -------------------------------------------------

    def share_estimate(self, *args):
        try:
            text = generate_estimate_text(self.calculator)

            share_text(text)

            if platform == "android":
                self.status_label.text = (
                    "Wybierz aplikację, której chcesz użyć "
                    "do udostępnienia kosztorysu."
                )
            else:
                self.status_label.text = (
                    "Kosztorys skopiowano do schowka."
                )

            self.status_label.theme_text_color = "Primary"

        except ValueError as error:
            self.status_label.text = str(error)
            self.status_label.theme_text_color = "Error"

        except Exception as error:
            self.status_label.text = (
                f"Nie udało się udostępnić kosztorysu: {error}"
            )
            self.status_label.theme_text_color = "Error"