# test 2.4 (compact tables)

import csv
import math
import re
import random

STAKE = 20
EW_FRACTION = 1 / 5
MAX_BANKROLL = 1000
RATING_THRESHOLD = 90.0

# ----------------------------
# IO / parsing
# ----------------------------

def read_csv(filename, key_fields):
    data = {}
    try:
        with open(filename, newline='') as file:
            reader = csv.DictReader(file)
            for row in reader:
                key = tuple(row[field].strip() for field in key_fields)
                data[key] = row
    except Exception as e:
        print(f"Error reading {filename}: {e}")
    return data

def extract_places(text):
    if not text:
        return 0
    t = str(text).lower()
    m = re.search(r'(\d+)\s*place', t)
    if m:
        return int(m.group(1))
    nums = re.findall(r'\d+', t)
    return int(nums[-1]) if nums else 0

# ----------------------------
# Core finance / staking
# ----------------------------

def calc_liability(lay_odds, lay_stake):
    return round((float(lay_odds) - 1) * lay_stake, 2)

def calc_lay_stake_back_matched(back_odds, lay_odds, stake, ew=False):
    if ew:
        payout = stake * (1 + EW_FRACTION * (back_odds - 1))
    else:
        payout = stake * back_odds
    return round(payout / lay_odds, 2)

def calc_qualifying_loss(back_odds, lay_win_odds, lay_place_odds):
    total_back_stake = STAKE * 2
    lay_win_stake = calc_lay_stake_back_matched(back_odds, lay_win_odds, STAKE)
    lay_place_stake = calc_lay_stake_back_matched(back_odds, lay_place_odds, STAKE, ew=True)
    total_lay_profit = lay_win_stake + lay_place_stake
    ql = total_back_stake - total_lay_profit
    return round(ql, 2), round(lay_win_stake, 2), round(lay_place_stake, 2)

def calc_profit_on_5th(back_odds, lay_win_stake, lay_place_stake):
    """
    Scenario: horse finishes in the "extra" place (e.g., 4th when bookie pays 4, exchange pays 3).

    Bookie side:
      - The win leg loses completely.
      - The place leg pays out at EW fraction, but remember: only the profit part counts here.
        (Stake itself isn’t returned in profit calc.)
    """
    # profit from place part (no stake returned here, just the gain)
    net_bookie = STAKE * EW_FRACTION * (back_odds - 1)

    # exchange side: both lay bets win → you keep the stakes as profit
    net_exchange = lay_win_stake + lay_place_stake

    # total outcome in this "sweet spot"
    return round(net_bookie + net_exchange, 2)

def calc_bet_rating(qualifying_loss, max_ql=None, min_ql=None):
    if qualifying_loss >= 0:
        return 100.0
    if qualifying_loss <= -40:
        return 0.0
    rating = round((1 + qualifying_loss / 40) * 100, 1)
    return max(0.0, min(100.0, rating))

def calc_expected_value(qualifying_loss, profit_on_5th, ep_probability):
    ep_prob_decimal = ep_probability / 100.0
    expected_value = (ep_prob_decimal * profit_on_5th) + ((1 - ep_prob_decimal) * qualifying_loss)
    return round(expected_value, 2)

def implied_decimal_from_prob_percent(pct):
    p = pct / 100.0
    return float('inf') if p <= 0 else round(1.0 / p, 2)

def ep_break_even_pct(ql, profit_on_5th):
    denom = (profit_on_5th - ql)
    if denom <= 0:
        return float('inf')
    p = (-ql) / denom
    return max(0.0, p * 100.0)

# ----------------------------
# Market → fair strengths
# ----------------------------

def _fairize_probs_from_decimals(decimals):
    raw = [0 if d <= 0 else 1.0 / d for d in decimals]
    s = sum(raw)
    return [x / s for x in raw] if s > 0 else [0 for _ in raw]

# ----------------------------
# Plackett–Luce simulation
# ----------------------------

def _sample_finish_pl(strengths, rng):
    idxs = list(range(len(strengths)))
    strengths_left = strengths[:]
    order = []
    for _ in range(len(strengths)):
        total = sum(strengths_left)
        if total <= 0:
            i = rng.randrange(len(strengths_left))
        else:
            r = rng.random() * total
            acc = 0.0
            i = 0
            for ii, w in enumerate(strengths_left):
                acc += w
                if r <= acc:
                    i = ii
                    break
        order.append(idxs[i])
        del strengths_left[i]
        del idxs[i]
    return order

