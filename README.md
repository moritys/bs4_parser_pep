
# Проект парсинга pep
Данный парсер служит для сбора информации о версиях Python и PEP. Все команды, информация и ошибки работы логируются.
### Команды парсера
* whats-new: парсинг информации о всех версиях Python и ссылок на их статьи
* latest-versions: статусы версий
* download: скачивание архива с последней версией
* [pep](https://peps.python.org/):  собирает информацию о количестве всех pep и их статусов
#### Атрибуты командной строки
* `-c` очистка кэша
* `-o pretty|file` вывод данных в виде таблицы или в файл

---
### Установка парсера
1. Скачать проект с github
2. Находясь в директории с проектом, установить виртуальное окружение:
`python -m venv venv`
`source venv/scripts/activate`
3. Установить зависимости:
`pip install -r 'requirements.txt'`
4. Запустить парсер в необходимом режиме (см. команды парсера):
`python main.py whats-new|latest-versions|download|pep *optional*: (-c, -o pretty|file)`

##### Автор
mori 🐒
