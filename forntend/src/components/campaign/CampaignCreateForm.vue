<script setup lang="ts">
import { computed } from 'vue'
import { CampaignForm, directory } from '@/api/api'
import UiAlert from '@/components/ui/UiAlert.vue'
import OfferSelect from '@/components/ui/OfferSelect.vue'
import UiButton from '@/components/ui/UiButton.vue'
import UiInput from '@/components/ui/UiInput.vue'
import UiSelect from '@/components/ui/UiSelect.vue'

const form = new CampaignForm()

const option_list = (items: typeof directory.domains) =>
  items?.map((i) => ({ value: i.id, label: i.name })) ?? null

const domains = computed(() => option_list(directory.domains))
const groups = computed(() => option_list(directory.groups))
const traffic_sources = computed(() => option_list(directory.traffic_sources))
</script>

<template>
  <form class="flex flex-col gap-5" @submit.prevent="form.submit()">
    <h1 class="text-2xl">New campaign</h1>

    <UiInput v-model="form.name" label="Name" placeholder="My campaign" :error="form.field_error('name')" />

    <div class="grid grid-cols-2 gap-4 max-sm:grid-cols-1">
      <UiInput
        v-model="form.geo"
        label="Geo"
        placeholder="AU"
        :maxlength="2"
        :error="form.field_error('geo')"
      />
      <OfferSelect v-model="form.offer_id" label="Offer" :error="form.field_error('offer_id')" />
    </div>

    <details class="advanced">
      <summary class="cursor-pointer text-sm text-gray-500">Domain, group and traffic source</summary>
      <div class="grid grid-cols-3 gap-4 mt-3 max-sm:grid-cols-1">
        <UiSelect v-model="form.domain_id" label="Domain" :options="domains" />
        <UiSelect v-model="form.group_id" label="Group" :options="groups" />
        <UiSelect v-model="form.traffic_source_id" label="Traffic source" :options="traffic_sources" />
      </div>
      <p class="text-xs text-gray-500 mt-2">The first active item of each list is used by default.</p>
    </details>

    <UiAlert v-if="form.error">{{ form.error }}</UiAlert>

    <UiAlert v-if="form.result" type="success">
      <div>Campaign created: ID {{ form.result.campaign_id }}, alias “{{ form.result.alias }}”.</div>
      <div class="mt-1">Streams: {{ form.result.streams.join(', ') }}.</div>
      <RouterLink
        :to="{ name: 'editor', params: { id: form.result.campaign_id } }"
        class="underline mt-2 inline-block"
      >
        Open in editor →
      </RouterLink>
    </UiAlert>

    <div>
      <UiButton type="submit" :disabled="form.is_loading">
        {{ form.is_loading ? 'Creating…' : 'Create' }}
      </UiButton>
    </div>
  </form>
</template>
