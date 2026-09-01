import { Link, Navigate, useParams } from "react-router-dom";
import { getIncidentById, incidents } from "../data/incidents";
import { getInvestigationDraft } from "../data/investigationDrafts";
import {
  categoryLabel,
  formatDate,
  formatUsd,
} from "../lib/format";

export function IncidentPage() {
  const { id } = useParams<{ id: string }>();
  const inc = id ? getIncidentById(id) : undefined;

  if (!inc) {
    return <Navigate to="/" replace />;
  }

  const related = (inc.relatedIds ?? [])
    .map((rid) => incidents.find((i) => i.id === rid))
    .filter(Boolean);
  const investigation = getInvestigationDraft(inc.id);

  return (
    <article className="article">
      <p className="muted">
        <Link to="/">← Timeline</Link>
      </p>
      <h1>{inc.title}</h1>
      <p className="muted">
        {formatDate(inc.date)}
        {inc.endDate ? ` – ${formatDate(inc.endDate)}` : ""}
        {" · "}
        {categoryLabel(inc.category)}
        {" · "}
        Severity: {inc.severity}
      </p>
      {inc.estimatedLossUsd !== null && (
        <p>
          <strong>Estimated loss:</strong> {formatUsd(inc.estimatedLossUsd)}
          {inc.lossDescription ? ` — ${inc.lossDescription}` : ""}
        </p>
      )}
      {inc.mitigated && (
        <p style={{ color: "var(--ok)" }}>
          Recovery / reimbursement or preemptive patch noted in sources.
        </p>
      )}

      <section className="article-section">
        <h2>Summary</h2>
        <p>{inc.summary}</p>
      </section>

      {inc.details && (
        <section className="article-section">
          <h2>Details</h2>
          <p>{inc.details}</p>
        </section>
      )}

      {inc.rootCause && (
        <section className="article-section">
          <h2>Root cause</h2>
          <p>{inc.rootCause}</p>
        </section>
      )}

      {inc.response && (
        <section className="article-section">
          <h2>Response</h2>
          <p>{inc.response}</p>
        </section>
      )}

      {inc.lesson && (
        <section className="article-section">
          <h2>Lessons learned</h2>
          <p>{inc.lesson}</p>
        </section>
      )}

      {inc.mitigations && inc.mitigations.length > 0 && (
        <section className="article-section">
          <h2>Mitigations that would have helped</h2>
          <ul className="checklist">
            {inc.mitigations.map((m, i) => (
              <li key={i}>{m}</li>
            ))}
          </ul>
        </section>
      )}

      {inc.tags.length > 0 && (
        <section className="article-section">
          <h2>Tags</h2>
          <div style={{ display: "flex", flexWrap: "wrap", gap: "0.45rem" }}>
            {inc.tags.map((t) => (
              <span key={t} className="pill">
                <code>{t}</code>
              </span>
            ))}
          </div>
        </section>
      )}

      {related.length > 0 && (
        <section className="article-section">
          <h2>Related incidents</h2>
          <ul className="related-list">
            {related.map((r) => (
              <li key={r!.id}>
                <Link to={`/incident/${r!.id}`}>{r!.title}</Link>
              </li>
            ))}
          </ul>
        </section>
      )}

      <section className="article-section">
        <h2>References</h2>
        <ol className="sources-list">
          {inc.sources.map((s) => (
            <li key={s.url}>
              <a href={s.url} target="_blank" rel="noreferrer">
                {s.label}
              </a>
            </li>
          ))}
        </ol>
      </section>

      {investigation && (
        <p className="footer-note">
          <a href={investigation.href}>On-chain investigation notes</a>
          {" — AI generated"}
        </p>
      )}
    </article>
  );
}
