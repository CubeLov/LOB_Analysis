<template>
  <div class="home-container">
    <div class="control-panel">
      <h2>LOB Analysis Dashboard</h2>
      
      <div class="status-info">
        <p>股票总数: {{ stocks.length }}</p>
        <p>已选择: {{ selectedStocks.length }}</p>
        <p>聚类状态: {{ clustersGenerated ? '已生成' : '未生成' }}</p>
        <p>当前时间: {{ currentRealTime || `时间步 ${currentTimeStep}` }}</p>
      </div>

      <div class="control-section">
        <h3>1. 股票选择</h3>
        <StockSelect :stocks="stocks" :stock-names="stockNames" :format-stock-code="formatStockCode" @update-selected-stocks="setSelectedStocks" />
      </div>
      
      <div class="control-section">
        <h3>2. 聚类配置</h3>
        <div class="cluster-config">
          <div class="cluster-time-mode">
            <label class="checkbox-container">
              <input 
                type="checkbox" 
                v-model="useRealTimeForCluster"
                @change="onClusterModeChange"
              />
              <span class="checkmark"></span>
              使用真实时间选择
            </label>
          </div>

          <!-- 时间步选择模式 -->
          <div v-if="!useRealTimeForCluster" class="timestep-cluster-mode">
            <label for="cluster-timestep">聚类基础时间步：</label>
            <input 
              type="number" 
              id="cluster-timestep" 
              v-model="clusterBaseTimeStep" 
              min="0" 
              max="1000"
              @change="onClusterBaseChange"
            />
          </div>

          <!-- 真实时间选择模式 -->
          <div v-if="useRealTimeForCluster" class="realtime-cluster-mode">
            <div class="cluster-time-input-group">
              <label for="cluster-real-date">聚类基础日期：</label>
              <input 
                type="date" 
                id="cluster-real-date" 
                v-model="clusterRealDate" 
                min="2019-01-02"
                max="2020-12-31"
                @change="updateClusterTimeFromReal"
              />
            </div>

            <div class="cluster-time-input-group">
              <label for="cluster-real-time">聚类基础时间：</label>
              <input 
                type="time" 
                id="cluster-real-time" 
                v-model="clusterRealTime" 
                min="09:10"
                max="15:05"
                step="60"
                @change="updateClusterTimeFromReal"
              />
            </div>

            <div class="cluster-time-tips">
              <p>提示：选择交易时间作为聚类基础，系统会自动调整到最近的5分钟时间点</p>
            </div>
          </div>
          
          <div v-if="clusterBaseRealTime" class="real-time-display">
            实际使用时间: {{ clusterBaseRealTime }}
          </div>

          <div v-if="clusterErrorMessage" class="cluster-error-message">
            <p>{{ clusterErrorMessage }}</p>
          </div>

          <button @click="generateClusters" :disabled="!selectedStocks.length">生成聚类</button>
        </div>
      </div>

      <div class="control-section">
        <h3>3. 时间范围选择</h3>
        <TimeSelect 
          @update-time-range="setTimeRange" 
          :cluster-base="clusterBaseTimeStep"
        />
      </div>

      <div class="control-section">
        <h3>4. 播放控制</h3>
        <div class="playback-options">
          <div class="skip-option">
            <label class="checkbox-container">
              <input 
                type="checkbox" 
                v-model="skipPrePostMarket"
                @change="onSkipOptionChange"
              />
              <span class="checkmark"></span>
              跳过盘前盘后时间
            </label>
          </div>
        </div>
        <div class="control-buttons">
          <PlaybackButton 
            @playback-clicked="onPlaybackClicked" 
            @stop-playback="stopPlayback"
            :is-playing="isPlaying"
            :disabled="!clustersGenerated"
          />
        </div>
      </div>
    </div>

    <div class="chart-section">
            <StockChart 
        :coordinates="coordinates" 
        :clusterInfo="clusterInfo" 
        :currentTimeStep="currentTimeStep"
        :currentRealTime="currentRealTime"
        :selectedStocks="selectedStocks"
        :clusterColors="clusterColors"
        :stockNames="stockNames"
        :formatStockCode="formatStockCode"
      />
    </div>
  </div>
