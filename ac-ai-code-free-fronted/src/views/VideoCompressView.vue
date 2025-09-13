<template>
  <div class="container">
    <h1>浏览器视频压缩工具</h1>

    <div class="upload-section">
      <div class="file-input-wrapper">
        <button class="file-input-button">选择视频文件</button>
        <input type="file" id="video-input" accept="video/*" multiple @change="handleFileSelect">
      </div>

      <div id="file-list" class="file-list" :style="{ display: selectedFiles.length > 0 ? 'block' : 'none' }">
        <h3>已选择的文件:</h3>
        <div id="file-items">
          <div class="file-item" v-for="(file, index) in selectedFiles" :key="index">
            <span class="file-name">{{ file.name }}</span>
            <span class="file-size">{{ (file.size / (1024 * 1024)).toFixed(2) }} MB</span>
            <button class="remove-file" @click="removeFile(index)">×</button>
          </div>
        </div>
      </div>

      <button id="compress-btn"
              :disabled="selectedFiles.length === 0 || isCompressing"
              @click="compressVideos">
        {{ isCompressing ? '压缩中...' : '开始批量压缩' }}
      </button>
    </div>

    <div class="progress-container">
      <div class="overall-progress">
        <div class="progress-header">
          <span>整体进度</span>
          <span id="overall-progress-text">{{ overallProgress }}%</span>
        </div>
        <div id="progress">
          <div id="progress-bar" :style="{ width: overallProgress + '%' }"></div>
        </div>
      </div>

      <div id="progress-text">{{ progressText }}</div>

      <div id="file-progress-container" class="file-progress-container"
           :style="{ display: isCompressing ? 'block' : 'none' }">
        <h3>文件进度</h3>
        <div id="file-progress-items">
          <div class="file-progress-item"
               v-for="(file, index) in selectedFiles"
               :key="index"
               :id="'file-progress-' + index">
            <div class="file-progress-header">
              <span>{{ file.name }} ({{ (file.size / (1024 * 1024)).toFixed(2) }} MB)</span>
              <span :id="'file-progress-text-' + index">{{ fileProgress[index] }}</span>
            </div>
            <div class="file-progress-bar-container">
              <div :id="'file-progress-bar-' + index"
                   class="file-progress-bar"
                   :style="{ width: fileProgressPercentage[index] + '%' }"></div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="download-section">
      <div id="download-links" class="download-links"
           :style="{ display: compressedBlobs.length > 0 ? 'block' : 'none' }">
        <h3>压缩完成的文件:</h3>
        <div id="download-link-items">
          <div class="download-link-item" v-for="(item, index) in compressedBlobs" :key="index">
            <span class="link-name">{{ item.originalName }}</span>
            <span class="file-size">{{ (item.blob.size / (1024 * 1024)).toFixed(2) }} MB</span>
            <a :href="item.blobUrl"
               :download="'compressed_' + item.originalName"
               class="download-link">下载</a>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'VideoCompressor',
  data() {
    return {
      selectedFiles: [],
      compressedBlobs: [],
      isCompressing: false,
      overallProgress: 0,
      progressText: '请选择视频文件',
      fileProgress: [], // 存储每个文件的进度文本
      fileProgressPercentage: [] // 存储每个文件的进度百分比
    };
  },
  methods: {
    handleFileSelect(event) {
      const files = Array.from(event.target.files);
      if (files.length > 0) {
        files.forEach(file => {
          const exists = this.selectedFiles.some(f => f.name === file.name && f.size === file.size);
          if (!exists) {
            this.selectedFiles.push(file);
          }
        });

        this.progressText = `${this.selectedFiles.length} 个文件已选择，点击开始批量压缩`;
        this.initFileProgress();
      }
    },

    removeFile(index) {
      this.selectedFiles.splice(index, 1);
      if (this.selectedFiles.length === 0) {
        this.progressText = '请选择视频文件';
      } else {
        this.progressText = `${this.selectedFiles.length} 个文件已选择，点击开始批量压缩`;
      }
      this.initFileProgress();
    },

    initFileProgress() {
      this.fileProgress = Array(this.selectedFiles.length).fill('等待中...');
      this.fileProgressPercentage = Array(this.selectedFiles.length).fill(0);
    },

    async compressVideos() {
      if (this.selectedFiles.length === 0) return;

      this.isCompressing = true;
      this.overallProgress = 0;
      this.progressText = '正在初始化...';
      this.compressedBlobs = [];
      this.initFileProgress();

      try {
        const compressionPromises = this.selectedFiles.map((file, index) =>
          this.compressVideo(file, index)
        );

        const results = await Promise.allSettled(compressionPromises);

        results.forEach((result, index) => {
          const fileName = this.selectedFiles[index].name;

          if (result.status === 'fulfilled') {
            this.compressedBlobs.push({
              blob: result.value,
              blobUrl: URL.createObjectURL(result.value),
              originalName: fileName
            });

            this.fileProgress.splice(index, 1, '完成');
          } else {
            console.error(`压缩文件 ${fileName} 失败:`, result.reason);
            this.fileProgress.splice(index, 1, '失败');
            this.fileProgressPercentage.splice(index, 1, 100);
          }
        });

        if (this.compressedBlobs.length > 0) {
          this.progressText = `批量压缩完成! 成功压缩 ${this.compressedBlobs.length}/${this.selectedFiles.length} 个文件`;
        } else {
          this.progressText = '所有文件压缩失败';
        }

      } catch (err) {
        console.error('批量压缩失败:', err);
        this.progressText = '批量压缩失败: ' + err.message;
      } finally {
        this.isCompressing = false;
        this.updateOverallProgress();
      }
    },

    compressVideo(file, fileIndex) {
      return new Promise(async (resolve, reject) => {
        try {
          this.fileProgress.splice(fileIndex, 1, '处理中...');

          const videoUrl = URL.createObjectURL(file);
          const videoElement = document.createElement('video');
          videoElement.src = videoUrl;
          videoElement.muted = true;
          await new Promise((resolve) => videoElement.onloadedmetadata = resolve);

          const canvas = document.createElement('canvas');
          const ctx = canvas.getContext('2d');

          const maxWidth = 1920;
          const maxHeight = 1080;
          let width = videoElement.videoWidth;
          let height = videoElement.videoHeight;

          if (width > maxWidth || height > maxHeight) {
            const ratio = Math.min(maxWidth / width, maxHeight / height);
            width = Math.floor(width * ratio);
            height = Math.floor(height * ratio);
          }

          canvas.width = width;
          canvas.height = height;

          const stream = canvas.captureStream();
          const options = {
            mimeType: 'video/mp4; codecs=avc1',
            videoBitsPerSecond: 5000000,
            audioBitsPerSecond: 128000
          };

          if (!MediaRecorder.isTypeSupported(options.mimeType)) {
            if (MediaRecorder.isTypeSupported('video/webm; codecs=vp9')) {
              options.mimeType = 'video/webm; codecs=vp9';
            } else if (MediaRecorder.isTypeSupported('video/webm')) {
              options.mimeType = 'video/webm';
            } else {
              throw new Error('不支持的视频格式');
            }
          }

          const mediaRecorder = new MediaRecorder(stream, options);

          const chunks = [];
          let totalSize = 0;

          mediaRecorder.ondataavailable = (e) => {
            if (e.data.size > 0) {
              chunks.push(e.data);
              totalSize += e.data.size;

              const progress = Math.min((totalSize / file.size) * 100, 100);
              this.fileProgressPercentage.splice(fileIndex, 1, progress);
              this.fileProgress.splice(fileIndex, 1, `${progress.toFixed(1)}%`);
              this.updateOverallProgress();
            }
          };

          mediaRecorder.start();
          videoElement.play();

          const startTime = Date.now();

          const drawFrame = () => {
            if (videoElement.paused || videoElement.ended) {
              mediaRecorder.stop();
              return;
            }
            ctx.drawImage(videoElement, 0, 0, width, height);

            const elapsed = Date.now() - startTime;
            const duration = videoElement.duration * 1000;

            if (duration) {
              const timeProgress = Math.min((elapsed / duration) * 100, 100);
              if (totalSize === 0) {
                this.fileProgressPercentage.splice(fileIndex, 1, timeProgress);
                this.fileProgress.splice(fileIndex, 1, `处理中: ${timeProgress.toFixed(1)}%`);
              }
            }

            requestAnimationFrame(drawFrame);
          };

          requestAnimationFrame(drawFrame);

          mediaRecorder.onstop = async () => {
            try {
              const videoBlob = new Blob(chunks, { type: options.mimeType });
              URL.revokeObjectURL(videoUrl);
              resolve(videoBlob);
            } catch (error) {
              reject(error);
            }
          };

          mediaRecorder.onerror = (e) => {
            console.error('MediaRecorder error:', e);
            reject(new Error('视频录制失败'));
          };

        } catch (error) {
          reject(error);
        }
      });
    },

    updateOverallProgress() {
      if (this.selectedFiles.length === 0) return;
      const completedFiles = this.compressedBlobs.length;
      const progress = (completedFiles / this.selectedFiles.length) * 100;
      this.overallProgress = Math.round(progress);
    }
  },

  watch: {
    selectedFiles: {
      handler() {
        // 监听文件列表变化，更新按钮状态
      },
      deep: true
    }
  },

  beforeUnmount() {
    // 清理创建的URL对象
    this.compressedBlobs.forEach(item => {
      URL.revokeObjectURL(item.blobUrl);
    });
  }
};
</script>

