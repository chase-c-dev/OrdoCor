const resource = (table, fields, required = [], orderBy = 'id DESC', parentField = null) => ({ table, fields, required, orderBy, parentField })

const RESOURCES = {
  todos: resource('todo_items', ['title', 'notes', 'is_completed'], ['title'], 'is_completed, created_at DESC'),
  calendar: resource('calendar_items', ['item_date', 'title', 'notes'], ['item_date', 'title'], 'item_date, title'),
  accounts: resource('investment_accounts', ['institution', 'name', 'account_type', 'notes'], ['institution', 'name'], 'institution, name'),
  stocks: resource('investment_stocks', ['ticker', 'company_name', 'purchase_date', 'purchase_price', 'shares', 'target_sell_price', 'notes'], ['ticker', 'company_name'], 'ticker'),
  'stock-watchlist': resource('investment_stock_watchlist', ['ticker', 'company_name', 'target_buy_price', 'notes'], ['ticker', 'company_name'], 'ticker'),
  'mutual-funds': resource('investment_mutual_funds', ['symbol', 'fund_name', 'purchase_date', 'purchase_price', 'shares', 'notes'], ['symbol', 'fund_name'], 'symbol'),
  'mutual-fund-watchlist': resource('investment_mutual_fund_watchlist', ['symbol', 'fund_name', 'target_buy_price', 'notes'], ['symbol', 'fund_name'], 'symbol'),
  banking: resource('investment_banking_products', ['product_name', 'institution', 'open_date', 'principal', 'interest_rate', 'maturity_date', 'maturity_value', 'notes'], ['product_name', 'institution'], 'maturity_date, product_name'),
  collectibles: resource('investment_collectibles', ['item_name', 'category', 'target_price', 'quantity', 'purchase_link', 'notes'], ['item_name'], 'item_name'),
  plans: resource('investment_pipeline', ['idea_name', 'investment_type', 'desired_purchase_price', 'desired_shares', 'target_date', 'status', 'notes'], ['idea_name'], 'target_date, idea_name'),
  recipes: resource('recipes', ['name', 'category', 'servings', 'prep_minutes', 'cook_minutes', 'ingredients', 'instructions', 'notes'], ['name'], 'name'),
  'recipe-categories': resource('recipe_categories', ['name'], ['name'], 'name'),
  projects: resource('projects', ['name', 'description'], ['name'], 'name'),
  wishlist: resource('wishlist_items', ['name', 'category', 'estimated_price', 'quantity', 'notes'], ['name'], 'category, name'),
  travel: resource('travel_destinations', ['country', 'city', 'priority', 'target_season', 'target_year', 'notes'], [], 'priority, country, city'),
  'house-reminders': resource('house_reminders', ['name', 'reminder_type', 'due_date', 'amount', 'notes'], ['name'], 'due_date, name'),
  'house-maintenance': resource('house_maintenance', ['title', 'frequency', 'due_date', 'video_url', 'notes'], ['title'], 'due_date, title'),
  'house-improvements': resource('house_improvements', ['name', 'priority', 'estimated_cost', 'notes'], ['name'], 'priority, name'),
  vehicles: resource('vehicles', ['name', 'make', 'model', 'vehicle_year', 'vin', 'notes'], ['name'], 'name'),
  'vehicle-maintenance': resource('vehicle_maintenance', ['vehicle_id', 'title', 'due_date', 'video_url', 'notes'], ['vehicle_id', 'title'], 'due_date, title', 'vehicle_id'),
  'vehicle-wishlist': resource('vehicle_wishlist', ['vehicle_id', 'item_name', 'category', 'estimated_price', 'notes'], ['vehicle_id', 'item_name'], 'category, item_name', 'vehicle_id'),
}

const MARKET_RESOURCES = {
  stocks: ['investment_stocks', 'ticker'],
  'stock-watchlist': ['investment_stock_watchlist', 'ticker'],
  'mutual-funds': ['investment_mutual_funds', 'symbol'],
  'mutual-fund-watchlist': ['investment_mutual_fund_watchlist', 'symbol'],
}

module.exports = { RESOURCES, MARKET_RESOURCES }
