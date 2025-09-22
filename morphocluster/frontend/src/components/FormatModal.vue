<template>
  <b-modal
    v-model="isVisible"
    title="Convert EcoTaxa Format"
    size="lg"
    @ok="handleConvert"
    @cancel="handleCancel"
    :ok-disabled="!isValid"
    ok-title="Start Conversion"
    cancel-title="Cancel"
  >
    <div class="format-conversion-form">
      <b-alert variant="info" show class="mb-4">
        <i class="mdi mdi-information"></i>
        <strong>EcoTaxa Format Detected</strong><br>
        This archive appears to be in EcoTaxa format. We'll convert it to the standard MorphoCluster format
        by processing the TSV/CSV files and organizing the images correctly.
      </b-alert>

      <!-- Archive Information -->
      <div class="archive-info mb-4">
        <h6>Archive Information</h6>
        <div class="info-grid">
          <div class="info-item">
            <strong>File:</strong>
            <span>{{ archive?.name || 'Unknown' }}</span>
          </div>
          <div class="info-item">
            <strong>Size:</strong>
            <span>{{ formatBytes(archive?.size || 0) }}</span>
          </div>
          <div class="info-item" v-if="archive?.validation?.file_count">
            <strong>Files:</strong>
            <span>{{ archive.validation.file_count }} files</span>
          </div>
          <div class="info-item" v-if="archive?.validation?.image_count">
            <strong>Images:</strong>
            <span>{{ archive.validation.image_count }} images</span>
          </div>
        </div>
      </div>

      <!-- Conversion Parameters -->
      <b-form @submit.prevent="handleConvert">
        <!-- Encoding Detection -->
        <b-form-group
          label="File Encoding"
          label-for="encoding"
          description="Character encoding for text files (usually auto-detected)"
        >
          <b-form-select
            id="encoding"
            v-model="parameters.encoding"
            :options="encodingOptions"
          />
        </b-form-group>

        <!-- Delimiter Detection -->
        <b-form-group
          label="CSV Delimiter"
          label-for="delimiter"
          description="Separator used in CSV/TSV files (usually auto-detected)"
        >
          <b-form-select
            id="delimiter"
            v-model="parameters.delimiter"
            :options="delimiterOptions"
          />
        </b-form-group>

        <!-- Source Format Preview -->
        <div v-if="previewData" class="format-preview mb-4">
          <h6>Source Format Preview</h6>
          <div class="preview-container">
            <b-table
              :items="previewData.sample_rows"
              :fields="previewData.columns"
              small
              striped
              class="preview-table"
            />
            <small class="text-muted">
              Showing first {{ previewData.sample_rows.length }} rows of {{ previewData.total_rows }} total rows
            </small>
          </div>
        </div>

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
                label="Force Overwrite"
                description="Overwrite existing index.csv if it already exists"
              >
                <b-form-checkbox
                  v-model="parameters.force_overwrite"
                  value="true"
                  unchecked-value="false"
                >
                  Force overwrite existing files
                </b-form-checkbox>
              </b-form-group>

              <b-form-group
                label="Skip Image Validation"
                description="Skip checking if all referenced images exist (faster but less safe)"
              >
                <b-form-checkbox
                  v-model="parameters.skip_image_validation"
                  value="true"
                  unchecked-value="false"
                >
                  Skip image validation
                </b-form-checkbox>
              </b-form-group>

              <b-form-group
                label="Custom Image Path Column"
                label-for="image-column"
                description="Column name containing image paths (auto-detected if empty)"
              >
                <b-form-input
                  id="image-column"
                  v-model="parameters.image_column"
                  placeholder="Auto-detect"
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
import * as api from '@/helpers/api.js';

