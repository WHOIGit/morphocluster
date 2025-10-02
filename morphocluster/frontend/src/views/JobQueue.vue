<template>
  <div id="job-queue">
    <nav class="navbar navbar-expand-lg navbar navbar-dark bg-dark">
      <router-link class="navbar-brand" :to="{ name: 'projects' }">
        <img src="/frontend/favicon.png" alt="MorphoCluster" class="navbar-logo" />
        MorphoCluster
      </router-link>
      <ul class="navbar-nav me-auto">
        <li class="nav-item">
          <router-link class="nav-link" :to="{ name: 'projects' }">Projects</router-link>
        </li>
        <li class="nav-item">
          <router-link class="nav-link" :to="{ name: 'files' }">Files</router-link>
        </li>
        <li class="nav-item">
          <router-link class="nav-link" :to="{ name: 'upload' }">Upload</router-link>
        </li>
        <li class="nav-item">
          <span class="nav-link active">Jobs</span>
        </li>
      </ul>
      <dark-mode-control />
    </nav>

    <div class="scrollable">
      <div class="container-fluid">
        <div class="row">
          <!-- Main Job Queue Section -->
          <div class="col-lg-12">
            <div class="job-queue-header">
              <h2>
                <i class="mdi mdi-briefcase-multiple"></i>
                Job Queue
              </h2>
              <p class="section-description">
                Monitor and manage all your background processing jobs including format conversion,
                feature extraction, clustering, and re-clustering operations.
              </p>
            </div>

            <!-- Alerts -->
            <div class="alerts" v-if="alerts.length">
              <b-alert :key="alert.id" v-for="alert of alerts" dismissible show :variant="alert.variant" @dismissed="removeAlert(alert.id)">
                {{ alert.message }}
              </b-alert>
            </div>

            <!-- Job Statistics -->
            <div class="job-stats row mb-4">
              <div class="col-md-3">
                <div class="stat-card stat-running">
                  <div class="stat-icon">
                    <i class="mdi mdi-play-circle"></i>
                  </div>
                  <div class="stat-info">
                    <div class="stat-number">{{ runningJobs.length }}</div>
                    <div class="stat-label">Running</div>
                  </div>
                </div>
              </div>
              <div class="col-md-3">
                <div class="stat-card stat-queued">
                  <div class="stat-icon">
                    <i class="mdi mdi-clock-outline"></i>
                  </div>
                  <div class="stat-info">
                    <div class="stat-number">{{ queuedJobs.length }}</div>
                    <div class="stat-label">Queued</div>
                  </div>
                </div>
              </div>
              <div class="col-md-3">
                <div class="stat-card stat-completed">
                  <div class="stat-icon">
                    <i class="mdi mdi-check-circle"></i>
                  </div>
                  <div class="stat-info">
                    <div class="stat-number">{{ completedJobs.length }}</div>
                    <div class="stat-label">Completed</div>
                  </div>
                </div>
              </div>
              <div class="col-md-3">
                <div class="stat-card stat-failed">
                  <div class="stat-icon">
                    <i class="mdi mdi-alert-circle"></i>
                  </div>
                  <div class="stat-info">
                    <div class="stat-number">{{ failedJobs.length }}</div>
                    <div class="stat-label">Failed</div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Job Filters -->
            <div class="job-filters mb-4">
              <div class="filter-buttons">
                <b-button
                  v-for="filter in filters"
                  :key="filter.key"
                  :variant="activeFilter === filter.key ? 'primary' : 'outline-primary'"
                  size="sm"
                  class="me-2"
                  @click="setFilter(filter.key)"
                >
                  {{ filter.label }}
                  <b-badge v-if="filter.count > 0" variant="light" class="ms-1">
                    {{ filter.count }}
                  </b-badge>
                </b-button>
              </div>
              <div class="filter-actions">
                <b-button
                  v-if="completedJobs.length > 0 || failedJobs.length > 0"
                  variant="outline-danger"
                  size="sm"
                  @click="clearCompleted"
                >
                  <i class="mdi mdi-delete-sweep"></i>
                  Clear Completed
                </b-button>
                <b-button
                  variant="outline-secondary"
                  size="sm"
                  @click="refreshJobs"
                  :disabled="isRefreshing"
                >
                  <i class="mdi mdi-refresh" :class="{ 'mdi-spin': isRefreshing }"></i>
                  Refresh
                </b-button>
              </div>
            </div>

            <!-- Jobs List -->
            <div class="jobs-container">
              <job-status
                ref="jobStatus"
                :show-logs="true"
                :auto-refresh="true"
                :filter-status="activeFilter !== 'all' ? activeFilter : null"
                @job-completed="handleJobCompleted"
                @job-failed="handleJobFailed"
                @job-cancelled="handleJobCancelled"
                @jobs-updated="handleJobsUpdated"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import JobStatus from '@/components/JobStatus.vue';
import DarkModeControl from '@/components/DarkModeControl.vue';

