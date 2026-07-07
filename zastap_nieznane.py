import pandas as pd
import networkx as nx
import re
import os

# =====================================
# PLIKI
# =====================================

INPUT_FILE = "Eksportowana-lista.csv"
GRAPH_FILE = "polaczenia.graphml"

# =====================================
# Wczytanie danych
# =====================================

ext = os.path.splitext(INPUT_FILE)[1].lower()

if ext == ".xlsx":
    df = pd.read_excel(INPUT_FILE)
elif ext == ".csv":
    df = pd.read_csv(INPUT_FILE, sep=";", encoding="utf-8-sig")
else:
    raise ValueError("Obsługiwane są tylko XLSX i CSV")

g = nx.read_graphml(GRAPH_FILE)

# =====================================
# Normalizacja nazw
# =====================================

NAME_FIX = {
    "Warszawa Zachodnia Peron 9": "Warszawa Zachodnia"
}


def normalize_name(x):
    if pd.isna(x):
        return x

    x = str(x).replace("\xa0", " ").strip()

    if x in NAME_FIX:
        return NAME_FIX[x]

    return x


# =====================================
# Mapa grafu
# =====================================

name_to_node = {}
node_to_name = {}

for node, attrs in g.nodes(data=True):
    if "name" in attrs:
        name = normalize_name(attrs["name"])
        name_to_node[name] = node
        node_to_name[node] = name

# =====================================
# Dane
# =====================================

df["Stacja"] = df["Stacja"].apply(normalize_name)

stations = df["Stacja"].tolist()

df["Przyjazd_dt"] = pd.to_datetime(
    df["Przyjazd"],
    dayfirst=True,
    errors="coerce"
)

arrivals = df["Przyjazd_dt"].tolist()

# =====================================
# Nieznana
# =====================================

def is_unknown(x):
    if pd.isna(x):
        return False

    return re.match(
        r"^Nieznana",
        str(x).strip(),
        re.IGNORECASE
    ) is not None


# =====================================
# Pomocnicze
# =====================================

def get_path(A, C):
    if A not in name_to_node:
        return None

    if C not in name_to_node:
        return None

    try:
        nodes = nx.shortest_path(
            g,
            name_to_node[A],
            name_to_node[C]
        )

        return [
            node_to_name.get(x, x)
            for x in nodes
        ]

    except nx.NetworkXNoPath:
        return None


def nearest_by_time(index, left, right):
    target = arrivals[index]

    if pd.isna(target):
        return None

    candidates = []

    if left >= 0 and not pd.isna(arrivals[left]):
        diff = abs(
            (target - arrivals[left]).total_seconds()
        )

        candidates.append(
            (diff, stations[left])
        )

    if right < len(stations) and not pd.isna(arrivals[right]):
        diff = abs(
            (target - arrivals[right]).total_seconds()
        )

        candidates.append(
            (diff, stations[right])
        )

    if not candidates:
        return None

    candidates.sort(key=lambda x: x[0])

    return candidates[0][1]


# =====================================
# Rekonstrukcja
# =====================================

changed = 0

for i in range(len(stations)):
    if not is_unknown(stations[i]):
        continue

    left = i - 1

    while left >= 0:
        if (
            not is_unknown(stations[left])
            and str(stations[left]).strip() != ""
        ):
            break

        left -= 1

    right = i + 1

    while right < len(stations):
        if (
            not is_unknown(stations[right])
            and str(stations[right]).strip() != ""
        ):
            break

        right += 1

    if left < 0 or right >= len(stations):
        continue

    A = stations[left]
    C = stations[right]

    path = get_path(A, C)

    if path:
        if len(path) == 3:
            stations[i] = path[1]
            changed += 1
            continue

        if len(path) > 3:
            continue

    new_station = nearest_by_time(
        i,
        left,
        right
    )

    if new_station:
        stations[i] = new_station
        changed += 1

# =====================================
# Zapis do pliku
# =====================================

df["Stacja"] = stations

df.drop(
    columns=["Przyjazd_dt"],
    inplace=True
)

output = "wynik" + ext

if ext == ".xlsx":
    df.to_excel(
        output,
        index=False
    )
else:
    df.to_csv(
        output,
        sep=";",
        index=False,
        encoding="utf-8-sig"
    )