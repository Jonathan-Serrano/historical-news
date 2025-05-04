<template>
  <div class="min-h-screen bg-body">
    <Header />
    <main class="flex flex-col md:flex-row p-4 gap-4">
      <UserInfo class="md:w-1/3" />
      <NewsSection class="md:w-2/3" />
    </main>
  </div>
</template>

<script setup lang="ts">
import Header from './components/Header.vue';
import UserInfo from './components/UserInfo.vue';
import NewsSection from './components/NewsSection.vue';
</script>
