export default function AgentTrace({ trace = [] }) {
  return (
    <section className="v2-panel">
      <h3>Analysis Steps</h3>
      {trace.length === 0 ? (
        <p className="v2-muted">No tool calls were required.</p>
      ) : (
        <div className="v2-trace-list">
          {trace.map((step) => (
            <div className="v2-trace-step" key={`${step.round}-${step.tool}`}>
              <strong>Round {step.round}: {step.tool}</strong>
              <span className={`v2-status ${step.status}`}>{step.status}</span>
              {step.planner_reason && <p>{step.planner_reason}</p>}
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
