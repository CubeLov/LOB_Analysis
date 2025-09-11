<template>
  <div class="time-select-container">
    <div class="time-input-group">
      <label for="start-time">开始时间步：</label>
      <input 
        type="number" 
        id="start-time" 
        v-model="startTime" 
        min="0" 
        max="100"
        @change="updateTimeRange"
      />
    </div>
    
    <div class="time-input-group">
      <label for="end-time">结束时间步：</label>
      <input 
        type="number" 
        id="end-time" 
        v-model="endTime" 
        :min="startTime" 
        max="100"
        @change="updateTimeRange"
      />
    </div>
    
    <div class="time-info">
      <p>播放范围: {{ startTime }} - {{ endTime }} ({{ endTime - startTime + 1 }} 步)</p>
      <p v-if="clusterBase !== undefined">聚类基础: {{ clusterBase }}</p>
    </div>
  </div>
</template>
  
<script>
export default {
  props: {
    clusterBase: {
      type: Number,
      default: 0
    }
  },
  data() {
    return {
      startTime: 0,
      endTime: 10,
    };
  },
  methods: {
    updateTimeRange() {
      // 确保结束时间不小于开始时间
      if (this.endTime < this.startTime) {
        this.endTime = this.startTime;
      }
      
      this.$emit('update-time-range', {
        start: parseInt(this.startTime),
        end: parseInt(this.endTime)
      });
    }
  },
  watch: {
    clusterBase(newBase) {
      // 当聚类基础改变时，可以调整时间范围
      if (newBase > this.endTime) {
        this.endTime = Math.min(newBase + 10, 100);
        this.updateTimeRange();
      }
    }
  },
  mounted() {
    this.updateTimeRange();
  }
};
</script>

<style scoped>
.time-select-container {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.time-input-group {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.time-input-group label {
  font-weight: 500;
  color: #6c757d;
  font-size: 14px;
}

.time-input-group input {
  padding: 8px 12px;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-size: 14px;
}

.time-info {
  background: #e9ecef;
  padding: 10px;
  border-radius: 4px;
  font-size: 12px;
  color: #495057;
}

.time-info p {
  margin: 0 0 5px 0;
}

.time-info p:last-child {
  margin-bottom: 0;
}
</style>
  