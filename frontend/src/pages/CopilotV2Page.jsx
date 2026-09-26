import { useState } from "react";
import ReactMarkdown from "react-markdown";

import { askV2Copilot } from "../api_v2";
import AgentTrace from "../components/AgentTrace";
import ContextPanel from "../components/ContextPanel";
import ExportButtons from "../components/ExportButtons";
import "../v2.css";


export default function CopilotV2Page() {
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function submit(event) {
    event.preventDefault();
    const clean = question.trim();
    if (!clean) return;
    setLoading(true);
    setError("");
    setResult(null);
    try {
      setResult(await askV2Copilot(clean));
    } catch (err) {
      setError(err.message || "Request failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="v2-copilot-page">
      <form className="v2-question-form" onSubmit={submit}>
        <textarea
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder="Ask across operational data and supplier documents..."
          rows={3}
        />
        <button type="submit" disabled={loading}>
          {loading ? "Analyzing..." : "Run v2 Analysis"}
        </button>
      </form>

      {error && <div className="v2-error">{error}</div>}

      {result && (
        <>
          <ContextPanel context={result.context} />
          <AgentTrace trace={result.trace} />

          <section className="v2-panel">
            <h3>Answer</h3>
            <ReactMarkdown>{result.answer || "No answer returned."}</ReactMarkdown>
            <ExportButtons analysisId={result.analysis_id} />
          </section>
        </>
      )}
    </div>
  );
}
