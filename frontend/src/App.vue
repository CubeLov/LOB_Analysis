<template>
  <div id="app">
    <div style="padding: 20px;">
      <h1>LOB Analysis Dashboard</h1>
      <HomeView />
    </div>
  </div>
</template>

<script>
import HomeView from './views/HomeView.vue';

export default {
  name: 'App',
  components: {
    HomeView
  }
};
</script>

<style>
#app {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  margin: 0;
  padding: 0;
  min-height: 100vh;
  background-color: #f5f5f5;
}

body {
  margin: 0;
  padding: 0;
}
</style>
