export interface InvestigationDraft {
  incidentId: string;
  title: string;
  date: string;
  href: string;
  status: "draft";
  published: false;
}

/** Static HTML IR drafts served from /investigations/. Not live wiki articles. */
export const investigationDrafts: InvestigationDraft[] = [
  {
    incidentId: "solana-owner-field-phishing-late-2025",
    title: "Owner-field phishing (Oct 2025)",
    date: "2025-10-01",
    href: "/investigations/owner-reassignment-phishing-investigation.html",
    status: "draft",
    published: false,
  },
  {
    incidentId: "swissborg-kiln-sol-staking-sep-2025",
    title: "SwissBorg / Kiln SOL staking",
    date: "2025-09-08",
    href: "/investigations/swissborg-kiln-investigation.html",
    status: "draft",
    published: false,
  },
  {
    incidentId: "aqua-rug-sep-2025",
    title: "Aqua rug",
    date: "2025-09-08",
    href: "/investigations/aqua-investigation.html",
    status: "draft",
    published: false,
  },
  {
    incidentId: "credix-rug-aug-2025",
    title: "CrediX (Sonic, not Solana CRDx)",
    date: "2025-08-04",
    href: "/investigations/credix-investigation.html",
    status: "draft",
    published: false,
  },
  {
    incidentId: "kodane-patch-manager-npm-jul-2025",
    title: "@kodane/patch-manager",
    date: "2025-07-28",
    href: "/investigations/kodane-patch-manager-investigation.html",
    status: "draft",
    published: false,
  },
  {
    incidentId: "swarms-discord-jul-2025",
    title: "Swarms Discord",
    date: "2025-07-21",
    href: "/investigations/swarms-discord-investigation.html",
    status: "draft",
    published: false,
  },
  {
    incidentId: "texture-lending-jul-2025",
    title: "Texture lending",
    date: "2025-07-09",
    href: "/investigations/texture-lending-investigation.html",
    status: "draft",
    published: false,
  },
  {
    incidentId: "cetus-sui-exploit-may-2025-see-also",
    title: "Cetus cross-chain note (Sui)",
    date: "2025-05-22",
    href: "/investigations/cetus-crosschain-note-investigation.html",
    status: "draft",
    published: false,
  },
  {
    incidentId: "loopscale-oracle-apr-2025",
    title: "Loopscale RateX",
    date: "2025-04-26",
    href: "/investigations/loopscale-ratex-investigation.html",
    status: "draft",
    published: false,
  },
  {
    incidentId: "timefun-backend-signing-mar-2025",
    title: "Time.fun disclosure",
    date: "2025-03-01",
    href: "/investigations/timefun-investigation.html",
    status: "draft",
    published: false,
  },
  {
    incidentId: "npm-malware-jan-2025",
    title: "npm malware wave 2025",
    date: "2025-01-15",
    href: "/investigations/npm-malware-wave-2025-investigation.html",
    status: "draft",
    published: false,
  },
  {
    incidentId: "noones-bridge-jan-2025",
    title: "NoOnes bridge",
    date: "2025-01-01",
    href: "/investigations/noones-bridge-investigation.html",
    status: "draft",
    published: false,
  },
  {
    incidentId: "solana-web3js-supply-chain-dec-2024",
    title: "@solana/web3.js npm",
    date: "2024-12-03",
    href: "/investigations/solana-web3js-npm-investigation.html",
    status: "draft",
    published: false,
  },
  {
    incidentId: "dexx-key-leak-nov-2024",
    title: "DEXX",
    date: "2024-11-16",
    href: "/investigations/dexx-investigation.html",
    status: "draft",
    published: false,
  },
  {
    incidentId: "banana-gun-sep-2024",
    title: "Banana Gun",
    date: "2024-09-19",
    href: "/investigations/banana-gun-investigation.html",
    status: "draft",
    published: false,
  },
  {
    incidentId: "parcl-dns-aug-2024",
    title: "Parcl DNS",
    date: "2024-08-20",
    href: "/investigations/parcl-dns-investigation.html",
    status: "draft",
    published: false,
  },
  {
    incidentId: "solana-elf-alignment-aug-2024",
    title: "ELF loader",
    date: "2024-08-08",
    href: "/investigations/elf-loader-investigation.html",
    status: "draft",
    published: false,
  },
  {
    incidentId: "pumpfun-insider-may-2024",
    title: "Pump.fun insider",
    date: "2024-05-16",
    href: "/investigations/pumpfun-insider-investigation.html",
    status: "draft",
    published: false,
  },
  {
    incidentId: "ionet-gpu-spoofing-apr-2024",
    title: "io.net spoof",
    date: "2024-04-18",
    href: "/investigations/ionet-spoof-investigation.html",
    status: "draft",
    published: false,
  },
  {
    incidentId: "solareum-telegram-mar-2024",
    title: "Solareum Telegram",
    date: "2024-03-29",
    href: "/investigations/solareum-telegram-investigation.html",
    status: "draft",
    published: false,
  },
];

export function getInvestigationDraft(
  incidentId: string,
): InvestigationDraft | undefined {
  return investigationDrafts.find((d) => d.incidentId === incidentId);
}
