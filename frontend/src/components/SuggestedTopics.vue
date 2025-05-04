<template>
  <div class="mt-4 flex flex-wrap gap-2">
    <Button
      v-for="(topic, index) in suggestedTopics"
      :key="index"
      :label="`Add ${topic}`"
      @click="confirmAddTopic($event, topic)"
      class="bg-green-500 text-white"
    />
  </div>
  <ConfirmPopup />
</template>

<script setup lang="ts">
import { useConfirm } from 'primevue/useconfirm';
import Button from 'primevue/button';
import ConfirmPopup from 'primevue/confirmpopup';
import { user } from '../data/user';

const confirm = useConfirm();
const suggestedTopics = ['Deep Learning', 'Natural Language Processing', 'Computer Vision'];

function confirmAddTopic(event: Event, topic: string) {
  confirm.require({
    target: event.currentTarget as HTMLElement,
    message: `Do you want to add ${topic} to your interests?`,
    header: 'Confirmation',
    icon: 'pi pi-exclamation-triangle',
    accept: () => {
      user.interests.push({ topic, level: 'Beginner' });
    },
  });
}
</script>
