def fibonacci_extension(high, low, pullback):
    fib_levels = [1.272, 1.618, 2.000, 2.618]
    extension_levels = {f"{level*100:.1f}%": pullback + (high - low) * level for level in fib_levels}
    return extension_levels

high_price = 109500
low_price = 76600
pullback_price = 93050  # 50% 回撤位

extension = fibonacci_extension(high_price, low_price, pullback_price)
for level, price in extension.items():
    print(f"{level} 扩展位: {price:.2f}")
