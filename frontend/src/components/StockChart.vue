<template>
  <div class="chart-wrapper">
    <div class="chart-header">
      <h3>股票聚类可视化</h3>
      <div class="chart-info">
        <span v-if="currentTimeStep !== undefined">当前时间步: {{ currentTimeStep }}</span>
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
    }
  },
  setup(props) {
    const chartContainer = ref(null);
    let isInitialized = false;

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
              text: [],
              stockCodes: []
            };
          }

          clusterGroups[clusterId].x.push(coord.umap1);
          clusterGroups[clusterId].y.push(coord.umap2);
          clusterGroups[clusterId].text.push(stockCode);
          clusterGroups[clusterId].stockCodes.push(stockCode);
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
            text: group.text,
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
              '<b>%{text}</b><br>' +
              'UMAP1: %{x:.2f}<br>' +
              'UMAP2: %{y:.2f}<br>' +
              '聚类: ' + (clusterId === '-1' ? '未分类' : clusterId) +
              '<extra></extra>'
          };
        });

        const layout = {
          title: {
            text: `股票聚类分布 (时间步: ${props.currentTimeStep ?? '未知'})`,
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
              duration: 800,
              easing: 'cubic-in-out'
            },
            frame: {
              duration: 800,
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
      () => [props.coordinates, props.clusterInfo, props.clusterColors, props.currentTimeStep],
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
