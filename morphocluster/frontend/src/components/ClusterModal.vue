<template>
  <b-modal
    v-model="isVisible"
    :title="modalTitle"
    size="lg"
    @ok="handleCluster"
    @cancel="handleCancel"
    :ok-disabled="!isValid"
    :ok-title="okTitle"
    cancel-title="Cancel"
  >
    <div class="cluster-form">
      <b-alert variant="info" show class="mb-4">
        <i class="mdi mdi-sitemap"></i>
        <strong>{{ isReclusterMode ? 'Re-clustering' : 'Initial Clustering' }}</strong><br>
        {{ isReclusterMode
           ? 'Re-cluster an existing project with different parameters to create a new project.'
           : 'Create a new MorphoCluster project by clustering the extracted features.' }}
        {{ !isReclusterMode ? 'This will group similar images together based on their visual features.' : '' }}
      </b-alert>

      <!-- Source Information -->
      <div class="source-info mb-4">
        <h6>Source Information</h6>
        <div class="info-grid">
          <div v-if="!isReclusterMode" class="info-item">
            <strong>Archive:</strong>
            <span>{{ archive?.original_filename || 'Unknown' }}</span>
          </div>
          <div v-if="isReclusterMode" class="info-item">
            <strong>Original Project:</strong>
            <span>{{ project?.name || 'Unknown' }}</span>
          </div>
          <div v-if="!isReclusterMode && archive?.validation?.image_count" class="info-item">
            <strong>Images:</strong>
            <span>{{ archive.validation.image_count }} images</span>
          </div>
          <div v-if="isReclusterMode" class="info-item">
            <strong>Project ID:</strong>
            <span>{{ project?.project_id || 'Unknown' }}</span>
          </div>
          <div v-if="!isReclusterMode" class="info-item">
            <strong>Features:</strong>
            <span>{{ featureFile || 'Feature extraction completed' }}</span>
          </div>
        </div>
      </div>

      <!-- Project Settings -->
      <b-form @submit.prevent="handleCluster">
        <b-form-group
          label="Project Name"
          label-for="project-name"
          :description="isReclusterMode ? 'Choose a name for the new re-clustered project' : 'Choose a descriptive name for your new project'"
          :invalid-feedback="projectNameError"
          :state="projectNameState"
        >
          <b-form-input
            id="project-name"
            v-model="parameters.project_name"
            :state="projectNameState"
            placeholder="e.g., Plankton Dataset 2023"
            required
          />
        </b-form-group>

        <b-form-group
          label="Project Description"
          label-for="project-description"
          description="Optional description of your dataset"
        >
          <b-form-textarea
            id="project-description"
            v-model="parameters.description"
            placeholder="Description of the dataset, sampling location, date, etc."
            rows="3"
          />
        </b-form-group>

        <!-- Clustering Parameters -->
        <b-card class="clustering-params mb-4" no-body>
          <b-card-header>
            <h6 class="mb-0">Clustering Parameters</h6>
          </b-card-header>
          <b-card-body>
            <b-form-group
              label="Minimum Cluster Size"
              label-for="min-cluster-size"
              :description="minClusterSizeDescription"
            >
              <b-form-input
                id="min-cluster-size"
                v-model.number="parameters.min_cluster_size"
                type="number"
                min="1"
                max="10000"
                step="1"
              />
              <div class="cluster-size-presets mt-2">
                <small class="text-muted">Presets: </small>
                <b-button
                  v-for="preset in clusterSizePresets"
                  :key="preset.value"
                  size="sm"
                  variant="outline-secondary"
                  class="me-1"
                  @click="parameters.min_cluster_size = preset.value"
                >
                  {{ preset.label }}
                </b-button>
              </div>
            </b-form-group>

            <b-form-group
              label="Minimum Samples"
              label-for="min-samples"
              description="Minimum number of samples for a point to be considered a core point"
            >
              <b-form-input
                id="min-samples"
                v-model.number="parameters.min_samples"
                type="number"
                min="1"
                max="100"
                step="1"
              />
            </b-form-group>

            <b-form-group
              label="Cluster Selection Method"
              label-for="cluster-method"
              description="Method for selecting final clusters from the hierarchy"
            >
              <b-form-select
                id="cluster-method"
                v-model="parameters.cluster_selection_method"
                :options="clusterMethodOptions"
              />
            </b-form-group>
          </b-card-body>
        </b-card>

        <!-- Advanced Options -->
        <b-card class="advanced-options mb-4" no-body>
          <b-card-header class="d-flex justify-content-between align-items-center">
            <h6 class="mb-0">Advanced Options</h6>
            <b-button
              variant="link"
              size="sm"
              @click="showAdvanced = !showAdvanced"
              class="p-0"
            >
              {{ showAdvanced ? 'Hide' : 'Show' }} Advanced
              <i :class="showAdvanced ? 'mdi mdi-chevron-up' : 'mdi mdi-chevron-down'"></i>
            </b-button>
          </b-card-header>
          <b-collapse v-model="showAdvanced">
            <b-card-body>
              <b-form-group
                label="Sample Size"
                label-for="sample-size"
                description="Maximum number of objects to use for clustering (0 = use all)"
              >
                <b-form-input
                  id="sample-size"
                  v-model.number="parameters.sample_size"
                  type="number"
                  min="0"
                  max="1000000"
                  step="1000"
                />
              </b-form-group>

              <b-form-group
                label="Keep Unexplored Ratio"
                label-for="keep-unexplored"
                description="Ratio of objects to keep unexplored for future analysis"
              >
                <b-form-input
                  id="keep-unexplored"
                  v-model.number="parameters.keep_unexplored_ratio"
                  type="number"
                  min="0"
                  max="1"
                  step="0.1"
                />
              </b-form-group>
            </b-card-body>
          </b-collapse>
        </b-card>

        <!-- Estimation Info -->
        <div v-if="estimatedTime || estimatedClusters" class="estimation-info">
          <b-alert variant="light" show>
            <div class="d-flex justify-content-between">
              <div v-if="estimatedTime">
                <strong>Estimated Time:</strong> {{ estimatedTime }}
              </div>
              <div v-if="estimatedClusters">
                <strong>Expected Clusters:</strong> ~{{ estimatedClusters }}
              </div>
            </div>
          </b-alert>
        </div>
      </b-form>
    </div>
  </b-modal>
