PEAK_GFLOPS = 836 * (10**9)

def flops(elapsed):
    return (2**37 / elapsed)

def ratio(elapsed):
    r = (flops(elapsed) / PEAK_GFLOPS) * 100
    print(f"{r:.6f}%")
