<script setup lang="ts">
import { computed, ref } from 'vue'
import { campaigns } from '@/api/api'
import UiAlert from '@/components/ui/UiAlert.vue'
import UiButton from '@/components/ui/UiButton.vue'
import UiInput from '@/components/ui/UiInput.vue'
import LayoutPage from '@/layout/LayoutPage.vue'
import LayoutWrapper from '@/layout/LayoutWrapper.vue'

const filter = ref('')

const filtered = computed(() => {
  const q = filter.value.trim().toLowerCase()
  const list = campaigns.list ?? []
  if (!q) return list
  return list.filter((c) => String(c.id) === q || (c.name ?? '').toLowerCase().includes(q))
})
</script>

<template>
  <LayoutPage>
    <LayoutWrapper>
      <div class="flex items-end justify-between gap-4 mb-4 max-sm:flex-col max-sm:items-stretch">
        <h1 class="text-2xl">Campaigns</h1>
        <div class="flex items-end gap-2">
          <UiInput v-model="filter" placeholder="Search by name or ID" size="sm" />
          <UiButton variant="secondary" :disabled="campaigns.is_loading" @click="campaigns.reload()">
            Refresh
          </UiButton>
        </div>
      </div>

      <UiAlert v-if="campaigns.error">{{ campaigns.error }}</UiAlert>
      <div v-else-if="campaigns.list === null" class="text-gray-500">Loading…</div>
      <div v-else-if="filtered.length === 0" class="text-gray-500">No campaigns found.</div>

      <div v-else class="rounded-xl ring-1 ring-slate-200 bg-white overflow-hidden">
        <RouterLink
          v-for="campaign in filtered"
          :key="campaign.id"
          :to="{ name: 'editor', params: { id: campaign.id } }"
          class="campaign-row"
        >
          <div class="text-gray-500 w-20">#{{ campaign.id }}</div>
          <div class="flex-1 min-w-0 truncate">{{ campaign.name }}</div>
          <div class="text-gray-500 max-sm:hidden">{{ campaign.alias }}</div>
          <div class="text-sm text-gray-500 w-16 text-right">{{ campaign.state }}</div>
        </RouterLink>
      </div>
    </LayoutWrapper>
  </LayoutPage>
</template>

<style lang="sass" scoped>
.campaign-row
  display: flex
  align-items: center
  gap: 1rem
  padding: .85rem 1.25rem
  color: $b
  & + &
    box-shadow: 0 -1px 0 $sub-90
  &:hover
    background: $sub-95
</style>
