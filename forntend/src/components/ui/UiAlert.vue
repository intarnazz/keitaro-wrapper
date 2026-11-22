<script setup lang="ts">
withDefaults(defineProps<{ type?: 'error' | 'success' | 'info' }>(), { type: 'error' })
</script>

<template>
  <div class="ui-alert" :class="`ui-alert_${type}`" role="alert"><slot /></div>
</template>

<style lang="sass" scoped>
.ui-alert
  padding: .75rem 1rem
  border-radius: 6px
  font-size: .9rem
  &_error
    background: rgba(216, 12, 49, .08)
    color: #a30923
  &_success
    background: $successBg
    color: $successColor
  &_info
    background: $sub-95
    color: $b
</style>
