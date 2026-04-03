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
 the total owed per user per circle.