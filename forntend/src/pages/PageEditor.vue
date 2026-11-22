<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { campaigns } from '@/api/api'
import StreamCard from '@/components/editor/StreamCard.vue'
import UiAlert from '@/components/ui/UiAlert.vue'
import UiButton from '@/components/ui/UiButton.vue'
import LayoutPage from '@/layout/LayoutPage.vue'
import LayoutWrapper from '@/layout/LayoutWrapper.vue'

const route = useRoute()
const campaign = computed(() => campaigns.get(Number(route.params['id'])))
</script>

<template>
  <LayoutPage>
    <LayoutWrapper>
      <RouterLink :to="{ name: 'campaigns' }" class="text-sm text-gray-500">← All campaigns</RouterLink>

      <div class="flex items-end justify-between gap-4 mt-2 mb-5 flex-wrap">
        <div class="min-w-0">
          <h1 class="text-2xl truncate">{{ campaign.name ?? `Campaign #${campaign.id}` }}</h1>
          <div class="text-sm text-gray-500">
            #{{ campaign.id }}<template v-if="campaign.alias"> · {{ campaign.alias }}</template>
          </div>
        </div>
        <UiButton variant="secondary" :disabled="campaign.is_loading" @click="campaign.fetch_streams()">
          {{ campaign.is_loading ? 'Loading…' : 'Fetch streams' }}
        </UiButton>
      </div>

      <UiAlert v-if="campaign.error" class="mb-4">{{ campaign.error }}</UiAlert>

      <div v-if="campaign.streams === null" class="text-gray-500">Loading streams…</div>
      <div v-else-if="campaign.streams.length === 0" class="text-gray-500">
        This campaign has no streams.
      </div>
      <div v-else class="flex flex-col gap-4">
        <StreamCard v-for="stream in campaign.streams" :key="stream.id" :stream="stream" />
      </div>
    </LayoutWrapper>
  </LayoutPage>
</template>
