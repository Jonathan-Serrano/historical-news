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
        // const response = await axios.get(`${apiUrl}/topic-summary?topic=${currentInterest.value.topic}`);
        
        //const data = "Graph Neural Nework is a type of neural network that operates on graph data structures. It is designed to learn from the relationships and connections between nodes in a graph, making it suitable for tasks such as node classification, link prediction, and graph classification. GNNs have applications in various fields, including social network analysis, recommendation systems, and molecular chemistry.";
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
    };
}