def calc_extra_place_probability_PL(back_odds, all_back_odds, exch_places, bookie_places, sims=20000, seed=42):
    if bookie_places <= exch_places:
        return 0.0
    fair_strengths = _fairize_probs_from_decimals(all_back_odds)
    try:
        horse_index = all_back_odds.index(back_odds)
    except ValueError:
        horse_index = min(range(len(all_back_odds)), key=lambda i: abs(all_back_odds[i] - back_odds))
    rng = random.Random(seed)
    target_rank = bookie_places
    hits = 0
    for _ in range(sims):
        order = _sample_finish_pl(fair_strengths, rng)
        if order.index(horse_index) + 1 == target_rank:
            hits += 1
    return round((hits / sims) * 100, 2)

# ----------------------------
# Printing (compact)
# ----------------------------

def short(s, n):
    s = str(s)
    return s if len(s) <= n else s[: max(0, n-1)] + "…"

def print_all_candidates(rows):
    """
    Compact table:
    Rank | Race(20) | Runner(18) | Back | LayW | LayP | LWin£ | LPl£ | Liab£ | QL£ | TQS | 5th£ | EP% | BE% | Gap% | EV£ | Avl | EP
    """
    print("\n All Candidates (compact):\n")
    header = (f"{'#':>2} | {'Race':<20} | {'Runner':<18} | {'Back':>5} | {'LayW':>5} | {'LayP':>5} | "
              f"{'LWin£':>6} | {'LPl£':>6} | {'Liab£':>7} | {'QL£':>6} | {'TQS':>4} | "
              f"{'5th£':>6} | {'EP%':>5} | {'BE%':>5} | {'Gap%':>5} | {'EV£':>6} | {'Avl':<3} | {'EP':<3}")
    print(header)
    print("-" * len(header))
    for e in rows:
        line = (f"{e.get('Rank', 0):>2} | {short(e['Race'],20):<20} | {short(e['Runner'],18):<18} | "
                f"{e['Back Odds']:>5.2f} | {e['Lay Win Odds']:>5.2f} | {e['Lay Place Odds']:>5.2f} | "
                f"{e['Lay Win Stake (£)']:>6.2f} | {e['Lay Place Stake (£)']:>6.2f} | "
                f"{e['Total Liability (£)']:>7.2f} | {e['Qualifying Loss (£)']:>6.2f} | "
                f"{e['Trade Quality Score']:>4.0f} | {e['Profit on 5th (£)']:>6.2f} | "
                f"{e['EP Probability']:>5.2f} | {e['EP Break-even (%)']:>5.2f} | "
                f"{e['Value Gap (%)']:>5.2f} | {e['Model EV (£)']:>6.2f} | "
                f"{('Y' if e['Available']=='Yes' else 'N'):<3} | {('Y' if e['EP Offer']=='Yep' else 'N'):<3}")
        print(line)

def print_risk_approved(rows, rating_threshold=RATING_THRESHOLD):
    print(f"\n Risk-Approved (Trade Quality Score ≥ {rating_threshold:.0f}):\n")
    selected = [e for e in rows if e["Trade Quality Score"] >= rating_threshold]
    if not selected:
        print("  (No selections with sufficient score today.)")
        return

    # Wider header and no fixed width for Execute so it prints in full
    header = (f"{'#':>2} | {'Race':<20} | {'Runner':<18} | {'Back':>5} | {'LayW':>5} | {'LayP':>5} | "
              f"{'QL£':>6} | {'5th£':>6} | {'EP%':>5} | {'BE%':>5} | {'Gap%':>5} | {'EV£':>6} | Execute")
    print(header)
    print("-" * len(header))

    for e in selected:
        execute = (f"Lay WIN @ {e['Lay Win Odds']:.2f} for £{e['Lay Win Stake (£)']:.2f}; "
                   f"Lay PLACE @ {e['Lay Place Odds']:.2f} for £{e['Lay Place Stake (£)']:.2f}")
        line = (f"{e['Rank']:>2} | {e['Race']:<20} | {e['Runner']:<18} | "
                f"{e['Back Odds']:>5.2f} | {e['Lay Win Odds']:>5.2f} | {e['Lay Place Odds']:>5.2f} | "
                f"{e['Qualifying Loss (£)']:>6.2f} | {e['Profit on 5th (£)']:>6.2f} | "
                f"{e['EP Probability']:>5.2f} | {e['EP Break-even (%)']:>5.2f} | "
                f"{e['Value Gap (%)']:>5.2f} | {e['Model EV (£)']:>6.2f} | {execute}")
        print(line)

