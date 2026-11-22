<script setup lang="ts">
withDefaults(
  defineProps<{
    variant?: 'primary' | 'secondary' | 'danger' | 'ghost'
    type?: 'button' | 'submit'
    disabled?: boolean
  }>(),
  { variant: 'primary', type: 'button', disabled: false },
)
</script>

<template>
  <button :type="type" :disabled="disabled" class="ui-button" :class="`ui-button_${variant}`">
    <slot />
  </button>
</template>

<style lang="sass" scoped>
.ui-button
  display: inline-flex
  align-items: center
  justify-content: center
  gap: .5rem
  padding: .5rem 1rem
  border-radius: 6px
  font-size: .875rem
  font-weight: 500
  white-space: nowrap
  transition: background-color .15s, color .15s, opacity .15s
  &:disabled
    opacity: .45
    cursor: not-allowed
  &_primary
    background: $main
    color: $w
    &:hover:not(:disabled)
      background: $second
  &_secondary
    background: $sub-95
    color: $b
    &:hover:not(:disabled)
      background: $sub-90
  &_danger
    background: transparent
    color: $red
    &:hover:not(:disabled)
      background: rgba(216, 12, 49, .08)
  &_ghost
    background: transparent
    color: $main
    &:hover:not(:disabled)
      background: $sub-95
</style>
