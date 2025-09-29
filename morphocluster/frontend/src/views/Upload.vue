<template>
  <div id="upload-view">
    <nav class="navbar navbar-expand-lg navbar navbar-dark bg-dark">
      <router-link class="navbar-brand" :to="{ name: 'projects' }">MorphoCluster</router-link>
      <div class="navbar-collapse">
        <ul class="navbar-nav me-auto">
          <li class="navbar-item">
            <router-link class="nav-link" :to="{ name: 'projects' }">Projects</router-link>
          </li>
          <li class="navbar-item">
            <router-link class="nav-link" :to="{ name: 'files' }">Files</router-link>
          </li>
          <li class="navbar-item">
            <span class="nav-link active">Upload</span>
          </li>
          <li class="navbar-item">
            <router-link class="nav-link" :to="{ name: 'jobs' }">Jobs</router-link>
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
                    :class="{ 'needs-conversion': archive.needs_conversion }"
                  >
                    <div class="archive-header">
                      <div class="archive-info">
                        <h6>{{ archive.original_filename || archive.filename || 'Unknown' }}</h6>
                        <small class="text-muted">{{ formatBytes(archive.file_size) || 'Size unknown' }}</small>
                      </div>
                      <div class="archive-status">
                        <b-badge
                          :variant="getArchiveStatusVariant(archive.status)"
                          class="me-2"
                        >
                          {{ getArchiveStatusText(archive.status) }}
                        </b-badge>
                        <span v-if="getArchiveFormat(archive)" class="format-badge">
                          {{ getArchiveFormat(archive) }}
                        </span>
                      </div>
                    </div>

                    <!-- EcoTaxa Conversion Warning -->
                    <div v-if="archive.needs_conversion" class="alert alert-warning mt-2">
                      <i class="mdi mdi-alert"></i>
                      This archive appears to be in EcoTaxa format and needs conversion.
                      <button
                        class="btn btn-warning btn-sm ms-2"
                        @click="showConvertModal(archive)"
                      >
                        Convert Format
                      </button>
                    </div>

                    <!-- Error Details -->
                    <b-alert
                      v-if="archive.status === 'error'"
                      variant="danger"
                      show
                      class="mt-2"
                    >
                      <i class="mdi mdi-alert-circle"></i>
                      <strong>Validation Error:</strong><br>
                      {{ archive.error_message || 'Unknown error occurred during validation' }}
                      <div v-if="getValidationData(archive)?.validation_warnings?.length" class="mt-2">
                        <small><strong>Warnings:</strong></small>
                        <ul class="mb-0 mt-1">
                          <li v-for="warning in getValidationData(archive).validation_warnings" :key="warning">
                            {{ warning }}
                          </li>
                        </ul>
                      </div>
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

                    <!-- Post-Processing Actions -->
                    <div v-if="archive.status === 'processed'" class="archive-actions mt-2">
                      <b-button
                        variant="success"
                        size="sm"
                        @click="showClusterModal(archive)"
                        class="me-2"
                      >
                        <i class="mdi mdi-sitemap"></i>
                        Create Project
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
                    <!-- Project Actions -->
                    <div v-if="archive.status === 'clustered'" class="archive-actions mt-2">
                      <b-button
                        variant="primary"
                        size="sm"
                        @click="viewProject(archive)"
                        class="me-2"
                      >
                        <i class="mdi mdi-folder-open"></i>
                        View Project
                      </b-button>
                      <span class="project-info text-muted">
                        Project: {{ getProjectName(archive) || 'Unknown' }}
                      </span>
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
                ref="jobStatus"
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

    <!-- Clustering Modal -->
    <cluster-modal
      v-if="showingClusterModal"
      :archive="selectedArchive"
      :feature-file="selectedArchive?.featureFile"
      @cluster="handleCluster"
      @cancel="hideClusterModal"
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
import ClusterModal from '@/components/ClusterModal.vue';
import { getUploadedArchives, saveUploadedArchive, updateUploadedArchive } from '@/helpers/api';

