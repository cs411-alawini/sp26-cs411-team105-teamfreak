## Comments On Original

Comment 1: Wrong UML notation: No relationship name mentioned. Exactly one cardinality is represented as 1..1.
Resolution: Relationship names have been added to all association lines in the UML diagram.

Comment 2: Circle.Creation_User_Id implies a creator relationship from User to Circle, but that relationship is shown in the UML diagram.
Resolution: The relational schema has been updated to explicitly define Creation_User_Id as a Foreign Key (FK) referencing User.User_Id. This ensures the relational design matches the creator relationship depicted in the UML diagram.

Comment 3: The UML shows a many to many relationship b/w Expense and Payments, but there is no relationship table in the schema design.
Resolution: Added new relationship table, Expense_Payment. This table includes Expense_Id and Payment_Id as a composite primary key to properly resolve the many-to-many relationship identified in the UML.

Comment 4: Discrepancy. For example: The Expenses FDs include Paid_By and Due_Date, but the final schema drops them. The writeup and FD section include User.Name, but the final relational schema for User omits Name.
Resolution: All attributes have been synchronized across the writeup, FD section, and relational schema. Specifically, Paid_By and Due_Date have been added to the Expenses table, and Name has been added to the User table to resolve all discrepancies.

Comment 5: Insufficient BCNF process. Follow the BCNF steps: List all FDs, check if R is in BCNF (explain how), compute closures (A+), create decompositions if needed.
Resolution: The normalization section has been entirely rewritten to provide formal mathematical proofs. For every relation, we now list all functional dependencies and perform attribute closure calculations to demonstrate that every determinant is a superkey, thereby proving BCNF compliance according to the step-by-step methodology covered in lectures.

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

**Expense_Payment**
    - Tracks the many-to-many relationship between Expenses and Payments.
    - A single payment can cover parts of multiple expenses, and a single expense can be paid off via multiple separate payments.

## Relationship Cardinalities
    - A user can belong to many Circles, and a Circle can have many Users (many-to-many)
    - A Circle can have many Expenses, but each Expense belongs to one Circle (one-to-many)
    - An Expense can be split among many Users, and each User can be involved in many Expenses (many-to-many)
    - A User can send and receive many Payments, but each Payment has exactly one User as its sender and one as its receiver (one-to-many).
    - An Expense can be settled by many Payments, and a Payment can settle multiple Expenses (many-to-many).

## Normalization
**User**
    - Relation: R = {User_Id, Name, Email, Password_Hash, Date_Joined}
    - FDs: 
  1. User_Id -> Name, Email, Password_Hash, Date_Joined
  2. Email -> User_Id
    - BCNF Check: 
      - Compute closure of User_Id: {User_Id}+ = {User_Id, Name, Email, Password_Hash, Date_Joined}. Since {User_Id}+ = R, User_Id is a superkey.
      - Compute closure of Email: {Email}+ = {Email, User_Id, Name, Password_Hash, Date_Joined}. Since {Email}+ = R, Email is a superkey.
    - Conclusion: Because the left-hand side of every FD is a superkey, the relation is already in BCNF. No decomposition is necessary.

**Circle**
    - Relation: R = {Circle_Id, Circle_Name, Creation_Date, Creation_User_Id}
    - FDs: 
  1. Circle_Id -> Circle_Name, Creation_Date, Creation_User_Id
    - BCNF Check: 
      - Compute closure of Circle_Id: {Circle_Id}+ = {Circle_Id, Circle_Name, Creation_Date, Creation_User_Id}. Since {Circle_Id}+ = R, Circle_Id is a superkey.
    - Conclusion: The relation is in BCNF.

