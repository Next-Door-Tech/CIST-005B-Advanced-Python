# Reflection

After running your pipeline with different input sizes, consider the following:

### **Performance Trends:**

How does each operation’s execution time change as the dataset grows?

1. Load in sales data: O(n)

       10      ->     239045 ns
       100     ->     577196 ns
       1000    ->    3908415 ns    # ~= prev * 10
       10000   ->   37766568 ns    # ~= prev * 10
       100000  ->  296913544 ns    # ~= prev * 10

2. Retrieve the latest sale: O(n log n) without indexing, O(1) with indexing

       ## no indexing ##
       10      ->     20079 ns
       100     ->     67051 ns
       1000    ->    546505 ns    # ~= prev * 10
       10000   ->   5687435 ns    # ~= prev * 10
       100000  ->  64667206 ns    # ~= prev * 10

       ## with indexing ##
       10      ->  5825 ns
       100     ->  5914 ns
       1000    ->  5256 ns
       10000   ->  5352 ns
       100000  ->  6460 ns

3. Compute the total revenue: O(n)

       10      ->     13794 ns
       100     ->     31400 ns
       1000    ->    207601 ns    # ~= prev * 10
       10000   ->   2001312 ns    # ~= prev * 10
       100000  ->  16740883 ns    # ~= prev * 10

4. Check for duplicate sale IDs: O(n) without indexing, O(n) with indexing

       ## no indexing ##
       10      ->     20964 ns
       100     ->     51497 ns
       1000    ->    304500 ns
       10000   ->   3585332 ns    # ~= prev * 10 * 5/4
       100000  ->  45262914 ns    # ~= prev * 10 * 6/5
       
       ## with indexing ##
       10      ->     6963 ns
       100     ->    14492 ns
       1000    ->    58598 ns
       10000   ->   389460 ns    # ~= prev * 10
       100000  ->  3844313 ns    # ~= prev * 10

5. Search for a sale by its ID: O(n) without indexing, O(1) with indexing

       ## no indexing ##
       10      ->     16081 ns
       100     ->     52651 ns
       1000    ->    291523 ns
       10000   ->   x ns    # ~= prev * 10 * 4/3
       100000  ->  x ns    # ~= prev * 10 * 5/4
       
       ## with indexing ##
       10      ->     3749 ns
       100     ->    4359 ns
       1000    ->    x ns
       10000   ->   x ns
       100000  ->  x ns


- Do the results align with the theoretical Big O expectations? 
  1. Load in sales data: Theoretical is O(n), so results are consistent
  2. Retrieve the latest sale: This could be done in O(n) time without building the index, so with no index cached my O(n log(n)) algorithm is slow. However, with the index built, my algorithm is O(1).
  3. Compute the total revenue: Without caching the total (which I did not implement) any algorithm is O(n), so mine matches the ideal.
  4. Check for duplicate sale IDs: The ideal case is O(n). Both my cached and uncached algorithms are O(n) (though the cache is still much faster).
  5. Search for a sale by its ID:

### **Real-World Implications:**

- Which steps might become bottlenecks in a production system processing millions of records?

        

- How would you optimize or replace the inefficient (quadratic) approach?

        Who says any of the approaches I used were quadratic? ;)

### **Practical Adjustments:**
- How might you put together a testing plan for this project?

    

- What additional error handling or data validation would be necessary?
