<template>
  <div class="time-select-container">
    <div class="selection-mode">
      <label class="checkbox-container">
        <input 
          type="checkbox" 
          v-model="useRealTime"
          @change="onModeChange"
        />
        <span class="checkmark"></span>
        使用真实时间选择
      </label>
    </div>

    <!-- 时间步选择模式 -->
    <div v-if="!useRealTime" class="timestep-mode">
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
    </div>

    <!-- 真实时间选择模式 -->
    <div v-if="useRealTime" class="realtime-mode">
      <div class="time-input-group">
        <label for="start-real-date">开始日期：</label>
        <input 
          type="date" 
          id="start-real-date" 
          v-model="startRealDate" 
          min="2019-01-02"
          max="2020-12-31"
          @change="updateTimeRangeFromReal"
        />
      </div>

      <div class="time-input-group">
        <label for="start-real-time">开始时间：</label>
        <input 
          type="time" 
          id="start-real-time" 
          v-model="startRealTime" 
          min="09:10"
          max="15:05"
          step="60"
          @change="updateTimeRangeFromReal"
        />
      </div>
      
      <div class="time-input-group">
        <label for="end-real-date">结束日期：</label>
        <input 
          type="date" 
          id="end-real-date" 
          v-model="endRealDate" 
          :min="startRealDate || '2019-01-02'"
          max="2020-12-31"
          @change="updateTimeRangeFromReal"
        />
      </div>

      <div class="time-input-group">
        <label for="end-real-time">结束时间：</label>
        <input 
          type="time" 
          id="end-real-time" 
          v-model="endRealTime" 
          min="09:10"
          max="15:05"
          step="60"
          @change="updateTimeRangeFromReal"
        />
      </div>
      
      <div class="time-tips">
        <p>提示：只能选择交易日的交易时间，可精确到分钟</p>
        <p>交易时间：09:15-09:30 (盘前竞价), 09:30-11:30 (上午), 13:00-15:00 (下午), 15:00-15:05 (盘后竞价)</p>
        <p>系统会自动将时间四舍五入到最近的5分钟时间点</p>
      </div>
    </div>
    
    <div class="time-info">
      <p>播放范围: {{ startTime }} - {{ endTime }} ({{ endTime - startTime + 1 }} 步)</p>
      <div v-if="startRealTimeDisplay && endRealTimeDisplay" class="real-time-range">
        <p>实际时间: {{ startRealTimeDisplay }} 至 {{ endRealTimeDisplay }}</p>
      </div>
      <p v-if="clusterBase !== undefined">聚类基础: {{ clusterBase }}</p>
    </div>

    <div v-if="errorMessage" class="error-message">
      <p>{{ errorMessage }}</p>
    </div>
  </div>
</template>
  
