<template>
  <div ref="chartContainer" class="chart-container"></div>
</template>

<script>
import { ref, watch, nextTick } from 'vue';  // 引入 nextTick
import Plotly from 'plotly.js-dist';

export default {
  props: ['coordinates', 'clusterInfo'],
  setup(props) {
    const chartContainer = ref(null);

    // 定义 drawChart 函数，确保在 watch 中调用时已经定义
    const drawChart = (coordinates, clusterInfo) => {
      // 等待 DOM 更新完成后再执行
      nextTick(() => {
        // 确保 chartContainer 已经存在
        if (chartContainer.value) {
          console.log('Coordinates:', coordinates);
          console.log('Cluster Info:', clusterInfo);

          const data = [];
          const stockCodes = Object.keys(coordinates);

          stockCodes.forEach(stockCode => {
            const coord = coordinates[stockCode];
            const clusterId = clusterInfo[stockCode] ? clusterInfo[stockCode].cluster_id : 0;

            data.push({
              x: [coord.umap1],
              y: [coord.umap2],
              mode: 'markers',
              type: 'scatter',
              name: stockCode,
              marker: {
                color: clusterId, // 根据聚类ID选择颜色
                size: 10,
                showscale: false, // 显示颜色条
              }
            });
          });

          const layout = {
            title: '股票 UMAP 坐标图',
            xaxis: { 
              title: 'UMAP1', 
              range: [-10, 20]  // 设置X轴范围，适应数据
            },
            yaxis: { 
              title: 'UMAP2', 
              range: [-10, 20]  // 设置Y轴范围，适应数据
            },
            showlegend: true,
            autosize: true,  // 自动调整图表大小
            margin: {
              l: 40,  // 左边距
              r: 40,  // 右边距
              b: 40,  // 底边距
              t: 40   // 顶边距
            }
          };

          // 通过 Plotly 渲染图表
          Plotly.newPlot(chartContainer.value, data, layout);
        } else {
          console.error("Chart container is not available.");
        }
      });
    };

    // 监听 props 数据的变化，确保数据变化时重新绘制图表
    watch(
      () => [props.coordinates, props.clusterInfo],
      () => {
        drawChart(props.coordinates, props.clusterInfo);
      },
      { immediate: true } // 组件初次挂载时也会立即执行
    );

    return { chartContainer };
  }
};
</script>

<style scoped>
.chart-container {
  width: 100%;
  height: 500px; /* 设置固定的高度 */
}
</style>
