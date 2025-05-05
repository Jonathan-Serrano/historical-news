<template>
  <header class="fixed top-0 left-0 w-full bg-white shadow z-10">
    <div class="flex flex-row justify-between px-10 py-3">
      <h1 class="text-2xl font-bold text-text-primary">News Catcher</h1>
      <section class="flex flex-row items-center gap-4">
        <h3 class="text-lg font-semibold">Today</h3>
        <DatePicker
          v-model="currentDate"
          dateFormat="mm/dd/yy"
          class="w-full"
          showButtonBar
        />
      </section>
    </div>
  </header>
</template>

<script setup lang="ts">
import DatePicker from 'primevue/datepicker';
import { useCurrentDate } from '../composables/useDate';
const { currentDate } = useCurrentDate();
</script>