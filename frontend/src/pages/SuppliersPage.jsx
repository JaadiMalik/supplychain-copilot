import {
  useEffect,
  useState,
} from "react";

import {
  Building2,
  Plus,
  Trash2,
  Loader2,
  RefreshCw,
  CheckCircle2,
  AlertCircle,
  ArrowRight,
  X,
} from "lucide-react";

import {
  getSupplierAliases,
  createSupplierAlias,
  deleteSupplierAlias,
} from "../api";


function SuppliersPage() {
  const [aliases, setAliases] =
    useState([]);

  const [loading, setLoading] =
    useState(true);

  const [saving, setSaving] =
    useState(false);

  const [deleting, setDeleting] =
    useState("");

  const [showForm, setShowForm] =
    useState(false);

  const [aliasName, setAliasName] =
    useState("");

  const [
    canonicalName,
    setCanonicalName,
  ] = useState("");

  const [message, setMessage] =
    useState("");

  const [error, setError] =
    useState("");


  async function loadAliases() {
    try {
      setLoading(true);
      setError("");

      const data =
        await getSupplierAliases();

      setAliases(
        data.aliases || []
      );
    } catch (err) {
      setError(
        err.message ||
          "Could not load suppliers."
      );
    } finally {
      setLoading(false);
    }
  }


  useEffect(() => {
    loadAliases();
  }, []);


  async function handleSave(
    event
  ) {
    event.preventDefault();

    if (
      !aliasName.trim() ||
      !canonicalName.trim()
    ) {
      setError(
        "Both supplier names are required."
      );

      return;
    }

    try {
      setSaving(true);
      setError("");
      setMessage("");

      await createSupplierAlias(
        aliasName.trim(),
        canonicalName.trim()
      );

      setMessage(
        "Supplier alias saved successfully."
      );

      setAliasName("");
      setCanonicalName("");
      setShowForm(false);

      await loadAliases();

    } catch (err) {
      setError(
        err.message ||
          "Could not save supplier alias."
      );
    } finally {
      setSaving(false);
    }
  }


  async function handleDelete(
    aliasName
  ) {
    const confirmed =
      window.confirm(
        `Delete supplier alias "${aliasName}"?`
      );

    if (!confirmed) {
      return;
    }

    try {
      setDeleting(aliasName);
      setError("");
      setMessage("");

      await deleteSupplierAlias(
        aliasName
      );

      setMessage(
        "Supplier alias deleted."
      );

      await loadAliases();

    } catch (err) {
      setError(
        err.message ||
          "Could not delete supplier alias."
      );
    } finally {
      setDeleting("");
    }
  }


  return (
    <div className="suppliers-page">

      {/* Header */}

      <div className="page-heading">

        <div>
          <h2>
            Supplier Registry
          </h2>

          <p>
            Map operational supplier
            names to verified legal
            contract identities.
          </p>
        </div>


        <div className="document-actions">

          <button
            className="secondary-action"
            onClick={loadAliases}
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
              setShowForm(true)
            }
          >
            <Plus size={17} />

            Add Alias
          </button>

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
            Verified aliases
          </span>

          <strong>
            {aliases.length}
          </strong>

        </div>


        <div className="stat-card">

          <span>
            Identity method
          </span>

          <strong
            style={{
              fontSize: "17px",
            }}
          >
            Explicit
          </strong>

        </div>


        <div className="stat-card">

          <span>
            Used by
          </span>

          <strong
            style={{
              fontSize: "17px",
            }}
          >
            Combined RAG
          </strong>

        </div>

      </div>


      {/* Supplier aliases */}

      <div className="documents-panel">

        <div className="documents-panel-header">

          <div>
            <h3>
              Supplier aliases
            </h3>

            <p>
              Only explicit mappings
              are treated as verified
              legal identity matches.
            </p>
          </div>

        </div>


        {loading ? (
          <div className="documents-loading">

            <Loader2
              size={25}
              className="spinner"
            />

            Loading suppliers...

          </div>
        ) : aliases.length === 0 ? (
          <div className="documents-empty">

            <div className="empty-file-icon">
              <Building2
                size={27}
              />
            </div>

            <h3>
              No supplier aliases
            </h3>

            <p>
              Add a verified mapping
              between an ERP supplier
              name and its legal
              contract identity.
            </p>


            <button
              className="primary-action"
              onClick={() =>
                setShowForm(true)
              }
            >
              <Plus size={17} />

              Add Alias
            </button>

          </div>
        ) : (
          <div className="supplier-alias-list">

            {aliases.map(
              (item) => (
                <div
                  className="supplier-alias-row"
                  key={
                    item.alias_name
                  }
                >

                  <div className="supplier-alias-main">

                    <div className="document-icon">
                      <Building2
                        size={20}
                      />
                    </div>


                    <div className="supplier-alias-names">

                      <div className="alias-name">
                        {
                          item.alias_name
                        }
                      </div>

                      <div className="alias-map">

                        <ArrowRight
                          size={13}
                        />

                        <span>
                          {
                            item.canonical_name
                          }
                        </span>

                      </div>

                    </div>

                  </div>


                  <div className="supplier-alias-actions">

                    <div className="verified-pill">

                      <CheckCircle2
                        size={13}
                      />

                      Verified

                    </div>


                    <button
                      className="delete-document"
                      title="Delete alias"
                      disabled={
                        deleting ===
                        item.alias_name
                      }
                      onClick={() =>
                        handleDelete(
                          item.alias_name
                        )
                      }
                    >
                      {deleting ===
                      item.alias_name ? (
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
              )
            )}

          </div>
        )}

      </div>


      {/* Add Alias Modal */}

      {showForm && (
        <div className="alias-modal-overlay">

          <div className="alias-modal">

            <div className="alias-modal-header">

              <div>
                <h3>
                  Add Supplier Alias
                </h3>

                <p>
                  Create an explicit,
                  verified legal-name
                  mapping.
                </p>
              </div>


              <button
                className="drawer-close"
                onClick={() =>
                  setShowForm(false)
                }
              >
                <X size={19} />
              </button>

            </div>


            <form
              onSubmit={handleSave}
              className="alias-form"
            >

              <label>
                Operational supplier
                name

                <input
                  type="text"
                  value={aliasName}
                  placeholder="Atlas Industrial"
                  onChange={(event) =>
                    setAliasName(
                      event.target.value
                    )
                  }
                />
              </label>


              <div className="alias-arrow">
                <ArrowRight
                  size={18}
                />
              </div>


              <label>
                Canonical / legal
                supplier name

                <input
                  type="text"
                  value={
                    canonicalName
                  }
                  placeholder="Atlas Industrial Supplies Ltd."
                  onChange={(event) =>
                    setCanonicalName(
                      event.target.value
                    )
                  }
                />
              </label>


              <div className="alias-warning">

                This mapping will be
                treated as a verified
                identity relationship
                during combined
                contract analysis.

              </div>


              <div className="alias-form-actions">

                <button
                  type="button"
                  className="secondary-action"
                  onClick={() =>
                    setShowForm(false)
                  }
                >
                  Cancel
                </button>


                <button
                  type="submit"
                  className="primary-action"
                  disabled={saving}
                >
                  {saving ? (
                    <Loader2
                      size={17}
                      className="spinner"
                    />
                  ) : (
                    <CheckCircle2
                      size={17}
                    />
                  )}

                  Save Alias
                </button>

              </div>

            </form>

          </div>

        </div>
      )}

    </div>
  );
}


export default SuppliersPage;