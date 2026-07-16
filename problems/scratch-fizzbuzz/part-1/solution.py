def fizzbuzz(n):
    out = ""
    if n % 3 == 0:
        out += "fizz"
    if n % 5 == 0:
        out += "buzz"
    return out or str(n)
