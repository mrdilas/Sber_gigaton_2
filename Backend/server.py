from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional, List
import os
import tempfile
import pdfplumber
from docx import Document
import uuid
from filework import GigaChatManager  # Импортируем ваш класс

app = FastAPI(
    title="GigaChat Document Analysis API",
    description="API для анализа документов с помощью GigaChat",
    version="1.0.0"
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене укажите конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Инициализация менеджера файлов
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
        # Создаем временный файл
        with tempfile.NamedTemporaryFile(delete=False, suffix=file.filename) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_path = temp_file.name
        
        try:
            # Определяем тип файла и обрабатываем
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
            # Удаляем временный файл
            if os.path.exists(temp_path):
                os.unlink(temp_path)

@app.get("/")
async def root():
    """Корневой endpoint"""
    return {
        "message": "GigaChat Document Analysis API работает!",
        "endpoints": {
            "health": "/health",
            "chat_with_text": "/chat/text",
            "chat_with_file": "/chat/file",
            "analyze_with_material": "/analyze/with-material",
            "list_files": "/files",
            "delete_file": "/files/{file_id}"
        }
    }

@app.get("/health")
async def health_check():
    """Проверка здоровья сервера"""
    try:
        # Проверяем подключение к GigaChat
        file_count = file_manager.get_file_count()
        return {
            "status": "healthy",
            "gigachat_connection": "active",
            "files_count": file_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка подключения к GigaChat: {str(e)}")

@app.post("/chat/text")
async def chat_with_text(
    message: str = Form(..., description="Текст сообщения пользователя")
):
    """
    Отправляет текстовое сообщение в GigaChat
    """
    try:
        if not message.strip():
            raise HTTPException(status_code=400, detail="Сообщение не может быть пустым")
        
        # Используем метод ask_according_to_material для текстового запроса
        responses = file_manager.ask_according_to_material(message)
        
        # Обрабатываем ответы
        results = []
        for i, response in enumerate(responses):
            if hasattr(response, 'choices') and response.choices:
                content = response.choices[0].message.content
                results.append({
                    "response_id": i + 1,
                    "content": content
                })
        
        return JSONResponse({
            "success": True,
            "message": message,
            "responses": results,
            "total_responses": len(results)
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка обработки запроса: {str(e)}")

@app.post("/chat/file")
async def chat_with_file(
    file: UploadFile = File(..., description="Файл для анализа (PDF, DOCX, TXT)"),
    question: Optional[str] = Form(None, description="Опциональный вопрос по файлу")
):
    """
    Анализирует загруженный файл и возвращает ответ
    
    - Файл преобразуется в текст и отправляется в GigaChat
    - Если передан вопрос, он объединяется с текстом файла
    """
    try:
        # Обрабатываем файл
        file_text = await FileProcessor.process_uploaded_file(file)
        
        # Формируем финальное сообщение
        if question and question.strip():
            final_message = f"Вопрос: {question}\n\nТекст файла:\n{file_text}"
        else:
            final_message = f"Проанализируйте следующий текст:\n\n{file_text}"
        
        # Получаем ответ от GigaChat
        responses = file_manager.ask_according_to_material(final_message)
        
        # Обрабатываем ответы
        results = []
        for i, response in enumerate(responses):
            if hasattr(response, 'choices') and response.choices:
                content = response.choices[0].message.content
                results.append({
                    "response_id": i + 1,
                    "content": content
                })
        
        return JSONResponse({
            "success": True,
            "filename": file.filename,
            "question": question,
            "file_preview": file_text[:500] + "..." if len(file_text) > 500 else file_text,
            "responses": results,
            "total_responses": len(results)
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка обработки файла: {str(e)}")

@app.post("/analyze/with-material")
async def analyze_with_material_attachment(
    message: str = Form(..., description="Текст сообщения пользователя"),
    file: UploadFile = File(..., description="Файл для прикрепления как материал (PDF, DOCX, TXT)")
):
    """
    Анализирует сообщение с прикрепленным файлом как материалом
    
    - Файл загружается в GigaChat
    - Сообщение анализируется на основе прикрепленного материала
    """
    try:
        material_id = None
        
        # Сохраняем файл временно
        with tempfile.NamedTemporaryFile(delete=False, suffix=file.filename) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_path = temp_file.name
        
        try:
            # Загружаем файл в GigaChat
            upload_response = file_manager.upload_file(temp_path)
            material_id = upload_response.id
            
            # Формируем промпт с прикрепленным материалом
            try:
                with open("PROMPT_WHO_ARE_YOU.txt", "r", encoding="utf-8") as prompt_file:
                    prompt_template = prompt_file.read()
            except FileNotFoundError:
                # Дефолтный промпт если файл не найден
                prompt_template = "Проанализируйте следующий вопрос на основе прикрепленного документа: {message}"
            
            prompt = prompt_template.format(message=message)
            
            # Отправляем запрос с прикрепленным материалом
            response = file_manager.giga.chat({
                "messages": [
                    {
                        "role": "assistant",
                        "content": prompt,
                        "attachments": [material_id],
                    }
                ],
                "temperature": 0.7,
                "max_tokens": 1000
            })
            
            result_content = response.choices[0].message.content
            
            return JSONResponse({
                "success": True,
                "message": message,
                "filename": file.filename,
                "response": result_content,
                "material_id": material_id,
                "analysis_type": "with_material_attachment"
            })
            
        finally:
            # Удаляем временный файл
            if os.path.exists(temp_path):
                os.unlink(temp_path)
        
    except Exception as e:
        # В случае ошибки удаляем загруженный файл из GigaChat
        if material_id:
            try:
                file_manager.delete_file_by_id(material_id)
            except:
                pass
        raise HTTPException(status_code=500, detail=f"Ошибка анализа с материалом: {str(e)}")

@app.post("/upload/file")
async def upload_file_only(
    file: UploadFile = File(..., description="Файл для загрузки в GigaChat")
):
    """
    Загружает файл в GigaChat без immediate анализа
    """
    try:
        # Сохраняем файл временно
        with tempfile.NamedTemporaryFile(delete=False, suffix=file.filename) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_path = temp_file.name
        
        try:
            # Загружаем файл в GigaChat
            upload_response = file_manager.upload_file(temp_path)
            
            return JSONResponse({
                "success": True,
                "filename": file.filename,
                "file_id": upload_response.id,
                "size": upload_response.size,
                "created_at": upload_response.created_at,
                "message": "Файл успешно загружен в GigaChat"
            })
            
        finally:
            # Удаляем временный файл
            if os.path.exists(temp_path):
                os.unlink(temp_path)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка загрузки файла: {str(e)}")

@app.get("/files")
async def list_files():
    """Получает список всех файлов в GigaChat"""
    try:
        files = file_manager.list_files_detailed()
        return JSONResponse({
            "success": True,
            "files": files,
            "total_count": len(files),
            "total_size": file_manager.get_total_files_size()
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения списка файлов: {str(e)}")

@app.delete("/files/{file_id}")
async def delete_file(file_id: str):
    """Удаляет файл из GigaChat по ID"""
    try:
        result = file_manager.delete_file_by_id(file_id)
        return JSONResponse({
            "success": True,
            "message": f"Файл {file_id} удален",
            "deleted_file_id": file_id
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка удаления файла: {str(e)}")

@app.delete("/files/name/{filename}")
async def delete_file_by_name(filename: str):
    """Удаляет файл из GigaChat по имени"""
    try:
        result = file_manager.delete_file_by_name(filename)
        return JSONResponse({
            "success": True,
            "message": f"Файл {filename} удален",
            "deleted_filename": filename
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка удаления файла: {str(e)}")

@app.delete("/files/all")
async def delete_all_files():
    """Удаляет все файлы из GigaChat"""
    try:
        results = file_manager.delete_all_files()
        return JSONResponse({
            "success": True,
            "message": "Все файлы удалены",
            "deleted_files": results
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка удаления файлов: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)