<style scoped>
* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  min-height: 100vh;
  padding: 20px;
}

.container {
  max-width: 1000px;
  margin: 0 auto;
  background: white;
  border-radius: 15px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
  padding: 30px;
}

h1 {
  text-align: center;
  color: #333;
  margin-bottom: 30px;
  font-size: 2.5rem;
}

.upload-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
  margin-bottom: 30px;
  padding: 20px;
  border: 2px dashed #ccc;
  border-radius: 10px;
  background-color: #f9f9f9;
  transition: border-color 0.3s;
}

.upload-section:hover {
  border-color: #667eea;
}

.file-input-wrapper {
  position: relative;
  overflow: hidden;
  display: inline-block;
  cursor: pointer;
}

.file-input-wrapper input[type=file] {
  position: absolute;
  left: 0;
  top: 0;
  opacity: 0;
  width: 100%;
  height: 100%;
  cursor: pointer;
}

.file-input-button {
  background: #667eea;
  color: white;
  padding: 12px 24px;
  border-radius: 30px;
  font-size: 16px;
  font-weight: 600;
  transition: all 0.3s;
  border: none;
  cursor: pointer;
}

.file-input-button:hover {
  background: #5a6fd8;
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
}

#compress-btn {
  background: #4CAF50;
  color: white;
  padding: 12px 30px;
  border: none;
  border-radius: 30px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

