import {
  useEffect,
  useState,
} from "react";

import {
  Activity,
  Brain,
  Database,
  HardDrive,
  Loader2,
  RefreshCw,
  Server,
  CheckCircle2,
  AlertTriangle,
  XCircle,
} from "lucide-react";

import {
  getSystemHealth,
} from "../api";


function SystemPage() {
  const [health, setHealth] =
    useState(null);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");


  async function loadHealth() {
    try {
      setLoading(true);
      setError("");

      const data =
        await getSystemHealth();

      setHealth(data);

    } catch (err) {
      setError(
        err.message ||
          "Could not load system status."
      );
    } finally {
      setLoading(false);
    }
  }


  useEffect(() => {
    loadHealth();
  }, []);


  function StatusBadge({
    status,
  }) {
    if (status === "healthy") {
      return (
        <div className="system-status healthy-status">
          <CheckCircle2 size={14} />
          Healthy
        </div>
      );
    }

    if (status === "degraded") {
      return (
        <div className="system-status degraded-status">
          <AlertTriangle size={14} />
          Degraded
        </div>
      );
    }

    return (
      <div className="system-status offline-status">
        <XCircle size={14} />
        Offline
      </div>
    );
  }


  if (loading) {
    return (
      <div className="dashboard-loading">
        <Loader2
          className="spinner"
          size={27}
        />

        Checking local AI stack...
      </div>
    );
  }


  if (error) {
    return (
      <div className="error-card">
        <strong>
          System information unavailable
        </strong>

        <p>{error}</p>

        <button
          className="secondary-action"
          onClick={loadHealth}
          style={{
            marginTop: "14px",
          }}
        >
          <RefreshCw size={15} />
          Retry
        </button>
      </div>
    );
  }


  const components =
    health?.components || {};

  const lm =
    components.lm_studio || {};

  const duckdb =
    components.duckdb || {};

  const chroma =
    components.chromadb || {};


  return (
    <div className="system-page">

      <div className="page-heading">

        <div>
          <h2>
            System
          </h2>

          <p>
            Runtime status of your local
            SupplyChain Copilot stack.
          </p>
        </div>


        <button
          className="secondary-action"
          onClick={loadHealth}
        >
          <RefreshCw size={16} />
          Refresh
        </button>

      </div>


      {/* Overall status */}

      <div className="system-overview">

        <div className="system-overview-icon">
          <Activity size={24} />
        </div>

        <div>
          <span>
            Overall system
          </span>

          <strong>
            {health?.status === "healthy"
              ? "All systems operational"
              : "Some services need attention"}
          </strong>
        </div>

        <StatusBadge
          status={
            health?.status
          }
        />

      </div>


      {/* Components */}

      <div className="system-grid">

        {/* LM Studio */}

        <div className="system-card">

          <div className="system-card-header">

            <div className="system-card-icon">
              <Brain size={20} />
            </div>

            <div>
              <strong>
                LM Studio
              </strong>

              <span>
                Local AI runtime
              </span>
            </div>

            <StatusBadge
              status={lm.status}
            />

          </div>


          <div className="system-details">

            <div>
              <span>
                LLM
              </span>

              <strong>
                {lm.llm_model || "—"}
              </strong>
            </div>

            <div>
              <span>
                Embedding model
              </span>

              <strong>
                {lm.embedding_model || "—"}
              </strong>
            </div>

            <div>
              <span>
                Server
              </span>

              <strong>
                {lm.url || "—"}
              </strong>
            </div>

            <div>
              <span>
                Loaded models
              </span>

              <strong>
                {lm.loaded_models?.length || 0}
              </strong>
            </div>

          </div>

        </div>


        {/* DuckDB */}

        <div className="system-card">

          <div className="system-card-header">

            <div className="system-card-icon">
              <Database size={20} />
            </div>

            <div>
              <strong>
                DuckDB
              </strong>

              <span>
                Operational analytics
              </span>
            </div>

            <StatusBadge
              status={duckdb.status}
            />

          </div>


          <div className="system-description">
            Structured CSV and Excel
            datasets are queried locally
            using read-only analytical SQL.
          </div>

        </div>


        {/* Chroma */}

        <div className="system-card">

          <div className="system-card-header">

            <div className="system-card-icon">
              <HardDrive size={20} />
            </div>

            <div>
              <strong>
                ChromaDB
              </strong>

              <span>
                Vector knowledge base
              </span>
            </div>

            <StatusBadge
              status={chroma.status}
            />

          </div>


          <div className="system-details">

            <div>
              <span>
                Collections
              </span>

              <strong>
                {chroma.collections ?? "—"}
              </strong>
            </div>

          </div>

        </div>


        {/* API */}

        <div className="system-card">

          <div className="system-card-header">

            <div className="system-card-icon">
              <Server size={20} />
            </div>

            <div>
              <strong>
                FastAPI
              </strong>

              <span>
                Backend API
              </span>
            </div>

            <StatusBadge
              status="healthy"
            />

          </div>


          <div className="system-description">
            Routes document RAG,
            structured analytics,
            supplier verification and
            combined intelligence.
          </div>

        </div>

      </div>


      {/* Architecture */}

      <div className="system-architecture">

        <div className="section-label">
          Architecture
        </div>

        <div className="architecture-flow">

          <div>
            React
          </div>

          <span>→</span>

          <div>
            FastAPI
          </div>

          <span>→</span>

          <div>
            Router
          </div>

          <span>→</span>

          <div>
            DuckDB / ChromaDB
          </div>

          <span>→</span>

          <div>
            Qwen
          </div>

        </div>

      </div>

    </div>
  );
}


export default SystemPage;