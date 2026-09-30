"""Local fitted retaining-pin centreline; bend lies outside the rod bore."""
def retaining_pin_points():
    return [(.0353,-.004+.007*j/24,0) for j in range(25)]+[(.0353,.003+.001*j/8,.0012*j/8) for j in range(1,9)]
