<script setup>
import TTSGenerator from './TTSGenerator.vue'
</script>

<template>
  <div id="app">
    <TTSGenerator />
  </div>
</template>

<style>
#app {
  width: 100%;
  min-height: 100vh;
  background-color: var(--ctp-base);
}

body {
  margin: 0;
  padding: 0;
  background-color: var(--ctp-base);
}
</style>
