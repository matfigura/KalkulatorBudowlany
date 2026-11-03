
from kivy.metrics import dp

from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDRaisedButton


class AddScreen(MDBoxLayout):

    def __init__(self, calculator, on_template_added=None, **kwargs):
        super().__init__(**kwargs)

        self.calculator = calculator
        self.on_template_added = on_template_added

        self.orientation = "vertical"
        self.padding = dp(20)
        self.spacing = dp(15)

        title = MDLabel(
            text="Dodaj nową usługę",
            font_style="H5",
            halign="center",
            size_hint_y=None,
            height=dp(50),
        )

        description = MDLabel(
            text="Utwórz szablon usługi z domyślną ceną za m².",
            halign="center",
            theme_text_color="Secondary",
            size_hint_y=None,
            height=dp(45),
        )

        self.name_field = MDTextField(
            hint_text="Nazwa usługi",
            mode="rectangle",
            size_hint_y=None,
            height=dp(55),
        )

        self.price_field = MDTextField(
            hint_text="Domyślna cena za m² (zł)",
            mode="rectangle",
            input_filter="float",
            size_hint_y=None,
            height=dp(55),
        )

        self.status_label = MDLabel(
            text="",
            halign="center",
            size_hint_y=None,
            height=dp(45),
        )

        save_button = MDRaisedButton(
            text="Zapisz usługę",
            size_hint_x=1,
        )

        save_button.bind(on_release=self.save_template)

        self.add_widget(title)
        self.add_widget(description)
        self.add_widget(self.name_field)
        self.add_widget(self.price_field)
        self.add_widget(save_button)
        self.add_widget(self.status_label)

    def save_template(self, instance):

        name = self.name_field.text.strip()
        price_text = self.price_field.text.strip().replace(",", ".")

        if not name:
            self.show_error("Wpisz nazwę usługi.")
            return

        if not price_text:
            self.show_error("Wpisz domyślną cenę.")
            return

        try:
            price = float(price_text)

            if price < 0:
                self.show_error("Cena nie może być ujemna.")
                return

            if not price < float("inf"):
                self.show_error("Podaj prawidłową cenę.")
                return

            self.calculator.add_template(name, price)

            self.name_field.text = ""
            self.price_field.text = ""

            self.status_label.text = "Usługa została zapisana."
            self.status_label.theme_text_color = "Primary"

            if self.on_template_added:
                self.on_template_added()

        except ValueError as error:
            self.show_error(str(error))

        except Exception as error:
            self.show_error(f"Nie udało się zapisać usługi: {error}")

    def show_error(self, message):

        self.status_label.text = message
        self.status_label.theme_text_color = "Error"
