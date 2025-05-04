<template>
  <section>
    <h3 class="text-lg font-semibold mb-2 text-text-primary">Interests</h3>
    <div class="flex flex-wrap gap-2">
      <Chip
        v-for="(interest, index) in user.interests"
        :key="index"
        :label="`${interest.topic} (${interest.level})`"
        removable
        @remove="removeInterest(index)"
        class="bg-primary-500 text-white"
      />
    </div>
    <div class="mt-2">
      <InputText v-model="newInterest" placeholder="Add interest" class="w-full mb-2" />
      <Dropdown
        v-model="newLevel"
        :options="levels"
        placeholder="Select level"
        class="w-full mb-2"
      />
      <Button label="Add" @click="addInterest" class="w-full" />
    </div>
  </section>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { user } from '../data/user';
import Chip from 'primevue/chip';
import InputText from 'primevue/inputtext';
import Dropdown from 'primevue/dropdown';
import Button from 'primevue/button';

const levels = ['Beginner', 'Intermediate', 'Expert'];
const newInterest = ref('');
const newLevel = ref('');

function addInterest() {
  if (newInterest.value && newLevel.value) {
    user.interests.push({ topic: newInterest.value, level: newLevel.value });
    newInterest.value = '';
    newLevel.value = '';
  }
}

function removeInterest(index: number) {
  user.interests.splice(index, 1);
}
</script>
