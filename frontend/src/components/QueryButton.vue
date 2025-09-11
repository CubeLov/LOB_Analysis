<template>
  <button 
    @click="onQueryClicked" 
    :disabled="disabled"
    class="query-btn"
  >
    🔍 查询当前时间步
  </button>
</template>
  
<script>
export default {
  props: {
    disabled: {
      type: Boolean,
      default: false
    }
  },
  methods: {
    onQueryClicked() {
      this.$emit('query-clicked');
    }
  }
};
</script>

<style scoped>
.query-btn {
  width: 100%;
  padding: 10px 16px;
  background: #17a2b8;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: background-color 0.2s;
}

.query-btn:hover:not(:disabled) {
  background: #138496;
}

.query-btn:disabled {
  background: #6c757d;
  cursor: not-allowed;
}
</style>
  