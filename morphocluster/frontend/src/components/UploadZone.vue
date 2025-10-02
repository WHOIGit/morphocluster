<template>
  <div class="upload-zone-container">
    <div
      class="upload-zone"
      :class="{
        'drag-over': isDragOver,
        'uploading': isUploading,
        'upload-complete': uploadComplete
      }"
      @dragover.prevent="handleDragOver"
      @dragenter.prevent="handleDragEnter"
      @dragleave.prevent="handleDragLeave"
      @drop.prevent="handleDrop"
      @click="openFileInput"
    >
      <div v-if="!isUploading && !uploadComplete" class="upload-content">
        <i class="mdi mdi-cloud-upload upload-icon"></i>
        <h4>{{ isDragOver ? 'Drop files here' : 'Upload Archive Files' }}</h4>
        <p>Drag & drop ZIP archives or click to browse</p>
        <p class="supported-formats">Supported: ZIP archives with images and index.csv</p>
        <b-button variant="primary" size="lg" class="upload-btn">
          <i class="mdi mdi-file-multiple"></i> Browse Files
        </b-button>
      </div>

      <div v-if="isUploading" class="upload-progress">
        <i class="mdi mdi-loading mdi-spin upload-icon"></i>
        <h4>Uploading Files...</h4>
        <div class="progress-container">
          <b-progress 
            :value="uploadProgress" 
            :max="100" 
            class="mb-3"
            :variant="uploadProgress === 100 ? 'success' : 'primary'"
            show-progress
          ></b-progress>
          <div class="upload-stats">
            <span>{{ formatBytes(uploadedBytes) }} / {{ formatBytes(totalBytes) }}</span>
            <span v-if="uploadSpeed > 0">{{ formatBytes(uploadSpeed) }}/s</span>
            <span v-if="timeRemaining > 0">{{ formatTime(timeRemaining) }} remaining</span>
          </div>
        </div>
        <b-button variant="outline-danger" size="sm" @click="cancelUpload" class="mt-2">
          Cancel Upload
        </b-button>
      </div>

      <div v-if="uploadComplete" class="upload-complete">
        <i class="mdi mdi-check-circle upload-icon text-success"></i>
        <h4>Upload Complete!</h4>
        <p>{{ uploadedFiles.length }} file(s) uploaded successfully</p>
        <div class="uploaded-files">
          <div v-for="file in uploadedFiles" :key="file.name" class="uploaded-file">
            <i class="mdi mdi-file-outline"></i>
            <span>{{ file.name }}</span>
            <span class="file-size">{{ formatBytes(file.size) }}</span>
          </div>
        </div>
        <div class="upload-actions mt-3">
          <b-button variant="primary" @click="resetUpload">
            <i class="mdi mdi-plus"></i>
            Upload More Files
          </b-button>
        </div>
      </div>
    </div>

    <input
      ref="fileInput"
      type="file"
      multiple
      accept=".zip,.tar,.tar.gz"
      style="display: none"
      @change="handleFileSelect"
    />

    <div v-if="errors.length" class="upload-errors mt-3">
      <b-alert
        v-for="(error, index) in errors"
        :key="index"
        variant="danger"
        dismissible
        @dismissed="removeError(index)"
      >
        {{ error }}
      </b-alert>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'UploadZone',
  props: {
    uploadUrl: {
      type: String,
      default: '/api/upload'
    },
    maxFileSize: {
      type: Number,
      default: 1024 * 1024 * 1024 // 1GB default
    },
    acceptedTypes: {
      type: Array,
      default: () => ['.zip', '.tar', '.tar.gz']
    }
  },
  emits: ['upload-start', 'upload-progress', 'upload-complete', 'upload-error', 'upload-cancel'],
  data() {
    return {
      isDragOver: false,
      isUploading: false,
      uploadComplete: false,
      uploadProgress: 0,
      uploadedBytes: 0,
      totalBytes: 0,
      uploadSpeed: 0,
      timeRemaining: 0,
      uploadedFiles: [],
      errors: [],
      uploadStartTime: 0,
      cancelTokenSource: null
    };
  },
  methods: {
    handleDragOver(event) {
      event.preventDefault();
      this.isDragOver = true;
    },
    
    handleDragEnter(event) {
      event.preventDefault();
      this.isDragOver = true;
    },
    
    handleDragLeave(event) {
      event.preventDefault();
      // Only set to false if we're leaving the upload zone entirely
      if (!this.$el.contains(event.relatedTarget)) {
        this.isDragOver = false;
      }
    },
    
    handleDrop(event) {
      event.preventDefault();
      this.isDragOver = false;
      const files = Array.from(event.dataTransfer.files);
      this.processFiles(files);
    },
    
    openFileInput() {
      if (!this.isUploading) {
        this.$refs.fileInput.click();
      }
    },
    
    handleFileSelect(event) {
      const files = Array.from(event.target.files);
      this.processFiles(files);
      // Clear the input so same file can be selected again
      event.target.value = '';
    },
    
    processFiles(files) {
      this.errors = [];
      
      if (files.length === 0) return;
      
      // Validate files
      const validFiles = [];
      for (const file of files) {
        if (!this.validateFile(file)) continue;
        validFiles.push(file);
      }
      
      if (validFiles.length === 0) return;
      
      this.uploadFiles(validFiles);
    },
    
    validateFile(file) {
      // Check file size
      if (file.size > this.maxFileSize) {
        this.errors.push(`File "${file.name}" is too large. Maximum size is ${this.formatBytes(this.maxFileSize)}.`);
        return false;
      }
      
      // Check file type
      const fileName = file.name.toLowerCase();
      const isAccepted = this.acceptedTypes.some(type => 
        fileName.endsWith(type.toLowerCase())
      );
      
      if (!isAccepted) {
        this.errors.push(`File "${file.name}" is not an accepted format. Accepted formats: ${this.acceptedTypes.join(', ')}`);
        return false;
      }
      
      return true;
    },
    
    async uploadFiles(files) {
      this.isUploading = true;
      this.uploadComplete = false;
      this.uploadProgress = 0;
      this.uploadedBytes = 0;
      this.totalBytes = files.reduce((total, file) => total + file.size, 0);
      this.uploadStartTime = Date.now();
      
      // Create cancel token
      this.cancelTokenSource = axios.CancelToken.source();
      
      const formData = new FormData();
      files.forEach(file => {
        formData.append('files', file);
      });
      
      this.$emit('upload-start', files);
      
      try {
        console.log('UploadZone: Starting axios post to', this.uploadUrl);
        const response = await axios.post(this.uploadUrl, formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
          cancelToken: this.cancelTokenSource.token,
          onUploadProgress: (progressEvent) => {
            this.updateProgress(progressEvent);
          },
        });

        console.log('UploadZone: Axios post completed, response:', response);

        this.uploadedFiles = files.map(file => ({
          name: file.name,
          size: file.size,
          type: file.type
        }));

        console.log('UploadZone: Set uploadedFiles:', this.uploadedFiles);

        this.uploadComplete = true;
        this.isUploading = false;

        console.log('UploadZone: About to emit upload-complete event');
        this.$emit('upload-complete', {
          files: this.uploadedFiles,
          response: response.data
        });
        console.log('UploadZone: Emitted upload-complete event');
        
      } catch (error) {
        console.error('UploadZone: Error during upload:', error);
        this.isUploading = false;
        
        if (axios.isCancel(error)) {
          this.$emit('upload-cancel');
        } else {
          this.errors.push(error.response?.data?.message || 'Upload failed. Please try again.');
          this.$emit('upload-error', error);
        }
      }
    },
    
    updateProgress(progressEvent) {
      this.uploadedBytes = progressEvent.loaded;
      this.uploadProgress = Math.round((progressEvent.loaded / progressEvent.total) * 100);
      
      const elapsed = (Date.now() - this.uploadStartTime) / 1000;
      this.uploadSpeed = elapsed > 0 ? progressEvent.loaded / elapsed : 0;
      
      if (this.uploadSpeed > 0) {
        const remaining = (progressEvent.total - progressEvent.loaded) / this.uploadSpeed;
        this.timeRemaining = remaining;
      }
      
      this.$emit('upload-progress', {
        progress: this.uploadProgress,
        uploadedBytes: this.uploadedBytes,
        totalBytes: this.totalBytes,
        uploadSpeed: this.uploadSpeed,
        timeRemaining: this.timeRemaining
      });
    },
    
    cancelUpload() {
      if (this.cancelTokenSource) {
        this.cancelTokenSource.cancel('Upload cancelled by user');
      }
    },
    
    resetUpload() {
      this.isUploading = false;
      this.uploadComplete = false;
      this.uploadProgress = 0;
      this.uploadedBytes = 0;
      this.totalBytes = 0;
      this.uploadSpeed = 0;
      this.timeRemaining = 0;
      this.uploadedFiles = [];
      this.errors = [];
    },
    
    removeError(index) {
      this.errors.splice(index, 1);
    },
    
    formatBytes(bytes) {
      if (bytes === 0) return '0 Bytes';
      const k = 1024;
      const sizes = ['Bytes', 'KB', 'MB', 'GB'];
      const i = Math.floor(Math.log(bytes) / Math.log(k));
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },
    
    formatTime(seconds) {
      if (seconds < 60) return `${Math.round(seconds)}s`;
      if (seconds < 3600) return `${Math.round(seconds / 60)}m`;
      return `${Math.round(seconds / 3600)}h`;
    }
  }
};
</script>

