from config import *
import database
import googletable
import telebot
from telebot import types
import datetime

# Создание экземпляра класса TeleBot для подключения к Telegram
bot = telebot.TeleBot(TOKEN)

# Создание экземпляра класса GoogleTable для подключения к таблицам
google_table = googletable.GoogleTable(FILENAME_GOOGLETABLE)
# Открытие таблицы с заданным именем
google_table.open_table(NAME_GOOGLETABLE)


# Формирование клавиатуры (кнопок) для отправки пользователю
def keyboard(user):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    # Список всех кнопок
    buttons = [types.KeyboardButton("Создать очередь"),
                types.KeyboardButton("Список очередей"),
                types.KeyboardButton("Запись в очередь"),
                types.KeyboardButton("Отмена записи"),
                types.KeyboardButton("Просмотр своих записей"),
                types.KeyboardButton("Запись на досдачу")]
    markup.add(*buttons)
    return markup


# Конвертер времени из строковой строки в экземпляр класса datetime
def convert_time(time_str):
    try:
        return datetime.datetime(year=int(time_str.split("-")[0].split(".")[2]),
                          month=int(time_str.split("-")[0].split(".")[1]),
                          day=int(time_str.split("-")[0].split(".")[0]),
                          hour=int(time_str.split("-")[1].split(":")[0]),
                          minute=int(time_str.split("-")[1].split(":")[1]))
    except IndexError:
        raise "Время должно передаваться в формате ДД.ММ.ГГГГ-ЧЧ:ММ"


# Создание очереди (user - массив)
def queue_create(user):
    try:
        queue_data = user["create_queue"].split("_")  # Преобразование в список данных о создании очереди у пользователя
        queue_priority = queue_data[0]  # Данные о приоритетности очереди
        queue_subject = queue_data[1]  # Данные о предмета очереди
        queue_teacher = queue_data[2]  # Данные о преподавателе очереди
        queue_time = queue_data[3]  # Данные о времени очереди
        table_data = google_table.read_data()  # Получение Google таблицы
        # Цикл, перебирающий всех преподавателей, для проверки был ли он занесён в таблицу
        for i in range(0, len(table_data["teacher"])):
            # Если преподаватель есть в таблице, то проверить не занят ли он в ближайший час
            if table_data["teacher"][i] == queue_teacher:
                # Разница между временем созданием очереди и временем преподавателя в таблице
                if abs((convert_time(table_data["time"][i]) - convert_time(queue_time)).seconds) <= 3600:
                    break
        else:
            # Если цикл не использовал break, то создаётся очередь
            google_table.create_queue(queue_subject, queue_teacher, queue_time, user, queue_priority)
            database.users_save(user["id"], "create_queue", "")  # Удаление в БД данных о создание очереди у пользователя
            database.users_save(user["id"], "location_in_bot", "menu")  # Перемещение пользователя в меню бота
            return "Очередь создана!"
        return "Уже существует очередь в течении часа к этому преподавателю!"
    except:
        return "Не удалось создать очередь!"


# Список всех очередей
def queue_list():
    text = ""  # Текст со всеми очередями
    table_data = google_table.read_data()  # Получение Google таблицы
    # Цикл, проходящий по всем строкам таблицы, для получения данных о каждой строке
    for i in range(0, len(table_data["subject"])):
        text += f"{i+1}. " + table_data["subject"][i] + " " + table_data["teacher"][i] + " " + table_data["time"][i] + "\n" + table_data["students"][i] + "\n"
    if text == "":
        return "На данный момент очередей нет!"
    else:
        return "Список очередей: \n" + text


# Добавление пользователя в очередь
def queue_add(user, number):
    # Используем исключение для обработки возможных ошибок при получении номера очереди от пользователя
    try:
        table_data = google_table.read_data()  # Получение Google таблицы
        # Проверка на то, что номер очереди существует среди очередей
        if len(table_data["subject"]) > 0 and (0 < int(number) <= len(table_data["subject"])):
            priority_id = 0  # Приоритетность пользователя при добавлении в очередь, если она задана при создании
            # Цикл, перебирающий всех студентов, в заданной очереди
            for name in table_data["students"][int(number)-1].split("\n"):
                # Если есть приоритетность в очереди и пользователь из приоритетной очереди, то его будем добавлять в конец приоритеной очереди
                if name.split(" ")[0] == table_data["priority"][int(number)-1]:
                    priority_id += 1
                # Проверка на нахождение пользователя в очереди, в случае нахождения, не добавляем его в данную очередь
                if name.split(" ")[1:] == user["name"]:
                    return "Вы уже есть в этой очереди!"
            # Если задана приоритетность в очереди, то добавляем пользователя по приоритетности, если она у него есть
            if user["group"] == table_data["priority"][int(number)-1]:
                students = table_data["students"][int(number) - 1].split("\n")  # Все студенты в данной очереди
                students.insert(priority_id, user["group"] + " " + user["name"])  # Вставка пользователя в нужное место приоритетности
                students = "\n".join(students)  # Преобразование списка в строку
                google_table.write_students(int(number) + 1, students)  # Перезапись всех студентов в очередь
            else: # Нет приоритета
                # Запись пользователя в конец очереди
                google_table.write_students(int(number)+1, table_data["students"][int(number)-1]+"\n"+user["group"]+" "+user["name"])
            return "Вы добавлены в очередь!"
        else:
            return "Введите номер очереди из списка!"
    except (IndexError, ValueError):
        return "Введите номер очереди из списка!"