export default {
  name: 'FormatModal',
  props: {
    archive: {
      type: Object,
      required: true
    }
  },
  emits: ['convert', 'cancel'],
  data() {
    return {
      isVisible: true,
      showAdvanced: false,
      parameters: {
        encoding: 'auto',
        delimiter: 'auto',
        force_overwrite: false,
        skip_image_validation: false,
        image_column: ''
      },
      encodingOptions: [
        { value: 'auto', text: 'Auto-detect' },
        { value: 'utf-8', text: 'UTF-8' },
        { value: 'latin-1', text: 'Latin-1 (ISO-8859-1)' },
        { value: 'windows-1252', text: 'Windows-1252' },
        { value: 'ascii', text: 'ASCII' }
      ],
      delimiterOptions: [
        { value: 'auto', text: 'Auto-detect' },
        { value: ',', text: 'Comma (,)' },
        { value: '\t', text: 'Tab' },
        { value: ';', text: 'Semicolon (;)' },
        { value: '|', text: 'Pipe (|)' }
      ],
      previewData: null,
      validationWarnings: [],
      isLoading: false
    };
  },
  computed: {
    isValid() {
      return this.parameters.encoding && this.parameters.delimiter;
    }
  },
  async mounted() {
    await this.loadPreview();
    this.validateParameters();
  },
  watch: {
    parameters: {
      handler: 'validateParameters',
      deep: true
    }
  },
  methods: {
    async loadPreview() {
      if (!this.archive?.name) return;
      
      this.isLoading = true;
      try {
        this.previewData = await api.previewArchive(this.archive.name);
        
        // Auto-detect encoding and delimiter from preview
        if (this.previewData.detected_encoding) {
          this.parameters.encoding = this.previewData.detected_encoding;
        }
        if (this.previewData.detected_delimiter) {
          this.parameters.delimiter = this.previewData.detected_delimiter;
        }
        
      } catch (error) {
        console.error('Failed to load preview:', error);
        this.validationWarnings.push('Could not load file preview. Conversion may not work correctly.');
      } finally {
        this.isLoading = false;
      }
    },

    validateParameters() {
      this.validationWarnings = [];

      // Check if encoding is supported
      if (this.parameters.encoding === 'auto' && !this.previewData?.detected_encoding) {
        this.validationWarnings.push('Encoding could not be auto-detected. Please select manually.');
      }

      // Check if delimiter is supported
      if (this.parameters.delimiter === 'auto' && !this.previewData?.detected_delimiter) {
        this.validationWarnings.push('CSV delimiter could not be auto-detected. Please select manually.');
      }

      // Check for image column
      if (this.parameters.image_column && this.previewData?.columns) {
        const columnExists = this.previewData.columns.some(col => 
          col.key === this.parameters.image_column
        );
        if (!columnExists) {
          this.validationWarnings.push(`Column "${this.parameters.image_column}" not found in the CSV file.`);
        }
      }

      // Check file size
      if (this.archive?.size > 1024 * 1024 * 1024) { // 1GB
        this.validationWarnings.push('Large archive detected. Conversion may take a long time.');
      }
    },

    async handleConvert() {
      if (!this.isValid) return;

      // Prepare parameters for API
      const convertParams = { ...this.parameters };
      
      // Convert 'auto' values to actual detected values
      if (convertParams.encoding === 'auto') {
        convertParams.encoding = this.previewData?.detected_encoding || 'utf-8';
      }
      if (convertParams.delimiter === 'auto') {
        convertParams.delimiter = this.previewData?.detected_delimiter || ',';
      }

      // Convert string booleans to actual booleans
      convertParams.force_overwrite = convertParams.force_overwrite === 'true' || convertParams.force_overwrite === true;
      convertParams.skip_image_validation = convertParams.skip_image_validation === 'true' || convertParams.skip_image_validation === true;

      this.$emit('convert', convertParams);
      this.isVisible = false;
    },

    handleCancel() {
      this.$emit('cancel');
      this.isVisible = false;
    },

    formatBytes(bytes) {
      if (bytes === 0) return '0 Bytes';
      const k = 1024;
      const sizes = ['Bytes', 'KB', 'MB', 'GB'];
      const i = Math.floor(Math.log(bytes) / Math.log(k));
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
  }
};
</script>

<style scoped>
.format-conversion-form {
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

.format-preview {
  border: 1px solid #dee2e6;
  border-radius: 4px;
  padding: 1rem;
  background-color: #f8f9fa;
}

.preview-container {
  max-height: 300px;
  overflow: auto;
}

.preview-table {
  font-size: 0.875rem;
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

/* Loading states */
.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(255, 255, 255, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
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
}
</style>