<style scoped>
.upload-zone-container {
  width: 100%;
}

.upload-zone {
  border: 3px dashed #dee2e6;
  border-radius: 12px;
  padding: 1rem 1.5rem;
  text-align: center;
  background-color: #f8f9fa;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  min-height: 120px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.upload-zone:hover {
  border-color: #007bff;
  background-color: #e7f3ff;
}

.upload-zone.drag-over {
  border-color: #28a745;
  background-color: #d4edda;
  transform: scale(1.02);
}

.upload-zone.uploading {
  border-color: #007bff;
  background-color: #e7f3ff;
  cursor: not-allowed;
}

.upload-zone.upload-complete {
  border-color: #28a745;
  background-color: #d4edda;
  cursor: default;
}

.upload-content, .upload-progress, .upload-complete {
  width: 100%;
}

.upload-icon {
  font-size: 3rem;
  margin-bottom: 0.75rem;
  color: #6c757d;
}

.upload-zone.drag-over .upload-icon {
  color: #28a745;
}

.upload-zone.uploading .upload-icon {
  color: #007bff;
}

.upload-complete .upload-icon {
  color: #28a745 !important;
}

.upload-zone h4 {
  margin-bottom: 0.5rem;
  color: #495057;
  font-weight: 600;
}

.upload-zone p {
  margin-bottom: 0.25rem;
  color: #6c757d;
}

