import cx_Oracle
import os
from dotenv import load_dotenv

load_dotenv()

password = os.getenv('ORACLE_PASSWORD_DB')
dsn_tns = cx_Oracle.makedsn('134.106.56.44', '1521', service_name='dbprak2') # if needed, place an 'r' before any parameter in order to address special characters such as '\'.
conn = cx_Oracle.connect(user=r'"BI21"', password=password, dsn=dsn_tns) # if needed, place an 'r' before any parameter in order to address special characters such as '\'. For example, if your user name contains '\', you'll need to place 'r' before the user name: user=r'User Name'

c = conn.cursor()
c.execute('select * from produkt_subkategorie order by produkt_subkategorie_id ASC') # use triple quotes if you want to spread your query across multiple lines
for row in c:
    new_cursor = conn.cursor()
    name = row[2].lower().replace(" ", "_").replace("ä", "ae").replace("ü", "ue").replace("ö", "oe")
    print(name)
    new_cursor.execute(f"UPDATE produkt_subkategorie SET slug = '{name}' WHERE produkt_subkategorie_id = {row[0]}")
    conn.commit()
conn.close()
