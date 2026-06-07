# Health Insurance Policyholder Retention & Revenue-at-Risk Analytics

## Project Overview

An end-to-end data analytics project built on a health insurance customer dataset, focused on identifying policyholders at risk of lapsing, quantifying revenue at risk, and evaluating campaign effectiveness. The project covers the full analytics pipeline from data augmentation and cleaning through to SQL analysis, exploratory data analysis, risk scoring, campaign ROI calculation, and an executive Power BI dashboard.

---

## Business Problem

Insurance companies lose significant revenue each year when policyholders choose not to renew their policies. This project addresses three core business questions:

- Which customers are most likely to lapse and why?
- How much revenue is at risk from potential lapses?
- Which retention campaigns are most effective at reducing churn?

---

## Dataset

**Source:** Health Insurance Cross Sell Prediction (Kaggle)

**Base rows:** 381,109

**Original columns:** 12

**Augmented columns:** 9 synthetic retention-focused columns added

| Synthetic Column | Description |
|---|---|
| `claim_history` | Number of past insurance claims |
| `premium_hike_pct` | Year-over-year premium increase percentage |
| `months_since_last_interaction` | Customer engagement recency |
| `late_payments` | Number of late premium payments |
| `campaign_contacted` | Whether the customer was part of a retention campaign |
| `campaign_type` | Email, agent call, or renewal discount |
| `campaign_response` | Whether the customer responded to the campaign |
| `lapse_risk_score` | Rule-based risk tier (Low, Medium, High) |
| `renewal_status` | Target variable, whether the customer renewed (1) or lapsed (0) |

---

## Project Structure

```
health-insurance-retention-analytics/
│
├── data/
│   ├── train.csv                           # Original Kaggle dataset
│   ├── train_enriched.csv                  # Augmented dataset
│   └── train_cleaned.csv                   # Cleaned and validated dataset
│
├── notebooks/
│   ├── phase1_augmentation.py              # Data augmentation script
│   ├── Phase2_Data_Cleaning.ipynb          # Data cleaning and validation
│   ├── Exploratory_Data_Analysis.ipynb     # EDA with Matplotlib visualisations
│   ├── Phase6_Risk_Scoring_Framework.ipynb # Risk scoring validation and priority action table
│   └── Phase7_Campaign_ROI_Analysis.ipynb  # Campaign ROI calculations
│
├── sql/
│   └── SQL_Analysis_Queries.sql            # 10 business queries in PostgreSQL
│
├── dashboard/
│   └── Health_Insurance_Retention_Dashboard.pbix  # Power BI dashboard
│
└── README.md
```

---

## Tools and Technologies

| Tool | Purpose |
|---|---|
| Python (Pandas, Matplotlib) | Data augmentation, cleaning, EDA, risk scoring, ROI analysis |
| PostgreSQL (pgAdmin) | Database storage and SQL analysis |
| Power BI | Executive dashboard and visualisation |
| Jupyter Notebooks | Interactive analysis and documentation |
| GitHub | Version control and portfolio hosting |

---

## Key Findings

### Lapse and Retention

- 33.38% of policyholders lapsed, representing 3.81 billion in total revenue at risk
- Medium risk customers represent the highest revenue at risk at 2.54 billion despite a lower individual lapse rate, due to their volume of 235,533 customers
- High risk customers lapse at 68.05%, making early intervention critical

### Strongest Drivers of Lapse

- Premium hikes above 20% drive a lapse rate of 48.2%, more than double the rate for minimal hikes
- Customers crossing 4 claims experience a sharp jump in lapse rate from 38% to 49%
- Customers with no interaction for 12 or more months lapse at over 40%
- Region 28 accounts for 1.38 billion in revenue at risk, nearly 4x the next highest region

### Campaign Effectiveness

- Agent calls achieve the highest response rate at 49.3% and the lowest lapse rate at 34.5%
- Email delivers the highest ROI due to minimal cost but has the lowest response rate at 19.2%
- All three campaign types produce a renewal lift of approximately 30 percentage points when customers respond

---

## Risk Scoring Framework

A rule-based lapse risk scoring system assigns each customer a tier based on premium hike percentage, late payment history, months since last interaction, campaign non-response, and claim history.

| Risk Tier | Customers | Lapse Rate | Revenue at Risk |
|---|---|---|---|
| High | 46,991 | 68.05% | 942 million |
| Medium | 235,533 | 35.90% | 2.54 billion |
| Low | 98,585 | 10.83% | 318 million |

---

## Business Recommendations

1. Implement automated engagement triggers at the 6 month mark for disengaged customers
2. Prioritise agent calls for Medium and High risk customers
3. Conduct a dedicated regional investigation into Region 28
4. Develop a targeted retention programme for customers aged 46 and above
5. Treat premium hikes above 10% as an automatic retention trigger
6. Introduce flexible payment plans for customers with 2 or more late payments
7. Use the 4-claim threshold as an early warning system for proactive outreach

---

## Power BI Dashboard

Three-page executive dashboard covering:

- **Page 1 - Executive Retention Overview:** KPI cards and headline charts showing overall lapse rate, revenue at risk, and regional concentration
- **Page 2 - Risk Segmentation:** Lapse rate breakdowns by age group, premium hike band, claim history, and customer risk profile with Priority Action Table
- **Page 3 - Campaign Effectiveness and ROI:** Response rates, renewal lift, revenue protected, and ROI comparison across all campaign types

---

## Author

**Hrishikesh Nair**

nairhrishi932@gmail.com
