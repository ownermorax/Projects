import os
import json
from PIL import Image, ExifTags
from PyPDF2 import PdfReader
from docx import Document
from datetime import datetime
import zipfile
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL.ExifTags import TAGS, GPSTAGS

class MetadataAnalyzer:
    def __init__(self):
        self.supported_formats = {
            'images': ['.jpg', '.jpeg', '.png', '.tiff', '.webp'],
            'pdf': ['.pdf'],
            'docx': ['.docx'],
            'zip': ['.zip']
        }
        
        self.important_exif_tags = {
            'Make': 'Производитель',
            'Model': 'Модель',
            'DateTime': 'Дата съемки',
            'ExposureTime': 'Выдержка',
            'FNumber': 'Диафрагма',
            'ISOSpeedRatings': 'ISO',
            'FocalLength': 'Фокусное расстояние',
            'LensModel': 'Объектив',
            'Artist': 'Автор',
            'Copyright': 'Авторские права',
            'GPSInfo': 'Координаты GPS'
        }

    def get_file_metadata(self, file_path):
        try:
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if file_ext in self.supported_formats['images']:
                return self._get_image_metadata(file_path)
            elif file_ext in self.supported_formats['pdf']:
                return self._get_pdf_metadata(file_path)
            elif file_ext in self.supported_formats['docx']:
                return self._get_docx_metadata(file_path)
            elif file_ext in self.supported_formats['zip']:
                return self._get_zip_metadata(file_path)
            else:
                return {"error": "Неподдерживаемый формат файла"}
        except Exception as e:
            return {"error": f"Ошибка обработки: {str(e)}"}

    def _get_image_metadata(self, file_path):
        try:
            metadata = {}
            with Image.open(file_path) as img:
                metadata['basic'] = {
                    'Тип': img.format,
                    'Размер': f"{img.size[0]}×{img.size[1]} пикселей",
                    'Цветовая модель': img.mode
                }
                
                exif_data = self._get_filtered_exif(img)
                if exif_data:
                    metadata['exif'] = exif_data
            
            self._add_system_metadata(file_path, metadata)
            return metadata
        except Exception as e:
            return {"error": f"Ошибка обработки изображения: {str(e)}"}

    def _get_filtered_exif(self, img):
        exif = {}
        try:
            if hasattr(img, '_getexif') and img._getexif() is not None:
                raw_exif = img._getexif()
                if raw_exif:
                    for tag_id, value in raw_exif.items():
                        tag_name = TAGS.get(tag_id, tag_id)
                        if tag_name in self.important_exif_tags:
                            cleaned = self._clean_exif_value(value, tag_name)
                            if cleaned:
                                exif[self.important_exif_tags[tag_name]] = cleaned
            
            if 'Координаты GPS' in exif and isinstance(exif['Координаты GPS'], dict):
                gps_data = self._parse_gps(exif['Координаты GPS'])
                if gps_data:
                    exif['Координаты GPS'] = gps_data
            
            return exif if exif else None
        except Exception as e:
            return {"exif_error": str(e)}

    def _clean_exif_value(self, value, tag_name):
        if value is None:
            return None
            
        if tag_name == 'FNumber':
            return f"f/{float(value[0])/value[1]:.1f}" if isinstance(value, tuple) else f"f/{value}"
        elif tag_name == 'ExposureTime':
            if isinstance(value, tuple):
                return f"{value[0]}/{value[1]} сек" if value[0] != 1 else f"1/{value[1]} сек"
            return f"{value} сек"
        elif tag_name == 'FocalLength':
            return f"{int(value[0]/value[1])} мм" if isinstance(value, tuple) else f"{value} мм"
        elif tag_name == 'DateTime':
            return value.replace(':', '-', 2)
        elif isinstance(value, bytes):
            return value.decode('utf-8', errors='ignore').strip()
        elif isinstance(value, (tuple, list)):
            return ', '.join(str(v) for v in value)
        else:
            return str(value)

    def _parse_gps(self, gps_info):
        if not isinstance(gps_info, dict):
            return "Неверный формат GPS данных"
        
        required_tags = {
            1: 'GPSLatitudeRef',  
            2: 'GPSLatitude',    
            3: 'GPSLongitudeRef', 
            4: 'GPSLongitude' 
        }
        
        missing_tags = []
        for tag_id, tag_name in required_tags.items():
            if tag_id not in gps_info:
                missing_tags.append(tag_name)
        
        if missing_tags:
            return f"Отсутствуют GPS теги: {', '.join(missing_tags)}"
        
        try:
            lat_ref = gps_info[1]  
            lat = gps_info[2]     
            
            lon_ref = gps_info[3]  
            lon = gps_info[4]      
            
            lat_dec = self._convert_dms_to_decimal(lat, lat_ref)
            lon_dec = self._convert_dms_to_decimal(lon, lon_ref)
            
            if lat_dec is None or lon_dec is None:
                return "Не удалось конвертировать координаты"
            
            return (
                f"Широта: {self._format_dms(lat, lat_ref)}\n"
                f"Долгота: {self._format_dms(lon, lon_ref)}\n"
                f"Десятичные градусы: {lat_dec:.6f}, {lon_dec:.6f}\n"
                f"Ссылка на карты: https://www.google.com/maps?q={lat_dec},{lon_dec}"
            )
        except Exception as e:
            return f"Ошибка обработки GPS: {str(e)}"

    def _convert_dms_to_decimal(self, dms, ref):
        try:
            degrees = dms[0][0] / dms[0][1]
            minutes = dms[1][0] / dms[1][1]
            seconds = dms[2][0] / dms[2][1]
            
            decimal = degrees + (minutes / 60) + (seconds / 3600)
            
            if ref in ['S', 'W']:
                decimal = -decimal
                
            return decimal
        except:
            return None

    def _format_dms(self, dms, ref):
        try:
            degrees = int(dms[0][0] / dms[0][1])
            minutes = int(dms[1][0] / dms[1][1])
            seconds = dms[2][0] / dms[2][1]
            
            return f"{degrees}° {minutes}' {seconds:.2f}\" {ref}"
        except:
            return "Некорректные данные"

    def _get_pdf_metadata(self, file_path):
        try:
            metadata = {}
            with open(file_path, 'rb') as f:
                pdf = PdfReader(f)
                
                if hasattr(pdf, 'metadata') and pdf.metadata:
                    clean_meta = {
                        'Название': pdf.metadata.get('/Title'),
                        'Автор': pdf.metadata.get('/Author'),
                        'Создатель': pdf.metadata.get('/Creator'),
                        'Дата создания': pdf.metadata.get('/CreationDate'),
                        'Дата изменения': pdf.metadata.get('/ModDate')
                    }
                    metadata['pdf_info'] = {k: v for k, v in clean_meta.items() if v}
                
                metadata['Страниц'] = len(pdf.pages)
                metadata['Зашифрован'] = 'Да' if pdf.is_encrypted else 'Нет'
            
            self._add_system_metadata(file_path, metadata)
            return metadata
        except Exception as e:
            return {"error": f"Ошибка обработки PDF: {str(e)}"}

    def _get_docx_metadata(self, file_path):
        try:
            metadata = {}
            doc = Document(file_path)
            props = doc.core_properties
            
            doc_meta = {
                'Название': props.title,
                'Автор': props.author,
                'Создан': str(props.created) if props.created else None,
                'Изменен': str(props.modified) if props.modified else None,
                'Редактор': props.last_modified_by,
                'Версия': props.revision,
                'Тема': props.subject,
                'Ключевые слова': props.keywords
            }
            
            metadata['docx_info'] = {k: v for k, v in doc_meta.items() if v}
            self._add_system_metadata(file_path, metadata)
            return metadata
        except Exception as e:
            return {"error": f"Ошибка обработки DOCX: {str(e)}"}

    def _get_zip_metadata(self, file_path):
        try:
            metadata = {}
            with zipfile.ZipFile(file_path, 'r') as zipf:
                files = []
                for info in zipf.infolist():
                    files.append({
                        'Файл': info.filename,
                        'Размер': f"{info.file_size/1024:.1f} KB",
                        'Сжатый размер': f"{info.compress_size/1024:.1f} KB",
                        'Дата': f"{info.date_time[2]}.{info.date_time[1]}.{info.date_time[0]}"
                    })
                metadata['files'] = files[:10]
                if len(files) > 10:
                    metadata['files'].append(f"... и еще {len(files)-10} файлов")
            
            self._add_system_metadata(file_path, metadata)
            return metadata
        except Exception as e:
            return {"error": f"Ошибка обработки ZIP: {str(e)}"}

    def _add_system_metadata(self, file_path, metadata):
        try:
            stat = os.stat(file_path)
            metadata['system_info'] = {
                'Имя файла': os.path.basename(file_path),
                'Размер': f"{stat.st_size/1024:.1f} KB",
                'Создан': datetime.fromtimestamp(stat.st_ctime).strftime('%d.%m.%Y %H:%M'),
                'Изменен': datetime.fromtimestamp(stat.st_mtime).strftime('%d.%m.%Y %H:%M')
            }
        except Exception as e:
            metadata['system_info_error'] = str(e)

    def save_metadata_to_file(self, metadata, output_path):
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Ошибка сохранения: {e}")
            return False

class MetadataAnalyzerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Анализатор метаданных")
        self.root.geometry("900x700")
        self.analyzer = MetadataAnalyzer()
        
        self.setup_ui()
        self.center_window()

    def center_window(self):
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.X, pady=5)
        
        self.select_btn = ttk.Button(top_frame, text="Выбрать файл", command=self.select_file)
        self.select_btn.pack(side=tk.LEFT, padx=5)
        
        self.save_btn = ttk.Button(top_frame, text="Сохранить метаданные", command=self.save_metadata, state=tk.DISABLED)
        self.save_btn.pack(side=tk.LEFT, padx=5)
        
        self.clear_btn = ttk.Button(top_frame, text="Очистить", command=self.clear_results)
        self.clear_btn.pack(side=tk.LEFT, padx=5)
        
        options_frame = ttk.Frame(top_frame)
        options_frame.pack(side=tk.RIGHT, padx=5)
        
        self.raw_data_var = tk.BooleanVar(value=False)
        self.raw_data_cb = ttk.Checkbutton(
            options_frame, text="Сырые данные", variable=self.raw_data_var,
            command=self.toggle_raw_data)
        self.raw_data_cb.pack(side=tk.RIGHT)
        
        result_frame = ttk.Frame(main_frame)
        result_frame.pack(fill=tk.BOTH, expand=True)
        
        self.result_text = tk.Text(
            result_frame, wrap=tk.WORD, font=('Consolas', 10),
            padx=5, pady=5)
        self.result_text.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(self.result_text)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.result_text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.result_text.yview)
        
        self.status_var = tk.StringVar()
        self.status_var.set("Готов к работе")
        status_bar = ttk.Label(
            self.root, textvariable=self.status_var, 
            relief=tk.SUNKEN, padding=(5, 2))
        status_bar.pack(fill=tk.X)

    def select_file(self):
        file_path = filedialog.askopenfilename(
            title="Выберите файл",
            filetypes=[
                ("Изображения", "*.jpg *.jpeg *.png *.tiff *.webp"),
                ("PDF документы", "*.pdf"),
                ("Word документы", "*.docx"),
                ("ZIP архивы", "*.zip"),
                ("Все файлы", "*.*")
            ]
        )
        
        if file_path:
            self.analyze_file(file_path)

    def analyze_file(self, file_path):
        self.result_text.delete(1.0, tk.END)
        self.status_var.set(f"Анализ {os.path.basename(file_path)}...")
        self.root.update()
        
        try:
            metadata = self.analyzer.get_file_metadata(file_path)
            
            if 'error' in metadata:
                self.result_text.insert(tk.END, f"Ошибка: {metadata['error']}")
                self.status_var.set("Ошибка анализа")
            else:
                if self.raw_data_var.get():
                    display_text = json.dumps(metadata, indent=4, ensure_ascii=False)
                else:
                    display_text = self._format_metadata(metadata)
                
                self.result_text.insert(tk.END, display_text)
                self.current_metadata = metadata
                self.save_btn.config(state=tk.NORMAL)
                self.status_var.set(f"Анализ завершен: {os.path.basename(file_path)}")
                
        except Exception as e:
            self.result_text.insert(tk.END, f"Ошибка: {str(e)}")
            self.status_var.set("Ошибка анализа")

    def _format_metadata(self, metadata):
        sections = []
        
        if 'system_info' in metadata:
            sys_info = metadata['system_info']
            sections.append("=== ОСНОВНАЯ ИНФОРМАЦИЯ ===")
            sections.extend(f"{k}: {v}" for k, v in sys_info.items())
            sections.append("")
        
        if 'basic' in metadata:
            sections.append("=== ХАРАКТЕРИСТИКИ ФАЙЛА ===")
            sections.extend(f"{k}: {v}" for k, v in metadata['basic'].items())
            sections.append("")
        
        if 'exif' in metadata and metadata['exif']:
            sections.append("=== МЕТАДАННЫЕ ===")
            for k, v in metadata['exif'].items():
                if k == 'Координаты GPS':
                    sections.append(f"{k}:\n{v}")
                else:
                    sections.append(f"{k}: {v}")
            sections.append("")
        
        for doc_type in ['pdf_info', 'docx_info']:
            if doc_type in metadata and metadata[doc_type]:
                sections.append(f"=== ИНФОРМАЦИЯ О ДОКУМЕНТЕ ===")
                sections.extend(f"{k}: {v}" for k, v in metadata[doc_type].items())
                sections.append("")
        
        if 'files' in metadata:
            sections.append("=== СОДЕРЖИМОЕ АРХИВА ===")
            for file_info in metadata['files']:
                if isinstance(file_info, dict):
                    sections.extend(f"{k}: {v}" for k, v in file_info.items())
                else:
                    sections.append(str(file_info))
                sections.append("")
        
        return "\n".join(sections)

    def toggle_raw_data(self):
        if hasattr(self, 'current_metadata'):
            self.analyze_file(self.current_metadata['system_info']['Имя файла'])

    def save_metadata(self):
        if hasattr(self, 'current_metadata'):
            output_path = filedialog.asksaveasfilename(
                title="Сохранить метаданные",
                defaultextension=".json",
                filetypes=[("JSON файлы", "*.json"), ("Все файлы", "*.*")]
            )
            
            if output_path:
                success = self.analyzer.save_metadata_to_file(
                    self.current_metadata, output_path)
                
                if success:
                    messagebox.showinfo("Успешно", "Метаданные сохранены")
                    self.status_var.set(f"Сохранено: {os.path.basename(output_path)}")
                else:
                    messagebox.showerror("Ошибка", "Не удалось сохранить")
                    self.status_var.set("Ошибка сохранения")

    def clear_results(self):
        self.result_text.delete(1.0, tk.END)
        if hasattr(self, 'current_metadata'):
            del self.current_metadata
        self.save_btn.config(state=tk.DISABLED)
        self.status_var.set("Готов к работе")

def main():
    root = tk.Tk()
    app = MetadataAnalyzerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
