####by morax
import openpyxl
import string

alphabet = 'АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯабвгдеёжзийклмнопрстуфхцчшщъыьэюяABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz1234567890-.'
#------------------------------------------
# 1 функция считывания данных
#------------------------------------------
def read_excel_data(filename, sheet_name):
    """ Считывает данные из таблицы Excel и возвращает список словарей. """
    workbook = openpyxl.load_workbook(filename)
    worksheet = workbook[sheet_name]
    
    data = []
    
    for row in worksheet.iter_rows(min_row=2):
        row_data = {}
        for i, cell in enumerate(row):
            row_data[worksheet.cell(row=1, column=i + 1).value] = cell.value
        data.append(row_data)
    
    return data

#------------------------------------------
# 2 Генерация ключа
#------------------------------------------
def keyx(raw: str, col: str):
    x = int(raw + col)
    while x > 130:
        x = x - 130
    return str(x)

#------------------------------------------
# 3 Функция шифрования Виженера
#------------------------------------------
def encrypt(txt: str, key: int):
    res = ''
    for el in txt:
        if el in alphabet:
            res+=alphabet[(alphabet.index(el)+key)% len(alphabet)]
        else:
            res += el
        return res
def vigenere_encrypt(text, key):
    cipher_text = ''
    k=0
    for i in range(len(text)):
        key_code = alphabet.index(key[k % len(key)])
        cipher_text += encrypt(text[i], key_code)
        if text[i] in alphabet:
            k+=1
    return cipher_text
#------------------------------------------
# 4 Функция дешифрования Виженера
#------------------------------------------
def decrypt(txt: str, key: int):
    res = ''
    for el in txt:
        if el in alphabet:
            res += alphabet[(alphabet.index(el) - key) % len(alphabet)]
        else:
            res += el
    return res

def vigenere_decrypt(ciphertext: str, key: str):
    text = ''
    key_length = len(key)
    k = 0
    for i in range(len(ciphertext)):
        if ciphertext[i] in alphabet:
            key_code = alphabet.index(key[k % key_length])
            text += decrypt(ciphertext[i], key_code)
            k += 1
    return text
#------------------------------------------
# 5 Запись зашифрованных данных в Excel
#------------------------------------------
def write_encrypted_data(data, filename):
    new_workbook = openpyxl.Workbook()
    new_worksheet = new_workbook.active
    new_worksheet.title = "Лист1"
    # Запись заголовков
    for i, header in enumerate(data[0].keys()):
        new_worksheet.cell(row=1, column=i + 1).value = header
    
    # Запись зашифрованных данных
    for row_num, row_data in enumerate(data, start=2):
        for col_num, value in enumerate(row_data.values(), start=1):
            encrypted_value = vigenere_encrypt(str(value), keyx(str(row_num), str(col_num)))  # Шифруем значение
            new_worksheet.cell(row=row_num, column=col_num).value = encrypted_value
            print(keyx(str(row_num), str(col_num)), " ",encrypted_value)
    
    new_workbook.save(filename)  # Сохраняем файл

#------------------------------------------
# 6 Запись расшифрованных данных в Excel
#------------------------------------------ 
def write_decrypted_data(data, filename):
    new_workbook = openpyxl.Workbook()
    new_worksheet = new_workbook.active
    new_worksheet.title = "Лист1"
    
    # Запись заголовков
    for i, header in enumerate(data[0].keys()):
        new_worksheet.cell(row=1, column=i + 1).value = header
    
    # Запись расшифрованных данных
    for row_num, row_data in enumerate(data, start=2):
        for col_num, value in enumerate(row_data.values(), start=1):
            decrypted_value = vigenere_decrypt(str(value), keyx(str(row_num), str(col_num)))  # Дешифруем значение
            new_worksheet.cell(row=row_num, column=col_num).value = decrypted_value  # Записываем расшифрованное значение
            print(keyx(str(row_num), str(col_num)), " ",decrypted_value)
    new_workbook.save(filename)  # Сохраняем файл
#------------------------------------------
# 7 Основная логика программы
#------------------------------------------
def main():
    choice = input("Введите 1 для шифрования или 2 для расшифровки: ")
    
    if choice == '1':
        filename = 'data.xlsx'
        sheet_name = 'Лист1'
        data = read_excel_data(filename, sheet_name)  # Считываем данные из Excel
        write_encrypted_data(data, 'encrypted_data.xlsx')  # Запись зашифрованных данных в новый файл
        print("Данные успешно зашифрованы и сохранены в 'encrypted_data.xlsx'.")

    elif choice == '2':
        encrypted_filename = 'encrypted_data.xlsx'
        sheet_name = 'Лист1'
        encrypted_data = read_excel_data(encrypted_filename, sheet_name)  # Считываем зашифрованные данные
        decrypted_data = []        
        write_decrypted_data(encrypted_data, 'decrypted_data.xlsx')  # Запись расшифрованных данных в новый файл
        print("Данные успешно расшифрованы и сохранены в 'decrypted_data.xlsx'.")

    else:
        print("Выберите правильный номер функции!")

if __name__ == '__main__':
    main()
