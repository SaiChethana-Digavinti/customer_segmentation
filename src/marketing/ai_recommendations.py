import os
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from google import genai


# ---------------------------------------------------------
# 1. Load environment variables
# ---------------------------------------------------------

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError(
        "GEMINI_API_KEY not found in .env file"
    )


# ---------------------------------------------------------
# 2. Create Gemini client
# ---------------------------------------------------------

client = genai.Client(
    api_key=api_key
)


# ---------------------------------------------------------
# 3. Load customer segmentation data
# ---------------------------------------------------------

INPUT_FILE = Path(
    "data/processed/customer_recommendations.csv"
)

df = pd.read_csv(INPUT_FILE)

print(
    f"Customers available: {len(df):,}"
)


# ---------------------------------------------------------
# 4. Select only 5 customers for testing
# ---------------------------------------------------------

test_customers = df.head(5).copy()

print(
    f"Testing AI recommendations for "
    f"{len(test_customers)} customers..."
)


# ---------------------------------------------------------
# 5. Function to generate AI message
# ---------------------------------------------------------

def generate_marketing_message(customer):

    prompt = f"""
You are a professional customer marketing assistant.

Create a short, personalized marketing message
for the following customer.

Customer information:
Customer ID: {customer['CustomerID']}
Segment: {customer['Segment']}
Recency: {customer['Recency']} days
Purchase Frequency: {customer['Frequency']}
Total Spending: {customer['Monetary']:.2f}

Marketing Strategy:
{customer['Marketing_Strategy']}

Recommended Action:
{customer['Recommended_Action']}

Campaign:
{customer['Campaign']}

Priority:
{customer['Priority']}

Requirements:
- Write a friendly and professional message.
- Keep it under 80 words.
- Do not mention customer segmentation, RFM,
  machine learning, or internal customer data.
- Do not invent a specific discount percentage.
- Include a clear call to action.
"""

    response = client.models.generate_content(
        model="gemini-3.1-flash-lite",
        contents=prompt
    )

    return (response.text or "").strip()


# ---------------------------------------------------------
# 6. Generate messages for test customers
# ---------------------------------------------------------

messages = []

for _, customer in test_customers.iterrows():

    print(
        f"\nGenerating message for Customer "
        f"{int(customer['CustomerID'])}..."
    )

    try:

        message = generate_marketing_message(
            customer
        )

    except Exception as error:

        message = (
            f"AI generation failed: {error}"
        )

    messages.append(message)


# ---------------------------------------------------------
# 7. Add AI messages to dataframe
# ---------------------------------------------------------

test_customers["AI_Marketing_Message"] = messages


# ---------------------------------------------------------
# 8. Display results
# ---------------------------------------------------------

print("\n" + "=" * 70)
print("AI MARKETING RECOMMENDATIONS")
print("=" * 70)

for _, customer in test_customers.iterrows():

    print(
        f"\nCustomer ID: "
        f"{int(customer['CustomerID'])}"
    )

    print(
        f"Segment: {customer['Segment']}"
    )

    print(
        f"Campaign: {customer['Campaign']}"
    )

    print(
        f"AI Message:\n"
        f"{customer['AI_Marketing_Message']}"
    )

    print("-" * 70)


# ---------------------------------------------------------
# 9. Save test results
# ---------------------------------------------------------

OUTPUT_FILE = Path(
    "data/processed/ai_test_recommendations.csv"
)

test_customers.to_csv(
    OUTPUT_FILE,
    index=False
)


print(
    "\nTest results saved to:"
)

print(OUTPUT_FILE)