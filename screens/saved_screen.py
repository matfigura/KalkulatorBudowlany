
import sqlite3

from kivy.metrics import dp
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup

from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDRaisedButton
from kivymd.app import MDApp
from sharing import generate_estimate_text, share_text


class SavedScreen(MDBoxLayout):
    def __init__(self, calculator, **kwargs):
        super().__init__(**kwargs)

        self.calculator = calculator
        self.orientation = "vertical"
        self.padding = dp(12)
        self.spacing = dp(10)

        self.status_label = MDLabel(
            text="Wybierz usługę i podaj powierzchnię.",
            size_hint_y=None,
            height=dp(35),
            halign="center",
        )
        self.add_widget(self.status_label)

        self.scroll = ScrollView()

        self.cards_layout = MDBoxLayout(
            orientation="vertical",
            spacing=dp(12),
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

        card = MDCard(
            orientation="vertical",
            padding=dp(14),
            spacing=dp(8),
            size_hint_y=None,
            height=dp(280),
            elevation=2,
        )

        title = MDLabel(
            text=service_name,
            font_style="H6",
            size_hint_y=None,
            height=dp(32),
        )

        price_field = MDTextField(
            hint_text="Cena za m² (zł)",
            text=default_price,
            input_filter="float",
            mode="rectangle",
            size_hint_y=None,
            height=dp(48),
        )

        area_field = MDTextField(
            hint_text="Powierzchnia (m²)",
            input_filter="float",
            mode="rectangle",
            size_hint_y=None,
            height=dp(48),
        )

        # Przyciski edycji i usuwania
        management_row = MDBoxLayout(
            orientation="horizontal",
            spacing=dp(8),
            size_hint_y=None,
            height=dp(42),
        )

        edit_button = MDRaisedButton(
            text="Edytuj",
            size_hint_x=0.5,
        )
        edit_button.bind(
            on_release=lambda instance: self.open_edit_popup(template)
        )

        delete_button = MDRaisedButton(
            text="Usuń",
            size_hint_x=0.5,
        )
        delete_button.bind(
            on_release=lambda instance: self.confirm_delete_template(
                template_id,
                service_name,
            )
        )

        management_row.add_widget(edit_button)
        management_row.add_widget(delete_button)

        # Dotychczasowy przycisk dodawania do kosztorysu
        add_button = MDRaisedButton(
            text="Oblicz i dodaj do wyceny",
            size_hint_x=1,
        )

        add_button.bind(
            on_release=lambda instance: self.add_to_estimate(
                template_id,
                price_field.text,
                area_field.text,
            )
        )

        card.add_widget(title)
        card.add_widget(price_field)
        card.add_widget(area_field)
        card.add_widget(management_row)
        card.add_widget(add_button)

        return card

    # -------------------------------------------------
    # EDYCJA ZAPISANEJ USŁUGI
    # -------------------------------------------------

    def open_edit_popup(self, template):
        template_id = template["id"]

        name_field = MDTextField(
            hint_text="Nazwa usługi",
            text=template["nazwa_uslugi"],
            mode="rectangle",
            size_hint_y=None,
            height=dp(55),
        )

        price_field = MDTextField(
            hint_text="Domyślna cena za m² (zł)",
            text=str(template["domyslna_cena_m2"]),
            input_filter="float",
            mode="rectangle",
            size_hint_y=None,
            height=dp(55),
        )

        content = MDBoxLayout(
            orientation="vertical",
            spacing=dp(12),
            padding=dp(12),
            size_hint_y=None,
            height=dp(190),
        )

        content.add_widget(name_field)
        content.add_widget(price_field)

        buttons_row = MDBoxLayout(
            orientation="horizontal",
            spacing=dp(8),
            size_hint_y=None,
            height=dp(45),
        )

        popup = Popup(
            title="Edytuj usługę",
            content=content,
            size_hint=(0.9, None),
            height=dp(310),
            auto_dismiss=False,
        )

        cancel_button = MDRaisedButton(
            text="Anuluj",
            size_hint_x=0.5,
        )
        cancel_button.bind(
            on_release=lambda instance: popup.dismiss()
        )

        save_button = MDRaisedButton(
            text="Zapisz",
            size_hint_x=0.5,
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
            padding=dp(12),
        )

        message = MDLabel(
            text=(
                f"Czy na pewno chcesz usunąć usługę:\n"
                f"{service_name}?"
            ),
            halign="center",
        )

        content.add_widget(message)

        buttons_row = MDBoxLayout(
            orientation="horizontal",
            spacing=dp(8),
            size_hint_y=None,
            height=dp(45),
        )

        popup = Popup(
            title="Potwierdź usunięcie",
            content=content,
            size_hint=(0.9, None),
            height=dp(220),
            auto_dismiss=False,
        )

        cancel_button = MDRaisedButton(
            text="Anuluj",
            size_hint_x=0.5,
        )
        cancel_button.bind(
            on_release=lambda instance: popup.dismiss()
        )

        delete_button = MDRaisedButton(
            text="Usuń",
            size_hint_x=0.5,
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
            padding=dp(12),
            spacing=dp(12),
        )

        content.add_widget(
            MDLabel(
                text=message,
                halign="center",
            )
        )

        close_button = MDRaisedButton(
            text="OK",
            size_hint_x=1,
            size_hint_y=None,
            height=dp(45),
        )

        popup = Popup(
            title=title,
            content=content,
            size_hint=(0.9, None),
            height=dp(230),
            auto_dismiss=False,
        )

        close_button.bind(
            on_release=lambda instance: popup.dismiss()
        )

        content.add_widget(close_button)
        popup.open()