</template>

<script>
import StockSelect from '../components/StockSelect.vue';
import TimeSelect from '../components/TimeSelect.vue';
import PlaybackButton from '../components/PlaybackButton.vue';
import StockChart from '../components/StockChart.vue';
import axios from 'axios';
import { timeConverter } from '../utils/timeConverter.js';

export default {
  components: {
    StockSelect,
    TimeSelect,
    PlaybackButton,
    StockChart,
  },
  data() {
    return {
      stocks: [],                  // 从后端获取的股票代码列表
      stockNames: {},              // 股票代码到股票名字的映射
      selectedStocks: [],          // 用户选择的股票集合
      clusterBaseTimeStep: 0,      // 聚类基础时间步
      timeRange: { start: 0, end: 10 }, // 播放时间范围
      currentTimeStep: 0,          // 当前显示的时间步
      coordinates: {},             // 获取的坐标数据
      clusterInfo: {},             // 聚类信息
      clusterColors: {},           // 每个聚类的颜色映射
      stockClusterMapping: {},     // 股票到聚类的映射（保持不变）
      clustersGenerated: false,    // 是否已生成聚类
      isPlaying: false,            // 是否正在播放
      playbackInterval: null,      // 播放定时器
      skipPrePostMarket: false,    // 是否跳过盘前盘后时间
      currentRealTime: '',         // 当前真实时间
      clusterBaseRealTime: '',     // 聚类基础真实时间
      useRealTimeForCluster: false, // 是否使用真实时间选择聚类基础时间
      clusterRealDate: '2019-01-02', // 聚类基础日期
      clusterRealTime: '09:30',    // 聚类基础时间
      clusterErrorMessage: ''      // 聚类时间转换错误信息
    };
  },
  methods: {
    // 工具函数：格式化股票代码为6位数字
    formatStockCode(stockCode) {
      // 提取数字部分
      const match = stockCode.match(/(\d+)/);
      if (match) {
        const number = match[1];
        // 补齐为6位
        const paddedNumber = number.padStart(6, '0');
        // 保持原有的前缀（如 sz, sh）
        return stockCode.replace(/\d+/, paddedNumber);
      }
      return stockCode; // 如果没有匹配到数字，返回原始代码
    },
    async fetchStocks() {
      try {
        console.log('开始获取股票列表...');
        const response = await axios.get('http://localhost:5050/api/stocks');
        const stockCodes = response.data.stock_codes || [];
        this.stocks = stockCodes;
        
        // 获取每个股票的详细信息（包括股票名字）
        console.log('开始获取股票名字信息...');
        const stockNamePromises = stockCodes.map(async (stockCode) => {
          try {
            const infoResponse = await axios.get(`http://localhost:5050/api/stock/${stockCode}/info`);
            return {
              code: stockCode,
              name: infoResponse.data.stock_name || stockCode
            };
          } catch (error) {
            console.warn(`获取股票${stockCode}信息失败:`, error.message);
            return {
              code: stockCode,
              name: stockCode // 如果获取失败，使用代码作为名字
            };
          }
        });
        
        const stockInfos = await Promise.all(stockNamePromises);
        
        // 构建股票名字映射
        this.stockNames = {};
        stockInfos.forEach(info => {
          this.stockNames[info.code] = info.name;
        });
        
        console.log('获取到股票数量:', this.stocks.length);
        console.log('股票名字映射:', this.stockNames);
      } catch (error) {
        console.error('无法获取股票列表:', error);
        // 如果后端不可用，使用测试数据
        this.stocks = ['sz000001', 'sz000002', 'sz000007', 'sz000021', 'sz000027'];
        // 为测试数据设置默认名字
        this.stockNames = {
          'sz000001': '平安银行',
          'sz000002': '万科A',
          'sz000007': '全新好',
          'sz000021': '深科技',
          'sz000027': '深圳能源'
        };
      }
    },
    
    setSelectedStocks(selectedStocks) {
      this.selectedStocks = selectedStocks;
      // 清除历史聚类数据，因为股票选择改变了
      this.clearClusterData();
      console.log('选择的股票:', selectedStocks);
    },
    
    setTimeRange(timeRange) {
      this.timeRange = timeRange;
      
      // 只有在没有生成聚类或者当前时间步超出新范围时才重置当前时间步
      if (!this.clustersGenerated || this.currentTimeStep < timeRange.start || this.currentTimeStep > timeRange.end) {
        this.currentTimeStep = timeRange.start;
        // 更新当前真实时间
        this.updateCurrentRealTime();
      }
      
      console.log('设置时间范围:', timeRange);
    },
    
    onClusterBaseChange() {
      // 清除历史聚类数据，因为聚类基础时间步改变了
      this.clearClusterData();
      // 更新聚类基础真实时间
      this.updateClusterBaseRealTime();
    },

    // 切换聚类时间选择模式
    onClusterModeChange() {
      this.clusterErrorMessage = '';
      if (this.useRealTimeForCluster) {
        // 如果切换到真实时间模式，使用当前时间步对应的真实时间作为初始值
        this.initializeClusterRealTimeInputs();
      }
    },

    // 初始化聚类真实时间输入框
    async initializeClusterRealTimeInputs() {
      try {
        const realTime = await timeConverter.convertTimeStep(this.clusterBaseTimeStep);
        this.parseClusterDateTime(realTime);
      } catch (error) {
        console.error('初始化聚类真实时间输入失败:', error);
        // 设置默认值
        this.clusterRealDate = '2019-01-02';
        this.clusterRealTime = '09:30';
      }
    },

    // 解析聚类日期时间字符串
    parseClusterDateTime(dateTimeStr) {
      // dateTimeStr格式: "2019-01-02 09:30:00"
      if (!dateTimeStr) return;
      
      const [date, time] = dateTimeStr.split(' ');
      const timeOnly = time.substring(0, 5); // 提取HH:MM部分
      
      this.clusterRealDate = date;
      this.clusterRealTime = timeOnly;
    },

    // 从真实时间更新聚类基础时间
    async updateClusterTimeFromReal() {
      if (!this.clusterRealDate || !this.clusterRealTime) {
        return;
      }

      this.clusterErrorMessage = '';

      try {
        // 构建完整的日期时间字符串
        const timeForAPI = `${this.clusterRealDate} ${this.clusterRealTime}`;

        // 调用后端API转换为时间步
        const response = await axios.post('http://localhost:5050/api/timestep', {
          time: timeForAPI
        });

        const newTimeStep = response.data.time_step;

        // 更新时间步
        this.clusterBaseTimeStep = newTimeStep;

        // 更新真实时间显示
        await this.updateClusterBaseRealTime();

        // 清除历史聚类数据，因为基础时间改变了
        this.clearClusterData();

        console.log(`聚类时间转换: ${timeForAPI} -> ${newTimeStep}`);

        // 显示实际使用的时间（四舍五入后的时间）
        const actualTime = await timeConverter.convertTimeStep(newTimeStep);
        
        if (actualTime !== timeForAPI) {
          console.log(`聚类时间已自动调整: ${timeForAPI} -> ${actualTime}`);
        }

      } catch (error) {
        console.error('聚类真实时间转换失败:', error);
        if (error.response && error.response.data && error.response.data.message) {
          this.clusterErrorMessage = `时间转换失败: ${error.response.data.message}`;
        } else {
          this.clusterErrorMessage = '时间转换失败，请检查时间格式和是否为交易时间';
        }
      }
    },
    
    onSkipOptionChange() {
      console.log('跳过盘前盘后时间选项改变:', this.skipPrePostMarket);
    },
    
    // 判断某个时间步是否为盘前盘后时间
    // k*50 (k=0,1,2,...) 和 r*50-1 (r=1,2,3,...)
    isPrePostMarketTime(timeStep) {
      // k*50 (k=0,1,2,...)：0, 50, 100, 150, ...
      if (timeStep % 50 === 0) {
        return true;
      }
      
      // r*50-1 (r=1,2,3,...)：49, 99, 149, 199, ...
      if ((timeStep + 1) % 50 === 0 && timeStep > 0) {
        return true;
      }
      
      return false;
    },
    
    // 获取下一个有效的时间步（如果启用跳过功能）
    getNextValidTimeStep(currentStep) {
      if (!this.skipPrePostMarket) {
        return currentStep + 1;
      }
      
      let nextStep = currentStep + 1;
      
      // 如果下一个时间步是盘前盘后时间，继续寻找下一个有效时间步
      while (nextStep <= this.timeRange.end && this.isPrePostMarketTime(nextStep)) {
        nextStep++;
      }
      
      return nextStep;
    },
    
    async generateClusters() {
      if (!this.selectedStocks.length) {
        alert('请先选择股票！');
        return;
      }
      
      try {
        console.log('生成聚类，选择的股票:', this.selectedStocks, '时间步:', this.clusterBaseTimeStep);
        
        // 清除历史聚类数据
        this.clearClusterData();
        
        const response = await axios.post('http://localhost:5050/api/coordinates/cluster', {
          stock_codes: this.selectedStocks,
          time_step: this.clusterBaseTimeStep
        });
        
        console.log('聚类响应:', response.data);
        
        this.clusterInfo = response.data.cluster_info;
        this.coordinates = response.data.coordinates;
        
        // 保存股票到聚类的映射关系
        this.stockClusterMapping = {};
        Object.keys(this.coordinates).forEach(stockCode => {
          const coord = this.coordinates[stockCode];
          if (coord && coord.cluster_id !== undefined) {
            this.stockClusterMapping[stockCode] = coord.cluster_id;
          }
        });
        
        this.generateClusterColors();
        this.clustersGenerated = true;
        
        // 更新当前时间步为聚类基础时间步
        this.currentTimeStep = this.clusterBaseTimeStep;
        
        // 更新当前真实时间显示
        await this.updateCurrentRealTime();
        
        console.log('聚类生成完成:', this.clusterInfo);
        console.log('股票聚类映射:', this.stockClusterMapping);
        console.log('初始坐标:', this.coordinates);
      } catch (error) {
        console.error('生成聚类失败:', error);
        alert('生成聚类失败: ' + error.message);
      }
    },
    
    clearClusterData() {
      // 停止当前播放
      if (this.isPlaying) {
        this.stopPlayback();
      }
      
      // 清除所有历史聚类相关数据
      this.coordinates = {};
      this.clusterInfo = {};
      this.clusterColors = {};
      this.stockClusterMapping = {};
      this.clustersGenerated = false;
      this.currentTimeStep = 0;
      this.currentRealTime = '';
      
      console.log('已清除历史聚类数据');
    },
    
    generateClusterColors() {
      // 重新初始化颜色映射，确保没有历史数据
      this.clusterColors = {};
      const clusterIds = new Set();
      
      // 从 coordinates 中提取聚类ID（后端应该在coordinates中包含cluster_id）
      Object.values(this.coordinates).forEach(coord => {
        if (coord && coord.cluster_id !== undefined) {
          clusterIds.add(coord.cluster_id);
        }
      });
      
      // 如果coordinates中没有cluster_id，检查clusterInfo结构
      if (clusterIds.size === 0 && this.clusterInfo && this.clusterInfo.n_clusters) {
        for (let i = 0; i < this.clusterInfo.n_clusters; i++) {
          clusterIds.add(i);
        }
      }
      
      const colors = [
        '#E74C3C', '#2ECC71', '#3498DB', '#F39C12', '#9B59B6',
        '#1ABC9C', '#E67E22', '#34495E', '#F1C40F', '#8E44AD',
        '#16A085', '#E8524B', '#27AE60', '#2980B9', '#D35400'
      ];
      
      let colorIndex = 0;
      clusterIds.forEach(clusterId => {
        this.clusterColors[clusterId] = colors[colorIndex % colors.length];
        colorIndex++;
      });
      
      console.log('找到的聚类ID:', Array.from(clusterIds));
      console.log('生成的聚类颜色:', this.clusterColors);
    },
    
    async fetchCoordinatesForTimeStep(timeStep) {
      try {
        // 添加请求超时，避免长时间等待
        const response = await axios.post('http://localhost:5050/api/coordinates', {
          stock_codes: this.selectedStocks,
          time_step: timeStep
        }, {
          timeout: 1000 // 1秒超时
        });
        
        // 获取新的坐标数据
        const newCoordinates = response.data.coordinates;
        
        // 将保存的聚类信息应用到新坐标中
        Object.keys(newCoordinates).forEach(stockCode => {
          if (this.stockClusterMapping[stockCode] !== undefined) {
            newCoordinates[stockCode].cluster_id = this.stockClusterMapping[stockCode];
          }
        });
        
        this.coordinates = newCoordinates;
        console.log(`时间步 ${timeStep} 的坐标:`, this.coordinates);
      } catch (error) {
        console.error('获取坐标失败:', error);
        // 如果请求失败，不阻塞播放，继续到下一个时间步
      }
    },
    

    
    onPlaybackClicked() {
      if (this.isPlaying) {
        // 如果正在播放，则暂停（保持当前时间步）
        this.pausePlayback();
        return;
      }
      
      if (!this.clustersGenerated) {
        alert('请先生成聚类！');
        return;
      }
      
      // 开始或继续播放
      this.startPlayback();
    },
    
    startPlayback() {
      // 立即设置播放状态，不等待API
      this.isPlaying = true;
      
      // 如果当前时间步还没有设置或超出范围，从开始播放
      if (this.currentTimeStep < this.timeRange.start || this.currentTimeStep > this.timeRange.end) {
        this.currentTimeStep = this.timeRange.start;
        this.updateCurrentRealTime(); // 更新真实时间
      }
      
      // 如果启用跳过功能且起始时间步是盘前盘后时间，跳转到下一个有效时间步
      if (this.skipPrePostMarket && this.isPrePostMarketTime(this.currentTimeStep)) {
        this.currentTimeStep = this.getNextValidTimeStep(this.currentTimeStep - 1);
        this.updateCurrentRealTime(); // 更新真实时间
      }
      
      console.log('开始播放，时间范围:', this.timeRange, '当前时间步:', this.currentTimeStep);
      console.log('跳过盘前盘后:', this.skipPrePostMarket);
      console.log('使用的聚类映射:', this.stockClusterMapping);
      
      // 异步获取当前时间步数据，但不阻塞播放状态设置
      this.fetchCoordinatesForTimeStep(this.currentTimeStep);
      
      this.playbackInterval = setInterval(() => {
        // 使用新的方法获取下一个有效时间步
        const nextTimeStep = this.getNextValidTimeStep(this.currentTimeStep);
        
        if (nextTimeStep > this.timeRange.end) {
          this.stopPlayback();
          return;
        }
        
        this.currentTimeStep = nextTimeStep;
        this.updateCurrentRealTime(); // 更新真实时间
        
        // 异步获取数据，不阻塞定时器
        this.fetchCoordinatesForTimeStep(this.currentTimeStep);
        
        const skipInfo = this.skipPrePostMarket ? ' (已启用跳过盘前盘后)' : '';
        console.log(`播放时间步: ${this.currentTimeStep}${skipInfo}`);
      }, 1000); // 每秒更新一次
    },
    
    pausePlayback() {
      // 立即停止定时器
      if (this.playbackInterval) {
        clearInterval(this.playbackInterval);
        this.playbackInterval = null;
      }
      this.isPlaying = false;
      console.log(`播放已暂停在时间步: ${this.currentTimeStep}`);
    },
    
    stopPlayback() {
      // 立即停止定时器
      if (this.playbackInterval) {
        clearInterval(this.playbackInterval);
        this.playbackInterval = null;
      }
      this.isPlaying = false;
      
      // 重置到时间范围的开始
      this.currentTimeStep = this.timeRange.start;
      this.updateCurrentRealTime(); // 更新真实时间
      
      // 立即显示重置后的时间步
      this.fetchCoordinatesForTimeStep(this.currentTimeStep);
      
      console.log('播放已停止，重置到时间步:', this.currentTimeStep);
    },

    // 更新当前真实时间
    async updateCurrentRealTime() {
      try {
        this.currentRealTime = await timeConverter.convertTimeStep(this.currentTimeStep);
      } catch (error) {
        console.error('更新当前真实时间失败:', error);
        this.currentRealTime = '';
      }
    },

    // 更新聚类基础真实时间
    async updateClusterBaseRealTime() {
      try {
        this.clusterBaseRealTime = await timeConverter.convertTimeStep(this.clusterBaseTimeStep);
      } catch (error) {
        console.error('更新聚类基础真实时间失败:', error);
        this.clusterBaseRealTime = '';
      }
    }
  },
  mounted() {
    console.log('HomeView组件已挂载');
    this.fetchStocks();
    // 初始化时间显示
    this.updateCurrentRealTime();
    this.updateClusterBaseRealTime();
  }
};
</script>

