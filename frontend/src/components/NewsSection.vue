<template>
  <section class="bg-card p-4 rounded shadow mt-20">
    <h2 class="text-xl font-bold mb-4 text-text-primary">Welcome, {{ user.name }}!</h2>
    <Menubar :model="menuItems" class="mb-4" />
    <section class="mb-6">
      <h3 class="text-lg font-semibold mb-2">While you were away ...</h3>
      <p class="mb-2">{{ user.name }} understands {{ currentTopic }} at level {{ currentLevel }}</p>
      <p class="mb-4">{{ summary }}</p>
      <Accordion :activeIndex="0">
        <AccordionTab v-for="(newsItem, index) in news" :key="index" :header="newsItem.title">
          <p>{{ newsItem.summary }}</p>
          <Button icon="pi pi-external-link" label="Read more" @click="goToArticle(newsItem.url)" class="mt-2" />
        </AccordionTab>
      </Accordion>
    </section>
    <section>
      <h3 class="text-lg font-semibold mb-2">Since you are unfamiliar with this topic</h3>
      <p class="mb-4">{{ historicalSummary }}</p>
      <Accordion :activeIndex="0">
        <AccordionTab v-for="(newsItem, index) in historicalNews" :key="index" :header="newsItem.title">
          <p>{{ newsItem.summary }}</p>
          <Button icon="pi pi-external-link" label="Read more" @click="goToArticle(newsItem.url)" class="mt-2" />
        </AccordionTab>
      </Accordion>
      <div class="mt-4 flex flex-wrap gap-2">
        <Button
          v-for="(topic, index) in suggestedTopics"
          :key="index"
          :label="topic"
          @click="confirmAddTopic(topic)"
        />
      </div>
    </section>
    <ConfirmPopup />
  </section>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { user } from '../data/user';
import { news, historicalNews, summary, historicalSummary, suggestedTopics } from '../data/news';
import Menubar from 'primevue/menubar';
import Accordion from 'primevue/accordion';
import AccordionTab from 'primevue/accordiontab';
import Button from 'primevue/button';
import ConfirmPopup from 'primevue/confirmpopup';
import { useConfirm } from 'primevue/useconfirm';

const currentTopic = ref(user.interests[0]?.topic || 'General');
const currentLevel = ref(user.interests[0]?.level || 'Beginner');

const menuItems = user.interests.map((interest) => ({
  label: interest.topic,
}));

const confirm = useConfirm();

function goToArticle(url: string) {
  window.open(url, '_blank');
}

function confirmAddTopic(topic: string) {
  confirm.require({
    message: `Do you want to add ${topic} to your interests?`,
    header: 'Confirmation',
    icon: 'pi pi-exclamation-triangle',
    accept: () => {
      user.interests.push({ topic, level: 'Beginner' });
    },
  });
}
</script>
