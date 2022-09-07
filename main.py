import os.path
from googleapiclient.discovery import build
from google.oauth2 import service_account


SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SERVICE_ACCOUNT_FILE = os.path.join(BASE_DIR, 'credentials.json')
credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build('sheets', 'v4', credentials=credentials).spreadsheets().values()
spreadsheet_id = '1zU3Bzgeq5L5T7PYYASGhQlQtFas3mjdch10gL2R61hA'


def create_queue():
    group_num = input('Введите номер группы: ')
    task = input('Введите название предмета: ')
    proffesor = input('Введите имя преподавателя: ')
    time = input('Введите время: ')
    info = f'{task}-{proffesor}-{time}'
    req = service.update(spreadsheetId=spreadsheet_id,
                         range=f'{group_num}!A1:A',
                         valueInputOption='USER_ENTERED',
                         body={'values': [[info]]}).execute()
    student_name = input('Введите ваше имя: ')
    # The ID and range of a spreadsheet.
    range_ = f'{group_num}!A2:E'
    array = {'values': [[student_name]]}
    response = service.append(spreadsheetId=spreadsheet_id,
                              range=range_,
                              valueInputOption='USER_ENTERED',
                              body=array).execute()

def add():
    group_num = input('Введите номер группы: ')
    student_name = input('Введите ваше имя: ')
    range_ = f'{group_num}!A2:E'
    array = {'values': [[student_name]]}
    response = service.append(spreadsheetId=spreadsheet_id,
                              range=range_,
                              valueInputOption='USER_ENTERED',
                              body=array).execute()

def view_queues(): #Call the Sheets API
    group_num = input('Введите номер группы: ')
    #range_ = group_num
    result = service.get(spreadsheetId=spreadsheet_id,
                         range=f'{group_num}').execute()

    data_from_sheet = result.get('values', [])
    print(data_from_sheet)


def active_entries():
    student_name = input('Введите ваше имя: ')
    result = service.batchGet(spreadsheetId=spreadsheet_id,
                         ranges=['4931','4932','4933','4936']).execute()

    result = result['valueRanges']
    for elem in result:
        if student_name in [x for y in elem['values'] for x in y]:
            print([elem['range'].split('!')[0].replace("'", ''), elem['values'][0][0], student_name])

def delete_student():
    group_num = input('Введите номер группы: ')
    student_name = input('Введите ваше имя: ')
    result = service.get(spreadsheetId=spreadsheet_id,
                         range=f'{group_num}').execute()
    data_from_sheet = result.get('values', [])
    data = []
    for i in data_from_sheet:
        for item in i:
            data.append(item)
    data.remove(student_name)
    data = [[el] for el in data]
    data.append([''])
    results = service.update(spreadsheetId=spreadsheet_id,
                         range=f'{group_num}!A1:A',
                         valueInputOption='USER_ENTERED',
                         body={'values': data}).execute()
    print(data)

def main():
    while True:
        menu = input('1. Создать очередь\n2. Вступить в очередь\n3. Посмотреть очередь\n4. Выйти из очереди\n5. Просмотр активный записей\n0. Выход\nВыберите: ')
        if menu == '1':
            create_queue()
        elif menu == '2':
            add()
        elif menu == '3':
            view_queues()
        elif menu == '4':
            delete_student()
        elif menu == '5':
            active_entries()
        elif menu == '0':
            return

if __name__ == '__main__':
     main()