<script>
import { timeConverter } from '../utils/timeConverter.js';
import axios from 'axios';

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
      startRealTime: '09:30',
      endRealTime: '10:30',
      startRealDate: '2019-01-02',
      endRealDate: '2019-01-02',
      useRealTime: false,
      startRealTimeDisplay: '',
      endRealTimeDisplay: '',
      errorMessage: ''
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
        this.startRealTimeDisplay = startReal;
        this.endRealTimeDisplay = endReal;
      } catch (error) {
        console.error('更新时间范围真实时间失败:', error);
        this.startRealTimeDisplay = '';
        this.endRealTimeDisplay = '';
      }
    },

    // 切换选择模式
    onModeChange() {
      this.errorMessage = '';
      if (this.useRealTime) {
        // 如果切换到真实时间模式，使用当前时间步对应的真实时间作为初始值
        this.initializeRealTimeInputs();
      }
    },

    // 初始化真实时间输入框
    async initializeRealTimeInputs() {
      try {
        const [startReal, endReal] = await Promise.all([
          timeConverter.convertTimeStep(this.startTime),
          timeConverter.convertTimeStep(this.endTime)
        ]);
        
        // 分离日期和时间
        this.parseDateTime(startReal, 'start');
        this.parseDateTime(endReal, 'end');
      } catch (error) {
        console.error('初始化真实时间输入失败:', error);
        // 设置默认值
        this.startRealDate = '2019-01-02';
        this.startRealTime = '09:30';
        this.endRealDate = '2019-01-02';
        this.endRealTime = '10:30';
      }
    },

    // 解析日期时间字符串
    parseDateTime(dateTimeStr, prefix) {
      // dateTimeStr格式: "2019-01-02 09:30:00"
      if (!dateTimeStr) return;
      
      const [date, time] = dateTimeStr.split(' ');
      const timeOnly = time.substring(0, 5); // 提取HH:MM部分
      
      if (prefix === 'start') {
        this.startRealDate = date;
        this.startRealTime = timeOnly;
      } else {
        this.endRealDate = date;
        this.endRealTime = timeOnly;
      }
    },

    // 构建完整的日期时间字符串
    buildDateTime(date, time) {
      if (!date || !time) return '';
      return `${date} ${time}`;
    },

    // 从真实时间更新时间范围
    async updateTimeRangeFromReal() {
      if (!this.startRealDate || !this.startRealTime || !this.endRealDate || !this.endRealTime) {
        return;
      }

      this.errorMessage = '';

      try {
        // 构建完整的日期时间字符串
        const startTimeForAPI = this.buildDateTime(this.startRealDate, this.startRealTime);
        const endTimeForAPI = this.buildDateTime(this.endRealDate, this.endRealTime);

        // 调用后端API转换为时间步
        const [startResponse, endResponse] = await Promise.all([
          axios.post('http://localhost:5050/api/timestep', {
            time: startTimeForAPI
          }),
          axios.post('http://localhost:5050/api/timestep', {
            time: endTimeForAPI
          })
        ]);

        const newStartTime = startResponse.data.time_step;
        const newEndTime = endResponse.data.time_step;

        // 确保结束时间不小于开始时间
        if (newEndTime < newStartTime) {
          this.errorMessage = '结束时间不能早于开始时间';
          return;
        }

        // 更新时间步
        this.startTime = newStartTime;
        this.endTime = newEndTime;

        // 更新真实时间显示
        await this.updateRealTimes();

        // 发送事件
        this.$emit('update-time-range', {
          start: parseInt(this.startTime),
          end: parseInt(this.endTime)
        });

        console.log(`真实时间转换: ${startTimeForAPI} -> ${newStartTime}, ${endTimeForAPI} -> ${newEndTime}`);

        // 显示实际使用的时间（四舍五入后的时间）
        const actualStartTime = await timeConverter.convertTimeStep(newStartTime);
        const actualEndTime = await timeConverter.convertTimeStep(newEndTime);
        
        if (actualStartTime !== startTimeForAPI || actualEndTime !== endTimeForAPI) {
          console.log(`时间已自动调整: ${startTimeForAPI} -> ${actualStartTime}, ${endTimeForAPI} -> ${actualEndTime}`);
        }

      } catch (error) {
        console.error('真实时间转换失败:', error);
        if (error.response && error.response.data && error.response.data.message) {
          this.errorMessage = `时间转换失败: ${error.response.data.message}`;
        } else {
          this.errorMessage = '时间转换失败，请检查时间格式和是否为交易时间';
        }
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

.selection-mode {
  padding: 10px;
  background: #f8f9fa;
  border-radius: 4px;
  border: 1px solid #e9ecef;
}

.checkbox-container {
  display: flex;
  align-items: center;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
}

.checkbox-container input[type="checkbox"] {
  margin-right: 8px;
  cursor: pointer;
}

.checkmark {
  margin-left: 0;
}

.timestep-mode, .realtime-mode {
  display: flex;
  flex-direction: column;
  gap: 12px;
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
  transition: border-color 0.15s ease-in-out;
}

.time-input-group input:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25);
}

.time-input-group input[type="datetime-local"] {
  cursor: pointer;
}

.time-tips {
  background: #fff3cd;
  padding: 8px 10px;
  border-radius: 4px;
  border: 1px solid #ffeaa7;
  font-size: 12px;
  color: #856404;
}

.time-tips p {
  margin: 0 0 4px 0;
}

.time-tips p:last-child {
  margin-bottom: 0;
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

.error-message {
  background: #f8d7da;
  padding: 8px 10px;
  border-radius: 4px;
  border: 1px solid #f5c6cb;
  color: #721c24;
  font-size: 12px;
}

.error-message p {
  margin: 0;
  font-weight: 500;
}
</style>
  