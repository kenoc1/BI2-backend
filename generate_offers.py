from random import randint

import cx_Oracle
import os
from dotenv import load_dotenv

load_dotenv()

PRODUCT_OFFER_MAX = 10


class Generator:

    def __init__(self):
        password = os.getenv('ORACLE_PASSWORD_DB')
        dsn_tns = cx_Oracle.makedsn('134.106.56.44', '1521',
                                    service_name='dbprak2')  # if needed, place an 'r' before any parameter in order to address special characters such as '\'.
        self.conn = cx_Oracle.connect(user=r'"bi21_onfi2"', password=password,
                                      dsn=dsn_tns)  # if needed, place an 'r' before any parameter in order to address special characters such as '\'. For example, if your user name contains '\', you'll need to place 'r' before the user name: user=r'User Name'

        print("Database version:", self.conn.version)
        pass

    def start(self):
        pass
        for x in range(PRODUCT_OFFER_MAX):
            self.set_random(self.get_random_product(), self.get_random_offer_value())

    def set_random(self, product_id: int, offer_discount: float):
        print(f"P-ID: {product_id} ; Discount: {offer_discount}")
        pass

    def get_random_offer_value(self) -> float:
        pass

    def reset_all_offers(self):
        pass

    def product_present(self, product_id):
        with self.conn.cursor() as cursor:
            cursor.execute("""select * from PRODUKT WHERE PRODUKT_ID = :product_id""", product_id=product_id)
            row = cursor.fetchone()
            if row:
                return True
            else:
                False

    def get_random_product(self) -> int:
        start_product_id = self.get_start_product_id()
        end_product_id = self.get_end_product_id()
        present_product = False
        while not present_product:
            product_id = randint(start_product_id, end_product_id)
            present_product = self.product_present(product_id)
        return product_id

    def get_start_product_id(self):
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("""select MIN(PRODUKT_ID) from PRODUKT""")
                row = cursor.fetchone()
                if row:
                    return row[0]
        except cx_Oracle.Error as error:
            print('Error occurred:')
            print(error)

    def get_end_product_id(self):
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("""select MAX(PRODUKT_ID) from PRODUKT""")
                row = cursor.fetchone()
                if row:
                    return row[0]
        except cx_Oracle.Error as error:
            print('Error occurred:')
            print(error)

    def select_all_products(self):
        return self._select_all_dict("PRODUKT")

    def _select_all_dict(self, table_name):
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(f"""select * from {table_name}""")
                cursor.rowfactory = lambda *args: dict(zip([d[0] for d in cursor.description], args))
                rows = cursor.fetchall()
                if rows:
                    return rows
                else:
                    return []
        except cx_Oracle.Error as error:
            print('Error occurred:')
            print(error)


if __name__ == "__main__":
    # create object
    generator = Generator()
    generator.start()
