import requests
import sys
from datetime import datetime

# Данные авторизации в API Trello
auth_params = {
    'key': "ВАШ KEY",
    'token': "ВАШ TOKEN", }
# Адрес, на котором расположен API Trello, # Именно туда мы будем отправлять HTTP запросы.
base_url = "https://api.trello.com/1/{}"

board_id = "ВАШ ID"


def read():
    # Получим данные всех колонок на доске:
    column_data = requests.get(base_url.format('boards') + '/' + board_id + '/lists', params=auth_params).json()
    # Теперь выведем название каждой колонки и всех заданий, которые к ней относятся:
    for column in column_data:
        # Получим данные всех задач в колонке и перечислим все названия
        task_data = requests.get(base_url.format('lists') + '/' + column['id'] + '/cards', params=auth_params).json()
        # Имя колонки с количеством задач
        name_with_task_quantity = column['name'] + " (" + str(len(task_data)) + ")"
        print(name_with_task_quantity)
        if not task_data:
            print('\t' + 'Нет задач!')
            continue
        for task in task_data:
            print('\t' + task['name'] + '   ' + " ID: {}".format(task['id']))


def create(name, column_name):
    # Получим данные всех колонок на доске
    column_data = requests.get(base_url.format('boards') + '/' + board_id + '/lists', params=auth_params).json()
    # есть ли колонка column_name
    column_is_exist = False
    # Переберём данные обо всех колонках, пока не найдём ту колонку, которая нам нужна
    for column in column_data:
        if column['name'] == column_name:
            # Создадим задачу с именем _name_ в найденной колонке
            requests.post(base_url.format('cards'), data={'name': name, 'idList': column['id'], **auth_params})
            column_is_exist = True
            break
    # Если колонки нет, создаем ее и вызываем create заново
    if not column_is_exist:
        create_list(column_name)
        create(name, column_name)

def move(name, column_name):
    # Список всех задач с именем name в исходных колонках и количество одноименных задач в целевой колонке
    task_list, already_have = find_all_tasks(name, column_name)
    # Если задачи для перемещения не найдены, информируем об этом
    if len(task_list) == 0:
        print("Нет задач для перемещения.")
        # Если в целевой колонке уже есть одноименные задачи, информируем об этом
        if already_have:
            print('В колонке "{}" уже есть "{}" одноименные задачи.'.format(column_name, already_have))

    elif len(task_list) == 1:
        if already_have:
            print('В колонке "{}" уже есть "{}" одноименные задачи. Перемещаю.'.format(column_name, already_have))
        move_selected_task(task_list[0]['id'], column_name)
    else:
        print('Найдено больше одной задачи с именем "{}".'.format(name))
        n = 1
        for task in task_list:
            print('{}. Колонка "{}". ID {}. Дата последней активности {}.'.format(n, task['list_name'], task['id'], task['time']))
            n += 1
        if already_have:
            print('В колонке "{}" уже есть {} одноименные задачи.'.format(column_name, already_have))
        print("")
        choice = int(input("Выберете порядковый номер из списка: "))
        # Перемещаем задачу с выбранным id
        move_selected_task(task_list[choice - 1]['id'], column_name)


def find_all_tasks(name, column_name):
    # Составляем список всех одноименных задач в исходных колонках
    # и считаем количество одноименных задач в целевой колонке
    all_cards = requests.get(base_url.format('boards') + '/' + board_id + '/cards', params=auth_params).json()
    duplicated_cards = []
    already_have = 0  # Количество одноименных задач в целевой колонке
    for card in all_cards:
        if card['name'] == name:
            # узнаем, в какой колонке задача
            card_list = requests.get(base_url.format('cards') + '/' + card['id'] + '/list', params=auth_params).json()
            if card_list["name"] == column_name:  # если задача в целевой колонке, учитываем ее,
                # но для выбора она будет недоступна
                already_have += 1
                continue
            card_data = {
                'id': card['id'],
                'list_name': card_list["name"],
                'time': card['dateLastActivity']
            }
            duplicated_cards.append(card_data)

    return duplicated_cards, already_have


# Перемещение выбранной задачи
def move_selected_task(task_id, column_name):
    # Теперь, когда у нас есть id задачи, которую мы хотим переместить
    # Переберём данные обо всех колонках, пока не найдём ту, в которую мы будем перемещать задачу
    column_data = requests.get(base_url.format('boards') + '/' + board_id + '/lists', params=auth_params).json()
    # есть ли колонка column_name
    column_is_exist = False
    for column in column_data:
        if column['name'] == column_name:
            # И выполним запрос к API для перемещения задачи в нужную колонку
            requests.put(base_url.format('cards') + '/' + task_id + '/idList',
                         data={'value': column['id'], **auth_params})
            column_is_exist = True
            break
    # Если колонки нет, создаем ее и вызываем create заново
    if not column_is_exist:
        create_list(column_name)
        move_selected_task(task_id, column_name)


# Создание колонки
def create_list(name):
    # Проверка на существование одноименной колонки
    column_data = requests.get(base_url.format('boards') + '/' + board_id + '/lists', params=auth_params).json()
    is_exist = False
    for column in column_data:
        if column['name'] == name:
            is_exist = True
    if is_exist:
        print("Такая колонка уже есть")

    else:
        id_board = (requests.get(base_url.format('boards') + '/' + board_id, params=auth_params).json())['id']
        requests.post(base_url.format('lists'), data={'name': name, 'idBoard': id_board, **auth_params})
        print("Новая колонка создана")



# Переименование колонки
def rename_list(name, new_name):
    column_data = requests.get(base_url.format('boards') + '/' + board_id + '/lists', params=auth_params).json()
    for column in column_data:
        if column['name'] == name:
            # Переименовываем колонку
            requests.put(base_url.format('lists') + '/' + column["id"], data={'name': new_name, **auth_params})
            break
    read()


# Удаление колонки
def delete_list(name):
    column_data = requests.get(base_url.format('boards') + '/' + board_id + '/lists', params=auth_params).json()
    for column in column_data:
        if column['name'] == name:
            # Арихивируем колонку
            requests.put(base_url.format('lists') + '/' + column["id"] + "/closed",
                         data={'value': 'true', **auth_params})
            break
    read()


if __name__ == "__main__":
    if len(sys.argv) <= 2:
        read()
    elif sys.argv[1] == 'create':
        create(sys.argv[2], sys.argv[3])
    elif sys.argv[1] == 'move':
        move(sys.argv[2], sys.argv[3])
    elif sys.argv[1] == 'createList':
        create_list(sys.argv[2])
    elif sys.argv[1] == 'renameList':
        rename_list(sys.argv[2], sys.argv[3])
    elif sys.argv[1] == 'deleteList':
        delete_list(sys.argv[2])
