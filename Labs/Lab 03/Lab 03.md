# Lab Week 3

Due Feb 17 by 11:59pm | Points 10  | Submitting a file upload | Available until Feb 19 at 11:59pm 

## Overview

Imagine you work for a retail company that needs to process sales records. Each record contains:

* A unique **sale ID**.
* A **sale date**.
* The **amount** of the sale.
* The **product name** sold.

Your program will offer the options to:

1. **Load in sales data** (reading from a CSV or database).
2. **Retrieve the latest sale**
3. **Compute the total revenue**
4. **Check for duplicate sale IDs**
5. **Search for a sale by its ID**

You will measure the performance of these operations and compare them against their theoretical Big O time complexity.

---

## Example CSV Content

    sale_id,sale_date,amount,product
    0,2024-01-15,150.00,Widget
    1,2024-02-20,200.50,Gadget
    2,2024-03-12,99.99,Thingamajig
    3,2024-04-25,250.75,Doohickey
    4,2024-05-10,125.30,Widget
    5,2024-06-15,300.00,Gadget
    6,2024-07-20,175.25,Thingamajig
    7,2024-08-30,99.99,Doohickey
    8,2024-09-05,220.10,Widget
    9,2024-10-12,199.99,Gadget

You will need to generate python code to randomly generate n number of data to store in a CSV for testing purposes. You will measure the time each operation takes at dataset sizes of 100, 1.000, 10.000, and 100.000 (if possible) and graph your results.

---

## Reflection

After running your pipeline with different input sizes, consider the following:

1. **Performance Trends:**
   - How does each operation’s execution time change as the dataset grows?
   - Do the results align with the theoretical Big O expectations?

2. **Real-World Implications:**
   - Which steps might become bottlenecks in a production system processing millions of records?
   - How would you optimize or replace the inefficient (quadratic) approach?

3. **Practical Adjustments:**
   - How might you put together a testing plan for this project?
   - What additional error handling or data validation would be necessary?

---

## Submission Guidelines

- **Code:** Submit your complete Python script with clear comments.
- **Report:** Provide your analysis and reflections either as inline comments at the bottom of your script or in a separate document (PDF/Markdown).

