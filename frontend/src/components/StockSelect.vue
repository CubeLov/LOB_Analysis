<template>
  <div class="stock-select-container">
    <div class="select-header">
      <label>选择股票 ({{ selectedStocks.length }}/{{ stocks.length }})</label>
      <div class="select-actions">
        <button @click="selectAll" class="action-btn">全选</button>
        <button @click="clearAll" class="action-btn">清空</button>
      </div>
    </div>
    
    <div class="search-box">
      <input 
        type="text" 
        v-model="searchQuery" 
        placeholder="搜索股票代码..."
        class="search-input"
      />
    </div>
    
    <div class="stock-list">
      <div 
        v-for="stock in filteredStocks" 
        :key="stock"
        class="stock-item"
        :class="{ selected: selectedStocks.includes(stock) }"
        @click="toggleStock(stock)"
      >
        <input
          type="checkbox"
          :checked="selectedStocks.includes(stock)"
          @change="toggleStock(stock)"
          @click.stop
        />
        <span class="stock-code">{{ stock }}</span>
      </div>
      
      <div v-if="filteredStocks.length === 0" class="no-results">
        没有找到匹配的股票
      </div>
    </div>
  </div>
</template>

<script>
export default {
  props: {
    stocks: {
      type: Array,
      default: () => []
    }
  },
  data() {
    return {
      selectedStocks: [],
      searchQuery: ''
    };
  },
  computed: {
    filteredStocks() {
      if (!this.searchQuery) {
        return this.stocks;
      }
      return this.stocks.filter(stock => 
        stock.toLowerCase().includes(this.searchQuery.toLowerCase())
      );
    }
  },
  methods: {
    toggleStock(stock) {
      const index = this.selectedStocks.indexOf(stock);
      if (index > -1) {
        this.selectedStocks.splice(index, 1);
      } else {
        this.selectedStocks.push(stock);
      }
      // 确保立即触发更新事件
      this.$emit('update-selected-stocks', [...this.selectedStocks]);
    },
    selectAll() {
      this.selectedStocks = [...this.filteredStocks];
      this.$emit('update-selected-stocks', [...this.selectedStocks]);
    },
    clearAll() {
      this.selectedStocks = [];
      this.$emit('update-selected-stocks', []);
    }
  },
  watch: {
    // 移除 watcher 中的 emit，避免与方法中的 emit 重复
    // selectedStocks 的变化现在直接在方法中处理
  }
};
</script>

<style scoped>
.stock-select-container {
  display: flex;
  flex-direction: column;
  height: 300px;
}

.select-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.select-header label {
  font-weight: 500;
  color: #495057;
}

.select-actions {
  display: flex;
  gap: 8px;
}

.action-btn {
  padding: 4px 8px;
  background: #6c757d;
  color: white;
  border: none;
  border-radius: 3px;
  cursor: pointer;
  font-size: 12px;
}

.action-btn:hover {
  background: #5a6268;
}

.search-box {
  margin-bottom: 10px;
}

.search-input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-size: 14px;
}

.stock-list {
  flex: 1;
  overflow-y: auto;
  border: 1px solid #e9ecef;
  border-radius: 4px;
  max-height: 200px;
}

.stock-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.stock-item:hover {
  background-color: #f8f9fa;
}

.stock-item.selected {
  background-color: #e3f2fd;
}

.stock-item input[type="checkbox"] {
  margin: 0;
}

.stock-code {
  font-family: 'Monaco', 'Consolas', monospace;
  font-size: 13px;
  color: #495057;
}

.no-results {
  padding: 20px;
  text-align: center;
  color: #6c757d;
  font-style: italic;
}

/* 滚动条样式 */
.stock-list::-webkit-scrollbar {
  width: 6px;
}

.stock-list::-webkit-scrollbar-track {
  background: #f1f1f1;
}

.stock-list::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.stock-list::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}
</style>
