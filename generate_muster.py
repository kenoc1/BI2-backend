# Bestellung 131127
import cx_Oracle
import os
from dotenv import load_dotenv

load_dotenv()


class InsertOrderPositions:
    def __init__(self):
        password = os.getenv('ORACLE_PASSWORD_DB')
        dsn_tns = cx_Oracle.makedsn('134.106.56.44', '1521', service_name='dbprak2')
        self.con_master = cx_Oracle.connect(user=r'"BI21"', password=password,
                                            dsn=dsn_tns, encoding="UTF-8")
        print("Database version:", self.con_master.version)

    def getBestellungvonMaenner(self):
        try:
            # get Bestellungen
            with self.con_master.cursor() as cursor:
                cursor.execute(
                    """select BESTELLUNG.Bestellung_ID, KUNDE.KUNDE_ID
                        from KUNDE, Bestellung,WARENKORB
                        where BESTELLUNG.WARENKORB_ID = WARENKORB.WARENKORB_ID
                          and WARENKORB.KUNDE_ID = KUNDE.KUNDE_ID
                          and Anrede = 'Herr'""")
                bestllungListvonMaenner = cursor.fetchall()
                return bestllungListvonMaenner
        except cx_Oracle.Error as error:
            print('Error occurred:')
            print(error)

    def getBestellungvonFrauen(self):
        try:
            # get Bestellungen
            with self.con_master.cursor() as cursor:
                cursor.execute(
                    """select BESTELLUNG.Bestellung_ID from KUNDE, Bestellung,WARENKORB
                        where BESTELLUNG.WARENKORB_ID = WARENKORB.WARENKORB_ID
                          and WARENKORB.KUNDE_ID = KUNDE.KUNDE_ID
                          and Anrede = 'Frau'""")
                # cursor.rowfactory = lambda *args: dict(zip([d[0] for d in cursor.description], args))

                bestellungListvonFrauen = cursor.fetchall()
                return bestellungListvonFrauen
        except cx_Oracle.Error as error:
            print('Error occurred:')
            print(error)

    # def getBestellungvonBayern(self):
    #     try:
    #         # get Bestellungen
    #         with self.con_master.cursor() as cursor:
    #             cursor.execute(
    #                 """select KUNDE.KUNDE_ID, BESTELLUNG.BESTELLUNG_ID
    #                     from KUNDE, ADRESSE,KUNDE_ADRESSE, BESTELLUNG, WARENKORB
    #                     where ADRESSE.ADRESSE_ID = KUNDE_ADRESSE.ADRESSE_ID
    #                       and BESTELLUNG.WARENKORB_ID = WARENKORB.WARENKORB_ID
    #                       and WARENKORB.KUNDE_ID = KUNDE.KUNDE_ID
    #                     and ADRESSE.BUNDESLAND like 'Bayern'""")
    #             bestellungListvonBayern = cursor.fetchall()
    #             return bestellungListvonBayern
    #     except cx_Oracle.Error as error:
    #         print('Error occurred:')
    #         print(error)

    def insert_Order_Positions(self, bestellungListvonFrauen, bestellungListvonMaenner):
        # 3950 = BBB BEST APPLE JAM
        # 989 = Even Better Head Cheese
        with self.con_master.cursor() as cursor:
            i = 10000
            while i > 0:
                cursor.execute(
                    f"""INSERT INTO BESTELLPOSITION(Produkt_ID, Bestellung_ID, Menge) VALUES(3950, :i, 1)""", i=i)
                cursor.execute(
                    f"""INSERT INTO BESTELLPOSITION(Produkt_ID, Bestellung_ID, Menge) VALUES(989, :i, 1)""", i=i)
                self.con_master.commit()
                i -= 1

        # 4106 = Cordless screwdrivers
        # 861 = Nationeel Chocolate Donuts
        with self.con_master.cursor() as cursor:
            i = 20000
            while i > 10000:
                cursor.execute(
                    f"""INSERT INTO BESTELLPOSITION(Produkt_ID, Bestellung_ID, Menge) VALUES(4106, {i}, 1)""")
                cursor.execute(
                    f"""INSERT INTO BESTELLPOSITION(Produkt_ID, Bestellung_ID, Menge) VALUES(861, {i}, 1)""")
                self.con_master.commit()
                i -= 1

        # # 112 = Tablet-PC
        # # 4063 = PigTail Frozen Chicken Wings
        # # 212 = High Top Oranges
        with self.con_master.cursor() as cursor:
            i = 30000
            while i > 20000:
                cursor.execute(
                    f"""INSERT INTO BESTELLPOSITION(Produkt_ID, Bestellung_ID, Menge) VALUES(112, {i}, 1)""")
                cursor.execute(
                    f"""INSERT INTO BESTELLPOSITION(Produkt_ID, Bestellung_ID, Menge) VALUES(4063, {i}, 1)""")
                cursor.execute(
                    f"""INSERT INTO BESTELLPOSITION(Produkt_ID, Bestellung_ID, Menge) VALUES(212, {i}, 1)""")
                self.con_master.commit()
                i -= 1

        # 3430 = Super Hot Chocolate
        # 3372 = Best Choice Potato Chips
        with self.con_master.cursor() as cursor:
            counter = 0
            i = 50000
            while i > 0:
                if i in bestellungListvonFrauen:
                    cursor.execute(
                        f"""INSERT INTO BESTELLPOSITION(Produkt_ID, Bestellung_ID, Menge) VALUES(3430, {i}, 1)""")
                    # cursor.execute(
                    #     f"""INSERT INTO BESTELLPOSITION(Produkt_ID, Bestellung_ID, Menge) VALUES(3372, {i}, 1)""")
                    self.con_master.commit()
                    counter += 1
                i -= 1
            print(f"Frauen Insert: {counter}")

        # 758 = Cormorant C-Size Batteries
        # 478 = Dollar Monthly Auto Magazine
        with self.con_master.cursor() as cursor:
            counter = 0
            i = 50000
            while i > 0:
                if i in bestellungListvonMaenner:
                    # cursor.execute(
                    #     f"""INSERT INTO BESTELLPOSITION(Produkt_ID, Bestellung_ID, Menge) VALUES(758, {i}, 1)""")
                    cursor.execute(
                        f"""INSERT INTO BESTELLPOSITION(Produkt_ID, Bestellung_ID, Menge) VALUES(478, {i}, 1)""")
                    self.con_master.commit()
                    counter += 1
                i -= 1
            print(f"Männer Insert: {counter}")

        # # 112 = Tablet-PC
        # # 4063 = PigTail Frozen Chicken Wings
        # with self.con_master.cursor() as cursor:
        #     i = 100000
        #     while i < 0:
        #         if i == bestellungListvonBayern[0]:
        #             cursor.execute(
        #                 f"""INSERT INTO BESTELLPOSITION(Produkt_ID, Bestellung_ID, Menge) VALUES(112, {i}, 1)""")
        #             cursor.execute(
        #                 f"""INSERT INTO BESTELLPOSITION(Produkt_ID, Bestellung_ID, Menge) VALUES(4063, {i} 1)""")
        #             self.con_master.commit()
        #             i -= 1

    def convert_list(self, list1) -> list:
        list2 = []
        for x in list1:
            list2.append(x[0])
        return list2

    def start(self):
        bestellungListvonFrauen = self.convert_list(self.getBestellungvonFrauen())
        bestellungListvonMaenner = self.convert_list(self.getBestellungvonMaenner())
        # bestellungListvonBayern = object.getBestellungvonBayern()
        self.insert_Order_Positions(bestellungListvonFrauen, bestellungListvonMaenner)


insertOrderPositions = InsertOrderPositions()
insertOrderPositions.start()
