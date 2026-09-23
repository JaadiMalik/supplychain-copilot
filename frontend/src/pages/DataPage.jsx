import {
  useEffect,
  useRef,
  useState,
} from "react";

import {
  Database,
  Upload,
  Loader2,
  RefreshCw,
  CheckCircle2,
  AlertCircle,
  Table2,
  ChevronRight,
  X,
} from "lucide-react";

import {
  getDatasets,
  uploadDataset,
  getDatasetPreview,
} from "../api";


function DataPage() {
  const [datasets, setDatasets] =
    useState([]);

  const [loading, setLoading] =
    useState(true);

  const [uploading, setUploading] =
    useState(false);

  const [error, setError] =
    useState("");

  const [message, setMessage] =
    useState("");

  const [
    selectedDataset,
    setSelectedDataset,
  ] = useState(null);

  const [
    previewLoading,
    setPreviewLoading,
  ] = useState(false);

  const fileInputRef =
    useRef(null);


  // ==================================================
  // Load datasets
  // ==================================================

  async function loadDatasets() {
    try {
      setLoading(true);
      setError("");

      const data =
        await getDatasets();

      const list = Array.isArray(data)
        ? data
        : data.datasets || [];

      setDatasets(list);

    } catch (err) {
      setError(
        err.message ||
          "Could not load datasets."
      );
    } finally {
      setLoading(false);
    }
  }


  useEffect(() => {
    loadDatasets();
  }, []);


  // ==================================================
  // Upload
  // ==================================================

  async function handleFileChange(
    event
  ) {
    const file =
      event.target.files?.[0];

    if (!file) {
      return;
    }

    const lowerName =
      file.name.toLowerCase();

    const valid =
      lowerName.endsWith(".csv") ||
      lowerName.endsWith(".xlsx");

    if (!valid) {
      setError(
        "Only CSV and XLSX files are supported."
      );

      event.target.value = "";
      return;
    }

    try {
      setUploading(true);
      setError("");
      setMessage("");

      await uploadDataset(file);

      setMessage(
        `${file.name} uploaded successfully.`
      );

      await loadDatasets();

    } catch (err) {
      setError(
        err.message ||
          "Could not upload dataset."
      );
    } finally {
      setUploading(false);

      if (fileInputRef.current) {
        fileInputRef.current.value =
          "";
      }
    }
  }


  // ==================================================
  // Preview
  // ==================================================

  async function openPreview(
    tableName
  ) {
    try {
      setPreviewLoading(true);
      setError("");

      const data =
        await getDatasetPreview(
          tableName
        );

      setSelectedDataset(data);

    } catch (err) {
      setError(
        err.message ||
          "Could not load preview."
      );
    } finally {
      setPreviewLoading(false);
    }
  }


  // ==================================================
  // Stats
  // ==================================================

  const totalRows =
    datasets.reduce(
      (total, item) =>
        total +
        (item.row_count || 0),
      0
    );


  const totalColumns =
    datasets.reduce(
      (total, item) =>
        total +
        (item.columns?.length || 0),
      0
    );


  return (
    <div className="data-page">

      {/* Header */}

      <div className="page-heading">

        <div>
          <h2>
            Structured Data
          </h2>

          <p>
            Upload CSV and Excel
            operational data for
            DuckDB analytics.
          </p>
        </div>


        <div className="document-actions">

          <button
            className="secondary-action"
            onClick={
              loadDatasets
            }
            disabled={loading}
          >
            <RefreshCw
              size={16}
              className={
                loading
                  ? "spinner"
                  : ""
              }
            />

            Refresh
          </button>


          <button
            className="primary-action"
            onClick={() =>
              fileInputRef.current?.click()
            }
            disabled={uploading}
          >

            {uploading ? (
              <Loader2
                size={17}
                className="spinner"
              />
            ) : (
              <Upload size={17} />
            )}

            {uploading
              ? "Importing..."
              : "Upload Data"}

          </button>


          <input
            ref={fileInputRef}
            type="file"
            accept=".csv,.xlsx"
            hidden
            onChange={
              handleFileChange
            }
          />

        </div>

      </div>


      {/* Messages */}

      {message && (
        <div className="page-message success-message">

          <CheckCircle2
            size={18}
          />

          {message}

        </div>
      )}


      {error && (
        <div className="page-message error-message">

          <AlertCircle
            size={18}
          />

          {error}

        </div>
      )}


      {/* Stats */}

      <div className="document-stats">

        <div className="stat-card">
          <span>
            DuckDB tables
          </span>

          <strong>
            {datasets.length}
          </strong>
        </div>


        <div className="stat-card">
          <span>
            Total rows
          </span>

          <strong>
            {totalRows}
          </strong>
        </div>


        <div className="stat-card">
          <span>
            Total columns
          </span>

          <strong>
            {totalColumns}
          </strong>
        </div>

      </div>


      {/* Dataset panel */}

      <div className="documents-panel">

        <div className="documents-panel-header">

          <div>
            <h3>
              Operational datasets
            </h3>

            <p>
              Tables available to
              SupplyChain Copilot
            </p>
          </div>

        </div>


        {loading ? (
          <div className="documents-loading">

            <Loader2
              size={25}
              className="spinner"
            />

            Loading datasets...

          </div>
        ) : datasets.length ===
          0 ? (
          <div className="documents-empty">

            <div className="empty-file-icon">
              <Database
                size={27}
              />
            </div>

            <h3>
              No structured data
            </h3>

            <p>
              Upload a CSV or XLSX
              workbook to create your
              first DuckDB dataset.
            </p>


            <button
              className="primary-action"
              onClick={() =>
                fileInputRef.current?.click()
              }
            >
              <Upload size={17} />

              Upload Data
            </button>

          </div>
        ) : (
          <div className="dataset-list">

            {datasets.map(
              (dataset) => (
                <button
                  key={
                    dataset.table_name
                  }
                  className="dataset-row"
                  onClick={() =>
                    openPreview(
                      dataset.table_name
                    )
                  }
                >

                  <div className="dataset-main">

                    <div className="document-icon">
                      <Table2
                        size={20}
                      />
                    </div>


                    <div className="dataset-info">

                      <strong>
                        {
                          dataset.table_name
                        }
                      </strong>


                      <div className="document-meta">

                        <span>
                          {
                            dataset.row_count
                          }{" "}
                          rows
                        </span>

                        <span>•</span>

                        <span>
                          {
                            dataset.columns
                              ?.length || 0
                          }{" "}
                          columns
                        </span>

                        {dataset.sheet_name && (
                          <>
                            <span>
                              •
                            </span>

                            <span>
                              Sheet:{" "}
                              {
                                dataset.sheet_name
                              }
                            </span>
                          </>
                        )}

                      </div>


                      <div className="dataset-source">
                        {
                          dataset.source_file
                        }
                      </div>

                    </div>

                  </div>


                  <ChevronRight
                    size={18}
                  />

                </button>
              )
            )}

          </div>
        )}

      </div>


      {/* ==================================================
          Preview Drawer
      ================================================== */}

      {(selectedDataset ||
        previewLoading) && (
        <div className="preview-overlay">

          <div className="preview-drawer">

            {previewLoading ? (
              <div className="preview-loading">

                <Loader2
                  size={26}
                  className="spinner"
                />

                Loading preview...

              </div>
            ) : (
              <>
                <div className="preview-header">

                  <div>
                    <h3>
                      {
                        selectedDataset
                          ?.table_name
                      }
                    </h3>

                    <p>
                      {
                        selectedDataset
                          ?.source_file
                      }
                    </p>
                  </div>


                  <button
                    className="drawer-close"
                    onClick={() =>
                      setSelectedDataset(
                        null
                      )
                    }
                  >
                    <X size={19} />
                  </button>

                </div>


                {/* Columns */}

                <div className="preview-section">

                  <div className="section-label">
                    Columns
                  </div>


                  <div className="column-list">

                    {selectedDataset?.columns?.map(
                      (column) => (
                        <div
                          className="column-chip"
                          key={
                            column.name
                          }
                        >
                          <strong>
                            {
                              column.name
                            }
                          </strong>

                          <span>
                            {
                              column.dtype
                            }
                          </span>
                        </div>
                      )
                    )}

                  </div>

                </div>


                {/* Rows */}

                <div className="preview-section">

                  <div className="section-label">
                    Preview
                  </div>


                  <div className="table-scroll">

                    <table className="data-preview-table">

                      <thead>
                        <tr>

                          {selectedDataset?.columns?.map(
                            (
                              column
                            ) => (
                              <th
                                key={
                                  column.name
                                }
                              >
                                {
                                  column.name
                                }
                              </th>
                            )
                          )}

                        </tr>
                      </thead>


                      <tbody>

                        {selectedDataset?.preview?.map(
                          (
                            row,
                            rowIndex
                          ) => (
                            <tr
                              key={
                                rowIndex
                              }
                            >

                              {selectedDataset.columns.map(
                                (
                                  column
                                ) => (
                                  <td
                                    key={
                                      column.name
                                    }
                                  >
                                    {row[
                                      column
                                        .name
                                    ] ===
                                      null ||
                                    row[
                                      column
                                        .name
                                    ] ===
                                      undefined ||
                                    row[
                                      column
                                        .name
                                    ] ===
                                      "NaT"
                                      ? "—"
                                      : String(
                                          row[
                                            column
                                              .name
                                          ]
                                        )}
                                  </td>
                                )
                              )}

                            </tr>
                          )
                        )}

                      </tbody>

                    </table>

                  </div>

                </div>

              </>
            )}

          </div>

        </div>
      )}

    </div>
  );
}


export default DataPage;