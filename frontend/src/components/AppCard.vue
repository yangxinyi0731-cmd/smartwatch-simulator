<script setup lang="ts">
withDefaults(
  defineProps<{
    as?: string
  }>(),
  {
    as: 'section',
  },
)
</script>

<template>
  <component :is="as" class="card app-card">
    <header v-if="$slots.header" class="card-header app-card__header">
      <slot name="header" />
    </header>
    <div class="card-body app-card__body">
      <slot />
    </div>
  </component>
</template>
