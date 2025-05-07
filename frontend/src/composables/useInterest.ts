import { ref, onMounted, watch } from "vue";
import axios from "axios";
const apiUrl = import.meta.env.VITE_API_URL;

const currentInterest = ref({
    topic: "",
    level: "",
});

function setCurrentInterest(topic: string, level: string) {
    currentInterest.value.topic = topic;
    currentInterest.value.level = level;
}


async function fetchTopicSummary(combined_summaries: String) {
    if (!combined_summaries) {
        console.warn("Combined summaries is empty. Skipping fetch.");
        return "";
    }
    try {
        const response = await axios.post(`${apiUrl}/summarize_all_articles`,{
          topic: currentInterest.value.topic,
          combined_summaries: combined_summaries,
        });
        console.log("Topic summary response:", response.data);
        return response.data;
    }
    catch (error) {
      console.error("Error fetching topic summary:", error);
      return "Error fetching topic summary";
  }
}

async function checkAndHandleHistory(user_id: string, topic: string, current_date: Date): Promise<{ initialized: boolean; data: any }> {
  try {
    // Check if history exists
    console.log("Checking if history exists for user:", user_id, "and topic:", topic);
    const getResponse = await axios.get(`${apiUrl}/articles/history`, {
      params: {
        user_id: user_id,
        topic: topic,
        level: currentInterest.value.level,
      },
    });

    console.log("History check response:", getResponse.data);

    if (getResponse.data && getResponse.data.length > 0) {
      console.log("History exists. Updating history...");

      // Update history with a PUT request
      const putResponse = await axios.put(`${apiUrl}/articles/history`, {
        user_id: user_id,
        topic: topic,
        current_date: current_date.toISOString(),
        level: currentInterest.value.level,
      });

      console.log("History updated:", putResponse.data);
      return { initialized: false, data: putResponse.data }; // Return updated history with initialized = false
    } else {
      console.log("No history found. Initializing history...");

      // Initialize history with a POST request
      const postResponse = await axios.post(`${apiUrl}/articles/history`, {
        user_id: user_id,
        topic: topic,
        current_date: current_date.toISOString(),
        level: currentInterest.value.level,
      });

      console.log("History initialized:", postResponse.data);
      return { initialized: true, data: postResponse.data }; // Return initialized history with initialized = true
    }
  } catch (error) {
    console.error("Error checking or handling history:", error);
    return { initialized: false, data: null }; // Return null data in case of an error
  }
}

async function fetchRelatedArticles(currentDate: Date) {
  if (!currentInterest.value.topic) {
    console.warn("Topic is empty. Skipping fetch.");
    return [];
  }

  try {
    const response = await axios.get(`${apiUrl}/articles/topic`, {
      params: {
        topic: currentInterest.value.topic,
        level: currentInterest.value.level,
        before_date: currentDate.toISOString().split("T")[0],
      },
    });

    console.log("Related articles response:", response.data);
    return response.data.articles ?? [];
  } catch (error) {
    console.error("Error fetching related articles:", error);
    return [];
  }
}


export function useInterest() {
  return {
    currentInterest,
    setCurrentInterest,
    fetchRelatedArticles,
    fetchTopicSummary,
    checkAndHandleHistory,
  };
}