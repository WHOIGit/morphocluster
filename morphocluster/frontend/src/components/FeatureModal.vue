<template>
  <b-modal
    v-model="isVisible"
    title="Extract Features"
    size="lg"
    @ok="handleExtract"
    @cancel="handleCancel"
    :ok-disabled="!isValid"
    ok-title="Start Extraction"
    cancel-title="Cancel"
  >
    <div class="feature-extraction-form">
      <b-alert variant="info" show class="mb-4">
        <i class="mdi mdi-cog"></i>
        <strong>Feature Extraction</strong><br>
        Extract image features using deep learning models. This process will analyze all images
        in the archive and generate feature vectors for clustering.
      </b-alert>

      <!-- Archive Information -->
      <div class="archive-info mb-4">
        <h6>Archive Information</h6>
        <div class="info-grid">
          <div class="info-item">
            <strong>Archive:</strong>
            <span>{{ archive?.original_filename || 'Unknown' }}</span>
          </div>
          <div class="info-item" v-if="archive?.validation?.image_count">
            <strong>Images:</strong>
            <span>{{ archive.validation.image_count }} images</span>
          </div>
          <div class="info-item" v-if="estimatedTime">
            <strong>Estimated Time:</strong>
            <span>{{ estimatedTime }}</span>
          </div>
          <div class="info-item" v-if="estimatedMemory">
            <strong>Memory Required:</strong>
            <span>{{ estimatedMemory }}</span>
          </div>
        </div>
      </div>

      <!-- Model Selection -->
      <b-form @submit.prevent="handleExtract">
        <b-form-group
          label="Feature Extraction Model"
          label-for="model"
          description="Choose the deep learning model for feature extraction"
        >
          <b-form-select
            id="model"
            v-model="parameters.model"
            :options="modelOptions"
          />
          <div v-if="selectedModelInfo" class="model-info mt-2">
            <small class="text-muted">
              <strong>{{ selectedModelInfo.name }}</strong><br>
              {{ selectedModelInfo.description }}<br>
              Output dimensions: {{ selectedModelInfo.output_dim }}
            </small>
          </div>
        </b-form-group>

        <!-- Custom Model Upload -->
        <div v-if="parameters.model === 'custom'" class="custom-model-section mb-4">
          <b-form-group
            label="Custom Model File"
            label-for="custom-model"
            description="Upload a pre-trained model file (.pth, .h5, .onnx)"
          >
            <b-form-file
              id="custom-model"
              v-model="customModelFile"
              accept=".pth,.h5,.onnx"
              placeholder="Choose model file..."
              drop-placeholder="Drop model file here..."
            />
          </b-form-group>
          
          <b-form-group
            label="Model Architecture"
            label-for="model-architecture"
            description="Specify the model architecture"
          >
            <b-form-select
              id="model-architecture"
              v-model="parameters.custom_architecture"
              :options="architectureOptions"
            />
          </b-form-group>
        </div>

        <!-- Processing Parameters -->
        <b-card class="processing-params mb-4" no-body>
          <b-card-header>
            <h6 class="mb-0">Processing Parameters</h6>
          </b-card-header>
          <b-card-body>
            <b-form-group
              label="Batch Size"
              label-for="batch-size"
              :description="batchSizeDescription"
            >
              <b-form-input
                id="batch-size"
                v-model.number="parameters.batch_size"
                type="number"
                min="1"
                max="1024"
                step="1"
              />
              <div class="batch-size-presets mt-2">
                <small class="text-muted">Presets: </small>
                <b-button
                  v-for="preset in batchSizePresets"
                  :key="preset.value"
                  size="sm"
                  variant="outline-secondary"
                  class="me-1"
                  @click="parameters.batch_size = preset.value"
                >
                  {{ preset.label }}
                </b-button>
              </div>
            </b-form-group>

            <b-form-group
              label="Normalization"
              description="Apply ImageNet normalization to input images"
            >
              <b-form-checkbox
                v-model="parameters.normalize"
                value="true"
                unchecked-value="false"
              >
                Apply normalization (recommended)
              </b-form-checkbox>
            </b-form-group>

            <b-form-group
              label="Hardware"
              label-for="device"
              description="Choose processing hardware"
            >
              <b-form-select
                id="device"
                v-model="parameters.device"
                :options="deviceOptions"
              />
              <div v-if="deviceInfo" class="device-info mt-2">
                <small class="text-muted">
                  {{ deviceInfo }}
                </small>
              </div>
            </b-form-group>
          </b-card-body>
        </b-card>

        <!-- Advanced Options -->
        <b-card class="advanced-options" no-body>
          <b-card-header>
            <b-button
              v-b-toggle.advanced-collapse
              variant="link"
              class="p-0 text-decoration-none"
            >
              <i :class="showAdvanced ? 'mdi mdi-chevron-up' : 'mdi mdi-chevron-down'"></i>
              Advanced Options
            </b-button>
          </b-card-header>
          <b-collapse id="advanced-collapse" v-model="showAdvanced">
            <b-card-body>
              <b-form-group
                label="Input Mean"
                label-for="input-mean"
                description="Custom normalization mean values (R,G,B)"
              >
                <b-form-input
                  id="input-mean"
                  v-model="parameters.input_mean"
                  placeholder="0.485,0.456,0.406"
                />
              </b-form-group>

              <b-form-group
                label="Input Std"
                label-for="input-std"
                description="Custom normalization standard deviation values (R,G,B)"
              >
                <b-form-input
                  id="input-std"
                  v-model="parameters.input_std"
                  placeholder="0.229,0.224,0.225"
                />
              </b-form-group>

              <b-form-group
                label="Image Resize"
                label-for="image-size"
                description="Target image size for processing (pixels)"
              >
                <b-form-input
                  id="image-size"
                  v-model.number="parameters.image_size"
                  type="number"
                  min="32"
                  max="1024"
                  step="1"
                />
              </b-form-group>

              <b-form-group
                label="Number of Workers"
                label-for="num-workers"
                description="Parallel data loading workers (0 = auto)"
              >
                <b-form-input
                  id="num-workers"
                  v-model.number="parameters.num_workers"
                  type="number"
                  min="0"
                  max="16"
                  step="1"
                />
              </b-form-group>

              <b-form-group
                label="Output Format"
                label-for="output-format"
                description="Feature vector storage format"
              >
                <b-form-select
                  id="output-format"
                  v-model="parameters.output_format"
                  :options="outputFormatOptions"
                />
              </b-form-group>
            </b-card-body>
          </b-collapse>
        </b-card>

        <!-- Validation Warnings -->
        <div v-if="validationWarnings.length" class="validation-warnings mt-3">
          <b-alert
            v-for="(warning, index) in validationWarnings"
            :key="index"
            variant="warning"
            show
            class="small"
          >
            <i class="mdi mdi-alert"></i>
            {{ warning }}
          </b-alert>
        </div>
      </b-form>
    </div>
  </b-modal>
