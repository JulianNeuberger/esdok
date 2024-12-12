import json

with open("results.json", "r") as f:
    data = json.load(f)

for k in data:
    print("------------------------------------------")
    print("----", k)
    print("------------------------------------------")

    for m in data[k]:
        m_val = sum(data[k][m]) / len(data[k][m])
        print(f"{m}: {m_val:.2f}")