<template>
  <div>
    <label for="stocks">选择股票：</label>
    <div v-for="stock in stocks" :key="stock">
      <input
        type="checkbox"
        :value="stock"
        v-model="selectedStocks"
      />
      {{ stock }}
    </div>
  </div>
</template>

<script>
export default {
  props: ['stocks'],
  data() {
    return {
      selectedStocks: [],
    };
  },
  watch: {
    selectedStocks(newSelection) {
      this.$emit('update-selected-stocks', newSelection);
    }
  }
};
</script>
