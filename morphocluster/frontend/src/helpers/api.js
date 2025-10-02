import axios from "axios";

export function getNode(node_id) {
    return axios.get(`/api/nodes/${node_id}`)
        .then(response => {
            return response.data;
        });
}

export function patchNode(node_id, data) {
    return axios.patch(`/api/nodes/${node_id}`, data)
        .then(response => {
            return response.data;
        });
}

/**
 * Get the next unapproved node for a subtree rooted at node_id.
 *
 * @param params {leaf: bool}
 */
export function getNextUnapprovedNode(node_id, params = null) {
    return axios.get(`/api/nodes/${node_id}/next`, { params })
        .then(response => {
            return response.data;
        });
}

/**
 * Get the next unfilled node for a subtree rooted at node_id.
 *
 * @param params {leaf: bool, preferred_first: bool, order_by: string}
 */
export function getNextUnfilledNode(node_id, params = null) {
    return axios.get(`/api/nodes/${node_id}/next_unfilled`, { params })
        .then(response => {
            return response.data;
        });
}

/**
 * Get the sorting progress for a subtree rooted at node_id.
 *
 * @param params {log: string}
 */
export function getNodeProgress(node_id, params = null) {
    return axios.get(`/api/nodes/${node_id}/progress`, { params })
        .then(response => {
            return response.data;
        });
}

/**
 * Get recommended objects for node_id.
 *
 * @param params {max_n: int}
 */
export function getNodeRecommendedObjects(node_id, params = null) {
    return axios.get(`/api/nodes/${node_id}/recommended_objects`, { params })
        .then(response => {
            return response.data;
        });
}

export function mergeNodeInto(node_id, dest_node_id) {
    const data = { dest_node_id };
    console.log(data)
    return axios.post(`/api/nodes/${node_id}/merge_into`, data);
}

// Files
// TODO: Documentation
export function getDirEntry(file_path) {
    return axios.get(`/api/files/${file_path}?download=false&info=true`)
        .then(response => {
            return response.data;
        });
}

export function getFileInfo(file_path) {
    return axios.get(`/api/files/${file_path}?download=false&info=true`)
        .then(response => {
            return response.data;
        });
}

export function getFile(file_path) {
    return axios.get(`/api/files/${file_path}?download=true&info=false`)
        .then(response => {
            return response.data;
        });
}

export function uploadFiles(files, file_path) {
    return axios.post(`/api/files/${file_path}`, files)
        .then(response => { return response.data; });
}


// Project

export function getProjects(include_progress = false) {
    return axios.get(`/api/projects`, { params: { include_progress } })
        .then(response => {
            return response.data;
        });
}

export function getProject(project_id, include_progress = false) {
    return axios.get(`/api/projects/${project_id}`, { params: { include_progress } })
        .then(response => {
            return response.data;
        });
}

export function saveProject(project_id) {
    return axios.post(`/api/projects/${project_id}/save`)
        .then(response => {
            return response.data;
        });
}

export function nodeAdoptMembers(node_id, members) {
    if (!Array.isArray(members)) {
        members = [members];
    }

    return axios.post(`/api/nodes/${node_id}/adopt_members`, { members: members });
}

export function nodeAcceptRecommendations(node_id, request_id, rejected_members, last_page, log_data = null) {
    return axios.post(`/api/nodes/${node_id}/accept_recommended_objects`,
        { request_id, rejected_members, last_page, log_data });
}

export function getUnfilledNodes(project_id) {
    return axios.get(`/api/projects/${project_id}/unfilled_nodes`).then(response => {
        return response.data;
    });
}

export function log(action, node_id = null, reverse_action = null, data = null) {
    return axios.post(`/api/log`,
        { action, node_id, reverse_action, data });
}

// Upload and Processing Pipeline

export function uploadArchives(files) {
    const formData = new FormData();
    files.forEach(file => {
        formData.append('files', file);
    });
    return axios.post('/api/upload', formData, {
        headers: {
            'Content-Type': 'multipart/form-data',
        },
    }).then(response => response.data);
}

export function validateArchive(fileName) {
    return axios.get(`/api/files/${fileName}/validate`)
        .then(response => response.data);
}

export function previewArchive(fileName) {
    return axios.get(`/api/files/${fileName}/preview`)
        .then(response => response.data);
}

export function convertEcoTaxaFormat(fileName, parameters) {
    return axios.post(`/api/files/${fileName}/convert`, parameters)
        .then(response => response.data);
}

export function extractFeatures(fileName, parameters) {
    return axios.post(`/api/files/${fileName}/extract`, parameters)
        .then(response => response.data);
}

export function createProjectFromFeatures(featuresId, parameters) {
    return axios.post(`/api/features/${featuresId}/cluster`, parameters)
        .then(response => response.data);
}

export function reclusterProject(projectId, parameters) {
    return axios.post(`/api/projects/${projectId}/recluster`, parameters)
        .then(response => response.data);
}

// Job Management

export function getUserJobs() {
    return axios.get('/api/jobs/user')
        .then(response => response.data);
}

export function getJobStatus(jobId) {
    return axios.get(`/api/jobs/${jobId}/status`)
        .then(response => response.data);
}

export function cancelJob(jobId) {
    return axios.delete(`/api/jobs/${jobId}`)
        .then(response => response.data);
}

// ===============================================================================
// Uploaded Archives Management
// ===============================================================================

export function getUploadedArchives() {
    return axios.get('/api/uploaded-archives')
        .then(response => response.data);
}

export function saveUploadedArchive(archiveData) {
    return axios.post('/api/uploaded-archives', archiveData)
        .then(response => response.data);
}

export function updateUploadedArchive(archiveId, updates) {
    return axios.put(`/api/uploaded-archives/${archiveId}`, updates)
        .then(response => response.data);
}