</template>

<script>
export default {
  name: 'FeatureModal',
  props: {
    archive: {
      type: Object,
      required: true
    }
  },
  emits: ['extract', 'cancel'],
  data() {
    return {
      isVisible: true,
      showAdvanced: false,
      customModelFile: null,
      parameters: {
        model: 'resnet18',
        custom_architecture: '',
        batch_size: 512,
        normalize: true,
        device: 'auto',
        input_mean: '0.485,0.456,0.406',
        input_std: '0.229,0.224,0.225',
        image_size: 224,
        num_workers: 0,
        output_format: 'hdf5'
      },
      modelOptions: [
        { value: 'resnet18', text: 'ResNet-18 (ImageNet) - Default' },
        { value: 'custom', text: 'Upload Custom Model...' }
      ],
      architectureOptions: [
        { value: 'resnet', text: 'ResNet' },
        { value: 'vgg', text: 'VGG' },
        { value: 'densenet', text: 'DenseNet' },
        { value: 'mobilenet', text: 'MobileNet' },
        { value: 'efficientnet', text: 'EfficientNet' },
        { value: 'custom', text: 'Custom Architecture' }
      ],
      deviceOptions: [
        { value: 'auto', text: 'Auto-detect (Recommended)' },
        { value: 'gpu', text: 'GPU (CUDA)' },
        { value: 'cpu', text: 'CPU Only' }
      ],
      outputFormatOptions: [
        { value: 'hdf5', text: 'HDF5 (.h5)' },
        { value: 'numpy', text: 'NumPy (.npz)' },
        { value: 'pickle', text: 'Pickle (.pkl)' }
      ],
      batchSizePresets: [
        { label: 'Small (128)', value: 128 },
        { label: 'Medium (512)', value: 512 },
        { label: 'Large (1024)', value: 1024 }
      ],
      modelInfo: {
        'resnet50': {
          name: 'ResNet-50',
          description: 'Deep residual network with 50 layers, pre-trained on ImageNet',
          output_dim: 2048
        },
        'resnet101': {
          name: 'ResNet-101',
          description: 'Deep residual network with 101 layers, pre-trained on ImageNet',
          output_dim: 2048
        },
        'vgg16': {
          name: 'VGG-16',
          description: 'Visual Geometry Group network with 16 layers',
          output_dim: 4096
        },
        'vgg19': {
          name: 'VGG-19',
          description: 'Visual Geometry Group network with 19 layers',
          output_dim: 4096
        },
        'densenet121': {
          name: 'DenseNet-121',
          description: 'Densely connected convolutional network',
          output_dim: 1024
        },
        'mobilenet_v2': {
          name: 'MobileNet V2',
          description: 'Efficient architecture for mobile devices',
          output_dim: 1280
        },
        'efficientnet_b0': {
          name: 'EfficientNet B0',
          description: 'Efficient and accurate convolutional neural network',
          output_dim: 1280
        }
      },
      validationWarnings: []
    };
  },
  computed: {
    isValid() {
      const baseValid = this.parameters.model && this.parameters.batch_size > 0;
      if (this.parameters.model === 'custom') {
        return baseValid && this.customModelFile && this.parameters.custom_architecture;
      }
      return baseValid;
    },
    
    selectedModelInfo() {
      return this.modelInfo[this.parameters.model] || null;
    },
    
    batchSizeDescription() {
      const imageCount = this.archive?.validation?.image_count || 0;
      const batches = Math.ceil(imageCount / this.parameters.batch_size);
      return `Images per batch. Total batches: ${batches} (${imageCount} images)`;
    },
    
    deviceInfo() {
      if (this.parameters.device === 'gpu') {
        return 'GPU acceleration will be used if available';
      } else if (this.parameters.device === 'cpu') {
        return 'Processing will use CPU only (slower but more compatible)';
      }
      return 'Automatically choose best available hardware';
    },
    
    estimatedTime() {
      const imageCount = this.archive?.validation?.image_count || 0;
      if (imageCount === 0) return null;
      
      // Rough estimates based on batch size and device
      const imagesPerSecond = this.parameters.device === 'gpu' ? 50 : 10;
      const seconds = Math.ceil(imageCount / imagesPerSecond);
      
      if (seconds < 60) return `~${seconds}s`;
      if (seconds < 3600) return `~${Math.ceil(seconds / 60)}m`;
      return `~${Math.ceil(seconds / 3600)}h`;
    },
    
    estimatedMemory() {
      const batchSize = this.parameters.batch_size;
      const imageSize = this.parameters.image_size;
      
      // Rough memory estimate: batch_size * image_size^2 * 3 channels * 4 bytes * model overhead
      const memoryMB = Math.ceil((batchSize * imageSize * imageSize * 3 * 4 * 2) / (1024 * 1024));
      
      if (memoryMB < 1024) return `~${memoryMB}MB`;
      return `~${Math.ceil(memoryMB / 1024)}GB`;
    }
  },
  mounted() {
    this.validateParameters();
  },
  watch: {
    parameters: {
      handler: 'validateParameters',
      deep: true
    },
    customModelFile: 'validateParameters'
  },
  methods: {
    validateParameters() {
      this.validationWarnings = [];

      // Check batch size
      if (this.parameters.batch_size > 1024) {
        this.validationWarnings.push('Large batch size may cause out-of-memory errors.');
      }

      // Check custom model
      if (this.parameters.model === 'custom' && !this.customModelFile) {
        this.validationWarnings.push('Please upload a custom model file.');
      }

      // Check image count
      const imageCount = this.archive?.validation?.image_count || 0;
      if (imageCount === 0) {
        this.validationWarnings.push('No images found in archive.');
      } else if (imageCount > 100000) {
        this.validationWarnings.push('Large number of images detected. Processing may take a long time.');
      }

      // Check memory requirements
      const estimatedMemoryGB = parseInt(this.estimatedMemory);
      if (estimatedMemoryGB > 8) {
        this.validationWarnings.push('High memory usage expected. Consider reducing batch size.');
      }

      // Check normalization parameters
      if (this.parameters.input_mean && !this.isValidFloatList(this.parameters.input_mean)) {
        this.validationWarnings.push('Input mean must be three comma-separated numbers.');
      }
      
      if (this.parameters.input_std && !this.isValidFloatList(this.parameters.input_std)) {
        this.validationWarnings.push('Input std must be three comma-separated numbers.');
      }
    },

    isValidFloatList(value) {
      if (!value) return true;
      const parts = value.split(',');
      if (parts.length !== 3) return false;
      return parts.every(part => !isNaN(parseFloat(part.trim())));
    },

    async handleExtract() {
      if (!this.isValid) return;

      // Prepare parameters for API
      const extractParams = { ...this.parameters };
      
      // Convert string booleans to actual booleans
      extractParams.normalize = extractParams.normalize === 'true' || extractParams.normalize === true;

      // Parse normalization parameters
      if (extractParams.input_mean) {
        extractParams.input_mean = extractParams.input_mean.split(',').map(x => parseFloat(x.trim()));
      }
      if (extractParams.input_std) {
        extractParams.input_std = extractParams.input_std.split(',').map(x => parseFloat(x.trim()));
      }

      // Handle custom model file
      if (extractParams.model === 'custom' && this.customModelFile) {
        // In a real implementation, you would upload the file first
        extractParams.custom_model_path = this.customModelFile.name;
      }

      this.$emit('extract', extractParams);
      this.isVisible = false;
    },

    handleCancel() {
      this.$emit('cancel');
      this.isVisible = false;
    }
  }
};
</script>

