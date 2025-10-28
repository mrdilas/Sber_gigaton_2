from gigachat import GigaChat
import os

class GigaChatManager:
    """Класс для управления файлами в GigaChat"""
    
    def __init__(self, credentials, scope="GIGACHAT_API_PERS", verify_ssl_certs=False):
        """
        Инициализация менеджера файлов
        
        Args:
            credentials (str): API токен
            scope (str): Scope для аутентификации
            verify_ssl_certs (bool): Проверять SSL сертификаты
        """
        self.giga = GigaChat(
            credentials=credentials, 
            scope=scope, 
            verify_ssl_certs=verify_ssl_certs
        )
        self._files_cache = None
    
    def get_files(self, force_refresh=False):
        """Получить список всех файлов"""
        if self._files_cache is None or force_refresh:
            self._files_cache = self.giga.get_files()
        return self._files_cache
    
    def get_files_filenames(self):
        """Получить список имен всех файлов"""
        filenames = []
        result = self.get_files()
        for res in result.data:
            filenames.append(res.filename)
        return filenames
    
    def get_files_ids(self):
        """Получить список ID всех файлов"""
        ids = []
        result = self.get_files()
        for res in result.data:
            ids.append(res.id_)
        return ids
    
    def get_file_info_by_id(self, file_id):
        """Получить информацию о файле по ID"""
        return self.giga.get_file(file_id)
    
    def get_file_info_by_name(self, filename):
        """Получить информацию о файле по имени"""
        result = self.get_files()
        for file_info in result.data:
            if file_info.filename == filename:
                return file_info
        return None
    
    def get_file_id_by_name(self, filename):
        """Получить ID файла по имени"""
        file_info = self.get_file_info_by_name(filename)
        return file_info.id if file_info else None
    
    def upload_file(self, filepath):
        """Загрузить файл в GigaChat"""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Файл {filepath} не найден")
        
        with open(filepath, "rb") as file:
            response = self.giga.upload_file(file)
        
        # Обновляем кэш
        self._files_cache = None
        
        return response
    
    def delete_file_by_id(self, file_id):
        """Удалить файл по ID"""
        response = self.giga.delete_file(file_id)
        
        # Обновляем кэш
        self._files_cache = None
        
        return response
    
    def delete_file_by_name(self, filename):
        """Удалить файл по имени"""
        file_id = self.get_file_id_by_name(filename)
        if file_id:
            return self.delete_file_by_id(file_id)
        else:
            raise ValueError(f"Файл с именем {filename} не найден")
    
    def file_exists(self, filename):
        """Проверить существует ли файл с таким именем"""
        return self.get_file_info_by_name(filename) is not None
    
    def get_file_size_by_name(self, filename):
        """Получить размер файла по имени"""
        file_info = self.get_file_info_by_name(filename)
        return file_info.size if file_info else None
    
    def get_file_upload_time_by_name(self, filename):
        """Получить время загрузки файла по имени"""
        file_info = self.get_file_info_by_name(filename)
        return file_info.created_at if file_info else None
    
    def list_files_detailed(self):
        """Получить детальную информацию о всех файлах"""
        files = []
        result = self.get_files()
        for file_info in result.data:
            files.append({
                'id': file_info.id,
                'filename': file_info.filename,
                'size': file_info.size,
                'created_at': file_info.created_at,
                'purpose': file_info.purpose
            })
        return files
    
    def upload_multiple_files(self, filepaths):
        """Загрузить несколько файлов"""
        responses = []
        for filepath in filepaths:
            try:
                response = self.upload_file(filepath)
                responses.append({
                    'filename': os.path.basename(filepath),
                    'status': 'success',
                    'response': response
                })
            except Exception as e:
                responses.append({
                    'filename': os.path.basename(filepath),
                    'status': 'error',
                    'error': str(e)
                })
        return responses
    
    def delete_all_files(self):
        """Удалить все файлы"""
        file_ids = self.get_files_ids()
        results = []
        
        for file_id in file_ids:
            try:
                response = self.delete_file_by_id(file_id)
                results.append({
                    'file_id': file_id,
                    'status': 'deleted'
                })
            except Exception as e:
                results.append({
                    'file_id': file_id,
                    'status': 'error',
                    'error': str(e)
                })
        
        return results
    
    def get_total_files_size(self):
        """Получить общий размер всех файлов"""
        total_size = 0
        result = self.get_files()
        for file_info in result.data:
            total_size += file_info.size
        return total_size
    
    def refresh_cache(self):
        """Принудительно обновить кэш файлов"""
        self._files_cache = None
        return self.get_files()
    
    def get_file_count(self):
        """Получить количество файлов"""
        return len(self.get_files_ids())
    
    def search_files_by_pattern(self, pattern):
        """Найти файлы по шаблону в имени"""
        filenames = self.get_files_filenames()
        matching_files = [name for name in filenames if pattern.lower() in name.lower()]
        return matching_files
    
    def ask_according_to_material(self, message: str):
        """Получить ответ на вопрос с привязкой к материалу"""
        
        # Читаем промпт из файла
        try:
            with open("PROMPT_WHO_ARE_YOU.txt", "r", encoding="utf-8") as file:
                prompt_template = file.read()
        except FileNotFoundError:
            raise FileNotFoundError("Файл PROMPT_WHO_ARE_YOU.txt не найден")
        except Exception as e:
            raise Exception(f"Ошибка при чтении файла: {e}")
        
        # Форматируем промпт с сообщением пользователя
        prompt = prompt_template.format(message=message)
        print(f"Запрос пользователя: \n{prompt}")
        result = []
        print(self.get_files_ids())
        for file in self.get_files_ids():
            result.append(self.giga.chat({
                "messages": [
                    {
                        "role": "user",
                        "content": prompt,
                        "attachments": [file],
                    }
                ],
                "temperature": 0.7,
                "max_tokens": 600
            }))
            print(result)
        return result
    
'''
giga = GigaChatManager("MDE5OWM5OGUtMDI3MC03ZGM4LWIyMjItODMyMjE3YjllZjFlOjEzMmUzZTg5LTU2ZTgtNDA2NS1hZmFhLTcwM2FmZTRjMzA2Ng==")

print(giga.get_files_filenames())
giga.delete_all_files()
giga.upload_file("44FZ.pdf")
giga.upload_file("223FZ.pdf")
print(giga.get_files_filenames())
'''
