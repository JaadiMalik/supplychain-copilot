import {
  useEffect,
  useState,
} from "react";

import ReactMarkdown from "react-markdown";

import {
  Bot,
  FileText,
  Database,
  LayoutDashboard,
  Send,
  Sparkles,
  Boxes,
  ChevronDown,
  ChevronUp,
  Loader2,
  CheckCircle2,
  CircleAlert,
  Settings,
} from "lucide-react";

import {
  askCopilot,
  getSystemHealth,
} from "./api";

import DashboardPage from "./pages/DashboardPage";
import DocumentsPage from "./pages/DocumentsPage";
import DataPage from "./pages/DataPage";
import SuppliersPage from "./pages/SuppliersPage";
import SystemPage from "./pages/SystemPage";

import "./App.css";


function App() {
  // ==================================================
  // Navigation
  // ==================================================

  const [
    activePage,
    setActivePage,
  ] = useState("dashboard");


  // ==================================================
  // Copilot
  // ==================================================

  const [
    question,
    setQuestion,
  ] = useState("");

  const [
    response,
    setResponse,
  ] = useState(null);

  const [
    loading,
    setLoading,
  ] = useState(false);

  const [
    error,
    setError,
  ] = useState("");

  const [
    showDetails,
    setShowDetails,
  ] = useState(false);


  // ==================================================
  // System Health
  // ==================================================

  const [
    systemHealth,
    setSystemHealth,
  ] = useState({
    status: "checking",
    components: {},
  });


  async function loadSystemHealth() {
    try {
      const data =
        await getSystemHealth();

      setSystemHealth(data);

    } catch {
      setSystemHealth({
        status: "offline",
        components: {},
      });
    }
  }


  useEffect(() => {
    loadSystemHealth();

    const interval =
      setInterval(
        loadSystemHealth,
        30000
      );

    return () => {
      clearInterval(interval);
    };
  }, []);


  function getHealthLabel() {
    if (
      systemHealth.status ===
      "healthy"
    ) {
      return "Healthy";
    }

    if (
      systemHealth.status ===
      "degraded"
    ) {
      return "Degraded";
    }

    if (
      systemHealth.status ===
      "offline"
    ) {
      return "Offline";
    }

    return "Checking...";
  }


  function getHealthClass() {
    if (
      systemHealth.status ===
      "healthy"
    ) {
      return "healthy";
    }

    if (
      systemHealth.status ===
      "degraded"
    ) {
      return "degraded";
    }

    if (
      systemHealth.status ===
      "offline"
    ) {
      return "offline";
    }

    return "checking";
  }


  // ==================================================
  // Example Questions
  // ==================================================

  const exampleQuestions = [
    "Which shipments are delayed?",

    "Which purchase orders are open?",

    "Which inventory items are below reorder level?",

    "Which open purchase orders belong to suppliers with contractual late-delivery penalties?",
  ];


  // ==================================================
  // Run Copilot Question
  // ==================================================

  async function runQuestion(
    questionToRun
  ) {
    const cleanQuestion =
      questionToRun.trim();

    if (!cleanQuestion) {
      return;
    }

    try {
      setQuestion(
        cleanQuestion
      );

      setLoading(true);

      setError("");

      setResponse(null);

      setShowDetails(false);


      const data =
        await askCopilot(
          cleanQuestion
        );


      setResponse(data);

    } catch (err) {
      setError(
        err.message ||
          "Something went wrong."
      );

    } finally {
      setLoading(false);
    }
  }


  async function handleAsk(
    event
  ) {
    if (event) {
      event.preventDefault();
    }

    await runQuestion(
      question
    );
  }


  // ==================================================
  // Dashboard → Copilot
  // ==================================================

  async function handleDashboardAsk(
    newQuestion
  ) {
    setActivePage(
      "copilot"
    );

    await runQuestion(
      newQuestion
    );
  }


  // ==================================================
  // Extract Answer
  // ==================================================

  function getAnswer() {
    if (!response) {
      return "";
    }

    const result =
      response.result;


    if (!result) {
      return (
        response.message ||
        ""
      );
    }


    if (result.answer) {
      return result.answer;
    }


    if (result.results) {
      return JSON.stringify(
        result.results,
        null,
        2
      );
    }


    return JSON.stringify(
      result,
      null,
      2
    );
  }


  // ==================================================
  // Route Label
  // ==================================================

  function getRouteLabel() {
    if (!response?.route) {
      return "";
    }

    const labels = {
      document:
        "Document RAG",

      data:
        "Structured Data",

      combined:
        "Combined Intelligence",

      unsupported:
        "Unsupported",

      error:
        "Error",
    };

    return (
      labels[
        response.route
      ] ||
      response.route
    );
  }


  // ==================================================
  // Structured Data Helpers
  // ==================================================

  function formatColumnName(
    column
  ) {
    return column
      .replaceAll(
        "_",
        " "
      )
      .replace(
        /\b\w/g,
        (letter) =>
          letter.toUpperCase()
      );
  }


  function formatTableValue(
    value
  ) {
    if (
      value === null ||
      value === undefined ||
      value === "NaT"
    ) {
      return "—";
    }


    if (
      typeof value ===
      "string"
    ) {
      const midnightDate =
        value.match(
          /^\d{4}-\d{2}-\d{2}T00:00:00$/
        );

      if (midnightDate) {
        return value.substring(
          0,
          10
        );
      }
    }


    return String(value);
  }


  function renderStructuredResults() {
    const results =
      response?.result?.results;


    if (
      !Array.isArray(
        results
      ) ||
      results.length === 0
    ) {
      return (
        <div className="empty-data-answer">
          No matching records found.
        </div>
      );
    }


    const columns =
      Object.keys(
        results[0]
      );


    return (
      <div className="copilot-data-table-wrapper">

        <table className="copilot-data-table">

          <thead>

            <tr>

              {columns.map(
                (column) => (
                  <th
                    key={column}
                  >
                    {
                      formatColumnName(
                        column
                      )
                    }
                  </th>
                )
              )}

            </tr>

          </thead>


          <tbody>

            {results.map(
              (
                row,
                rowIndex
              ) => (
                <tr
                  key={rowIndex}
                >

                  {columns.map(
                    (
                      column
                    ) => (
                      <td
                        key={
                          column
                        }
                      >
                        {
                          formatTableValue(
                            row[
                              column
                            ]
                          )
                        }
                      </td>
                    )
                  )}

                </tr>
              )
            )}

          </tbody>

        </table>

      </div>
    );
  }


  // ==================================================
  // Evidence Groups
  // ==================================================

  function getEvidenceGroups() {
    if (!response?.result) {
      return {
        confirmed: [],
        unconfirmed: [],
      };
    }


    const result =
      response.result;


    // --------------------------------------------------
    // Document-only RAG
    // --------------------------------------------------

    if (
      result.sources &&
      !result.supplier_evidence
    ) {
      return {
        confirmed:
          result.sources.map(
            (source) => ({
              ...source,
              supplier: null,
            })
          ),

        unconfirmed: [],
      };
    }


    // --------------------------------------------------
    // Combined RAG + Data
    // --------------------------------------------------

    if (
      result.supplier_evidence
    ) {
      const confirmed = [];

      const unconfirmed = [];


      result.supplier_evidence.forEach(
        (item) => {
          const evidenceItem = {
            operationalSupplier:
              item.operational_supplier,

            canonicalSupplier:
              item.canonical_supplier,

            aliasResolved:
              item.alias_resolved,

            supplierCoverageConfirmed:
              item.supplier_coverage_confirmed,

            penaltyClauseConfirmed:
              item.penalty_clause_confirmed,

            confirmed:
              item.confirmed,

            penaltyType:
              item.penalty_type,

            rate:
              item.rate,

            calculationPeriod:
              item.calculation_period,

            maximumCap:
              item.maximum_cap,

            exceptions:
              item.exceptions || [],

            sources:
              item.sources || [],
          };


          if (
            item.confirmed
          ) {
            confirmed.push(
              evidenceItem
            );
          } else {
            unconfirmed.push(
              evidenceItem
            );
          }
        }
      );


      return {
        confirmed,
        unconfirmed,
      };
    }


    return {
      confirmed: [],
      unconfirmed: [],
    };
  }


  const evidenceGroups =
    getEvidenceGroups();


  // ==================================================
  // Page Title
  // ==================================================

  function getPageTitle() {
    if (
      activePage ===
      "dashboard"
    ) {
      return "Dashboard";
    }


    if (
      activePage ===
      "documents"
    ) {
      return "Documents";
    }


    if (
      activePage ===
      "data"
    ) {
      return "Data";
    }


    if (
      activePage ===
      "suppliers"
    ) {
      return "Suppliers";
    }


    if (
      activePage ===
      "system"
    ) {
      return "System";
    }


    return "Operations Copilot";
  }


  // ==================================================
  // Page Description
  // ==================================================

  function getPageDescription() {
    if (
      activePage ===
      "dashboard"
    ) {
      return "Overview of your supply-chain intelligence workspace.";
    }


    if (
      activePage ===
      "documents"
    ) {
      return "Manage the document knowledge base used by your AI assistant.";
    }


    if (
      activePage ===
      "data"
    ) {
      return "Manage CSV and Excel operational datasets.";
    }


    if (
      activePage ===
      "suppliers"
    ) {
      return "Manage supplier identities and verified aliases.";
    }


    if (
      activePage ===
      "system"
    ) {
      return "Monitor your local AI and data services.";
    }


    return "Ask questions across contracts, inventory, shipments and purchase orders.";
  }


  // ==================================================
  // Render App
  // ==================================================

  return (
    <div className="app-shell">

      {/* ==================================================
          SIDEBAR
      ================================================== */}

      <aside className="sidebar">

        {/* Brand */}

        <div className="brand">

          <div className="brand-icon">

            <Boxes
              size={23}
            />

          </div>


          <div>

            <div className="brand-title">
              SupplyChain
            </div>

            <div className="brand-subtitle">
              Copilot
            </div>

          </div>

        </div>


        {/* Navigation */}

        <nav className="nav">

          {/* Dashboard */}

          <button
            className={`nav-item ${
              activePage ===
              "dashboard"
                ? "active"
                : ""
            }`}
            onClick={() =>
              setActivePage(
                "dashboard"
              )
            }
          >

            <LayoutDashboard
              size={19}
            />

            Dashboard

          </button>


          {/* Copilot */}

          <button
            className={`nav-item ${
              activePage ===
              "copilot"
                ? "active"
                : ""
            }`}
            onClick={() =>
              setActivePage(
                "copilot"
              )
            }
          >

            <Sparkles
              size={19}
            />

            Copilot

          </button>


          {/* Documents */}

          <button
            className={`nav-item ${
              activePage ===
              "documents"
                ? "active"
                : ""
            }`}
            onClick={() =>
              setActivePage(
                "documents"
              )
            }
          >

            <FileText
              size={19}
            />

            Documents

          </button>


          {/* Data */}

          <button
            className={`nav-item ${
              activePage ===
              "data"
                ? "active"
                : ""
            }`}
            onClick={() =>
              setActivePage(
                "data"
              )
            }
          >

            <Database
              size={19}
            />

            Data

          </button>


          {/* Suppliers */}

          <button
            className={`nav-item ${
              activePage ===
              "suppliers"
                ? "active"
                : ""
            }`}
            onClick={() =>
              setActivePage(
                "suppliers"
              )
            }
          >

            <Boxes
              size={19}
            />

            Suppliers

          </button>


          {/* System */}

          <button
            className={`nav-item ${
              activePage ===
              "system"
                ? "active"
                : ""
            }`}
            onClick={() =>
              setActivePage(
                "system"
              )
            }
          >

            <Settings
              size={19}
            />

            System

          </button>

        </nav>


        {/* ==================================================
            HEALTH STATUS
        ================================================== */}

        <div
          className="sidebar-footer"
          onClick={
            loadSystemHealth
          }
          title="Click to refresh system status"
        >

          <div
            className={`status-dot ${getHealthClass()}`}
          />


          <div>

            <div className="status-title">

              Local AI ·{" "}
              {getHealthLabel()}

            </div>


            <div className="status-text">
              Qwen + Nomic + DuckDB
            </div>

          </div>

        </div>

      </aside>


      {/* ==================================================
          MAIN CONTENT
      ================================================== */}

      <main className="main-content">

        {/* ==================================================
            TOP BAR
        ================================================== */}

        <header className="topbar">

          <div>

            <h1>
              {getPageTitle()}
            </h1>

            <p>
              {getPageDescription()}
            </p>

          </div>


          <div className="local-badge">

            <span
              className={`top-health-dot ${getHealthClass()}`}
            />

            {getHealthLabel()}

          </div>

        </header>


        {/* ==================================================
            WORKSPACE
        ================================================== */}

        <section className="workspace">

          {/* Dashboard */}

          {activePage ===
            "dashboard" && (
            <DashboardPage
              onNavigate={
                setActivePage
              }
              onAsk={
                handleDashboardAsk
              }
            />
          )}


          {/* Documents */}

          {activePage ===
            "documents" && (
            <DocumentsPage />
          )}


          {/* Data */}

          {activePage ===
            "data" && (
            <DataPage />
          )}


          {/* Suppliers */}

          {activePage ===
            "suppliers" && (
            <SuppliersPage />
          )}


          {/* System */}

          {activePage ===
            "system" && (
            <SystemPage />
          )}


          {/* ==================================================
              COPILOT PAGE
          ================================================== */}

          {activePage ===
            "copilot" && (
            <>

              {/* ==================================================
                  WELCOME
              ================================================== */}

              {!response &&
                !loading &&
                !error && (
                  <div className="welcome">

                    <div className="welcome-icon">

                      <Bot
                        size={30}
                      />

                    </div>


                    <h2>
                      What would you
                      like to know?
                    </h2>


                    <p>
                      Analyze operational
                      data and cross-reference
                      supplier documents using
                      your local AI stack.
                    </p>


                    <div className="examples">

                      {exampleQuestions.map(
                        (
                          example
                        ) => (
                          <button
                            key={
                              example
                            }
                            className="example-card"
                            onClick={() =>
                              runQuestion(
                                example
                              )
                            }
                          >

                            <Sparkles
                              size={
                                16
                              }
                            />


                            <span>
                              {
                                example
                              }
                            </span>

                          </button>
                        )
                      )}

                    </div>

                  </div>
                )}


              {/* ==================================================
                  LOADING
              ================================================== */}

              {loading && (
                <div className="loading-card">

                  <Loader2
                    className="spinner"
                    size={30}
                  />


                  <div>

                    <h3>
                      Analyzing your
                      question
                    </h3>


                    <p>
                      Routing across
                      documents and
                      operational data...
                    </p>

                  </div>

                </div>
              )}


              {/* ==================================================
                  ERROR
              ================================================== */}

              {error && (
                <div className="error-card">

                  <strong>
                    Request failed
                  </strong>

                  <p>
                    {error}
                  </p>

                </div>
              )}


              {/* ==================================================
                  RESPONSE
              ================================================== */}

              {response && (
                <div className="response-container">

                  {/* User Question */}

                  <div className="question-card">

                    <div className="question-label">
                      Your question
                    </div>


                    <div className="question-text">
                      {question}
                    </div>

                  </div>


                  {/* Copilot Answer */}

                  <div className="answer-card">

                    {/* ------------------------------------------
                        Answer Header
                    ------------------------------------------ */}

                    <div className="answer-header">

                      <div className="assistant-title">

                        <div className="assistant-icon">

                          <Bot
                            size={20}
                          />

                        </div>


                        <div>

                          <strong>
                            SupplyChain Copilot
                          </strong>


                          <div className="route-badge">
                            {
                              getRouteLabel()
                            }
                          </div>

                        </div>

                      </div>

                    </div>


                    {/* ------------------------------------------
                        DATA ROUTE
                    ------------------------------------------ */}

                    {response?.route ===
                      "data" &&
                    response?.result
                      ?.results ? (
                      <div className="answer-text">

                        {
                          renderStructuredResults()
                        }

                      </div>
                    ) : (
                      /* ------------------------------------------
                         DOCUMENT + COMBINED ROUTES
                      ------------------------------------------ */

                      <div className="answer-text markdown-content">

                        <ReactMarkdown>
                          {getAnswer()}
                        </ReactMarkdown>

                      </div>
                    )}


                    {/* ==================================================
                        EVIDENCE
                    ================================================== */}

                    {(
                      evidenceGroups
                        .confirmed
                        .length > 0
                      ||
                      evidenceGroups
                        .unconfirmed
                        .length > 0
                    ) && (
                      <div className="evidence-section">

                        <div className="section-label">
                          Evidence
                        </div>


                        {/* ------------------------------------------
                            Confirmed Evidence
                        ------------------------------------------ */}

                        {evidenceGroups
                          .confirmed
                          .length > 0 && (
                          <div className="evidence-group">

                            <div className="evidence-heading confirmed-heading">

                              <CheckCircle2
                                size={17}
                              />


                              <span>
                                Confirmed contract evidence
                              </span>

                            </div>


                            <div className="confirmed-evidence-list">

                              {evidenceGroups.confirmed.map(
                                (
                                  item,
                                  index
                                ) => {

                                  // ======================================
                                  // Document-only RAG
                                  // ======================================

                                  if (
                                    !item.operationalSupplier
                                  ) {
                                    return (
                                      <div
                                        className="evidence-card confirmed-card"
                                        key={`${item.document}-${item.page}-${index}`}
                                      >

                                        <div className="evidence-card-title">

                                          <FileText
                                            size={17}
                                          />


                                          <strong>
                                            {
                                              item.document
                                            }
                                          </strong>

                                        </div>


                                        <div className="evidence-meta">

                                          Page{" "}
                                          {
                                            item.page
                                          }

                                        </div>

                                      </div>
                                    );
                                  }


                                  // ======================================
                                  // Combined Evidence
                                  // ======================================

                                  return (
                                    <div
                                      className="evidence-card confirmed-card"
                                      key={
                                        item.operationalSupplier
                                      }
                                    >

                                      <div className="supplier-evidence-top">

                                        <div>

                                          <div className="supplier-name">

                                            {
                                              item.operationalSupplier
                                            }

                                          </div>


                                          {item.aliasResolved &&
                                            item.canonicalSupplier !==
                                              item.operationalSupplier && (
                                              <div className="canonical-name">

                                                Verified as{" "}

                                                {
                                                  item.canonicalSupplier
                                                }

                                              </div>
                                            )}

                                        </div>


                                        <div className="verified-pill">

                                          <CheckCircle2
                                            size={13}
                                          />

                                          Verified

                                        </div>

                                      </div>


                                      {/* Contract Terms */}

                                      {(item.penaltyType ||
                                        item.rate ||
                                        item.maximumCap) && (
                                        <div className="contract-term-grid">

                                          {item.penaltyType && (
                                            <div>

                                              <span>
                                                Type
                                              </span>

                                              <strong>
                                                {
                                                  item.penaltyType
                                                }
                                              </strong>

                                            </div>
                                          )}


                                          {item.rate && (
                                            <div>

                                              <span>
                                                Rate
                                              </span>

                                              <strong>
                                                {
                                                  item.rate
                                                }
                                              </strong>

                                            </div>
                                          )}


                                          {item.maximumCap && (
                                            <div>

                                              <span>
                                                Maximum
                                              </span>

                                              <strong>
                                                {
                                                  item.maximumCap
                                                }
                                              </strong>

                                            </div>
                                          )}

                                        </div>
                                      )}


                                      {/* Source Documents */}

                                      {item.sources
                                        .length > 0 && (
                                        <div className="evidence-source-row">

                                          {item.sources.map(
                                            (
                                              source,
                                              sourceIndex
                                            ) => (
                                              <div
                                                className="source-chip"
                                                key={`${source.document}-${source.page}-${sourceIndex}`}
                                              >

                                                <FileText
                                                  size={15}
                                                />


                                                <div>

                                                  <strong>

                                                    {
                                                      source.document
                                                    }

                                                  </strong>


                                                  <span>

                                                    Page{" "}
                                                    {
                                                      source.page
                                                    }

                                                  </span>

                                                </div>

                                              </div>
                                            )
                                          )}

                                        </div>
                                      )}

                                    </div>
                                  );
                                }
                              )}

                            </div>

                          </div>
                        )}


                        {/* ------------------------------------------
                            Unconfirmed Suppliers
                        ------------------------------------------ */}

                        {evidenceGroups
                          .unconfirmed
                          .length > 0 && (
                          <div className="evidence-group unconfirmed-group">

                            <div className="evidence-heading unconfirmed-heading">

                              <CircleAlert
                                size={17}
                              />


                              <span>
                                No confirmed contract evidence
                              </span>

                            </div>


                            <div className="unconfirmed-list">

                              {evidenceGroups.unconfirmed.map(
                                (
                                  item
                                ) => (
                                  <div
                                    className="unconfirmed-item"
                                    key={
                                      item.operationalSupplier
                                    }
                                  >

                                    <div>

                                      <strong>

                                        {
                                          item.operationalSupplier
                                        }

                                      </strong>


                                      {item.canonicalSupplier &&
                                        item.canonicalSupplier !==
                                          item.operationalSupplier && (
                                          <span>

                                            {
                                              item.canonicalSupplier
                                            }

                                          </span>
                                        )}

                                    </div>


                                    <div className="unconfirmed-badge">
                                      Unconfirmed
                                    </div>

                                  </div>
                                )
                              )}

                            </div>

                          </div>
                        )}

                      </div>
                    )}


                    {/* ==================================================
                        TECHNICAL DETAILS
                    ================================================== */}

                    <button
                      className="details-button"
                      onClick={() =>
                        setShowDetails(
                          !showDetails
                        )
                      }
                    >

                      Technical details


                      {showDetails ? (
                        <ChevronUp
                          size={17}
                        />
                      ) : (
                        <ChevronDown
                          size={17}
                        />
                      )}

                    </button>


                    {showDetails && (
                      <div className="technical-details">

                        {/* Route */}

                        <div className="detail-row">

                          <span>
                            Route
                          </span>


                          <strong>
                            {
                              response.route
                            }
                          </strong>

                        </div>


                        {/* Router Reason */}

                        {response.router_reason && (
                          <div className="detail-block">

                            <span>
                              Router reason
                            </span>


                            <p>
                              {
                                response.router_reason
                              }
                            </p>

                          </div>
                        )}


                        {/* Data Explanation */}

                        {response.result
                          ?.explanation && (
                          <div className="detail-block">

                            <span>
                              Analysis
                            </span>


                            <p>
                              {
                                response
                                  .result
                                  .explanation
                              }
                            </p>

                          </div>
                        )}


                        {/* Data Question */}

                        {response.result
                          ?.data_question && (
                          <div className="detail-block">

                            <span>
                              Data question
                            </span>


                            <p>
                              {
                                response
                                  .result
                                  .data_question
                              }
                            </p>

                          </div>
                        )}


                        {/* Document Requirement */}

                        {response.result
                          ?.document_requirement && (
                          <div className="detail-block">

                            <span>
                              Document requirement
                            </span>


                            <p>
                              {
                                response
                                  .result
                                  .document_requirement
                              }
                            </p>

                          </div>
                        )}


                        {/* SQL */}

                        {response.result
                          ?.sql && (
                          <div className="detail-block">

                            <span>
                              Generated SQL
                            </span>


                            <pre>

                              {
                                response
                                  .result
                                  .sql
                              }

                            </pre>

                          </div>
                        )}


                        {/* Confirmed Suppliers */}

                        {response.result
                          ?.confirmed_suppliers && (
                          <div className="detail-block">

                            <span>
                              Confirmed suppliers
                            </span>


                            <p>

                              {
                                response
                                  .result
                                  .confirmed_suppliers
                                  .join(
                                    ", "
                                  )
                                ||
                                "None"
                              }

                            </p>

                          </div>
                        )}

                      </div>
                    )}

                  </div>

                </div>
              )}

            </>
          )}

        </section>


        {/* ==================================================
            COPILOT COMPOSER
        ================================================== */}

        {activePage ===
          "copilot" && (
          <div className="composer-wrapper">

            <form
              className="composer"
              onSubmit={
                handleAsk
              }
            >

              <textarea
                value={
                  question
                }
                placeholder="Ask about contracts, purchase orders, inventory, shipments..."
                onChange={(
                  event
                ) =>
                  setQuestion(
                    event
                      .target
                      .value
                  )
                }
                onKeyDown={(
                  event
                ) => {

                  if (
                    event.key ===
                      "Enter"
                    &&
                    !event.shiftKey
                  ) {

                    event.preventDefault();

                    handleAsk();

                  }

                }}
                rows={1}
              />


              <button
                type="submit"
                disabled={
                  loading ||
                  !question.trim()
                }
              >

                {loading ? (
                  <Loader2
                    className="spinner"
                    size={19}
                  />
                ) : (
                  <Send
                    size={19}
                  />
                )}

              </button>

            </form>


            <div className="composer-note">

              Local AI · Your operational data
              remains on your machine

            </div>

          </div>
        )}

      </main>

    </div>
  );
}


export default App;