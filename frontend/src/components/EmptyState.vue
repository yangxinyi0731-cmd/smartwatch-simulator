<script setup lang="ts">
defineProps<{
  title: string
  description: string
}>()
</script>

<template>
  <div class="empty-state" role="status">
    <span class="empty-state__icon" aria-hidden="true">
      <slot name="icon" />
    </span>
    <div>
      <h3>{{ title }}</h3>
      <p>{{ description }}</p>
      <slot />
    </div>
  </div>
</template>
