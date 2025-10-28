from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional
import os
import tempfile
import pdfplumber
from docx import Document
from filework import GigaChatManager  # Импортируем ваш класс

app = FastAPI(
    title="GigaChat Document Analysis API",
    description="API для анализа документов с помощью GigaChat",
    version="1.0.0"
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Инициализация менеджера
API_TOKEN = "MDE5OWM5OGUtMDI3MC03ZGM4LWIyMjItODMyMjE3YjllZjFlOjEzMmUzZTg5LTU2ZTgtNDA2NS1hZmFhLTcwM2FmZTRjMzA2Ng=="
file_manager = GigaChatManager(
    credentials=API_TOKEN,
    scope="GIGACHAT_API_PERS",
    verify_ssl_certs=False
)

class FileProcessor:
    """Класс для обработки загружаемых файлов"""
    
    @staticmethod
    async def extract_text_from_pdf(file_path: str) -> str:
        """Извлекает текст из PDF файла"""
        text = ""
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Ошибка чтения PDF: {e}")
        return text
    
    @staticmethod
    async def extract_text_from_docx(file_path: str) -> str:
        """Извлекает текст из DOCX файла"""
        text = ""
        try:
            doc = Document(file_path)
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text += paragraph.text + "\n"
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Ошибка чтения DOCX: {e}")
        return text
    
    @staticmethod
    async def extract_text_from_txt(file_path: str) -> str:
        """Извлекает текст из TXT файла"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                text = file.read()
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Ошибка чтения TXT: {e}")
        return text
    
    @staticmethod
    async def process_uploaded_file(file: UploadFile) -> str:
        """Обрабатывает загруженный файл и возвращает текст"""
        with tempfile.NamedTemporaryFile(delete=False, suffix=file.filename) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_path = temp_file.name
        
        try:
            file_extension = file.filename.lower().split('.')[-1] if file.filename else ''
            
            if file_extension == 'pdf':
                text = await FileProcessor.extract_text_from_pdf(temp_path)
            elif file_extension in ['docx', 'doc']:
                text = await FileProcessor.extract_text_from_docx(temp_path)
            elif file_extension == 'txt':
                text = await FileProcessor.extract_text_from_txt(temp_path)
            else:
                raise HTTPException(
                    status_code=400, 
                    detail="Неподдерживаемый формат файла. Поддерживаются: PDF, DOCX, DOC, TXT"
                )
            
            if not text.strip():
                raise HTTPException(status_code=400, detail="Файл не содержит текста")
            
            return text.strip()
        
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

@app.post("/api/chat")
async def chat_with_message(
    message: str = Form(..., description="Текст сообщения пользователя"),
    file: Optional[UploadFile] = File(None, description="Опциональный файл (PDF, DOCX, DOC, TXT)")
):
    """
    Основной endpoint для чата с нейросетью
    """
    try:
        final_message = message
        
        # Если передан файл, обрабатываем его и добавляем текст к сообщению
        if file:
            # Проверяем тип файла
            file_extension = file.filename.lower().split('.')[-1] if file.filename else ''
            allowed_extensions = ['pdf', 'docx', 'doc', 'txt']
            
            if file_extension not in allowed_extensions:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Неподдерживаемый формат файла. Поддерживаются: {', '.join(allowed_extensions).upper()}"
                )
            
            # Извлекаем текст из файла
            file_text = await FileProcessor.process_uploaded_file(file)
            
            # Формируем финальное сообщение: текст пользователя + текст из файла
            if file_text:
                if final_message.strip():
                    # Если есть и текст и файл - объединяем
                    final_message = f"{final_message}\n\nКонтекст из файла '{file.filename}':\n{file_text}"
                else:
                    # Если только файл - используем текст файла как сообщение
                    final_message = f"Проанализируйте следующий документ:\n{file_text}"
        
        if not final_message.strip():
            raise HTTPException(status_code=400, detail="Сообщение не может быть пустым")
        
        # Отправляем запрос в GigaChat (простой чат без прикрепленных файлов)
        responses = file_manager.ask_according_to_material(final_message)
        
        # Обрабатываем ответ
        if responses and hasattr(responses[0], 'choices') and responses[0].choices:
            result_content = responses[0].choices[0].message.content
        else:
            result_content = "Не удалось получить ответ от нейросети"
        
        # Всегда возвращаем одинаковый формат
        return JSONResponse({
            "response": result_content
        })
        
    except Exception as e:
<<<<<<< Updated upstream
        raise HTTPException(status_code=500, detail=f"Ошибка обработки запроса: {str(e)}")   
=======
        raise HTTPException(status_code=500, detail=f"Ошибка обработки запроса: {str(e)}")
    
    
>>>>>>> Stashed changes
# Обновляем endpoint для загрузки файлов - переименовываем для поддержки всех типов
@app.post("/api/file/upload")
async def upload_file(
    file: UploadFile = File(..., description="Файл для загрузки (PDF, DOCX, DOC, TXT)")
):
    """
    Загружает файл в GigaChat и возвращает его ID
    """
    try:
        # Проверяем тип файла
        file_extension = file.filename.lower().split('.')[-1] if file.filename else ''
        allowed_extensions = ['pdf', 'docx', 'doc', 'txt']
        
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"Неподдерживаемый формат файла. Поддерживаются: {', '.join(allowed_extensions).upper()}"
            )
        
        # Сохраняем файл временно
        with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_extension}') as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_path = temp_file.name
        
        try:
            # Загружаем файл в GigaChat
            upload_response = file_manager.upload_file(temp_path)
            
            # Возвращаем только ID файла и базовую информацию
            return JSONResponse({
                "file": {
                    "id": upload_response.id,
                    "filename": file.filename,
                    "size": upload_response.size,
                    "type": file_extension.upper()
                }
            })
            
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка загрузки файла: {str(e)}")

# Обновляем endpoint для получения списка файлов
@app.get("/api/files")
async def get_files():
    """
    Возвращает список всех файлов в GigaChat
    """
    try:
        files = file_manager.list_files_detailed()
        
        # Поддерживаемые типы файлов
        supported_files = []
        for file_info in files:
            file_extension = file_info['filename'].lower().split('.')[-1]
            if file_extension in ['pdf', 'docx', 'doc', 'txt']:
                supported_files.append({
                    "id": file_info['id'],
                    "name": file_info['filename'],
                    "size": file_info['size'],
                    "type": file_extension.upper(),
                    "uploaded_at": file_info['created_at']
                })
        
        return JSONResponse({
            "files": supported_files
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения списка файлов: {str(e)}")

@app.get("/health")
async def health_check():
    """Проверка здоровья сервера"""
    try:
        file_count = file_manager.get_file_count()
        return {
            "status": "healthy",
            "gigachat_connection": "active",
            "files_count": file_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка подключения к GigaChat: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=5000, reload=True)