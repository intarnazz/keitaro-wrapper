<script setup lang="ts">
const model = defineModel<string>({ required: true })

withDefaults(
  defineProps<{
    label?: string
    error?: string | null
    placeholder?: string
    inputmode?: 'text' | 'numeric'
    maxlength?: number
    size?: 'md' | 'sm'
  }>(),
  { label: '', error: null, placeholder: '', inputmode: 'text', maxlength: 255, size: 'md' },
)
</script>

<template>
  <label class="ui-input" :class="[`ui-input_${size}`, { 'ui-input_error': error }]">
    <span v-if="label" class="ui-input__label">{{ label }}</span>
    <input
      v-model="model"
      class="ui-input__field"
      :placeholder="placeholder"
      :inputmode="inputmode"
      :maxlength="maxlength"
      autocomplete="off"
    />
    <span v-if="error" class="ui-input__error">{{ error }}</span>
  </label>
</template>

<style lang="sass" scoped>
.ui-input
  display: flex
  flex-direction: column
  gap: .25rem
  &__label
    font-size: .875rem
    color: $sub
  &__field
    width: 100%
    padding: .6rem .75rem
    border: 1px solid $sub-90
    border-radius: 6px
    background: $w
    transition: border-color .15s, box-shadow .15s
    &:focus
      border-color: $main
      box-shadow: 0 0 0 3px rgba(41, 141, 214, .15)
  &_sm &__field
    padding: .3rem .5rem
    font-size: .875rem
  &__error
    font-size: .8rem
    color: $red
  &_error &__field
    border-color: $red
</style>
