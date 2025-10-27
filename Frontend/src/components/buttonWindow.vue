<template>
  <div class="button-window">

    
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

.toolbar {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.toolbar-btn {
  padding: 10px 15px;
  background: #f0f0f0;
  border: 1px solid #ddd;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.toolbar-btn:hover {
  background: #e0e0e0;
  transform: translateY(-2px);
}
</style>