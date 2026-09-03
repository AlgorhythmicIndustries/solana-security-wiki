import { Link } from "react-router-dom";

interface Section {
  id: string;
  title: string;
  intro?: string;
  items: string[];
}

const sections: Section[] = [
  {
    id: "program",
    title: "1. Program (smart contract) hygiene",
    intro:
      "These controls would have prevented or limited the contract-bug class of incidents (Wormhole, Cashio, Crema, Loopscale, Texture, Stake Nova).",
    items: [
      "Verify every account by canonical address or PDA derivation; never trust shape alone (especially sysvars).",
      "Pin the canonical SPL Token and Token-2022 program IDs; never accept an attacker-supplied token program from remaining accounts for CPI (Aquifer-class drain path).",
      "Assert that program-owned accounts are owned by your program ID on every read.",
      "Enforce signer constraints on every privileged instruction; a passed-in 'authority' is not authentication.",
      "Use floor (not round) for outflows; assert no transaction can withdraw more value than it deposited at the same exchange rate.",
      "Property-based / invariant tests for accounting math (deposit/redeem round-trips, fee distribution, swap conservation).",
      "Lint and ban deprecated APIs (e.g., load_instruction_at) in CI.",
      "Use Anchor account constraints (`#[account(...)]`) or equivalent for ownership and address checks; do not write ad-hoc checks if the framework provides them.",
      "Run a third-party audit (Neodyme, OtterSec, Halborn, Asymmetric, Sec3, Zellic) before mainnet TVL grows; require an audit on every privileged-instruction change.",
      "Run differential / fuzz testing against attacker-supplied accounts and instruction permutations.",
      "Build and test against a current Solana feature-flag set; runtime semantics change.",
    ],
  },
  {
    id: "authorities",
    title: "2. Authority and multisig configuration",
    intro:
      "These controls would have prevented or limited Raydium, Saga DAO, Pump.fun, Credix, Step Finance, Drift, and Aquifer.",
    items: [
      "Move every program upgrade authority to a multisig (Squads or equivalent) from launch.",
      "Use a meaningful threshold (suggested minimum 3-of-5 for council, higher for treasury); never 1-of-N.",
      "Each signer on an independent, hardware-backed device, with separate trust domain.",
      "Mandatory minimum timelock on changes to the multisig itself and to upgrade authority.",
      "Mandatory timelock on changes to the collateral whitelist, oracle configuration, fee parameters, and risk parameters.",
      "Eliminate or strictly bound admin instructions: no 'mint arbitrary supply' or 'withdraw arbitrary fee' single-call paths.",
      "Document signer identities (or hashed pseudonyms) so the community can audit signer set composition.",
      "Rotate signers on any departure; revoke prior device access immediately.",
      "Keep the deploy keypair offline; do not store mainnet program keypairs on dev workstations.",
      "Track all outstanding durable-nonce accounts and treat each as a long-lived signed authorization.",
    ],
  },
  {
    id: "signing-ceremony",
    title: "3. Signing ceremony controls",
    intro:
      "Direct response to Drift, SwissBorg/Kiln, and the broader DPRK-style social-engineering pattern.",
    items: [
      "Decode every multisig payload to a human-readable form before any approval.",
      "Require an out-of-band confirmation between at least two signers before approving any non-trivial action.",
      "Designate at least one signer per ceremony as a 'devil's advocate' whose job is to look for malicious encoding.",
      "Sign on a dedicated, hardened device — not a developer laptop.",
      "Air-gap or transaction-only signing environment; no general-purpose browsing or email on signing devices.",
      "Reject any unstake / authority-change transaction whose instruction count or set exceeds the documented baseline.",
      "Maintain a signing-ceremony runbook with explicit steps; review it quarterly.",
      "Conduct quarterly tabletop exercises that simulate a contributor compromise and a counterparty social-engineering attempt.",
    ],
  },
  {
    id: "oracle-risk",
    title: "4. Oracle integration and risk parameters",
    intro:
      "These controls would have prevented or limited Mango Markets, Solend (Nov 2022), MarginFi, Nirvana, Loopscale.",
    items: [
      "Use multi-source oracles (Pyth, Switchboard) with confidence intervals; reject prices whose interval exceeds your tolerance.",
      "Reject stale prices; use Pyth's getPriceNoOlderThan-style helpers with a strict slot tolerance.",
      "Apply TWAP/VWAP windows for any price that drives borrow capacity, mint capacity, or liquidation.",
      "Per-asset borrow caps inversely proportional to spot DEX depth at acceptable slippage.",
      "Per-asset deposit caps; very low for thinly-traded or novel collateral.",
      "Isolate volatile or thinly-traded collateral into separate, smaller markets (Aave-style isolation).",
      "Per-block / per-tx liquidation rate-limits to bound cascade risk.",
      "Circuit breakers that auto-pause borrowing on > X% mark moves in Y minutes.",
      "Treat new collateral types (PTs, LSTs, RWAs) as a separate launch with its own audit and risk review.",
      "Stress-test against flash-loan + liquidity-shock scenarios pre-launch.",
    ],
  },
  {
    id: "supply-chain",
    title: "5. Supply chain and dependencies",
    intro:
      "Coverage for the @solana/web3.js, @kodane/patch-manager, npm wave, and Telegram-bot incidents.",
    items: [
      "Pin every dependency version; lockfiles committed; no wildcard ranges in production manifests.",
      "Run an SCA tool (Socket.dev, Snyk, Dependabot) on every PR with blocking severity policy.",
      "Enable npm 2FA + provenance / sigstore for any package you publish.",
      "Verify upstream package signatures (`npm audit signatures`) in CI.",
      "Maintain an internal mirror of critical dependencies; audit upstream changes before pulling.",
      "Sandbox dev environments; never sign mainnet from a workstation that pulls arbitrary packages.",
      "Restrict IDE extensions; prefer signed/verified extensions only.",
      "Independently review any code or repo shared by an external counterparty before cloning to a privileged machine.",
      "Subscribe to security advisories for every framework you use (Anchor, Agave, Pyth, etc.).",
      "Avoid handling raw private keys in any process that loads npm packages; route signing through a separate hardened service.",
    ],
  },
  {
    id: "frontend-web2",
    title: "6. Frontend, DNS, and social account hygiene",
    intro:
      "Coverage for Raydium DNS, Parcl, BONKfun, Watt Protocol, Solar, Swarms, and the broader phishing-channel pattern.",
    items: [
      "Registrar-lock the production domain; choose a registrar with hardware-2FA and human-confirmed transfer policies.",
      "Enable DNSSEC.",
      "Add a CAA DNS record restricting which CAs can issue certificates.",
      "Subscribe to certificate-transparency monitoring; alert on any new certificate issuance.",
      "Hardware-2FA on all DNS, hosting, registrar, and CDN accounts.",
      "Hardware-2FA on every X, Discord, Telegram, GitHub, npm, and email account with project access.",
      "Limit social and registrar access to a small, trained group; revoke immediately on departure.",
      "Pin frontend assets via IPFS / Arweave; publish the canonical hash on-chain or via the verified social account.",
      "Operate a status page and a verified backup channel users can cross-reference.",
      "Configure audit-log alerting in Discord (e.g., Wick) for destructive admin actions.",
      "Set up Cloudflare or equivalent DDoS protection for high-traffic events (claim sites, airdrops).",
    ],
  },
  {
    id: "endpoint",
    title: "7. Endpoint and personal-device security",
    intro:
      "Direct response to Step Finance, Drift, DEXX, Solareum, Aquifer, and the broader trend of executive-device and privileged-wallet compromise.",
    items: [
      "Hardware wallets (Ledger / Trezor) for every privileged signer; never sign from a general-purpose laptop.",
      "EDR / managed-detection on every privileged endpoint.",
      "Restrict admin software install rights; centralized device management.",
      "Full-disk encryption, screen lock, and remote-wipe enabled.",
      "Separate user accounts per role on shared machines.",
      "No reuse of personal wallets for project signing.",
      "Background and reference checks for new contributors with privileged access.",
      "Mandatory phishing-defense training; refresh annually.",
      "Treat any device that ever held a hot key as compromised on suspicion; rotate keys.",
    ],
  },
  {
    id: "backend",
    title: "8. Backend, custody, and key management",
    intro:
      "Coverage for Thunder Terminal, Solareum, DEXX, Banana Gun, Time.fun, and exchange-class incidents like Upbit.",
    items: [
      "Store credentials and signing keys in HSM/KMS or MPC; never in env files, code, or logs.",
      "Use scoped, short-lived credentials with rotation; audit every issuance.",
      "Network-isolate the signing service from the user-facing API; require mTLS between them.",
      "Per-user spend velocity limits and step-up auth for unusual flows.",
      "Hot/cold custody split with strict refill discipline and human approval above thresholds.",
      "Continuous outbound monitoring; circuit-break at thresholds.",
      "One-click 'pause withdrawals' kill switch operable by on-call engineers.",
      "Scrub sensitive data at the SDK layer; configure Sentry / analytics with allow-lists, not deny-lists.",
      "Annual third-party application pentest covering data egress paths, not just smart contracts.",
      "Reserve attestation / SOC 2-equivalent for any custodial service.",
    ],
  },
  {
    id: "monitoring",
    title: "9. Monitoring and incident response",
    intro:
      "Cuts response time when something does happen; improves detection coverage.",
    items: [
      "On-chain monitoring for authority changes, admin-only instructions, and parameter changes (Hypernative, Range, Sec3, Forta).",
      "On-chain monitoring for unusual outflows, mint/redeem rates, and pool-ratio shifts.",
      "Off-chain monitoring for cert-transparency events, DNS changes, and reachability of canonical domain.",
      "Pager rotation with a documented escalation path; out-of-band reachable.",
      "Circuit-breaker / pause mechanism callable by on-call within minutes (Brick-style).",
      "Subscribe to upstream incident channels (counterparty status pages, X) with auto-pause on alert.",
      "Maintain a published incident-response runbook covering: identify, contain, communicate, recover, post-mortem.",
      "Pre-establish relationships with stablecoin issuers, exchanges, and bridge teams for fast asset freezes.",
      "Pre-establish a relationship with a chain-analytics partner (TRM, Chainalysis, Elliptic) before you need one.",
      "Rehearse incident response with tabletop exercises at least quarterly.",
    ],
  },
  {
    id: "governance",
    title: "10. Governance and DAO operations",
    intro:
      "Coverage for Audius, Synthetify, Solend SLND1–SLND3.",
    items: [
      "High quorum thresholds; raise automatically as a function of treasury size.",
      "Mandatory timelock between proposal pass and execution.",
      "Strict allow-list of instructions a passed proposal can execute.",
      "Security council with veto power over treasury and upgrade-authority proposals.",
      "Cap voting power per wallet, or use vote-weight curves to prevent single-wallet control.",
      "Off-chain notification (email, Telegram, Discord) for every new proposal.",
      "Make every proposal payload human-readable in the UI before voting.",
      "Pre-publish a stressed-market playbook so emergency votes are not the only response option.",
    ],
  },
  {
    id: "user-protection",
    title: "11. User-protection and disclosure",
    intro:
      "Reduces user blast radius and aligns with current wallet/UX security expectations.",
    items: [
      "Publish exact transaction shapes users will be asked to sign for claims, swaps, governance.",
      "Default token approvals to bounded amounts (not unlimited) wherever possible.",
      "Surface security guidance and bookmarkable canonical URLs in onboarding.",
      "Recommend hardware wallets in-product for users above an asset threshold.",
      "Provide an in-product way to revoke prior token approvals.",
      "Maintain a public bug bounty (Immunefi or equivalent) with clear scope and payout floor that incentivizes disclosure over exploitation.",
      "Maintain an insurance fund or partner with a coverage provider; size and policy disclosed publicly.",
      "Publish post-mortems on every incident, including narrowly-averted ones.",
    ],
  },
];

