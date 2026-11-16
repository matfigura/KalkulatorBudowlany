from kivy.metrics import dp
from kivy.clock import Clock
from kivy.uix.scrollview import ScrollView

from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField

from theme import BG, PRIMARY, make_card, primary_button, heading, muted


class AddScreen(MDBoxLayout):

    def __init__(self, calculator, on_template_added=None, **kwargs):
        super().__init__(**kwargs)

        self.calculator = calculator
        self.on_template_added = on_template_added

        self.orientation = "vertical"
        self.md_bg_color = BG
        self.padding = dp(12)
        self.spacing = dp(10)

        # PRZEWIJANY FORMULARZ
        self.scroll = ScrollView(
            do_scroll_x=False,
            do_scroll_y=True,
            bar_width=dp(3),
            scroll_type=["bars", "content"],
        )

        self.form = MDBoxLayout(
            orientation="vertical",
            padding=dp(4),
            spacing=dp(15),
            size_hint_y=None,
        )
        self.form.bind(
            minimum_height=self.form.setter("height")
        )

        # KARTA FORMULARZA
        card = make_card(padding=dp(20), spacing=dp(14))

        title = heading(
            "Dodaj nową usługę",
            height=dp(40),
            font_style="H5",
        )

        description = muted(
            "Utwórz szablon usługi z domyślną ceną za m².",
            height=dp(40),
        )

        self.name_field = MDTextField(
            hint_text="Nazwa usługi",
            mode="rectangle",
            line_color_focus=PRIMARY,
            size_hint_y=None,
            height=dp(60),
        )

        self.price_field = MDTextField(
            hint_text="Domyślna cena za m² (zł)",
            mode="rectangle",
            input_filter="float",
            line_color_focus=PRIMARY,
            size_hint_y=None,
            height=dp(60),
        )

        # AUTOMATYCZNE PRZEWIJANIE DO AKTYWNEGO POLA
        self.name_field.bind(focus=self.on_field_focus)
        self.price_field.bind(focus=self.on_field_focus)

        self.save_button = primary_button("Zapisz usługę")
        self.save_button.bind(on_release=self.save_template)

        self.status_label = MDLabel(
            text="",
            halign="center",
            size_hint_y=None,
            height=dp(40),
        )

        card.add_widget(title)
        card.add_widget(description)
        card.add_widget(self.name_field)
        card.add_widget(self.price_field)
        card.add_widget(self.save_button)
        card.add_widget(self.status_label)

        self.form.add_widget(card)
        self.scroll.add_widget(self.form)

        self.add_widget(self.scroll)

    def on_field_focus(self, instance, focused):

        if focused:
            Clock.schedule_once(
                lambda dt: self.scroll_to_field(instance),
                0.35
            )

    def scroll_to_field(self, field):

        try:
            self.scroll.scroll_to(
                field,
                padding=dp(30),
                animate=True
            )
        except Exception:
            pass

    def save_template(self, instance):

        name = self.name_field.text.strip()

        price_text = (
            self.price_field.text
            .strip()
            .replace(",", ".")
        )

        if not name:
            self.show_error("Wpisz nazwę usługi.")
            self.name_field.focus = True
            return

        if not price_text:
            self.show_error("Wpisz domyślną cenę.")
            self.price_field.focus = True
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

            self.name_field.focus = False
            self.price_field.focus = False

            self.status_label.text = (
                "Usługa została zapisana."
            )

            self.status_label.theme_text_color = "Primary"

            if self.on_template_added:
                self.on_template_added()

        except ValueError as error:
            self.show_error(str(error))

        except Exception as error:
            self.show_error(
                f"Nie udało się zapisać usługi: {error}"
            )

    def show_error(self, message):

        self.status_label.text = message
        self.status_label.theme_text_color = "Error"