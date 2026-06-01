#!/usr/bin/env python3
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from storage import InMemoryStorage

# Глобальное хранилище
storage = InMemoryStorage()


def render_html(body: str) -> str:
    """Оборачивает контент в базовый HTML шаблон"""
    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Книжный магазин</title>
</head>
<body>
    <div>
        <nav>
            <a href="/">Главная</a> | 
            <a href="/authors">Авторы</a> | 
            <a href="/books">Книги</a> | 
            <a href="/search">Поиск книг</a>
        </nav>
        <hr>
        {body}
    </div>
</body>
</html>"""


class BookStoreHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query_params = parse_qs(parsed.query)

        # ========== MAIN CONTROLLER (Health Check) ==========
        if path == "/" or path == "/check":
            self._handle_main()
        # ========== AUTHOR CONTROLLER ==========
        elif path == "/authors":
            self._handle_authors_list()
        elif path.startswith("/authors/"):
            self._handle_author_detail(path)
        # ========== BOOK CONTROLLER ==========
        elif path == "/books":
            self._handle_books_list()
        elif path == "/search":
            title = query_params.get('title', [None])[0]
            self._handle_books_search(title)
        elif path.startswith("/books/"):
            self._handle_book_detail(path)
        else:
            self._handle_404()

    # ========== MAIN CONTROLLER ==========
    def _handle_main(self):
        """Главная страница и Health Check"""
        books_count = storage.get_books_count()
        body = f"""
        <h1>Добро пожаловать в наш магазин!!!</h1>
        <h3>У нас аж {books_count} книги!!!</h3>
        <p>Сервер работает, всё хорошо!</p>
        """
        self._send_html(200, render_html(body))

    # ========== AUTHOR CONTROLLER ==========
    def _handle_authors_list(self):
        """Список всех авторов"""
        authors = storage.get_all_authors()
        items = "".join([
            f"<li><a href='/authors/{author.id}'>{author.first_name} {author.last_name}</a></li>"
            for author in authors
        ])
        body = f"<h1>Наши авторы</h1><ul>{items}</ul>"
        self._send_html(200, render_html(body))

    def _handle_author_detail(self, path: str):
        """Детальная страница автора"""
        try:
            author_id = int(path.split("/")[-1])
            author = storage.get_author_by_id(author_id)
            if author:
                body = f"""
                <h1>{author.first_name} {author.last_name}</h1>
                <p>ID: {author.id}</p>
                <a href='/authors'>Назад к списку</a>
                """
                self._send_html(200, render_html(body))
            else:
                self._handle_404("Автор не найден")
        except ValueError:
            self._handle_404()

    # ========== BOOK CONTROLLER ==========
    def _handle_books_list(self):
        """Список всех книг"""
        books = storage.get_all_books()
        items = "".join([
            f"<li><a href='/books/{book.id}'>{book.title} ({book.isbn})</a></li>"
            for book in books
        ])
        body = f"<h1>Наши книги</h1><ul>{items}</ul>"
        self._send_html(200, render_html(body))

    def _handle_book_detail(self, path: str):
        """Детальная страница книги"""
        try:
            book_id = int(path.split("/")[-1])
            book = storage.get_book_by_id(book_id)
            if book:
                body = f"""
                <h1>{book.title}</h1>
                <p><strong>ISBN:</strong> {book.isbn}</p>
                <p><strong>Автор:</strong> {book.author.first_name} {book.author.last_name}</p>
                <p><strong>ID:</strong> {book.id}</p>
                <a href='/books'>Назад к списку</a>
                """
                self._send_html(200, render_html(body))
            else:
                self._handle_404("Книга не найдена")
        except ValueError:
            self._handle_404()

    def _handle_books_search(self, title: str = None):
        """Поиск книг по названию"""
        if title is None:
            # Показываем форму поиска
            body = """
            <h1>Поиск книг</h1>
            <form action='/search' method='GET'>
                <input type='text' name='title' placeholder='Введите название...' style='padding: 5px; width: 200px;'>
                <button type='submit' style='padding: 5px 10px;'>Искать</button>
            </form>
            """
            self._send_html(200, render_html(body))
        else:
            # Выполняем поиск
            books = storage.search_books_by_title(title)
            if books:
                items = "".join([
                    f"<li><a href='/books/{book.id}'>{book.title} ({book.isbn})</a></li>"
                    for book in books
                ])
                body = f"<h1>Результаты поиска: '{title}'</h1><ul>{items}</ul><a href='/search'>Новый поиск</a>"
            else:
                body = f"<h1>Книги не найдены по запросу '{title}'</h1><a href='/search'>Новый поиск</a>"
            self._send_html(200, render_html(body))

    # ========== ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ==========
    def _send_html(self, status: int, content: str):
        """Отправляет HTML ответ"""
        self.send_response(status)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(content.encode('utf-8'))

    def _send_json(self, status: int, data: dict):
        """Отправляет JSON ответ (для API)"""
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

    def _handle_404(self, message: str = "Страница не найдена"):
        """Обработка 404 ошибки"""
        body = f"<h1>404 - {message}</h1><a href='/'>На главную</a>"
        self._send_html(404, render_html(body))

    def log_message(self, format, *args):
        """Вывод логов в консоль"""
        print(f"[{self.address_string()}] {format % args}")


def run_server(port: int = 5000):
    server_address = ('', port)
    httpd = HTTPServer(server_address, BookStoreHandler)
    print(f"Сервер запущен на порту {port}")
    print(f"Доступен по адресу: http://localhost:{port}")
    print("Нажмите Ctrl+C для остановки")
    httpd.serve_forever()

"""
как перекинуть файл: 
scp "D:\Учёба\bookstore.jar" bob@10.226.75.156:/home/bob/

создать /var/www/app c 755
скопировать файлы приложения туда
"""

"""
/etc/nginx/sites-available/bookstore
server {
    listen 80;
    server_name _;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
    }
}

и создаём сслыку на это:
sudo ln -s /etc/nginx/sites-available/bookstore /etc/nginx/sites-enabled/
"""

if __name__ == '__main__':
    run_server()

"""
/etc/systemd/system/bookstore.service
[Unit]
Description=Simple bookstore
After=network.target

[Service]
Type=simple
User=boris
ExecStart=/usr/bin/python3 /var/www/app/server.py

[Install]
WantedBy=multi-user.target
"""