export function ChecklistPage() {
  return (
    <article className="article">
      <p className="muted">
        <Link to="/">← Timeline</Link>
      </p>
      <h1>Solana defender checklist</h1>
      <p className="muted">
        A condensed, opinionated list of configuration, process, and setup
        items that teams building on Solana should consider before mainnet and
        re-review on a regular cadence. Items are mapped to incident classes
        documented elsewhere on this site.
      </p>

      <div className="callout">
        <p>
          <strong>How to use this:</strong> walk each section with your team
          and produce a short written justification for any item you do not
          adopt. The checklist is intentionally maximalist — small teams will
          deprioritize, but the deprioritization should be deliberate.
        </p>
      </div>

      <aside className="toc">
        <h3>Sections</h3>
        <ol>
          {sections.map((s) => (
            <li key={s.id}>
              <a href={`#${s.id}`}>{s.title.replace(/^\d+\.\s*/, "")}</a>
            </li>
          ))}
        </ol>
      </aside>

      {sections.map((s) => (
        <section key={s.id} id={s.id} className="article-section">
          <h2>{s.title}</h2>
          {s.intro && <p>{s.intro}</p>}
          <ul className="checklist">
            {s.items.map((item, i) => (
              <li key={i}>{item}</li>
            ))}
          </ul>
        </section>
      ))}

      <section className="article-section">
        <h2>Further reading inside this wiki</h2>
        <ul>
          <li>
            <Link to="/trends">Trends in Solana exploitation activity</Link>{" "}
            — what defenders should focus on right now.
          </li>
          <li>
            <Link to="/?category=application">All application-layer incidents</Link>
          </li>
          <li>
            <Link to="/?category=supply-chain">All supply-chain incidents</Link>
          </li>
          <li>
            <Link to="/?category=core-protocol">All core-protocol incidents</Link>
          </li>
          <li>
            <Link to="/?category=network">All network / infrastructure incidents</Link>
          </li>
        </ul>
      </section>
    </article>
  );
}
