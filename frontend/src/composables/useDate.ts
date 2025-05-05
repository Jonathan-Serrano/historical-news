import { ref, onMounted, watch } from "vue";
import axios from "axios";

const apiUrl = import.meta.env.VITE_API_URL;

export function useCurrentDate() {
  const currentDate = ref<Date | null>(null);

  const fetchCurrentDate = async () => {
    try {
      const response = await axios.get(`${apiUrl}/date`);
      currentDate.value = new Date(response.data.current_date);
    } catch (error) {
      console.error("Failed to fetch current date:", error);
    }
  };

  const updateCurrentDate = async () => {
    if (currentDate.value) {
      try {
        await axios.put(
          `${apiUrl}/date`,
          { current_date: currentDate.value.toISOString() },
          { headers: { "Content-Type": "application/json" } }
        );
        console.log("Date updated successfully!");
      } catch (error) {
        console.error("Failed to update date:", error);
      }
    }
  };

  watch(currentDate, (newDate) => {
    if (newDate) {
        console.log("Current date changed:", currentDate.value);
      updateCurrentDate();
    }
  });

  onMounted(fetchCurrentDate);

  return {
    currentDate,
    fetchCurrentDate,
    updateCurrentDate,
  };
}
