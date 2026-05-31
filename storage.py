import json
from dataclasses import dataclass
from typing import Dict, Optional, List
from threading import Lock


# ========== МОДЕЛИ (2 сущности) ==========

@dataclass
class Author:
    id: int
    first_name: str
    last_name: str

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "firstName": self.first_name,
            "lastName": self.last_name
        }


@dataclass
class Book:
    id: int
    title: str
    isbn: str
    author: Author

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "isbn": self.isbn,
            "author": self.author.to_dict()
        }


# ========== ХРАНИЛИЩЕ (InMemoryStorage) ==========

class InMemoryStorage:
    def __init__(self):
        self.authors: Dict[int, Author] = {}
        self.books: Dict[int, Book] = {}
        self._author_seq = 0
        self._book_seq = 0
        self._lock = Lock()

        # Заполняем тестовыми данными
        self._init_data()

    def _init_data(self):
        # Добавляем авторов
        self._author_seq += 1
        author1 = Author(self._author_seq, "Лев", "Толстой")
        self.authors[author1.id] = author1

        self._author_seq += 1
        author2 = Author(self._author_seq, "Федор", "Достоевский")
        self.authors[author2.id] = author2

        # Добавляем книги
        self._book_seq += 1
        book1 = Book(self._book_seq, "Война и мир", "364294392", author1)
        self.books[book1.id] = book1

        self._book_seq += 1
        book2 = Book(self._book_seq, "Идиот", "90234234", author2)
        self.books[book2.id] = book2

        self._book_seq += 1
        book3 = Book(self._book_seq, "Униженные и оскорбленные", "34502934", author2)
        self.books[book3.id] = book3

    def get_all_authors(self) -> List[Author]:
        return list(self.authors.values())

    def get_author_by_id(self, author_id: int) -> Optional[Author]:
        return self.authors.get(author_id)

    def get_all_books(self) -> List[Book]:
        return list(self.books.values())

    def get_book_by_id(self, book_id: int) -> Optional[Book]:
        return self.books.get(book_id)

    def search_books_by_title(self, title: str) -> List[Book]:
        if not title:
            return self.get_all_books()
        title_lower = title.lower()
        return [book for book in self.books.values()
                if title_lower in book.title.lower()]

    def get_books_count(self) -> int:
        return len(self.books)