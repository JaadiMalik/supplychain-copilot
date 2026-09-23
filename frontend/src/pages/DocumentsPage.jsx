import { useEffect, useRef, useState } from "react";

import {
  FileText,
  Upload,
  Trash2,
  Loader2,
  RefreshCw,
  CheckCircle2,
  AlertCircle,
} from "lucide-react";

import {
  getDocuments,
  uploadDocument,
  deleteDocument,
} from "../api";


function DocumentsPage() {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [deleting, setDeleting] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const fileInputRef = useRef(null);


  async function loadDocuments() {
    try {
      setLoading(true);
      setError("");

      const data = await getDocuments();

      /*
       * Supports either:
       *
       * { documents: [...] }
       *
       * or directly:
       *
       * [...]
       */
      const list = Array.isArray(data)
        ? data
        : data.documents || [];

      setDocuments(list);
    } catch (err) {
      setError(
        err.message ||
          "Could not load documents."
      );
    } finally {
      setLoading(false);
    }
  }


  useEffect(() => {
    loadDocuments();
  }, []);


  async function handleFileChange(event) {
    const file = event.target.files?.[0];

    if (!file) {
      return;
    }

    if (
      file.type !== "application/pdf" &&
      !file.name.toLowerCase().endsWith(".pdf")
    ) {
      setError(
        "Only PDF documents are supported."
      );

      event.target.value = "";
      return;
    }

    try {
      setUploading(true);
      setError("");
      setMessage("");

      const result =
        await uploadDocument(file);

      setMessage(
        `${file.name} uploaded and indexed successfully.`
      );

      console.log(
        "Upload result:",
        result
      );

      await loadDocuments();
    } catch (err) {
      setError(
        err.message ||
          "Could not upload document."
      );
    } finally {
      setUploading(false);

      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  }


  async function handleDelete(filename) {
    const confirmed = window.confirm(
      `Delete "${filename}"?\n\nThis will also remove its indexed chunks from the vector database.`
    );

    if (!confirmed) {
      return;
    }

    try {
      setDeleting(filename);
      setError("");
      setMessage("");

      await deleteDocument(filename);

      setMessage(
        `${filename} deleted successfully.`
      );

      await loadDocuments();
    } catch (err) {
      setError(
        err.message ||
          "Could not delete document."
      );
    } finally {
      setDeleting("");
    }
  }


  function formatBytes(bytes) {
    if (
      bytes === undefined ||
      bytes === null
    ) {
      return "—";
    }

    if (bytes < 1024) {
      return `${bytes} B`;
    }

    if (bytes < 1024 * 1024) {
      return `${(
        bytes / 1024
      ).toFixed(1)} KB`;
    }

    return `${(
      bytes /
      (1024 * 1024)
    ).toFixed(1)} MB`;
  }


  return (
    <div className="documents-page">

      {/* Header */}

      <div className="page-heading">
        <div>
          <h2>Documents</h2>

          <p>
            Upload supplier contracts, SOPs and
            operational documents for RAG analysis.
          </p>
        </div>

        <div className="document-actions">

          <button
            className="secondary-action"
            onClick={loadDocuments}
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
              ? "Indexing..."
              : "Upload PDF"}
          </button>

          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,application/pdf"
            hidden
            onChange={handleFileChange}
          />

        </div>
      </div>


      {/* Notifications */}

      {message && (
        <div className="page-message success-message">
          <CheckCircle2 size={18} />
          {message}
        </div>
      )}

      {error && (
        <div className="page-message error-message">
          <AlertCircle size={18} />
          {error}
        </div>
      )}


      {/* Stats */}

      <div className="document-stats">

        <div className="stat-card">
          <span>Indexed documents</span>

          <strong>
            {documents.length}
          </strong>
        </div>

        <div className="stat-card">
          <span>Total pages</span>

          <strong>
            {documents.reduce(
              (total, doc) =>
                total +
                (doc.pages || 0),
              0
            )}
          </strong>
        </div>

        <div className="stat-card">
          <span>Vector chunks</span>

          <strong>
            {documents.reduce(
              (total, doc) =>
                total +
                (doc.chunks || 0),
              0
            )}
          </strong>
        </div>

      </div>


      {/* Document List */}

      <div className="documents-panel">

        <div className="documents-panel-header">
          <div>
            <h3>Knowledge base</h3>

            <p>
              Documents indexed in ChromaDB
            </p>
          </div>
        </div>


        {loading ? (
          <div className="documents-loading">
            <Loader2
              className="spinner"
              size={25}
            />

            Loading documents...
          </div>
        ) : documents.length === 0 ? (
          <div className="documents-empty">

            <div className="empty-file-icon">
              <FileText size={27} />
            </div>

            <h3>
              No documents indexed
            </h3>

            <p>
              Upload your first PDF to begin
              building the document knowledge base.
            </p>

            <button
              className="primary-action"
              onClick={() =>
                fileInputRef.current?.click()
              }
            >
              <Upload size={17} />
              Upload PDF
            </button>

          </div>
        ) : (
          <div className="document-list">

            {documents.map(
              (document) => {

                const filename =
                  document.filename ||
                  document.document ||
                  document.name;

                return (
                  <div
                    className="document-row"
                    key={filename}
                  >

                    <div className="document-main">

                      <div className="document-icon">
                        <FileText
                          size={21}
                        />
                      </div>

                      <div className="document-info">
                        <strong>
                          {filename}
                        </strong>

                        <div className="document-meta">

                          <span>
                            {document.pages ||
                              0}{" "}
                            pages
                          </span>

                          <span>•</span>

                          <span>
                            {document.chunks ||
                              0}{" "}
                            chunks
                          </span>

                          {document.size_bytes !==
                            undefined && (
                            <>
                              <span>•</span>

                              <span>
                                {formatBytes(
                                  document.size_bytes
                                )}
                              </span>
                            </>
                          )}

                        </div>
                      </div>

                    </div>


                    <div className="document-status">

                      <div className="indexed-pill">
                        <CheckCircle2
                          size={13}
                        />

                        Indexed
                      </div>

                      <button
                        className="delete-document"
                        title="Delete document"
                        disabled={
                          deleting ===
                          filename
                        }
                        onClick={() =>
                          handleDelete(
                            filename
                          )
                        }
                      >
                        {deleting ===
                        filename ? (
                          <Loader2
                            size={17}
                            className="spinner"
                          />
                        ) : (
                          <Trash2
                            size={17}
                          />
                        )}
                      </button>

                    </div>

                  </div>
                );
              }
            )}

          </div>
        )}

      </div>

    </div>
  );
}


export default DocumentsPage;