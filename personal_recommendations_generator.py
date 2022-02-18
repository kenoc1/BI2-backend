from random import randint, uniform

import cx_Oracle
import os
import re
from dotenv import load_dotenv

load_dotenv()

SEX = 20
BUY_AGAIN = 35
PRODUCT = 45


class Generator:
    def __init__(self):
        password = os.getenv('ORACLE_PASSWORD_DB')
        dsn_tns = cx_Oracle.makedsn('134.106.56.44', '1521', service_name='dbprak2')
        self.conn = cx_Oracle.connect(user=r'"BI21"', password=password, dsn=dsn_tns)
        print("Database version:", self.conn.version)
        pass

    def get_associations_for_all_customers(self):
        customer_ids = []
        for customer_id in customer_ids:
            self.get_assosiations_for_one_customer(customer_id)

    def get_associations_for_one_customer(self, customer_id):
        associations = []
        associations_sex = self.get_associations_for_sex(customer_id)
        associations_buy_again = self.get_associations_buy_again(customer_id)
        associations_last_orders = self.get_associations_last_orders(customer_id)
        for association in associations_sex:
            associations.append(Association(association.sku, association.match / SEX))
        for association in associations_buy_again:
            if any(x.sku == association.sku for x in associations):
                for a in associations:
                    if a.sku == association.sku:
                        a.match = a.match + (association.match / BUY_AGAIN)
            else:
                associations.append(Association(association.sku, association.match / BUY_AGAIN))
        for association in associations_last_orders:
            if any(x.sku == association.sku for x in associations):
                for a in associations:
                    if a.sku == association.sku:
                        a.match = a.match + (association.match / PRODUCT)
            else:
                associations.append(Association(association.sku, association.match / PRODUCT))
        associations.sort(key=lambda x: x.match, reverse=True)
        return associations

    def get_associations_last_orders(self, customer_id):
        associations = []
        last_orders = self.get_last_ordered_products(customer_id)
        for product_sku in last_orders:
            associations_one_product = []
            with self.conn.cursor() as c:
                sql = "SELECT ITEMS_ADD, LIFT FROM ASSOBESTELLUNG WHERE ITEMS_BASE = '{" + str(
                    product_sku) + "}' ORDER BY LIFT DESC FETCH FIRST 1 ROWS ONLY"
                c.execute(sql)
                row = c.fetchone()
                if row:
                    best_lift = float(row[1])
            with self.conn.cursor() as c:
                sql = "SELECT ITEMS_ADD, LIFT FROM ASSOBESTELLUNG WHERE ITEMS_BASE = '{" + str(
                    product_sku) + "}' ORDER BY LIFT DESC FETCH FIRST 10 ROWS ONLY"
                c.execute(sql)
                if c:
                    for row in c:
                        association = Association(re.search(r'\d+', row[0]).group(), row[1] / best_lift)
                        associations_one_product.append(association)
            for product in associations_one_product:
                if any(x.sku == product.sku for x in associations):
                    pass
                else:
                    associations.append(product)
        return list(set(associations))[:50]

    def get_last_ordered_products(self, customer_id):
        last_orders = []
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(f"""SELECT P.SKU
                                        FROM PRODUKT P
                                            JOIN BESTELLPOSITION BP ON P.PRODUKT_ID = BP.PRODUKT_ID
                                            JOIN BESTELLUNG B ON BP.BESTELLUNG_ID = BP.BESTELLUNG_ID
                                            JOIN WARENKORB W ON B.WARENKORB_ID = W.WARENKORB_ID
                                        WHERE W.KUNDE_ID = {customer_id}
                                        ORDER BY B.BESTELLDATUM DESC
                                        FETCH FIRST 150 ROWS ONLY""")
                rows = cursor.fetchall()
                for row in rows:
                    last_orders.append(row[0])
                return list(set(last_orders))[:50]
        except cx_Oracle.Error as error:
            print('Error occurred:')
            print(error)

    def get_associations_buy_again(self, customer_id):
        associations = []
        with self.conn.cursor() as cursor:
            cursor.execute(f"""SELECT count(*) AS ANZAHL, P.SKU
                                    FROM PRODUKT P 
                                        JOIN BESTELLPOSITION BP ON P.PRODUKT_ID = BP.PRODUKT_ID
                                        JOIN BESTELLUNG B ON B.BESTELLUNG_ID=BP.BESTELLUNG_ID
                                        JOIN WARENKORB W ON W.WARENKORB_ID=B.WARENKORB_ID
                                        JOIN KUNDE K ON K.KUNDE_ID=W.KUNDE_ID
                                    WHERE K.KUNDE_ID = {customer_id}
                                    GROUP BY P.SKU
                                    ORDER BY ANZAHL DESC
                                    FETCH FIRST 1 ROWS ONLY""")
            row = cursor.fetchone()
            most_orders = row[0]
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(f"""SELECT count(*) AS ANZAHL, P.SKU
                                        FROM PRODUKT P 
                                            JOIN BESTELLPOSITION BP ON P.PRODUKT_ID = BP.PRODUKT_ID
                                            JOIN BESTELLUNG B ON B.BESTELLUNG_ID=BP.BESTELLUNG_ID
                                            JOIN WARENKORB W ON W.WARENKORB_ID=B.WARENKORB_ID
                                            JOIN KUNDE K ON K.KUNDE_ID=W.KUNDE_ID
                                        WHERE K.KUNDE_ID = {customer_id}
                                        GROUP BY P.SKU
                                        ORDER BY ANZAHL DESC
                                        FETCH FIRST 50 ROWS ONLY""")
                rows = cursor.fetchall()
                if rows:
                    for row in rows:
                        association = Association(row[1], row[0] / most_orders)
                        associations.append(association)
        except cx_Oracle.Error as error:
            print('Error occurred:')
            print(error)
        return associations

    def get_associations_for_sex(self, customer_id):
        associations = []
        last_orders = self.get_last_ordered_products(customer_id)
        sex = self.get_sex_for_customer(customer_id)
        if sex == "Frau":
            associations = self.get_associations(last_orders, "ASSOANREDEFRAU")
        elif sex == "Herr":
            associations = self.get_associations(last_orders, "ASSOANREDEHERR")
        else:
            pass
        return list(set(associations))[:50]

    def get_sex_for_customer(self, customer_id):
        with self.conn.cursor() as cursor:
            cursor.execute(f"SELECT ANREDE FROM KUNDE WHERE KUNDE_ID = {customer_id}")
            row = cursor.fetchone()
            sex = row[0]
        return sex

    def get_associations(self, last_orders, db_table):
        associations = []
        with self.conn.cursor() as c:
            sql = f"SELECT ITEMS_ADD, LIFT FROM {db_table} ORDER BY LIFT DESC FETCH FIRST 1 ROWS ONLY"
            c.execute(sql)
            row = c.fetchone()
            if row:
                best_lift = float(row[1])
        for sku in last_orders:
            associations_one_product = []
            with self.conn.cursor() as c:
                sql2 = ("SELECT ITEMS_ADD, LIFT FROM " + db_table + " WHERE ITEMS_BASE = '{" +
                        str(sku) + "}'ORDER BY LIFT DESC FETCH FIRST 1 ROWS ONLY")
                c.execute(sql2)
                if c:
                    for row in c:
                        association = Association(re.search(r'\d+', row[0]).group(), row[1] / best_lift)
                        associations_one_product.append(association)
                for product in associations_one_product:
                    if any(x.sku == product.sku for x in associations):
                        pass
                    else:
                        associations.append(product)
        return associations


class Association:
    def __init__(self, sku, match):
        self.sku = sku
        self.match = match

    def __str__(self):
        return "{0} , {1}".format(str(self.sku), str(self.match))


if __name__ == "__main__":
    generator = Generator()
    # generator.get_associations_buy_again(2774)
    # generator.get_associations_last_orders(2774)
    # generator.get_associations_for_sex(2774)
    associations = generator.get_associations_for_one_customer(2774)

    for association in associations:
        print(association)
