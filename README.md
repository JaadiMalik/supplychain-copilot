# SupplyChain Copilot

A local AI-powered assistant for supply-chain operations.

SupplyChain Copilot combines structured operational data with supplier documents so users can ask questions in natural language across:

- Purchase orders
- Shipments
- Inventory
- Supplier contracts
- Penalty clauses
- Supplier identity mappings

The application runs locally using Qwen, Nomic embeddings, DuckDB, ChromaDB, FastAPI, and React.

---

## Overview

Supply-chain teams often work across two very different types of information:

1. Structured operational data
   - CSV
   - Excel
   - Purchase orders
   - Inventory
   - Shipments

2. Unstructured documents
   - Supplier agreements
   - Contracts
   - Policies
   - Terms and conditions

SupplyChain Copilot connects both.

Example question:

> Which open purchase orders belong to suppliers with contractual late-delivery penalties?

To answer this, the system:

1. Queries operational purchase-order data
2. Finds the suppliers involved
3. Resolves supplier aliases
4. Searches supplier contracts
5. Verifies contractual penalty clauses
6. Returns only deterministically confirmed suppliers and purchase orders

---

# Key Features

## AI Operations Copilot

Ask operational questions using natural language.

Examples:

- Which shipments are delayed?
- Which purchase orders are open?
- Which inventory items are below reorder level?
- Which suppliers have contractual late-delivery penalties?
- Which open POs belong to suppliers with confirmed penalty clauses?

---

## Structured Data Analytics

Upload:

- CSV
- XLSX

Excel workbooks can contain multiple sheets.

Each sheet is automatically converted into a DuckDB table.

The system dynamically discovers the database schema and generates SQL based on the user's question.

---

## Document RAG

Upload supplier agreements and other PDF documents.

The ingestion pipeline:

```text
PDF
 ↓
PyMuPDF
 ↓
Text extraction
 ↓
Chunking
 ↓
Nomic embeddings
 ↓
ChromaDB
 ↓
Semantic retrieval
 ↓
Qwen