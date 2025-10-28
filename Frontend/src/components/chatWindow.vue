<template>
    <div class="chat-container" v-if="mounted">
        <!-- Заголовок чата -->
        <div class="chat-header">
            <h2>Chat Assistant</h2>
        </div>

        <!-- Область сообщений -->
        <div class="messages-container" ref="messagesContainer">
            <div 
                v-for="(message, index) in messages" 
                :key="index" 
                :class="['message', message.type]"
            >
                <!-- Текстовое содержимое сообщения -->
                <div 
                    v-if="message.text"
                    class="message-content" 
                    v-html="message.text"
                >
                </div>
                
                <!-- Информация о файле (если есть) -->
                <div 
                    v-if="message.fileInfo" 
                    class="file-message-content"
                >
                    <div class="file-preview-content">
                        <img :src="getFileIcon(message.fileInfo.name)" alt="File" class="file-preview-icon" />
                        <div class="file-info">
                            <span class="file-name">{{ message.fileInfo.name }}</span>
                            <span class="file-size">{{ formatFileSize(message.fileInfo.size) }}</span>
                        </div>
                    </div>
                </div>
                
                <div class="message-time">
                    {{ formatTime(message.timestamp) }}
                </div>
            </div>
            <!-- Индикатор загрузки -->
            <div v-if="isLoading" class="loading-message">
                <div class="loading-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
        </div>

        <!-- Поле ввода и кнопки отправки -->
        <div class="input-container">
            <!-- Область прикрепленного файла -->
            <div v-if="attachedFile" class="attached-file-preview">
                <div class="file-preview-content">
                    <img :src="getFileIcon(attachedFile.name)" alt="File" class="file-preview-icon" />
                    <div class="file-info">
                        <span class="file-name">{{ attachedFile.name }}</span>
                        <span class="file-size">{{ formatFileSize(attachedFile.size) }}</span>
                    </div>
                    <button @click="removeAttachedFile" class="remove-file-button" title="Удалить файл">
                        ×
                    </button>
                </div>
            </div>

            <div class="input-wrapper">
                <input 
                    v-model="newMessage" 
                    @keyup.enter="sendMessage"
                    placeholder="Введите ваш запрос..."
                    class="message-input"
                    :disabled="isLoading"
                />

                <!-- кнопка голосового ввода -->
                <button 
                    @click="toggleVoiceInput"
                    :class="['voice-button', { 'recording': isRecording }]"
                    type="button"
                    :disabled="isLoading"
                    title="Голосовой ввод"
                >
                    <img 
                        v-if="!isRecording" 
                        :src="microphoneIcon" 
                        alt="Голосовой ввод" 
                        class="voice-icon"
                    />
                    <img 
                        v-else 
                        :src="recordingIcon" 
                        alt="Идет запись" 
                        class="voice-icon recording"
                    />
                </button>

                <!-- кнопка добавления файла -->
                <button 
                    @click="addFileOnChat"
                    class="paperClip-button"
                    type="button"
                    :disabled="loadingFile || isLoading"
                    title="Добавление файла"
                >
                    <img 
                        v-if="!loadingFile" 
                        :src="paperClipIcon" 
                        alt="Добавление файла" 
                        class="paperClip-icon"
                    />
                
                    <div 
                        v-else 
                        class="loader-container"
                    >
                        <div class="bouncing-dots">
                            <div class="dot"></div>
                            <div class="dot"></div>
                            <div class="dot"></div>
                        </div>
                    </div>
                </button>

                <input 
                    type="file" 
                    ref="fileInput"
                    @change="handleFileSelect"
                    accept=".pdf,.docx,.txt,.doc"
                    style="display: none"
                />

                <!-- кнопка отправки сообщения -->
                <button 
                    @click="sendMessage" 
                    :disabled="!canSendMessage"
                    class="send-button"
                >
                    <span v-if="!isLoading">Отправить</span>
                    <span v-else>Отправка...</span>
                </button>
            </div>
            <!-- Индикатор голосового ввода -->
            <div v-if="isRecording" class="voice-status">
                Говорите... {{ recordingTime }}с
            </div>
        </div>
    </div>
</template>