# ----------------------------
# Main
# ----------------------------

if __name__ == "__main__":
    racecard = read_csv('racecard.csv', ['Race', 'Runner'])
    lay_win = read_csv('lay_win_odds.csv', ['Race', 'Runner'])
    lay_place = read_csv('lay_place_odds.csv', ['Race', 'Runner'])

    temp_rows = []
    qls = []

    for key in racecard:
        if key in lay_win and key in lay_place:
            rc = racecard[key]
            lw = lay_win[key]
            lp = lay_place[key]

            bookie_places = extract_places(rc.get('EW Terms', ''))
            exch_places   = extract_places(lp.get('Place Terms', ''))
            extra_place   = bookie_places > exch_places

            back_odds      = float(rc["Back Odds"])
            lay_win_odds   = float(lw["Lay Win Odds"])
            lay_place_odds = float(lp["Lay Place Odds"])

            ql, lay_win_stake, lay_place_stake = calc_qualifying_loss(back_odds, lay_win_odds, lay_place_odds)
            qls.append(ql)

            liability_win   = calc_liability(lay_win_odds, lay_win_stake)
            liability_place = calc_liability(lay_place_odds, lay_place_stake)
            total_liability = round(liability_win + liability_place, 2)

            available = "Yes" if total_liability <= MAX_BANKROLL else "No"

            temp_rows.append({
                "Race": key[0],
                "Runner": key[1],
                "Back Odds": round(back_odds, 2),
                "Lay Win Odds": round(lay_win_odds, 2),
                "Lay Place Odds": round(lay_place_odds, 2),
                "Lay Win Stake (£)": lay_win_stake,
                "Lay Place Stake (£)": lay_place_stake,
                "Bookie Places": bookie_places,
                "Exchange Places": exch_places,
                "EP Offer": "Yep" if extra_place else "Nope",
                "Qualifying Loss (£)": ql,
                "Profit on 5th (£)": calc_profit_on_5th(back_odds, lay_win_stake, lay_place_stake),
                "Total Liability (£)": total_liability,
                "Available": available
            })

    # Bounds for rating (kept for completeness)
    min_ql = min(qls) if qls else 0
    max_ql = max(qls) if qls else 1

    all_back_odds = [e["Back Odds"] for e in temp_rows]

    all_rows = []
    for e in temp_rows:
        # Score
        e["Trade Quality Score"] = calc_bet_rating(e["Qualifying Loss (£)"], max_ql, min_ql)

        # EP probability via PL simulation
        ep_pct = calc_extra_place_probability_PL(
            back_odds=e["Back Odds"],
            all_back_odds=all_back_odds,
            exch_places=e["Exchange Places"],
            bookie_places=e["Bookie Places"],
            sims=20000,
            seed=42
        )
        e["EP Probability"]  = ep_pct
        e["EP Implied Odds"] = implied_decimal_from_prob_percent(ep_pct)

        # EV + diagnostics
        model_ev = calc_expected_value(e["Qualifying Loss (£)"], e["Profit on 5th (£)"], e["EP Probability"])
        e["Model EV (£)"] = model_ev

        be_pct = ep_break_even_pct(e["Qualifying Loss (£)"], e["Profit on 5th (£)"])
        e["EP Break-even (%)"] = 0.0 if be_pct == float('inf') else be_pct
        e["Value Gap (%)"] = e["EP Probability"] - e["EP Break-even (%)"]

        all_rows.append(e)

    # Sort and rank All Candidates
    def sort_key_all(e):
        primary = e["Trade Quality Score"]
        if primary == 100.0:
            return (primary, e["Value Gap (%)"], e["EP Probability"])
        return (primary, e["Value Gap (%)"])
    all_rows.sort(key=sort_key_all, reverse=True)
    for i, e in enumerate(all_rows, 1):
        e["Rank"] = i

    # Output: All + Risk-Approved (≥90 only)
    print_all_candidates(all_rows)
    print_risk_approved(all_rows, rating_threshold=RATING_THRESHOLD)