import { useState } from "react";
import UploadScreen from "./components/UploadScreen";
import PipelineScreen from "./components/PipelineScreen";
import ResultScreen from "./components/ResultScreen";

// App has 3 screens:
// 1. Upload   — drag-drop image or load demo
// 2. Pipeline — 5 steps animating as they complete
// 3. Result   — explanation + quiz + "Open in AR" button

export default function App() {
  const [screen, setScreen] = useState("upload");   // upload | pipeline | result
  const [contract, setContract] = useState(null);
  const [error, setError] = useState(null);

  const handleUpload = async (file) => {
    setScreen("pipeline");
    setError(null);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const res = await fetch("http://localhost:8000/analyze", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) throw new Error("Pipeline failed. Check backend.");
      const data = await res.json();
      setContract(data);
      setScreen("result");
    } catch (err) {
      setError(err.message);
      setScreen("upload");
    }
  };

  const handleDemo = async () => {
    setScreen("pipeline");
    setError(null);

    try {
      const res = await fetch("http://localhost:8000/demo");
      if (!res.ok) throw new Error("Demo load failed. Check backend.");
      const data = await res.json();
      setContract(data);
      setScreen("result");
    } catch (err) {
      setError(err.message);
      setScreen("upload");
    }
  };

  const handleReset = () => {
    setScreen("upload");
    setContract(null);
    setError(null);
  };

  return (
    <div style={{ minHeight: "100vh" }}>
      {screen === "upload" && (
        <UploadScreen
          onUpload={handleUpload}
          onDemo={handleDemo}
          error={error}
        />
      )}
      {screen === "pipeline" && <PipelineScreen />}
      {screen === "result" && (
        <ResultScreen contract={contract} onReset={handleReset} />
      )}
    </div>
  );
}