</template>

<script>
export default {
  name: 'ClusterModal',
  props: {
    archive: {
      type: Object,
      required: false,
      default: null
    },
    featureFile: {
      type: String,
      default: null
    },
    project: {
      type: Object,
      required: false,
      default: null
    }
  },
  emits: ['cluster', 'cancel'],
  data() {
    return {
      isVisible: true,
      showAdvanced: false,
      parameters: {
        project_name: '',
        description: '',
        min_cluster_size: 128,
        min_samples: 1,
        cluster_selection_method: 'leaf',
        sample_size: 0, // 0 means use all
        keep_unexplored_ratio: 0.0
      },
      clusterSizePresets: [
        { value: 32, label: 'Small (32)' },
        { value: 64, label: 'Medium (64)' },
        { value: 128, label: 'Large (128)' },
        { value: 256, label: 'X-Large (256)' }
      ],
      clusterMethodOptions: [
        { value: 'eom', text: 'EOM (Excess of Mass)' },
        { value: 'leaf', text: 'Leaf (Most Granular)' }
      ]
    };
  },
  computed: {
    isReclusterMode() {
      return this.project !== null;
    },
    modalTitle() {
      return this.isReclusterMode ? 'Re-cluster Project' : 'Create Project (Initial Clustering)';
    },
    okTitle() {
      return this.isReclusterMode ? 'Start Re-clustering' : 'Create Project';
    },
    projectNameState() {
      if (this.parameters.project_name.length === 0) return null;
      return this.parameters.project_name.length >= 3 ? true : false;
    },
    projectNameError() {
      if (this.parameters.project_name.length > 0 && this.parameters.project_name.length < 3) {
        return 'Project name must be at least 3 characters long';
      }
      return '';
    },
    isValid() {
      return this.parameters.project_name.length >= 3;
    },
    minClusterSizeDescription() {
      const size = this.parameters.min_cluster_size;
      if (size < 32) return 'Very small clusters - may produce many tiny groups';
      if (size < 64) return 'Small clusters - good for detailed analysis';
      if (size < 128) return 'Medium clusters - balanced approach';
      if (size < 256) return 'Large clusters - broader groupings';
      return 'Very large clusters - coarse groupings';
    },
    estimatedTime() {
      const imageCount = this.archive?.validation?.image_count || 0;
      if (imageCount > 10000) return '10-30 minutes';
      if (imageCount > 5000) return '5-15 minutes';
      if (imageCount > 1000) return '2-5 minutes';
      return '1-2 minutes';
    },
    estimatedClusters() {
      const imageCount = this.archive?.validation?.image_count || 0;
      const clusterSize = this.parameters.min_cluster_size;
      if (imageCount && clusterSize) {
        return Math.floor(imageCount / clusterSize / 2); // Rough estimate
      }
      return null;
    }
  },
  mounted() {
    if (this.isReclusterMode && this.project?.name) {
      // For re-clustering, extract previous parameters and set new defaults
      const previousParams = this.extractClusteringParameters();

      if (previousParams.min_cluster_size) {
        // Set new min_cluster_size to half of previous (minimum 8)
        this.parameters.min_cluster_size = Math.max(8, Math.floor(previousParams.min_cluster_size / 2));
      } else {
        // Fallback: assume previous was 64, so new default is 32
        this.parameters.min_cluster_size = 32;
      }

      // Copy other parameters from previous clustering
      if (previousParams.min_samples) {
        this.parameters.min_samples = previousParams.min_samples;
      }
      if (previousParams.cluster_selection_method) {
        this.parameters.cluster_selection_method = previousParams.cluster_selection_method;
      }

      // Set project name with new cluster size
      this.parameters.project_name = `${this.project.name} (${this.parameters.min_cluster_size})`;
    } else if (this.archive?.original_filename) {
      // For initial clustering, set default project name based on archive name
      const baseName = this.archive.original_filename.replace(/\.(zip|tar|tar\.gz)$/i, '');
      this.parameters.project_name = baseName.replace(/_/g, ' ');
    }
  },
  watch: {
    // Update project name when min_cluster_size changes (for re-clustering mode)
    'parameters.min_cluster_size'() {
      if (this.isReclusterMode && this.project?.name) {
        // Extract the base name (remove existing cluster size if present)
        const baseName = this.project.name.replace(/\s*\(\d+\)$/, '');
        this.parameters.project_name = `${baseName} (${this.parameters.min_cluster_size})`;
      }
    }
  },
  methods: {
    extractClusteringParameters() {
      // Extract clustering parameters from project metadata
      if (!this.project?.metadata) {
        return {};
      }

      try {
        const metadata = JSON.parse(this.project.metadata);
        // The clustering parameters should be under metadata.cluster
        return metadata.cluster || {};
      } catch (e) {
        console.warn('Failed to parse project metadata:', e);
        return {};
      }
    },

    handleCluster() {
      if (this.isValid) {
        this.$emit('cluster', this.parameters);
      }
    },
    handleCancel() {
      this.isVisible = false;
      this.$emit('cancel');
    }
  }
};
</script>

<style scoped>
.cluster-form {
  max-height: 70vh;
  overflow-y: auto;
}

.archive-info,
.source-info {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 6px;
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
  align-items: center;
  padding: 0.25rem 0;
  color: var(--text-primary);
}

.info-item strong {
  margin-right: 0.5rem;
  color: var(--text-primary);
}

.clustering-params .card-header,
.advanced-options .card-header {
  background-color: var(--bg-secondary) !important;
  border-bottom: 1px solid var(--border-color) !important;
}

.clustering-params .card-header h6,
.advanced-options .card-header h6 {
  color: var(--text-primary) !important;
}

.clustering-params .card-body,
.advanced-options .card-body {
  background-color: var(--card-bg) !important;
}

.cluster-size-presets {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  flex-wrap: wrap;
}

.estimation-info {
  margin-top: 1rem;
}

/* Form descriptions should use secondary text color */
:deep(.form-group small),
:deep(.form-text),
:deep(.invalid-feedback),
:deep(.form-group .text-muted) {
  color: var(--text-secondary) !important;
}

@media (max-width: 768px) {
  .info-grid {
    grid-template-columns: 1fr;
  }

  .info-item {
    flex-direction: column;
    align-items: flex-start;
  }

  .cluster-size-presets {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>