let yahooClient

async function client() {
  if (yahooClient) return yahooClient
  const module = await import('yahoo-finance2')
  const YahooFinance = module.default
  yahooClient = typeof YahooFinance === 'function' ? new YahooFinance({ suppressNotices: ['yahooSurvey'] }) : YahooFinance
  return yahooClient
}

const number = (value) => value !== null && value !== undefined && value !== '' && Number.isFinite(Number(value)) ? Number(value) : null
const money = (value) => number(value) === null ? null : `$${number(value).toLocaleString(undefined, { maximumFractionDigits: 2 })}`
const compact = (value) => number(value) === null ? null : Intl.NumberFormat('en', { notation: 'compact', maximumFractionDigits: 2 }).format(number(value))
const percent = (value) => { const parsed = number(value); if (parsed === null) return null; return `${(Math.abs(parsed) < 1 ? parsed * 100 : parsed).toFixed(2)}%` }
const title = (value) => String(value || '').replaceAll('_', ' ').replaceAll('-', ' ').replace(/\b\w/g, (letter) => letter.toUpperCase())

function analystRecommendations(data) {
  const financial = data.financialData || {}
  const trend = data.recommendationTrend?.trend?.find((item) => item.period === '0m') || data.recommendationTrend?.trend?.[0]
  const recommendationMean = number(financial.recommendationMean)
  const recommendations = [
    ['Consensus', financial.recommendationKey ? title(financial.recommendationKey) : null],
    ['Recommendation Score', recommendationMean === null ? null : `${recommendationMean.toFixed(2)} / 5`],
    ['Analyst Opinions', number(financial.numberOfAnalystOpinions)],
    ['Mean Price Target', money(financial.targetMeanPrice)],
    ['High Price Target', money(financial.targetHighPrice)],
    ['Low Price Target', money(financial.targetLowPrice)],
    ['Strong Buy', number(trend?.strongBuy)], ['Buy', number(trend?.buy)], ['Hold', number(trend?.hold)],
    ['Sell', number(trend?.sell)], ['Strong Sell', number(trend?.strongSell)],
  ]
  const latestRatings = (data.upgradeDowngradeHistory?.history || []).filter((item) => item.firm && item.toGrade).sort((a, b) => new Date(b.epochGradeDate) - new Date(a.epochGradeDate)).slice(0, 6)
  for (const rating of latestRatings) recommendations.push([rating.firm, `${rating.toGrade}${rating.action ? ` · ${title(rating.action)}` : ''}`])
  const breakdown = trend ? [
    ['Strong Buy', trend.strongBuy], ['Buy', trend.buy], ['Hold', trend.hold], ['Sell', trend.sell], ['Strong Sell', trend.strongSell],
  ].map(([name, value]) => ({ name, value: number(value) || 0 })) : []
  return { rows: recommendations.filter(([, value]) => value !== null && value !== undefined && value !== '').map(([label, value]) => ({ label, value: String(value) })), breakdown }
}

async function quote(symbol) {
  const clean = symbol.trim().toUpperCase()
  const data = await (await client()).quote(clean)
  const price = number(data.regularMarketPrice)
  if (!price || price <= 0) throw new Error('Market data unavailable.')
  let dividend = number(data.dividendYield ?? data.trailingAnnualDividendYield)
  if (dividend !== null && Math.abs(dividend) < 1) dividend *= 100
  return { ticker: clean, market_price: price, dividend_yield: dividend, fetched_at: new Date().toISOString() }
}

async function history(symbol) {
  const clean = symbol.trim().toUpperCase(); const period1 = new Date(); period1.setFullYear(period1.getFullYear() - 5)
  const data = await (await client()).chart(clean, { period1, period2: new Date(), interval: '1d' })
  const rows = (data.quotes || []).filter((row) => row.date && number(row.close) !== null).map((row) => ({ price_date: new Date(row.date).toISOString().slice(0, 10), close_price: number(row.close) }))
  if (!rows.length) throw new Error('Market history unavailable.')
  return rows
}

async function fundamentals(symbol) {
  const clean = symbol.trim().toUpperCase()
  const data = await (await client()).quoteSummary(clean, { modules: ['summaryDetail', 'price', 'defaultKeyStatistics', 'assetProfile', 'fundProfile', 'financialData', 'recommendationTrend', 'upgradeDowngradeHistory'] })
  const detail = data.summaryDetail || {}; const price = data.price || {}; const stats = data.defaultKeyStatistics || {}; const profile = data.assetProfile || {}; const fund = data.fundProfile || {}
  const values = [
    ['Security Type', price.quoteType], ['Exchange', price.exchangeName], ['Currency', price.currency],
    ['Sector', profile.sector], ['Industry', profile.industry], ['Market Cap', price.marketCap ? `$${compact(price.marketCap)}` : null],
    ['Total Assets', stats.totalAssets ? `$${compact(stats.totalAssets)}` : null], ['Trailing P/E', number(detail.trailingPE)?.toFixed(2)],
    ['Forward P/E', number(detail.forwardPE)?.toFixed(2)], ['EPS', money(stats.trailingEps)], ['Beta', number(stats.beta)?.toFixed(2)],
    ['52-Week High', money(detail.fiftyTwoWeekHigh)], ['52-Week Low', money(detail.fiftyTwoWeekLow)],
    ['Average Volume', compact(detail.averageVolume)], ['Expense Ratio', percent(fund.feesExpensesInvestment?.annualReportExpenseRatio)],
    ['Fund Category', fund.categoryName],
  ].filter(([, value]) => value !== null && value !== undefined && value !== '')
  const analyst = analystRecommendations(data)
  return { rows: values.map(([label, value]) => ({ label, value: String(value) })), recommendations: analyst.rows, recommendationBreakdown: analyst.breakdown }
}

module.exports = { analystRecommendations, fundamentals, history, quote }
