import {
  useEffect,
  useState,
} from "react";
const currency =
  import.meta.env.VITE_CURRENCY || "PKR";
import {
  AlertTriangle,
  Boxes,
  Database,
  FileText,
  Loader2,
  PackageOpen,
  RefreshCw,
  Sparkles,
  Truck,
  Users,
  WalletCards,
  ArrowRight,
} from "lucide-react";

import {
  getDashboardSummary,
} from "../api";


function DashboardPage({
  onNavigate,
  onAsk,
}) {
  const [dashboard, setDashboard] =
    useState(null);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");


  async function loadDashboard() {
    try {
      setLoading(true);
      setError("");

      const data =
        await getDashboardSummary();

      setDashboard(data);

    } catch (err) {
      setError(
        err.message ||
          "Could not load dashboard."
      );
    } finally {
      setLoading(false);
    }
  }


  useEffect(() => {
    loadDashboard();
  }, []);


  function formatNumber(value) {
    return new Intl.NumberFormat(
      "en-US"
    ).format(value || 0);
  }


function formatMoney(value) {
  return new Intl.NumberFormat(
    "en-US",
    {
      style: "currency",
      currency,
      maximumFractionDigits: 0,
    }
  ).format(value || 0);
}


  if (loading) {
    return (
      <div className="dashboard-loading">
        <Loader2
          size={28}
          className="spinner"
        />

        Loading operational dashboard...
      </div>
    );
  }


  if (error) {
    return (
      <div className="error-card">
        <strong>
          Dashboard unavailable
        </strong>

        <p>{error}</p>

        <button
          className="secondary-action"
          onClick={loadDashboard}
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


  const metrics =
    dashboard?.metrics || {};

  const operationalCards = [
    {
      title:
        "Delayed shipments",

      value:
        metrics.delayed_shipments,

      icon:
        AlertTriangle,

      question:
        "Which shipments are delayed?",
    },

    {
      title:
        "Open purchase orders",

      value:
        metrics.open_purchase_orders,

      icon:
        PackageOpen,

      question:
        "Which purchase orders are open?",
    },

    {
      title:
        "Low-stock items",

      value:
        metrics.low_stock_items,

      icon:
        Boxes,

      question:
        "Which inventory items are below reorder level?",
    },

    {
      title:
        "Outstanding PO value",

      value:
        formatMoney(
          metrics.open_po_outstanding_value
        ),

      icon:
        WalletCards,

      question:
        "What is the outstanding value of open purchase orders by supplier?",
    },
  ];


  const quickQuestions = [
    "Which shipments are delayed?",

    "Which inventory items are below reorder level?",

    "Which open purchase orders belong to suppliers with contractual late-delivery penalties?",
  ];


  return (
    <div className="dashboard-page">

      {/* Heading */}

      <div className="dashboard-page-heading">

        <div>
          <h2>
            Operations Overview
          </h2>

          <p>
            Live summary from your
            structured data and AI
            knowledge base.
          </p>
        </div>


        <button
          className="secondary-action"
          onClick={loadDashboard}
        >
          <RefreshCw size={16} />

          Refresh
        </button>

      </div>


      {/* Operational attention */}

      <div className="dashboard-section-header">
        <div>
          <h3>
            Operational attention
          </h3>

          <p>
            Current issues detected in
            your uploaded data.
          </p>
        </div>
      </div>


      <div className="operations-grid">

        {operationalCards.map(
          (card) => {
            const Icon =
              card.icon;

            return (
              <button
                className="operation-card"
                key={card.title}
                onClick={() =>
                  onAsk(
                    card.question
                  )
                }
              >

                <div className="operation-card-top">

                  <div className="operation-icon">
                    <Icon size={19} />
                  </div>

                  <ArrowRight
                    size={16}
                    className="operation-arrow"
                  />

                </div>


                <strong>
                  {card.value}
                </strong>

                <span>
                  {card.title}
                </span>

              </button>
            );
          }
        )}

      </div>


      {/* Knowledge base */}

      <div className="dashboard-section-header second-section">

        <div>
          <h3>
            Workspace
          </h3>

          <p>
            Knowledge and data available
            to SupplyChain Copilot.
          </p>
        </div>

      </div>


      <div className="workspace-metric-grid">

        <button
          className="workspace-metric-card"
          onClick={() =>
            onNavigate(
              "documents"
            )
          }
        >
          <div className="workspace-icon">
            <FileText size={19} />
          </div>

          <div>
            <strong>
              {metrics.documents || 0}
            </strong>

            <span>
              Indexed documents
            </span>

            <small>
              {metrics.document_pages ||
                0}{" "}
              pages ·{" "}
              {metrics.document_chunks ||
                0}{" "}
              chunks
            </small>
          </div>
        </button>


        <button
          className="workspace-metric-card"
          onClick={() =>
            onNavigate(
              "data"
            )
          }
        >
          <div className="workspace-icon">
            <Database size={19} />
          </div>

          <div>
            <strong>
              {metrics.datasets || 0}
            </strong>

            <span>
              DuckDB tables
            </span>

            <small>
              {formatNumber(
                metrics.dataset_rows
              )}{" "}
              total rows
            </small>
          </div>
        </button>


        <button
          className="workspace-metric-card"
          onClick={() =>
            onNavigate(
              "suppliers"
            )
          }
        >
          <div className="workspace-icon">
            <Users size={19} />
          </div>

          <div>
            <strong>
              {metrics.supplier_aliases ||
                0}
            </strong>

            <span>
              Supplier aliases
            </span>

            <small>
              Verified identity mappings
            </small>
          </div>
        </button>

      </div>


      {/* Bottom grid */}

      <div className="dashboard-bottom-grid">

        {/* Recent datasets */}

        <div className="dashboard-panel">

          <div className="dashboard-panel-header">

            <div>
              <h3>
                Recent datasets
              </h3>

              <p>
                Operational tables
                available for analytics.
              </p>
            </div>


            <button
              onClick={() =>
                onNavigate(
                  "data"
                )
              }
            >
              View all
            </button>

          </div>


          <div className="recent-dataset-list">

            {dashboard
              ?.recent_datasets
              ?.map(
                (dataset) => (
                  <div
                    className="recent-dataset-row"
                    key={
                      dataset.table_name
                    }
                  >

                    <div className="recent-dataset-icon">
                      <Database
                        size={16}
                      />
                    </div>


                    <div className="recent-dataset-info">

                      <strong>
                        {
                          dataset.table_name
                        }
                      </strong>

                      <span>
                        {
                          dataset.row_count
                        }{" "}
                        rows ·{" "}
                        {
                          dataset.columns
                        }{" "}
                        columns
                      </span>

                    </div>

                  </div>
                )
              )}

          </div>

        </div>


        {/* Quick questions */}

        <div className="dashboard-panel">

          <div className="dashboard-panel-header">

            <div>
              <h3>
                Ask Copilot
              </h3>

              <p>
                Jump directly into an
                operational question.
              </p>
            </div>

            <Sparkles size={18} />

          </div>


          <div className="quick-question-list">

            {quickQuestions.map(
              (question) => (
                <button
                  key={question}
                  onClick={() =>
                    onAsk(
                      question
                    )
                  }
                >

                  <Sparkles
                    size={14}
                  />

                  <span>
                    {question}
                  </span>

                  <ArrowRight
                    size={14}
                  />

                </button>
              )
            )}

          </div>

        </div>

      </div>

    </div>
  );
}


export default DashboardPage;