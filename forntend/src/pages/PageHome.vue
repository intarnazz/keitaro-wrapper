<script setup lang="ts">
import CampaignCreateForm from '@/components/campaign/CampaignCreateForm.vue'
import LayoutPage from '@/layout/LayoutPage.vue'
import LayoutWrapper from '@/layout/LayoutWrapper.vue'
</script>

<template>
  <LayoutPage>
    <LayoutWrapper>
      <div class="max-w-xl mx-auto p-6 rounded-xl ring-1 ring-slate-200 bg-white">
        <CampaignCreateForm />
      </div>
    </LayoutWrapper>
  </LayoutPage>
</template>