<style scoped>
.feature-extraction-form {
  max-height: 70vh;
  overflow-y: auto;
}

.archive-info {
  background-color: #f8f9fa;
  border: 1px solid #dee2e6;
  border-radius: 4px;
  padding: 1rem;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 0.5rem;
}

.info-item {
  display: flex;
  justify-content: space-between;
}

.info-item strong {
  margin-right: 0.5rem;
}

.custom-model-section {
  background-color: #f8f9fa;
  border: 1px solid #dee2e6;
  border-radius: 4px;
  padding: 1rem;
}

.model-info {
  background-color: #e7f3ff;
  border: 1px solid #bee5eb;
  border-radius: 4px;
  padding: 0.75rem;
}

.processing-params .card-header {
  background-color: #f8f9fa;
}

.batch-size-presets .btn {
  margin-bottom: 0.25rem;
}

.device-info {
  background-color: #e7f3ff;
  border: 1px solid #bee5eb;
  border-radius: 4px;
  padding: 0.5rem;
}

.advanced-options {
  margin-top: 1rem;
}

.advanced-options .card-header {
  padding: 0.75rem 1rem;
  background-color: #f8f9fa;
}

.validation-warnings .alert {
  padding: 0.5rem 0.75rem;
  margin-bottom: 0.5rem;
}

.validation-warnings .alert:last-child {
  margin-bottom: 0;
}

@media (max-width: 768px) {
  .info-grid {
    grid-template-columns: 1fr;
  }
  
  .info-item {
    flex-direction: column;
  }
  
  .info-item strong {
    margin-right: 0;
    margin-bottom: 0.25rem;
  }

  .batch-size-presets .btn {
    width: 100%;
    margin-bottom: 0.5rem;
  }
}
</style>