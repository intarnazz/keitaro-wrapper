<script setup lang="ts">
/**
 * Компонент MainWrapper
 *
 * Обертка для основного контента страницы.
 * Проверяет наличие токена в sessionStorage и хранит его локально.
 * Содержимое компонента вставляется через слот.
 */
import IconUp from '@/components/icons/IconUp.vue'

// onMounted(() => {
//   up_fast()
// })

// watch(
//   () => route.params.id,
//   () => {
//     up_fast()
//   },
// )
</script>

<template>
  <!-- Основной контейнер страницы -->
  <main class="main gap4 box-y flex">
    <IconUp />
    <!-- Слот для вставки дочернего контента -->
    <slot />
  </main>
</template>

<style lang="sass" scoped>
.main
  justify-content: flex-start
  align-items: center
  padding: 2rem 0
  min-height: 94.2vh
</style>
