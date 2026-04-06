import React, { useState } from "react";

const steps = [
  "Dataset",
  "Parameters",
  "Training",
  "Preview & Export"
];

export default function LoRATraining() {
  const [step, setStep] = useState(0);
  // Dataset state
  const [dataset, setDataset] = useState(null);
  // Params state
  const [params, setParams] = useState({
    learningRate: 1e-4,
    batchSize: 1,
    epochs: 25,
    resolution: 512,
    networkRank: 32,
    alpha: 32.0,
    dropout: 0.0,
  });
  // Training state
  const [training, setTraining] = useState({ running: false, progress: 0, log: "" });
  // Preview/export state
  const [preview, setPreview] = useState(null);
  const [exportUrl, setExportUrl] = useState(null);

  // Handlers
  function handleDatasetUpload(e) {
    setDataset(e.target.files);
  }
  function handleParamChange(e) {
    setParams({ ...params, [e.target.name]: e.target.value });
  }
  function startTraining() {
    setTraining({ running: true, progress: 0, log: "Training started..." });
    // Simulate training
    let p = 0;
    const interval = setInterval(() => {
      p += 10;
      setTraining(t => ({ ...t, progress: p, log: t.log + `\nEpoch ${p/10}` }));
      if (p >= 100) {
        clearInterval(interval);
        setTraining(t => ({ ...t, running: false, log: t.log + "\nTraining complete!" }));
        setPreview("/placeholder_lora_preview.png");
        setExportUrl("/placeholder_lora.safetensors");
      }
    }, 500);
  }

  return (
    <div className="p-4 bg-white rounded shadow mt-4">
      <h2 className="text-xl font-bold mb-2">LoRA Training Workflow</h2>
      <div className="flex space-x-2 mb-4">
        {steps.map((s, i) => (
          <button
            key={s}
            className={`px-3 py-1 rounded ${i === step ? "bg-blue-500 text-white" : "bg-gray-200"}`}
            onClick={() => setStep(i)}
          >
            {s}
          </button>
        ))}
      </div>
      {step === 0 && (
        <div>
          <h3 className="font-semibold mb-2">1. Upload Dataset</h3>
          <input type="file" multiple accept="image/*" onChange={handleDatasetUpload} />
          {dataset && <div className="mt-2 text-green-700">{dataset.length} files selected</div>}
        </div>
      )}
      {step === 1 && (
        <div>
          <h3 className="font-semibold mb-2">2. Configure Parameters</h3>
          <div className="grid grid-cols-2 gap-2">
            <label>Learning Rate <input type="number" step="1e-5" name="learningRate" value={params.learningRate} onChange={handleParamChange} className="border p-1 w-24" /></label>
            <label>Batch Size <input type="number" name="batchSize" value={params.batchSize} onChange={handleParamChange} className="border p-1 w-24" /></label>
            <label>Epochs <input type="number" name="epochs" value={params.epochs} onChange={handleParamChange} className="border p-1 w-24" /></label>
            <label>Resolution <input type="number" name="resolution" value={params.resolution} onChange={handleParamChange} className="border p-1 w-24" /></label>
            <label>Network Rank <input type="number" name="networkRank" value={params.networkRank} onChange={handleParamChange} className="border p-1 w-24" /></label>
            <label>Alpha <input type="number" step="0.1" name="alpha" value={params.alpha} onChange={handleParamChange} className="border p-1 w-24" /></label>
            <label>Dropout <input type="number" step="0.01" name="dropout" value={params.dropout} onChange={handleParamChange} className="border p-1 w-24" /></label>
          </div>
        </div>
      )}
      {step === 2 && (
        <div>
          <h3 className="font-semibold mb-2">3. Training</h3>
          <button
            className="bg-blue-500 text-white px-4 py-2 rounded mb-2"
            disabled={training.running}
            onClick={startTraining}
          >
            {training.running ? "Training..." : "Start Training"}
          </button>
          <div className="mt-2">
            <progress value={training.progress} max="100" className="w-full" />
            <pre className="bg-gray-100 p-2 mt-2 h-32 overflow-y-scroll">{training.log}</pre>
          </div>
        </div>
      )}
      {step === 3 && (
        <div>
          <h3 className="font-semibold mb-2">4. Preview & Export</h3>
          {preview && <img src={preview} alt="preview" className="max-h-48 mb-2" />}
          {exportUrl && <a href={exportUrl} download className="text-blue-600 underline">Download LoRA Model</a>}
        </div>
      )}
    </div>
  );
}
