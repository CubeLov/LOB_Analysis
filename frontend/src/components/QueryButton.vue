<template>
    <button @click="onQueryClicked">开始查询</button>
  </template>
  
  <script>
  export default {
    methods: {
      onQueryClicked() {
        this.$emit('query-clicked');
      }
    }
  };
  </script>
  