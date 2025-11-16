<script lang="ts" setup>
import { useColorMode } from '@vueuse/core'
import { RouterView } from 'vue-router'

useColorMode({ initialValue: 'light' })
</script>
<template>
  <RouterView />
</template>
