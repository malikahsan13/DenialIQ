import pandas as pd
from langchain.schema import Document

df = pd.read_csv("carc_rarc_codes.csv")

csv_docs = []
for _, row in df.iterrows():
    text = f"""
    Code: {row['code']}
    Type: {row['type']}
    Description: {row['description']}
    Group Code: {row.get('group_code', '')}
    """

    csv_docs.append(
        Document(
            page_content=text.strip(),
            metadata={
                "type": row["type"],
                "code": row["code"],
                "source": "CARC_RARC_CSV"
            }
        )
    )
