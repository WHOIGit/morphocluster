<template>
  <div class="job-status-container">
    <div v-if="jobs.length === 0" class="no-jobs">
      <i class="mdi mdi-briefcase-outline"></i>
      <p>No active jobs</p>
    </div>

    <div v-else class="jobs-list">
      <div
        v-for="job in jobs"
        :key="job.id"
        class="job-item"
        :class="{ 
          'job-completed': job.status === 'completed',
          'job-failed': job.status === 'failed',
          'job-running': job.status === 'running'
        }"
      >
        <div class="job-header">
          <div class="job-info">
            <h6 class="job-title">{{ getJobTitle(job) }}</h6>
            <small class="job-details">{{ getJobDetails(job) }}</small>
          </div>
          <div class="job-actions">
            <b-button
              v-if="job.status === 'running'"
              size="sm"
              variant="outline-danger"
              @click="cancelJob(job.id)"
              :disabled="job.cancelling"
            >
              <i class="mdi mdi-stop"></i>
              {{ job.cancelling ? 'Cancelling...' : 'Cancel' }}
            </b-button>
            <b-button
              v-if="job.status === 'completed' || job.status === 'failed'"
              size="sm"
              variant="outline-secondary"
              @click="removeJob(job.id)"
            >
              <i class="mdi mdi-close"></i>
            </b-button>
          </div>
        </div>

        <div class="job-status">
          <div class="status-info">
            <i :class="getStatusIcon(job.status)"></i>
            <span class="status-text">{{ getStatusText(job.status) }}</span>
            <span v-if="job.status === 'running' && job.eta" class="eta">
              ETA: {{ formatTime(job.eta) }}
            </span>
          </div>
          
          <div v-if="job.status === 'running'" class="progress-container">
            <b-progress 
              :value="job.progress || 0" 
              :max="100"
              :variant="getProgressVariant(job.status)"
              :animated="job.status === 'running'"
              show-progress
            ></b-progress>
            <div v-if="job.current_step" class="current-step">
              {{ job.current_step }}
            </div>
          </div>

          <div v-if="job.status === 'failed' && job.error_message" class="error-message">
            <i class="mdi mdi-alert-circle"></i>
            {{ job.error_message }}
          </div>

          <div v-if="job.status === 'completed' && job.result_url" class="result-actions">
            <b-button
              size="sm"
              variant="success"
              @click="viewResult(job)"
            >
              <i class="mdi mdi-eye"></i>
              View Result
            </b-button>
          </div>
        </div>

        <div v-if="showLogs && job.logs && job.logs.length" class="job-logs">
          <small class="logs-title">Recent logs:</small>
          <div class="logs-content">
            <div
              v-for="(log, index) in job.logs.slice(-5)"
              :key="index"
              class="log-entry"
              :class="'log-' + log.level"
            >
              <span class="log-time">{{ formatLogTime(log.timestamp) }}</span>
              <span class="log-message">{{ log.message }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="jobs.length > 0" class="jobs-actions">
      <b-button
        size="sm"
        variant="outline-secondary"
        @click="toggleLogs"
      >
        <i :class="showLogs ? 'mdi mdi-chevron-up' : 'mdi mdi-chevron-down'"></i>
        {{ showLogs ? 'Hide' : 'Show' }} Logs
      </b-button>
      <b-button
        size="sm"
        variant="outline-danger"
        @click="clearCompletedJobs"
        :disabled="!hasCompletedJobs"
      >
        <i class="mdi mdi-delete-sweep"></i>
        Clear Completed
      </b-button>
    </div>
  </div>
</template>

<script>

export default {
  name: 'JobStatus',
  props: {
    autoRefresh: {
      type: Boolean,
      default: true
    },
    refreshInterval: {
      type: Number,
      default: 2000 // 2 seconds
    }
  },
  emits: ['job-completed', 'job-failed', 'job-cancelled'],
  data() {
    return {
      jobs: [],
      showLogs: false,
      refreshTimer: null,
      isLoading: false
    };
  },
  computed: {
    hasCompletedJobs() {
      return this.jobs.some(job => ['completed', 'failed'].includes(job.status));
    }
  },
  async mounted() {
    await this.fetchJobs();
    if (this.autoRefresh) {
      this.startRefresh();
    }
  },
  beforeUnmount() {
    this.stopRefresh();
  },
  methods: {
    async fetchJobs() {
      if (this.isLoading) return;
      
      this.isLoading = true;
      try {
        const response = await this.$axios.get('/api/jobs/user');
        const newJobs = response.data;
        
        // Check for status changes
        this.jobs.forEach(oldJob => {
          const newJob = newJobs.find(j => j.id === oldJob.id);
          if (newJob && oldJob.status !== newJob.status) {
            if (newJob.status === 'completed') {
              this.$emit('job-completed', newJob);
            } else if (newJob.status === 'failed') {
              this.$emit('job-failed', newJob);
            }
          }
        });
        
        this.jobs = newJobs;
      } catch (error) {
        console.error('Failed to fetch jobs:', error);
      } finally {
        this.isLoading = false;
      }
    },

    async cancelJob(jobId) {
      const job = this.jobs.find(j => j.id === jobId);
      if (job) {
        job.cancelling = true;
        try {
          await this.$axios.delete(`/api/jobs/${jobId}`);
          this.$emit('job-cancelled', job);
        } catch (error) {
          console.error('Failed to cancel job:', error);
          job.cancelling = false;
        }
      }
    },

    removeJob(jobId) {
      const index = this.jobs.findIndex(j => j.id === jobId);
      if (index !== -1) {
        this.jobs.splice(index, 1);
      }
    },

    clearCompletedJobs() {
      this.jobs = this.jobs.filter(job => !['completed', 'failed'].includes(job.status));
    },

    viewResult(job) {
      if (job.result_url) {
        this.$router.push(job.result_url);
      }
    },

    startRefresh() {
      if (this.refreshTimer) {
        clearInterval(this.refreshTimer);
      }
      this.refreshTimer = setInterval(() => {
        this.fetchJobs();
      }, this.refreshInterval);
    },

    stopRefresh() {
      if (this.refreshTimer) {
        clearInterval(this.refreshTimer);
        this.refreshTimer = null;
      }
    },

    toggleLogs() {
      this.showLogs = !this.showLogs;
    },

    getJobTitle(job) {
      const titles = {
        'format_conversion': 'Converting EcoTaxa Format',
        'feature_extraction': 'Extracting Features',
        'initial_clustering': 'Creating Project',
        'reclustering': 'Re-clustering Project'
      };
      return titles[job.job_type] || 'Processing';
    },

    getJobDetails(job) {
      if (job.job_type === 'format_conversion') {
        return `Archive: ${job.parameters?.archive_name || 'Unknown'}`;
      } else if (job.job_type === 'feature_extraction') {
        return `Model: ${job.parameters?.model || 'ImageNet'}, Batch: ${job.parameters?.batch_size || 512}`;
      } else if (job.job_type === 'initial_clustering' || job.job_type === 'reclustering') {
        return `Min cluster size: ${job.parameters?.min_cluster_size || 128}`;
      }
      return '';
    },

    getStatusIcon(status) {
      const icons = {
        'pending': 'mdi mdi-clock-outline text-warning',
        'running': 'mdi mdi-loading mdi-spin text-primary',
        'completed': 'mdi mdi-check-circle text-success',
        'failed': 'mdi mdi-alert-circle text-danger',
        'cancelled': 'mdi mdi-stop-circle text-secondary'
      };
      return icons[status] || 'mdi mdi-help-circle text-muted';
    },

    getStatusText(status) {
      const texts = {
        'pending': 'Pending',
        'running': 'Running',
        'completed': 'Completed',
        'failed': 'Failed',
        'cancelled': 'Cancelled'
      };
      return texts[status] || 'Unknown';
    },

    getProgressVariant(status) {
      const variants = {
        'running': 'primary',
        'completed': 'success',
        'failed': 'danger'
      };
      return variants[status] || 'secondary';
    },

    formatTime(seconds) {
      if (seconds < 60) return `${Math.round(seconds)}s`;
      if (seconds < 3600) return `${Math.round(seconds / 60)}m`;
      return `${Math.round(seconds / 3600)}h`;
    },

    formatLogTime(timestamp) {
      return new Date(timestamp).toLocaleTimeString();
    }
  }
};
</script>

<style scoped>
.job-status-container {
  border: 1px solid #dee2e6;
  border-radius: 8px;
  background: white;
}

.no-jobs {
  text-align: center;
  padding: 2rem;
  color: #6c757d;
}

.no-jobs i {
  font-size: 3rem;
  margin-bottom: 0.5rem;
}

.job-item {
  border-bottom: 1px solid #e9ecef;
  padding: 1rem;
}

.job-item:last-child {
  border-bottom: none;
}

.job-item.job-completed {
  border-left: 4px solid #28a745;
  background-color: #f8fff9;
}

.job-item.job-failed {
  border-left: 4px solid #dc3545;
  background-color: #fff5f5;
}

.job-item.job-running {
  border-left: 4px solid #007bff;
  background-color: #f8f9ff;
}

.job-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 0.5rem;
}

