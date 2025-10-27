from flask import Flask, request, jsonify
from flask_cors import CORS
from neyro import GigaChatManager
from supabase import create_client, Client
import time
import os
import uuid
from werkzeug.utils import secure_filename
from pdf_segmenter import process_pdf_to_txt
import logging
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Конфигурация
API_TOKEN = 'MDE5OWM5OGUtMDI3MC03ZGM4LWIyMjItODMyMjE3YjllZjFlOjEzMmUzZTg5LTU2ZTgtNDA2NS1hZmFhLTcwM2FmZTRjMzA2Ng=='
SUPABASE_URL = 'https://guwpfrhmzgflqwetkkos.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imd1d3BmcmhtemdmbHF3ZXRra29zIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjA2Mzc3ODYsImV4cCI6MjA3NjIxMzc4Nn0.2Ak_MBIDbL-PFXqX0HoGKH8a1qKxeYtRPTez0YUpMuU'



# Инициализация клиентов
giga_manager = GigaChatManager(API_TOKEN)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    """Проверка расширения файла"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def init_supabase():
    """Инициализация Supabase"""
    try:
        response = supabase.table('file_data').select('id').limit(1).execute()
        print("✅ Подключение к Supabase успешно")
        return True
    except Exception as e:
        print(f"❌ Ошибка подключения к Supabase: {e}")
        return False



def validate_chat_request(data):
    """Валидация запроса чата"""
    if not data:
        raise ValueError("Данные запроса обязательны")
    
    message = data.get('message', '').strip()
    if not message:
        raise ValueError("Сообщение обязательно")
    
    if len(message) > 10000:
        raise ValueError("Сообщение слишком длинное")
    
    return message, data.get('file_id')


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('app.log'),
            logging.StreamHandler()
        ]
    )

setup_logging()
logger = logging.getLogger(__name__)


@app.route('/api/metrics', methods=['GET'])
def get_metrics():
    """Метрики использования API"""
    try:
        # Статистика из базы
        files_response = supabase.table('file_data').select('id', count='exact').execute()
        files_count = files_response.count
        
        # Статистика GigaChat
        gigachat_files = len(giga_manager.files)
        
        return jsonify({
            'total_files': files_count,
            'gigachat_files': gigachat_files,
            'server_uptime': time.time() - app_start_time,
            'status': 'success'
        })
    except Exception as e:
        logger.error(f"Ошибка получения метрик: {e}")
        return jsonify({'error': str(e)}), 500

# Глобальная переменная времени старта
app_start_time = time.time()



@app.route('/api/health', methods=['GET'])
def health_check():
    """Проверка работоспособности"""
    try:
        # Проверяем GigaChat
        gigachat_files = giga_manager.files
        
        # Проверяем Supabase
        files_response = supabase.table('file_data').select('id', count='exact').execute()
        files_count = files_response.count if hasattr(files_response, 'count') else len(files_response.data)
        
        return jsonify({
            'status': 'OK',
            'gigachat_files': len(gigachat_files),
            'database_files': files_count,
            'server_time': time.strftime('%Y-%m-%d %H:%M:%S')
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def chat_with_ai():
    """
    Основной эндпоинт для чата
    """
    try:
        data = request.get_json()
        user_message, file_id = validate_chat_request(data)


        if not data:
            return jsonify({'error': 'Данные запроса обязательны'}), 400

        user_message = data.get('message')
        file_id = data.get('file_id')

        if not user_message:
            return jsonify({'error': 'Сообщение обязательно'}), 400

        print(f"💬 Получен запрос: '{user_message}'")
        print(f"📁 File ID: {file_id}")

        # Получаем gigachat_file_id из базы данных
        gigachat_file_id = None
        file_name = None
        
        if file_id:
            try:
                response = supabase.table('file_data').select('*').eq('id', file_id).execute()
                # Пробуем разные названия таблиц
                tables_to_try = ['file_data']
                
                if response.data:
                    file_info = response.data[0]
                    gigachat_file_id = file_info.get('gigachat_file_id')
                    file_name = file_info.get('name')
                    print(f"📄 Найден файл: {file_name}, GigaChat ID: {gigachat_file_id}")
                else:
                    print(f"⚠️ Файл с ID {file_id} не найден в базе")
                for table_name in tables_to_try:
                    try:
                        response = supabase.table(table_name).select('*').eq('id', file_id).execute()
                        
                        if response.data:
                            file_info = response.data[0]
                            gigachat_file_id = file_info.get('gigachat_file_id')
                            file_name = file_info.get('name')
                            print(file_id, file_info, file_name)
                            print(f"✅ Найден файл в таблице {table_name}: {file_name}, GigaChat ID: {gigachat_file_id}")
                            break
                        else:
                            print(f"⚠️ Файл с ID {file_id} не найден в таблице {table_name}")
                    except Exception as e:
                        print(f"⚠️ Ошибка поиска в таблице {table_name}: {e}")
                        continue
                
                if not gigachat_file_id:
                    print(f"❌ Файл с ID {file_id} не найден ни в одной таблице")
                    
            except Exception as e:
                print(f"⚠️ Ошибка поиска файла в базе: {e}")
                print(f"⚠️ Общая ошибка поиска файла в базе: {e}")

        # Отправляем запрос в GigaChat
        start_time = time.time()
        
        try:
            if gigachat_file_id:
                print("🚀 Отправка запроса к GigaChat с прикрепленным файлом...")
                result = giga_manager.ask_according_to_material(user_message, gigachat_file_id)
            else:
                print("🚀 Отправка общего запроса к GigaChat...")
                result = giga_manager.giga.chat({
                    "messages": [{"role": "user", "content": f"""Ты эксперт в сфере гражданских прав и свобод, "
                    "а также хорошо знаком с законами, кодексами и подзаконными актами РФ. Тебе необходимо сформулировать ответ на"
                    "вопрос пользователя, основанный на документах, действующих на территории РФ. Ответь строго в формате Markdown. "
                    "Вот вопрос пользователя: **{user_message}**"
                    "Ответ необходимо сформулировать грамотно, а также указать в виде списка, на каких документах (законах)"
                    "РФ основан ответ/консультация.

