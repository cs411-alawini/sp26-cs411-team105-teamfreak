# CS 411 Final Project Report: Team 105 (TeamFreak) 

##Changes from the original proposal 

Our original Stage 1 proposal had a few ideas that we ended up either scaling back or removing. The biggest one was the debt approval system. In the proposal, we said that debts would "only become active once both parties give approval," like a two-way handshake before any balance showed up. We ended up dropping this. It added a lot of complexity and didn't feel necessary for a friend group expense tracker where people generally trust each other. Instead, when someone logs an expense with a split, it just goes live immediately. 

We also originally talked about a "simplified settlement suggestion" system where, for example, if A owes B and B owes C, the system could simplify the chain, so A just pays C. This is kind of like the transitive property we covered earlier in the semester. We did end up implementing settlement suggestions, but it works more as a greedy net-balance algorithm rather than the full chain-of-debt optimization we originally described. 

## Usefulness 

Overall, we think the app achieved what it was supposed to do at a core level. You can create circles, add members, log expenses with even/percent/custom splits, record payments against those expenses, and see real-time balances of who owes who within a circle. The dashboard gives you a quick overview of all your circles with how much you owe and how much is owed to you, which is the main thing you'd want from an app like this. 

Where it falls short is in some of the secondary features. We don't have notifications, there's no email integration, and the settlement suggestions are displayed, but you can't one-click execute a suggested settlement (you'd have to manually record each payment). The reliability score also doesn't dynamically update. Instead, it should ideally recalculate every time a payment is made or missed. But for the scope of a class project, the core expense tracking and balance computation works well and is actually usable. 

## Data schema and source changes 

For the data source, we stuck with what we said in Stage 1, so there was no change there. 

The schema itself went through several iterations though. The original DatabaseDesign.md had six tables (Users, Circle, Circle_Member, Expense, Expense_Split, Payments), and after Stage 2 feedback we added a seventh table, Expense_Payment, to resolve the many-to-many relationship between Expenses and Payments that was shown in our UML but not the schema. We also added the Paid_By and Due_Date columns to the Expenses table and added Name back to the Users table because of the discrepancies between our FDs and our actual schema. 

In the final implementation, we ended up dropping Paid_By and Due_Date from the Expense table since the code doesn't reference them. We also added a Rank column to the Users table that wasn't in any of the original designs, which stores the reliability score we display on the frontend. 

## ER diagram and table implementation changes 

The original ER diagram had a many-to-many between Expenses and Payments shown in the UML, but we didn't have a table for it in Stage 2. That was a big piece of feedback, and adding the Expense_Payment table was the main change we made. This table has a primary key of (Expense_Id, Payment_Id) and lets a single payment cover parts of multiple expenses and a single expense be paid off by multiple payments, which is how real-world expense splitting actually works. 

Another difference is that the original design had an Expense_Payment able that was added after Stage 2 revisions but was somewhat theoretical. In the final app, this table is extremely important because when you record a payment, the system inserts into both the Payments table and the Expense_Payment table within a single transaction, so every payment is always linked to a specific expense. This linkage is what allows us to compute remaining balances accurately (Amount_Owed minus the sum of linked payments). 

## Functionalities added or removed 

We added: 

User registration and login with password hashing and session management. This wasn't detailed in the proposal but obviously necessary for a real app. 

The ability to create a new circle inline while creating an expense (the "Create new circle" option on the expense form). We added it as a nice quality-of-life addition that we thought of during development. 

A "Settle All" button on the circle detail page that generates payments for every outstanding balance in one click. This is useful for when a group is done and everyone just wants to zero out. 

An expense review page powered by a stored procedure (GetExpenseDetail) that pulls together the expense info, splits, and payments in one call. 

User profile page with the ability to update name, email, and password, plus a summary of total balances across all circles. 

Removed: 

Debt approval workflow (both parties confirming a debt). This was too complex and would’ve slowed down development. 

Search functionality for groups, users, and expenses. The proposal mentioned this but we didn't build a dedicated search feature. You navigate through circles from the dashboard instead. 

Predictive payback date based on reliability scoring. We had the rank but never built the prediction feature around it. 

We added specific features if they were easy to implement and improved user experience. We removed features mostly because of complexity due to time constraints. 

## How advanced database programs complement the application 

We implemented two main advanced database features: a stored procedure and a transaction system. 

