# Lab Week 13

Due May 5 by 11:59pm | Points 10 | Submitting a file upload | Available until May 7 at 11:59pm

## Lab Assignment: Implementing Directed Graphs for a City Transportation Network

### Background

Graph theory is a significant area in computer science and mathematics that studies the properties of graphs. It has
vast applications, including in transportation networks. In this lab assignment, you will use graph theory to model a
simplified transportation network of a fictional city. You will implement a directed graph to represent connections
between different locations in the city and use traversal algorithms to find routes.

### Objective

Your task is to create a Python program that models the city's transportation network using a directed graph. Each node
in the graph will represent a landmark, and each edge will represent a road between the landmarks. You will implement
both BFS and DFS traversal methods to find all landmarks reachable from a given starting point.

### Requirements

1. Graph Implementation:
    - Implement a `Graph` class that uses adjacency lists or matrices to keep track of edges.
    - Implement `addVertex` and `addEdge` methods for the `Graph` class.
    - Ensure that your graph can handle `String` identifiers for vertices.

2. Traversal Algorithms:
    - Implement a method in your `Graph` class for BFS that prints out the order of landmarks visited.
    - Implement a method in your `Graph` class for DFS using a stack that prints out the order of landmarks visited.

3. Testing Your Network:
    - Create a method to instantiate a sample city network with at least 10 landmarks and 15 roads.
    - Demonstrate both BFS and DFS traversals starting from a given landmark.

4. Real-World Application - Route Finding:
    - Implement a function that uses BFS to find the shortest path (in terms of the number of edges) from one landmark
      to another if one exists.
    - Print out the route (sequence of landmarks) of the shortest path.

5. Analysis:
    - Write a brief analysis of the differences between BFS and DFS in the context of your transportation network.
    - Discuss the scenarios in which one might be preferred over the other.

### Deliverables

1. **Source Code**: A `.py`/`.ipynb` file containing your graph implementation and traversal methods.
2. **Documentation**: Submit output screenshots.
3. **Report**: A document detailing your implementation, test cases, results, and your analysis of BFS vs. DFS in this
   application.
