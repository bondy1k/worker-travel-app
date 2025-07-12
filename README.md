# worker-travel-app
A web app to digitize the WSIB Worker Travel &amp; Expense Form (2721A), letting injured workers submit mileage, transit, parking, and meal claims online. Includes auto-calculated mileage, receipt uploads, and digital signature.

## Storage

Submitted claims are persisted to `travel_app.db` using SQLite. Each submission is stored in a `submissions` table and each travel row in a `travel_entries` table referencing its parent submission. JSON and CSV copies are still written to the `submissions/` folder for easy export.
