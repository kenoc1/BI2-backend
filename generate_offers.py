from random import randint, uniform

import cx_Oracle
import os
from dotenv import load_dotenv

load_dotenv()

PRODUCT_OFFER_MAX = 56
PRODUCT_SUB_CATEGORY_MAX = 14


class Generator:

    def __init__(self):
        password = os.getenv('ORACLE_PASSWORD_DB')
        dsn_tns = cx_Oracle.makedsn('134.106.56.44', '1521',
                                    service_name='dbprak2')  # if needed, place an 'r' before any parameter in order to address special characters such as '\'.
        self.conn = cx_Oracle.connect(user=r'"BI21"', password=password,
                                      dsn=dsn_tns)  # if needed, place an 'r' before any parameter in order to address special characters such as '\'. For example, if your user name contains '\', you'll need to place 'r' before the user name: user=r'User Name'

        print("Database version:", self.conn.version)
        pass

    def start(self):
        # 56 Produkte
        # 14 Subkategorien
        subcategories = []
        for x in range(PRODUCT_SUB_CATEGORY_MAX):
            subcategories.append(self.get_random_subcategory_id(subcategories))

        for x in range(PRODUCT_OFFER_MAX):
            self.set_random(self.get_random_product(subcategories[randint(0, PRODUCT_SUB_CATEGORY_MAX - 1)]),
                            self.get_random_offer_value())

    def set_random(self, product_id: int, offer_discount: float):
        print(f"P-ID: {product_id} ; Discount: {offer_discount}")
        with self.conn.cursor() as cursor:
            cursor.execute(
                """update PRODUKT set ANGEBOTSRABATT=:offer_discount where PRODUKT_ID = :product_id""",
                product_id=product_id, offer_discount=offer_discount)
            self.conn.commit()

    def get_random_offer_value(self) -> float:
        return round(uniform(0.01, 0.5), 2)

    def reset_all_offers(self):
        with self.conn.cursor() as cursor:
            cursor.execute("""update PRODUKT set ANGEBOTSRABATT=0  where ANGEBOTSRABATT <> 0""")
            self.conn.commit()

    def subcategory_present(self, subcategory_id, present_subcategory_ids):
        with self.conn.cursor() as cursor:
            cursor.execute(
                """select * from PRODUKT WHERE PRODUKTKLASSE_ID = :subcategory_id AND DATENHERKUNFT_ID = 1""",
                subcategory_id=subcategory_id)
            row = cursor.fetchone()
            if row:
                if row in present_subcategory_ids:
                    return False
                else:
                    return True
            else:
                return False

    def get_product_list_filtered(self, subcategory_id):
        try:
            result = False
            while not result:
                with self.conn.cursor() as cursor:
                    cursor.execute(
                        """select PRODUKT_ID from PRODUKT WHERE PRODUKTKLASSE_ID = :subcategory_id AND DATENHERKUNFT_ID = 1""",
                        subcategory_id=subcategory_id)
                    row = cursor.fetchall()
                    if row:
                        result = True
                        return row
        except cx_Oracle.Error as error:
            print('Error occurred:')
            print(error)

    def get_random_product(self, subcategory_id) -> int:
        product_list = self.get_product_list_filtered(subcategory_id)
        return product_list[randint(0, len(product_list) - 1)][0]

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

    def get_random_subcategory_id(self, present_subcategory_ids):
        present_subcategory_id = False
        while not present_subcategory_id:
            subcategory_id = randint(1, 113)
            present_subcategory_id = self.subcategory_present(subcategory_id, present_subcategory_ids)
        print(f"SK-ID: {subcategory_id}")
        return subcategory_id


if __name__ == "__main__":
    # create object
    generator = Generator()
    generator.reset_all_offers()
    generator.start()
