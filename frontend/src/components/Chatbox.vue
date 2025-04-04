<template>
  <div class="p-4">
    <div v-for="msg in messages" :key="msg.id" class="mb-2">
      <p><strong>{{ msg.role }}:</strong> {{ msg.content }}</p>
    </div>
    <input v-model="userInput" @keyup.enter="sendMessage" class="border p-2 w-full" />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const messages = ref<{ role: string, content: string }[]>([])
const userInput = ref("")

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
