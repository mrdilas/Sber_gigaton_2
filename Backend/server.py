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
            elif file_extension == 'docx':
                text = await FileProcessor.extract_text_from_docx(temp_path)
            elif file_extension == 'txt':
                text = await FileProcessor.extract_text_from_txt(temp_path)
            else:
                raise HTTPException(
                    status_code=400, 
                    detail="Неподдерживаемый формат файла. Поддерживаются: PDF, DOCX, TXT"
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
    file: Optional[UploadFile] = File(None, description="Опциональный файл (PDF, DOCX, TXT)"),
    file_id: Optional[str] = Form(None, description="ID файла в GigaChat")
):
    """
    Основной endpoint для чата с нейросетью
    Возвращает только текст ответа нейросети
    """
    try:
        final_message = message
        
        # Если передан файл, обрабатываем его
        if file:
            file_text = await FileProcessor.process_uploaded_file(file)
            if file_text:
                if final_message:
                    final_message = f"{final_message}\n\nКонтекст из файла:\n{file_text}"
                else:
                    final_message = file_text
        
        if not final_message.strip():
            raise HTTPException(status_code=400, detail="Сообщение не может быть пустым")
        
        # Если указан file_id, используем метод с прикрепленным материалом
        if file_id:
            try:
                with open("PROMPT_WHO_ARE_YOU.txt", "r", encoding="utf-8") as prompt_file:
                    prompt_template = prompt_file.read()
            except FileNotFoundError:
                prompt_template = "Проанализируйте следующий вопрос: {message}"
            
            prompt = prompt_template.format(message=final_message)
            
            response = file_manager.giga.chat({
                "messages": [
                    {
                        "role": "assistant",
                        "content": prompt,
                        "attachments": [file_id],
                    }
                ],
                "temperature": 0.7,
                "max_tokens": 1000
            })
            
            result_content = response.choices[0].message.content
            
        else:
            # Обычный чат без прикрепленного файла
            responses = file_manager.ask_according_to_material(final_message)
            
            # Берем первый ответ (можно изменить логику если нужно объединять ответы)
            if responses and hasattr(responses[0], 'choices') and responses[0].choices:
                result_content = responses[0].choices[0].message.content
            else:
                result_content = "Не удалось получить ответ от нейросети"
        
        # Возвращаем ТОЛЬКО текст ответа нейросети
        return JSONResponse({
            "response": result_content
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка обработки запроса: {str(e)}")

@app.post("/api/pdf/upload")
async def upload_pdf_file(
    file: UploadFile = File(..., description="PDF файл для загрузки")
):
    """
    Загружает PDF файл в GigaChat и возвращает его ID
    """
    try:
        # Проверяем что файл PDF
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Поддерживаются только PDF файлы")
        
        # Сохраняем файл временно
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
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
                    "size": upload_response.size
                }
            })
            
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка загрузки файла: {str(e)}")

@app.get("/api/pdf/files")
async def get_pdf_files():
    """
    Возвращает список PDF файлов в GigaChat
    """
    try:
        files = file_manager.list_files_detailed()
        
        # Фильтруем только PDF файлы (по расширению)
        pdf_files = []
        for file_info in files:
            if file_info['filename'].lower().endswith('.pdf'):
                pdf_files.append({
                    "id": file_info['id'],
                    "name": file_info['filename'],
                    "size": file_info['size'],
                    "uploaded_at": file_info['created_at']
                })
        
        return JSONResponse({
            "files": pdf_files
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