// src/App.tsx
import { ChatWidget } from "./components/ChatWidget";

function App() {
  return (
    <div
      style={{
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        minHeight: "100vh",
        backgroundColor: "#fafafa",
      }}
    >
      <ChatWidget />
    </div>
  );
}

export default App;