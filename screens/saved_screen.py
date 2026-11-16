import sqlite3

from kivy.metrics import dp
from kivy.uix.scrollview import ScrollView

from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.app import MDApp
from sharing import generate_estimate_text, share_text

from theme import (
    BG, PRIMARY, make_card, make_popup, button_row,
    primary_button, tonal_button, danger_button, heading, muted,
)


class SavedScreen(MDBoxLayout):
    def __init__(self, calculator, **kwargs):
        super().__init__(**kwargs)

        self.calculator = calculator
        self.orientation = "vertical"
        self.md_bg_color = BG
        self.padding = dp(12)
        self.spacing = dp(8)

        self.status_label = MDLabel(
            text="Wybierz usługę i podaj powierzchnię.",
            size_hint_y=None,
            height=dp(35),
            halign="center",
            theme_text_color="Secondary",
        )
        self.add_widget(self.status_label)

        self.scroll = ScrollView(bar_width=dp(3))

        self.cards_layout = MDBoxLayout(
            orientation="vertical",
            spacing=dp(14),
            padding=dp(4),
            size_hint_y=None,
        )
        self.cards_layout.bind(
            minimum_height=self.cards_layout.setter("height")
        )

        self.scroll.add_widget(self.cards_layout)
        self.add_widget(self.scroll)

        self.refresh_templates()

    def refresh_templates(self):
        self.cards_layout.clear_widgets()

        templates = self.calculator.db.get_templates()

        if not templates:
            self.cards_layout.add_widget(
                MDLabel(
                    text="Brak zapisanych usług.",
                    halign="center",
                    theme_text_color="Secondary",
                    size_hint_y=None,
                    height=dp(100),
                )
            )
            return

        for template in templates:
            card = self.create_service_card(template)
            self.cards_layout.add_widget(card)

    def create_service_card(self, template):

        template_id = template["id"]
        service_name = template["nazwa_uslugi"]
        default_price = str(template["domyslna_cena_m2"])

        card = make_card(padding=dp(18), spacing=dp(12))

        # NAZWA USŁUGI
        title = heading(service_name, height=dp(34))

        # CENA
        price_field = MDTextField(
            hint_text="Cena za m² (zł)",
            text=default_price,
            input_filter="float",
            mode="rectangle",
            line_color_focus=PRIMARY,
            size_hint_y=None,
            height=dp(52),
        )

        # POWIERZCHNIA
        area_field = MDTextField(
            hint_text="Powierzchnia (m²)",
            input_filter="float",
            mode="rectangle",
            line_color_focus=PRIMARY,
            size_hint_y=None,
            height=dp(52),
        )

        # GÓRA: "Oblicz i dodaj do wyceny" - cała szerokość
        add_button = primary_button("Oblicz i dodaj do wyceny")

        add_button.bind(
            on_release=lambda instance: self.add_to_estimate(
                template_id,
                price_field.text,
                area_field.text,
            )
        )

        # DÓŁ: "Edytuj" i "Usuń" - po połowie szerokości
        management_row = button_row(height=dp(46), spacing=dp(10))

        edit_button = tonal_button("Edytuj", size_hint=(0.5, 1))
        edit_button.bind(
            on_release=lambda instance: self.open_edit_popup(template)
        )

        delete_button = danger_button("Usuń", size_hint=(0.5, 1))
        delete_button.bind(
            on_release=lambda instance: self.confirm_delete_template(
                template_id,
                service_name,
            )
        )

        management_row.add_widget(edit_button)
        management_row.add_widget(delete_button)

        card.add_widget(title)
        card.add_widget(price_field)
        card.add_widget(area_field)
        card.add_widget(add_button)
        card.add_widget(management_row)

        return card

    # -------------------------------------------------
    # EDYCJA ZAPISANEJ USŁUGI
    # -------------------------------------------------

    def open_edit_popup(self, template):

        template_id = template["id"]

        content = MDBoxLayout(
            orientation="vertical",
            padding=dp(18),
            spacing=dp(12),
        )

        name_field = MDTextField(
            text=template["nazwa_uslugi"],
            hint_text="Nazwa usługi",
            mode="rectangle",
            line_color_focus=PRIMARY,
            size_hint_y=None,
            height=dp(56),
        )

        price_field = MDTextField(
            text=str(template["domyslna_cena_m2"]),
            hint_text="Domyślna cena za m² (zł)",
            input_filter="float",
            mode="rectangle",
            line_color_focus=PRIMARY,
            size_hint_y=None,
            height=dp(56),
        )

        buttons_row = button_row()

        popup = make_popup("Edytuj usługę", content, dp(320), align_top=True)

        cancel_button = tonal_button(
            "Anuluj", height=dp(48), size_hint=(0.5, 1)
        )
        cancel_button.bind(
            on_release=lambda instance: popup.dismiss()
        )

        save_button = primary_button(
            "Zapisz", height=dp(48), size_hint=(0.5, 1)
        )
        save_button.bind(
            on_release=lambda instance: self.save_template_changes(
                popup,
                template_id,
                name_field.text,
                price_field.text,
            )
        )

        buttons_row.add_widget(cancel_button)
        buttons_row.add_widget(save_button)

        content.add_widget(name_field)
        content.add_widget(price_field)
        content.add_widget(buttons_row)

        popup.open()

    def save_template_changes(
        self,
        popup,
        template_id,
        name,
        price_text,
    ):
        try:
            price = float(price_text.replace(",", "."))

            if price < 0:
                raise ValueError("Cena nie może być ujemna.")

            if not name.strip():
                raise ValueError("Podaj nazwę usługi.")

            updated = self.calculator.edit_template(
                template_id,
                name,
                price,
            )

            if updated is False:
                raise ValueError("Nie znaleziono usługi do edycji.")

            popup.dismiss()
            self.refresh_templates()

            self.status_label.text = "Usługa została zaktualizowana."
            self.status_label.theme_text_color = "Primary"

        except ValueError as error:
            self.show_message(str(error), "Błąd edycji")

        except Exception as error:
            self.show_message(
                f"Nie udało się edytować usługi: {error}",
                "Błąd",
            )

    # -------------------------------------------------
    # USUWANIE ZAPISANEJ USŁUGI
    # -------------------------------------------------

    def confirm_delete_template(self, template_id, service_name):
        content = MDBoxLayout(
            orientation="vertical",
            spacing=dp(12),
            padding=dp(14),
        )

        message = MDLabel(
            text=(
                f"Czy na pewno chcesz usunąć usługę:\n"
                f"{service_name}?"
            ),
            halign="center",
        )

        content.add_widget(message)

        buttons_row = button_row(height=dp(46))

        popup = make_popup("Potwierdź usunięcie", content, dp(220))

        cancel_button = tonal_button(
            "Anuluj", height=dp(46), size_hint=(0.5, 1)
        )
        cancel_button.bind(
            on_release=lambda instance: popup.dismiss()
        )

        delete_button = danger_button(
            "Usuń", height=dp(46), size_hint=(0.5, 1)
        )
        delete_button.bind(
            on_release=lambda instance: self.delete_template(
                popup,
                template_id,
            )
        )

        buttons_row.add_widget(cancel_button)
        buttons_row.add_widget(delete_button)

        content.add_widget(buttons_row)

        popup.open()

    def delete_template(self, popup, template_id):
        try:
            deleted = self.calculator.delete_template(template_id)

            if deleted is False:
                raise ValueError("Nie znaleziono usługi do usunięcia.")

            popup.dismiss()
            self.refresh_templates()

            self.status_label.text = "Usługa została usunięta."
            self.status_label.theme_text_color = "Primary"

        except sqlite3.IntegrityError:
            popup.dismiss()
            self.show_message(
                "Nie można usunąć tej usługi, ponieważ jest już "
                "używana w kosztorysie.\n\n"
                "Najpierw usuń powiązaną pozycję z kosztorysu.",
                "Nie można usunąć usługi",
            )

        except Exception as error:
            popup.dismiss()
            self.show_message(
                f"Nie udało się usunąć usługi: {error}",
                "Błąd",
            )

    # -------------------------------------------------
    # DODAWANIE POZYCJI DO KOSZTORYSU
    # -------------------------------------------------

    def add_to_estimate(self, template_id, price_text, area_text):
        try:
            price = float(price_text.replace(",", "."))
            area = float(area_text.replace(",", "."))

            if price < 0 or area <= 0:
                raise ValueError(
                    "Cena nie może być ujemna, a powierzchnia "
                    "musi być większa od zera."
                )

            self.calculator.add_to_estimate(
                template_id,
                price,
                area,
            )

            app = MDApp.get_running_app()

            if hasattr(app, "summary_screen"):
                app.summary_screen.refresh_summary()

            self.status_label.text = "Pozycja została dodana do wyceny."
            self.status_label.theme_text_color = "Primary"

        except ValueError as error:
            self.status_label.text = str(error)
            self.status_label.theme_text_color = "Error"

        except Exception as error:
            self.status_label.text = (
                f"Nie udało się dodać pozycji: {error}"
            )
            self.status_label.theme_text_color = "Error"

    # -------------------------------------------------
    # KOMUNIKATY
    # -------------------------------------------------

    def show_message(self, message, title="Informacja"):
        content = MDBoxLayout(
            orientation="vertical",
            padding=dp(14),
            spacing=dp(12),
        )

        content.add_widget(
            MDLabel(
                text=message,
                halign="center",
            )
        )

        close_button = primary_button("OK", height=dp(46))

        popup = make_popup(title, content, dp(250))

        close_button.bind(
            on_release=lambda instance: popup.dismiss()
        )

        content.add_widget(close_button)
        popup.open()