<template>
  <aside class="bg-card p-4 rounded shadow mt-20">
    <div class="flex flex-col items-center">
      <img src="../assets/user-avatar.jpg" alt="User Avatar" class="w-32 h-32 rounded-full mb-4" />
      <h2 class="text-xl font-bold mb-2">{{ user.name }}</h2>
    </div>
    
    <!-- Interests Section -->
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
      <div class="mt-2 flex flex-row gap-2">
        <AutoComplete
          v-model="newInterest"
          :suggestions="filteredInterests"
          @complete="searchInterest"
          placeholder="Add interest"
          class="w-full"
          forceSelection
          dropdown 
        />
        <Dropdown v-model="newLevel" :options="levels" placeholder="Select level" class="w-full" />
        <Button label="Add" @click="addInterest" class="w-full" />
      </div>
    </section>
    
    <!-- Base Understanding Section -->
    <section class="mb-4">
      <h3 class="text-lg font-semibold mb-2">Base Understanding</h3>
      <Slider v-model="understandingValue" :min="0" :max="2" :step="1" class="w-full" />
      <p class="text-center mt-2">{{ levels[understandingValue] }}</p>
    </section>

    <!-- Date Joined Section -->
    <section>
      <h3 class="text-lg font-semibold mb-2">Date Joined</h3>
      <DatePicker v-model="user.joinDate" dateFormat="mm/dd/yy" class="w-full" />
    </section>
  </aside>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';
import axios from 'axios';
import Chip from 'primevue/chip';
import Dropdown from 'primevue/dropdown';
import Button from 'primevue/button';
import Slider from 'primevue/slider';
import DatePicker from 'primevue/datepicker'; 
import AutoComplete from 'primevue/AutoComplete';
import { useUser } from '../composables/useUser';
const { user, levels, understandingValue, fetchUserData } = useUser();

const apiUrl = import.meta.env.VITE_API_URL;

const filteredInterests = ref([] as string[]);        
const newInterest = ref(""); 
const newLevel = ref('');
const interests = ref<string[]>([]);

const searchInterest = (event : any) => {
  const query = event.query.toLowerCase();
  filteredInterests.value = interests.value.filter((interest) =>
    interest.toLowerCase().includes(query)
  );
};

async function fetchAllInterests() {
  try {
    const response = await axios.get(`${apiUrl}/interests`);
    if (response.data) {
      console.log('Interests fetched:', response.data);
      interests.value = response.data;
    } else {
      console.error('No interests found');
    }
  } catch (error) {
    console.error('Error fetching interests:', error);
    return [];
  }
}

async function addInterest() {
  if (newInterest.value && newLevel.value) {
    try {
      await axios.post(`${apiUrl}/user/${user.value.id}/interest`, {
        topic_name: newInterest.value,
        level: newLevel.value
      });
      user.value.interests.push({ topic: newInterest.value, level: newLevel.value });
      newInterest.value = '';
      newLevel.value = '';
    } catch (error) {
      console.error('Error adding interest:', error);
    }
  }
}

async function removeInterest(index: number) {
  const interest = user.value.interests[index];
  try {
    await axios.delete(`${apiUrl}/user/${user.value.id}/interest`, {
      data: { topic_name: interest.topic }
    });
    user.value.interests.splice(index, 1);
  } catch (error) {
    console.error('Error removing interest:', error);
  }
}

onMounted(() => {
  fetchUserData();
  fetchAllInterests();
});
</script>
