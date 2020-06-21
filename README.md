# JointPython
Клиент серверный чат. Серверная часть поддерживается базой данных PostgreSql. Графический интерфейс написан с использованием Qt.
Функционал: 
1. Сервер приложения чата, обрабатывающий запросы от клиентсикх приложений или запросов отправленных командой курл
2. Клиентское приложение:
2.1 В графичечкой версии поддерживаются возможности регистрации, авторизации, выбора чат-группы, посылки сообщений и выбора языка интерфейса
2.2 В дополнении в консольной версии поддерживается возможность создания новых групп, удаления групп, добавления и исключения пользователей руппы от лица админимтратора группы

Примеры графического интерфеса : 

Регистрация:
![Registration](https://github.com/enotnadoske/JointPython/tree/master/pics/RegistrationWindow.png)

Авторизация:
![Authorization](https://github.com/enotnadoske/JointPython/tree/master/pics/LoginWindow.png)

Чат:
![Chat](https://github.com/enotnadoske/JointPython/tree/master/pics/ChatWindow.png)

Состав команды и распределение проделанной работы


VityasZV:
1. Лидер комманды и основной ревьюер.
2. Основы работы сервера и базовых классов, 
3. Основы взаимодействия сервера с базой данных, многопоточная работа с клиентами.
4. Обработка запросов регистрации, авторизации, отправки сообщений в глобальный чат.

SamuilYu:
1. Основы работы клиента: запросы регистрации, авторизации, отправки сообщений и групповые действия; логика консольного приложения.
2. Изменения базовых классов и логики работы с базой данных для осуществления работы с множеством чат-групп.
3. Дополнения в сервер: обработка запросов групповых действий, отправка сообщения в чат-группы.

enotnadoske: 
1. Шаблоны графического интерфрейса.
2. Графический интерфейс клиентского приложения с помощью qt5, доработка логики клента для поддержки графического интерфейса.
3. Встроенная проверка кода с помощью pylint.

zvonand:
1. Тестирование базовых функций
2. Локализация интерфейса
3. Подгтовка wheel пакета

Порядок полуавтоматической установки
Wheel в папке dist

Порядок установки и запуска вручную
1. Склонировать файлы в локальный репозиторий
2. Установить СУБД PostgreSQL
3. От лица postgres создать базу данных chat, в базе данных запустить все три скрипта из папки psql
4. Установить в виртуальном окружении пакеты PyQt5, psycopg2, urllib3, requests
5. Запустить сервер
6. Запустить желаемое число клиентов
