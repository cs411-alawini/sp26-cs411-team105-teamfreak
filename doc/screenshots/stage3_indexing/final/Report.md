The selected final indexes are: idx_expense_circle_id on Expense(Circle_Id), idx_es_composite on Expense_Split(Expense_Id, User_Id, Amount_Owed), idx_es_user_amount on Expense_Split(User_Id, Expense_Id, Amount_Owed) (retained due to foreign key constraint), and idx_expense_user_status_date on Expense(User_Id, Status, Paid_Date).

Adv. Query1: Cost = 818 No change
Adv. Query2: Cost = 801 No change (execution plan was improved, however)
Adv. Query3: Cost = 452 No change (execution plan was improved, however)