export default {
  name: 'JobQueueView',
  components: {
    JobStatus,
    DarkModeControl,
  },
  data() {
    return {
      activeFilter: 'all',
      isRefreshing: false,
      completedJobIds: new Set(), // Track completed jobs for notifications
      alerts: [],
      nextAlertId: 1,
      jobs: [], // Local copy of jobs for reactivity
    };
  },
  mounted() {
    // Sync initial jobs data after JobStatus is mounted
    this.$nextTick(() => {
      if (this.$refs.jobStatus && this.$refs.jobStatus.jobs) {
        this.jobs = this.$refs.jobStatus.jobs;
      }
    });
  },
  computed: {
    allJobs() {
      return this.jobs; // All jobs for statistics
    },
    filteredJobs() {
      // Jobs filtered by active filter for display
      if (this.activeFilter === 'all') {
        return this.jobs;
      }
      return this.jobs.filter(job => job.status === this.activeFilter);
    },
    runningJobs() {
      return this.jobs.filter(job => job.status === 'running');
    },
    queuedJobs() {
      return this.jobs.filter(job => job.status === 'queued');
    },
    completedJobs() {
      return this.jobs.filter(job => job.status === 'completed');
    },
    failedJobs() {
      return this.jobs.filter(job => job.status === 'failed');
    },
    filters() {
      return [
        { key: 'all', label: 'All', count: this.jobs.length },
        { key: 'running', label: 'Running', count: this.runningJobs.length },
        { key: 'queued', label: 'Queued', count: this.queuedJobs.length },
        { key: 'completed', label: 'Completed', count: this.completedJobs.length },
        { key: 'failed', label: 'Failed', count: this.failedJobs.length },
      ];
    },
  },
  methods: {
    setFilter(filter) {
      this.activeFilter = filter;
    },
    async refreshJobs() {
      this.isRefreshing = true;
      try {
        await this.$refs.jobStatus.fetchJobs();
      } finally {
        this.isRefreshing = false;
      }
    },
    clearCompleted() {
      this.$refs.jobStatus.clearCompletedJobs();
    },
    handleJobCompleted(job) {
      // Show success alert
      this.addAlert(`Job "${this.getJobTitle(job)}" completed successfully!`, 'success');
    },
    handleJobFailed(job) {
      // Show error alert
      this.addAlert(`Job "${this.getJobTitle(job)}" failed: ${job.error_message || 'Unknown error'}`, 'danger');
    },
    handleJobCancelled(job) {
      this.addAlert(`Job "${this.getJobTitle(job)}" was cancelled.`, 'warning');
    },
    handleJobsUpdated(jobs) {
      // Sync jobs data from JobStatus component
      this.jobs = jobs;
    },
    addAlert(message, variant = 'info') {
      const alert = {
        id: this.nextAlertId++,
        message,
        variant,
      };
      this.alerts.unshift(alert);

      // Auto-remove after 5 seconds
      setTimeout(() => {
        this.removeAlert(alert.id);
      }, 5000);
    },
    removeAlert(alertId) {
      const index = this.alerts.findIndex(alert => alert.id === alertId);
      if (index !== -1) {
        this.alerts.splice(index, 1);
      }
    },
    getJobTitle(job) {
      // Use the same logic as JobStatus component
      if (job.name) return job.name;
      if (job.description) return job.description;
      return `${job.type || 'Processing'} Job`;
    },
  },
};
</script>

<style scoped>
#job-queue {
  display: flex;
  flex-direction: column;
  align-items: stretch;
  flex: 1;
  overflow: hidden;
}

.scrollable {
  overflow-y: auto;
  flex: 1;
}

.job-queue-header {
  padding: 1.5rem 0 1rem;
  border-bottom: 1px solid var(--border-color);
  margin-bottom: 1.5rem;
}

.job-queue-header h2 {
  margin-bottom: 0.5rem;
  color: var(--text-primary);
}

.job-queue-header h2 i {
  margin-right: 0.5rem;
}

.section-description {
  color: var(--text-secondary);
  margin-bottom: 0;
}

/* Alerts */
.alerts {
  margin-bottom: 1rem;
}

/* Job Statistics */
.job-stats {
  margin-bottom: 1.5rem;
}

.stat-card {
  display: flex;
  align-items: center;
  padding: 1rem;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  background: var(--card-bg);
  border-left: 4px solid transparent;
  color: var(--text-primary);
}

.stat-running {
  border-left-color: #007bff;
}

.stat-queued {
  border-left-color: #ffc107;
}

.stat-completed {
  border-left-color: #28a745;
}

.stat-failed {
  border-left-color: #dc3545;
}

.stat-icon {
  font-size: 2rem;
  margin-right: 1rem;
}

.stat-running .stat-icon {
  color: #007bff;
}

.stat-queued .stat-icon {
  color: #ffc107;
}

.stat-completed .stat-icon {
  color: #28a745;
}

.stat-failed .stat-icon {
  color: #dc3545;
}

.stat-info {
  flex: 1;
}

.stat-number {
  font-size: 1.5rem;
  font-weight: bold;
  line-height: 1;
  margin-bottom: 0.25rem;
}

.stat-label {
  font-size: 0.875rem;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* Job Filters */
.job-filters {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  background: var(--bg-secondary);
  border-radius: 8px;
  flex-wrap: wrap;
  gap: 1rem;
}

.filter-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.filter-actions {
  display: flex;
  gap: 0.5rem;
}

/* Jobs Container */
.jobs-container {
  background: var(--card-bg);
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  padding: 1rem;
}

/* Responsive */
@media (max-width: 768px) {
  .job-filters {
    flex-direction: column;
    align-items: stretch;
  }

  .filter-buttons {
    justify-content: center;
  }

  .filter-actions {
    justify-content: center;
  }

  .job-stats .col-md-3 {
    margin-bottom: 1rem;
  }
}

/* Animations */
.mdi-spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>