<script setup lang="ts">
import { computed, ref } from 'vue'
import { Offer, OfferSearch } from '@/api/api'
import UiButton from '@/components/ui/UiButton.vue'
import UiInput from '@/components/ui/UiInput.vue'

const props = defineProps<{
  /** ID офферов, которые уже активны в потоке */
  taken: number[]
  disabled: boolean
}>()

const emit = defineEmits<{ add: [offer_id: number] }>()

const search = new OfferSearch()
const selected = ref<Offer | null>(null)
const is_open = ref(false)

const options = computed(() => (search.results ?? []).filter((o) => !props.taken.includes(o.id)))

/** Выбранный оффер или ID, введённый вручную */
const offer_id = computed<number | null>(() => {
  if (selected.value) return selected.value.id
  const typed = search.query.trim()
  return /^[1-9]\d*$/.test(typed) ? Number(typed) : null
})

const select = (offer: Offer) => {
  selected.value = offer
  search.query = offer.label
  is_open.value = false
}

const on_input = () => {
  selected.value = null
  is_open.value = true
}

const add = () => {
  if (offer_id.value !== null) emit('add', offer_id.value)
}

/** Очищает выбор после добавления */
const clear = () => {
  selected.value = null
  search.query = ''
}

defineExpose({ clear })
</script>

<template>
  <div class="flex items-end gap-2">
    <div class="picker flex-1" @focusin="is_open = true" @input="on_input">
      <UiInput
        v-model="search.query"
        placeholder="Offer ID or name"
        size="sm"
        :error="search.error"
      />
      <div v-if="is_open && options.length > 0" class="picker__list">
        <div
          v-for="offer in options"
          :key="offer.id"
          class="picker__item"
          @mousedown.prevent="select(offer)"
        >
          {{ offer.label }}
        </div>
      </div>
    </div>
    <UiButton :disabled="disabled || offer_id === null" @click="add">Add offer</UiButton>
  </div>
</template>

<style lang="sass" scoped>
.picker
  position: relative
  &__list
    position: absolute
    z-index: 10
    top: 100%
    left: 0
    right: 0
    max-height: 14rem
    overflow-y: auto
    margin-top: .25rem
    background: $w
    border-radius: 6px
    box-shadow: 0 4px 16px rgba(0, 0, 0, .12)
  &__item
    padding: .5rem .75rem
    cursor: pointer
    &:hover
      background: $sub-95
</style>
