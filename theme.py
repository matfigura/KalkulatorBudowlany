"""Wspólny styl aplikacji (kolory + gotowe widgety)."""
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.popup import Popup

from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDFillRoundFlatButton
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel

# ---------- PALETA ----------
BG = (0.95, 0.96, 0.98, 1)
SURFACE = (1, 1, 1, 1)
PRIMARY = (0.09, 0.33, 0.62, 1)
TEXT_DARK = (0.10, 0.16, 0.24, 1)
TEXT_MUTED = (0.42, 0.47, 0.55, 1)
WHITE = (1, 1, 1, 1)

TONAL_BG = (0.89, 0.93, 0.98, 1)
TONAL_TEXT = (0.09, 0.28, 0.50, 1)
DANGER_BG = (0.99, 0.90, 0.89, 1)
DANGER_TEXT = (0.74, 0.16, 0.14, 1)

RADIUS = dp(20)


# ---------- KARTA ----------
def make_card(**kwargs):
    params = dict(
        orientation="vertical",
        padding=dp(18),
        spacing=dp(12),
        size_hint_y=None,
        elevation=2,
        radius=[RADIUS],
        md_bg_color=SURFACE,
    )
    params.update(kwargs)
    card = MDCard(**params)
    card.bind(minimum_height=card.setter("height"))
    return card


# ---------- PRZYCISKI ----------
def _button(text, bg, fg, height, size_hint, font_size="15sp"):
    return MDFillRoundFlatButton(
        text=text,
        md_bg_color=bg,
        text_color=fg,
        font_size=font_size,
        size_hint=size_hint,
        height=height,
    )


def primary_button(text, height=dp(50), size_hint=(1, None), **kw):
    return _button(text, PRIMARY, WHITE, height, size_hint, **kw)


def tonal_button(text, height=dp(44), size_hint=(1, None), **kw):
    return _button(text, TONAL_BG, TONAL_TEXT, height, size_hint, **kw)


def danger_button(text, height=dp(44), size_hint=(1, None), **kw):
    return _button(text, DANGER_BG, DANGER_TEXT, height, size_hint, **kw)


# ---------- ETYKIETY ----------
def heading(text, height=dp(34), font_style="H6", halign="left"):
    return MDLabel(
        text=text,
        font_style=font_style,
        halign=halign,
        theme_text_color="Custom",
        text_color=TEXT_DARK,
        size_hint_y=None,
        height=height,
    )


def muted(text, height=dp(30), halign="left"):
    return MDLabel(
        text=text,
        halign=halign,
        theme_text_color="Custom",
        text_color=TEXT_MUTED,
        size_hint_y=None,
        height=height,
    )


# ---------- POPUP ----------
class AdaptivePopup(Popup):
    """Popup, który dopasowuje się do klawiatury ekranowej:
    - bez klawiatury: wyśrodkowany,
    - z klawiaturą: przyklejony do góry widocznego obszaru,
      a jego wysokość jest ograniczona do wolnego miejsca."""

    def __init__(self, desired_height=dp(300), **kwargs):
        self._desired_height = desired_height
        super().__init__(**kwargs)

    def on_open(self):
        Window.bind(
            keyboard_height=self._on_keyboard,
            size=self._on_keyboard,
        )
        self._fit()

    def on_dismiss(self):
        Window.unbind(
            keyboard_height=self._on_keyboard,
            size=self._on_keyboard,
        )

    def _on_keyboard(self, *args):
        # Opóźnienie, żeby wykonać się PO własnym wyśrodkowaniu Kivy
        Clock.schedule_once(lambda dt: self._fit(), 0)
        Clock.schedule_once(lambda dt: self._fit(), 0.25)

    def _fit(self):
        self.height = min(self._desired_height, Window.height - dp(24))
        self._align_center()

    def _align_center(self, *args):
        if not getattr(self, "_is_open", True):
            return
        self.center_x = Window.width / 2
        if Window.keyboard_height > 0:
            self.top = Window.height - dp(12)
        else:
            self.center_y = Window.height / 2


def make_popup(title, content, height):
    return AdaptivePopup(
        desired_height=height,
        title=title,
        content=content,
        size_hint=(0.92, None),
        height=height,
        auto_dismiss=False,
        title_color=TEXT_DARK,
        title_size="18sp",
        separator_height=0,
        background="",
        background_color=WHITE,
        overlay_color=(0, 0, 0, 0.45),
    )


def button_row(height=dp(48), spacing=dp(12)):
    return MDBoxLayout(
        orientation="horizontal",
        spacing=spacing,
        size_hint_y=None,
        height=height,
    )