<script setup lang="ts">
import LayoutWrapper from '@/layout/LayoutWrapper.vue'
</script>

<template>
  <header class="header">
    <LayoutWrapper>
      <div class="flex items-center justify-between h-14">
        <RouterLink :to="{ name: 'home' }" class="font-semibold text-lg">Keitaro wrapper</RouterLink>
        <nav class="flex gap-1">
          <RouterLink :to="{ name: 'home' }" class="header__link">New campaign</RouterLink>
          <RouterLink :to="{ name: 'campaigns' }" class="header__link">Campaign editor</RouterLink>
        </nav>
      </div>
    </LayoutWrapper>
  </header>
</template>

<style lang="sass" scoped>
.header
  background: $w
  box-shadow: 0 1px 0 $sub-90
  &__link
    padding: .4rem .8rem
    border-radius: 6px
    color: $sub
    &:hover
      background: $sub-95
    &.router-link-exact-active,
    &.router-link-active:not([href="/"])
      color: $main
      background: rgba(41, 141, 214, .1)
</style>
