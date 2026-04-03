# Database Design

## Team
Team 105 - TeamFreak

## Schema Overview
Our database models an expense-sharing application with the following tables:
- Users
- Circle
- Circle_Member
- Expense
- Expense_Split
- Payments
- Expense_Payment


### DDL Commands

CREATE TABLE `teamfreakdata`.Users(
  User_Id INT PRIMARY KEY AUTO_INCREMENT,
  Name VARCHAR(100) NOT NULL,
  Email VARCHAR(255) NOT NULL UNIQUE,
  Password_Hash VARCHAR(255) NOT NULL,
  Date_Joined DATE NOT NULL
);

CREATE TABLE `teamfreakdata`.Circle (
  Circle_Id INT PRIMARY KEY AUTO_INCREMENT,
  Circle_Name VARCHAR(100) NOT NULL,
  Creation_Date DATE NOT NULL,
  Creation_User_Id INT NOT NULL,
  FOREIGN KEY (Creation_User_Id) REFERENCES Users(User_Id)
);

CREATE TABLE `teamfreakdata`.Circle_Member (
  Circle_Id INT NOT NULL,
  User_Id INT NOT NULL,
  Role VARCHAR(50) NOT NULL,
  Status ENUM('Invited', 'Active', 'Left', 'Rejected') NOT NULL,
  Date_Joined DATE,
  PRIMARY KEY (Circle_Id, User_Id),
  FOREIGN KEY (Circle_Id) REFERENCES Circle(Circle_Id),
  FOREIGN KEY (User_Id) REFERENCES Users(User_Id)
);

CREATE TABLE `teamfreakdata`.Expense(
  Expense_Id INT PRIMARY KEY AUTO_INCREMENT,
  Amount DECIMAL(10,2) NOT NULL,
  Circle_Id INT NOT NULL,
  User_Id INT NOT NULL,
  Creation_Date DATE NOT NULL,
  Paid_Date DATE,
  Status ENUM('Active', 'Settled', 'Overdue', 'Canceled') NOT NULL,
  Description TEXT,
  Split_Type ENUM('Even', 'Percent', 'Custom') NOT NULL,
  FOREIGN KEY (Circle_Id) REFERENCES Circle(Circle_Id),
  FOREIGN KEY (User_Id) REFERENCES Users(User_Id)
);


CREATE TABLE `teamfreakdata`.Expense_Split (
  Expense_Id INT NOT NULL,
  User_Id INT NOT NULL,
  Amount_Owed DECIMAL(10,2) NOT NULL,
  PRIMARY KEY (Expense_Id, User_Id),
  FOREIGN KEY (Expense_Id) REFERENCES Expense(Expense_Id),
  FOREIGN KEY (User_Id) REFERENCES Users(User_Id)
);


CREATE TABLE `teamfreakdata`.Payments(
  Payment_Id INT PRIMARY KEY AUTO_INCREMENT,
  Sender_Id INT NOT NULL,
  Receiver_Id INT NOT NULL,
  Circle_Id INT NOT NULL,
  Amount DECIMAL(10,2) NOT NULL,
  Payment_Date DATE NOT NULL,
  Description TEXT,
  FOREIGN KEY (Sender_Id) REFERENCES Users(User_Id),
  FOREIGN KEY (Receiver_Id) REFERENCES Users(User_Id),
  FOREIGN KEY (Circle_Id) REFERENCES Circle(Circle_Id)
);

CREATE TABLE `teamfreakdata`.Expense_Payment  (

  Expense_Id INT NOT NULL,
  Payment_Id INT NOT NULL,
  PRIMARY KEY (Expense_Id, Payment_Id),
  FOREIGN KEY (Expense_Id) REFERENCES Expense(Expense_Id),
  FOREIGN KEY (Payment_Id) REFERENCES Payments(Payment_Id)
);



####Advanced Queries:


SELECT
    u.User_Id,
    u.Name,
    c.Circle_Id,
    c.Circle_Name,
    SUM(es.Amount_Owed) AS Total_Amount_Owed
FROM Users u
JOIN Expense_Split es
    ON u.User_Id = es.User_Id
JOIN Expense e ON es.Expense_Id = e.Expense_Id
JOIN Circle c ON e.Circle_Id = c.Circle_Id
GROUP BY u.User_Id, u.Name, c.Circle_Id, c.Circle_Name
ORDER BY Total_Amount_Owed DESC
LIMIT 15;

This advanced query computes the total amount owed by each user within each circle.
 It joins the Users, Expense_Split, Expense, and Circle tables to associate users
 with their expense splits and corresponding circles. The query then aggregates the
 Amount_Owed values using SUM and groups the results by user and circle to produce
 the total owed per user per circle. In the future this will be one of our most commonly
 used queries as this information is very relevant for each individual user.


SELECT 
    es1.User_Id AS Debtor,
    es2.User_Id AS Creditor,
    e.Circle_Id,
    SUM(es1.Amount_Owed - es2.Amount_Owed) AS Net_Balance
FROM Expense e
JOIN Expense_Split es1 
    ON e.Expense_Id = es1.Expense_Id
JOIN Expense_Split es2 
    ON e.Expense_Id = es2.Expense_Id
WHERE es1.User_Id <> es2.User_Id
GROUP BY es1.User_Id, es2.User_Id, e.Circle_Id
HAVING Net_Balance > 0
ORDER BY Net_Balance DESC
LIMIT 15;

This advanced query computes the net balance between pairs of users within each circle to 
determine who owes whom. It joins the Expense table with the Expense_Split table twice to 
compare the amounts owed by different users participating in the same expense. The query aggregates 
the differences in owed amounts using SUM and groups the results by debtor, creditor, and circle.
The HAVING clause filters to include only positive balances, indicating outstanding debts between users. 
This query can be used in the future to power features such as real-time balance tracking and simplified 
settlement suggestions, helping users minimize the number of transactions needed to settle debts.


SELECT 
    u.User_Id,
    u.Name,
    COUNT(e.Expense_Id) AS Overdue_Expenses
FROM Users u
JOIN Expense e 
    ON u.User_Id = e.User_Id
WHERE e.Status = 'Overdue'
   OR e.Paid_Date > (
        SELECT AVG(e2.Paid_Date)
        FROM Expense e2
        WHERE e2.User_Id = u.User_Id
    )
GROUP BY u.User_Id, u.Name
ORDER BY Overdue_Expenses DESC
LIMIT 15;

This advanced query identifies users with overdue or relatively late payments to support reliability 
analysis. It joins the Users and Expense tables to associate each user with their recorded expenses. 
The query counts overdue expenses and uses a correlated subquery to compare each payment date against 
the user’s average payment date. The results are aggregated using COUNT and grouped by user, producing 
a list of users ranked by the number of overdue or late payments. This query can be used in the future 
to inform a user reliability scoring system, helping predict repayment behavior and build trust within 
social circles.