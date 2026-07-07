# Signal Metrics — research & ideation

Per-company "alternative" financial metrics for Tamara: the numbers you *don't*
see on the front page of Yahoo/Google Finance, chosen to sharpen a thesis rather
than decorate a ticker. US equities first.

This is a research/ideation doc, not a build spec. It feeds a future "signal"
building block that sits alongside the prices block.

---

## 0. The bar: what makes a metric "thoughtful" here

Front-page metrics (P/E, market cap, day change, 52-wk range, dividend yield) are
*coordinates*, not *signal*. They tell you where a stock is, not what to think.
A Tamara metric has to clear five tests — these are the anti-slop guardrails
([[anti-slop-differentiation]]) applied to numbers:

1. **The "so what" test.** Would this number, if it moved, change how you'd argue
   the thesis? If not, it's a vanity metric. Cut it.
2. **Relative, never absolute.** A number alone is noise. Show it against *its own
   history* (z-score / percentile vs the company's last 5 yrs) and *against peers*
   (percentile in sector). "SBC is 18% of revenue" is weak; "SBC is 18% of revenue
   — 92nd percentile among software, and up from 11% three years ago" is signal.
3. **Provenance.** Every metric cites where it came from (the 10-Q line, the FINRA
   file, the Form 4). This plugs straight into Tamara's `sources` model and makes
   the app trustworthy instead of another dashboard of context-free figures.
4. **A directional read.** Each metric carries a bull/bear lean *for this company*
   ("rising DSO while revenue growth slows → bear: possible channel stuffing").
   This is the "narratives take a position" principle ([[narratives-take-a-position]])
   pushed into the data layer, and it makes the model a *scorekeeper*, not a
   summarizer.
5. **Friction, not a verdict.** The best metric raises a *question* the user has to
   answer ("why did they capitalize more R&D this year?"), not a pat conclusion.
   That's the signal-producing friction the product needs.

Two more properties, product-specific:

- **Per-company adaptivity.** The metric *set* differs by company. A bank's panel
  is nothing like a pre-revenue biotech's. See §2 for the selection engine.
- **Narrative-native framing.** Show each metric two ways Tamara is uniquely placed
  to: **as-of the narrative's creation vs now** (reuses the prices block's
  `since_change` idea — did the thesis's premise actually play out?), and **vs the
  company's own history** (regime change is more interesting than the level).

---

## 1. The metric families (the wealth of ideas)

Each entry: **metric — what it reveals the front page doesn't — who it fits —
source.** Sources: `EDGAR` = free SEC XBRL companyfacts/frames; `FINRA` = free-ish
short data; `OPT-free` = computable from Yahoo option chains; `OPT-paid` = needs a
vendor; `13F/4` = free EDGAR ownership filings; `EST` = consensus/estimates
(mostly paid); `MKT` = price/volume we already ingest.

### A. Cash & capital allocation — "is the reported profit real money, and where does it go?"

- **Owner earnings / FCF conversion** (FCF ÷ net income). Reveals whether GAAP
  earnings turn into cash. <70% persistently is a yellow flag; >100% (e.g. mature
  subscription) is quality. *Fits: everyone.* `EDGAR`
- **Stock-based comp as % of revenue and % of FCF.** The single most-hidden cost in
  modern tech. "Adjusted" numbers add SBC back as if it's free; it isn't. *Fits:
  software, growth tech.* `EDGAR` (ShareBasedCompensation)
- **Buyback yield net of dilution** (shares repurchased − shares issued to comp,
  ÷ market cap). Many "buybacks" just mop up dilution and return nothing to
  holders. Net share count trend is the truth serum. *Fits: mature tech, banks,
  consumer.* `EDGAR`
- **ROIC vs WACC (economic profit spread).** Is the company creating or destroying
  value on invested capital? A growing company with ROIC < WACC is a value
  incinerator. *Fits: capital allocators, roll-ups, industrials.* `EDGAR`
- **Incremental ROIC** (ΔNOPAT ÷ Δinvested capital, trailing). Where's the *next*
  dollar going — is reinvestment still paying off, or is the flywheel slowing?
  *Fits: compounders, retail expansion stories.* `EDGAR`
- **Reinvestment runway / capex intensity** (capex ÷ sales; growth vs maintenance
  capex split). How much of "cash flow" is really required just to stand still.
  *Fits: capital-intensive, telecom, energy, semis.* `EDGAR`
- **Cash conversion cycle** (DSO + DIO − DPO). Working-capital discipline; a
  lengthening cycle can precede a cash crunch or signal demand softness. *Fits:
  retail, hardware, industrials.* `EDGAR`

### B. Earnings quality / forensic accounting — "is management massaging the numbers?"

- **Sloan accruals ratio** ((net income − CFO) ÷ total assets). High accruals →
  earnings driven by estimates, not cash → historically predict underperformance.
  *Fits: everyone; loudest for serial acquirers.* `EDGAR`
- **Beneish M-score** (8-variable earnings-manipulation model). A composite forensic
  flag; not a verdict but a "look closer." *Fits: any company with a too-clean
  chart.* `EDGAR`
- **Piotroski F-score** (9-point fundamental health). Cheap, robust quality filter,
  especially for beaten-down names. *Fits: value/turnaround theses.* `EDGAR`
- **GAAP vs non-GAAP gap** (and its trend). When "adjusted" EPS drifts ever further
  from GAAP, ask what's being excluded and why it recurs every quarter. *Fits:
  tech, biotech, anything with big "one-time" items.* `EDGAR`
- **DSO trend vs revenue growth.** Receivables growing faster than sales → pulled-
  forward or lower-quality revenue. *Fits: enterprise/B2B.* `EDGAR`
- **Days inventory + inventory ÷ sales.** Building inventory into slowing demand is
  a classic pre-writedown tell. *Fits: retail, hardware, autos, semis.* `EDGAR`
- **Deferred revenue / RPO trend.** For subscription models this is *forward* demand
  hiding on the balance sheet — often more telling than the income statement.
  *Fits: SaaS, subscription.* `EDGAR`
- **Effective tax rate anomalies.** A sudden ETR drop can flatter EPS unsustainably.
  *Fits: multinationals.* `EDGAR`

### C. Unit economics & growth quality — "is the growth healthy or bought?"

- **Rule of 40** (revenue growth % + FCF or EBITDA margin %). The canonical SaaS
  health line; below 40 and falling is a re-rating risk. *Fits: software.* `EDGAR`
- **Net revenue retention** (when disclosed) / deferred-rev-implied retention proxy.
  Expansion vs churn — the real engine of durable software growth. *Fits: SaaS.*
  `EDGAR` (often only in 10-K text / IR)
- **"Magic number" & CAC payback proxies** (Δrevenue ÷ prior S&M). Sales efficiency;
  deteriorating efficiency precedes guidance cuts. *Fits: growth SaaS, consumer.*
  `EDGAR`
- **Revenue per employee (and trend).** Operating leverage or the lack of it; useful
  cross-company scale proxy. *Fits: services, tech.* `EDGAR` (headcount in 10-K)
- **Gross margin trajectory & mix.** The cleanest read on pricing power and unit
  economics; front pages show the level, rarely the *slope*. *Fits: everyone.*
  `EDGAR`
- **Same-store / organic vs acquired growth.** Strips the M&A sugar high. *Fits:
  retail, restaurants, roll-ups.* `EDGAR` + 10-K text

### D. Balance-sheet resilience & refinancing — "what breaks it?"

- **Net debt / EBITDA + interest coverage (EBIT ÷ interest).** Standard but rarely
  front-and-center; the difference between a dip and a death spiral. *Fits:
  leveraged, cyclicals.* `EDGAR`
- **Debt maturity wall + weighted-avg coupon vs current market rate (refi risk).**
  The most underappreciated 2024–2026 metric: cheap debt maturing into a higher-
  rate world quietly re-rates FCF. *Fits: REITs, utilities, LBO'd names, telecom.*
  `EDGAR` (debt schedule in 10-K notes)
- **Altman Z-score.** Distress probability composite for the tail. *Fits: distressed/
  deep-value.* `EDGAR`
- **Lease- and pension-adjusted leverage.** Off-balance-sheet obligations that
  headline leverage misses. *Fits: retail, airlines, industrials.* `EDGAR`
- **Cash runway (quarters to zero)** = cash ÷ quarterly burn. The number that
  matters most for anything pre-profit. *Fits: biotech, early growth.* `EDGAR`

### E. Moat / durability proxies — "will it still be here in 10 years?"

- **ROIC persistence** (how many of last 10 yrs above a threshold). Durable high
  returns ≈ a moat. *Fits: compounders.* `EDGAR`
- **Gross-margin stability** (std dev over cycle). Pricing power under stress.
  *Fits: consumer staples, brands.* `EDGAR`
- **R&D capitalized vs expensed (and the swing).** Capitalizing more R&D flatters
  earnings and can mask deteriorating economics. *Fits: software, pharma.* `EDGAR`
- **Maintenance vs growth capex split.** How much "investment" is really upkeep.
  *Fits: industrials, energy, telecom.* `EDGAR` (partly estimated)

### F. Ownership, insiders & governance — "what do the people who know best do?"

- **Insider buying/selling clusters** (Form 4). *Cluster* buys by multiple insiders
  are among the higher-signal events in markets; routine 10b5-1 sales are noise —
  distinguish them. *Fits: everyone.* `13F/4`
- **Insider ownership % and change.** Skin in the game. *Fits: founder-led,
  small/mid-cap.* `13F/4` + proxy
- **13F institutional flow & concentration.** Are smart-money holders adding or
  bailing; is the register dangerously concentrated (crowded)? *Fits: everyone;
  loudest for small caps.* `13F`
- **Dual-class / voting control.** Governance risk the price ignores until it
  doesn't. *Fits: founder tech, media.* proxy/10-K
- **Executive comp alignment** (pay vs performance; dilution from comp). *Fits:
  everyone.* proxy (DEF 14A)
- **Related-party transactions & auditor changes.** Rare but high-signal red flags.
  *Fits: any "too good" story.* 10-K/8-K

### G. Options-implied positioning & sentiment — "what is the market pricing that the chart won't tell you?"

- **Implied earnings move** (from the ATM straddle nearest earnings). The market's
  own bet on how big the reaction is — frames the risk of an event thesis. *Fits:
  anything with a binary catalyst.* `OPT-free`
- **Put/call ratio (volume & open interest).** Crude fear/greed and hedging demand.
  *Fits: liquid names.* `OPT-free`
- **IV rank / IV percentile.** Is optionality cheap or expensive vs the stock's own
  history — matters for *how* to express a view. *Fits: liquid names.* `OPT-paid`
  (or self-computed from history)
- **Vol risk premium** (implied − realized vol). Persistent premium = the market
  overpays for protection here. *Fits: liquid, low-beta.* `OPT-free`+`MKT`
- **Skew** (25-delta put vs call IV). Crash fear / demand for downside protection.
  *Fits: single-stock tail risk.* `OPT-paid`
- **Term structure** (front vs back IV; backwardation = near-term event risk).
  *Fits: pre-catalyst.* `OPT-free`
- **Dealer gamma / max pain.** Where hedging flows may pin or amplify price. Use
  sparingly and label as positioning, not fundamentals. *Fits: high-OI single
  names.* `OPT-paid`
- **Borrow fee / hard-to-borrow rate.** Cost to be short — a real, tradable
  sentiment gauge. *Fits: crowded shorts.* `OPT-paid`/broker

### H. Short interest & squeeze dynamics

- **Short interest % of float + days-to-cover.** Bearish conviction and squeeze
  fuel. *Fits: contested names.* `FINRA`
- **Daily short-volume ratio** (FINRA daily short vol ÷ total). A higher-frequency
  read than the bi-monthly official SI — *with the caveat* it's off-exchange TRF
  volume and mixes market-maker hedging with directional shorting. *Fits: active
  names.* `FINRA`
- **Failures-to-deliver.** Settlement stress; niche but occasionally decisive.
  *Fits: small-cap squeezes.* SEC FTD file (free)

### I. Volume, liquidity & microstructure — "can the thesis even be traded?"

- **Dollar volume & Amihud illiquidity.** Can you get in/out without moving it;
  liquidity risk the market cap hides. *Fits: small/mid-cap.* `MKT`
- **Volume vs 20/50-day average (unusual volume flag).** Conviction behind a move.
  *Fits: everyone.* `MKT`
- **On-balance / accumulation-distribution trend.** Is volume confirming price.
  *Fits: everyone.* `MKT`
- **VWAP deviation, block-trade proxies.** Institutional footprint. *Fits: mid-cap.*
  `MKT`

### J. Attention & social — "who's watching, and is it hot money?" (handle with care)

Social is the *most* slop-prone family. Frame it strictly as **attention &
positioning**, never as fundamentals, and always paired with a skeptic's read.

- **Mention velocity & sentiment** (Reddit/WSB, StockTwits) — *change* matters more
  than level; spikes flag crowding/reflexivity. `social (API-limited/paid)`
- **Google Trends search interest** — retail attention proxy, free via pytrends.
- **News volume & tone** — narrative momentum. `news API`
- **Retail vs institutional flow proxies** (e.g. off-exchange %). Who's driving it.
- *Anti-slop framing:* these belong in a clearly-labeled "Attention (noisy)"
  section, and Tamara should treat a social spike as a *prompt to ask why*, not
  evidence. Ties to [[anti-slop-differentiation]].

### K. Expectations, revisions & reflexivity — "what's already in the price?"

- **Reverse-DCF implied growth.** What growth does today's price *require*? Reframes
  "expensive/cheap" as "plausible/implausible" — the most thesis-useful valuation
  cut there is, and it needs no consensus data. *Fits: everyone.* `EDGAR`+`MKT`
- **NTM multiple vs its own 5-yr history (z-score).** Is the re-rating the story, or
  the fundamentals? *Fits: everyone.* `MKT`+`EST`/`EDGAR`
- **Estimate-revision breadth & dispersion.** Analysts moving together (or wildly
  apart) precedes moves; dispersion = uncertainty. *Fits: covered names.* `EST`
  (paid) — approximate free via guidance-vs-actual history.
- **Earnings surprise history & guidance credibility** (beat/raise streak, guide-
  down history). *Fits: everyone.* `EDGAR`+8-K text

### L. Sector-specific packs

The overlap ends here — these are where per-company selection earns its keep.

- **Banks / financials:** net interest margin, efficiency ratio, non-performing
  loans & coverage, CET1 capital ratio, deposit beta & mix (sticky vs hot),
  tangible book value & price/TBV, net charge-offs. `EDGAR` (bank XBRL tags)
- **REITs:** FFO/AFFO (not EPS), occupancy, same-store NOI, implied cap rate,
  WALT (lease term), debt maturity ladder. `EDGAR`
- **Energy / E&P:** reserve replacement ratio, finding & development cost, netback,
  decline rate, hedge book, breakeven price. `EDGAR` + 10-K
- **Biotech / pharma:** cash runway (quarters), monthly burn, pipeline stage map &
  catalyst calendar, R&D productivity. `EDGAR` + 8-K/clinicaltrials.
- **Semiconductors:** book-to-bill, fab utilization, inventory days, capex cycle
  position. `EDGAR` + industry.
- **Insurance:** combined ratio, float growth, reserve development, investment
  yield. `EDGAR`
- **Retail / consumer:** same-store sales, sales per sq ft, inventory turns,
  e-comm mix. `EDGAR` + 10-K.
- **Subscription/telecom:** ARPU, churn, net adds, LTV/CAC, subscriber acquisition
  cost. `EDGAR` + IR.
- **Miners:** all-in sustaining cost (AISC), grade, reserve life. 10-K.
- **Airlines:** RASM, CASM (ex-fuel), load factor, ASMs. `EDGAR`.

### M. Narrative-native / time-series framing (Tamara's edge)

Not new metrics — a *lens* on the ones above that only Tamara can apply:

- **Since-thesis delta.** Every metric shown as-of the narrative's `created_at` vs
  now (reusing the prices block's `since` machinery). "You argued margins would
  expand; here's what they've done since." This is the single most differentiated,
  product-native idea in this doc.
- **Own-history z-score / percentile.** Level is boring; regime change is the story.
- **"What would have to be true" panel.** Pair reverse-DCF implied growth with the
  metric that most tests it, per company.

---

## 2. The metric-selection engine (per-company adaptivity)

The user's key requirement: *the selection differs company to company, with
overlap.* Model that as **core + sector pack + situational triggers.**

**Step 1 — classify the company** (mostly derivable from EDGAR + SIC code):

- Sector / industry (SIC → our sector pack in §1.L)
- Business model (subscription, transactional, capital-intensive, financial,
  commodity, R&D-driven)
- Lifecycle stage (pre-revenue, hypergrowth-unprofitable, growth-profitable,
  mature, declining) — inferable from revenue growth + margins + FCF sign
- Capital structure (net cash vs levered)
- Situation flags (high short interest, imminent earnings, heavy SBC/dilution,
  recent auditor change, debt wall < 24 mo, insider cluster, unusual volume)

**Step 2 — assemble the panel:**

- **Core (always, ~4–5):** FCF conversion, net share-count trend, gross-margin
  slope, ROIC−WACC, reverse-DCF implied growth. These are the universal "quality +
  expectations" spine that overlaps across every company.
- **+ Sector pack (from §1.L).**
- **+ Lifecycle overlay:** pre-revenue → cash runway/burn; hypergrowth → Rule of 40,
  SBC%, magic number; mature → buyback yield, incremental ROIC; declining →
  accruals, debt/EBITDA, Altman Z.
- **+ Situational triggers (only when live):** high SI → short pack; earnings < 2 wks
  → implied move + skew; debt wall → refi risk; insider cluster → Form 4 detail.
  These make the panel feel *alive* and specific instead of a static template.

**Worked archetypes:**

- *Unprofitable hypergrowth SaaS (e.g. a CRWV-like):* Rule of 40, SBC % of rev &
  FCF, NRR/deferred-rev trend, magic number, cash runway, gross-margin slope,
  implied earnings move. (Almost nothing from the front page.)
- *Mature cash cow (e.g. a mega-cap):* buyback yield net of dilution, FCF
  conversion, incremental ROIC, reverse-DCF implied growth, ETR anomalies, capex
  intensity.
- *Bank:* NIM, efficiency ratio, NPL & coverage, CET1, deposit beta, price/TBV.
- *Pre-revenue biotech:* cash runway, monthly burn, catalyst calendar, dilution
  history, implied move into a data readout.
- *High-short contested name:* SI % float, days-to-cover, borrow fee, daily short-
  volume ratio, accruals, cash runway, skew.
- *Capital-intensive cyclical (energy/industrial):* ROIC−WACC through cycle, maint.
  vs growth capex, net debt/EBITDA, refi wall, reserve/utilization metric.

---

## 3. Data sourcing reality (US first)

- **SEC EDGAR `companyfacts` / `frames` (FREE, no key).** The backbone. One request
  returns every XBRL-tagged fact for a company (income statement, balance sheet,
  cash flow) as JSON keyed by us-gaap concept; a nightly `companyfacts.zip` bulk
  archive exists. Families A–E, K, most of L, and insider/13F filings are all
  computable from free SEC data. This is a *huge* advantage — it means the highest-
  signal families cost Tamara nothing but code.
  ([SEC EDGAR APIs](https://www.sec.gov/search-filings/edgar-application-programming-interfaces))
  - Practical notes: map by CIK (need a ticker→CIK table, free from SEC); handle
    company-specific extension tags and tag drift across years; annual = `CY####`,
    quarterly = `CY####Q#`, instant = `CY####Q#I`.
- **FINRA short data (free-ish).** Daily short-sale *volume* files + bi-monthly
  official *short interest*. Caveat: daily files are off-exchange TRF only and mix
  market-maker hedging with directional shorts — label honestly.
  ([FINRA short data](https://www.finra.org/finra-data/browse-catalog/short-sale-volume-data))
- **Options.** Basic metrics (implied move, put/call, term structure) are
  computable *free* from Yahoo option chains (per-ticker, delayed). Advanced (IV
  rank/percentile, skew, dealer gamma, borrow) need a paid vendor —
  [Barchart](https://www.barchart.com/ondemand/api) (delayed 25–30 min),
  [ORATS](https://orats.com/data-api), [EODHD](https://eodhd.com/lp/us-stock-options-api)
  (~$100/mo). → **Tier-2 / paid; log in TODO.**
- **Estimates & revisions.** Mostly paid (consensus behind FactSet/Refinitiv/
  Zacks). Approximate free via guidance-vs-actual history from 8-Ks.
- **Social.** API-limited/paid and noisy; lowest priority, strongest guardrails.

This maps cleanly onto the tiered model already in the codebase: **US fundamentals
(free, now) → short/volume (free-ish, near) → options (paid, later) → social
(optional, latest).** Mirrors [[prices-polygon-todo]] / the tiered prices design.

---

## 4. Recommended MVP starter set (computable now, free, US)

A tight, high-signal, per-company-adaptive panel Tamara can build on the **free
SEC + FINRA + existing price** data, no paid feeds:

**Core (every US company):**
1. FCF conversion (FCF ÷ net income)
2. Net share-count trend / buyback yield net of dilution
3. Gross-margin slope (level + 3-yr trend)
4. ROIC − WACC (economic-profit spread)
5. Reverse-DCF implied growth ("what the price needs to be true")
6. Sloan accruals ratio (earnings-quality flag)

**Lifecycle/sector overlays (pick as classified):**
7. SBC % of revenue & FCF (growth tech)
8. Rule of 40 (SaaS) / cash runway (pre-profit)
9. Net debt/EBITDA + refi wall (levered)
10. Sector headline (NIM / FFO / AISC / combined ratio / …)

**Situational (only when triggered, free):**
11. Short interest % float + days-to-cover (FINRA) — when elevated
12. Insider cluster buys (Form 4) — when present

Every metric ships with: **as-of-thesis vs now**, **own-history z-score**, a
one-line **plain-language read**, a **bull/bear lean**, and a **source link** to
the filing. That packaging *is* the product; the raw numbers are commodity.

**Phasing:**
- **P1 (free, US):** EDGAR companyfacts pipeline → families A–E + reverse-DCF +
  the selection engine. Highest signal, zero data cost.
- **P2 (free-ish):** FINRA short + volume/liquidity + Form 4/13F.
- **P3 (paid):** options-implied (IV rank, skew, gamma) + consensus revisions.
- **P4 (optional, guarded):** social/attention.

---

## 5. Anti-slop guardrails (do / don't)

- **Do** show every metric relative to history and peers; **don't** show bare levels.
- **Do** attach provenance and a directional read; **don't** present a metric
  without a "so what."
- **Do** let a metric raise a question; **don't** let the model resolve it for the
  user — it's a sparring partner and scorekeeper, not an oracle
  ([[anti-slop-differentiation]]).
- **Do** label freshness/lag and data caveats (FINRA TRF-only, options delayed);
  **don't** imply precision the source doesn't have.
- **Do** cap the panel (~6–10 live metrics); **don't** dump 40 ratios — the
  curation *is* the signal.
