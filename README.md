# extra-place-screener

## QUICK SUMMARY
-  **What it is:** A calculator-only model that evaluates “Extra Place” horse-racing structures.  
-  **Risk-first:** Uses Qualifying Loss (QL) and liability caps to filter opportunities.  
-  **Positive EV logic:** Explicit break-even probabilities, value gaps, and model EV to identify long-term favourable setups.  
-  **Systematic, not gambling:** Typical QL = £2–£3 for potential payoffs 10–100× higher; multiple horses per race can be risk-approved; variance smooths out over many runs.  
-  **Why it matters:** Shows how small, controlled losses can be structured into a long-term positive expectation model, with transparent, auditable maths.  

# Extra Place Screener — Decision Support “Brain”

## Purpose
This repository contains a **calculator-only model** that evaluates “Extra Place” horse-racing structures.  
It is built to demonstrate **risk-first thinking**, **positive EV logic**, and **decision-support modelling** rather than any operational betting.

- **Inputs:** fixed CSV files (racecard, lay odds).  
- **Outputs:** transparent tables ranking opportunities, with a risk-approved shortlist.  
- **No live APIs, no wallets, no order placement.** This is the *brain/calculator layer* only (reproducible, auditable, and gambling-free.)

---

## 1) What is an Extra Place and why does it create edge?
An **each-way bet** is two bets at the bookmaker:
- **Win leg:** horse must win.  
- **Place leg:** horse must finish in the paid places.

Normally, both bookmaker and exchange pay (e.g., top 4). Sometimes the bookmaker offers **one extra place** (e.g., top 5).  
If your horse finishes exactly in that extra slot:

- **Bookmaker:** place bet wins (pays top 5).  
- **Exchange:** lay bet wins (you laid top 4, horse was 5th).  

This overlap creates a **positive tail outcome**: both sides pay simultaneously.  
All other outcomes typically cost a **small, controlled Qualifying Loss (QL)**. The edge comes from whether the probability of landing in that extra place outweighs the frequent small losses → **positive Expected Value (EV).**

---

## 2) Risk framing — how risk is implemented
This repo was designed with **risk-first principles**:

- **No operational risk:** only fixed CSVs, no bookmaker/exchange connections.  
- **Liability caps:** selections exceeding a bankroll cap are filtered out.  
- **QL as risk proxy:** QL represents the typical small loss when EP does not hit. Lower QL = less capital risked per attempt.  
- **Trade Quality Score (0–100):** monotone in QL, used as the first filter before considering edge.  
- **Risk-Approved list:** only candidates with Score ≥ 90 appear, each with full lay execution instructions.

This mirrors how a risk committee might gate opportunities: **is risk acceptable before chasing edge?**

---

## 3) How positive EV is calculated
The model explicitly computes **edge vs. break-even**:

**Step A — Market-consistent probabilities**  
- Convert decimal odds into implied probabilities (1/odds).  
- Remove overround by renormalising across the field.  
- These become fair “strengths” for each runner.  

**Step B — EP probability (EP%)**  
- Use a **Plackett–Luce simulation** of race finish order.  
- Estimate Pr(horse finishes exactly in the extra place).  
- This is the asymmetric payoff outcome.  

**Step C — Cashflows & QL**  
- Lay stakes are sized to match bookmaker payouts leg-by-leg.  
- Compute liabilities and the qualifying loss (QL).  

**Step D — Break-even, value gap, EV**  
- **Profit on EP hit:** bookmaker place profit + both lay stakes.  
- **Break-even EP%:** probability required to offset QL.  
- **Value gap:** model EP% – break-even EP%.  
- **Model EV (£):** EV = (EP% × Profit_onEP) + ((1 – EP%) × QL)


A selection is **only attractive if:**
- QL is small (low risk),  
- EP% > break-even probability,  
- EV ≥ 0.

---

## 4) Long-term EV logic
- A typical “risk-approved” trade (Score ≥ 90) might show a **QL of £2–£3**.  
- If the horse lands in the extra place, the **profit is often 10×–100× that loss** (£20–£200+).  
- Multiple horses can be backed in the same race (if rated ≥ 90), further increasing the chance of hitting the asymmetric outcome.  
- Over many iterations, this produces a **positive expectation game**, not gambling.  

This is the same principle used in professional trading: **small, capped downside vs. asymmetric upside, repeated systematically.**

---

## 5) Why this is gambling-free
This repository is not a betting bot. It is a **calculator**:

- Reads fixed CSVs.  
- Performs transparent computations.  
- Outputs tables for audit.  

There are **no live bets, no hidden integrations, no side effects**.  

Importantly, the underlying strategy is **matched betting**, which is fundamentally different from gambling:  
- It hedges bookmaker bets against exchange lays, eliminating speculative exposure.  
- Losses are capped and predictable (Qualifying Loss).  
- Positive outcomes (Extra Place hits) create asymmetric profit opportunities.  
- Over many iterations, the expected value is positive, not chance-driven.  

The purpose here is to showcase **risk-modelling and decision-support logic** — not to gamble — in a way that can be extended to other systematic domains (e.g, trading, research...)
---

## 6) Key Takeaways
- **Risk is first-class:** trades are filtered by liability and QL before EV is even considered.  
- **Edge is explicit:** break-even thresholds vs. market-consistent probabilities.  
- **Reproducible:** fixed seed, pure stdlib, auditable outputs.  
- **Extendable:** the same framework could and has driven live systems (APIs, portfolio optimisation, CI testing), however I have not published here.  

This is a demonstration of **systematic edge detection under risk constraints**, framed in a transparent, auditable way.

---

## 7) Inputs & outputs
**Inputs (CSV):**
- `racecard.csv` → Race, Runner, Back Odds, EW Terms  
- `lay_win_odds.csv` → Race, Runner, Lay Win Odds  
- `lay_place_odds.csv` → Race, Runner, Lay Place Odds, Place Terms  

**Outputs:**
- **All Candidates (compact):** full diagnostics (QL, liability, EP%, EV, etc.).  
- **Risk-Approved (≥ 90 Score):** shortlist with full lay instructions.  

See [`examples/output_demo.txt`](examples/output_demo.txt) for a captured run.

---

## 8) Assumptions & limitations
- Market-only priors (no form/history data).  
- EP% is estimated via simulation; no uncertainty bands here.  
- Execution frictions (commission, slippage) not modelled.  
- This is not advice; it’s a demonstrator.

---

## 9) Running the calculator
Requires Python 3.8+ (stdlib only). Place the three CSVs in the repo root or adjust paths.

```bash
# macOS/Linux
python src/extra_place_screener.py > examples/output_demo.txt

# Windows (cmd.exe)
python src\extra_place_screener.py > examples\output_demo.txt  
