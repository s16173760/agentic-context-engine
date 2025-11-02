"""
Buggy code samples for the Code Bug Hunter demo.

Each sample contains a subtle bug that needs to be identified and fixed.
"""

BUGGY_SAMPLES = [
    {
        "id": 1,
        "language": "Python",
        "code": """
class LRUCache:
    def __init__(self, capacity):
        self.capacity = capacity
        self.cache = {}
        self.order = []
    
    def get(self, key):
        if key in self.cache:
            self.order.remove(key)
            self.order.append(key)
            return self.cache[key]
        return -1
    
    def put(self, key, value):
        if key in self.cache:
            self.order.remove(key)
        self.cache[key] = value
        self.order.append(key)
        
        if len(self.cache) > self.capacity:
            oldest = self.order.pop(0)
            del self.cache[oldest]

# Test
cache = LRUCache(2)
cache.put(1, 1)
cache.put(2, 2)
print(cache.get(1))  # returns 1
cache.put(3, 3)      # evicts key 2
print(cache.get(2))  # returns -1 (not found)
cache.put(4, 4)      # evicts key 1
print(cache.get(1))  # should return -1, might return 1
print(cache.get(3))  # returns 3
print(cache.get(4))  # returns 4
""",
        "bug_type": "Race condition with list operations",
        "ground_truth": "List.remove() is O(n) which causes severe performance degradation. More critically, when updating existing key, order.remove(key) followed by order.append(key) can cause issues if key appears multiple times in order list (which shouldn't happen but isn't prevented). Should use OrderedDict or custom doubly-linked list for O(1) operations. The fundamental flaw is using list for order tracking instead of a proper data structure.",
        "severity": "critical"
    },
    {
        "id": 2,
        "language": "Python",
        "code": """
def find_median_sorted_arrays(nums1, nums2):
    merged = []
    i, j = 0, 0
    
    while i < len(nums1) and j < len(nums2):
        if nums1[i] < nums2[j]:
            merged.append(nums1[i])
            i += 1
        else:
            merged.append(nums2[j])
            j += 1
    
    while i < len(nums1):
        merged.append(nums1[i])
        i += 1
    
    while j < len(nums2):
        merged.append(nums2[j])
        j += 1
    
    n = len(merged)
    if n % 2 == 0:
        return (merged[n//2] + merged[n//2 - 1]) / 2
    else:
        return merged[n//2]

# Test cases
print(find_median_sorted_arrays([1, 3], [2]))           # Expected: 2.0
print(find_median_sorted_arrays([1, 2], [3, 4]))        # Expected: 2.5
print(find_median_sorted_arrays([], [1]))               # Expected: 1
print(find_median_sorted_arrays([100000], [100001]))    # Expected: 100000.5
""",
        "bug_type": "Algorithm efficiency violation",
        "ground_truth": "This O(m+n) space and time solution violates the expected O(log(min(m,n))) complexity for finding median of two sorted arrays. While functionally correct for small inputs, it fails the implicit efficiency requirement. The correct approach uses binary search to partition arrays without merging. This is a design flaw where a naive solution masks the need for sophisticated algorithmic thinking. Additionally, there's potential integer overflow risk when adding merged[n//2] + merged[n//2-1] for very large numbers, though Python handles this.",
        "severity": "high"
    },
    {
        "id": 3,
        "language": "Python",
        "code": """
class EventEmitter:
    def __init__(self):
        self.listeners = {}
    
    def on(self, event, callback):
        if event not in self.listeners:
            self.listeners[event] = []
        self.listeners[event].append(callback)
    
    def emit(self, event, *args):
        if event in self.listeners:
            for callback in self.listeners[event]:
                callback(*args)
    
    def remove_listener(self, event, callback):
        if event in self.listeners:
            self.listeners[event].remove(callback)

# Test
emitter = EventEmitter()

def handler1(data):
    print(f"Handler 1: {data}")
    if data > 5:
        emitter.remove_listener('data', handler2)

def handler2(data):
    print(f"Handler 2: {data}")

emitter.on('data', handler1)
emitter.on('data', handler2)

for i in range(10):
    emitter.emit('data', i)
""",
        "bug_type": "Iterator modification during iteration",
        "ground_truth": "Modifying self.listeners[event] list during iteration in emit() causes undefined behavior. When handler1 calls remove_listener() during emit(), it removes handler2 from the list being iterated, causing handler2 to be skipped or raising ValueError. This is a classic reentrancy bug. Fix requires iterating over a copy: 'for callback in self.listeners[event][:]:' or using a deferred removal queue. Additionally, remove() will raise ValueError if callback not found - should use 'if callback in self.listeners[event]: self.listeners[event].remove(callback)'.",
        "severity": "critical"
    },
    {
        "id": 4,
        "language": "Python",
        "code": """
def calculate_portfolio_returns(prices, weights):
    \"\"\"
    Calculate weighted portfolio returns.
    prices: dict of {asset: [price_t0, price_t1, ...]}
    weights: dict of {asset: weight} where sum of weights = 1.0
    Returns: list of period returns
    \"\"\"
    assets = list(prices.keys())
    periods = len(prices[assets[0]])
    returns = []
    
    for i in range(periods - 1):
        period_return = 0
        for asset in assets:
            price_change = (prices[asset][i+1] - prices[asset][i]) / prices[asset][i]
            weighted_return = price_change * weights[asset]
            period_return += weighted_return
        returns.append(period_return)
    
    return returns

# Test
prices = {
    'AAPL': [100, 105, 103, 108],
    'GOOGL': [1500, 1520, 1510, 1530],
    'MSFT': [200, 198, 202, 205]
}

weights = {
    'AAPL': 0.4,
    'GOOGL': 0.35,
    'MSFT': 0.25
}

returns = calculate_portfolio_returns(prices, weights)
print(f"Portfolio returns: {returns}")
print(f"Total return: {sum(returns):.2%}")
""",
        "bug_type": "Floating point precision and compounding error",
        "ground_truth": "Multiple critical bugs: (1) Doesn't validate that sum(weights.values()) == 1.0, allowing incorrect calculations. (2) Doesn't validate all assets have same number of price points, causing IndexError if lengths differ. (3) Doesn't handle zero or negative prices which cause division by zero or incorrect returns. (4) Summing period returns to get total return is mathematically incorrect - should use compounding: (1+r1)*(1+r2)*...-1. (5) No handling of missing assets in weights vs prices. (6) Floating point comparison issues if checking weight sum. This requires deep financial mathematics understanding to catch all issues.",
        "severity": "critical"
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


def get_all_samples():
    """
    Get all bug samples for the race.
    
    The playbook is pre-trained with strategies for ALL samples,
    so both baseline and ACE see the same samples during the race.
    
    Returns:
        list: All 10 buggy code samples
    """
    return BUGGY_SAMPLES


def get_race_samples(count=4):
    """
    Get a subset of samples for the demo race.
    
    Args:
        count: Number of samples to return (default 4)
    
    Returns:
        list: First `count` buggy code samples
    """
    return BUGGY_SAMPLES[:count]

