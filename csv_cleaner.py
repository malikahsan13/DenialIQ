import pandas as pd

df = pd.read_csv("card_rarc_codes.csv")

# Remove rows where column B contains "Start:"
#df = df[~df.iloc[:, 1].astype(str).str.contains("Start:", case=False, na=False)]
df = df[~df.iloc[:, 1].astype(str).str.contains("Notes:", case=False, na=False)]


df.to_csv("output.csv", index=False)