#compress-btn:hover:not(:disabled) {
  background: #45a049;
  transform: translateY(-2px);
  box-shadow: 0 6px 8px rgba(0, 0, 0, 0.15);
}

#compress-btn:disabled {
  background: #cccccc;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.file-list {
  width: 100%;
  max-height: 200px;
  overflow-y: auto;
  margin-top: 15px;
  border: 1px solid #eee;
  border-radius: 8px;
  padding: 10px;
  background: white;
}

.file-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px;
  border-bottom: 1px solid #eee;
}

.file-item:last-child {
  border-bottom: none;
}

.file-name {
  font-weight: 500;
  color: #333;
  flex: 1;
}

.file-size {
  color: #666;
  font-size: 0.9rem;
  margin: 0 15px;
}

.remove-file {
  background: #ff4d4d;
  color: white;
  border: none;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  cursor: pointer;
  font-size: 12px;
}

.progress-container {
  width: 100%;
  margin: 20px 0;
}

.overall-progress {
  margin-bottom: 20px;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-weight: 500;
}

#progress {
  height: 20px;
  width: 100%;
  border: 1px solid #ccc;
  border-radius: 10px;
  overflow: hidden;
  background: #f0f0f0;
}

#progress-bar {
  height: 100%;
  width: 0%;
  background: linear-gradient(90deg, #4CAF50, #8BC34A);
  transition: width 0.3s;
}

#progress-text {
  margin-top: 10px;
  font-size: 14px;
  text-align: center;
  color: #666;
}

.file-progress-container {
  margin-top: 20px;
}

.file-progress-item {
  margin-bottom: 15px;
  padding: 10px;
  border: 1px solid #eee;
  border-radius: 8px;
  background: #fafafa;
}

.file-progress-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 5px;
  font-weight: 500;
}

.file-progress-bar-container {
  height: 12px;
  width: 100%;
  border: 1px solid #ddd;
  border-radius: 6px;
  overflow: hidden;
  background: #f5f5f5;
}

.file-progress-bar {
  height: 100%;
  width: 0%;
  background: linear-gradient(90deg, #2196F3, #03A9F4);
  transition: width 0.3s;
}

.download-section {
  margin-top: 20px;
  text-align: center;
}

.download-link {
  display: inline-block;
  background: #667eea;
  color: white;
  padding: 12px 24px;
  border-radius: 30px;
  text-decoration: none;
  font-weight: 600;
  transition: all 0.3s;
  margin: 5px;
}

.download-link:hover {
  background: #5a6fd8;
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
}

.download-links {
  max-height: 300px;
  overflow-y: auto;
  padding: 10px;
  border: 1px solid #eee;
  border-radius: 8px;
  margin-top: 15px;
  background: white;
}

.download-link-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px;
  border-bottom: 1px solid #eee;
}

.download-link-item:last-child {
  border-bottom: none;
}

.link-name {
  font-weight: 500;
  color: #333;
  flex: 1;
}

.status-indicator {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  margin-right: 10px;
}

.status-pending {
  background-color: #ccc;
}

.status-processing {
  background-color: #ff9800;
}

.status-completed {
  background-color: #4CAF50;
}

.status-error {
  background-color: #f44336;
}

@media (max-width: 768px) {
  .container {
    padding: 15px;
  }

  h1 {
    font-size: 2rem;
  }
}
</style>
