import cx_Oracle
import os
from dotenv import load_dotenv

load_dotenv()

password = os.getenv('ORACLE_PASSWORD_DB')
dsn_tns = cx_Oracle.makedsn('134.106.56.44', '1521', service_name='dbprak2') # if needed, place an 'r' before any parameter in order to address special characters such as '\'.
conn = cx_Oracle.connect(user=r'"BI21"', password=password, dsn=dsn_tns) # if needed, place an 'r' before any parameter in order to address special characters such as '\'. For example, if your user name contains '\', you'll need to place 'r' before the user name: user=r'User Name'

c = conn.cursor()
c.execute('SELECT * FROM BI21.BESTELLUNG, BI21.BESTELLPOSITION WHERE BESTELLUNG.BESTELLUNG_ID=BESTELLPOSITION.BESTELLUNG_ID AND BESTELLUNG.WARENKORB_ID = 2280') # use triple quotes if you want to spread your query across multiple lines
for row in c:
    # new_cursor = conn.cursor()
    print(row)
    conn.commit()
conn.close()
