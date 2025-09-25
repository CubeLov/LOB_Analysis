<template>
  <div class="chart-wrapper">
    <div class="chart-header">
      <h3>股票聚类可视化</h3>
      <div class="chart-info">
        <span v-if="currentRealTime">当前时间: {{ currentRealTime }}</span>
        <span v-else-if="currentTimeStep !== undefined">时间步: {{ currentTimeStep }}</span>
        <span v-if="selectedStocks.length">显示股票: {{ selectedStocks.length }}只</span>
      </div>
    </div>
    
    <div ref="chartContainer" class="chart-container"></div>
    
    <div v-if="Object.keys(clusterColors).length" class="legend-container">
      <h4>聚类图例</h4>
      <div class="legend-items">
        <div 
          v-for="(color, clusterId) in clusterColors" 
          :key="clusterId"
          class="legend-item"
        >
          <div class="legend-color" :style="{ backgroundColor: color }"></div>
          <span>聚类 {{ clusterId }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, watch, nextTick } from 'vue';
import Plotly from 'plotly.js-dist';

export default {
  props: {
    coordinates: {
      type: Object,
      default: () => ({})
    },
    clusterInfo: {
      type: Object,
      default: () => ({})
    },
    currentTimeStep: {
      type: Number,
      default: undefined
    },
    selectedStocks: {
      type: Array,
      default: () => []
    },
    clusterColors: {
      type: Object,
      default: () => ({})
    },
    stockNames: {
      type: Object,
      default: () => ({})
    },
    formatStockCode: {
      type: Function,
      required: true
    },
    currentRealTime: {
      type: String,
      default: ''
    }
  },
  setup(props) {
    const chartContainer = ref(null);
    let isInitialized = false;

    const calculateEndTime = (startTime, timeStep) => {
      try {
        // 分割日期和时间部分 "YYYY-MM-DD HH:MM"
        const [datePart, timePart] = startTime.split(' ');
        if (!datePart || !timePart) {
          return startTime; // 格式不正确时返回原始值
        }
        
        // 分割年月日
        const [year, month, day] = datePart.split('-').map(Number);
        // 分割小时和分钟
        const [hours, minutes] = timePart.split(':').map(Number);
        
        // 确定需要添加的分钟数
        const minutesToAdd = (timeStep % 50 === 0) ? 15 : 5;
        
        // 计算总分钟数并处理进位
        let totalMinutes = hours * 60 + minutes + minutesToAdd;
        let newHours = Math.floor(totalMinutes / 60);
        let newMinutes = totalMinutes % 60;
        let newDay = day;
        
        // 格式化数字为两位数
        const pad = (num) => num.toString().padStart(2, '0');
        
        // 组合成新的时间字符串
        return `${year}-${pad(month)}-${pad(newDay)} ${pad(newHours)}:${pad(newMinutes)}`;
      } catch (error) {
        console.error('计算结束时间失败:', error);
        return startTime;
      }
    };

    // 格式化时间段显示
    const formatTimeRange = (startTime, timeStep) => {
      const endTime = calculateEndTime(startTime, timeStep);
      return `${startTime} ~ ${endTime}`;
    };

    const drawChart = (coordinates, clusterInfo, clusterColors, animate = false) => {
      nextTick(() => {
        if (!chartContainer.value) {
          console.log('图表容器不可用');
          return;
        }

        if (!coordinates || !Object.keys(coordinates).length) {
          console.log('没有坐标数据，清空图表');
          // 如果没有数据，显示空图表
          const emptyLayout = {
            title: '请选择股票并生成聚类',
            xaxis: { title: 'UMAP 坐标 1' },
            yaxis: { title: 'UMAP 坐标 2' },
            showlegend: false
          };
          Plotly.newPlot(chartContainer.value, [], emptyLayout);
          return;
        }

        console.log('绘制图表:', {
          coordinates: Object.keys(coordinates).length,
          clusterInfo: Object.keys(clusterInfo || {}).length,
          clusterColors: Object.keys(clusterColors || {}).length,
          animate
        });

        // 准备数据按聚类分组
        const clusterGroups = {};
        const stockCodes = Object.keys(coordinates);

        // 将股票按聚类分组
        stockCodes.forEach(stockCode => {
          const coord = coordinates[stockCode];
          if (!coord) return;

          // 聚类ID应该在坐标数据中
          const clusterId = coord.cluster_id ?? -1;
          
          if (!clusterGroups[clusterId]) {
            clusterGroups[clusterId] = {
              x: [],
              y: [],
              text: [],           // 图表上显示的文本（股票名字）
              stockNames: [],     // 悬停时显示的股票名字
              stockCodes: [],     // 悬停时显示的股票代码
              originalCodes: []   // 原始股票代码（用于内部处理）
            };
          }

          clusterGroups[clusterId].x.push(coord.umap1);
          clusterGroups[clusterId].y.push(coord.umap2);
          
          const stockName = props.stockNames[stockCode] || stockCode;
          const formattedCode = props.formatStockCode(stockCode);
          
          // 图表上显示股票名字
          clusterGroups[clusterId].text.push(stockName);
          // 悬停时分别存储股票名字和代码
          clusterGroups[clusterId].stockNames.push(stockName);
          clusterGroups[clusterId].stockCodes.push(formattedCode);
          clusterGroups[clusterId].originalCodes.push(stockCode);
        });

        // 创建Plotly数据
        const data = Object.keys(clusterGroups).map(clusterId => {
          const group = clusterGroups[clusterId];
          const color = clusterColors[clusterId] || '#999999';
          
          return {
            x: group.x,
            y: group.y,
            mode: 'markers+text',
            type: 'scatter',
            name: clusterId === '-1' ? '未分类' : `聚类 ${clusterId}`,
            text: group.text,        // 图表上显示的文本（只有股票名字）
            customdata: group.stockNames.map((name, index) => [name, group.stockCodes[index]]), // 传递股票名字和代码
            textposition: 'top center',
            textfont: {
              size: 10,
              color: '#333'
            },
            marker: {
              color: color,
              size: 12,
              line: {
                color: '#fff',
                width: 2
              },
              opacity: 0.8
            },
            hovertemplate: 
              '<b>%{customdata[0]}</b><br>' +
              '股票代码: %{customdata[1]}<br>' +
              'UMAP1: %{x:.2f}<br>' +
              'UMAP2: %{y:.2f}<br>' +
              '聚类: ' + (clusterId === '-1' ? '未分类' : clusterId) +
              '<extra></extra>'
          };
        });

        const layout = {
          title: {
            text: props.currentRealTime ? 
              `股票聚类分布 (${formatTimeRange(props.currentRealTime, props.currentTimeStep ?? 0)})` : 
              `股票聚类分布 (时间步: ${props.currentTimeStep ?? '未知'})`,
            font: { size: 16 }
          },
          xaxis: { 
            title: 'UMAP 坐标 1',
            range: [-15, 25],
            zeroline: true,
            zerolinecolor: '#ddd',
            gridcolor: '#f0f0f0'
          },
          yaxis: { 
            title: 'UMAP 坐标 2',
            range: [-15, 25],
            zeroline: true,
            zerolinecolor: '#ddd',
            gridcolor: '#f0f0f0'
          },
          showlegend: true,
          legend: {
            x: 1.02,
            y: 1,
            bgcolor: 'rgba(255,255,255,0.8)',
            bordercolor: '#ddd',
            borderwidth: 1
          },
          autosize: true,
          margin: {
            l: 60,
            r: 150,
            b: 60,
            t: 80
          },
          plot_bgcolor: '#fafafa',
          paper_bgcolor: '#ffffff'
        };

        const config = {
          displayModeBar: true,
          displaylogo: false,
          modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d'],
          responsive: true
        };

        if (!isInitialized) {
          // 初次渲染
          Plotly.newPlot(chartContainer.value, data, layout, config);
          isInitialized = true;
        } else if (animate) {
          // 动画更新
          const update = {};
          data.forEach((trace, index) => {
            update[`x[${index}]`] = [trace.x];
            update[`y[${index}]`] = [trace.y];
          });

          Plotly.animate(chartContainer.value, {
            data: data,
            layout: layout
          }, {
            transition: {
              duration: 250,
              easing: 'cubic-in-out'
            },
            frame: {
              duration: 250,
              redraw: true
            }
          });
        } else {
          // 静态更新
          Plotly.react(chartContainer.value, data, layout, config);
        }
      });
    };

    // 监听数据变化
    watch(
      () => [props.coordinates, props.clusterInfo, props.clusterColors, props.currentTimeStep, props.stockNames, props.formatStockCode, props.currentRealTime],
      (newValues, oldValues) => {
        // 安全地解构新值
        const [newCoords, newClusterInfo, newClusterColors] = newValues || [{}, {}, {}];
        
        // 安全地解构旧值
        const [oldCoords] = oldValues || [{}];
        
        const shouldAnimate = isInitialized && 
                            Object.keys(newCoords || {}).length > 0 && 
                            Object.keys(oldCoords || {}).length > 0;
        
        drawChart(newCoords || {}, newClusterInfo || {}, newClusterColors || {}, shouldAnimate);
      },
      { immediate: true, deep: true }
    );

    return { chartContainer };
  }
};
</script>

<style scoped>
.chart-wrapper {
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 20px;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 2px solid #007bff;
}

.chart-header h3 {
  margin: 0;
  color: #333;
  font-size: 20px;
}

.chart-info {
  display: flex;
  gap: 20px;
  font-size: 14px;
  color: #666;
}

.chart-container {
  flex: 1;
  min-height: 400px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.legend-container {
  margin-top: 20px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

.legend-container h4 {
  margin: 0 0 10px 0;
  color: #495057;
  font-size: 14px;
  font-weight: 600;
}

.legend-items {
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #495057;
}

.legend-color {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  border: 2px solid #fff;
  box-shadow: 0 1px 3px rgba(0,0,0,0.2);
}
</style>
