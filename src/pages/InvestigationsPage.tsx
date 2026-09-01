import { Link } from "react-router-dom";
import { investigationDrafts } from "../data/investigationDrafts";
import { getIncidentById } from "../data/incidents";
import { formatDate } from "../lib/format";

export function InvestigationsPage() {
  const sorted = [...investigationDrafts].sort((a, b) =>
    b.date.localeCompare(a.date),
  );

  return (
    <>
      <h2 className="page-title">Investigation drafts</h2>
      <p className="page-lede">
        On-chain IR notes for wiki incidents. These pages are{" "}
        <span className="pill">draft</span> and{" "}
        <span className="pill">not published</span> — they are not a substitute
        for the live incident articles. Every drain claim is supposed to carry a
        full signature; missing hashes are labeled as coverage gaps.
      </p>
      <p className="muted">
        {sorted.length} drafts in this batch (owner-field phishing through
        Solareum).
      </p>
      <ul className="timeline">
        {sorted.map((d) => {
          const inc = getIncidentById(d.incidentId);
          return (
            <li key={d.incidentId}>
              <article className="incident-card">
                <div className="incident-meta">
                  <span className="pill">{formatDate(d.date)}</span>
                  <span className="pill">draft</span>
                  <span className="pill">not published</span>
                </div>
                <h3>
                  <a href={d.href}>{d.title}</a>
                </h3>
                <p className="incident-summary">
                  Wiki id <code>{d.incidentId}</code>
                  {inc ? (
                    <>
                      {" · "}
                      <Link to={`/incident/${inc.id}`}>Live incident page</Link>
                    </>
                  ) : null}
                </p>
              </article>
            </li>
          );
        })}
      </ul>
    </>
  );
}
