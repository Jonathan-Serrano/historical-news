<template>
  <Accordion :activeIndex="null">
    <AccordionTab :header="newsItem.title">
      <p class="text-text-secondary">{{ newsItem.summary }}</p>
      <Button
        icon="pi pi-external-link"
        label="Read More"
        @click="goToArticle(newsItem.url)"
        class="mt-2"
      />
    </AccordionTab>
  </Accordion>
</template>

<script setup lang="ts">
import { defineProps } from 'vue';
import Button from 'primevue/button';
import Accordion from 'primevue/accordion';
import AccordionTab from 'primevue/accordiontab';

const props = defineProps({
  newsItem: {
    type: Object,
    required: true,
  },
});

function goToArticle(url: string) {
  window.open(url, '_blank');
}
</script>
