
from pathlib import Path

from kivy.utils import platform
from kivymd.app import MDApp
from kivymd.uix.bottomnavigation import (
    MDBottomNavigation,
    MDBottomNavigationItem
)
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel

from database import Database
from calculations import CalculatorService
from screens.saved_screen import SavedScreen
from screens.summary_screen import SummaryScreen
from screens.add_screen import AddScreen


class KalkulatorBudowlanyApp(MDApp):

    def build(self):

        # MOTYW APLIKACJI

        self.title = "Kalkulator Budowlany"

        self.theme_cls.theme_style = "Light"
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.accent_palette = "Orange"

        # ŚCIEŻKA BAZY DANYCH

        if platform == "android":

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
            orientation="vertical"
        )

        # DOLNA NAWIGACJA

        navigation = MDBottomNavigation(
            panel_color="#FFFFFF",
            selected_color_background="#DCE7F5",
            text_color_active="#1565C0"
        )

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

    # WIDOK TYMCZASOWY

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
