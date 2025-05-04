import { createApp } from "vue";
import App from "./App.vue";
import PrimeVue from "primevue/config";
import Aura from "@primeuix/themes/aura";
import ConfirmationService from "primevue/confirmationservice";
import ToastService from "primevue/toastservice";
import "primeicons/primeicons.css";
import "./assets/tailwind.css";

const app = createApp(App);

app.use(PrimeVue, {
  theme: {
    preset: Aura,
    semantic: {
      primary: {
        50: "{sky.50}",
        100: "{sky.100}",
        200: "{sky.200}",
        300: "{sky.300}",
        400: "{sky.400}",
        500: "{sky.500}",
        600: "{sky.600}",
        700: "{sky.700}",
        800: "{sky.800}",
        900: "{sky.900}",
        950: "{sky.950}",
      },
      secondary: {
        50: "{indigo.50}",
        100: "{indigo.100}",
        200: "{indigo.200}",
        300: "{indigo.300}",
        400: "{indigo.400}",
        500: "{indigo.500}",
        600: "{indigo.600}",
        700: "{indigo.700}",
        800: "{indigo.800}",
        900: "{indigo.900}",
        950: "{indigo.950}",
      },
      neutral: {
        50: "{gray.50}",
        100: "{gray.100}",
        200: "{gray.200}",
        300: "{gray.300}",
        400: "{gray.400}",
        500: "{gray.500}",
        600: "{gray.600}",
        700: "{gray.700}",
        800: "{gray.800}",
        900: "{gray.900}",
        950: "{gray.950}",
      },
    },
    options: {
      darkModeSelector: false,
    },
  },
  ripple: true,
});

app.use(ConfirmationService);
app.use(ToastService);
app.mount("#app");
