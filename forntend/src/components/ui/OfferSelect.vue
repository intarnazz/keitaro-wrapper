<script setup lang="ts">
import { computed, ref, shallowRef, watch } from 'vue'
import { Offer, OfferSearch } from '@/api/api'

const model = defineModel<number | null>({ required: true })

withDefaults(defineProps<{ label?: string; error?: string | null }>(), { label: '', error: null })

// В выпадающем списке показываем до 50 офферов, остальные находятся поиском
const search = new OfferSearch(50)
const selected = shallowRef<Offer | null>(null)
const is_open = ref(false)

// Сброс значения снаружи (например, после создания кампании) очищает выбор
watch(model, (id) => {
  if (id === null) selected.value = null
})

/** В закрытом состоянии показываем выбранный оффер, в открытом строку поиска */
const shown = computed(() => (is_open.value ? search.query : (selected.value?.label ?? '')))

const open = () => {
  is_open.value = true
  if (search.query) search.query = ''
}

const on_input = (event: Event) => {
  is_open.value = true
  search.query = (event.target as HTMLInputElement).value
}

const pick = (offer: Offer) => {
  selected.value = offer
  model.value = offer.id
  is_open.value = false
}
</script>

<template>
  <div class="offer-select" :class="{ 'offer-select_error': error }">
    <label>
      <span v-if="label" class="offer-select__label">{{ label }}</span>
      <input
        class="offer-select__field"
        :value="shown"
        placeholder="Select an offer"
        autocomplete="off"
        @focus="open"
        @click="open"
        @input="on_input"
        @blur="is_open = false"
        @keydown.esc="is_open = false"
      />
    </label>

    <div v-if="is_open" class="offer-select__list">
      <div v-if="search.error" class="offer-select__hint">{{ search.error }}</div>
      <div v-else-if="search.results === null" class="offer-select__hint">Loading…</div>
      <div v-else-if="search.results.length === 0" class="offer-select__hint">No offers found</div>
      <div
        v-for="offer in search.results ?? []"
        :key="offer.id"
        class="offer-select__item"
        :class="{ 'offer-select__item_active': offer.id === model }"
        @mousedown.prevent="pick(offer)"
      >
        {{ offer.label }}
      </div>
    </div>

    <span v-if="error" class="offer-select__error-text">{{ error }}</span>
  </div>
</template>

<style lang="sass" scoped>
.offer-select
  position: relative
  display: flex
  flex-direction: column
  gap: .25rem
  &__label
    display: block
    margin-bottom: .25rem
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
    cursor: pointer
    &:focus
      border-color: $main
      box-shadow: 0 0 0 3px rgba(41, 141, 214, .15)
  &_error &__field
    border-color: $red
  &__list
    position: absolute
    z-index: 10
    top: 100%
    left: 0
    right: 0
    max-height: 16rem
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
    &_active
      background: rgba(41, 141, 214, .1)
  &__hint
    padding: .5rem .75rem
    color: $sub
    font-size: .875rem
  &__error-text
    font-size: .8rem
    color: $red
</style>
