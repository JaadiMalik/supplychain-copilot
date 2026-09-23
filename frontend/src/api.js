const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  "http://127.0.0.1:8000";

export async function askCopilot(question) {
  const response = await fetch(`${API_BASE_URL}/ask`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      question,
    }),
  });

  if (!response.ok) {
    throw new Error(
      `API request failed: ${response.status}`
    );
  }

  return response.json();
}


// ==================================================
// Documents
// ==================================================

export async function getDocuments() {
  const response = await fetch(
    `${API_BASE_URL}/documents`
  );

  if (!response.ok) {
    throw new Error(
      `Failed to load documents: ${response.status}`
    );
  }

  return response.json();
}


export async function uploadDocument(file) {
  const formData = new FormData();

  formData.append("file", file);

  const response = await fetch(
    `${API_BASE_URL}/upload`,
    {
      method: "POST",
      body: formData,
    }
  );

  if (!response.ok) {
    let message = "Document upload failed.";

    try {
      const error = await response.json();
      message =
        error.detail ||
        error.message ||
        message;
    } catch {
      // Ignore invalid JSON response
    }

    throw new Error(message);
  }

  return response.json();
}


export async function deleteDocument(filename) {
  const response = await fetch(
    `${API_BASE_URL}/documents/${encodeURIComponent(
      filename
    )}`,
    {
      method: "DELETE",
    }
  );

  if (!response.ok) {
    let message = "Document deletion failed.";

    try {
      const error = await response.json();
      message =
        error.detail ||
        error.message ||
        message;
    } catch {
      // Ignore invalid JSON response
    }

    throw new Error(message);
  }

  return response.json();
}
// ==================================================
// Structured Data
// ==================================================

export async function getDatasets() {
  const response = await fetch(
    `${API_BASE_URL}/data/datasets`
  );

  if (!response.ok) {
    throw new Error(
      `Failed to load datasets: ${response.status}`
    );
  }

  return response.json();
}


export async function uploadDataset(file) {
  const formData = new FormData();

  formData.append("file", file);

  const response = await fetch(
    `${API_BASE_URL}/data/upload`,
    {
      method: "POST",
      body: formData,
    }
  );

  if (!response.ok) {
    let message = "Dataset upload failed.";

    try {
      const error = await response.json();

      message =
        error.detail ||
        error.message ||
        message;
    } catch {
      // Ignore invalid JSON
    }

    throw new Error(message);
  }

  return response.json();
}


export async function getDatasetPreview(
  tableName
) {
  const response = await fetch(
    `${API_BASE_URL}/data/datasets/${encodeURIComponent(
      tableName
    )}`
  );

  if (!response.ok) {
    throw new Error(
      `Failed to load dataset: ${response.status}`
    );
  }

  return response.json();
}
// ==================================================
// Suppliers
// ==================================================

export async function getSupplierAliases() {
  const response = await fetch(
    `${API_BASE_URL}/suppliers/aliases`
  );

  if (!response.ok) {
    throw new Error(
      `Failed to load supplier aliases: ${response.status}`
    );
  }

  return response.json();
}


export async function createSupplierAlias(
  aliasName,
  canonicalName
) {
  const response = await fetch(
    `${API_BASE_URL}/suppliers/aliases`,
    {
      method: "POST",

      headers: {
        "Content-Type":
          "application/json",
      },

      body: JSON.stringify({
        alias_name: aliasName,
        canonical_name:
          canonicalName,
      }),
    }
  );

  if (!response.ok) {
    let message =
      "Failed to save supplier alias.";

    try {
      const error =
        await response.json();

      message =
        error.detail ||
        error.message ||
        message;
    } catch {
      // Ignore invalid JSON
    }

    throw new Error(message);
  }

  return response.json();
}


export async function deleteSupplierAlias(
  aliasName
) {
  const response = await fetch(
    `${API_BASE_URL}/suppliers/aliases/${encodeURIComponent(
      aliasName
    )}`,
    {
      method: "DELETE",
    }
  );

  if (!response.ok) {
    let message =
      "Failed to delete supplier alias.";

    try {
      const error =
        await response.json();

      message =
        error.detail ||
        error.message ||
        message;
    } catch {
      // Ignore invalid JSON
    }

    throw new Error(message);
  }

  return response.json();
}
// ==================================================
// Dashboard
// ==================================================

export async function getDashboardSummary() {
  const response = await fetch(
    `${API_BASE_URL}/dashboard`
  );

  if (!response.ok) {
    throw new Error(
      `Failed to load dashboard: ${response.status}`
    );
  }

  return response.json();
}
// ==================================================
// System Health
// ==================================================

export async function getSystemHealth() {
  const response = await fetch(
    `${API_BASE_URL}/health`
  );

  if (!response.ok) {
    throw new Error(
      `Health check failed: ${response.status}`
    );
  }

  return response.json();
}