Ответь технически грамотно в таком формате Markdown:
## Консультация по вашему вопросу
Здесь должна быть описана ваша ситуация, грамотно с юридической точки зрения, с использованием **жирного шрифта** для ключевых моментов.

### Законы, являющиеся основаниями для консультации
1. **К1-ый кодекс РФ** - тут должны быть перечислены связи с нашим вопросом
    > Статья 1 - её описание, основанное на вопросе пользователя
    > Статья N - её описание, основанное на вопросе пользователя
2. **К2-ой кодекс РФ** - тут должны быть перечислены связи с нашим вопросом
    > Статья 1 - её описание, основанное на вопросе пользователя
    
### Ваши действия (потенциально возможные)
* Действие 1
* Действие 2
* Действие 3

Данный ответ сгенерирован нейросетью и не призывает Вас действовать, основываясь на данных рекомендациях."""}],
                    "temperature": 0.1
                })

            # Извлекаем ответ
            if hasattr(result, 'choices') and len(result.choices) > 0:
                ai_response = result.choices[0].message.content
            elif hasattr(result, 'message') and hasattr(result.message, 'content'):
                ai_response = result.message.content
            else:
                ai_response = "Не удалось получить ответ от нейросети"
            print(giga_manager.get_balance())
        except Exception as e:
            print(f"❌ Ошибка GigaChat: {e}")
            return jsonify({'error': f'Ошибка нейросети: {str(e)}'}), 500

        processing_time = time.time() - start_time

        print(f"✅ Ответ получен за {processing_time:.2f} сек")

        return jsonify({
            'response': ai_response,
            'status': 'success',
            'processing_time': f"{processing_time:.2f} сек",
            'used_file_id': file_id,
            'used_file_name': file_name
        })

    except Exception as e:
        print(f"❌ Ошибка при обработке запроса: {e}")
        return jsonify({
            'error': f'Внутренняя ошибка сервера: {str(e)}',
            'status': 'error'
        }), 500

@app.route('/api/pdf/upload', methods=['POST'])
def upload_pdf_file():
    """Загрузка PDF файла, обработка через pdf_segmenter и загрузка TXT в GigaChat"""
    try:
        print("📥 Начало загрузки файла...")
        
        if 'file' not in request.files:
            return jsonify({'error': 'Файл обязателен'}), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'Файл не выбран'}), 400

        if not allowed_file(file.filename):
            return jsonify({'error': 'Разрешены только PDF файлы'}), 400

        # Сохраняем PDF временно
        file_content = file.read()
        file_size = len(file_content)
        
        # Создаем уникальное имя для временного файла
        temp_pdf_filename = f"temp_{uuid.uuid4()}.pdf"
        temp_txt_filename = f"temp_{uuid.uuid4()}.txt"
        
        try:
            # Сохраняем PDF файл
            with open(temp_pdf_filename, 'wb') as temp_file:
                temp_file.write(file_content)
            
            print(f"📄 PDF сохранен временно: {temp_pdf_filename}, размер: {file_size} байт")

            # Обрабатываем PDF через pdf_segmenter
            print("🔧 Обработка PDF через pdf_segmenter...")
            processed_text = process_pdf_to_txt(temp_pdf_filename)
            
            # Сохраняем обработанный текст в TXT файл
            with open(temp_txt_filename, 'w', encoding='utf-8') as txt_file:
                txt_file.write(processed_text)
            
            print(f"✅ PDF обработан, создан TXT файл: {temp_txt_filename}")

            # Загружаем TXT файл в GigaChat
            print(f"📤 Загрузка TXT файла в GigaChat: {file.filename}")
            giga_manager.upload_file(temp_txt_filename)
            
            # Получаем ID загруженного файла
            files = giga_manager.files
            if not files:
                raise Exception("Не удалось получить ID загруженного файла")
                
            latest_file = files[-1]
            gigachat_file_id = latest_file.id
            
            print(f"✅ TXT файл загружен в GigaChat с ID: {gigachat_file_id}")

            # Сохраняем в базу данных
            file_data = {
                'name': secure_filename(file.filename),
                'file_size': file_size,
                'gigachat_file_id': gigachat_file_id,
                'created_at': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            print(f"💾 Сохранение в базу данных: {file_data}")
            response = supabase.table('file_data').insert(file_data).execute()
            
            if not response.data:
                raise Exception("Не удалось сохранить в базу данных")
                
            saved_file = response.data[0]
            print(f"✅ Файл сохранен в базу с ID: {saved_file['id']}")

            return jsonify({
                'message': 'PDF файл успешно обработан и загружен',
                'file': saved_file,
                'file_size_mb': round(file_size / (1024 * 1024), 2),
                'status': 'success'
            })
            
        finally:
            # Удаляем временные файлы
            for temp_file in [temp_pdf_filename, temp_txt_filename]:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    print(f"🗑️ Временный файл удален: {temp_file}")

    except Exception as e:
        print(f"❌ Ошибка загрузки файла: {e}")
        return jsonify({
            'error': f'Ошибка обработки файла: {str(e)}',
            'status': 'error'
        }), 500

@app.route('/api/pdf/files', methods=['GET'])
def get_pdf_files_list():
    """Получение списка всех обработанных файлов"""
    try:
        print("📋 Запрос списка файлов...")
        response = supabase.table('file_data').select('*').order('created_at', desc=True).execute()
        
        files = response.data
        print(f"✅ Получено файлов: {len(files)}")
        
        return jsonify({
            'files': files,
            'total_count': len(files),
            'status': 'success'
        })
        
    except Exception as e:
        print(f"❌ Ошибка получения файлов: {e}")
        return jsonify({
            'error': f'Ошибка получения файлов: {str(e)}',
            'status': 'error'
        }), 500

@app.route('/api/pdf/delete/<file_id>', methods=['DELETE'])
def delete_pdf_file(file_id):
    """Удаление файла"""
    try:
        print(f"🗑️ Запрос на удаление файла: {file_id}")
        
        # Получаем информацию о файле
        response = supabase.table('file_data').select('*').eq('id', file_id).execute()
        
        if not response.data:
            return jsonify({'error': 'Файл не найден'}), 404
            
        file_info = response.data[0]
        gigachat_file_id = file_info.get('gigachat_file_id')
        file_name = file_info.get('name')
        
        # Удаляем из GigaChat
        if gigachat_file_id:
            try:
                giga_manager.delete_file_by_id(gigachat_file_id)
                print(f"✅ Удален из GigaChat: {gigachat_file_id}")
            except Exception as e:
                print(f"⚠️ Ошибка удаления из GigaChat: {e}")
        
        # Удаляем из базы
        supabase.table('file_data').delete().eq('id', file_id).execute()
        
        print(f"✅ Файл удален из базы: {file_name}")
        
        return jsonify({
            'message': 'Файл успешно удален',
            'deleted_file_id': file_id,
            'deleted_file_name': file_name,
            'status': 'success'
        })
        
    except Exception as e:
        print(f"❌ Ошибка удаления файла: {e}")
        return jsonify({
            'error': f'Ошибка удаления файла: {str(e)}',
            'status': 'error'
        }), 500

if __name__ == '__main__':
    print("🚀 Запуск Chat Server на http://localhost:5000")
    print("=" * 60)
    
    # Проверяем подключения
    try:
        files = giga_manager.files
        print(f"✅ GigaChat: {len(files)} файлов")
        for f in files:
            print(f"   📄 {f.fullname} (ID: {f.id})")
    except Exception as e:
        print(f"❌ Ошибка GigaChat: {e}")

    # Инициализируем Supabase
    if init_supabase():
        print("✅ Supabase: подключение установлено")
    else:
        print("❌ Supabase: ошибка подключения")
    
    print("=" * 60)
    print("📝 Доступные эндпоинты:")
    print("  POST /api/chat           - Чат с AI")
    print("  POST /api/pdf/upload     - Загрузка и обработка PDF")
    print("  GET  /api/pdf/files      - Список файлов") 
    print("  DELETE /api/pdf/delete/<id> - Удаление файла")
    print("  GET  /api/health         - Проверка здоровья")
    print("=" * 60)
    print(giga_manager.get_balance())
    #$giga_manager.delete_all_files()
    app.run(host='0.0.0.0', port=5000, debug=True)