<script setup lang="ts">
withDefaults(
  defineProps<{
    intent?: 'primary' | 'neutral'
    emphasis?: 'solid' | 'outline' | 'ghost'
    busy?: boolean
    disabled?: boolean
    type?: 'button' | 'submit' | 'reset'
  }>(),
  {
    intent: 'neutral',
    emphasis: 'outline',
    busy: false,
    disabled: false,
    type: 'button',
  },
)
</script>

<template>
  <button
    class="app-button"
    :class="[`app-button--${intent}`, `app-button--${emphasis}`]"
    :type="type"
    :disabled="disabled || busy"
    :aria-busy="busy"
  >
    <slot />
  </button>
</template>
