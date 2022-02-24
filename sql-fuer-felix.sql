-- Kundenranking (Umsatz)


-- Käufe auf Zeit
select TRUNC(RECHNUNGSDATUM), count(RECHNUNG_ID) as ANZAHL_KAEUFE
from RECHNUNG
where RECHNUNGSDATUM between sysdate - 100 AND sysdate
group by TRUNC(RECHNUNGSDATUM);

-- Umsatz auf Zeit
select TRUNC(RECHNUNGSDATUM), sum( SUMME_BRUTTO) as GESAMT_UMSATZ_BRUTTO
from RECHNUNG
where RECHNUNGSDATUM between sysdate - 100 AND sysdate
group by TRUNC(RECHNUNGSDATUM);

-- Ranking
SELECT PRODUKT_ID, RANKING
FROM PRODUKT;

-- Meistverkaufteste Produkte
SELECT BESTELLPOSITION.PRODUKT_ID, COUNT(BESTELLPOSITION.PRODUKT_ID)
FROM BESTELLPOSITION,
     BESTELLUNG
WHERE BESTELLPOSITION.BESTELLUNG_ID = BESTELLUNG.BESTELLUNG_ID
group by BESTELLPOSITION.PRODUKT_ID;

-- Anzahl an Bestellungen - täglich/monatlich/gesamt
SELECT COUNT(Distinct BESTELLUNG_ID)
FROM BESTELLUNG
Where BESTELLDATUM between sysdate - 1 AND sysdate;

SELECT COUNT(Distinct BESTELLUNG_ID)
FROM BESTELLUNG
Where BESTELLDATUM between add_months(trunc(sysdate, 'mm'), -1) and last_day(add_months(trunc(sysdate, 'mm'), -1));

select COUNT(BESTELLUNG_ID)
FROM BESTELLPOSITION;
