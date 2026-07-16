def outstanding_balance(principal, events):
    # walk the events and knock down the balance
    bal = principal
    for e in events:
        bal = bal - e["amount"]
    return {"outstanding": bal}