.job-info {
  flex: 1;
}

.job-title {
  margin: 0 0 0.25rem 0;
  font-weight: 600;
  color: #495057;
}

.job-details {
  color: #6c757d;
  font-size: 0.875rem;
}

.job-actions {
  margin-left: 1rem;
}

.job-status {
  margin-bottom: 0.5rem;
}

.status-info {
  display: flex;
  align-items: center;
  margin-bottom: 0.75rem;
}

.status-info i {
  margin-right: 0.5rem;
}

.status-text {
  font-weight: 500;
  margin-right: 1rem;
}

.eta {
  color: #6c757d;
  font-size: 0.875rem;
}

.progress-container {
  margin-bottom: 0.5rem;
}

.current-step {
  font-size: 0.875rem;
  color: #6c757d;
  margin-top: 0.25rem;
}

.error-message {
  display: flex;
  align-items: flex-start;
  color: #dc3545;
  font-size: 0.875rem;
  padding: 0.5rem;
  background-color: #f8d7da;
  border: 1px solid #f5c6cb;
  border-radius: 4px;
}

.error-message i {
  margin-right: 0.5rem;
  margin-top: 0.1rem;
}

.result-actions {
  margin-top: 0.5rem;
}

.job-logs {
  margin-top: 1rem;
  padding-top: 0.75rem;
  border-top: 1px solid #e9ecef;
}

