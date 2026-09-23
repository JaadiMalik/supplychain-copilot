from app.analytics.service import ask_data


question = input(
    "\nAsk about inventory data: "
)

result = ask_data(question)


print("\nSTATUS")
print("=" * 60)
print(result["status"])


print("\nGENERATED SQL")
print("=" * 60)
print(result.get("sql"))


print("\nRESULT")
print("=" * 60)

for row in result.get("results", []):
    print(row)