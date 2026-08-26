# Home loans synthetic data dictionary

The dataset represents one synthetic Australian home loan application per row.
It contains no customer names, contact details, account numbers, addresses,
government identifiers, protected attributes or free-text customer notes.

| Column | Type | Description |
|---|---|---|
| `loan_id` | string | Synthetic technical identifier. |
| `application_date` | date | Date the application was received. |
| `settlement_date` | date, nullable | Settlement date for active loans. |
| `state` | string | Australian state or territory. |
| `postcode_region` | string | Broad synthetic geography: Metro, Inner Regional or Outer Regional. |
| `property_type` | string | House, Apartment, Townhouse or Land. |
| `occupancy_type` | string | Owner Occupied or Investment. |
| `loan_purpose` | string | Purchase, Refinance, Construction or Equity Release. |
| `first_home_buyer` | boolean | Synthetic first home buyer indicator. |
| `channel` | string | Broker, Direct or Digital. |
| `loan_amount` | decimal | Original requested or originated amount in AUD. |
| `property_value` | decimal | Synthetic property value in AUD. |
| `deposit_amount` | decimal | Property value less loan amount. |
| `lvr_pct` | decimal | Loan-to-value ratio percentage. |
| `interest_rate_pct` | decimal | Synthetic annual interest rate percentage. |
| `term_years` | integer | Original loan term. |
| `repayment_type` | string | Principal and Interest or Interest Only. |
| `monthly_repayment` | decimal | Synthetic monthly repayment in AUD. |
| `application_status` | string | Active, Approved, Declined or Withdrawn. |
| `days_to_decision` | integer | Synthetic elapsed days to the recorded outcome. |
| `credit_score_band` | string | Broad synthetic score band; not a real bureau score. |
| `debt_to_income_ratio` | decimal | Synthetic debt-to-income ratio. |
| `arrears_days` | integer | Days in arrears for active loans; zero otherwise. |
| `hardship_flag` | boolean | Synthetic hardship arrangement indicator. |
| `annual_household_income` | decimal | Synthetic household income in AUD. |
| `current_balance` | decimal | Current balance for active loans; zero otherwise. |

The ingestion notebook adds:

| Derived column | Description |
|---|---|
| `application_month` | First day of the application month. |
| `settlement_month` | First day of the settlement month. |
| `is_high_lvr` | `true` when `lvr_pct >= 80`. |
| `is_in_arrears` | `true` when `arrears_days > 0`. |
| `delinquency_band` | Current, 1-29 days, 30-59 days or 60+ days. |

## Agent business definitions

- Active portfolio metrics use `application_status = 'Active'`.
- Current exposure uses `current_balance`, not `loan_amount`.
- Approval-rate denominators include Active, Approved and Declined, and exclude
  Withdrawn.
- High LVR means at least 80%.
- 30+ arrears means at least 30 arrears days.

