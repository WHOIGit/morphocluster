<template>
    <div>Dummy</div>
</template>

<script>
export default {
    name: "dummy-component",
    mounted () {
        console.log("mounted dummy-component");
    },
    created () {
        console.log("created dummy-component");
    },
    inistialized () {
        console.log("inistialized dummy-component");
    },
    updated () {
        console.log("updated dummy-component");
    },
    activated () {
        console.log("activated dummy-component");
    },
    unmounted () {
        console.log("unmounted dummy-component");
    },
}
</script>
