<template>
  <section class="bg-card p-4 rounded shadow mt-20">
    <h2 class="text-xl font-bold mb-4 text-text-primary">Welcome, {{ user.name }}!</h2>
    <Menubar :model="menuItems" class="mb-4" />
    <section class="mb-6" v-if="currentInterest.topic">
      <h3 class="text-lg font-semibold mb-2">While you were away ...</h3>
      <Message severity="info" class="mb-2">{{ user.name }} understands {{ currentInterest.topic }} at level {{ currentInterest.level }}</Message>
      <p class="mb-4">{{ summary }}</p>
      <template v-if="isLoading">
        <div class="flex justify-center items-center">
          <i class="pi pi-spin pi-spinner text-2xl"></i>
        </div>
      </template>
      <Accordion :activeIndex="0">
        <AccordionTab v-for="(newsItem, index) in news" :key="index" :header="newsItem.title">
            <p v-if="!isLoading">{{ newsItem.summary }}</p>
            <i v-else class="pi pi-spin pi-spinner"></i>
          <Button icon="pi pi-external-link" label="Read more" @click="goToArticle(newsItem.link)" class="mt-2" />
        </AccordionTab>
      </Accordion>
      <div class="mt-4 flex flex-col gap-2" v-if="suggestedTopics.length > 0">
        <h3 class="text-lg font-semibold mb-2">Recommended Topics based on your current Topics</h3>
        <Message severity="info" class="mb-2">These topics are generated from Jaccard Similarity score</Message>
        <div class="mt-4 flex flex-wrap gap-2">
          <Button
            v-for="(topic, index) in suggestedTopics"
            :key="index"
            :label="topic"
            @click="confirmAddTopic(topic)"
          />
        </div>
      </div>
    </section>
    <section>
      <h3 class="text-lg font-semibold mb-2">Since you are unfamiliar with this topic</h3>
      <p class="mb-4">{{ historicalSummary }}</p>
      <Accordion :activeIndex="0">
        <AccordionTab v-for="(newsItem, index) in historicalNews" :key="index" :header="newsItem.title">
          <p>{{ newsItem.summary }}</p>
          <Button icon="pi pi-external-link" label="Read more" @click="goToArticle(newsItem.link)" class="mt-2" />
        </AccordionTab>
      </Accordion>
      <div class="mt-4 flex flex-col gap-2" v-if="seedTopics.length > 0">
        <h3 class="text-lg font-semibold mb-2">Recommended Topics to Explore for Starter!</h3>
        <Message severity="info" class="mb-2">These topics are generated from CELF Influence Maximization algorithm</Message>
        <div class="mt-4 flex flex-wrap gap-2">
          <Button
            v-for="(topic, index) in seedTopics"
            :key="index"
            :label="topic"
            @click="confirmAddTopic(topic)"
          />
        </div>
      </div>
    </section>
    <ConfirmPopup />
  </section>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { historicalNews, historicalSummary } from '../data/news';
import Menubar from 'primevue/menubar';
import Accordion from 'primevue/accordion';
import AccordionTab from 'primevue/accordiontab';
import Button from 'primevue/button';
import ConfirmPopup from 'primevue/confirmpopup';
import { useConfirm } from 'primevue/useconfirm';
import { useUser } from '../composables/useUser';
import Message from 'primevue/message';
import { useInterest } from '../composables/useInterest';
import { useCurrentDate } from '../composables/useDate';
import { onMounted } from 'vue';
import axios from 'axios';


const { user } = useUser();
const { currentInterest, setCurrentInterest, fetchTopicSummary, fetchRelatedArticles } = useInterest();
const { currentDate } = useCurrentDate();
const summary = ref('');
const news = ref<{ title: string; summary: string; url: string }[]>([]);
const isLoading = ref(false);
const apiUrl = import.meta.env.VITE_API_URL;

const menuItems = computed(() => {
  return user.value.interests.map((interest) => ({
    label: interest.topic,
    icon: 'pi pi-fw pi-tag',
    command: () => {
      setCurrentInterest(interest.topic, interest.level);
      fetchRelatedTopics(interest.topic, user.value.id).then((result) => {
        suggestedTopics.value = result;
        console.log('Suggested topics:', result);
      });
      
      if (currentDate.value) {
          isLoading.value = true;
          fetchRelatedArticles(currentDate.value).then((result) => {
          news.value = result;
          console.log('Fetched news:', result);
          const summaries = news.value.map((article) => article.summary);
          console.log('Summaries:', summaries);
          const combined_summaries = summaries.join("\n\n");
          fetchTopicSummary(combined_summaries).then((api_summary) => {
            isLoading.value = false;
            summary.value = api_summary;
          });
        });
      }
    },
  }));
});

const confirm = useConfirm();

function goToArticle(url: string) {
  window.open(url);
}

function confirmAddTopic(topic: string) {
  confirm.require({
    message: `Do you want to add ${topic} to your interests?`,
    header: 'Confirmation',
    icon: 'pi pi-exclamation-triangle',
    accept: () => {
      user.value.interests = [
        ...user.value.interests,
        { topic, level: user.value.baseUnderstanding },
      ];
    },
  });
}

async function fetchSeedTopics(): Promise<string[]> {
  try {
    const response = await axios.get(`${apiUrl}/topic/get_seed`);
    console.log("Seed topics response:", response.data);
    const seedTopics = response.data.map((topic: { name: string }) => topic.name);
    console.log("Seed topics:", seedTopics);
    return seedTopics;
  } catch (error) {
    console.error("Error fetching seed topics:", error);
    return [];
  }
}

async function fetchRelatedTopics(topicName: string, userId: string): Promise<string[]> {
  try {
    const response = await axios.get(`${apiUrl}/topic/${topicName}?id=${userId}`);
    const relatedTopics = response.data.map((topic: { name: string }) => topic.name);
    return relatedTopics;
  } catch (error) {
    console.error("Error fetching related topics:", error);
    return [];
  }
}


const seedTopics = ref<string[]>([]);
const suggestedTopics = ref<string[]>([]);

onMounted(async () => {
  seedTopics.value = await fetchSeedTopics();
});
</script>
