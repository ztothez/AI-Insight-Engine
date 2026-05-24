"""Single function doing 6 unrelated things — clean code violation."""

ID = "clean_god_function_01"
CATEGORY = "clean_code_violation"
LANGUAGE = "python"
STRICTNESS = 3
CODE = '''def process_order(order_data):
    # Validate the order
    if not order_data.get("items"):
        raise ValueError("No items")
    if order_data.get("total", 0) <= 0:
        raise ValueError("Invalid total")

    # Calculate tax
    tax = order_data["total"] * 0.24
    order_data["tax"] = tax
    order_data["grand_total"] = order_data["total"] + tax

    # Send confirmation email
    import smtplib
    server = smtplib.SMTP("smtp.example.com", 587)
    server.login("noreply@example.com", "password123")
    server.sendmail("noreply@example.com", order_data["email"],
                    f"Subject: Order\\n\\nYour total is {order_data['grand_total']}")
    server.quit()

    # Save to database
    import sqlite3
    conn = sqlite3.connect("orders.db")
    conn.execute("INSERT INTO orders VALUES (?, ?, ?)",
                 (order_data["id"], order_data["email"], order_data["grand_total"]))
    conn.commit()

    # Log to file
    with open("/var/log/orders.log", "a") as f:
        f.write(f"Order {order_data['id']} processed\\n")

    # Trigger fulfillment webhook
    import requests
    requests.post("https://warehouse.example.com/fulfill", json=order_data)

    return order_data
'''
EXPECTED = {
    "maintainability_score_max": 5.0,
    "should_contain_violations": ["function", "responsibility"],
    "should_have_citations": True,
}
