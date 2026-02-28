## Schema

**User**
User_Id
Name 
Email
Password_Hash
Date_Joined

**Circle**
Circle_Id
Circle_Name
Creation_Date
Creation_User_Id

**Circle_Member**
Circle_Id
User_Id
Role
Status (Invited, Active, Left)
Date_Joined

**Expenses**
Expense_Id
User_Id
Amount
Circle_Id
Paid_By
Creation_Date
Due_Date
Paid_Date
Status (Active, Settled, Overdue, Canceled)
Description
Split_Type (Even, Percent, Custom)

**Expense_Split**
Expense_Id
User_Id
Amount_Owed

**Payments**
Payment_Id
Sender_Id
Receiver_Id
Circle_Id
Amount
Payment_Date
Description

## Assumptions and Relations

**User**
    - Each User has a unique User_Id and can join multiple groups
    - Name makes a user identifiable to their peers
    - Email is unique per user and is used for login
    - Password is used for user login
    - Date_Joined is used to keep tracked of when an account is created 
    - Users are referenced by many records to participate in multiple groups, create expenses, pay, owe, and receive payments
**Circle**
    - A Circle represents a “circle of friends” for expenses and settlements uniquely identified by a Circle_Id with an identifiable Circle_Name
    - Creation_User_Id is the user who created the group at the Creation_Date to mark age of group
    - Expenses, debts, and payments all belong to a group
    - Grouping is the core organizational unit with multiple members and transactions
**Circle_Member**
    - A user with user_id can be invited to a group with group_id and accept/reject the invite
    - Status tracks the membership lifecycle of Invited -> Active -> Left or Invited -> Rejected
    - Role is group specific where a User can be an admin or member of different groups
    - Joined_Date is when Status within a group becomes active
    - Many-toMany relationship between Users and Circles
**Expenses**
    - An Expense is created within a Circle_Id
    - User_Id is the user who entered an expense at the Creation_Date who is owed money
    - Status reflects whether an expense is active, settled, or canceled
    - A Due_date is used to reflect when the owee needs the payment
    - Paid_By reflects who made a payment which may be different from the creator
    - Paid_Date shows when the expense occured
    - A Description may be used as a communication between users as to what an expense is for
    - Split_Type determines how splits are calculated either Even, Percent, or Custom
    - Paid_Date is when an expense is settled, may be null if not applicable
    - Generates splits, debts, and is queried and edited independently

**Expense_Split**
    - Each Expense_Id has one or more participants
    - Each participant gets and Amount_Owed for that expense
    - The sum of Amount_Owed across all users  in the expense 
    - An expense can involve many users and each user’s owed amount needs to be stored in a multi-row structure

**Payments**
    - A payment is a real transfer from one user to another within a Circle_Id
    - Uniquely identified by a Payment_Id
    - Transfer is reflected between a Sender_Id user to a Receiver_Id user
    - The amount is shown in Amount 
    - Description is optional metadata
    - Payments need to be recorded historically and can happen independent of a single expense

## Relationship Cardinalities
    - A user can belong to many Circles, and a Circle can have many Users (many-to-many)
    - A Circle can have many Expenses, but each Expense belongs to one Circle (one-to-many)
    - An Expense can be split among many Users, and each User can be involved in many Expenses (many-to-many)
    - A User can send and receive many Payments, but each Payment has exactly one User as its sender and one as its receiver (one-to-many)

## Normalization
**User BCNF**
FDs:
    - User_Id: Name, Email, Password_Hash, Date_Joined
    - Email: User_Id

**Circle BCNF**
FDs:
    - Circle_Id: Circle_Name, Creation_date, Creation_User

**Circle_Member BCNF**
FDs:
    - (User_Id, Circle_Id): Role, Status, Date_Joined

**Expenses BCNF**
FDs:
    - Expense_Id: Amount, Circle_Id, User_Id, Paid_By, Creation_Date, Due_Date, Paid_Date, Status, Description, Split_Type

**Expense_Split BCNF**
FDs:
    - (Expense_Id, User_Id): Amount_Owed


**Payments BCNF**
FDs:
    - Payment_Id: Sender_Id, Receiver_Id, Circle_Id, Amount, Payment_Date, Description

Our schema is normalized to BCNF. Each table represents a single real-world concept, and all non-key attributes in every table are fully functionally dependent on a candidate key and nothing else. We use composite keys in the appropriate, necessary tables such as Circle_Member and Expense_Split. No table contains transitive dependencies, and we removed an extraneous table to make sure no derived data is intentionally stored twice.

## Conceptual Database Design
User(User_Id: INT PK, Email: VARCHAR(255), Password_Hash: VARCHAR(255), Date_Joined: DATE)

Circle(Circle_Id: INT PK, Circle_Name: VARCHAR(50), Creation_Date: DATE, Creation_User_Id: INT FK to User.User_Id)

Circle_Member(Circle_Id: INT FK to Circle.Circle_Id, User_Id: INT FK to User.User_Id, Role: VARCHAR(50), Status: VARCHAR(50), Date_Joined: DATE, PK(Circle_Id, User_Id))

Expenses(Expense_Id: INT PK, Amount: DECIMAL(10,2), Circle_Id: INT FK to Circle.Circle_Id, Owed_User_Id: INT FK to User.User_Id, Creation_Date: DATE, Paid_Date: DATE, Status: VARCHAR(50), Description: VARCHAR(255), Split_Type: VARCHAR(20))

Expense_Split(Expense_Id: INT FK to Expenses.Expense_Id, User_Id: INT FK to User.User_Id, Amount_Owed: DECIMAL(10,2), PK(Expense_Id, User_Id))

Payments(Payment_Id: INT PK, Sender_Id: INT FK to User.User_Id, Receiver_Id: INT FK to User.User_Id, Circle_Id: INT FK to Circle.Circle_Id, Amount: DECIMAL(10,2), Payment_Date: DATE, Description: VARCHAR(255))
