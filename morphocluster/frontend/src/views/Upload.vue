<template>
  <div id="upload-view">
    <nav class="navbar navbar-expand-lg navbar navbar-dark bg-dark">
      <router-link class="navbar-brand" :to="{ name: 'home' }">MorphoCluster</router-link>
      <div class="navbar-collapse">
        <ul class="navbar-nav me-auto">
          <li class="navbar-item">
            <router-link class="nav-link" :to="{ name: 'files' }">Files</router-link>
          </li>
          <li class="navbar-item">
            <span class="nav-link active">Upload</span>
          </li>
        </ul>
      </div>
      <dark-mode-control />
    </nav>

    <div class="upload-container">
      <div class="container-fluid">
        <div class="row">
          <!-- Main Upload Section -->
          <div class="col-lg-8">
            <div class="upload-section">
              <h2>Upload Data Archives</h2>
              <p class="section-description">
                Upload ZIP archives containing images and metadata for processing in MorphoCluster.
                Supports EcoTaxa format and standard archive structures.
              </p>

              <upload-zone
                :upload-url="uploadUrl"
                :max-file-size="maxFileSize"
                :accepted-types="acceptedTypes"
                @upload-start="handleUploadStart"
                @upload-progress="handleUploadProgress"
                @upload-complete="handleUploadComplete"
                @upload-error="handleUploadError"
                @upload-cancel="handleUploadCancel"
              />

              <!-- Format Detection & Conversion -->
              <div v-if="uploadedArchives.length" class="mt-4">
                <h4>Uploaded Archives</h4>
                <div class="archives-list">
                  <div
                    v-for="archive in uploadedArchives"
                    :key="archive.id"
                    class="archive-item"
                    :class="{ 'needs-conversion': archive.needsConversion }"
                  >
                    <div class="archive-header">
                      <div class="archive-info">
                        <h6>{{ archive.name }}</h6>
                        <small class="text-muted">{{ formatBytes(archive.size) }}</small>
                      </div>
                      <div class="archive-status">
                        <b-badge
                          :variant="getArchiveStatusVariant(archive.status)"
                          class="me-2"
                        >
                          {{ getArchiveStatusText(archive.status) }}
                        </b-badge>
                        <span v-if="archive.format" class="format-badge">
                          {{ archive.format }}
                        </span>
                      </div>
                    </div>

                    <!-- EcoTaxa Conversion Warning -->
                    <b-alert
                      v-if="archive.needsConversion"
                      variant="warning"
                      show
                      class="mt-2"
                    >
                      <i class="mdi mdi-alert"></i>
                      This archive appears to be in EcoTaxa format and needs conversion.
                      <b-button
                        variant="warning"
                        size="sm"
                        class="ms-2"
                        @click="showConvertModal(archive)"
                      >
                        Convert Format
                      </b-button>
                    </b-alert>

                    <!-- Archive Actions -->
                    <div v-if="archive.status === 'ready'" class="archive-actions mt-2">
                      <b-button
                        variant="info"
                        size="sm"
                        @click="showExtractModal(archive)"
                        :disabled="!isArchiveValid(archive)"
                        class="me-2"
                      >
                        <i class="mdi mdi-cog"></i>
                        Extract Features
                      </b-button>
                      <b-button
                        variant="outline-secondary"
                        size="sm"
                        @click="previewArchive(archive)"
                      >
                        <i class="mdi mdi-eye"></i>
                        Preview
                      </b-button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Job Status Sidebar -->
          <div class="col-lg-4">
            <div class="job-status-section">
              <h4>Processing Jobs</h4>
              <job-status
                @job-completed="handleJobCompleted"
                @job-failed="handleJobFailed"
                @job-cancelled="handleJobCancelled"
              />
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Format Conversion Modal -->
    <format-modal
      v-if="showingConvertModal"
      :archive="selectedArchive"
      @convert="handleConvert"
      @cancel="hideConvertModal"
    />

    <!-- Feature Extraction Modal -->
    <feature-modal
      v-if="showingExtractModal"
      :archive="selectedArchive"
      @extract="handleExtract"
      @cancel="hideExtractModal"
    />

    <!-- Archive Preview Modal -->
    <b-modal
      v-model="showingPreviewModal"
      title="Archive Preview"
      size="lg"
      ok-only
      ok-title="Close"
    >
      <div v-if="previewData">
        <h6>Archive Contents</h6>
        <ul class="list-unstyled">
          <li v-for="file in previewData.files.slice(0, 10)" :key="file">
            <i class="mdi mdi-file"></i> {{ file }}
          </li>
          <li v-if="previewData.files.length > 10" class="text-muted">
            ... and {{ previewData.files.length - 10 }} more files
          </li>
        </ul>
        
        <h6 class="mt-3">Sample Entries</h6>
        <div v-if="previewData.sample_entries" class="table-responsive">
          <table class="table table-sm">
            <thead>
              <tr>
                <th v-for="column in Object.keys(previewData.sample_entries[0] || {})" :key="column">
                  {{ column }}
                </th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(entry, index) in previewData.sample_entries.slice(0, 5)" :key="index">
                <td v-for="column in Object.keys(entry)" :key="column">
                  {{ entry[column] }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </b-modal>
  </div>
</template>

<script>
import UploadZone from '@/components/UploadZone.vue';
import JobStatus from '@/components/JobStatus.vue';
import DarkModeControl from '@/components/DarkModeControl.vue';
import FormatModal from '@/components/FormatModal.vue';
import FeatureModal from '@/components/FeatureModal.vue';

export default {
  name: 'UploadView',
  components: {
    UploadZone,
    JobStatus,
    DarkModeControl,
    FormatModal,
    FeatureModal
  },
  data() {
    return {
      uploadUrl: '/api/upload',
      maxFileSize: 2 * 1024 * 1024 * 1024, // 2GB
      acceptedTypes: ['.zip', '.tar', '.tar.gz'],
      uploadedArchives: [],
      selectedArchive: null,
      showingConvertModal: false,
      showingExtractModal: false,
      showingPreviewModal: false,
      previewData: null
    };
  },
  methods: {
    handleUploadStart(files) {
      console.log('Upload started:', files);
    },

    handleUploadProgress(progress) {
      console.log('Upload progress:', progress);
    },

    async handleUploadComplete(result) {
      console.log('Upload completed:', result);
      
      // Process uploaded files and validate them
      for (const file of result.files) {
        try {
          const validation = await this.$axios.get(`/api/files/${file.name}/validate`);
          this.uploadedArchives.push({
            id: Date.now() + Math.random(),
            name: file.name,
            size: file.size,
            status: 'validating',
            format: validation.data.format,
            needsConversion: validation.data.needs_conversion,
            isValid: validation.data.is_valid,
            validation: validation.data
          });
        } catch (error) {
          console.error('Validation failed:', error);
          this.uploadedArchives.push({
            id: Date.now() + Math.random(),
            name: file.name,
            size: file.size,
            status: 'error',
            error: error.message
          });
        }
      }
      
      // Update archive statuses
      this.updateArchiveStatuses();
    },

    handleUploadError(error) {
      console.error('Upload error:', error);
      this.$bvToast.toast('Upload failed. Please try again.', {
        title: 'Upload Error',
        variant: 'danger',
        solid: true
      });
    },

    handleUploadCancel() {
      console.log('Upload cancelled');
    },

    async updateArchiveStatuses() {
      for (const archive of this.uploadedArchives) {
        if (archive.status === 'validating') {
          // Simulate validation completion
          setTimeout(() => {
            archive.status = archive.isValid ? 'ready' : 'error';
          }, 1000);
        }
      }
    },

    showConvertModal(archive) {
      this.selectedArchive = archive;
      this.showingConvertModal = true;
    },

    hideConvertModal() {
      this.showingConvertModal = false;
      this.selectedArchive = null;
    },

    showExtractModal(archive) {
      this.selectedArchive = archive;
      this.showingExtractModal = true;
    },

    hideExtractModal() {
      this.showingExtractModal = false;
      this.selectedArchive = null;
    },

    async previewArchive(archive) {
      try {
        const response = await this.$axios.get(`/api/files/${archive.name}/preview`);
        this.previewData = response.data;
        this.showingPreviewModal = true;
      } catch (error) {
        console.error('Preview failed:', error);
        this.$bvToast.toast('Failed to load preview.', {
          title: 'Preview Error',
          variant: 'danger',
          solid: true
        });
      }
    },

    async handleConvert(parameters) {
      this.hideConvertModal();
      
      try {
        await this.$axios.post(
          `/api/files/${this.selectedArchive.name}/convert`,
          parameters
        );
        
        this.$bvToast.toast('Format conversion started.', {
          title: 'Conversion Started',
          variant: 'info',
          solid: true
        });
        
        // Update archive status
        this.selectedArchive.status = 'converting';
        
      } catch (error) {
        console.error('Conversion failed:', error);
        this.$bvToast.toast('Failed to start conversion.', {
          title: 'Conversion Error',
          variant: 'danger',
          solid: true
        });
      }
    },

    async handleExtract(parameters) {
      this.hideExtractModal();
      
      try {
        await this.$axios.post(
          `/api/files/${this.selectedArchive.name}/extract`,
          parameters
        );
        
        this.$bvToast.toast('Feature extraction started.', {
          title: 'Extraction Started',
          variant: 'info',
          solid: true
        });
        
      } catch (error) {
        console.error('Extraction failed:', error);
        this.$bvToast.toast('Failed to start feature extraction.', {
          title: 'Extraction Error',
          variant: 'danger',
          solid: true
        });
      }
    },

    handleJobCompleted(job) {
      this.$bvToast.toast(`${this.getJobTitle(job)} completed successfully!`, {
        title: 'Job Completed',
        variant: 'success',
        solid: true
      });
      
      // Navigate to result if applicable
      if (job.result_url) {
        this.$router.push(job.result_url);
      }
    },

    handleJobFailed(job) {
      this.$bvToast.toast(`${this.getJobTitle(job)} failed: ${job.error_message}`, {
        title: 'Job Failed',
        variant: 'danger',
        solid: true,
        autoHideDelay: 8000
      });
    },

    handleJobCancelled(job) {
      this.$bvToast.toast(`${this.getJobTitle(job)} was cancelled.`, {
        title: 'Job Cancelled',
        variant: 'warning',
        solid: true
      });
    },

    getJobTitle(job) {
      const titles = {
        'format_conversion': 'Format Conversion',
        'feature_extraction': 'Feature Extraction',
        'initial_clustering': 'Project Creation',
        'reclustering': 'Re-clustering'
      };
      return titles[job.job_type] || 'Job';
    },

    isArchiveValid(archive) {
      return archive.status === 'ready' && archive.isValid;
    },

    getArchiveStatusVariant(status) {
      const variants = {
        'validating': 'warning',
        'ready': 'success',
        'converting': 'info',
        'error': 'danger'
      };
      return variants[status] || 'secondary';
    },

    getArchiveStatusText(status) {
      const texts = {
        'validating': 'Validating',
        'ready': 'Ready',
        'converting': 'Converting',
        'error': 'Error'
      };
      return texts[status] || 'Unknown';
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
#upload-view {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.upload-container {
  flex: 1;
  padding: 2rem 0;
  background-color: #f8f9fa;
}

.upload-section {
  background: white;
  border-radius: 8px;
  padding: 2rem;
  margin-bottom: 2rem;
}

.section-description {
  color: #6c757d;
  margin-bottom: 2rem;
}

.job-status-section {
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
  position: sticky;
  top: 2rem;
}

.archives-list {
  border: 1px solid #dee2e6;
  border-radius: 8px;
  background: white;
}

.archive-item {
  padding: 1.5rem;
  border-bottom: 1px solid #e9ecef;
}

.archive-item:last-child {
  border-bottom: none;
}

.archive-item.needs-conversion {
  background-color: #fff3cd;
  border-left: 4px solid #ffc107;
}

.archive-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 0.5rem;
}

.archive-info h6 {
  margin: 0;
  font-weight: 600;
}

.archive-status {
  display: flex;
  align-items: center;
}

.format-badge {
  background-color: #e9ecef;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 500;
  color: #495057;
}

.archive-actions {
  display: flex;
  gap: 0.5rem;
}

@media (max-width: 992px) {
  .job-status-section {
    position: static;
    margin-top: 2rem;
  }
  
  .upload-container {
    padding: 1rem 0;
  }
  
  .upload-section,
  .job-status-section {
    padding: 1.5rem;
  }
}

@media (max-width: 576px) {
  .archive-header {
    flex-direction: column;
    align-items: stretch;
  }
  
  .archive-status {
    margin-top: 0.5rem;
    justify-content: flex-start;
  }
  
  .archive-actions {
    flex-direction: column;
  }
}
</style>