<script>
import microphoneIcon from '../assets/microphone.svg';
import recordingIcon from '../assets/microphone.svg';
import paperClipIcon from '../assets/paperclip.svg';
import pdfIcon from '../assets/pdf.svg'; 
import wordIcon from '../assets/word.svg';
import txtIcon from '../assets/txt.svg';

export default {
    name: 'ChatWindow',

    props: {
        selectedFileId: {
            type: [String, Number],
            default: null
        }
    },
    
    data() {
        return {
            messages: [
                {
                    text: 'Привет! Я нейросеть, готовая помочь вам. Задайте ваш вопрос!',
                    type: 'bot',
                    timestamp: new Date()
                }
            ],
            mounted: false,
            newMessage: '',
            isLoading: false,
            isRecording: false,
            recognition: null,
            recordingTime: 0,
            recordingTimer: null,
            loadingFile: false,
            
            attachedFile: null,
            microphoneIcon: microphoneIcon,
            recordingIcon: recordingIcon,
            paperClipIcon: paperClipIcon,
            pdfIcon: pdfIcon,
            txtIcon: txtIcon,
            wordIcon: wordIcon,
            apiUrl: 'http://localhost:5000/api/chat'
        }
    },
    
    computed: {
        // Кнопка отправки активна, когда есть текст ИЛИ прикреплен файл
        canSendMessage() {
            return (this.newMessage.trim() || this.attachedFile) && !this.isLoading;
        }
    },
    
    methods: {
        // Метод для получения иконки в зависимости от типа файла
        getFileIcon(filename) {
            if (!filename) return this.pdfIcon;
            
            const extension = filename.toLowerCase().split('.').pop();
            
            switch (extension) {
                case 'pdf':
                    return this.pdfIcon;
                case 'docx':
                case 'doc':
                    return this.wordIcon;
                case 'txt':
                    return this.txtIcon;
                default:
                    return this.pdfIcon;
            }
        },

        // Проверка типа файла
        isValidFileType(file) {
            const allowedTypes = [
                'application/pdf',
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'application/msword',
                'text/plain'
            ];
            
            const allowedExtensions = ['.pdf', '.docx', '.doc', '.txt'];
            const fileExtension = '.' + file.name.toLowerCase().split('.').pop();
            
            return allowedTypes.includes(file.type) || allowedExtensions.includes(fileExtension);
        },

        // Получение человекочитаемого типа файла
        getFileTypeDescription(filename) {
            const extension = filename.toLowerCase().split('.').pop();
            
            switch (extension) {
                case 'pdf':
                    return 'PDF документ';
                case 'docx':
                case 'doc':
                    return 'Word документ';
                case 'txt':
                    return 'Текстовый файл';
                default:
                    return 'Документ';
            }
        },

        async sendMessage() {
            if (!this.canSendMessage) return;

            const userMessageText = this.newMessage.trim();
            this.newMessage = '';
            
            // Создаем сообщение пользователя с возможной информацией о файле
            const userMessage = {
                text: userMessageText,
                type: 'user',
                timestamp: new Date()
            };
            
            // Если есть прикрепленный файл, добавляем информацию о нем в сообщение
            if (this.attachedFile) {
                userMessage.fileInfo = {
                    name: this.attachedFile.name,
                    size: this.attachedFile.size,
                    type: this.attachedFile.type
                };
            }
            
            this.messages.push(userMessage);
            this.isLoading = true;
            
            this.$nextTick(() => {
                this.scrollToBottom();
            });

            try {
                const formData = new FormData();
                
                // Всегда добавляем сообщение
                formData.append('message', userMessageText);

                // СЦЕНАРИЙ 1: Если есть прикрепленный файл - отправляем его
                if (this.attachedFile) {
                    formData.append('file', this.attachedFile);
                    
                    console.log('Отправляем запрос с ВРЕМЕННЫМ файлом:', {
                        message: userMessageText,
                        fileName: this.attachedFile.name
                    });

                } 
                // СЦЕНАРИЙ 2: Если выбран файл из базы - отправляем только file_id
                else if (this.selectedFileId) {
                    formData.append('file_id', this.selectedFileId);
                    
                    console.log('Отправляем запрос с файлом из БАЗЫ:', {
                        message: userMessageText,
                        file_id: this.selectedFileId
                    });
                }
                // СЦЕНАРИЙ 3: Только текст (без файлов)
                else {
                    console.log('Отправляем ТЕКСТОВЫЙ запрос:', {
                        message: userMessageText
                    });
                }

                // ДЕБАГ: Проверим что отправляем
                console.log('FormData содержимое:');
                for (let [key, value] of formData.entries()) {
                    console.log(key, value);
                }

                const response = await fetch(this.apiUrl, {
                    method: 'POST',
                    // НЕ добавляем Content-Type header для FormData - браузер сам установит
                    body: formData
                });

                if (!response.ok) {
                    // Получим больше информации об ошибке
                    const errorText = await response.text();
                    console.error('Детали ошибки:', errorText);
                    throw new Error(`HTTP error! status: ${response.status}. Details: ${errorText}`);
                }

                const data = await response.json();
                
                console.log('Получен ответ от сервера:', data);

                if (data.response) {
                    const formattedResponse = this.formatResponse(data.response);
                    
                    const botMessage = {
                        text: formattedResponse,
                        type: 'bot',
                        timestamp: new Date()
                    };
                    
                    this.messages.push(botMessage);
                } else {
                    this.addSystemMessage('Не удалось получить ответ от нейросети');
                }

                // Убираем прикрепленный файл после отправки (только для временных файлов)
                if (this.attachedFile) {
                    this.attachedFile = null;
                }
                
            } catch (error) {
                console.error('Ошибка при отправке сообщения:', error);
                
                this.addSystemMessage(`Произошла ошибка: ${error.message}`);
                this.showErrorNotification(`Ошибка: ${error.message}`);
            } finally {
                this.isLoading = false;
                
                this.$nextTick(() => {
                    this.scrollToBottom();
                });
            }
        },
        
        showErrorNotification(message) {
            if (this.$notify) {
                this.$notify({
                    title: 'Ошибка',
                    text: message,
                    type: 'error'
                });
            } else {
                alert(`Ошибка: ${message}`);
            }
        },

        addSystemMessage(text) {
            const systemMessage = {
                text: this.formatResponse(text),
                type: 'system',
                timestamp: new Date()
            };
            
            this.messages.push(systemMessage);
            this.$nextTick(() => {
                this.scrollToBottom();
            });
        },

        addFileSelectionMessage(fileId) {
            const selectionMessage = {
                text: `📁 <strong>Выбран документ для поиска</strong><br>
                       <small>Теперь нейросеть будет искать информацию в выбранном файле</small>`,
                type: 'system',
                timestamp: new Date()
            };
            
            this.messages.push(selectionMessage);
            this.$nextTick(() => {
                this.scrollToBottom();
            });
        },

        formatResponse(text) {
            if (!text) return '';
            
            let formattedText = text;

            // Преобразование Markdown в HTML
            formattedText = formattedText.replace(/^##\s*(.*)$/gm, '<h2>$1</h2>');
            formattedText = formattedText.replace(/^###\s*(.*)$/gm, '<h3>$1</h3>');
            formattedText = formattedText.replace(/^>\s*(.*)$/gm, '<blockquote>$1</blockquote>');
            formattedText = formattedText.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
            formattedText = formattedText.replace(/\n/g, '<br>');
            formattedText = formattedText.replace(/\t/g, '&nbsp;&nbsp;&nbsp;&nbsp;');
            formattedText = formattedText.replace(/  /g, '&nbsp;&nbsp;');
            
            return formattedText;
        },

        // Новый метод для выбора файла (без загрузки в БД)
        handleFileSelect(event) {
            const file = event.target.files[0];
            if (!file) return;

            // Проверяем тип файла
            if (!this.isValidFileType(file)) {
                alert('Пожалуйста, выберите файл в формате PDF, Word (DOC/DOCX) или TXT');
                return;
            }

            const maxSize = 150 * 1024 * 1024;
            if (file.size > maxSize) {
                alert('Файл слишком большой. Максимальный размер 150MB');
                return;
            }

            // Просто прикрепляем файл к сообщению
            this.attachedFile = file;
            
            // Очищаем input для возможности выбора того же файла снова
            event.target.value = '';
            
            console.log('Файл прикреплен:', {
                name: file.name,
                size: file.size,
                type: file.type,
                description: this.getFileTypeDescription(file.name)
            });
        },

        // Метод для удаления прикрепленного файла
        removeAttachedFile() {
            this.attachedFile = null;
        },

        // Форматирование размера файла
        formatFileSize(bytes) {
            if (bytes === 0) return '0 Bytes';
            const k = 1024;
            const sizes = ['Bytes', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
        },

        // Остальные методы остаются без изменений
        toggleVoiceInput() {
            if (this.isRecording) {
                this.stopVoiceRecognition();
            } else {
                this.startVoiceRecognition();
            }
        },

        startVoiceRecognition() {
            if (!('webkitSpeechRecognition' in window)) {
                alert('Голосовой ввод не поддерживается вашим браузером');
                return;
            }

            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            this.recognition = new SpeechRecognition();
            
            this.recognition.continuous = false;
            this.recognition.interimResults = true;
            this.recognition.lang = 'ru-RU';

            this.recognition.onstart = () => {
                this.isRecording = true;
                this.recordingTime = 0;
                this.recordingTimer = setInterval(() => {
                    this.recordingTime++;
                }, 1000);
            };

            this.recognition.onresult = (event) => {
                let transcript = '';
                for (let i = event.resultIndex; i < event.results.length; i++) {
                    transcript += event.results[i][0].transcript;
                }
                this.newMessage = transcript;
            };

            this.recognition.onerror = (event) => {
                if (event.error === 'not-allowed') {
                    alert('Разрешите доступ к микрофону');
                }
                this.stopVoiceRecognition();
            };

            this.recognition.onend = () => {
                this.stopVoiceRecognition();
            };

            this.recognition.start();
        },

        stopVoiceRecognition() {
            if (this.recognition) {
                this.recognition.stop();
            }
            this.isRecording = false;
            if (this.recordingTimer) {
                clearInterval(this.recordingTimer);
                this.recordingTimer = null;
            }
        },

        addFileOnChat() {
            if (this.loadingFile || this.isLoading) return;
            this.$refs.fileInput.click();
        },

        // Старый метод для загрузки в БД (оставляем на случай если понадобится)
        async handleFileUpload(event) {
            const file = event.target.files[0];
            if (!file || this.loadingFile) return;

            if (!this.isValidFileType(file)) {
                alert('Пожалуйста, выберите файл в формате PDF, Word (DOC/DOCX) или TXT');
                return;
            }

            const maxSize = 150 * 1024 * 1024;
            if (file.size > maxSize) {
                alert('Файл слишком большой. Максимальный размер 150MB');
                return;
            }

            this.loadingFile = true;

            try {
                const formData = new FormData();
                formData.append('file', file);

                const response = await fetch('http://localhost:5000/api/file/upload', {
                    method: 'POST',
                    body: formData
                });

                const data = await response.json();
                
                if (!response.ok) {
                    throw new Error(data.error || `HTTP error! status: ${response.status}`);
                }

                await this.loadPdfFiles();
                event.target.value = '';
                
                if (data.file && data.file.id) {
                    this.$emit('file-uploaded', data.file.id);
                }
                
                alert(`Файл успешно загружен! Размер: ${data.file_size_mb || (file.size / (1024 * 1024)).toFixed(2)} MB`);

            } catch (error) {
                console.error('Ошибка загрузки файла:', error);
                this.addSystemMessage('Ошибка при загрузке файла: ' + error.message);
            } finally {
                this.loadingFile = false;
            }
        },

        async loadPdfFiles() {
            try {
                const response = await fetch('http://localhost:5000/api/files');
                const data = await response.json();
                
                if (!response.ok) throw new Error(data.error);
                
                this.pdfFiles = data.files.map(file => ({
                    id: file.id,
                    name: file.name,
                    url: file.file_url,
                    storage_path: file.storage_path,
                    uploaded_at: file.uploaded_at
                }));

                console.log('Загружен список файлов:', this.pdfFiles);

            } catch (error) {
                console.error('Ошибка загрузки списка файлов:', error);
                this.pdfFiles = [];
            }
        },

        scrollToBottom() {
            const container = this.$refs.messagesContainer;
            if (container) {
                container.scrollTop = container.scrollHeight;
            }
        },
        
        formatTime(timestamp) {
            return timestamp.toLocaleTimeString('ru-RU', { 
                hour: '2-digit', 
                minute: '2-digit' 
            });
        },
    },
    
    watch: {
        selectedFileId(newFileId) {
            if (newFileId) {
                this.addFileSelectionMessage(newFileId);
            }
        }
    },

    mounted() {
        this.mounted = true;
        this.scrollToBottom();
    },

    beforeUnmount() {
        this.mounted = false;
        this.stopVoiceRecognition();
    }
}
</script>

<style scoped>
/* Добавляем стили для превью прикрепленного файла */
.attached-file-preview {
    margin-bottom: 15px;
    padding: 12px 16px;
    background: linear-gradient(135deg, #f8f9fa, #e9ecef);
    border: 2px dashed #667eea;
    border-radius: 12px;
    animation: slideDown 0.3s ease;
}

@keyframes slideDown {
    from {
        opacity: 0;
        transform: translateY(-10px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.file-preview-content {
    display: flex;
    align-items: center;
    gap: 12px;
}

.file-preview-icon {
    width: 40px;
    height: 40px;
    flex-shrink: 0;
}

.file-info {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 2px;
}

.file-name {
    font-weight: 600;
    color: #333;
    font-size: 14px;
}

.file-size {
    font-size: 12px;
    color: #666;
}

.remove-file-button {
    background: none;
    border: none;
    font-size: 20px;
    color: #ff6b6b;
    cursor: pointer;
    width: 24px;
    height: 24px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
    transition: all 0.3s ease;
}

.remove-file-button:hover {
    background: #ff6b6b;
    color: white;
    transform: scale(1.1);
}

/* Стили для файлов в сообщениях чата */
.file-message-content {
    margin-top: 8px;
    padding: 12px 16px;
    background: rgba(255, 255, 255, 0.9);
    border-radius: 12px;
    border: 1px solid rgba(102, 126, 234, 0.2);
}

.message.user .file-message-content {
    background: rgba(255, 255, 255, 0.2);
    border: 1px solid rgba(255, 255, 255, 0.3);
}

/* Остальные стили остаются без изменений */
.chat-container {
    display: flex;
    flex-direction: column;
    height: 100%;
    max-width: 1000px;
    margin: 0 auto;
    background: rgb(248, 244, 244);
    border-radius: 20px;
    overflow: hidden;
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1), 0 15px 12px rgba(0, 0, 0, 0.08);
    font-family: 'Inter', 'Segoe UI', 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif;
    backdrop-filter: blur(10px);
}
.element { -ms-overflow-style: none; }
.chat-header {
    background: linear-gradient(0deg, rgb(126, 157, 199), rgb(75, 35, 159));
    color: white;
    padding: 20px 30px;
    text-align: center;
    backdrop-filter: blur(10px);
    border-radius: 0px 0px 20px 20px;
    -webkit-user-select: none;
	-khtml-user-select: none;
	-moz-user-select: none;
	-ms-user-select: none;
	user-select: none;
}

.chat-header h2 {
    margin: 0;
    font-size: 1.5rem;
    font-weight: 600;
    letter-spacing: -0.5px;
    text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    
}

.messages-container {
    flex: 1;
    padding: 25px;
    overflow-y: auto;
    max-height: 800px;
    background: rgb(248, 244, 244);
    backdrop-filter: blur(15px);
}

.message {
    margin-bottom: 20px;
    display: flex;
    flex-direction: column;
    animation: messageSlide 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94);
}

@keyframes messageSlide {
    from {
        opacity: 0;
        transform: translateY(20px) scale(0.95);
    }
    to {
        opacity: 1;
        transform: translateY(0) scale(1);
    }
}

.message.user {
    align-items: flex-end;
}

.message.bot {
    align-items: flex-start;
}

.message.system {
    align-items: center;
}

.message-content {
    max-width: 75%;
    padding: 18px 22px;
    border-radius: 24px;
    word-wrap: break-word;
    font-size: 16px;
    line-height: 1.5;
    font-weight: 400;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
    position: relative;
    transition: all 0.3s ease;
}

.message-content:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15);
}

.message.user .message-content {
    background: linear-gradient(135deg, #667eea, #764ba2);
    color: white;
    border-bottom-right-radius: 8px;
    border-top-right-radius: 24px;
    border-top-left-radius: 24px;
}

.message.bot .message-content {
    background: linear-gradient(135deg, #667eea, #764ba2);
    color: white;
    border-bottom-left-radius: 8px;
    border-top-right-radius: 24px;
    border-top-left-radius: 24px;
}

.message.system .message-content {
    background: linear-gradient(135deg, #cf6b29, #da3e1b);
    color: white;
    border: none;
    text-align: center;
    font-style: italic;
    max-width: 85%;
    margin: 0 auto;
    font-weight: 500;
    border-radius: 20px;
}

.message-time {
    font-size: 0.8rem;
    color: rgba(15, 15, 15, 0.8);
    margin-top: 8px;
    font-weight: 500;
    -webkit-user-select: none;
	-khtml-user-select: none;
	-moz-user-select: none;
	-ms-user-select: none;
	user-select: none;
}

.message.bot .message-time,
.message.system .message-time {
    color: rgba(15, 15, 15, 0.8);
}

.input-container {
    padding: 25px;
    background: rgba(255, 255, 255, 0.98);
    border-top: 1px solid rgba(255, 255, 255, 0.2);
    backdrop-filter: blur(20px);
    border-radius: 20px 20px 0px 0px;
}

.input-wrapper {
    display: flex;
    gap: 12px;
    align-items: center;
}

.message-input {
    flex: 1;
    padding: 16px 20px;
    border: 2px solid rgba(102, 126, 234, 0.2);
    border-radius: 25px;
    outline: none;
    font-size: 16px;
    font-weight: 400;
    background: rgba(255, 255, 255, 0.9);
    transition: all 0.3s ease;
    font-family: inherit;
}

.message-input:focus {
    border-color: #667eea;
    background: white;
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    transform: scale(1.02);
}

.message-input:disabled {
    background-color: rgba(245, 245, 245, 0.7);
    cursor: not-allowed;
}

.send-button {
    padding: 16px 24px;
    background: linear-gradient(135deg, #667eea, #764ba2);
    color: white;
    border: none;
    border-radius: 25px;
    cursor: pointer;
    font-size: 16px;
    font-weight: 600;
    transition: all 0.3s ease;
    white-space: nowrap;
    font-family: inherit;
    letter-spacing: -0.2px;
    box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    -webkit-user-select: none;
	-khtml-user-select: none;
	-moz-user-select: none;
	-ms-user-select: none;
	user-select: none;
}

.send-button:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
}

.send-button:disabled {
    background: linear-gradient(135deg, #cccccc, #999999);
    cursor: not-allowed;
    transform: none;
    box-shadow: none;
}

.voice-button {
    padding: 14px;
    background: linear-gradient(135deg, #f093fb, #f5576c);
    border: none;
    border-radius: 50%;
    cursor: pointer;
    width: 50px;
    height: 50px;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.3s ease;
    box-shadow: 0 4px 15px rgba(245, 87, 108, 0.3);
    -webkit-user-select: none;
	-khtml-user-select: none;
	-moz-user-select: none;
	-ms-user-select: none;
	user-select: none;
}

.voice-button:hover:not(:disabled) {
    transform: translateY(-2px) scale(1.05);
    box-shadow: 0 6px 20px rgba(245, 87, 108, 0.4);
}

.voice-button.recording {
    background: linear-gradient(135deg, #ff6b6b, #ee5a52);
    animation: pulse 2s infinite;
}

.voice-button:disabled {
    opacity: 0.6;
    cursor: not-allowed;
    transform: none;
}

.voice-icon {
    width: 22px;
    height: 22px;
    object-fit: contain;
    transition: all 0.3s ease;
    filter: brightness(0) invert(1);
}

.voice-button:hover .voice-icon {
    transform: scale(1.1);
}

.voice-button.recording .voice-icon {
    animation: recordingPulse 1.5s infinite;
}

@keyframes recordingPulse {
    0%, 100% {
        transform: scale(1);
        opacity: 1;
    }
    50% {
        transform: scale(1.3);
        opacity: 0.8;
    }
}

.voice-status {
    text-align: center;
    margin-top: 12px;
    font-size: 14px;
    color: #667eea;
    font-weight: 500;
    font-style: italic;
}

.paperClip-button {
    padding: 14px;
    background: linear-gradient(135deg, #4ecdc4, #44a08d);
    border: none;
    border-radius: 50%;
    cursor: pointer;
    width: 50px;
    height: 50px;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.3s ease;
    box-shadow: 0 4px 15px rgba(78, 205, 196, 0.3);
    -webkit-user-select: none;
	-khtml-user-select: none;
	-moz-user-select: none;
	-ms-user-select: none;
	user-select: none;
}

.paperClip-icon {
    width: 22px;
    height: 22px;
    object-fit: contain;
    transition: all 0.3s ease;
    filter: brightness(0) invert(1);
}

.paperClip-button:hover {
    transform: translateY(-2px) scale(1.05);
    box-shadow: 0 6px 20px rgba(78, 205, 196, 0.4);
}

.loader-container {
    display: flex;
    justify-content: center;
    align-items: center;
}

.bouncing-dots {
    display: flex;
    justify-content: space-between;
    width: 35px;
}

.dot {
    width: 10px;
    height: 10px;
    background-color: white;
    border-radius: 50%;
    animation: bounce 1.5s infinite;
}

.dot:nth-child(1) {
    animation-delay: 0s;
}

.dot:nth-child(2) {
    animation-delay: 0.3s;
}

.dot:nth-child(3) {
    animation-delay: 0.6s;
}

@keyframes bounce {
    0%, 100% {
        transform: translateY(0);
    }
    50% {
        transform: translateY(-10px);
    }
}

.loading-message {
    display: flex;
    justify-content: flex-start;
    margin: 15px 0;
}

.loading-dots {
    display: flex;
    gap: 6px;
    padding: 18px 22px;
    background: linear-gradient(135deg, #667eea, #764ba2);
    border-radius: 24px;
    border-bottom-left-radius: 8px;
}

.loading-dots span {
    width: 10px;
    height: 10px;
    background: white;
    border-radius: 50%;
    animation: loadingBounce 1.4s infinite ease-in-out;
}

.loading-dots span:nth-child(1) { animation-delay: -0.32s; }
.loading-dots span:nth-child(2) { animation-delay: -0.16s; }

@keyframes loadingBounce {
    0%, 80%, 100% {
        transform: scale(0.8);
        opacity: 0.5;
    }
    40% {
        transform: scale(1.2);
        opacity: 1;
    }
}

.messages-container::-webkit-scrollbar {
    width: 8px;
}

.messages-container::-webkit-scrollbar-track {
    background: rgba(102, 126, 234, 0.1);
    border-radius: 4px;
}

.messages-container::-webkit-scrollbar-thumb {
    background: linear-gradient(135deg, #667eea, #764ba2);
    border-radius: 4px;
}

.messages-container::-webkit-scrollbar-thumb:hover {
    background: linear-gradient(135deg, #764ba2, #667eea);
}

@keyframes pulse {
    0% {
        box-shadow: 0 0 0 0 rgba(255, 107, 107, 0.7);
    }
    70% {
        box-shadow: 0 0 0 15px rgba(255, 107, 107, 0);
    }
    100% {
        box-shadow: 0 0 0 0 rgba(255, 107, 107, 0);
    }
}

@media (max-width: 768px) {
    .chat-container {
        border-radius: 0;
        height: 100vh;
    }
    
    .message-content {
        max-width: 85%;
        font-size: 15px;
        padding: 16px 18px;
    }
    
    .messages-container {
        padding: 20px 15px;
    }
    
    .input-container {
        padding: 20px 15px;
    }
    
    .attached-file-preview {
        padding: 10px 12px;
    }
    
    .file-preview-content {
        gap: 8px;
    }
}
</style>