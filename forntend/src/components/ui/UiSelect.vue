<script setup lang="ts">
const model = defineModel<number | null>({ required: true })

withDefaults(
  defineProps<{
    label?: string
    options: { value: number; label: string }[] | null
  }>(),
  { label: '' },
)
</script>

<template>
  <label class="ui-select">
    <span v-if="label" class="ui-select__label">{{ label }}</span>
    <select v-model="model" class="ui-select__field" :disabled="!options">
      <option v-if="!options" :value="null">Loading…</option>
      <option v-for="option in options" :key="option.value" :value="option.value">
        {{ option.label }}
      </option>
    </select>
  </label>
</template>

<style lang="sass" scoped>
.ui-select
  display: flex
  flex-direction: column
  gap: .25rem
  &__label
    font-size: .875rem
    color: $sub
  &__field
    width: 100%
    padding: .6rem 2.25rem .6rem .75rem
    border: 1px solid $sub-90
    border-radius: 6px
    background-color: $w
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 12 8' fill='none' stroke='%23808080' stroke-width='1.5'%3E%3Cpath d='M1 1.5l5 5 5-5'/%3E%3C/svg%3E")
    background-repeat: no-repeat
    background-position: right .75rem center
    background-size: .7rem
    &:focus
      border-color: $main
      box-shadow: 0 0 0 3px rgba(41, 141, 214, .15)
</style>
