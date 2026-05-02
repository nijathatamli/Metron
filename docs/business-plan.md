# Metron — Business & Product Plan

> **Prepared for Series A investors**
> Baku, Azerbaijan · 2024

---

## Task 1 — Partner Onboarding Flow

### A) Registration Process

| Step | Action | Details | Duration |
|------|--------|---------|----------|
| 1 | **Application** | Partner visits `partners.metron.az` or scans a Metron sales rep's QR code. Fills in: business name, legal entity name, TIN (VÖEN), category, address, contact person, phone, email. | 5 min |
| 2 | **Document Upload** | Uploads: (a) Business license / DSMF registration extract, (b) Bank account details (IBAN, bank name, SWIFT), (c) Photo of storefront. Optional: menu/price list for category tagging. | 5 min |
| 3 | **Automated Pre-check** | System validates VÖEN against the Tax Ministry public registry, checks for duplicates, and flags incomplete submissions. Auto-approved if all documents parse correctly. | Instant |
| 4 | **Manual Review** | Metron ops team verifies: (a) business is physically operational, (b) bank account matches legal entity, (c) category is appropriate. For Tier 3 (API) partners, a technical onboarding call is scheduled. | 1–2 business days |
| 5 | **Approval & Kit Delivery** | Partner receives: welcome email with dashboard credentials, branded QR stand (acrylic table stand + window sticker), integration guide for their tier. | 1–3 business days (courier) |
| 6 | **Go-Live** | Partner activates their profile on the dashboard. First test transaction with a Metron team member. Partner appears in the user app's store map. | Same day |

**Total onboarding time: 3–5 business days** from application to live transactions.

---

### B) Technical Integration Tiers

#### Tier 1 — QR Code Only (Zero Tech)

**Flow:**
1. Customer opens Metron app → taps "Redeem" → enters product price
2. Customer shows the generated payment QR to the cashier
3. Cashier scans the QR with their personal phone (Metron Partner app) or the customer scans the partner's static QR
4. Both screens confirm: coins deducted, cash remainder displayed
5. Customer pays the cash remainder via card/cash to the partner directly

**Target partner:** Small cafes, street food vendors, single-location shops with no POS system. Estimated 70% of initial partners.

| Pros | Cons |
|------|------|
| Zero hardware cost | Manual confirmation per transaction |
| Works on any smartphone | Cashier must have phone accessible |
| Onboarding in < 1 hour | No automated reconciliation |
| No internet requirement on partner side (offline QR validation with signed tokens) | Slightly slower checkout (~15 sec overhead) |

---

#### Tier 2 — Web Dashboard + Manual Redemption

**Flow:**
1. Partner logs into `dashboard.metron.az` on a tablet or laptop kept at the counter
2. Customer provides their Metron user ID or scans their app QR
3. Partner enters the product price and coins to deduct on the dashboard
4. System processes the transaction; both parties see confirmation
5. Dashboard updates settlement balance in real time

**Target partner:** Mid-size cafes and restaurants with a tablet/laptop at the register. Estimated 25% of partners.

| Pros | Cons |
|------|------|
| Real-time transaction history | Requires stable internet |
| Built-in settlement tracking | Needs a dedicated device at counter |
| Can handle multiple staff logins | 10–20 sec per transaction |
| Daily CSV export for bookkeeping | — |

---

#### Tier 3 — POS / API Integration (Full Automation)

**Flow:**
1. Partner's existing POS system calls `POST /api/v1/partner/redeem` at checkout
2. Metron returns the coin/cash split; POS adjusts the bill automatically
3. Customer sees "Metron Coins applied" on their receipt
4. Settlement data flows directly into the partner's accounting system

**Target partner:** Chains with existing POS infrastructure (e.g., franchise cafes, supermarkets). Estimated 5% of partners initially, growing to 20% by Month 12.

| Pros | Cons |
|------|------|
| Fully automated — zero cashier friction | Requires developer resources on partner side |
| Sub-second transaction processing | 2–4 week integration timeline |
| Automatic daily reconciliation | API key management responsibility |
| Supports high transaction volume | — |

