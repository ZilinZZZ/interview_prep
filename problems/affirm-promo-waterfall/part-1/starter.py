def apply_promo(purchase_amount, promos):
    promo = promos[0]
    if promo["type"] == "percent_off":
        discount = purchase_amount * promo["value"] / 100
    else:
        discount = promo["value"]
    final_amount = purchase_amount - discount
    return {
        "purchase_amount": purchase_amount,
        "discount_amount": discount,
        "final_amount": final_amount,
    }
