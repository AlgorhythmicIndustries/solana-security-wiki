import { useSyncExternalStore } from "react";
import { Link, Outlet } from "react-router-dom";
import { ThemeToggle } from "./ThemeToggle";

const WIDE_SIDEBAR_MQ = "(min-width: 901px)";

function useWideSidebar() {
  return useSyncExternalStore(
    (onChange) => {
      const mq = window.matchMedia(WIDE_SIDEBAR_MQ);
      mq.addEventListener("change", onChange);
      return () => mq.removeEventListener("change", onChange);
    },
    () => window.matchMedia(WIDE_SIDEBAR_MQ).matches,
    () => true,
  );
}

const categories = [
  { id: "all", label: "All categories" },
  { id: "application", label: "Application exploits" },
  { id: "supply-chain", label: "Supply chain" },
  { id: "core-protocol", label: "Core protocol" },
  { id: "network", label: "Network / infra" },
] as const;

export function Layout() {
  const isWideSidebar = useWideSidebar();

  const secondaryNav = (
    <>
      <div className="nav-section-title">Jump to category</div>
      <ul className="nav-list">
        {categories.slice(1).map((c) => (
          <li key={c.id}>
            <Link to={`/?category=${c.id}`}>{c.label}</Link>
          </li>
        ))}
      </ul>

      <div className="nav-section-title">Core references</div>
      <ul className="nav-list">
        <li>
          <a
            href="https://collinsdefipen.medium.com/history-of-solana-security-incidents-a-deep-dive-2332d17e6375"
            target="_blank"
            rel="noreferrer"
          >
            CollinsDeFiPen (Medium)
          </a>
        </li>
        <li>
          <a
            href="https://medium.com/@manuelpz.dev/a-not-so-brief-historical-review-of-solanas-major-security-incidents-ef09867cb6bf"
            target="_blank"
            rel="noreferrer"
          >
            Manuel Pena (Medium)
          </a>
        </li>
        <li>
          <a
            href="https://www.helius.dev/blog/solana-hacks"
            target="_blank"
            rel="noreferrer"
          >
            Helius incident catalog
          </a>
        </li>
        <li>
          <a
            href="https://hacked.slowmist.io/?c=Solana"
            target="_blank"
            rel="noreferrer"
          >
            SlowMist hacked DB (Solana)
          </a>
        </li>
      </ul>

      <div className="nav-section-title">Hackathon surveys (overlap)</div>
      <p className="brand-sub" style={{ marginTop: "0.35rem" }}>
        Many entries recycle the same events; still useful for extra links &
        angles.
      </p>
      <ul className="nav-list">
        <li>
          <a
            href="https://pineanalytics.substack.com/p/the-history-of-solana-security-incidents"
            target="_blank"
            rel="noreferrer"
          >
            Pine Analytics (Substack)
          </a>
        </li>
        <li>
          <a
            href="https://medium.com/@i2032084/history-of-solana-security-incidents-hacks-halts-and-hard-lessons-13d3052297c9"
            target="_blank"
            rel="noreferrer"
          >
            Abdulmalik Abdulrashid (Medium)
          </a>
        </li>
        <li>
          <a
            href="https://medium.com/@nitin132/the-history-of-solana-security-incidents-a-comprehensive-analysis-8f217c6971e6"
            target="_blank"
            rel="noreferrer"
          >
            Nitin132 — wide source list
          </a>
        </li>
        <li>
          <a
            href="https://medium.com/@obemarton2004/raydium-exploit-1ecbf22cd682"
            target="_blank"
            rel="noreferrer"
          >
            Martin Obe — Raydium deep dive
          </a>
        </li>
        <li>
          <a
            href="https://medium.com/@samuelisaac1995/solana-security-incidents-mar-2020-apr-2025-2741069145f4"
            target="_blank"
            rel="noreferrer"
          >
            Zackmendel — data + Flipside
          </a>
        </li>
      </ul>
    </>
  );

  return (
    <div className="app-shell">
      <a href="#main-content" className="skip-link">
        Skip to content
      </a>
      <aside className="sidebar">
        <h1 className="brand">Solana Security Wiki</h1>
        <p className="brand-sub">
          A living timeline of documented incidents on Solana—apps, wallets,
          libraries, and the L1 itself.
        </p>

        <div className="nav-section-title">Explore</div>
        <ul className="nav-list">
          <li>
            <Link to="/">Incident Timeline &amp; search</Link>
          </li>
        </ul>

        <div className="nav-section-title">Articles</div>
        <ul className="nav-list">
          <li>
            <Link to="/investigations">Investigation drafts</Link>
          </li>
          <li>
            <Link to="/trends">Exploitation trends &amp; defender focus</Link>
          </li>
          <li>
            <Link to="/checklist">Defender checklist</Link>
          </li>
          <li>
            <Link to="/videos">Video resources</Link>
          </li>
          <li>
            <Link to="/resources">Miscellaneous resources</Link>
          </li>
          <li>
            <Link to="/simds">SIMDs (security)</Link>
          </li>
        </ul>

        {isWideSidebar ? (
          secondaryNav
        ) : (
          <details className="sidebar-details">
            <summary className="sidebar-details-summary">
              Categories &amp; external sources
            </summary>
            <div className="sidebar-details-body">{secondaryNav}</div>
          </details>
        )}
      </aside>
      <main id="main-content" className="main" tabIndex={-1}>
        <div className="main-top-bar">
          <ThemeToggle />
        </div>
        <Outlet />
      </main>
    </div>
  );
}
