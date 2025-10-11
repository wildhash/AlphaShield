export const mockStats = {
  quick: { cash: "$5,000", savings: "$15,000", debt: "$30,000", previousDebt: "$48,000", netWorth: "$24,000" },
  health: { lines: [ { label: "Liquidity", value: 85 }, { label: "Debt", value: 92 }, { label: "Investment", value: 78 }, { label: "Spending", value: 58 }, { label: "Goals", value: 65 } ] },
  spending: [ { label: "Housing", pct: 100, amount: "$2500/$2500", color: "blue" }, { label: "Groceries", pct: 33, amount: "$280/$850", color: "blue" }, { label: "Dining", pct: 84, amount: "$380/$450", color: "orange" }, { label: "Transportation", pct: 18, amount: "$45/$250" } ],
  burn: "$112.70/day",
  loan: { investmentValue: "$19,260", nextPayment: "Nov 11, 2025" },
  investment: { value: "$19,300", returnPct: 7.0, initial: "$18,000" },
  goals: [ { title: "Emergency Fund", status: "ontrack", pct: 50, current: "$15,000", target: "$30,000" }, { title: "Home Down Payment", status: "behind", pct: 8, current: "$8,000", target: "$100,000" } ],
  actions: [ { id: "a1", title: "Reduce dining spending 20%", note: "Easy • save $300/mo", done: false }, { id: "a2", title: "Max out 401k before year-end", note: "Medium • save $2,664 tax", done: false }, { id: "a3", title: "Harvest tax losses", note: "Easy • save $400", done: false } ],
  portfolio: [ { symbol: "SPY", shares: 28.5, value: "$12,832", pnl: "+$144" }, { symbol: "AGG", shares: 42, value: "$4,368", pnl: "+$21" }, { symbol: "Cash", shares: "—", value: "$2,100", pnl: "$0" } ],
  lender: { defaultProbability: 8, paymentCoverage: 1.9, incomeStability: 75, spendingDiscipline: 68 },
  __insights: [ { title: "Dining spending is high", description: "Dining is at 84% of budget — consider trimming.", severity: "warning" } ]
};