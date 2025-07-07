def fibonacci_retracement(high, low):
    fib_levels = [0.236, 0.382, 0.5, 0.618, 0.786]
    retracement_levels = {f"{level*100:.1f}%": low + (high - low) * level for level in fib_levels}
    return retracement_levels

high_price = 85300  # 最高点
low_price = 76600    # 最低点

retracement = fibonacci_retracement(high_price, low_price)
for level, price in retracement.items():
    print(f"{level} 回撤位: {price:.2f}")