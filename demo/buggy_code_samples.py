"""
Buggy code samples for the Code Bug Hunter demo.

Each sample contains a subtle bug that needs to be identified and fixed.
"""

BUGGY_SAMPLES = [
    {
        "id": 1,
        "language": "Python",
        "code": """
def calculate_average(numbers):
    total = 0
    for i in range(len(numbers)):
        total += numbers[i]
    return total / len(numbers)

# Test
scores = [85, 90, 78, 92, 88]
avg = calculate_average(scores)
print(f"Average: {avg}")
""",
        "bug_type": "Division by zero",
        "ground_truth": "Missing check for empty list - will crash with ZeroDivisionError if numbers list is empty",
        "severity": "high"
    },
    {
        "id": 2,
        "language": "Python",
        "code": """
def find_max_index(arr):
    max_val = arr[0]
    max_idx = 0
    for i in range(len(arr)):
        if arr[i] > max_val:
            max_val = arr[i]
            max_idx = i
    return max_idx

# Test
data = [3, 7, 2, 9, 1]
print(find_max_index(data))
""",
        "bug_type": "Off-by-one error",
        "ground_truth": "Loop should use range(1, len(arr)) to skip first element which is already set as max_val",
        "severity": "medium"
    },
    {
        "id": 3,
        "language": "Python",
        "code": """
def merge_dicts(dict1, dict2):
    result = dict1
    for key, value in dict2.items():
        result[key] = value
    return result

# Test
a = {"x": 1, "y": 2}
b = {"y": 3, "z": 4}
merged = merge_dicts(a, b)
print(f"Merged: {merged}")
print(f"Original a: {a}")
""",
        "bug_type": "Mutation bug",
        "ground_truth": "Function mutates dict1 instead of creating a new dict. Should use result = dict1.copy()",
        "severity": "high"
    },
    {
        "id": 4,
        "language": "Python",
        "code": """
def remove_duplicates(items):
    unique = []
    for item in items:
        if item not in unique:
            unique.append(item)
    return unique

# Test
numbers = [1, 2, 2, 3, 4, 4, 5]
print(remove_duplicates(numbers))
""",
        "bug_type": "Performance issue",
        "ground_truth": "O(n²) complexity - 'item not in unique' is O(n). Should use a set for O(1) lookups",
        "severity": "low"
    },
    {
        "id": 5,
        "language": "Python",
        "code": """
class Counter:
    def __init__(self):
        self.count = 0
    
    def increment(self):
        self.count += 1
    
    def reset(self):
        self.count == 0

# Test
c = Counter()
c.increment()
c.increment()
c.reset()
print(c.count)  # Expected: 0, Actual: 2
""",
        "bug_type": "Logic error",
        "ground_truth": "reset() uses comparison (==) instead of assignment (=). Should be self.count = 0",
        "severity": "high"
    },
    {
        "id": 6,
        "language": "Python",
        "code": """
def get_user_data(user_id):
    users = {
        1: {"name": "Alice", "age": 30},
        2: {"name": "Bob", "age": 25}
    }
    return users[user_id]

# Test
print(get_user_data(1))
print(get_user_data(3))  # Will crash
""",
        "bug_type": "Missing error handling",
        "ground_truth": "No KeyError handling for invalid user_id. Should use users.get(user_id) or try/except",
        "severity": "high"
    },
    {
        "id": 7,
        "language": "Python",
        "code": """
def process_items(items):
    results = []
    for item in items:
        if item > 0:
            results.append(item * 2)
        elif item < 0:
            results.append(item * -1)
    return results

# Test
nums = [1, -2, 0, 3, -4]
print(process_items(nums))  # Missing 0
""",
        "bug_type": "Missing case",
        "ground_truth": "Zero values are silently dropped. Should handle item == 0 case or document behavior",
        "severity": "medium"
    },
    {
        "id": 8,
        "language": "Python",
        "code": """
def calculate_discount(price, discount_pct):
    discount = price * discount_pct
    final_price = price - discount
    return final_price

# Test
original = 100
discount = calculate_discount(original, 20)
print(f"Price: ${discount}")  # Expected: $80, Actual: $-1900
""",
        "bug_type": "Unit confusion",
        "ground_truth": "discount_pct should be divided by 100 or passed as 0.20 instead of 20. Percentage not converted to decimal",
        "severity": "high"
    },
    {
        "id": 9,
        "language": "Python",
        "code": """
def safe_divide(a, b):
    try:
        return a / b
    except:
        return 0

# Test
print(safe_divide(10, 2))   # 5.0
print(safe_divide(10, 0))   # 0
print(safe_divide("10", 2))  # 0 - silently fails
""",
        "bug_type": "Overly broad exception",
        "ground_truth": "Bare except catches all exceptions including TypeError. Should catch ZeroDivisionError specifically",
        "severity": "medium"
    },
    {
        "id": 10,
        "language": "Python",
        "code": """
def filter_even_numbers(numbers):
    for num in numbers:
        if num % 2 == 0:
            numbers.remove(num)
    return numbers

# Test
data = [1, 2, 3, 4, 5, 6, 7, 8]
result = filter_even_numbers(data)
print(result)  # Expected: [1, 3, 5, 7], Actual: [1, 3, 5, 7] but misses some
""",
        "bug_type": "Iterator modification",
        "ground_truth": "Modifying list while iterating causes skipped elements. Should use list comprehension or iterate over copy",
        "severity": "high"
    }
]


def get_train_test_split(train_size=6):
    """
    Split samples into training and test sets.
    
    Training samples (first 6):
        - Used to build ACE's playbook with learned strategies
        - ACE learns from mistakes on these samples
        
    Test samples (last 4):
        - Used for the actual race comparison
        - Baseline sees these fresh (no learning)
        - ACE applies its learned strategies
    
    Args:
        train_size: Number of samples for training (default 6, leaves 4 for testing)
    
    Returns:
        tuple: (train_samples, test_samples)
    """
    train = BUGGY_SAMPLES[:train_size]
    test = BUGGY_SAMPLES[train_size:]
    return train, test

