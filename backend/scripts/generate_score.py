import pandas as pd
from openai import OpenAI
import re
from dotenv import load_dotenv
load_dotenv()
import os
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
file_path = "backend/data/logs/evaluation.xlsx"
# file_path = "backend/data/logs/gemini.xlsx"
df = pd.read_excel(file_path)
df = df.sample(frac=1).reset_index(drop=True)
def get_gpt_score(row):
    """
    Send row data to ChatGPT for scoring using English prompts.
    """
    player_input = str(row['player_input'])
    narrative_text = str(row['narrative_text'])

    system_prompt = (
        "You are an expert critic for text-based RPG games. "
        "Your task is to evaluate the AI Dungeon Master's performance based on the player's input. "
        "You must output ONLY a single integer from 1 to 5."


        
    )
    

    user_prompt = f"""
    Please rate the AI DM's response on a scale of 1 to 5 based on the interaction below, specifically focusing on these two dimensions:

    1. **Rule Consistency**: Whether actions resolve with appropriate checks, logical outcomes, and correct state tracking (e.g., health, inventory).
    2. **Narrative Quality**: Clarity, engagement, and responsiveness to the player's specific input.

    [Scoring Rubric]
    1 (Terrible): Fails both criteria significantly. Rules are broken (e.g., logical contradictions), and narrative is confusing or completely ignores the player.
    2 (Poor): Major issues in either rules (e.g., ignoring a clear action) or narrative (e.g., extremely dry, repetitive, or nonsensical).
    3 (Average): Functional. Rules are generally followed with no glaring errors; narrative is clear but lacks engagement or "flavor".
    4 (Good): Strong performance. Actions resolve logically with appropriate outcomes; the writing is engaging and responsive.
    5 (Excellent): Flawless execution. Mechanics are handled perfectly (appropriate checks/consequences), and the narrative is highly immersive and creatively responds to the user.

    [Interaction]
    Player Input: "{player_input}"
    AI DM Response: "{narrative_text}"

    [Output Requirement]
    Output ONLY the integer score (e.g., 5). Do not add any explanation, labels, or punctuation.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini", 
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.0, 
            max_tokens=5
        )
        
        content = response.choices[0].message.content.strip()
        
        match = re.search(r'\d', content)
        if match:
            return int(match.group())
        else:
            return None
            
    except Exception as e:
        print(f"Error processing row: {e}")
        return None

print("Starting evaluation with English prompts...")

df['gpt_score'] = df.apply(get_gpt_score, axis=1)


df.to_excel(file_path, index=False)

print(f"Done! Saved to {file_path}")
print(df[['player_input', 'gpt_score']].head())