.supported-formats {
  font-size: 0.875rem;
  font-style: italic;
  margin-bottom: 1rem !important;
}

.upload-btn {
  margin-top: 1rem;
  padding: 0.75rem 2rem;
  font-size: 1.1rem;
  font-weight: 500;
}

.progress-container {
  max-width: 500px;
  margin: 0 auto 1rem;
}

.upload-stats {
  display: flex;
  justify-content: space-between;
  font-size: 0.875rem;
  color: #6c757d;
  margin-top: 0.5rem;
}

.uploaded-files {
  max-width: 500px;
  margin: 1rem auto;
  text-align: left;
}

.uploaded-file {
  display: flex;
  align-items: center;
  padding: 0.5rem;
  background-color: rgba(40, 167, 69, 0.1);
  border: 1px solid rgba(40, 167, 69, 0.2);
  border-radius: 4px;
  margin-bottom: 0.5rem;
}

.uploaded-file i {
  margin-right: 0.5rem;
  color: #28a745;
}

.uploaded-file span:first-of-type {
  flex: 1;
  font-weight: 500;
}

.file-size {
  color: #6c757d;
  font-size: 0.875rem;
}

.upload-actions {
  display: flex;
  justify-content: center;
  gap: 0.5rem;
}

.upload-errors {
  text-align: left;
}

@media (max-width: 768px) {
  .upload-zone {
    padding: 2rem 1rem;
    min-height: 250px;
  }
  
  .upload-icon {
    font-size: 3rem;
  }
  
  .upload-actions {
    flex-direction: column;
    align-items: center;
  }
  
  .upload-stats {
    flex-direction: column;
    text-align: center;
  }
}
</style>