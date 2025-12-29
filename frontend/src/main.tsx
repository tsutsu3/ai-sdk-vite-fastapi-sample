import ReactDOM from "react-dom/client";
import App from "./app";
import "./index.css";
import "./i18n/i18n";

const startMocks = async () => {
  if (import.meta.env.DEV && import.meta.env.VITE_MSW === "true") {
    const { worker } = await import("./mocks/browser");
    await worker.start({
      onUnhandledRequest: "bypass",
    });
  }
};

startMocks().then(() => {
  ReactDOM.createRoot(document.getElementById("root")!).render(<App />);
});
