import pandas as pd
import numpy as np

# Set seed so results are reproducible — every run produces the same synthetic data.
# If you change this number, all the random values change. Keep it fixed.
np.random.seed(42)

# ── LOAD ──────────────────────────────────────────────────────────────────────
df = pd.read_csv("train.csv")
n = len(df)  # 381,109 rows — we'll use this to size every synthetic column

print(f"Loaded {n:,} rows, {df.shape[1]} columns")
print(df.columns.tolist())


# ── HELPER: map Vehicle_Age to an ordinal number ──────────────────────────────
# We need a numeric version of Vehicle_Age to drive several synthetic columns.
# Older vehicles → more claims, higher risk. This mapping encodes that logic.
vehicle_age_map = {"< 1 Year": 0, "1-2 Year": 1, "> 2 Years": 2}
vehicle_age_ord = df["Vehicle_Age"].map(vehicle_age_map)  # 0, 1, or 2


# ── 1. claim_history ──────────────────────────────────────────────────────────
# Number of past insurance claims the customer has filed.
# Logic:
#   - Older vehicles have more claims (vehicle_age_ord adds 0–2 base claims)
#   - Vehicle_Damage = Yes adds extra claim likelihood (people who had damage tend to claim)
#   - We draw from a Poisson distribution because claims are count data (0, 1, 2, ...)
#     and Poisson is the standard model for rare, independent events
#   - We clip at 0 to prevent negatives (Poisson won't produce them but safety first)

base_lambda = vehicle_age_ord + df["Vehicle_Damage"].map({"Yes": 1, "No": 0}) + 0.5
df["claim_history"] = np.random.poisson(lam=base_lambda).clip(0)


# ── 2. premium_hike_pct ───────────────────────────────────────────────────────
# Year-over-year percentage increase in the customer's premium.
# Logic:
#   - Customers with more claims get hit with larger premium hikes (actuarially accurate)
#   - Base hike is drawn from a normal distribution centred at 8% (realistic industry average)
#   - Each past claim adds ~3% on top
#   - We clip at 0 (no negative hikes) and 50 (no absurd outliers for a base dataset)

df["premium_hike_pct"] = (
    np.random.normal(loc=8, scale=4, size=n) + df["claim_history"] * 3
).clip(0, 50).round(2)


# ── 3. months_since_last_interaction ─────────────────────────────────────────
# How many months ago the customer last interacted with the insurer.
# Logic:
#   - Vintage (days as a customer) is the anchor — longer-tenured customers
#     tend to go longer between interactions (they're "set and forget")
#   - We convert Vintage to months and add noise
#   - Customers who previously responded (Response=1) are more engaged → lower recency gap
#   - Clip between 1 and 24 months (realistic CRM range)

base_recency = (df["Vintage"] / 30) * 0.4 + np.random.normal(loc=6, scale=3, size=n)
engagement_adjustment = df["Response"].map({1: -2, 0: 2})  # engaged = more recent contact
df["months_since_last_interaction"] = (
    base_recency + engagement_adjustment
).clip(1, 24).round(0).astype(int)


# ── 4. late_payments ──────────────────────────────────────────────────────────
# Number of times the customer paid their premium late.
# Logic:
#   - Younger customers (Age < 30) tend to have slightly more late payments
#   - High premium hike → financial stress → more late payments
#   - Poisson again (count data, rare events)
#   - Lambda capped low (0.5–2) because most customers pay on time

age_factor = np.where(df["Age"] < 30, 0.5, 0)
hike_factor = (df["premium_hike_pct"] / 25).clip(0, 1)  # normalise hike to 0–1 contribution
late_lambda = 0.3 + age_factor + hike_factor
df["late_payments"] = np.random.poisson(lam=late_lambda).clip(0, 8)


# ── 5. campaign_contacted ─────────────────────────────────────────────────────
# Binary flag: was this customer contacted as part of a retention campaign?
# Logic:
#   - Higher-risk customers (high premium hike, high claims) are more likely
#     to be targeted by retention teams — this mirrors real CRM logic
#   - We build a contact probability that rises with risk signals
#   - Bernoulli draw (0 or 1) based on that probability

contact_prob = (
    0.3                                          # base contact rate: 30% of all customers
    + (df["premium_hike_pct"] / 100) * 0.3      # higher hike → more likely to be contacted
    + (df["claim_history"] / 10) * 0.2          # more claims → more likely to be contacted
).clip(0, 0.85)  # cap at 85% — no insurer contacts everyone

df["campaign_contacted"] = np.random.binomial(n=1, p=contact_prob)


# ── 6. campaign_type ──────────────────────────────────────────────────────────
# What type of retention campaign was used.
# Logic:
#   - Only relevant for customers who were contacted (campaign_contacted = 1)
#   - Three types reflect real insurance retention strategies:
#       email           → low-cost, broad reach, used for low-risk customers
#       agent_call      → high-touch, used for high-value / high-risk customers
#       renewal_discount → incentive-based, used for customers likely to lapse
#   - We assign probabilities based on Annual_Premium tercile:
#       Low premium  → mostly email
#       Mid premium  → mix
#       High premium → more agent calls

campaign_types = ["email", "agent_call", "renewal_discount"]

# Compute premium tercile (0=low, 1=mid, 2=high)
premium_tercile = pd.qcut(df["Annual_Premium"], q=3, labels=[0, 1, 2]).astype(int)

