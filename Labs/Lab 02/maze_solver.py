def maze_solver_helper(maze: list[list[int]], x: int, y: int, path: list[tuple]) -> bool:
    if maze[x][y]:
        return False

    maze[x][y] = 1

    if (x, y) == (len(maze) - 1, len(maze[0]) - 1):
        path.append((x, y))
        return True

    elif x < len(maze) - 1 and maze_solver_helper(maze, x + 1, y, path):  # down
        path.append((x, y))
        return True

    elif y < len(maze[0]) - 1 and maze_solver_helper(maze, x, y + 1, path):  # right
        path.append((x, y))
        return True

    elif x > 0 and maze_solver_helper(maze, x - 1, y, path):  # up
        path.append((x, y))
        return True

    elif y > 0 and maze_solver_helper(maze, x, y - 1, path):  # left
        path.append((x, y))
        return True

    else:
        return False


def maze_solver(maze: list[list[int]]) -> bool:
    maze = maze.copy()  # do not modify original maze
    path = list()

    if maze_solver_helper(maze, 0, 0, path):
        path.reverse()
        print(path)
        return True
    else:
        print("No path found.")
        return False


test_maze_1 = [
    [0, 0, 1, 0, 0, 0, 1, 0, 0, 0],
    [1, 0, 1, 0, 1, 0, 1, 0, 1, 0],
    [1, 0, 0, 0, 1, 0, 0, 0, 1, 0],
    [1, 1, 1, 0, 1, 1, 1, 0, 1, 0],
    [0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
    [0, 1, 1, 1, 1, 0, 1, 1, 1, 0],
    [0, 1, 0, 0, 0, 0, 0, 0, 1, 0],
    [0, 1, 0, 1, 1, 1, 1, 0, 1, 0],
    [0, 0, 0, 1, 0, 0, 0, 0, 0, 0],
    [1, 1, 0, 1, 0, 1, 1, 1, 1, 0],
]

print("Test maze 1:")
maze_solver(test_maze_1)
print()

test_maze_2 = [
    [0, 0, 1, 0, 0, 0, 1, 0, 0, 0],
    [1, 0, 1, 0, 1, 0, 0, 0, 1, 0],
    [1, 0, 0, 0, 1, 1, 1, 1, 1, 0],
    [1, 1, 1, 0, 1, 1, 1, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 1, 0, 1, 1],
    [0, 1, 1, 1, 1, 0, 1, 0, 0, 0],
    [0, 1, 0, 0, 0, 0, 0, 1, 1, 0],
    [0, 1, 0, 1, 1, 1, 1, 1, 1, 0],
    [0, 0, 0, 1, 0, 0, 0, 0, 1, 0],
    [1, 1, 0, 0, 0, 1, 1, 1, 1, 0],
]

print("Test maze 2:")
maze_solver(test_maze_2)
print()

test_maze_3 = [
    [0, 0, 1, 0, 0, 0, 1, 0, 0, 0],
    [1, 0, 1, 0, 1, 0, 1, 0, 1, 0],
    [1, 0, 0, 0, 1, 0, 0, 0, 1, 0],
    [1, 1, 1, 0, 1, 1, 1, 0, 1, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 1, 1],  # Blocked exit
    [0, 1, 1, 1, 1, 0, 1, 0, 1, 0],
    [0, 1, 0, 0, 0, 0, 0, 1, 1, 0],
    [0, 1, 0, 1, 1, 1, 1, 1, 1, 0],
    [0, 0, 0, 1, 0, 0, 0, 0, 1, 0],
    [1, 1, 0, 0, 0, 1, 1, 1, 1, 0],
]

print("Test maze 3:")
maze_solver(test_maze_3)
print()

test_maze_4 = [
    [0]
]

print("Test maze 4:")
maze_solver(test_maze_4)
print()

test_maze_5 = [
    [1]
]

print("Test maze 5:")
maze_solver(test_maze_5)
print()
