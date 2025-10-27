from gigachat import GigaChat

API_TOKEN = 'MDE5OTlhYjktYzA5My03ZjQzLTk1OTMtMzI5NzVmYTA0OWMyOjJlYjNkOWYxLWFmMTYtNGRlMy04ODQ2LWY2MTk0OWU4ODhjZQ=='

class File:
    def __init__(self, index: int, id: str, fullname: str):
        self.index = index
        self.id = id
        self.fullname = fullname

    def __repr__(self):
        return f"File(index={self.index}, id='{self.id}', fullname='{self.fullname}')"

class GigaChatManager:
    def __init__(self, api_token: str):
        self.giga = GigaChat(
            credentials=api_token,
            verify_ssl_certs=False,
        )
        self._files_cache = None

    def _get_files_data(self):
        if self._files_cache is None:
            self._files_cache = self.giga.get_files()
        return self._files_cache

    @property
    def files(self) -> list[File]:
        return [
            File(index, data.id_, data.filename)
            for index, data in enumerate(self._get_files_data().data)
        ]

    def delete_all_files(self):
        print("🗑️ Удаление всех файлов из GigaChat...")
        files_count = len(self.files)
        for i, file in enumerate(self.files, 1):
            print(f"Удаление файла {i}/{files_count}: {file.fullname}")
            self.giga.delete_file(file.id)
        self._files_cache = None
        print("✅ Все файлы удалены")

    def delete_file_by_id(self, file_id: str):
        self.giga.delete_file(file_id)
        self._files_cache = None

    def get_balance(self):
        table_data = []
        for balance_item in self.giga.get_balance().balance:
            table_data.append([balance_item.usage, f"{balance_item.value:,.0f}"])
        print("Баланс:")
        return table_data
    
    def upload_file(self, file_path: str):
        print(f"📤 Загрузка файла в GigaChat: {file_path}")
        
        with open(file_path, "rb") as file:
            self.giga.upload_file(file)
        self._files_cache = None
        print(f"✅ Файл успешно загружен в GigaChat")

    def ask_according_to_material(self, message: str, material_id: str):
        prompt = f"""Ты эксперт в сфере гражданских прав и свобод, "
                    "а также хорошо знакомы законы, кодексы и подзаконные акты РФ. Тебе необходимо сформулировать ответ на"
                    "вопрос пользователя, основанный на документах, действующих на территории РФ. Вот вопрос пользователя:"
                     + {message} + "."
                     "Ответ необходимо сформулировать граммотно, а также указать в виде списка, на каких документах (законах)"
                     "РФ основан ответ/консультация.

Ответь технически грамотно в таком формате:
## Консультация по вашему вопросу
Здесь должна быть описана ваша ситуация, грамотно с юридической точки зрения
Пример структуры ответа
### Законы, являющиеся основаниями ответственности
1. K1-ый кодекс РФ - тут должны быть перечисленны связи с нашим вопросом
> Cтатья 1 - её описание, основанное на вопросе вопроса пользователя
...
> Cтатья n - её описание, основанное на вопросе вопроса пользователя
2. K2-ый кодекс РФ - тут должны быть перечисленны связи с нашим вопросом
> Cтатья 1 - её описание, основанное на вопросе вопроса пользователя
...
> Cтатья j - её описание, основанное на вопросе вопроса пользователя
...
m. Km-ый кодекс РФ - тут должны быть перечисленны связи с нашим вопросом
> Cтатья 1 - её описание, основанное на вопросе вопроса пользователя
...
> Cтатья p - её описание, основанное на вопросе вопроса пользователя
### Ваши действия (потенциально возможные)
1. Действие 1
2. Действие 2
3. Действие 3

В конце должно быть написано Данный ответ сгенерирован нейросетью и не призывает Вас действовать, основываясь на данных рекомендациях."""

        result = self.giga.chat({
            "messages": [
                {
                    "role": "assistant",
                    "content": prompt,
                    "attachments": [material_id],
                    
                }
            ],
            "temperature": 0.7,
            "max_tokens": 400
        })
        return result
    
