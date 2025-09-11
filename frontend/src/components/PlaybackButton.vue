<template>
  <div class="playback-controls">
    <button 
      @click="onPlaybackClicked" 
      :disabled="disabled"
      :class="{ 'playing': isPlaying }"
      class="playback-btn"
    >
      {{ isPlaying ? '⏸️ 暂停' : '▶️ 播放' }}
    </button>
    
    <button 
      @click="onStopClicked"
      :disabled="disabled || !isPlaying"
      class="stop-btn"
      :class="{ 'visible': isPlaying }"
    >
      ⏹️ 停止
    </button>
  </div>
</template>
  
<script>
export default {
  props: {
    isPlaying: {
      type: Boolean,
      default: false
    },
    disabled: {
      type: Boolean,
      default: false
    }
  },
  methods: {
    onPlaybackClicked() {
      this.$emit('playback-clicked');
    },
    onStopClicked() {
      this.$emit('stop-playback');
    }
  }
};
</script>

<style scoped>
.playback-controls {
  display: flex;
  gap: 10px;
}

.playback-btn, .stop-btn {
  padding: 10px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: background-color 0.2s;
}

.playback-btn {
  background: #28a745;
  color: white;
}

.playback-btn:hover:not(:disabled) {
  background: #218838;
}

.playback-btn.playing {
  background: #ffc107;
  color: #212529;
}

.playback-btn.playing:hover {
  background: #e0a800;
}

.playback-btn:disabled {
  background: #6c757d;
  cursor: not-allowed;
}

.stop-btn {
  background: #dc3545;
  color: white;
  opacity: 0.6;
  transition: opacity 0.2s;
}

.stop-btn.visible {
  opacity: 1;
}

.stop-btn:hover:not(:disabled) {
  background: #c82333;
}

.stop-btn:disabled {
  background: #6c757d;
  cursor: not-allowed;
  opacity: 0.4;
}
</style>
  