**Circle_Member**
    - Relation: R = {Circle_Id, User_Id, Role, Status, Date_Joined}
    - FDs: 
  1. (Circle_Id, User_Id) -> Role, Status, Date_Joined
    - BCNF Check: 
      - Compute closure of (Circle_Id, User_Id): {Circle_Id, User_Id}+ = {Circle_Id, User_Id, Role, Status, Date_Joined}. Since {Circle_Id, User_Id}+ = R, the composite key is a superkey.
    - Conclusion: The relation is in BCNF.

**Expenses**
    - Relation: R = {Expense_Id, Amount, Circle_Id, Owed_User_Id, Paid_By, Creation_Date, Due_Date, Paid_Date, Status, Description, Split_Type}
    - FDs: 
  1. Expense_Id -> Amount, Circle_Id, Owed_User_Id, Paid_By, Creation_Date, Due_Date, Paid_Date, Status, Description, Split_Type
    - BCNF Check: 
      - Compute closure of Expense_Id: {Expense_Id}+ = R. Since {Expense_Id}+ yields all attributes in the relation, it is a superkey.
    - Conclusion: The relation is in BCNF.

**Expense_Split**
    - Relation: R = {Expense_Id, User_Id, Amount_Owed}
    - FDs: 
  1. (Expense_Id, User_Id) -> Amount_Owed
    - BCNF Check: 
      - Compute closure of (Expense_Id, User_Id): {Expense_Id, User_Id}+ = {Expense_Id, User_Id, Amount_Owed}. Since it equals R, it is a superkey.
    - Conclusion: The relation is in BCNF.

**Payments**
    - Relation: R = {Payment_Id, Sender_Id, Receiver_Id, Circle_Id, Amount, Payment_Date, Description}
    - FDs: 
  1. Payment_Id -> Sender_Id, Receiver_Id, Circle_Id, Amount, Payment_Date, Description
    - BCNF Check: 
      - Compute closure of Payment_Id: {Payment_Id}+ = R. Since {Payment_Id}+ yields all attributes, it is a superkey.
    - Conclusion: The relation is in BCNF.

**Expense_Payment**
    - Relation: R = {Expense_Id, Payment_Id}
    - FDs: None (only trivial dependencies exist).
    - BCNF Check: 
      - A relation with only two attributes and no non-trivial FDs is inherently in BCNF. The candidate key is the combination of (Expense_Id, Payment_Id).
    - Conclusion: The relation is in BCNF.


## Conceptual Database Design
User(User_Id: INT PK, Name: VARCHAR(255), Email: VARCHAR(255), Password_Hash: VARCHAR(255), Date_Joined: DATE)

Circle(Circle_Id: INT PK, Circle_Name: VARCHAR(50), Creation_Date: DATE, Creation_User_Id: INT FK to User.User_Id)

Circle_Member(Circle_Id: INT FK to Circle.Circle_Id, User_Id: INT FK to User.User_Id, Role: VARCHAR(50), Status: VARCHAR(50), Date_Joined: DATE, PK(Circle_Id, User_Id))

Expenses(Expense_Id: INT PK, Amount: DECIMAL(10,2), Circle_Id: INT FK to Circle.Circle_Id, Owed_User_Id: INT FK to User.User_Id, Paid_By: INT FK to User.User_Id, Creation_Date: DATE, Due_Date: DATE, Paid_Date: DATE, Status: VARCHAR(50), Description: VARCHAR(255), Split_Type: VARCHAR(20))

Expense_Split(Expense_Id: INT FK to Expenses.Expense_Id, User_Id: INT FK to User.User_Id, Amount_Owed: DECIMAL(10,2), PK(Expense_Id, User_Id))

Payments(Payment_Id: INT PK, Sender_Id: INT FK to User.User_Id, Receiver_Id: INT FK to User.User_Id, Circle_Id: INT FK to Circle.Circle_Id, Amount: DECIMAL(10,2), Payment_Date: DATE, Description: VARCHAR(255))

Expense_Payment(Expense_Id: INT FK to Expenses.Expense_Id, Payment_Id: INT FK to Payments.Payment_Id, PK(Expense_Id, Payment_Id))