<template>
    <div id="labeling2">
        <h2 v-if="this.node">{{this.node.name}}</h2>
        <div id="node-info" class="scrollable">
            <node-header v-if="node" :node="node"/>

            <div class="row">
                <div v-for="m in node_members" class="col col-1" :key="getUniqueId(m)">
                    <member-preview
                        v-bind:member="m"
                        />
                </div>
            </div>
            <div ref="scrollTrigger" class="scroll-trigger">
                <div v-if="!allMembersLoaded" class="text-center my-3">
                    <div class="spinner-border" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import axios from "axios";

import MemberPreview from "@/components/MemberPreview.vue";
import NodeHeader from "@/components/NodeHeader.vue";

export default {
  name: "Labeling2View",
  props: {
    node_id: Number
  },
  components: {
    MemberPreview,
    NodeHeader
  },
  data() {
    return {
      node: null,
      node_members: [],
      message: null,
      members_url: null,
      page: null,
      allMembersLoaded: false
    };
  },
  methods: {
    setMessage: function(msg) {
      this.message = msg;
    },
    setupIntersectionObserver() {
      if (this.$refs.scrollTrigger) {
        this.observer = new IntersectionObserver((entries) => {
          const entry = entries[0];
          if (entry.isIntersecting && !this.allMembersLoaded) {
            this.loadMoreMembers();
          }
        }, { threshold: 0.1 });
        
        this.observer.observe(this.$refs.scrollTrigger);
      }
    },
    loadMoreMembers() {
      if (this.allMembersLoaded) return;
      
      const mockState = {
        loaded: () => {},
        complete: () => { this.allMembersLoaded = true; }
      };
      
      this.updateMembers(mockState);
    },
    updateMembers($state) {
      var updateMembersUrl = false;

      if (!this.members_url) {
        this.members_url = `/api/nodes/${
          this.node_id
        }/members?objects=true&arrange_by=interleaved`;
        this.page = 0;
        updateMembersUrl = true;
      } else {
        this.page += 1;
      }

      var url = `${this.members_url}&page=${this.page}`;

      console.log(`Loading ${url}...`);

      axios
        .get(`${this.members_url}&page=${this.page}`)
        .then(response => {
          this.node_members = this.node_members.concat(response.data.data);
          if (updateMembersUrl) {
            this.members_url = response.data.links.self;
            console.log(this.members_url);
          }

          $state.loaded();
          console.log("Done loading.");
        })
        .catch(e => {
          this.setMessage(e.message);
          console.log(e);
        });
    }
  },
  mounted() {
    // Load node info
    axios
      .get(`/api/nodes/${this.node_id}`)
      .then(response => {
        this.node = response.data;
        this.$nextTick(() => {
          this.setupIntersectionObserver();
        });
      })
      .catch(e => {
        this.setMessage(e.message);
        console.log(e);
      });
  },
  beforeDestroy() {
    if (this.observer) {
      this.observer.disconnect();
    }
  }
};
</script>

<style>
#labeling2 {
  display: flex;
  flex-direction: column;
  align-items: stretch;
  flex: 1;
  overflow: hidden;
}

#labeling2 > * {
  padding: 0 10px;
}

.scrollable {
  margin: 0;
  overflow-y: auto;
}

#node-members .col,
#recommended-members .col {
  padding: 0 5px;
}

#node-members {
  flex: 1;
}

#recommended-members,
#report {
  flex: 2;
}

#progress {
  display: flex;
  flex-wrap: nowrap;
  margin: 0.2em 0;
}

#progress div {
  height: 0.2em;
}

.section-heading {
  margin: 0.2em 0;
}
</style>
