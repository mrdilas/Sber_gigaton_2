<template>
  <div class="button-window">
    <div class="block-info">
      <h3>🤖 AI Document Assistant</h3>
      <p><strong>Умный анализ документов с помощью нейросети GigaChat</strong></p>
      
      <div class="features">
        <p>📄 <strong>Поддерживаемые форматы:</strong><br>
        • PDF документы<br>
        • Word (DOC/DOCX)<br>
        • Текстовые файлы (TXT)</p>
        
        <p>🎯 <strong>Возможности:</strong><br>
        • Анализ и поиск в документах<br>
        • Ответы на вопросы по содержимому<br>
        • Голосовой ввод запросов<br>
        • Прикрепление файлов к диалогу</p>
        
        <p>⚡ <strong>Как использовать:</strong><br>
        1. Прикрепите файл через скрепку<br>
        2. Задайте вопрос текстом или голосом<br>
        3. Получите точный ответ от ИИ</p>
      </div>
      
      <p class="tech-info">Технологии: Vue.js • FastAPI • GigaChat API</p>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ButtonWindow',
  components: {
    
  },
  
  methods: {
    
  }
}
</script>

<style scoped>
.button-window {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.block-info {
  width: 350px;
  padding: 20px;
  overflow-y: auto;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 20px;
  border: 2px solid #5a67d8;
  box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
  margin: 0px 30px 0px 0px;
  font-family: 'Inter', sans-serif;
}

.block-info h3 {
  margin: 0 0 15px 0;
  font-size: 1.4rem;
  text-align: center;
  color: white;
}

.block-info p {
  margin: 12px 0;
  line-height: 1.5;
  font-size: 0.95rem;
}

.features {
  margin: 15px 0;
  padding: 15px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  backdrop-filter: blur(10px);
}

.features p {
  margin: 15px 0;
}

.tech-info {
  text-align: center;
  font-style: italic;
  font-size: 0.85rem;
  opacity: 0.9;
  margin-top: 20px;
  padding-top: 15px;
  border-top: 1px solid rgba(255, 255, 255, 0.3);
}

@media (max-width: 768px) {
  .block-info {
    width: 100%;
    margin: 0;
    padding: 15px;
  }
  
  .block-info h3 {
    font-size: 1.2rem;
  }
  
  .features {
    padding: 12px;
  }
}
</style>