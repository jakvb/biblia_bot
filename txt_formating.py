from collections import OrderedDict


class Book:
    def __init__(self, book):
        self._book = self._check_begining(book)

    def __str__(self):
        return self._book

    @property
    def book(self):
        return self._book

    @property
    def pretty(self):
        return books[self._book]

    def next(self):
        try:
            self._book = list(books.keys())[list(books.keys()).index(self.book) + 1]
        except IndexError:
            self._book = list(books.keys())[0]
        return self._book

    def _to_ascii(self, txt):
        ret = []
        for ch in txt:
            if ch in repls:
                ret.append(repls[ch])
            else:
                ret.append(ch)
        return ''.join(ret)

    def _check_begining(self, txt):
        for book in chapters:
            b = self._to_ascii(book.lower())
            if b.startswith(txt):
                return chapters[book]


repls = {
    'ľ': 'l',
    'š': 's',
    'č': 'c',
    'ť': 't',
    'ž': 'z',
    'ý': 'y',
    'á': 'a',
    'í': 'i',
    'ú': 'u',
    'ň': 'n',
    'ó': 'o',
}

books = OrderedDict([
    ("gn", "Genezis"),
    ("ex", "Exodus"),
    ("lv", "Levitikus"),
    ("nm", "Numeri"),
    ("dt", "Deuteronómium"),
    ("joz", "Jozua"),
    ("sdc", "Sudcov"),
    ("rut", "Rút"),
    ("1sam", "Prvá Samuelova"),
    ("2sam", "Druhá Samuelova"),
    ("1krl", "Prvá kráľov"),
    ("2krl", "Druhá kráľov"),
    ("1krn", "Prvá kroník"),
    ("2krn", "Druhá kroník"),
    ("ezd", "Ezdráš"),
    ("neh", "Nehemiáš"),
    ("est", "Ester"),
    ("job", "Jób"),
    ("z", "Žalmy"),
    ("pris", "Príslovia"),
    ("koh", "Kohelet"),
    ("koh", "Kazateľ"),
    ("vlp", "Veľpieseň"),
    ("iz", "Izaiáš"),
    ("jer", "Jeremiáš"),
    ("nar", "Náreky"),
    ("ez", "Ezechiel"),
    ("dan", "Daniel"),
    ("oz", "Ozeáš"),
    ("joel", "Joel"),
    ("am", "Amos"),
    ("abd", "Abdiáš"),
    ("jon", "Jonáš"),
    ("mich", "Micheáš"),
    ("nah", "Nahum"),
    ("hab", "Habakuk"),
    ("sof", "Sofoniáš"),
    ("ag", "Aggeus"),
    ("zach", "Zachariáš"),
    ("mal", "Malachiáš"),
    ("mt", "Matúš"),
    ("mk", "Marek"),
    ("lk", "Lukáš"),
    ("jn", "Ján"),
    ("sk", "Skutky apoštolov"),
    ("rim", "Rimanom"),
    ("1kor", "Prvý Korinťanom"),
    ("2kor", "Druhý Korinťanom"),
    ("ga", "Galaťanom"),
    ("ef", "Efezanom"),
    ("flp", "Filipanom"),
    ("kol", "Kolosanom"),
    ("1tes", "Prvý Tesaloničanom"),
    ("2tes", "Druhý Tesaloničanom"),
    ("1tim", "Prvý Timotejovi"),
    ("2tim", "Druhý Timotejovi"),
    ("tit", "Títovi"),
    ("flm", "Filemonovi"),
    ("heb", "Hebrejom"),
    ("jk", "Jakubov"),
    ("1pt", "Prvý Petrov"),
    ("2pt", "Druhý Petrov"),
    ("1jn", "Prvý Jánov"),
    ("2jn", "Druhý Jánov"),
    ("3jn", "Tretí Jánov"),
    ("jud", "Júdov"),
    ("zj", "Zjavenie Jána")
])

chapters = dict(zip(books.values(), books.keys()))