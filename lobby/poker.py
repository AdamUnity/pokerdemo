import random
from itertools import combinations


KOLORY = ['pik', 'kier', 'karo', 'trefl']
WARTOSCI = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']

SYMBOLE_KOLOROW = {
    'pik': '♠',
    'kier': '♥',
    'karo': '♦',
    'trefl': '♣',
}

RANGI_WARTOSCI = {w: i for i, w in enumerate(WARTOSCI)}  # '2'=0, 'A'=12


# ------------------------------------------------------------------ #
# Karta                                                                #
# ------------------------------------------------------------------ #

class Karta:
    def __init__(self, wartosc, kolor):
        self.wartosc = wartosc
        self.kolor = kolor

    def __repr__(self):
        return f'{self.wartosc}{SYMBOLE_KOLOROW[self.kolor]}'

    def do_slownika(self):
        return {'wartosc': self.wartosc, 'kolor': self.kolor, 'symbol': repr(self)}

    @staticmethod
    def ze_slownika(d):
        return Karta(d['wartosc'], d['kolor'])


# ------------------------------------------------------------------ #
# Talia                                                                #
# ------------------------------------------------------------------ #

class Talia:
    def __init__(self):
        self.karty = [Karta(w, k) for k in KOLORY for w in WARTOSCI]
        random.shuffle(self.karty)

    def dobierz(self, ile=1):
        wyciagniete = self.karty[:ile]
        self.karty = self.karty[ile:]
        return wyciagniete

    def do_slownika(self):
        return [k.do_slownika() for k in self.karty]

    @staticmethod
    def ze_slownika(lista):
        t = Talia.__new__(Talia)
        t.karty = [Karta.ze_slownika(d) for d in lista]
        return t


# ------------------------------------------------------------------ #
# Ocena układów                                                        #
# ------------------------------------------------------------------ #

def _rangi(karty):
    return sorted([RANGI_WARTOSCI[k.wartosc] for k in karty], reverse=True)

def _czy_flush(karty):
    return len(set(k.kolor for k in karty)) == 1

def _czy_straight(rangi):
    unikalne = sorted(set(rangi), reverse=True)
    if len(unikalne) < 5:
        return False, []
    for i in range(len(unikalne) - 4):
        sekwencja = unikalne[i:i+5]
        if sekwencja[0] - sekwencja[4] == 4:
            return True, sekwencja
    # As jako 1 (A-2-3-4-5)
    if set([12, 0, 1, 2, 3]).issubset(set(unikalne)):
        return True, [3, 2, 1, 0, -1]
    return False, []

def ocen_reke(karty_gracza, karty_wspolne):
    wszystkie = karty_gracza + karty_wspolne
    najlepszy = (0, 'Wysoka karta', [])

    for combo in combinations(wszystkie, min(5, len(wszystkie))):
        combo = list(combo)
        wynik = _ocen_5_kart(combo)
        if wynik[0] > najlepszy[0]:
            najlepszy = wynik

    return najlepszy[0], najlepszy[1]

def _ocen_5_kart(karty):
    rangi = _rangi(karty)
    flush = _czy_flush(karty)
    straight, straight_rangi = _czy_straight(rangi)

    from collections import Counter
    licznik = Counter(rangi)
    grupy = sorted(licznik.values(), reverse=True)
    unikalne_rangi = sorted(licznik.keys(), key=lambda r: (licznik[r], r), reverse=True)

    if flush and straight:
        if rangi[0] == 12 and rangi[1] == 11:
            return (9_000_000 + sum(rangi), 'Poker królewski', rangi)
        return (8_000_000 + sum(rangi), 'Poker', rangi)

    if grupy[0] == 4:
        return (7_000_000 + unikalne_rangi[0] * 1000 + unikalne_rangi[-1], 'Kareta', unikalne_rangi)

    if grupy[:2] == [3, 2]:
        return (6_000_000 + unikalne_rangi[0] * 1000 + unikalne_rangi[-1], 'Full', unikalne_rangi)

    if flush:
        return (5_000_000 + sum(r * (13 ** i) for i, r in enumerate(reversed(rangi))), 'Kolor', rangi)

    if straight:
        return (4_000_000 + straight_rangi[0], 'Strit', straight_rangi)

    if grupy[0] == 3:
        return (3_000_000 + unikalne_rangi[0] * 1000, 'Trójka', unikalne_rangi)

    if grupy[:2] == [2, 2]:
        pary = sorted([r for r, c in licznik.items() if c == 2], reverse=True)
        kicker = [r for r, c in licznik.items() if c == 1][0]
        return (2_000_000 + pary[0] * 10000 + pary[1] * 100 + kicker, 'Dwie pary', unikalne_rangi)

    if grupy[0] == 2:
        return (1_000_000 + unikalne_rangi[0] * 10000, 'Para', unikalne_rangi)

    return (sum(r * (13 ** i) for i, r in enumerate(reversed(rangi))), 'Wysoka karta', rangi)


