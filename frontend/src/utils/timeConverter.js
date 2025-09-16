/**
 * 时间转换工具函数
 * 用于将时间步转换为真实时间
 */

import axios from 'axios';

class TimeConverter {
  constructor() {
    // 缓存已转换的时间，避免重复请求
    this.timeCache = new Map();
    // 请求队列，避免同时请求相同的时间步
    this.requestQueue = new Map();
  }

  /**
   * 将时间步转换为真实时间
   * @param {number} timeStep - 时间步
   * @returns {Promise<string>} 真实时间字符串
   */
  async convertTimeStep(timeStep) {
    // 如果已经缓存了，直接返回
    if (this.timeCache.has(timeStep)) {
      return this.timeCache.get(timeStep);
    }

    // 如果正在请求中，等待请求完成
    if (this.requestQueue.has(timeStep)) {
      return await this.requestQueue.get(timeStep);
    }

    // 创建新的请求
    const requestPromise = this._fetchTimeFromApi(timeStep);
    this.requestQueue.set(timeStep, requestPromise);

    try {
      const realTime = await requestPromise;
      // 缓存结果
      this.timeCache.set(timeStep, realTime);
      return realTime;
    } finally {
      // 清除请求队列
      this.requestQueue.delete(timeStep);
    }
  }

  /**
   * 批量转换时间步
   * @param {number[]} timeSteps - 时间步数组
   * @returns {Promise<Object>} 时间步到真实时间的映射对象
   */
  async convertTimeSteps(timeSteps) {
    const promises = timeSteps.map(timeStep => 
      this.convertTimeStep(timeStep).then(realTime => ({
        timeStep,
        realTime
      }))
    );

    const results = await Promise.all(promises);
    const mapping = {};
    
    results.forEach(({ timeStep, realTime }) => {
      mapping[timeStep] = realTime;
    });

    return mapping;
  }

  /**
   * 从API获取真实时间
   * @param {number} timeStep - 时间步
   * @returns {Promise<string>} 真实时间字符串
   */
  async _fetchTimeFromApi(timeStep) {
    try {
      const response = await axios.post('http://localhost:5050/api/times', {
        time_step: timeStep
      });

      return response.data.accurate_time;
    } catch (error) {
      console.error(`获取时间步 ${timeStep} 的真实时间失败:`, error);
      // 如果API请求失败，返回原始时间步作为备选
      return `时间步 ${timeStep}`;
    }
  }

  /**
   * 格式化真实时间显示（可选的格式化方法）
   * @param {string} realTime - 真实时间字符串
   * @returns {string} 格式化后的时间字符串
   */
  formatRealTime(realTime) {
    try {
      // 如果是标准时间格式，可以进行格式化
      const date = new Date(realTime);
      if (!isNaN(date.getTime())) {
        return date.toLocaleString('zh-CN', {
          year: 'numeric',
          month: '2-digit',
          day: '2-digit',
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit'
        });
      }
    } catch (error) {
      console.warn('时间格式化失败:', error);
    }
    
    // 如果格式化失败，返回原始字符串
    return realTime;
  }

  /**
   * 清除缓存
   */
  clearCache() {
    this.timeCache.clear();
    this.requestQueue.clear();
  }

  /**
   * 获取缓存状态信息
   */
  getCacheInfo() {
    return {
      cacheSize: this.timeCache.size,
      queueSize: this.requestQueue.size,
      cachedTimeSteps: Array.from(this.timeCache.keys())
    };
  }
}

// 创建单例实例
export const timeConverter = new TimeConverter();

// 导出类供需要时使用
export { TimeConverter };

// 便捷函数
export const convertTimeStep = (timeStep) => timeConverter.convertTimeStep(timeStep);
export const convertTimeSteps = (timeSteps) => timeConverter.convertTimeSteps(timeSteps);
export const formatRealTime = (realTime) => timeConverter.formatRealTime(realTime);