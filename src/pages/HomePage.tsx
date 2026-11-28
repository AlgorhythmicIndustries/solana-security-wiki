import { useCallback, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { TimelineRangeSlider } from "../components/TimelineRangeSlider";
import { incidents } from "../data/incidents";
import { filterIncidents } from "../lib/search";
import {
  categoryLabel,
  formatDate,
  formatUsd,
} from "../lib/format";
import type { IncidentCategory } from "../types";

function severityClass(s: string): string {
  return `pill pill-severity-${s}`;
}

export function HomePage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const categoryParam = (searchParams.get("category") ?? "all") as
    | IncidentCategory
    | "all";
  const [query, setQuery] = useState("");
  const [year, setYear] = useState<string>("all");

  const years = useMemo(() => {
    const y = new Set<string>();
    for (const i of incidents) y.add(i.date.slice(0, 4));
    return [...y].sort().reverse();
  }, []);

  const dataBounds = useMemo(() => {
    let min = incidents[0]?.date ?? "";
    let max = incidents[0]?.date ?? "";
    for (const i of incidents) {
      if (i.date < min) min = i.date;
      if (i.date > max) max = i.date;
    }
    return { min, max };
  }, []);

  const [rangeStart, setRangeStart] = useState(dataBounds.min);
  const [rangeEnd, setRangeEnd] = useState(dataBounds.max);

  const onTimelineRangeChange = useCallback((start: string, end: string) => {
    setRangeStart(start);
    setRangeEnd(end);
  }, []);

  const sorted = useMemo(
    () => [...incidents].sort((a, b) => b.date.localeCompare(a.date)),
    [],
  );

  const preDateFiltered = useMemo(
    () =>
      filterIncidents(sorted, {
        query,
        category: categoryParam,
        year,
      }),
    [sorted, query, categoryParam, year],
  );

  const filtered = useMemo(
    () =>
      filterIncidents(sorted, {
        query,
        category: categoryParam,
        year,
        dateFrom: rangeStart,
        dateTo: rangeEnd,
      }),
    [sorted, query, categoryParam, year, rangeStart, rangeEnd],
  );

  const stats = useMemo(() => {
    const byCat: Record<string, number> = {};
    for (const i of incidents) {
      byCat[i.category] = (byCat[i.category] ?? 0) + 1;
    }
    const gross = incidents.reduce((acc, i) => {
      if (i.estimatedLossUsd == null) return acc;
      return acc + i.estimatedLossUsd;
    }, 0);
    const mitigated = incidents.filter((i) => i.mitigated).length;
    return { byCat, gross, mitigated, total: incidents.length };
  }, []);

  const setCategory = (c: IncidentCategory | "all") => {
    const next = new URLSearchParams(searchParams);
    if (c === "all") next.delete("category");
    else next.set("category", c);
    setSearchParams(next);
  };

  return (
    <>
      <h2 className="page-title">Incident timeline</h2>
      <p className="page-lede">
        This site aggregates{" "}
        <strong>{stats.total} documented events</strong> from public post-mortems,
        audits, and community post-mortems (including overlapping Helius /
        Superteam hackathon write-ups). Figures are approximate; always read
        primary sources. Entries exclude common social-engineering rugs unless they
        reflect a technical vulnerability class.
      </p>
      <p className="page-lede">
        Check out <Link to="/trends">trends in Solana exploitation activity</Link>{" "}
        and a <Link to="/checklist">defender checklist</Link> distilled from
        every incident below.
      </p>

      <div className="stats-grid">
        <div className="stat-card">
          <p className="stat-value">{stats.total}</p>
          <p className="stat-label">Incidents</p>
        </div>
        <div className="stat-card">
          <p className="stat-value">{stats.mitigated}</p>
          <p className="stat-label">With recovery / patch notes</p>
        </div>
        <div className="stat-card">
          <p className="stat-value">{formatUsd(stats.gross)}</p>
          <p className="stat-label">Sum of listed USD estimates</p>
        </div>
        <div className="stat-card">
          <p className="stat-value">{stats.byCat["application"] ?? 0}</p>
          <p className="stat-label">Application layer</p>
        </div>
      </div>

      <div className="filters">
        <div className="field">
          <label htmlFor="q">Search</label>
          <input
            id="q"
            type="search"
            placeholder="wormhole, oracle, slope…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            autoComplete="off"
          />
        </div>
        <div className="field">
          <label htmlFor="cat">Category</label>
          <select
            id="cat"
            value={categoryParam}
            onChange={(e) =>
              setCategory(e.target.value as IncidentCategory | "all")
            }
          >
            <option value="all">All categories</option>
            <option value="application">Application</option>
            <option value="supply-chain">Supply chain</option>
            <option value="core-protocol">Core protocol</option>
            <option value="network">Network / infra</option>
          </select>
        </div>
        <div className="field">
          <label htmlFor="yr">Year</label>
          <select
            id="yr"
            value={year}
            onChange={(e) => setYear(e.target.value)}
          >
            <option value="all">All years</option>
            {years.map((y) => (
              <option key={y} value={y}>
                {y}
              </option>
            ))}
          </select>
        </div>
      </div>

      <TimelineRangeSlider
        dataMin={dataBounds.min}
        dataMax={dataBounds.max}
        rangeStart={rangeStart}
        rangeEnd={rangeEnd}
        onRangeChange={onTimelineRangeChange}
        dotIncidents={preDateFiltered}
      />

      <p className="muted">
        Showing <strong>{filtered.length}</strong> of {preDateFiltered.length}{" "}
        incidents in view (of {sorted.length} total), newest first. Drag the
        handles on the bar to narrow the date range; dots match your search /
        category / year filters.
      </p>

      <ul className="timeline">
        {filtered.map((inc) => (
          <li key={inc.id}>
            <article className="incident-card">
              <div className="incident-meta">
                <span className="pill">{formatDate(inc.date)}</span>
                <span className="pill">{categoryLabel(inc.category)}</span>
                <span className={severityClass(inc.severity)}>{inc.severity}</span>
                {inc.estimatedLossUsd !== null && (
                  <span className="pill">{formatUsd(inc.estimatedLossUsd)}</span>
                )}
                {inc.mitigated && (
                  <span className="pill" style={{ borderColor: "var(--ok)", color: "var(--ok)" }}>
                    mitigated / recovered
                  </span>
                )}
              </div>
              <h3>
                <Link to={`/incident/${inc.id}`}>{inc.title}</Link>
              </h3>
              <p className="incident-summary">{inc.summary}</p>
            </article>
          </li>
        ))}
      </ul>

      {filtered.length === 0 && (
        <p className="muted">No incidents match these filters.</p>
      )}

      <footer className="footer-note">
        Built for researchers and builders. If you spot a factual error or a
        missing well-sourced incident, open an issue or PR on the project
        repository. This is not legal or investment advice.
      </footer>
    </>
  );
}
