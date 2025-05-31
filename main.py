def clean_file(input_file_path, output_file_path=None):
    chars_to_replace = ['°', '\u202F', '\u00A0']
    replacement_char = ' '
    if output_file_path is None:
        import os
        base, ext = os.path.splitext(input_file_path)
        output_file_path = f"{base}_cleaned{ext}"
    
    try:
        with open(input_file_path, 'r', encoding='utf-8') as infile:
            content = infile.read()
        modified_content = content
        replacements_count = 0
        for char in chars_to_replace:
            if char in modified_content:
                replacements_count += modified_content.count(char)
                modified_content = modified_content.replace(char, replacement_char)
        with open(output_file_path, 'w', encoding='utf-8') as outfile:
            outfile.write(modified_content) 
        print(f"Файл успешно очищен. Произведено замен: {replacements_count}")
        print(f"Результат сохранен в: {output_file_path}")
    except Exception as e:
        print(f"Ошибка при обработке файла: {str(e)}")

if __name__ == '__main__':
    input_file = "text.txt"  # Ваш исходный файл
    clean_file(input_file)
