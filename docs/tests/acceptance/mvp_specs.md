# Acceptance Test Specs (MVP)

These specs define user‑visible acceptance criteria using Gherkin‑style scenarios and Playwright‑style pseudo‑code (no execution). Scope: TL;DR, Factor Explain, News filters, Scenario sliders.

---

## 1) TL;DR card renders fast with deltas

Feature: TL;DR shows decision, conviction, drivers, and changes

Scenario: TL;DR loads within 1.5s and shows required elements
  Given I open "/report/AAPL"
  When the page loads
  Then I should see a TL;DR card with
    | field          |
    | Verdict        |
    | Conviction     |
    | Key Drivers    |
    | Since Last Rev |
  And it should load within 1500 ms (p95)

Pseudo-code (Playwright)
- const start = Date.now()
- await page.goto('/report/AAPL')
- await page.getByTestId('tldr-card').waitFor({ timeout: 1500 })
- expect(await page.getByTestId('tldr-verdict').text()).toMatch(/Buy|Hold|Avoid/)
- expect(page.getByTestId('tldr-drivers').locator('li')).toHaveCountBetween(2,4)
- const elapsed = Date.now() - start; expect(elapsed).toBeLessThan(1500)

---

## 2) Factor card Explain drawer shows recipe and inputs

Feature: Factor Explain provides transparency

Scenario: Explain shows thresholds and input values
  Given I open "/report/AAPL"
  And the Factor card "Valuation" is visible
  When I click "Explain" on the Valuation card
  Then a drawer opens with
    | item                       |
    | Score header               |
    | Thresholds/Rules applied   |
    | Inputs table with values   |
    | Timestamps and providers   |
    | Link to peers comparison   |

Pseudo-code
- const card = page.getByTestId('factor-card-valuation')
- await card.getByRole('button', { name: 'Explain' }).click()
- const drawer = page.getByTestId('explain-drawer')
- await expect(drawer).toBeVisible()
- await expect(drawer.getByTestId('recipe')).toContainText(['P/E', 'EV/EBITDA', 'P/S'])
- await expect(drawer.getByTestId('inputs-table').locator('tr')).toHaveCountGreaterThan(1)
- await expect(drawer).toContainText(['Alpha Vantage','Finnhub'])
- await drawer.getByRole('link', { name: 'Compare vs peers' }).isVisible()

---

## 3) News timeline filters articles by time and topic

Feature: News filters refine the timeline and headline list

Scenario: Filtering to 7d and topic "earnings" updates both views
  Given I open "/report/AAPL?tab=news"
  When I set time filter to "7d"
  And I enable topic chip "earnings"
  Then the timeline shows clusters only for the last 7 days
  And the headline list shows items tagged with earnings

Pseudo-code
- await page.goto('/report/AAPL?tab=news')
- await page.getByTestId('filter-time').selectOption('7d')
- await page.getByTestId('topic-chip-earnings').click()
- const clusters = page.getByTestId('news-timeline').locator('[data-cluster]')
- await expect(clusters).toSatisfy(isWithinLast7Days)
- const headlines = page.getByTestId('headlines-list').locator('[data-topic~="earnings"]')
- await expect(headlines.count()).toBeGreaterThan(0)

---

## 4) Scenario sliders recompute score instantly

Feature: Scenario panel supports weight sliders with instant recompute

Scenario: Adjusting weights changes final score within 250ms perceived
  Given I open "/report/AAPL"
  And I open the Scenario panel
  When I move the "Valuation weight" slider from 20% to 30%
  Then the final score updates within 250 ms
  And the Contribution Waterfall reflects new weights

Pseudo-code
- await page.getByTestId('open-scenarios').click()
- const before = await page.getByTestId('final-score').text()
- const t0 = performance.now()
- await page.getByTestId('slider-valuation').fill('30')
- await page.getByTestId('final-score').waitForChange({ timeout: 250 })
- const t1 = performance.now(); expect(t1 - t0).toBeLessThan(250)
- await expect(page.getByTestId('contrib-waterfall')).toReflectWeights()

---

## 5) What Changed diff shows factor and input deltas

Feature: Diff view communicates movement since last review

Scenario: Diff drawer shows per‑factor deltas with color coding
  Given I open "/report/AAPL"
  When I click the "Since Last Review" chip
  Then a drawer opens showing
    | item                        |
    | Factor deltas with ▲▼ and values |
    | Input metric deltas           |
    | Time window selected          |

Pseudo-code
- await page.getByTestId('change-chip').click()
- const diff = page.getByTestId('diff-drawer')
- await expect(diff).toBeVisible()
- await expect(diff.getByTestId('factor-deltas')).toContainText(['Valuation','Sentiment'])
- await expect(diff.getByTestId('input-deltas').locator('tr')).toHaveCountGreaterThan(0)

---

## Non‑functional checks (MVP)
- TL;DR first meaningful paint < 1200 ms on p95
- Interaction latency (slider → score) < 250 ms perceived
- News list virtualization prevents jank on 100+ items
- Accessibility: labels, roles, keyboard navigation for core actions