.logs-title {
  font-weight: 600;
  color: #495057;
  display: block;
  margin-bottom: 0.5rem;
}

.logs-content {
  background-color: #f8f9fa;
  border: 1px solid #dee2e6;
  border-radius: 4px;
  padding: 0.5rem;
  max-height: 200px;
  overflow-y: auto;
}

.log-entry {
  font-family: monospace;
  font-size: 0.75rem;
  margin-bottom: 0.25rem;
  display: flex;
}

.log-time {
  color: #6c757d;
  margin-right: 0.5rem;
  flex-shrink: 0;
}

.log-message {
  flex: 1;
}

.log-entry.log-error {
  color: #dc3545;
}

.log-entry.log-warning {
  color: #fd7e14;
}

.log-entry.log-info {
  color: #17a2b8;
}

.jobs-actions {
  padding: 0.75rem 1rem;
  border-top: 1px solid #e9ecef;
  background-color: #f8f9fa;
  display: flex;
  justify-content: space-between;
}

@media (max-width: 768px) {
  .job-header {
    flex-direction: column;
    align-items: stretch;
  }

  .job-actions {
    margin-left: 0;
    margin-top: 0.5rem;
  }

  .status-info {
    flex-wrap: wrap;
  }

  .eta {
    width: 100%;
    margin-top: 0.25rem;
  }

  .jobs-actions {
    flex-direction: column;
    gap: 0.5rem;
  }
}
</style>