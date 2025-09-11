<template>
    <button @click="onPlaybackClicked">播放</button>
  </template>
  
  <script>
  export default {
    methods: {
      onPlaybackClicked() {
        this.$emit('playback-clicked');
      }
    }
  };
  </script>
  