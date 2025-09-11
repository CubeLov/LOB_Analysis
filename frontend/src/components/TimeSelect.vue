<template>
    <div>
      <label for="time-step">选择时间步：</label>
      <input type="number" id="time-step" v-model="timeStep" min="0" />
    </div>
  </template>
  
  <script>
  export default {
    data() {
      return {
        timeStep: 0,
      };
    },
    watch: {
      timeStep(newTimeStep) {
        this.$emit('update-time-step', newTimeStep);
      }
    }
  };
  </script>
  