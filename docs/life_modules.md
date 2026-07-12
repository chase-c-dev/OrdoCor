# Life Modules

## Home

The Home page contains:

- TODO list with add, modify, remove, and completion checks
- Full-year calendar with previous/next year navigation
- Calendar items assigned to individual days
- Upcoming list for calendar items due in the next 7 days

Tables:

- `todo_items`
- `calendar_items`

## Recipes

Recipes use a cookbook-style page view rather than a table.

Features:

- Category filter
- Search by recipe name
- Add, modify, and remove recipes
- Add recipe categories
- Previous/next recipe navigation
- Recipe image selected from the user's computer
- Ingredients, instructions, prep time, cook time, servings, and notes

Recipe images are stored in SQLite as blobs so they are included in database backups.

Tables:

- `recipes`
- `recipe_categories`

## Projects

Projects track work currently in progress.

Fields:

- Project name
- Description

Table:

- `projects`

## Wishlist

Wishlist tracks products the user wants to purchase.

Fields:

- Product
- Category
- Estimated price
- Quantity
- Notes

Calculated display value:

- Total: estimated price x quantity

Table:

- `wishlist_items`

## Travel

Travel tracks countries and cities the user wants to visit.

Fields:

- Country
- City
- Priority
- Target season
- Target year
- Notes

Table:

- `travel_destinations`

## House

House tracks recurring home responsibilities and future home improvement ideas.

Tax and insurance reminder fields:

- Reminder name
- Category
- Due date
- Amount
- Frequency
- Notes

Maintenance fields:

- Maintenance item
- Area
- Due date
- Reference link
- Notes

Improvement fields:

- Improvement
- Area
- Estimated cost
- Priority
- Notes

Tables:

- `house_reminders`
- `house_maintenance`
- `house_improvements`

## Vehicle

Vehicle tracks owned vehicles, maintenance items, and vehicle-related wishlist items.

Vehicle fields:

- Vehicle name
- Make
- Model
- Year
- VIN
- License plate
- Notes

Maintenance fields:

- Maintenance item
- Due date
- Mileage
- Estimated cost
- Video or reference link
- Notes

Wishlist fields:

- Wishlist item
- Category
- Estimated price
- Priority
- Notes

Tables:

- `vehicles`
- `vehicle_maintenance`
- `vehicle_wishlist`

## Settings

Settings includes database backup/restore controls, the last successful backup time, optional
password controls, and a persistent color palette selector.

Password controls:

- Enable password
- Change password
- Disable password

Available palettes:

- Medieval
- Woodland
- Moonlit
- Rosewood

Moonlit is the default for new users. The selected palette is stored in the `app_settings`
table, becomes the user's default, and is applied at the next launch.
