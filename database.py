
import sqlite3
from pathlib import Path


class Database:

    def __init__(self, db_path=None):

        if db_path is None:
            db_path = (
                Path(__file__).resolve().parent
                / "kalkulator_budowlany.db"
            )

        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self.create_tables()

    # POŁĄCZENIE Z BAZĄ

    def connect(self):

        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")

        return connection

    # TWORZENIE TABEL

    def create_tables(self):

        with self.connect() as conn:

            conn.execute("""
                CREATE TABLE IF NOT EXISTS Szablony_Uslug (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nazwa_uslugi TEXT NOT NULL,
                    domyslna_cena_m2 REAL NOT NULL
                        CHECK(domyslna_cena_m2 >= 0)
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS Pozycje_Kosztorysu (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    szablon_id INTEGER NOT NULL,
                    nazwa_uslugi TEXT NOT NULL,
                    cena_za_jednostke REAL NOT NULL
                        CHECK(cena_za_jednostke >= 0),
                    ilosc_metrow REAL NOT NULL
                        CHECK(ilosc_metrow > 0),
                    wartosc_razem REAL GENERATED ALWAYS AS (
                        ROUND(cena_za_jednostke * ilosc_metrow, 2)
                    ) STORED,
                    FOREIGN KEY (szablon_id)
                        REFERENCES Szablony_Uslug(id)
                        ON DELETE RESTRICT
                )
            """)

    # SZABLONY USŁUG

    def add_template(self, name, price):

        with self.connect() as conn:

            cursor = conn.execute("""
                INSERT INTO Szablony_Uslug
                (nazwa_uslugi, domyslna_cena_m2)
                VALUES (?, ?)
            """, (name, float(price)))

            return cursor.lastrowid

    def get_templates(self):

        with self.connect() as conn:

            return conn.execute("""
                SELECT *
                FROM Szablony_Uslug
                ORDER BY id
            """).fetchall()

    def get_template(self, template_id):

        with self.connect() as conn:

            return conn.execute("""
                SELECT *
                FROM Szablony_Uslug
                WHERE id = ?
            """, (template_id,)).fetchone()

    def update_template(self, template_id, name, default_price):

        with self.connect() as conn:

            cursor = conn.execute("""
                UPDATE Szablony_Uslug
                SET nazwa_uslugi = ?,
                    domyslna_cena_m2 = ?
                WHERE id = ?
            """, (
                name,
                float(default_price),
                template_id
            ))

            return cursor.rowcount > 0

    def delete_template(self, template_id):

        with self.connect() as conn:

            cursor = conn.execute("""
                DELETE FROM Szablony_Uslug
                WHERE id = ?
            """, (template_id,))

            return cursor.rowcount > 0

    # POZYCJE KOSZTORYSU

    def add_estimate_item(self, template_id, price, area):

        template = self.get_template(template_id)

        if template is None:
            raise ValueError("Nie znaleziono szablonu.")

        with self.connect() as conn:

            cursor = conn.execute("""
                INSERT INTO Pozycje_Kosztorysu
                (
                    szablon_id,
                    nazwa_uslugi,
                    cena_za_jednostke,
                    ilosc_metrow
                )
                VALUES (?, ?, ?, ?)
            """, (
                template_id,
                template["nazwa_uslugi"],
                float(price),
                float(area)
            ))

            return cursor.lastrowid

    def get_estimate(self):

        with self.connect() as conn:

            return conn.execute("""
                SELECT *
                FROM Pozycje_Kosztorysu
                ORDER BY id
            """).fetchall()

    def get_estimate_item(self, item_id):

        with self.connect() as conn:

            return conn.execute("""
                SELECT *
                FROM Pozycje_Kosztorysu
                WHERE id = ?
            """, (item_id,)).fetchone()

    def update_estimate_item(self, item_id, price, area):

        with self.connect() as conn:

            cursor = conn.execute("""
                UPDATE Pozycje_Kosztorysu
                SET cena_za_jednostke = ?,
                    ilosc_metrow = ?
                WHERE id = ?
            """, (
                float(price),
                float(area),
                item_id
            ))

            return cursor.rowcount > 0

    def delete_estimate_item(self, item_id):

        with self.connect() as conn:

            cursor = conn.execute("""
                DELETE FROM Pozycje_Kosztorysu
                WHERE id = ?
            """, (item_id,))

            return cursor.rowcount > 0

    # SUMA KOSZTORYSU

    def get_total(self):

        with self.connect() as conn:

            result = conn.execute("""
                SELECT COALESCE(SUM(wartosc_razem), 0) AS suma
                FROM Pozycje_Kosztorysu
            """).fetchone()

            return result["suma"]

    # CZYSZCZENIE KOSZTORYSU

    def clear_estimate(self):

        with self.connect() as conn:

            conn.execute("""
                DELETE FROM Pozycje_Kosztorysu
            """)