**API documentation:** OpenAPI spec at `api.metron.az/docs`. Sandbox environment provided. Dedicated integration support engineer assigned.

---

### C) Partner Dashboard — Features & Metrics

**Overview Tab:**
- Today's coin redemptions (count + AZN value)
- Today's unique Metron customers
- Current settlement balance (what Metron owes the partner)
- Month-to-date totals with % change vs. prior month

**Analytics Tab:**
- Daily / weekly / monthly redemption volume (AZN) — bar chart
- Unique Metron customers per period — line chart
- Average transaction value (total and coin portion)
- Peak redemption hours — heatmap (helps partners staff accordingly)
- Repeat customer rate (% of Metron users who return within 7 days)

**Transactions Tab:**
- Full transaction history with filters: date range, status, amount
- Each row: timestamp, transaction ID, coins redeemed, cash paid, total, status
- Export: CSV and PDF, date-range selectable
- Search by transaction ID for dispute resolution

**Settlement Tab:**
- Current unsettled balance
- Settlement history: date, amount, bank reference, status
- Next scheduled settlement date and projected amount
- Invoice download (auto-generated, VÖEN-compliant)

**Settings Tab:**
- QR code generator (regenerate, download, print)
- Business profile editor (name, logo, category, hours)
- Staff accounts (add/remove cashiers with limited permissions)
- API key management (Tier 3 only: generate, rotate, revoke)
- Notification preferences (email/SMS on settlement, daily summary)

---

## Task 2 — Financial Model

### Money Flow — Worked Example

**Scenario:** Kamran buys a 2.50 AZN coffee at Coff Coffee. He has 4.00 coins and uses 1.80.

#### Step-by-step flow:

| # | Event | Amount |
|---|-------|--------|
| 1 | **User pays** | 1.80 coins deducted from wallet + 0.70 AZN cash to Coff Coffee |
| 2 | **Coff Coffee receives** | 0.70 AZN cash immediately (from customer) |
| 3 | **Metron owes Coff Coffee** | 1.80 AZN minus commission, settled weekly |
| 4 | **Metron commission** | 12% of coin value = 0.216 AZN → Metron keeps 0.22 AZN |
| 5 | **Metron settles** | 1.80 − 0.22 = 1.58 AZN bank transfer to Coff Coffee |
| 6 | **Coff Coffee total received** | 0.70 (cash) + 1.58 (settlement) = **2.28 AZN** for a 2.50 AZN product |

**Coff Coffee's effective discount: 8.8%** — comparable to credit card interchange + loyalty program costs they'd pay anyway, but with guaranteed foot traffic from Metron's user base.

---

### Commission Model (Hybrid)

| Component | Rate | Rationale |
|-----------|------|-----------|
| **Transaction commission** | 12% of coin value redeemed | Core revenue stream. Competitive with food delivery platforms (15–30%) and card interchange (1.5–2.5%). Partners accept this because coins drive incremental foot traffic. |
| **Monthly SaaS fee** | 0 AZN (Tier 1 & 2), 29 AZN/mo (Tier 3) | Keeps barrier to entry at zero for small partners. Tier 3 fee covers API support and SLA costs. |
| **Premium placement** | 15 AZN/mo (optional) | "Featured Partner" badge + top position in the app's partner list. |

---

### Coin Funding Sources

| Source | Contribution | Mechanism |
|--------|-------------|-----------|
| **Metro operator revenue share** | 40% of coin funding | Metron signs a revenue-share agreement with Bakı Metropoliteni. The metro operator benefits from load-balanced ridership (reduced peak infrastructure strain). Metron receives 0.05–0.08 AZN per off-peak trip logged. This funds the coins issued. |
| **Partner commissions** | 35% of coin funding | The 12% commission on every redemption flows back into the coin reserve. As redemption volume grows, this becomes self-sustaining. |
| **Investor float** | 20% of coin funding (Year 1 only) | Seed/Series A capital pre-funds the coin reserve during the growth phase before commission revenue scales. |
| **Breakage (unredeemed coins)** | 5% of coin funding | Industry data shows 10–20% of loyalty points go unredeemed. Conservative 5% assumption. These coins expire after 12 months and return to the reserve. |

