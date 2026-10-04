/** Supplies synthetic offline data for the packaged-interface layout check. */
const { contextBridge } = require('electron')

contextBridge.exposeInMainWorld('ordocor', {
  invoke: async (route) => {
    let data = []
    if (route === '/status') data = { setupSeen: true, unlocked: true }
    else if (route === '/settings') data = { theme: 'Moonlit' }
    else if (route === '/resources/stocks') data = [{
      id: 1, company_name: 'Example stock', ticker: 'TEST', shares: 10,
      purchase_price: 100, market_price: 110, notes: 'Synthetic layout test notes.',
    }]
    else if (route.endsWith('/history')) data = Array.from({ length: 60 }, (_, index) => ({
      price_date: new Date(Date.UTC(2026, 0, index + 1)).toISOString().slice(0, 10),
      close_price: 100 + index,
    }))
    else if (route.endsWith('/fundamentals')) data = {
      rows: [{ label: 'Market cap', value: '$1B' }],
      recommendations: [{ label: 'Consensus', value: 'Buy' }],
      recommendationBreakdown: [{ name: 'Buy', value: 10 }],
    }
    return { ok: true, data }
  },
})
