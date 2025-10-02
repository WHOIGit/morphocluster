<template>
    <div id="projects">
        <nav class="navbar navbar-expand-lg navbar navbar-dark bg-dark">
            <router-link class="navbar-brand" :to="{ name: 'projects' }">
                <img src="/frontend/favicon.png" alt="MorphoCluster" class="navbar-logo" />
                MorphoCluster
            </router-link>
            <ul class="navbar-nav me-auto">
                <li class="nav-item">
                    <span class="nav-link active">Projects</span>
                </li>
                <li class="nav-item">
                    <router-link class="nav-link" :to="{ name: 'files' }">Files</router-link>
                </li>
                <li class="nav-item">
                    <router-link class="nav-link" :to="{ name: 'upload' }">Upload</router-link>
                </li>
                <li class="nav-item">
                    <router-link class="nav-link" :to="{ name: 'jobs' }">Jobs</router-link>
                </li>
            </ul>
            <dark-mode-control />
        </nav>
        <div class="scrollable">
            <div class="container">
                <div class="alerts" v-if="alerts.length">
                    <b-alert :key="a" v-for="a of alerts" dismissible show :variant="a.variant">
                        {{ a.message }}
                    </b-alert>
                </div>
                <b-table id="projects_table" striped sort-by="name" :items="projects" :fields="fields" showEmpty>
                    <template slot="table-colgroup">
                        <col class="col-wide" />
                        <col class="col-narrow" />
                    </template>
                    <template v-slot:cell(name)="data">
                        <router-link :to="{
                            name: 'project',
                            params: { project_id: data.item.project_id },
                        }">{{ data.item.name }}</router-link>
                    </template>
                    <template v-slot:cell(progress)="data">
                        <!-- validated / grown clusters -->
                        <b-progress v-if="'progress' in data.item" :max="data.item.progress.leaves_n_nodes" class="mb-1">
                            <b-progress-bar variant="success" :value="data.item.progress.leaves_n_filled_nodes
                            " v-b-tooltip.hover
                                :title="`${data.item.progress.leaves_n_filled_nodes} / ${data.item.progress.leaves_n_nodes} clusters grown`" />
                            <b-progress-bar variant="warning" :value="data.item.progress.leaves_n_approved_nodes -
                                data.item.progress.leaves_n_filled_nodes
                            " v-b-tooltip.hover :title="`${Humanize.compactInteger(
    data.item.progress.leaves_n_approved_nodes,
    1
)} / ${Humanize.compactInteger(
    data.item.progress.leaves_n_nodes,
    1
)} clusters validated`" />
                        </b-progress>
                        <!-- objects in clusters -->
                        <b-progress v-if="'progress' in data.item" :max="data.item.progress.n_objects_deep" class="mb-1"
                            :title="`${Humanize.compactInteger(
                                data.item.progress.leaves_n_approved_objects,
                                1
                            )} / ${Humanize.compactInteger(
                                data.item.progress.n_objects_deep,
                                1
                            )} (${Math.round(
                                (data.item.progress.leaves_n_approved_objects /
                                    data.item.progress.n_objects_deep) *
                                100
                            )}%) objects in validated clusters`">
                            <b-progress-bar variant="success" :value="data.item.progress.leaves_n_approved_objects
                            " v-b-tooltip.hover />
                        </b-progress>
                    </template>
                    <template v-slot:cell(action)="data">
                        <b-button size="sm" variant="primary" class="mr-2" :to="{
                            name: 'approve',
                            params: { project_id: data.item.project_id },
                        }">
                            Validate
                        </b-button>
                        <b-button size="sm" variant="primary" class="mr-2" :to="{
                            name: 'bisect',
                            params: { project_id: data.item.project_id },
                        }">Grow</b-button>
                        <b-button
                            size="sm"
                            :variant="isProjectReadyForReclustering(data.item) ? 'info' : 'secondary'"
                            :disabled="!isProjectReadyForReclustering(data.item)"
                            class="mr-2"
                            @click="showReclusterModal(data.item)"
                            v-b-tooltip.hover
                            :title="getReclusterTooltip(data.item)"
                        >
                            Re-cluster
                        </b-button>
                    </template>
                    <template v-slot:empty>
                        <div class="text-center">No projects available.</div>
                    </template>
                </b-table>
                <p v-if="!projects">No projects available.</p>
                <div style="margin: 0 auto; width: 0">
                    <b-button size="sm" variant="danger" class="mr-2" href="/labeling">
                        Expert mode
                    </b-button>
                </div>
            </div>
        </div>

        <!-- Re-cluster Modal -->
        <cluster-modal
            v-if="showReclusteringModal"
            :project="selectedProject"
            @cluster="handleRecluster"
            @cancel="handleReclusterCancel"
        />
    </div>
</template>

<script>
import * as api from "@/helpers/api.js";
import DarkModeControl from "@/components/DarkModeControl.vue";
import ClusterModal from "@/components/ClusterModal.vue";


import Humanize from "humanize-plus";

export default {
    name: "ProjectsView",
    props: {},
    components: {
        DarkModeControl,
        ClusterModal
    },
    data() {
        return {
            fields: [
                //{ key: "project_id", sortable: true },
                { key: "name", sortable: true },
                "progress",
                "action",
            ],
            projects: [],
            alerts: [],
            showReclusteringModal: false,
            selectedProject: null,
            // Make Humanize available in template:
            Humanize,
        };
    },
    methods: {
        showReclusterModal(project) {
            if (!this.isProjectReadyForReclustering(project)) {
                this.alerts.push({
                    variant: 'warning',
                    message: 'Complete validation and growing stages before re-clustering this project.'
                });
                return;
            }

            this.selectedProject = project;
            this.showReclusteringModal = true;
        },

        handleRecluster(parameters) {
            if (!this.selectedProject) return;

            // Start re-clustering job
            api.reclusterProject(this.selectedProject.project_id, parameters)
                .then(response => {
                    this.alerts.push({
                        variant: 'success',
                        message: `Re-clustering job started for "${this.selectedProject.name}". Job ID: ${response.job_id}`
                    });
                    this.showReclusteringModal = false;
                    this.selectedProject = null;
                })
                .catch(error => {
                    console.error('Re-clustering failed:', error);
                    this.alerts.push({
                        variant: 'danger',
                        message: `Failed to start re-clustering: ${error.response?.data?.error || error.message}`
                    });
                });
        },

        handleReclusterCancel() {
            this.showReclusteringModal = false;
            this.selectedProject = null;
        },

        isProjectReadyForReclustering(project) {
            // Project is ready for re-clustering when both validation and growing are complete
            if (!project.progress) return false;

            const progress = project.progress;
            const totalNodes = progress.leaves_n_nodes || 0;
            const approvedNodes = progress.leaves_n_approved_nodes || 0;
            const filledNodes = progress.leaves_n_filled_nodes || 0;

            // Both validation and growing must be complete
            return totalNodes > 0 && approvedNodes === totalNodes && filledNodes === totalNodes;
        },

        getReclusterTooltip(project) {
            if (!project.progress) {
                return 'No progress information available';
            }

            const progress = project.progress;
            const totalNodes = progress.leaves_n_nodes || 0;
            const approvedNodes = progress.leaves_n_approved_nodes || 0;
            const filledNodes = progress.leaves_n_filled_nodes || 0;

            if (totalNodes === 0) {
                return 'Project has no clusters to re-cluster';
            }

            const validationComplete = approvedNodes === totalNodes;
            const growingComplete = filledNodes === totalNodes;

            if (validationComplete && growingComplete) {
                return 'Ready for re-clustering - validation and growing are complete';
            }

            const missing = [];
            if (!validationComplete) {
                missing.push(`validation (${approvedNodes}/${totalNodes} clusters validated)`);
            }
            if (!growingComplete) {
                missing.push(`growing (${filledNodes}/${totalNodes} clusters grown)`);
            }

            return `Complete ${missing.join(' and ')} before re-clustering`;
        },
    },
    mounted() {
        // Load node info
        api.getProjects()
            .then((projects) => {
                this.projects = projects;

                return Promise.all(
                    this.projects.map((p) => {
                        return api
                            .getNodeProgress(p.node_id)
                            .then((progress) => {
                                console.log(`Got progress for ${p.node_id}.`);
                                p.progress = progress;
                            });
                    })
                );
            })
            .catch((e) => {
                console.log(e);
                // TODO: Use axiosErrorHandler
                this.alerts.unshift({
                    message: e.message,
                    variant: "danger",
                });
            });
    },
};
</script>

<style>
#projects {
    display: flex;
    flex-direction: column;
    align-items: stretch;
    flex: 1;
    overflow: hidden;
}

#projects_table,
#projects_table.table {
    background-color: var(--table-bg) !important;
    color: var(--text-primary) !important;
}

#projects_table tr td:nth-child(1) {
    width: 100%;
}

#projects_table tr td:not(:nth-child(1)) {
    width: auto;
    text-align: right;
    white-space: nowrap;
}

#projects_table thead,
#projects_table thead th {
    background-color: var(--bg-secondary) !important;
    color: var(--text-primary) !important;
    border-color: var(--border-color) !important;
}

#projects_table tbody,
#projects_table tbody tr,
#projects_table.table-striped tbody tr {
    background-color: var(--table-bg) !important;
    color: var(--text-primary) !important;
    border-color: var(--border-color) !important;
}

#projects_table tbody tr:nth-of-type(odd),
#projects_table.table-striped tbody tr:nth-of-type(odd) {
    background-color: var(--bg-secondary) !important;
}

#projects_table tbody tr:hover,
#projects_table.table-hover tbody tr:hover {
    background-color: var(--table-hover-bg) !important;
}

#projects_table tbody tr td,
#projects_table tbody td {
    border-color: var(--border-color) !important;
    color: var(--text-primary) !important;
    background-color: transparent !important;
}

#projects_table a {
    color: var(--text-primary) !important;
}

:root.dark-mode #projects_table a {
    color: #5cb3ff !important;
}

:root.dark-mode #projects_table a:hover {
    color: #8dc9ff !important;
}

.scrollable {
    overflow-y: auto;
}

.alerts {
    padding-top: 1em;
}

/* Override Bootstrap button styles in dark mode */
:root.dark-mode #projects_table .btn-primary {
    background-color: #0d6efd !important;
    border-color: #0d6efd !important;
    color: #ffffff !important;
}

:root.dark-mode #projects_table .btn-info {
    background-color: #0dcaf0 !important;
    border-color: #0dcaf0 !important;
    color: #000000 !important;
}

:root.dark-mode #projects_table .btn-secondary {
    background-color: #6c757d !important;
    border-color: #6c757d !important;
    color: #ffffff !important;
}
</style>