---

### Settlement Cycle

**Proposed: Weekly settlement (every Monday for prior Mon–Sun transactions).**

| Factor | Weekly | Bi-weekly |
|--------|--------|-----------|
| Partner cash flow | Better — small businesses need frequent payouts | Slower — may cause cash flow strain |
| Metron float benefit | 3–7 day average float | 7–14 day average float |
| Operational cost | 52 batch transfers/year per partner | 26 batch transfers/year per partner |
| Partner satisfaction | Higher (benchmarked against Bolt Food: weekly) | Lower |

**Decision: Weekly wins.** The goodwill and competitive positioning (vs. Wolt/Bolt's weekly payouts) outweighs the marginal float benefit of bi-weekly. Metron holds an average 3.5-day float on coin value, which provides short-term working capital.

---

### Unit Economics Table

| Persona | Avg Trip Fare | Cashback % | Coins Earned / Trip | Trips / Month | Monthly Coins Earned | Avg Redemption | Metron Margin (12%) |
|---------|--------------|------------|--------------------:|---------------|--------------------:|---------------:|-------------------:|
| **Off-peak heavy user** | 0.40 AZN | 15% (density < 0.30) | 0.060 ⬡ | 44 (2×/day weekdays) | 2.64 ⬡ | 2.40 AZN | 0.29 AZN |
| **Mixed commuter** | 0.40 AZN | 8% avg (varies) | 0.032 ⬡ | 44 | 1.41 ⬡ | 1.20 AZN | 0.14 AZN |
| **Peak-only rider** | 0.40 AZN | 0–3% avg | 0.006 ⬡ | 44 | 0.26 ⬡ | 0.20 AZN | 0.02 AZN |

**Key insight:** The system is self-selecting — off-peak users earn and redeem the most, which is exactly the behavior Metron and the metro operator want to incentivize. Peak-only users cost Metron almost nothing in coin issuance.

---

## Task 3 — Azerbaijan Partner Target List

| # | Partner Name | Category | Est. Monthly Customers | Coin Fit Score (1–10) | Notes |
|---|-------------|----------|----------------------:|:---------------------:|-------|
| 1 | Coff Coffee | ☕ Coffee | 8,000 | 9 | Multiple Baku locations, metro-adjacent, young clientele |
| 2 | Limon Coffee | ☕ Coffee | 5,500 | 9 | Popular chain, strong Instagram presence |
| 3 | Brew Lab | ☕ Coffee | 3,200 | 8 | Specialty coffee, tech-savvy crowd near 28 May |
| 4 | Sütlü Coffee | ☕ Coffee | 2,800 | 7 | 2 locations, loyal student base |
| 5 | Coffee Mood | ☕ Coffee | 4,500 | 8 | High-traffic location near Sahil |
| 6 | Cup & Co | ☕ Coffee | 2,000 | 7 | Boutique café, Fountain Square area |
| 7 | Kahve Dünyası | ☕ Coffee | 6,000 | 8 | Turkish chain with Baku presence, brand recognition |
| 8 | Starbucks Azerbaijan | ☕ Coffee | 12,000 | 6 | High volume but corporate approval slower |
| 9 | Noir Coffee | ☕ Coffee | 1,800 | 7 | Trendy spot near Nəriman Nərimanov station |
| 10 | JavaHouse | ☕ Coffee | 2,200 | 7 | Co-working café, repeat daily customers |
| 11 | Mangal House | 🥩 Restaurant | 4,000 | 7 | Kebab chain, multiple locations |
| 12 | Salam Bro | 🥗 Fast Food | 5,500 | 9 | Fast-casual, young demographic, metro-adjacent |
| 13 | Çudo Piroq | 🍕 Restaurant | 3,800 | 8 | Quick-service, affordable, high turnover |
| 14 | KFC Azerbaijan | 🍗 Restaurant | 15,000 | 7 | High volume, corporate chain, API integration likely |
| 15 | McDonald's Azerbaijan | 🍔 Restaurant | 18,000 | 6 | Massive volume but lengthy partnership approval |
| 16 | Kebab City | 🥩 Restaurant | 2,500 | 7 | Local favorite, 3 locations near metro |
| 17 | Dönər House | 🌯 Restaurant | 3,200 | 8 | Fast food, low average ticket, high frequency |
| 18 | Fisincan | 🍖 Restaurant | 2,000 | 6 | Traditional Azerbaijani cuisine, tourist + local mix |
| 19 | Sumakh | 🥘 Restaurant | 1,800 | 6 | National cuisine, lunch crowd near Ulduz |
| 20 | Panda Asian Food | 🍜 Restaurant | 2,800 | 7 | Affordable Asian food, university crowd |
| 21 | Chocolate Box | 🧁 Bakery | 3,500 | 8 | Dessert chain, impulse-buy price point perfect for coins |
| 22 | Doğma Çay Evi | 🍵 Tea House | 2,200 | 8 | Traditional tea house, metro-adjacent, very low ticket |
| 23 | Şirin Şeylər | 🎂 Bakery | 1,500 | 7 | Pastry shop near Koroğlu station |
| 24 | Aşpaz Bakery | 🥐 Bakery | 2,000 | 7 | Fresh bread and pastries, morning commuter traffic |
| 25 | Paris Croissant | 🥐 Bakery | 1,800 | 7 | Upscale bakery, 2 locations, mid-ticket range |
| 26 | Zeytun Aptek | 💊 Pharmacy | 8,000 | 5 | Pharmacy chain, high foot traffic but lower engagement |
| 27 | Ali & Nino Bookstore | 📚 Bookstore | 3,000 | 6 | Iconic brand, cultural alignment, tourist + local |
| 28 | Bravo Supermarket | 🛒 Market | 20,000 | 5 | Massive volume, complex POS integration, low margin |
| 29 | Araz Market | 🛒 Market | 15,000 | 5 | Large chain, would need Tier 3 integration |
| 30 | Bolt Market Baku | 📦 Delivery | 10,000 | 4 | Online-first, potential API partner but competitive overlap |

**Prioritization:** Partners scoring 7+ should be targeted in the first 3 months. Score 8–9 partners (Coff Coffee, Limon, Salam Bro, Chocolate Box, Doğma Çay Evi, Dönər House) are ideal launch partners — low ticket price, high frequency, metro-adjacent, young audience.

---

## Task 4 — User Journey Map: Kamran

> **Kamran, 26** — Junior software developer at a fintech company near 28 May station. Lives near Həzi Aslanov. Commutes daily via metro. Tech-savvy, price-conscious, buys coffee every morning.

---

### Stage 1: Discovery

| Dimension | Detail |
|-----------|--------|
| **What Kamran does** | Sees an Instagram Reel from a friend showing "Just earned free coffee from riding the metro 🚇☕" with a screenshot of the Metron app. Kamran taps the link in bio. |
| **What the system does** | Attribution link tracks the referral source (Instagram → friend's referral code). Landing page loads with a 30-second explainer animation and "Download" CTA. |
| **Emotional state** | Curious, mildly skeptical. "Is this real? Free coffee for riding the metro?" |
| **Friction point** | Doesn't trust it — sounds like a scam or a data-harvesting app. |
| **How Metron resolves** | Landing page shows: (a) partnership with Bakı Metropoliteni logo, (b) "Your data stays on your device — we only track tap-in/tap-out times," (c) live counter: "12,847 coffees redeemed this month." Social proof + institutional trust. |

---

### Stage 2: Download & Registration

| Dimension | Detail |
|-----------|--------|
| **What Kamran does** | Downloads from App Store. Opens app. Signs up with phone number (+994 XX XXX XX XX). Receives SMS OTP. Sets display name. |
| **What the system does** | Creates user record, generates UUID, initializes coin_balance = 0.00. Sends welcome push notification: "Welcome to Metron! Link your BakıKart to start earning." |
| **Emotional state** | Engaged but impatient — wants to see value quickly. |
| **Friction point** | Registration takes too long or asks for too much info upfront. |
| **How Metron resolves** | 3-step registration: phone → OTP → name. No email required. No profile photo. Under 60 seconds. Deferred data collection (address, preferences) to later. |

---

### Stage 3: Links BakıKart

| Dimension | Detail |
|-----------|--------|
| **What Kamran does** | Taps "Link Card." Enters the 11-digit BakıKart number printed on the back. Taps NFC (if supported) or enters manually. |
| **What the system does** | Validates the card number format. Stores `metro_card_id` in the users table. Begins listening for trip events associated with that card via the metro operator data feed. |
| **Emotional state** | Slightly anxious — "Will this charge my card? Is it safe?" |
| **Friction point** | Kamran doesn't know where to find his card number. NFC might not work on his phone. |
| **How Metron resolves** | Visual guide overlay: photo of a BakıKart with an arrow pointing to the number. Fallback: manual entry with format validation and instant confirmation. Explicit copy: "We never charge your card. We only read trip data." |

---

### Stage 4: First Trip — Earns Coins

| Dimension | Detail |
|-----------|--------|
| **What Kamran does** | Takes his usual 08:15 metro from Həzi Aslanov to 28 May. Taps BakıKart at the turnstile as always. |
| **What the system does** | Metro data feed registers: card_id, station_id=HA-08, timestamp=08:15, direction=inbound. System calls density prediction: density_score=0.88 (packed), cashback_percent=0. Kamran earns 0.00 coins. Trip is logged in `metro_trips`. Push notification: "Trip logged! 28 May → Həzi Aslanov. Peak hour — 0% cashback. 💡 Try traveling after 10:00 for 15% cashback!" |
| **Emotional state** | Disappointed — earned nothing. But intrigued by the suggestion. |
| **Friction point** | First experience is zero reward. Risk of immediate churn. |
| **How Metron resolves** | (a) First-trip bonus: award 0.50 coins regardless of density as a welcome gift. (b) Push notification frames it positively with actionable advice. (c) Dashboard shows the heatmap so Kamran sees exactly when he'd earn more. Creates a "game" mental model, not a "failure." |

---

### Stage 5: Checks Balance & Heatmap

| Dimension | Detail |
|-----------|--------|
| **What Kamran does** | Opens the app during lunch break. Sees 0.50 ⬡ balance (welcome bonus). Swipes to the Cashback Calculator screen. Drags the time slider and watches the density/cashback numbers change. Notices: 10:00–12:00 and 14:00–16:00 show 15% cashback. |
| **What the system does** | Dashboard fetches cached density predictions for Kamran's home station (HA-08). Renders 24-hour heatmap. Animates coin balance with the gold shimmer effect. |
| **Emotional state** | Motivated. "If I shift my commute by 90 minutes, I earn 15%? That's 0.06 per trip... 1.32/month... free coffee every 2 weeks." He does the math. |
| **Friction point** | The earned amounts seem small per trip. Kamran might think it's not worth changing habits. |
| **How Metron resolves** | Dashboard shows projected monthly earnings: "At your current pace: 0.26 ⬡/month. If you shift 3 trips/week off-peak: 1.58 ⬡/month — that's a free coffee!" Framing in tangible rewards, not abstract points. |

---

### Stage 6: Redeems at Coff Coffee

| Dimension | Detail |
|-----------|--------|
| **What Kamran does** | After 2 weeks of adjusted commuting, Kamran has 1.85 ⬡. He walks into Coff Coffee near 28 May station. Orders a latte (2.50 AZN). Opens Metron → Partner Stores → Coff Coffee → "Pay with Coins." Enters 2.50 AZN price, slides coin slider to 1.85. Sees: "Coins: 1.85 ⬡ / Cash: 0.65 AZN." Taps Confirm. Shows QR to barista. |
| **What the system does** | Creates redemption record. Debits 1.85 from user balance. Generates signed QR with transaction_id and idempotency_key. Barista scans → partner app confirms: "Metron payment: 1.85 ⬡ applied. Collect 0.65 AZN cash." Settlement of 1.85 × 0.88 = 1.63 AZN queued for next Monday payout to Coff Coffee. |
| **Emotional state** | Delighted. "I just paid 0.65 for a 2.50 latte. This is real." Takes a screenshot, shares on Instagram story. |
| **Friction point** | Barista doesn't know what Metron is or how to scan the QR. |
| **How Metron resolves** | (a) Partner onboarding includes barista training (2-min video). (b) QR stand at the register has instructions for staff. (c) Fallback: barista can enter the 6-digit transaction code manually. (d) Kamran's screen shows "Show this to the cashier" with clear visual instructions. |

---

### Stage 7: Returns Next Day — Habit Formed

| Dimension | Detail |
|-----------|--------|
| **What Kamran does** | Next morning, intentionally takes the 10:15 metro instead of 08:15. Checks app at the turnstile — sees "You're earning 15% right now!" badge. Arrives at work, sees 0.06 ⬡ credited instantly. Opens app at lunch to check the running total. Plans his next Coff Coffee visit. |
| **What the system does** | Trip logged, density=0.18 (empty), cashback=15%, coins_earned=0.06. Streak counter incremented: "3-day off-peak streak 🔥". Push notification (evening): "You've earned 0.42 ⬡ this week — keep it up!" Referral prompt after 5th trip: "Invite a friend, both get 0.50 ⬡." |
| **Emotional state** | Satisfied and habitual. Metron is now part of his daily routine. He tells coworkers about it. |
| **Friction point** | Habit decay — after the novelty wears off, Kamran might stop checking the app. |
| **How Metron resolves** | (a) Weekly summary push: "This week: 4 off-peak trips, 0.24 ⬡ earned, rank #847 in Baku." Gamification. (b) Monthly milestone rewards: "10 off-peak trips = bonus 0.50 ⬡." (c) Partner flash deals: "Double coins at Chocolate Box this Friday!" (d) The real lock-in: Kamran now genuinely prefers the emptier metro. The behavior shift is self-reinforcing even without the app. |

---

## Task 5 — 12-Month KPI Forecast

### Assumptions

| Parameter | Value | Justification |
|-----------|-------|---------------|
| Baku Metro daily ridership | 200,000 trips/day | Bakı Metropoliteni public data |
| Month 1 adoption | 0.5% of daily riders = 1,000 users | Conservative for a new app with no marketing spend beyond social media |
| Monthly user growth rate | 30% M1–M3, 20% M4–M6, 15% M7–M9, 10% M10–M12 | Typical consumer app S-curve: viral phase → organic plateau |
| MAU / Registered ratio | 60% initially, stabilizing at 50% | Industry benchmark for utility apps |
| Trips per MAU per month | 30 (weekday commuters, 2×/day avg) | Conservative — power users do 44+ |
| Avg cashback rate | 6% blended (mix of peak and off-peak) | Weighted average across all density bands |
| Metro fare | 0.40 AZN | Current BakıKart single-trip fare |
| Coins earned per trip | 0.024 ⬡ avg (0.40 × 6%) | Blended rate |
| Redemption rate | 65% of issued coins (Month 1), growing to 80% | Low initially (users accumulate), rises as partner network grows |
| Avg Metron commission | 12% of redeemed coin value | Hybrid model per Task 2 |
| Partner onboarding | 8 at launch, +3–5/month | Realistic for a 2-person BD team |

---

### Monthly Projection Table

| Month | Registered Users | MAU | Trips Logged | Coins Issued (AZN) | Coins Redeemed (AZN) | Active Partners | Metron Revenue (AZN) |
|------:|-----------------:|----:|-------------:|--------------------:|---------------------:|----------------:|---------------------:|
| 1 | 1,000 | 600 | 18,000 | 432 | 281 | 8 | 34 |
| 2 | 1,300 | 780 | 23,400 | 562 | 393 | 11 | 47 |
| 3 | 1,690 | 1,014 | 30,420 | 730 | 548 | 15 | 66 |
| 4 | 2,028 | 1,217 | 36,504 | 876 | 701 | 18 | 84 |
| 5 | 2,434 | 1,460 | 43,805 | 1,051 | 893 | 22 | 107 |
| 6 | 2,920 | 1,752 | 52,566 | 1,262 | 1,072 | 25 | 129 |
| 7 | 3,358 | 1,847 | 55,410 | 1,330 | 1,130 | 28 | 136 |
| 8 | 3,862 | 2,124 | 63,722 | 1,529 | 1,330 | 32 | 160 |
| 9 | 4,441 | 2,443 | 73,280 | 1,759 | 1,548 | 35 | 186 |
| 10 | 4,885 | 2,686 | 80,580 | 1,934 | 1,741 | 38 | 209 |
| 11 | 5,374 | 2,955 | 88,660 | 2,128 | 1,915 | 41 | 230 |
| 12 | 5,911 | 3,251 | 97,526 | 2,341 | 2,107 | 45 | 253 |

---

### Quarterly Narrative

#### Q1 (Months 1–3): Launch & Validation

**Target: 1,690 users, 15 partners, 66 AZN monthly revenue**

Focus is product-market fit, not revenue. Launch with 8 hand-picked partners near high-traffic stations (28 May, Həzi Aslanov, İçərişəhər). Primary acquisition channel: Instagram/TikTok content showing real redemptions. Key milestone: first 100 organic redemptions without Metron team involvement. Revenue is negligible — the priority is proving the loop works (ride → earn → redeem → ride again).

#### Q2 (Months 4–6): Growth & Network Effects

**Target: 2,920 users, 25 partners, 129 AZN monthly revenue**

Partner network reaches critical mass — at least one partner within 200m of every metro station. Introduce the referral program (invite a friend → both earn 0.50 ⬡). Launch "Flash Deals" where partners offer 2× coin acceptance on slow days (driving traffic to partners during their off-peak). Begin conversations with Bakı Metropoliteni for official co-branding (in-station posters, BakıKart linking via NFC at turnstiles). Revenue crosses 100 AZN/month — not meaningful yet, but the trajectory validates the model.

#### Q3 (Months 7–9): Monetization & Efficiency

**Target: 4,441 users, 35 partners, 186 AZN monthly revenue**

Introduce Tier 3 API integrations with 2–3 chain partners (KFC, Kahve Dünyası). Launch premium partner placement (15 AZN/month). Optimize the ML model with 6 months of real trip data — cashback rates become more precise, further incentivizing off-peak shifts. Begin tracking metro operator KPI: % reduction in peak-hour density at pilot stations. This data is critical for the metro partnership renewal negotiation.

#### Q4 (Months 10–12): Scale & Series A Readiness

**Target: 5,911 users, 45 partners, 253 AZN monthly revenue**

Monthly revenue run-rate: ~3,000 AZN/year. Not yet profitable, but unit economics are proven: each active user generates 0.08 AZN/month in margin, with CAC trending toward zero (organic + referral). Key Series A metrics to present:

| Metric | Value |
|--------|-------|
| Total registered users | 5,911 |
| MAU | 3,251 (55%) |
| Total coins issued (Year 1) | 13,934 AZN |
| Total coins redeemed (Year 1) | 11,659 AZN |
| Redemption rate | 83.7% |
| Active partners | 45 |
| Net Revenue (Year 1) | ~1,641 AZN |
| User CAC | < 0.50 AZN (organic-heavy) |
| LTV (projected 24-mo) | ~1.90 AZN per user |

**The pitch:** Metron is not a loyalty app — it's infrastructure for demand-side metro management. The cashback is the mechanism; the product is behavioral shift at city scale. With 200,000 daily riders in Baku alone, and metro systems across the region (Tbilisi, Istanbul, Almaty) facing the same peak-hour problem, Metron's TAM extends well beyond Azerbaijan.

---

*End of document. All projections based on stated assumptions. Actual results will vary with execution speed, metro operator partnership terms, and market conditions.*
