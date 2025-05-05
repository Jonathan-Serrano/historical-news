import { ref, watch } from "vue";
import axios from "axios";

const apiUrl = import.meta.env.VITE_API_URL;

const user = ref({
  id: "user123",
  name: "John Doe",
  baseUnderstanding: "Intermediate",
  joinDate: new Date("2025-05-04T00:00:00Z"),
  interests: [] as { topic: string; level: string }[],
});

const levels = ["Beginner", "Intermediate", "Expert"];
const understandingValue = ref(levels.indexOf(user.value.baseUnderstanding));

async function fetchUserData() {
  try {
    const response = await axios.get(`${apiUrl}/user?id=${user.value.id}`);
    if (response.data) {
      user.value = {
        id: response.data.id,
        name: response.data.name,
        baseUnderstanding: response.data.base_understanding,
        joinDate: new Date(response.data.join_date),
        interests: response.data.interests.map((interest: any) => ({
          topic: interest.topic,
          level: interest.level,
        })),
      };
    } else {
      await createUser();
    }
  } catch (error) {
    console.error("Error fetching user data:", error);
  }
}

async function createUser() {
  try {
    const response = await axios.post(`${apiUrl}/user`, {
      id: user.value.id,
      name: user.value.name,
      base_understanding: user.value.baseUnderstanding,
      join_date: user.value.joinDate,
    });
    console.log(response.data.message);
    fetchUserData();
  } catch (error) {
    console.error("Error creating user:", error);
  }
}

async function updateUser() {
  try {
    await axios.put(`${apiUrl}/user`, {
      id: user.value.id,
      name: user.value.name,
      base_understanding: levels[understandingValue.value],
      join_date: user.value.joinDate,
    });
  } catch (error) {
    console.error("Error updating user info:", error);
  }
}

watch([understandingValue, user], updateUser, { deep: true });
watch(
  () => user.value.baseUnderstanding,
  (newBaseUnderstanding) => {
    understandingValue.value = levels.indexOf(newBaseUnderstanding);
  }
);

export function useUser() {
  return {
    user,
    levels,
    understandingValue,
    fetchUserData,
    createUser,
    updateUser,
  };
}
