export default function ContextPanel({ context }) {
  if (!context) return null;

  const suppliers = context.entities?.suppliers || [];
  const period = context.period || {};

  return (
    <section className="v2-panel">
      <h3>Resolved Context</h3>
      <div className="v2-chip-row">
        <span className="v2-chip">Intent: {context.intent?.name || "—"}</span>
        {context.entities?.statuses?.map((status) => (
          <span className="v2-chip" key={status}>Status: {status}</span>
        ))}
        {suppliers.map((supplier) => (
          <span className="v2-chip" key={`${supplier.matched_text}-${supplier.canonical_name}`}>
            Supplier: {supplier.canonical_name}
          </span>
        ))}
        {period.matched && (
          <span className="v2-chip">
            Period: {period.start_date} → {period.end_date}
          </span>
        )}
      </div>
    </section>
  );
}
