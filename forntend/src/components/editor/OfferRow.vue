<script setup lang="ts">
import { ref, watch } from 'vue'
import type { Stream, StreamOffer } from '@/api/api'
import UiButton from '@/components/ui/UiButton.vue'
import UiInput from '@/components/ui/UiInput.vue'

const props = defineProps<{ stream: Stream; offer: StreamOffer }>()

// Поле доли: ввод нового значения закрепляет оффер с этой долей
const share_text = ref(String(props.offer.share))
watch(
  () => props.offer.share,
  (share) => (share_text.value = String(share)),
)

const commit_share = () => {
  const value = Number(share_text.value)
  if (Number.isInteger(value) && value >= 1 && value <= 100 && value !== props.offer.share) {
    void props.stream.pin_offer(props.offer, true, value)
  } else {
    share_text.value = String(props.offer.share)
  }
}
</script>

<template>
  <div class="row" :class="{ row_removed: offer.is_removed }">
    <div class="min-w-0 flex-1">
      <div class="truncate" :class="{ 'line-through': offer.is_removed }">{{ offer.title }}</div>
      <div class="text-xs text-gray-500">
        #{{ offer.offer_id }}
        <span v-if="offer.is_new" class="text-amber-600">· new</span>
        <span v-else-if="offer.is_removed && !offer.changed">· removed</span>
        <span v-else-if="offer.is_removed">· will be removed</span>
        <span v-else-if="offer.changed" class="text-amber-600">· changed</span>
      </div>
    </div>

    <div v-if="offer.is_removed" class="w-24 text-right text-gray-500">0%</div>
    <div v-else class="w-24 flex items-center gap-1">
      <UiInput
        v-model="share_text"
        size="sm"
        inputmode="numeric"
        :maxlength="3"
        @change="commit_share"
        @keyup.enter="commit_share"
      />
      <span class="text-gray-500">%</span>
    </div>

    <div class="flex gap-1 w-48 justify-end">
      <template v-if="offer.is_removed">
        <UiButton variant="secondary" :disabled="stream.is_loading" @click="stream.restore_offer(offer)">
          Bring back
        </UiButton>
      </template>
      <template v-else>
        <UiButton
          :variant="offer.pinned ? 'primary' : 'ghost'"
          :disabled="stream.is_loading"
          @click="stream.pin_offer(offer, !offer.pinned)"
        >
          {{ offer.pinned ? 'Pinned' : 'Pin' }}
        </UiButton>
        <UiButton variant="danger" :disabled="stream.is_loading" @click="stream.remove_offer(offer)">
          Remove
        </UiButton>
      </template>
    </div>
  </div>
</template>

<style lang="sass" scoped>
.row
  display: flex
  align-items: center
  gap: 1rem
  padding: .6rem 0
  & + &
    box-shadow: 0 -1px 0 $sub-90
  &_removed
    opacity: .55
@media screen and (max-width: 640px)
  .row
    flex-wrap: wrap
</style>
