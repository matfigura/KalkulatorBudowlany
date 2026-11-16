from pathlib import Path

from kivy.utils import platform
from kivy.core.window import Window
from kivy.config import Config
from kivymd.app import MDApp
from kivymd.uix.bottomnavigation import (
    MDBottomNavigation,
    MDBottomNavigationItem
)
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.toolbar import MDTopAppBar

from database import Database
from calculations import CalculatorService
from screens.saved_screen import SavedScreen
from screens.summary_screen import SummaryScreen
from screens.add_screen import AddScreen
from theme import BG, PRIMARY, WHITE


class KalkulatorBudowlanyApp(MDApp):

    def build(self):

        # MOTYW APLIKACJI

        self.title = "Kalkulator Budowlany"

        self.theme_cls.theme_style = "Light"
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.primary_hue = "700"
        self.theme_cls.accent_palette = "Orange"

        Window.clearcolor = BG

        if platform == "android":
            Window.softinput_mode = "below_target"

        # ŚCIEŻKA BAZY DANYCH

        if platform == "android":
            Config.set("kivy", "keyboard_mode", "below_target")

            db_path = (
                Path(self.user_data_dir)
                / "kalkulator_budowlany.db"
            )

        else:

            db_path = (
                Path(__file__).resolve().parent
                / "kalkulator_budowlany.db"
            )

        # BACKEND

        self.db = Database(db_path)
        self.calculator = CalculatorService(self.db)

        print("BAZA DANYCH:", db_path)
        print("CZY PLIK ISTNIEJE:", db_path.exists())

        templates = self.db.get_templates()

        print("LICZBA SZABLONÓW:", len(templates))
        print("SZABLONY:", [dict(row) for row in templates])

        # GŁÓWNY UKŁAD

        root = MDBoxLayout(
            orientation="vertical",
            md_bg_color=BG
        )

        # GÓRNY PASEK

        top_bar = MDTopAppBar(
            title="Kalkulator Budowlany",
            elevation=0,
            md_bg_color=PRIMARY,
            specific_text_color=WHITE,
        )
        root.add_widget(top_bar)

        # DOLNA NAWIGACJA

        navigation = MDBottomNavigation(
            panel_color="#FFFFFF",
            selected_color_background="#E4EDF7",
            text_color_active="#17528F",
        )

        # Ustawiane po utworzeniu widgetu (w konstruktorze powoduje
        # błąd, bo self.ids jeszcze nie istnieje).
        navigation.text_color_normal = "#7A8594"

        # ZAKŁADKA 1

        saved_tab = MDBottomNavigationItem(
            name="saved",
            text="Zapisane",
            icon="bookmark"
        )

        self.saved_screen = SavedScreen(self.calculator)
        saved_tab.add_widget(self.saved_screen)

        # ZAKŁADKA 2

        add_tab = MDBottomNavigationItem(
            name="add",
            text="Dodaj nowe",
            icon="plus-circle"
        )

        add_tab.add_widget(
            AddScreen(
                self.calculator,
                on_template_added=self.refresh_saved_screen
            )
        )

        # ZAKŁADKA 3

        summary_tab = MDBottomNavigationItem(
            name="summary",
            text="Podsumowanie",
            icon="calculator"
        )

        self.summary_screen = SummaryScreen(self.calculator)

        summary_tab.add_widget(self.summary_screen)

        navigation.add_widget(saved_tab)
        navigation.add_widget(add_tab)
        navigation.add_widget(summary_tab)

        root.add_widget(navigation)

        return root

    def refresh_saved_screen(self):
        if hasattr(self, "saved_screen"):
            self.saved_screen.refresh_templates()

    def create_placeholder(self, title, description):

        layout = MDBoxLayout(
            orientation="vertical",
            padding=30,
            spacing=20
        )

        heading = MDLabel(
            text=title,
            halign="center",
            font_style="H5",
            adaptive_height=True
        )

        message = MDLabel(
            text=description,
            halign="center",
            theme_text_color="Secondary"
        )

        layout.add_widget(heading)
        layout.add_widget(message)

        return layout


if __name__ == "__main__":
    KalkulatorBudowlanyApp().run()