# Удаление пользователя из очереди
def queue_delete(user, number):
    # Используем исключение для обработки возможных ошибок при получении номера очереди от пользователя
    try:
        table_data = google_table.read_data()  # Получение Google таблицы
        count = 1  # Счётчик перебора наших активных записей в очередь
        # Цикл, перебирающий все очереди
        for i in range(0, len(table_data["students"])):
            students = table_data["students"][i].split("\n")  # Список пользователей в очереди
            # Цикл, перебирающий всех студентов в очереди
            for k in range(0, len(students)):
                # Проверка на то, есть ли пользователь в очереди или нет
                if " ".join(students[k].split(" ")[1:]) == user["name"]:
                    # Проверка на номер активной очереди и номер, заданный пользователем
                    if count == int(number):
                        students.pop(k)  # Удаление пользователя из общего списка всех пользователей очереди
                        update_students = "\n".join(students)  # Преобразование обновлённого списка в строку
                        # Если список пользователей в очереди пустой, то удалить очередь
                        if update_students == "":
                            google_table.delete_queue(i+2)
                        else:
                            google_table.write_students(i+2, update_students)
                        return "Вы успешно отменили запись!"
                    count += 1

        return "Такого номера с записью не существует!"
    except ValueError:
        return "Введите номер для отмены!"


# Список всех очередей у пользователя
def queue_active_list(user):
    text = ""  # Текст со всеми очередями
    table_data = google_table.read_data()  # Получение Google таблицы
    count = 1  # Номер очереди
    # Цикл, перебирающий все очереди
    for i in range(0, len(table_data["students"])):
        students = table_data["students"][i].split("\n")  # Список пользователей в очереди
        # Цикл, перебирающий всех студентов в очереди
        for k in range(0, len(students)):
            # Проверка на то, есть ли пользователь в очереди или нет
            if " ".join(students[k].split(" ")[1:]) == user["name"]:
                text += f"{count}. {k+1} в очереди " + table_data["subject"][i] + " " + table_data["teacher"][i] + " " + table_data["time"][i] + "\n"
                count += 1
                break
    if text == "":
        return "На данный момент Вы не находитесь не в одной очереди!"
    else:
        return "Список активных очередей: \n" + text


# Досдача пользователем в очереди
def queue_re_add(user, number):
    # Используем исключение для обработки возможных ошибок при получении номера очереди от пользователя
    try:
        table_data = google_table.read_data()  # Получение Google таблицы
        # Проверка на то, что номер очереди существует среди очередей
        if len(table_data["subject"]) > 0 and (0 < int(number) <= len(table_data["subject"])):
            # Цикл, перебирающий всех студентов в очереди
            for name in table_data["students"][int(number)-1].split("\n"):
                # Проверка на то, есть ли пользователь в очереди или нет
                if " ".join(name.split(" ")[1:]) == user["name"]:
                    return "Вы уже есть в этой очереди!"
            students = table_data["students"][int(number) - 1].split("\n")  # Все студенты в данной очереди
            students.insert(0, user["group"] + " " + user["name"])  # Вставка пользователя в начало
            students = "\n".join(students)  # Преобразование списка в строку
            google_table.write_students(int(number) + 1, students)  # Перезапись всех студентов в очередь
            return "Вы добавлены в очередь!"
        else:
            return "Введите номер очереди из списка!"
    except (IndexError, ValueError):
        return "Введите номер очереди из списка!"


# Обработчик сообщений для команды /start
@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id, "👋 Приветствую! Укажите Вашу группу, фамилию и имя.\n"
                                      "Например: 5810 Иванов Иван")


