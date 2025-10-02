<template>
    <div id="files">
        <nav class="navbar navbar-expand-lg navbar navbar-dark bg-dark">
            <router-link class="navbar-brand" :to="{ name: 'projects' }">
                <img src="/frontend/favicon.png" alt="MorphoCluster" class="navbar-logo" />
                MorphoCluster
            </router-link>
            <div class="navbar-collapse" id="navbarNav">
                <ul class="navbar-nav me-auto">
                    <li class="navbar-item">
                        <router-link class="nav-link" :to="{ name: 'projects' }">Projects</router-link>
                    </li>
                    <li class="navbar-item">
                        <span class="nav-link active">Files</span>
                    </li>
                    <li class="navbar-item">
                        <router-link class="nav-link" :to="{ name: 'upload' }">Upload</router-link>
                    </li>
                    <li class="navbar-item">
                        <router-link class="nav-link" :to="{ name: 'jobs' }">Jobs</router-link>
                    </li>
                    <li v-for="(parent, index) in entry && entry.parents ? entry.parents.slice() : []" :key="index" class="navbar-item">
                        <router-link class="nav-link" :to="{ name: 'files', params: { file_path: parent.path } }">{{
                            parent.name
                        }}</router-link>
                    </li>
                    <li class="navbar-item" v-if="entry && entry.name != '.'">
                        <span class="nav-link">{{ entry.name }}</span>
                    </li>
                </ul>
            </div>
            <dark-mode-control />
        </nav>
        <div class="scrollable">
            <div class="container" v-if="entry && entry.type === 'directory'">
                <div class="alerts" v-if="alerts.length">
                    <b-alert :key="a" v-for="a of alerts" dismissible show :variant="a.variant">
                        {{ a.message }}
                    </b-alert>
                </div>
                <b-table id="files_table" striped :items="entry.children || []" :fields="fields" showEmpty>
                    <template v-slot:cell(name)="child">
                        <router-link v-if="child.item.type === 'directory'" :to="{
                            name: 'files',
                            params: { file_path: child.item.path },
                        }"><i class="mdi mdi-folder" /> {{ child.item.name }}</router-link>
                        <router-link v-if="child.item.type === 'file'" :to="{
                            name: 'files',
                            params: { file_path: child.item.path },
                        }"><i class="mdi mdi-file" /> {{ child.item.name }} </router-link>
                    </template>
                </b-table>
            </div>
            <div class="container" v-if="entry && entry.type === 'file'">
                <!--TODO: Convert to regular table and select and format properties by hand. -->
                <table id="table" style="width=100%">
                    <tr>
                        <td style="padding-right: 20px;">Name:</td>
                        <td>{{ entry.name }}</td>
                    </tr>
                    <tr>
                        <td style="padding-right: 20px;">Created On:</td>
                        <td>{{ entry.last_modified }}</td>
                    </tr>
                </table>
                <div class=" d-flex justify-content-center">
                    <b-button size="sm" variant="primary" class="mx-2" @click.prevent="downloadFile">
                        Download
                    </b-button>
                    <b-button size="sm" variant="primary" class="mx-2">
                        Import as project
                    </b-button>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import "@mdi/font/css/materialdesignicons.css";
import * as api from "@/helpers/api.js";
// Bootstrap is already imported globally in main.js
import DarkModeControl from "@/components/DarkModeControl.vue";

export default {
    name: "FilesView",
    props: { file_path: String },
    response: "",
    components: { DarkModeControl },
    data() {
        return {
            fields: [
                { key: "name" },
                "last_modified",
            ],
            entry: null,
            alerts: [],
        };
    },
    created() {
        this.initialize();
    },
    watch: {
        $route: "initialize",
    },
    methods: {
        getBasename(path) {
            const parts = path.split('/');
            return parts[parts.length - 1];
        },
        async initialize() {
            try {
                this.entry = await api.getFileInfo(this.file_path);
            } catch (error) {
                console.error(error);
                this.alerts.unshift({
                    message: error.message,
                    variant: "danger",
                });
            }
        },
        downloadFile() {
            window.open(`/api/files/${this.entry.path}?download=1`);
        },
    },
};
</script>

<style>
#files {
    display: flex;
    flex-direction: column;
    align-items: stretch;
    flex: 1;
    overflow: hidden;
}

#files_table,
#files_table.table {
    background-color: var(--table-bg) !important;
    color: var(--text-primary) !important;
}

#files_table tr td:nth-child(1) {
    width: 100%;
}

#files_table tr td:not(:nth-child(1)) {
    width: auto;
    text-align: right;
    white-space: nowrap;
}

#files_table thead,
#files_table thead th {
    background-color: var(--bg-secondary) !important;
    color: var(--text-primary) !important;
    border-color: var(--border-color) !important;
}

#files_table tbody,
#files_table tbody tr,
#files_table.table-striped tbody tr {
    background-color: var(--table-bg) !important;
    color: var(--text-primary) !important;
    border-color: var(--border-color) !important;
}

#files_table tbody tr:nth-of-type(odd),
#files_table.table-striped tbody tr:nth-of-type(odd) {
    background-color: var(--bg-secondary) !important;
}

#files_table tbody tr:hover,
#files_table.table-hover tbody tr:hover {
    background-color: var(--table-hover-bg) !important;
}

#files_table tbody tr td,
#files_table tbody td {
    border-color: var(--border-color) !important;
    color: var(--text-primary) !important;
    background-color: transparent !important;
}

#files_table a {
    color: var(--text-primary) !important;
}

:root.dark-mode #files_table a {
    color: #5cb3ff !important;
}

:root.dark-mode #files_table a:hover {
    color: #8dc9ff !important;
}

.scrollable {
    overflow-y: auto;
}

.alerts {
    padding-top: 1em;
}

.dropzone {
    border: 2px dashed var(--border-color);
    background-color: var(--bg-secondary);
    padding: 20px;
    text-align: center;
    cursor: pointer;
    color: var(--text-secondary);
}
</style>