library(readxl)
library(igraph)
library(stringr)
library(writexl)

# =========================
# 1. dane
# =========================
eksp_lista <- read_xlsx("Eksportowana lista.xlsx")
g <- read_graph("polaczenia.graphml", format = "graphml")

df <- eksp_lista
stations <- as.character(df$Stacja)

# =========================
# 2. detekcja "Nieznana"
# =========================

is_unknown <- function(x){
  if(length(x) != 1) return(FALSE)
  if(is.na(x)) return(FALSE)
  if(x == "") return(FALSE)

  str_detect(x, regex("^Nieznana", ignore_case = TRUE))
}

# =========================
# 3. sąsiedzi w grafie
# =========================

get_neighbors <- function(g, node){
  if(is.na(node) || !(node %in% V(g)$name)) return(character(0))
  neighbors(g, node)$name
}

# =========================
# 4. główna rekonstrukcja
# =========================

n <- length(stations)

for(i in seq_len(n)){

  # tylko Nieznana
  if(!is_unknown(stations[i])) next

  # znajdź lewy anchor
  left <- i - 1
  while(left >= 1 && (is.na(stations[left]) || stations[left] == "" || is_unknown(stations[left]))){
    left <- left - 1
  }

  # znajdź prawy anchor
  right <- i + 1
  while(right <= n && (is.na(stations[right]) || stations[right] == "" || is_unknown(stations[right]))){
    right <- right + 1
  }

  # jeśli brak anchorów
  if(left < 1 || right > n) next

  A <- stations[left]
  B <- stations[right]

  # jeśli nie istnieją w grafie
  if(!(A %in% V(g)$name) || !(B %in% V(g)$name)) next

  # shortest path jako referencja topologii
  path <- suppressWarnings(shortest_paths(g, A, B)$vpath[[1]])
  path <- V(g)$name[path]

  if(length(path) == 0) next

  # indeksowanie w segmencie
  segment <- left:right

  for(k in segment){

    if(is_unknown(stations[k])){

      pos <- k - left + 1

      if(pos <= length(path)){
        stations[k] <- path[pos]
      }
    }
  }
}

# =========================
# 5. zapis
# =========================

df$Stacja <- stations
write_xlsx(df, "wynik.xlsx")