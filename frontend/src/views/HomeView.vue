<template>
  <div>
    <StockSelect :stocks="stocks" @update-selected-stocks="setSelectedStocks" />
    <TimeSelect @update-time-step="setTimeStep" />
    <QueryButton @query-clicked="onQueryClicked" />
    <PlaybackButton @playback-clicked="onPlaybackClicked" />
    <StockChart :coordinates="coordinates" :clusterInfo="clusterInfo" />
  </div>
</template>

<script>
// import { ref } from 'vue';
import StockSelect from '../components/StockSelect.vue';
import TimeSelect from '../components/TimeSelect.vue';
import QueryButton from '../components/QueryButton.vue';
import PlaybackButton from '../components/PlaybackButton.vue';
import StockChart from '../components/StockChart.vue';
import axios from 'axios';

export default {
  components: {
    StockSelect,
    TimeSelect,
    QueryButton,
    PlaybackButton,
    StockChart,
  },
  data() {
    return {
      stocks: [],        // 从后端获取的股票代码列表
      selectedStocks: [],// 用户选择的股票集合
      timeStep: 0,       // 用户选择的时间步
      coordinates: {},   // 获取的坐标数据
      clusterInfo: {},   // 聚类信息
    };
  },
  methods: {
    async fetchStocks() {
      try {
        const response = await axios.get('http://localhost:5050/api/stocks');
        this.stocks = response.data.stock_codes; // 获取所有股票的代码
      } catch (error) {
        console.error('无法获取股票列表:', error);
      }
    },
    setSelectedStocks(selectedStocks) {
      this.selectedStocks = selectedStocks;
    },
    setTimeStep(timeStep) {
      this.timeStep = timeStep;
    },
    async onQueryClicked() {
      try {
        const response = await axios.post('http://localhost:5050/api/coordinates/cluster', {
          stock_codes: this.selectedStocks, // 发送整个选中的股票集合
          time_step: this.timeStep
        });
        this.coordinates = response.data.coordinates;
        this.clusterInfo = response.data.cluster_info;
        console.log('Received coordinates:', this.coordinates);  // 打印查询结果
        console.log('Received clusterInfo:', this.clusterInfo);
      } catch (error) {
        console.error('查询失败:', error);
      }
    },
    async onPlaybackClicked() {
      let currentStep = this.timeStep;
      const interval = setInterval(async () => {
        try {
          const response = await axios.post('http://localhost:5050/api/coordinates/cluster', {
            stock_codes: this.selectedStocks, // 发送整个选中的股票集合
            time_step: currentStep
          });
          this.coordinates = response.data.coordinates;
          this.clusterInfo = response.data.cluster_info;
          console.log('Playback - Received coordinates:', this.coordinates);
          console.log('Playback - Received clusterInfo:', this.clusterInfo);
          currentStep++;

          // 如果达到最大时间步数，则停止播放
          if (currentStep > 100) {
            clearInterval(interval);
          }
        } catch (error) {
          console.error('播放失败:', error);
          clearInterval(interval);
        }
      }, 2000); // 每秒更新一次
    }
  },
  mounted() {
    this.fetchStocks(); // 加载股票代码
  }
};
</script>