# Обработчик сообщений
@bot.message_handler(content_types='text')
def message_reply(message):
    user = database.users_read(message.chat.id)  # Данные пользователя из БД
    user_message = message.text.lower()  # Сообщение пользователя, приведённое в нижний регистр
    user_id = message.chat.id  # Telegram ID пользователя
    # Если данные пользователя есть в БД, то пропускаем регистрацию
    if user:
        user_message_split = user_message.split(" ")  # Разделение сообщение пользователя по словам
        # Если нахождение пользователя в боте в "create_queue_priority", то ждём сообщение о будущей приоритетности очереди
        if user["location_in_bot"] == "create_queue_priority":
            if user_message == "-":
                database.users_save(user_id, "create_queue", "-_")  # Сохранение у пользователя в БД данных о будущей очереди
                database.users_save(user_id, "location_in_bot", "create_queue_subject")  # Перемещение пользователя в боте
            else:
                database.users_save(user_id, "create_queue", message.text+"_")  # Сохранение у пользователя в БД данных о будущей очереди
                database.users_save(user_id, "location_in_bot", "create_queue_subject")  # Перемещение пользователя в боте
            bot.send_message(user_id, "Введите название предмета")
        # Если нахождение пользователя в боте в "create_queue_subject", то ждём сообщение о будущем предмете очереди
        elif user["location_in_bot"] == "create_queue_subject":
            database.users_save(user_id, "create_queue", user["create_queue"]+message.text+"_")  # Сохранение у пользователя в БД данных о будущей очереди
            database.users_save(user_id, "location_in_bot", "create_queue_teacher")  # Перемещение пользователя в боте
            bot.send_message(user_id, "Введите ФИО преподавателя\n"
                                      "Например: Иванов Иван Иванович")
        # Если нахождение пользователя в боте в "create_queue_teacher", то ждём сообщение о будущеем преподавателе очереди
        elif user["location_in_bot"] == "create_queue_teacher":
            database.users_save(user_id, "create_queue", user["create_queue"] + message.text + "_")  # Сохранение у пользователя в БД данных о будущей очереди
            database.users_save(user_id, "location_in_bot", "create_queue_time")  # Перемещение пользователя в боте
            bot.send_message(user_id, "Введите дату и время начало очереди\n"
                                      "Например: 16.07.2022 16:00")
        # Если нахождение пользователя в боте в "create_queue_time", то ждём сообщение о будущем времени очереди
        elif user["location_in_bot"] == "create_queue_time":
            temp_time = user_message.split(" ")  # Сообщение разделённое на дату и время
            database.users_save(user_id, "create_queue", user["create_queue"] + temp_time[0] + "-" + temp_time[1])  # Сохранение у пользователя в БД данных о будущей очереди
            database.users_save(user_id, "location_in_bot", "menu")  # Перемещение пользователя в боте
            bot.send_message(user_id, queue_create(database.users_read(message.chat.id))) # Создание очереди
        else:
            if user_message == "создать очередь":
                bot.send_message(user_id, "Введите \"-\", если нужна обычная очередь или название группы,"
                                          " если нужна приоритетная очередь")
                database.users_save(user_id, "location_in_bot", "create_queue_priority")  # Перемещение пользователя в боте
            elif user_message == "список очередей":
                bot.send_message(user_id, queue_list())
            elif user_message == "запись в очередь":
                bot.send_message(user_id, "Для записи в очередь:\nЗапись [Номер очереди]")
            elif len(user_message_split) == 2 and user_message_split[0] == "запись":
                bot.send_message(user_id, queue_add(user, user_message_split[1]))
            elif user_message == "отмена записи":
                bot.send_message(user_id, "Для отмены очереди:\nОтмена [Номер очереди]")
            elif len(user_message_split) == 2 and user_message_split[0] == "отмена":
                bot.send_message(user_id, queue_delete(user, user_message_split[1]))
            elif user_message == "просмотр своих записей":
                bot.send_message(user_id, queue_active_list(user))
            elif user_message == "запись на досдачу":
                bot.send_message(user_id, "Для записи на досдачу:\nДосдать [Номер очереди]")
            elif len(user_message_split) == 2 and user_message_split[0] == "досдать":
                bot.send_message(user_id, queue_re_add(user, user_message_split[1]))
            else:
                bot.send_message(user_id, "Меню\nСоздать очередь\nСписок очередей\nЗапись в очередь\n"
                                          "Отмена записи\nПросмотр своих записей", reply_markup=keyboard(user))
    else: # Регистрация пользователя
        user_message_split = message.text.split(" ")  # Разделение сообщение пользователя по словам
        # Если сообщение состоит из 3 и более слов, то регистрируем пользователя в БД
        if len(user_message_split) >= 3:
            # Регистрация в БД
            database.user_register(user_id, " ".join(user_message_split[1:]), user_message_split[0])
            bot.send_message(user_id, "Вы зарегистрировались!")
            bot.send_message(user_id, "Меню\nСоздать очередь\nСписок очередей\nЗапись в очередь\n"
                                      "Отмена записи\nПросмотр своих записей", reply_markup=keyboard(user))
        else:
            bot.send_message(user_id, "Укажите свою группу, фамилию и имя для регистрации!")


if __name__ == '__main__':
    print("Бот запущен.")
    bot.polling(none_stop=True)  # Запуск бота
