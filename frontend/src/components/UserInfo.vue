<template>
  <aside class="bg-card p-4 rounded shadow mt-20">
    <div class="flex flex-col items-center">
      <img src="../assets/user-avatar.jpg" alt="User Avatar" class="w-32 h-32 rounded-full mb-4" />
      <h2 class="text-xl font-bold mb-2">{{ user.name }}</h2>
    </div>
    <section class="mb-4">
      <h3 class="text-lg font-semibold mb-2">Interests</h3>
      <div class="flex flex-wrap gap-2">
        <Chip
          v-for="(interest, index) in user.interests"
          :key="index"
          :label="`${interest.topic} (${interest.level})`"
          removable
          @remove="removeInterest(index)"
        />
      </div>
      <div class="mt-2">
        <InputText v-model="newInterest" placeholder="Add interest" class="w-full mb-2" />
        <Dropdown v-model="newLevel" :options="levels" placeholder="Select level" class="w-full mb-2" />
        <Button label="Add" @click="addInterest" class="w-full" />
      </div>
    </section>
    <section class="mb-4">
      <h3 class="text-lg font-semibold mb-2">Base Understanding</h3>
      <Slider v-model="understandingValue" :min="0" :max="2" :step="1" class="w-full" />
      <p class="text-center mt-2">{{ levels[understandingValue] }}</p>
    </section>
    <section>
      <h3 class="text-lg font-semibold mb-2">Date Joined</h3>
      <Calendar v-model="user.joinDate" dateFormat="mm/dd/yy" class="w-full" />
    </section>
  </aside>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { user } from '../data/user';
import Chip from 'primevue/chip';
import InputText from 'primevue/inputtext';
import Dropdown from 'primevue/dropdown';
import Button from 'primevue/button';
import Slider from 'primevue/slider';
import Calendar from 'primevue/calendar';

const levels = ['Beginner', 'Intermediate', 'Expert'];
const understandingValue = ref(levels.indexOf(user.baseUnderstanding));

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