<style scoped>
.home-container {
  display: flex;
  height: 100vh;
  gap: 20px;
  padding: 20px;
}

.control-panel {
  flex: 0 0 400px;
  background: #f8f9fa;
  border-radius: 8px;
  padding: 20px;
  overflow-y: auto;
}

.control-panel h2 {
  margin: 0 0 20px 0;
  color: #333;
  text-align: center;
}

.status-info {
  background: #e9ecef;
  padding: 15px;
  border-radius: 8px;
  margin-bottom: 20px;
  border-left: 4px solid #007bff;
}

.status-info p {
  margin: 5px 0;
  font-family: monospace;
  font-size: 14px;
}

.control-section {
  margin-bottom: 25px;
  padding: 20px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.control-section h3 {
  margin: 0 0 15px 0;
  color: #495057;
  font-size: 16px;
  font-weight: 600;
}

.cluster-config {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.cluster-config label {
  font-weight: 500;
  color: #6c757d;
}

.cluster-config input {
  padding: 8px 12px;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-size: 14px;
}

.cluster-config button {
  padding: 10px 16px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
}

.cluster-config button:hover:not(:disabled) {
  background: #0056b3;
}

.cluster-config button:disabled {
  background: #6c757d;
  cursor: not-allowed;
}

.cluster-time-mode {
  padding: 8px;
  background: #f8f9fa;
  border-radius: 4px;
  border: 1px solid #e9ecef;
  margin-bottom: 10px;
}

.timestep-cluster-mode, .realtime-cluster-mode {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.cluster-time-input-group {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.cluster-time-input-group label {
  font-weight: 500;
  color: #6c757d;
  font-size: 14px;
}

.cluster-time-input-group input {
  padding: 8px 12px;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-size: 14px;
  transition: border-color 0.15s ease-in-out;
}

.cluster-time-input-group input:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25);
}

.cluster-time-tips {
  background: #fff3cd;
  padding: 8px 10px;
  border-radius: 4px;
  border: 1px solid #ffeaa7;
  font-size: 12px;
  color: #856404;
}

.cluster-time-tips p {
  margin: 0;
}

.cluster-error-message {
  background: #f8d7da;
  padding: 8px 10px;
  border-radius: 4px;
  border: 1px solid #f5c6cb;
  color: #721c24;
  font-size: 12px;
}

.cluster-error-message p {
  margin: 0;
  font-weight: 500;
}

.real-time-display {
  margin-top: 8px;
  padding: 8px 12px;
  background: #e3f2fd;
  border: 1px solid #bbdefb;
  border-radius: 4px;
  font-size: 12px;
  color: #1565c0;
  font-family: monospace;
}

.real-time-display {
  font-size: 12px;
  color: #28a745;
  background: #f8f9fa;
  padding: 6px 10px;
  border-radius: 4px;
  border-left: 3px solid #28a745;
  margin: 5px 0;
  font-family: monospace;
}

.playback-options {
  margin-bottom: 20px;
}

.skip-option {
  padding: 15px;
  background: #f8f9fa;
  border-radius: 6px;
  border: 1px solid #e9ecef;
}

.checkbox-container {
  display: flex;
  align-items: center;
  cursor: pointer;
  font-weight: 500;
  color: #495057;
  user-select: none;
}

.checkbox-container input[type="checkbox"] {
  margin-right: 10px;
  transform: scale(1.2);
  cursor: pointer;
}

.option-description {
  margin-top: 8px;
  font-size: 12px;
  color: #6c757d;
  font-style: italic;
}

.control-buttons {
  display: flex;
  flex-direction: column;
  gap: 15px;
  align-items: center;
}

.chart-section {
  flex: 1;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  overflow: hidden;
}
</style>
