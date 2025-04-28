<template>
  <div class="p-4">
    <div v-for="msg in messages" :key="msg.id" class="mb-2">
      <p><strong>{{ msg.role }}:</strong> {{ msg.content }}</p>
    </div>
    <input v-model="userInput" @keyup.enter="sendMessage" class="border p-2 w-full" />
    <div class="relative mt-2">
      <button @click="toggleDropdown" class="border p-2 w-full bg-gray-200">
        {{ selectedOption }}
      </button>
      <ul v-if="dropdownOpen" class="absolute bg-gray-900 border mt-1 w-full">
        <li v-for="option in options" :key="option" @click="selectOption(option)" class="p-2 hover:bg-gray-700 cursor-pointer">
          {{ option }}
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const messages = ref<{ role: string, content: string }[]>([])
const userInput = ref("")
const dropdownOpen = ref(false)
const options = ref(["Easy Read", "Standard Summary", "Deep Dive"])
const selectedOption = ref("Standard Summary") // Default option set to "B"

const toggleDropdown = () => {
  dropdownOpen.value = !dropdownOpen.value
}

const selectOption = (option: string) => {
  // messages.value.push({ role: "user", content: `Change ${option}` })
  selectedOption.value = option
  dropdownOpen.value = false
}

const sendMessage = async () => {
  messages.value.push({ role: "user", content: userInput.value })
  const res = await fetch(import.meta.env.VITE_API_URL + '/api/chat', {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message: userInput.value }),
  })
  const data = await res.json()
  messages.value.push({ role: "bot", content: data.response })
  userInput.value = ""
}
</script>