export default {
  name: 'UploadView',
  components: {
    UploadZone,
    JobStatus,
    DarkModeControl,
    FormatModal,
    FeatureModal,
    ClusterModal
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
      showingClusterModal: false,
      showingPreviewModal: false,
      previewData: null,
      processedJobIds: new Set() // Track processed job IDs to prevent duplicates
    };
  },
  async mounted() {
    // Load persisted archives on component mount
    try {
      const persistedArchives = await getUploadedArchives();
      this.uploadedArchives = persistedArchives;

    } catch (error) {
      console.error('Failed to load persisted archives:', error);
      // Keep empty array as fallback
    }
  },
  methods: {
    handleUploadStart(files) {
      console.log('Upload started:', files);
    },

    handleUploadProgress(progress) {
      console.log('Upload progress:', progress);
    },

    async handleUploadComplete(result) {
      console.log('Upload.vue: handleUploadComplete called');
      console.log('Upload completed:', result);

      // Debug: check the structure
      console.log('result.response:', result.response);
      console.log('result.response?.files:', result.response?.files);

      // Get files from the API response (not the component's uploadedFiles)
      const uploadedFiles = result.response?.files || [];
      console.log('Files to validate:', uploadedFiles);

      if (uploadedFiles.length === 0) {
        console.error('No files found in response for validation');
        return;
      }

      // Process uploaded files and validate them
      for (const file of uploadedFiles) {
        console.log('Validating file:', file.name);
        try {
          const validation = await this.$axios.get(`/api/files/${encodeURIComponent(file.name)}/validate`);
          console.log('Validation result:', validation.data);

          const archiveData = {
            filename: file.name,
            original_filename: file.name,
            file_size: file.size,
            status: 'ready',
            is_valid: validation.data.is_valid,
            needs_conversion: validation.data.needs_conversion,
            validation_data: JSON.stringify(validation.data),
            metadata: JSON.stringify({
              format: validation.data.format
            })
          };

          // Save to backend and get the persisted record
          console.log('Saving archive to backend:', archiveData);
          const savedArchive = await saveUploadedArchive(archiveData);
          console.log('Saved archive response:', savedArchive);
          this.uploadedArchives.push(savedArchive);
        } catch (error) {
          console.error('Validation failed for', file.name, ':', error);
          const errorArchive = {
            filename: file.name,
            original_filename: file.name,
            file_size: file.size,
            status: 'error',
            is_valid: false,
            needs_conversion: false,
            error_message: error.response?.data?.error || error.message
          };

          console.log('Saving error archive to backend:', errorArchive);
          const savedArchive = await saveUploadedArchive(errorArchive);
          console.log('Saved error archive response:', savedArchive);
          this.uploadedArchives.push(savedArchive);
        }
      }
    },

    handleUploadError(error) {
      console.error('Upload error:', error);
      alert('Upload failed. Please try again: ' + error.message);
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

    showClusterModal(archive) {
      this.selectedArchive = archive;
      this.showingClusterModal = true;
    },

    hideClusterModal() {
      this.showingClusterModal = false;
      this.selectedArchive = null;
    },
    viewProject(archive) {
      if (archive.project_id) {
        // Navigate to the project view
        this.$router.push(`/p/${archive.project_id}`);
      } else {
        console.error('No project ID available for archive:', archive.original_filename);
      }
    },

    async previewArchive(archive) {
      try {
        const response = await this.$axios.get(`/api/files/${archive.filename}/preview`);
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
      const archive = this.selectedArchive;
      this.hideConvertModal();

      if (!archive) {
        console.error('No archive selected for conversion');
        return;
      }

      try {
        console.log('Converting archive:', {
          filename: archive.filename,
          original_filename: archive.original_filename,
          full_archive_object: archive
        });

        await this.$axios.post(
          `/api/files/${archive.filename}/convert`,
          parameters
        );

        console.log('Format conversion started for:', archive.original_filename);

        // Update archive status
        await this.updateArchive(archive, { status: 'converting' });

        // Immediately refresh job list to show the new job
        this.$refs.jobStatus?.fetchJobs();

      } catch (error) {
        console.error('Conversion failed:', error);
        console.error('Error details:', error.response?.data);
      }
    },

    async handleExtract(parameters) {
      const archive = this.selectedArchive;
      this.hideExtractModal();

      if (!archive) {
        console.error('No archive selected for extraction');
        return;
      }

      try {
        await this.$axios.post(
          `/api/files/${archive.filename}/extract`,
          parameters
        );

        // Update archive status
        await this.updateArchive(archive, { status: 'extracting' });

        // Immediately refresh job list to show the new job
        this.$refs.jobStatus?.fetchJobs();

      } catch (error) {
        console.error('Extraction failed:', error);
        console.error('Error details:', error.response?.data);
      }
    },

    async handleCluster(parameters) {
      const archive = this.selectedArchive;
      this.hideClusterModal();

      if (!archive) {
        console.error('No archive selected for clustering');
        return;
      }

      try {
        await this.$axios.post(
          `/api/files/${encodeURIComponent(archive.filename)}/cluster`,
          parameters
        );

        // Update archive status
        await this.updateArchive(archive, { status: 'clustering' });

        // Immediately refresh job list to show the new job
        this.$refs.jobStatus?.fetchJobs();

      } catch (error) {
        console.error('Clustering failed:', error);
      }
    },

    async handleJobCompleted(job) {
      // Check if this job has already been processed to prevent duplicates
      if (this.processedJobIds.has(job.id)) {
        return;
      }

      // Mark job as processed
      this.processedJobIds.add(job.id);

      // Helper function to find archive with flexible name matching
      const findArchive = (archiveName) => {
        if (!archiveName) return null;

        const nameWithZip = archiveName.endsWith('.zip') ? archiveName : archiveName + '.zip';
        const nameWithoutZip = archiveName.replace(/\.zip$/, '');

        return this.uploadedArchives.find(a =>
          a.filename === archiveName ||
          a.original_filename === archiveName ||
          a.filename === nameWithZip ||
          a.original_filename === nameWithZip ||
          a.filename === nameWithoutZip ||
          a.original_filename === nameWithoutZip
        );
      };

      // Update archive status based on job type
      if (job.job_type === 'format_conversion' && job.archive_name) {
        const archive = findArchive(job.archive_name);
        if (archive && !archive.project_id) { // Don't update if project already exists
          const updates = {
            status: 'ready',
            needs_conversion: false,
            metadata: JSON.stringify({
              ...this.parseMetadata(archive),
              format: 'standard'
            })
          };

          // Update archive name to point to converted file
          if (job.result && job.result.converted_file) {
            updates.filename = job.result.converted_file;
          }

          await this.updateArchive(archive, updates);
        }
      } else if (job.job_type === 'feature_extraction' && job.archive_name) {
        const archive = findArchive(job.archive_name);
        if (archive && !archive.project_id) { // Don't update if project already exists
          const updates = {
            status: 'processed'
          };

          // Store feature file info for clustering
          if (job.result && job.result.feature_file) {
            updates.feature_file = job.result.feature_file;
          }

          await this.updateArchive(archive, updates);
        }
      } else if (job.job_type === 'initial_clustering' && job.archive_name) {
        const archive = findArchive(job.archive_name);
        if (archive) {
          const updates = {
            status: 'clustered'
          };

          // Store project info
          if (job.result && job.result.project_id) {
            updates.project_id = job.result.project_id;
            // Create clean metadata object
            const cleanMetadata = {
              format: 'standard',
              project_name: job.result.project_name
            };
            updates.metadata = JSON.stringify(cleanMetadata);
          }

          await this.updateArchive(archive, updates);
        }
      }

      // Navigate to result if applicable
      if (job.result_url) {
        this.$router.push(job.result_url);
      }
    },

    async handleJobFailed(job) {
      // Helper function to find archive (same as in handleJobCompleted)
      const findArchive = (archiveName) => {
        if (!archiveName) return null;

        const nameWithZip = archiveName.endsWith('.zip') ? archiveName : archiveName + '.zip';
        const nameWithoutZip = archiveName.replace(/\.zip$/, '');

        return this.uploadedArchives.find(a =>
          a.filename === archiveName ||
          a.original_filename === archiveName ||
          a.filename === nameWithZip ||
          a.original_filename === nameWithZip ||
          a.filename === nameWithoutZip ||
          a.original_filename === nameWithoutZip
        );
      };

      // Reset archive status if conversion failed
      if (job.job_type === 'format_conversion' && job.archive_name) {
        const archive = findArchive(job.archive_name);
        if (archive) {
          await this.updateArchive(archive, {
            status: 'ready', // Back to ready so user can try again
            error_message: job.error_message
          });
        }
      }
    },

    handleJobCancelled() {
      // Job was cancelled, no specific action needed
    },

    async updateArchive(archive, updates) {
      try {
        console.log('updateArchive: calling API with id:', archive.id, 'updates:', updates);
        const updatedArchive = await updateUploadedArchive(archive.id, updates);
        console.log('updateArchive: API response:', updatedArchive);
        // Update local copy with server response
        Object.assign(archive, updatedArchive);
        console.log('updateArchive: local object after assign:', {
          needs_conversion: archive.needs_conversion,
          status: archive.status,
          filename: archive.filename
        });
      } catch (error) {
        console.error('Failed to update archive:', error);
        console.log('updateArchive: using fallback, applying updates locally:', updates);
        // Fallback: apply updates locally only
        Object.assign(archive, updates);
        console.log('updateArchive: local object after fallback:', {
          needs_conversion: archive.needs_conversion,
          status: archive.status,
          filename: archive.filename
        });
      }
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
      return archive.status === 'ready' && archive.is_valid;
    },

    getArchiveFormat(archive) {
      try {
        const metadata = JSON.parse(archive.metadata || '{}');
        return metadata.format;
      } catch {
        return null;
      }
    },

    getValidationData(archive) {
      try {
        return JSON.parse(archive.validation_data || '{}');
      } catch {
        return {};
      }
    },

    getProjectName(archive) {
      try {
        const metadata = JSON.parse(archive.metadata || '{}');
        return metadata.project_name;
      } catch {
        return null;
      }
    },

    parseMetadata(archive) {
      try {
        const metadataStr = archive.metadata || '{}';
        return JSON.parse(metadataStr);
      } catch (error) {
        console.warn('Failed to parse archive metadata:', error, 'Raw metadata:', archive.metadata);
        // If parsing fails, try to handle common cases
        if (typeof archive.metadata === 'object') {
          return archive.metadata; // Already an object
        }
        return {}; // Fallback to empty object
      }
    },

    getArchiveStatusVariant(status) {
      const variants = {
        'validating': 'warning',
        'ready': 'success',
        'converting': 'info',
        'extracting': 'info',
        'processing': 'info',
        'clustering': 'info',
        'processed': 'primary',
        'clustered': 'success',
        'error': 'danger'
      };
      return variants[status] || 'secondary';
    },

    getArchiveStatusText(status) {
      const texts = {
        'validating': 'Validating',
        'ready': 'Ready',
        'converting': 'Converting',
        'extracting': 'Extracting',
        'processing': 'Processing',
        'clustering': 'Clustering',
        'processed': 'Processed',
        'clustered': 'Project Created',
        'error': 'Error'
      };
      return texts[status] || 'Unknown';
    },

    formatBytes(bytes) {
      // Handle invalid input
      if (bytes === null || bytes === undefined || isNaN(bytes)) {
        return null; // This will trigger the fallback in the template
      }
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
  padding: 2rem 0 4rem 0;
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
  max-height: calc(100vh - 4rem);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.job-status-section h4 {
  margin-bottom: 1rem;
  flex-shrink: 0;
}

/* Make the JobStatus component scrollable */
.job-status-section >>> .job-status-container {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  max-height: calc(100vh - 8rem);
}

/* Also target the jobs list directly */
.job-status-section >>> .jobs-list {
  max-height: calc(100vh - 8rem);
  overflow-y: auto;
}

.job-status-section >>> .job-item {
  flex-shrink: 0;
}

.archives-list {
  border: 1px solid #dee2e6;
  border-radius: 8px;
  background: white;
  max-height: 40vh;
  overflow-y: auto;
  margin-bottom: 2rem;
  padding-bottom: 1rem;
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