# ------------------------------------------------------------------ #
# Stan gry                                                             #
# ------------------------------------------------------------------ #

FAZY = ['pre-flop', 'flop', 'turn', 'river', 'showdown']

class GraPoker:

    def __init__(self, gracze_usernames, small_blind=50):
        self.gracze = gracze_usernames
        self.small_blind = small_blind
        self.big_blind = small_blind * 2

        self.talia = Talia()
        self.karty_wspolne = []
        self.reka = {u: [] for u in gracze_usernames}

        self.pula = 0
        self.stawki = {u: 0 for u in gracze_usernames}
        self.zuzyty_stos = {u: 0 for u in gracze_usernames}

        self.aktywni = list(gracze_usernames)
        self.faza = 'pre-flop'
        self.indeks_aktywnego = 0
        self.czy_skonczona = False
        self.zwyciezca = None
        self.uklady = {}

        self._rozdaj()
        self._pobierz_blindy()

    def _rozdaj(self):
        for u in self.gracze:
            self.reka[u] = self.talia.dobierz(2)

    def _pobierz_blindy(self):
        if len(self.gracze) >= 2:
            sb = self.gracze[0]
            bb = self.gracze[1]
            self._postaw(sb, self.small_blind)
            self._postaw(bb, self.big_blind)
            self.indeks_aktywnego = 2 % len(self.aktywni)

    def _postaw(self, username, kwota):
        self.stawki[username] = self.stawki.get(username, 0) + kwota
        self.zuzyty_stos[username] = self.zuzyty_stos.get(username, 0) + kwota
        self.pula += kwota

    def aktywny_gracz(self):
        if not self.aktywni:
            return None
        return self.aktywni[self.indeks_aktywnego % len(self.aktywni)]

    def max_stawka(self):
        return max(self.stawki.values()) if self.stawki else 0

    def do_wyrownania(self, username):
        return max(0, self.max_stawka() - self.stawki.get(username, 0))

    def fold(self, username):
        if username not in self.aktywni:
            return False, 'Nie jesteś aktywnym graczem.'
        self.aktywni.remove(username)
        if len(self.aktywni) == 1:
            self._zakoncz(self.aktywni[0])
            return True, 'ok'
        self.indeks_aktywnego = self.indeks_aktywnego % len(self.aktywni)
        self._sprawdz_koniec_rundy()
        return True, 'ok'

    def check(self, username):
        if username != self.aktywny_gracz():
            return False, 'Nie twoja tura.'
        if self.do_wyrownania(username) > 0:
            return False, 'Musisz wyrównać lub spasować.'
        self._nastepny_gracz()
        self._sprawdz_koniec_rundy()
        return True, 'ok'

    def call(self, username):
        if username != self.aktywny_gracz():
            return False, 'Nie twoja tura.'
        kwota = self.do_wyrownania(username)
        if kwota == 0:
            return self.check(username)
        self._postaw(username, kwota)
        self._nastepny_gracz()
        self._sprawdz_koniec_rundy()
        return True, 'ok'

    def raise_bet(self, username, kwota_laczna):
        if username != self.aktywny_gracz():
            return False, 'Nie twoja tura.'
        minimum = self.max_stawka() + self.big_blind
        if kwota_laczna < minimum:
            return False, f'Minimalne podbicie to {minimum}.'
        roznica = kwota_laczna - self.stawki.get(username, 0)
        self._postaw(username, roznica)
        self._nastepny_gracz()
        return True, 'ok'

    def _nastepny_gracz(self):
        self.indeks_aktywnego = (self.indeks_aktywnego + 1) % len(self.aktywni)

    def _sprawdz_koniec_rundy(self):
        maks = self.max_stawka()
        wszyscy_wyrownali = all(self.stawki.get(u, 0) == maks for u in self.aktywni)
        if wszyscy_wyrownali:
            self._nastepna_faza()

    def _nastepna_faza(self):
        self.stawki = {u: 0 for u in self.gracze}
        self.indeks_aktywnego = 0

        if self.faza == 'pre-flop':
            self.karty_wspolne += self.talia.dobierz(3)
            self.faza = 'flop'
        elif self.faza == 'flop':
            self.karty_wspolne += self.talia.dobierz(1)
            self.faza = 'turn'
        elif self.faza == 'turn':
            self.karty_wspolne += self.talia.dobierz(1)
            self.faza = 'river'
        elif self.faza == 'river':
            self.faza = 'showdown'
            self._showdown()

    def _showdown(self):
        najlepszy_wynik = -1
        zwyciezca = None
        for u in self.aktywni:
            wynik, nazwa = ocen_reke(self.reka[u], self.karty_wspolne)
            self.uklady[u] = nazwa
            if wynik > najlepszy_wynik:
                najlepszy_wynik = wynik
                zwyciezca = u
        self._zakoncz(zwyciezca)

    def _zakoncz(self, zwyciezca):
        self.zwyciezca = zwyciezca
        self.czy_skonczona = True

    def do_slownika(self):
        return {
            'gracze': self.gracze,
            'small_blind': self.small_blind,
            'big_blind': self.big_blind,
            'talia': self.talia.do_slownika(),
            'karty_wspolne': [k.do_slownika() for k in self.karty_wspolne],
            'reka': {u: [k.do_slownika() for k in karty] for u, karty in self.reka.items()},
            'pula': self.pula,
            'stawki': self.stawki,
            'zuzyty_stos': self.zuzyty_stos,
            'aktywni': self.aktywni,
            'faza': self.faza,
            'indeks_aktywnego': self.indeks_aktywnego,
            'czy_skonczona': self.czy_skonczona,
            'zwyciezca': self.zwyciezca,
            'uklady': self.uklady,
        }

    @staticmethod
    def ze_slownika(d):
        g = GraPoker.__new__(GraPoker)
        g.gracze = d['gracze']
        g.small_blind = d['small_blind']
        g.big_blind = d['big_blind']
        g.talia = Talia.ze_slownika(d['talia'])
        g.karty_wspolne = [Karta.ze_slownika(k) for k in d['karty_wspolne']]
        g.reka = {u: [Karta.ze_slownika(k) for k in karty] for u, karty in d['reka'].items()}
        g.pula = d['pula']
        g.stawki = d['stawki']
        g.zuzyty_stos = d['zuzyty_stos']
        g.aktywni = d['aktywni']
        g.faza = d['faza']
        g.indeks_aktywnego = d['indeks_aktywnego']
        g.czy_skonczona = d['czy_skonczona']
        g.zwyciezca = d['zwyciezca']
        g.uklady = d['uklady']
        return g

    def stan_dla_gracza(self, username):
        return {
            'faza': self.faza,
            'pula': self.pula,
            'karty_wspolne': [k.do_slownika() for k in self.karty_wspolne],
            'moje_karty': [k.do_slownika() for k in self.reka.get(username, [])],
            'aktywny_gracz': self.aktywny_gracz(),
            'aktywni': self.aktywni,
            'stawki': self.stawki,
            'do_wyrownania': self.do_wyrownania(username),
            'max_stawka': self.max_stawka(),
            'czy_skonczona': self.czy_skonczona,
            'zwyciezca': self.zwyciezca,
            'uklady': self.uklady if self.czy_skonczona else {},
            'reka_wszystkich': (
                {u: [k.do_slownika() for k in karty] for u, karty in self.reka.items()}
                if self.czy_skonczona else {}
            ),
        }