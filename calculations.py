
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


class CalculatorService:

    def __init__(self, database):
        self.db = database

    # WALIDACJA LICZB

    @staticmethod
    def validate_number(value, allow_zero=False):

        try:
            number = Decimal(str(value).replace(",", "."))

        except (InvalidOperation, ValueError, TypeError):
            raise ValueError("Wprowadzono nieprawidłową liczbę.")

        if not number.is_finite():
            raise ValueError("Wartość musi być liczbą skończoną.")

        if number < 0 or (number == 0 and not allow_zero):
            raise ValueError("Wartość musi być większa od zera.")

        return number

    # FORMATOWANIE CEN

    @staticmethod
    def format_money(value):

        number = Decimal(str(value)).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP
        )

        return f"{number:,.2f}".replace(",", " ").replace(".", ",")

    # DODAWANIE SZABLONU

    def add_template(self, name, price):

        name = name.strip()

        if not name:
            raise ValueError("Nazwa usługi nie może być pusta.")

        price = self.validate_number(price, allow_zero=True)

        return self.db.add_template(name, price)

    # POBIERANIE SZABLONÓW

    def get_templates(self):
        return self.db.get_templates()

    def get_template(self, template_id):
        return self.db.get_template(template_id)

    # EDYCJA SZABLONU

    def edit_template(self, template_id, name, price):

        name = name.strip()

        if not name:
            raise ValueError("Podaj nazwę usługi.")

        price = self.validate_number(price, allow_zero=True)

        if self.db.get_template(template_id) is None:
            raise ValueError("Nie znaleziono szablonu.")

        return self.db.update_template(
            template_id,
            name,
            price
        )

    # USUWANIE SZABLONU

    def delete_template(self, template_id):

        if self.db.get_template(template_id) is None:
            raise ValueError("Nie znaleziono szablonu.")

        return self.db.delete_template(template_id)

    # DODAWANIE POZYCJI DO KOSZTORYSU

    def add_to_estimate(self, template_id, price, area):

        price = self.validate_number(price, allow_zero=True)
        area = self.validate_number(area)

        if self.db.get_template(template_id) is None:
            raise ValueError("Nie znaleziono szablonu.")

        return self.db.add_estimate_item(
            template_id,
            price,
            area
        )

    # EDYCJA POZYCJI KOSZTORYSU

    def edit_estimate_item(self, item_id, price, area):

        price = self.validate_number(price, allow_zero=True)
        area = self.validate_number(area)

        if not self.db.get_estimate_item(item_id):
            raise ValueError("Nie znaleziono pozycji.")

        return self.db.update_estimate_item(
            item_id,
            price,
            area
        )

    # USUWANIE POZYCJI KOSZTORYSU

    def delete_estimate_item(self, item_id):

        return self.db.delete_estimate_item(item_id)

    # SUMA KOSZTORYSU

    def get_total(self):
        return self.db.get_total()

    # CZYSZCZENIE KOSZTORYSU

    def clear_estimate(self):
        return self.db.clear_estimate()