The stored procedure GetExpenseDetail is called from the expense review page. It takes an expense ID and returns three result sets in one call: the expense metadata (amount, circle, creator, status, dates), the split breakdown (who owes how much), and the payment history for that expense. This is a good use of a stored procedure because it bundles what would otherwise be three separate queries into a single database round-trip, which is more efficient and keeps the logic on the database side. It complements the app because the expense review page needs all three pieces of data together, and having them come from one procedure call keeps the route handler clean. 

For transactions, we used them in two critical places: recording a payment (inserting into Payments and Expense_Payment atomically) and the Settle All feature (which generates potentially many payments across all outstanding balances in one go). The transaction wrapper in db.py uses a context manager that commits on success and rolls back on any exception. This is necessary for data integrity because if the Expense_Payment insert fails after the Payment insert, we don't want an orphaned payment record sitting in the database with no expense linkage. The Settle All feature especially benefits from this because it could be inserting dozens of rows, and a partial failure would leave the balances in an inconsistent state. 

## Technical challenges 

Logan Alt: Getting the balance computation right with the Expense_Payment linkage was tough. The query in get_circle_balance_rows does a LEFT JOIN on a subquery that sums payments grouped by expense, sender, and receiver. We were double-counting payments at first because the join conditions only matched on expense ID and not on the specific sender/receiver pair. In the future I would be careful about what we GROUP BY in payment aggregation subqueries, and test with cases where one expense has multiple partial payments. 

Nathan Hwang: The expense creation form has a lot of dynamic behavior. Selecting a circle populates participants, selecting "Create new circle" swaps in different fields, and the split type changes what inputs show per participant. We should have React or Vue instead of vanilla JS since the forms were so complex. It would have saved a lot of debugging time. 

Charlie Niewiarowski: Implementing the settlement suggestion algorithm with Python's Decimal type was harder than expected. We had bugs where suggestions were off by a penny because net balances weren't being calculated constantly. The fix was to calculate to two decimal places at every step and use copy_abs() for debtor amounts. I would avoid this by using Decimal everywhere and writing tests with edge cases like splitting $10.00 three ways. 

Eric Yang: Generating realistic test data and then getting it to actually work with our schema was tedious. The generated data would have things like duplicate emails, foreign key references to users or circles that didn't exist yet, or dates that didn't make sense (like a payment date before the expense was created). We had to go through multiple rounds of cleaning and re-prompting to get a dataset that was both large enough to test and consistent enough to not break on import. In the future, I would define the schema constraints first. Also, I’d import data in dependency order (Users first, then Circles, then Circle_Member, etc.) to not get foreign key errors. 

## Other changes compared to the original proposal 

We didn't end up using the Expense Status field the way we originally planned. The proposal described statuses like "Active," "Settled," "Overdue," and "Canceled," and we do have those as ENUM values, but in the actual app we compute whether an expense is settled dynamically by checking if linked payments sum up to the full amount. The status column mostly just stays as "Active" and doesn't get updated programmatically. 

The UI also ended up looking different from the mockup. The mockup showed something more like a mobile app with cards and visual flair, and what we built is a more straightforward Flask web app with clean but basic HTML/CSS. 

## Future work 

The reliability scoring system needs actual logic behind it. Right now, Rank is basically static. Ideally it would recalculate after each payment using factors like on-time rate and transaction volume, possibly through a trigger on the Payments table. 

Adding the ability to edit and delete expenses would matter a lot for real use. There's no way to fix a mistake without touching the database directly as of now. 

Overdue detection and notifications would also help. We could add Due Data back to the Expense table and run a scheduled job to flag overdue expenses. 

Recurring expenses (like monthly rent splits) would make the app more useful for ongoing shared living situations. But that isn’t as necessary as the former features and would be implemented later. 

##Division of labor and teamwork 

Our team was Logan Alt, Nathan Hwang, Charlie Niewiarowski, and Eric Yang. 

Logan handled the backend database layer and query logic. He wrote most of queries.py and db.py, worked on balance computation, and handled the stored procedure. 

Nathan focused on the frontend, including Flask templates, HTML/CSS styling, the dynamic JavaScript for the expense form, and UI/UX decisions. He also built the user authentication flow. 

Charlie worked on the business logic in services.py, including expense creation with different split types, the settlement suggestion algorithm, payment recording with transaction safety, and the Settle All feature. 

Eric worked on data collection, data testing, and contributed to the backend algorithm work. 

Teamwork went well overall. We communicated on text and used GitHub to manage our code. Everyone contributed meaningfully and the final product works. 
