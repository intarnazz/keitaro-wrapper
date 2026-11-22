<script setup lang="ts">
import { useTemplateRef } from 'vue'
import type { Stream } from '@/api/api'
import OfferPicker from '@/components/editor/OfferPicker.vue'
import OfferRow from '@/components/editor/OfferRow.vue'
import UiAlert from '@/components/ui/UiAlert.vue'
import UiButton from '@/components/ui/UiButton.vue'

const props = defineProps<{ stream: Stream }>()

const picker = useTemplateRef('picker')

const add = async (offer_id: number) => {
  if (await props.stream.add_offer(offer_id)) picker.value?.clear()
}
</script>

<template>
  <section class="card" :class="{ card_dirty: stream.dirty, card_muted: !stream.is_editable }">
    <div class="flex items-center justify-between gap-3 flex-wrap">
      <div class="min-w-0">
        <div class="font-medium truncate">{{ stream.name }}</div>
        <div class="text-xs text-gray-500">Stream #{{ stream.keitaro_stream_id }}</div>
      </div>
      <div v-if="stream.dirty" class="badge">Not published</div>
    </div>

    <p v-if="!stream.is_editable" class="text-sm text-gray-500 mt-2">
      No offers in this stream, so there is nothing to edit.
    </p>

    <template v-else>
      <div class="mt-3">
        <OfferRow v-for="offer in stream.offers" :key="offer.offer_id" :stream="stream" :offer="offer" />
      </div>

      <div class="flex justify-end text-sm mt-1" :class="stream.is_balanced ? 'text-gray-500' : 'text-red-600'">
        Total: {{ stream.total_share }}%
      </div>

      <div class="mt-3">
        <OfferPicker
          ref="picker"
          :taken="stream.active_offers.map((o) => o.offer_id)"
          :disabled="stream.is_loading"
          @add="add"
        />
      </div>

      <UiAlert v-if="stream.error" class="mt-3">{{ stream.error }}</UiAlert>

      <div class="flex justify-end gap-2 mt-4">
        <UiButton variant="secondary" :disabled="!stream.dirty || stream.is_loading" @click="stream.cancel()">
          Cancel
        </UiButton>
        <UiButton
          :disabled="!stream.dirty || !stream.is_balanced || stream.is_loading"
          @click="stream.push()"
        >
          Push to Keitaro
        </UiButton>
      </div>
    </template>
  </section>
</template>

<style lang="sass" scoped>
.card
  padding: 1.25rem
  border-radius: 12px
  background: $w
  box-shadow: 0 0 0 1px #e2e8f0
  transition: background-color .2s, box-shadow .2s
  &_dirty
    background: #fffbea
    box-shadow: 0 0 0 1px #f5c542
  &_muted
    background: $sub-95
.badge
  padding: .15rem .6rem
  border-radius: 999px
  background: #f5c542
  color: #5c4500
  font-size: .75rem
  font-weight: 500
</style>
