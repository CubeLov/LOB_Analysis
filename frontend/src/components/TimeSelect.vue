<template>
  <div class="time-select-container">
    <div class="time-input-group">
      <label for="start-time">开始时间步：</label>
      <input 
        type="number" 
        id="start-time" 
        v-model="startTime" 
        min="0" 
        max="1000"
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
        max="1000"
        @change="updateTimeRange"
      />
    </div>
    
    <div class="time-info">
      <p>播放范围: {{ startTime }} - {{ endTime }} ({{ endTime - startTime + 1 }} 步)</p>
      <div v-if="startRealTime && endRealTime" class="real-time-range">
        <p>实际时间: {{ startRealTime }} 至 {{ endRealTime }}</p>
      </div>
      <p v-if="clusterBase !== undefined">聚类基础: {{ clusterBase }}</p>
    </div>
  </div>
</template>
  
<script>
import { timeConverter } from '../utils/timeConverter.js';

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
      startRealTime: '',
      endRealTime: ''
    };
  },
  methods: {
    updateTimeRange() {
      // 确保结束时间不小于开始时间
      if (this.endTime < this.startTime) {
        this.endTime = this.startTime;
      }
      
      // 更新真实时间显示
      this.updateRealTimes();
      
      this.$emit('update-time-range', {
        start: parseInt(this.startTime),
        end: parseInt(this.endTime)
      });
    },

    // 更新真实时间显示
    async updateRealTimes() {
      try {
        const [startReal, endReal] = await Promise.all([
          timeConverter.convertTimeStep(this.startTime),
          timeConverter.convertTimeStep(this.endTime)
        ]);
        this.startRealTime = startReal;
        this.endRealTime = endReal;
      } catch (error) {
        console.error('更新时间范围真实时间失败:', error);
        this.startRealTime = '';
        this.endRealTime = '';
      }
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

.real-time-range {
  background: #e8f5e8;
  padding: 8px;
  border-radius: 4px;
  margin: 5px 0;
  border-left: 3px solid #28a745;
}

.real-time-range p {
  font-size: 11px;
  color: #155724;
  font-family: monospace;
}
</style>
  