def assign_campaign_type(row_idx):
    if df.loc[row_idx, "campaign_contacted"] == 0:
        return None  # not contacted → no campaign type
    t = premium_tercile.loc[row_idx]
    if t == 0:
        probs = [0.6, 0.2, 0.2]   # low premium → mostly email
    elif t == 1:
        probs = [0.35, 0.35, 0.3]  # mid premium → balanced
    else:
        probs = [0.15, 0.55, 0.3]  # high premium → mostly agent calls
    return np.random.choice(campaign_types, p=probs)

# Apply row-by-row (vectorised version would need more complexity; this is readable)
df["campaign_type"] = [assign_campaign_type(i) for i in df.index]


# ── 7. campaign_response ──────────────────────────────────────────────────────
# Did the customer respond positively to the campaign?
# Logic:
#   - Only applicable when campaign_contacted = 1
#   - Agent calls have the highest response rate (personal touch)
#   - Renewal discounts are effective for price-sensitive customers
#   - Email has the lowest response rate
#   - Previously_Insured = 0 → customer doesn't have vehicle insurance →
#     more likely to respond to a cross-sell / retention campaign
#   - Response (original col) = expressed interest → boost their campaign response probability

response_probs = {
    "email": 0.15,
    "agent_call": 0.45,
    "renewal_discount": 0.35,
    None: 0                      # not contacted → cannot respond
}

def assign_campaign_response(row_idx):
    if df.loc[row_idx, "campaign_contacted"] == 0:
        return None
    base_p = response_probs[df.loc[row_idx, "campaign_type"]]
    # Boost for engaged customers (original Response = 1)
    boost = 0.1 if df.loc[row_idx, "Response"] == 1 else 0
    # Boost for uninsured (more receptive to insurance products)
    boost += 0.05 if df.loc[row_idx, "Previously_Insured"] == 0 else 0
    p = min(base_p + boost, 0.95)
    return np.random.binomial(n=1, p=p)

df["campaign_response"] = [assign_campaign_response(i) for i in df.index]


# ── 8. lapse_risk_score ───────────────────────────────────────────────────────
# Rule-based risk tier: Low / Medium / High
# Logic (mirrors what a real retention analyst would score):
#   Each risk factor contributes points:
#     premium_hike_pct >= 15      → +2  (big hike = strong lapse signal)
#     premium_hike_pct >= 8       → +1  (moderate hike)
#     late_payments >= 3          → +2  (habitually late = disengaged)
#     late_payments >= 1          → +1
#     months_since_last_interaction >= 12 → +2  (long silence = disengaged)
#     months_since_last_interaction >= 6  → +1
#     campaign_contacted=1 but campaign_response=0 → +2 (reached but didn't bite)
#     claim_history >= 4          → +1  (high claims → premium hike → lapse risk)
#   Total score → tier:
#     0–2  → Low
#     3–5  → Medium
#     6+   → High

def compute_risk_score(row):
    score = 0

    # Premium hike factor
    if row["premium_hike_pct"] >= 15:
        score += 2
    elif row["premium_hike_pct"] >= 8:
        score += 1

    # Late payment factor
    if row["late_payments"] >= 3:
        score += 2
    elif row["late_payments"] >= 1:
        score += 1

    # Engagement recency factor
    if row["months_since_last_interaction"] >= 12:
        score += 2
    elif row["months_since_last_interaction"] >= 6:
        score += 1

    # Campaign non-response factor (strong lapse signal)
    if row["campaign_contacted"] == 1 and row["campaign_response"] == 0:
        score += 2

    # Claim history factor
    if row["claim_history"] >= 4:
        score += 1

    # Map score to tier
    if score <= 2:
        return "Low"
    elif score <= 5:
        return "Medium"
    else:
        return "High"

df["lapse_risk_score"] = df.apply(compute_risk_score, axis=1)


# ── 9. renewal_status ─────────────────────────────────────────────────────────
# TARGET VARIABLE: Did the customer renew their policy? (1 = Yes, 0 = No / Lapsed)
# Logic:
#   - This is the outcome we're predicting in Phase 6 (risk scoring)
#   - Renewal probability is driven by risk score, campaign response, and engagement
#   - High risk → low renewal probability
#   - Successful campaign response → boosts renewal probability
#   - Previously_Insured = 1 → already has insurance → more stable → higher renewal rate

risk_renewal_prob = {"Low": 0.85, "Medium": 0.60, "High": 0.30}

def assign_renewal(row):
    base_p = risk_renewal_prob[row["lapse_risk_score"]]

    # Campaign response boosts renewal
    if row["campaign_response"] == 1:
        base_p = min(base_p + 0.15, 0.97)

    # Already insured customers are stickier
    if row["Previously_Insured"] == 1:
        base_p = min(base_p + 0.05, 0.97)

    return np.random.binomial(n=1, p=base_p)

df["renewal_status"] = df.apply(assign_renewal, axis=1)


# ── SAVE ──────────────────────────────────────────────────────────────────────
output_path = "train_enriched.csv"
df.to_csv(output_path, index=False)

print(f"\n✓ Saved enriched dataset: {output_path}")
print(f"  Shape: {df.shape}")
print(f"\nNew columns added:")
new_cols = [
    "claim_history", "premium_hike_pct", "months_since_last_interaction",
    "late_payments", "campaign_contacted", "campaign_type",
    "campaign_response", "lapse_risk_score", "renewal_status"

]
for col in new_cols:
    print(f"  {col}: {df[col].dtype} | sample values: {df[col].value_counts().head(3).to_dict()}")

print(f"\nRenewal rate: {df['renewal_status'].mean():.1%}")
print(f"Lapse risk distribution:\n{df['lapse_risk_score'].value_counts()}")
