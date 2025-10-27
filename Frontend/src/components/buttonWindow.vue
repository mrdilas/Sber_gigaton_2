<template>
  <div class="button-window">
    <div class="block-info">
      информация о сайте
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
  background-color: #bbb7b7;
  border-radius: 20px;
  border: 2px solid #777575;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  margin: 0px 30px 0px 0px;
}
</style>