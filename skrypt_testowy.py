import pandas as pd
import xml.etree.ElementTree as ET
import os
from datetime import datetime

WEJSCIOWY_PLIK   = r"C:\Users\vira.pozniak\Documents\skrypt_upięknienie_macro_danych_witek\Eksportowana-lista.xlsx"
SLOWNIK_STACJI   = r"C:\Users\vira.pozniak\Documents\skrypt_upięknienie_macro_danych_witek\stacje-2025-2026.xml"
PLIK_WYJSCIOWY   = None

#wczytanie słownika
def wczytaj_slownik_stacji(sciezka_xml):

    drzewo = ET.parse(sciezka_xml)
    korzen = drzewo.getroot()

    slownik = {}
    for stacja in korzen.findall("station"):
        nazwa       = stacja.get("name", "").strip()
        pelna_nazwa = stacja.get("fullName", "").strip()
        id_st       = stacja.get("id", "")

        if nazwa:
            slownik[nazwa] = id_st
        if pelna_nazwa:
            slownik[pelna_nazwa] = id_st
    return slownik


#wczytanie pliku wejsciowego
def wczytaj_eksportowana_liste(sciezka):
    rozszerzenie = os.path.splitext(sciezka)[1].lower()
    if rozszerzenie == ".csv":
        df = pd.read_csv(sciezka, sep=";", header=None, encoding="utf-8-sig",
                          dtype=str, keep_default_na=False)
    elif rozszerzenie in (".xlsx", ".xls"):
        df = pd.read_excel(sciezka, header=None, dtype=str)
        df = df.fillna("")
    dane = df.iloc[3:].reset_index(drop=True)
    return dane


#pomocnicze funkcje
def parsuj_czas(wartosc):
    wartosc = str(wartosc).strip()
    if wartosc in ("", "--", "---", "nan"):
        return None, None
    try:
        dt = datetime.strptime(wartosc, "%d.%m.%Y %H:%M:%S")
        return dt.date(), dt.strftime("%H:%M")
    except ValueError:
        return None, None
    


def ustal_sklad(pojazd2_nazwa):
    pojazd2_nazwa = str(pojazd2_nazwa).strip()
    if pojazd2_nazwa in ("", "---", "nan"):
        return 1
    return 2

#główne przetwarzanie 
def przetworz(dane, slownik_stacji):
    wyniki = []

    biezacy_numer_pociagu = None
    biezacy_sklad = None

    for _, wiersz in dane.iterrows():

        lp             = str(wiersz[0]).strip()
        nr_pociagu = wiersz[1]
        pojazd1_nazwa  = wiersz[2]
        pojazd2_nazwa  = wiersz[4]
        stacja         = str(wiersz[6]).strip()
        przyjazd_raw   = wiersz[7]
        odjazd_raw     = wiersz[8]
        weszlo     = wiersz[9]
        wyszlo     = wiersz[10]
        na_pociagu = wiersz[11]

        if lp.lower().startswith("suma"):
            continue

        if lp == "" and stacja == "":
            continue

        if nr_pociagu is not None:
            biezacy_numer_pociagu = nr_pociagu
            biezacy_sklad = ustal_sklad(pojazd2_nazwa)

        if biezacy_numer_pociagu is None:
            continue

        data_przyj, czas_przyj = parsuj_czas(przyjazd_raw)
        data_odj,   czas_odj   = parsuj_czas(odjazd_raw)

        data_wiersza = data_przyj or data_odj

        if stacja.startswith("Nieznana stacja"):
            id_stacji = ""
        else:
            id_stacji = slownik_stacji.get(stacja, "")


        wyniki.append({
            "data":           data_wiersza.strftime("%Y-%m-%d") if data_wiersza else "",
            "numer_pociagu":  biezacy_numer_pociagu,
            "id_stacji":      id_stacji,
            "nazwa_stacji":   stacja,
            "przyjechal":     czas_przyj or "",
            "odjechal":       czas_odj or "",
            "weszlo":         weszlo if weszlo is not None else "",
            "wyszlo":         wyszlo if wyszlo is not None else "",
            "na_pociagu":     na_pociagu if na_pociagu is not None else "",
            "sklad":          biezacy_sklad,
        })

    return pd.DataFrame(wyniki, columns=[
        "data", "numer_pociagu", "id_stacji", "nazwa_stacji",
        "przyjechal", "odjechal", "weszlo", "wyszlo", "na_pociagu", "sklad"
    ])

#główna część
def main():
    slownik_stacji = wczytaj_slownik_stacji(SLOWNIK_STACJI)
    dane_surowe    = wczytaj_eksportowana_liste(WEJSCIOWY_PLIK)
    tabela_macro   = przetworz(dane_surowe, slownik_stacji)

    global PLIK_WYJSCIOWY
    if PLIK_WYJSCIOWY is None:
        nazwa_bazowa = os.path.splitext(os.path.basename(WEJSCIOWY_PLIK))[0]
        PLIK_WYJSCIOWY = os.path.join(
            os.path.dirname(WEJSCIOWY_PLIK), f"macro_{nazwa_bazowa}.csv"
        )
    tabela_macro.to_csv(PLIK_WYJSCIOWY, index=False, header=False, sep=";", encoding="utf-8-sig")

if __name__ == "__main__":
    main()

