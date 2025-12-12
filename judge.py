import google.generativeai as genai
from dotenv import load_dotenv
import json
import os
import glob
import difflib

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-flash-latest')

def evaluate_hallucination(response, context):
    prompt = f"""
    You are a strict fact-checking judge.
    
    TASK:
    Compare the AI RESPONSE against the provided SOURCE CONTEXT.
    Determine if the AI response contains any information NOT present in the context (Hallucination).
    
    SOURCE CONTEXT:
    {context}
    
    AI RESPONSE:
    {response}
    
    OUTPUT FORMAT (JSON ONLY):
    {{
        "is_hallucination": "yes" or "no",
        "score": 0.0 to 1.0 (1.0 = perfectly faithful, 0.0 = complete hallucination),
        "reason": "short explanation of any errors"
    }}
    """
    
    result = model.generate_content(
        prompt,
        generation_config={"response_mime_type": "application/json"}
    )
    
    # Convert the string text into a real Python Dictionary
    return json.loads(result.text)

def evaluate_relevance(user_query, response):
    prompt = f"""
    You are a conversation evaluator.
    
    TASK:
    Rate how relevant and helpful the AI RESPONSE is to the USER QUERY.
    
    USER QUERY:
    {user_query}
    
    AI RESPONSE:
    {response}
    
    OUTPUT FORMAT (JSON ONLY):
    {{
        "relevance_score": 0.0 to 1.0,
        "reasoning": "short explanation"
    }}
    """
    
    # Force JSON output
    result = model.generate_content(
        prompt,
        generation_config={"response_mime_type": "application/json"}
    )
    
    # Parse the text into a dictionary
    return json.loads(result.text)

def load_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)
    
def extract_context(vector_data):
    """
    Reconstructs the 'Truth' text from the vector IDs.
    """
    # Get the list of IDs the AI actually used
    used_ids = vector_data['data']['sources']['vectors_used']
    
    # Get the big database of all available facts
    all_vectors = vector_data['data']['vector_data']
    
    context_text = []
    
    # Find the specific text for each used ID
    for vec in all_vectors:
        if vec['id'] in used_ids:
            # We add the Source ID so the LLM knows where it came from
            context_text.append(f"[Source ID {vec['id']}]: {vec['text']}")
    
    return "\n\n".join(context_text)


def find_matching_turn(vector_data, chat_files):
    ai_response_fingerprint = " ".join(vector_data['data']['sources']['final_response'])
    
    best_match = None
    highest_ratio = 0.0

    for chat in chat_files:
        for i, turn in enumerate(chat['conversation_turns']):
            if turn['role'] == 'AI/Chatbot':
                
                ratio = difflib.SequenceMatcher(None, turn['message'], ai_response_fingerprint).ratio()
                
                if ratio > 0.85 and ratio > highest_ratio:
                    highest_ratio = ratio
                    
                    user_query = chat['conversation_turns'][i-1]['message'] if i > 0 else ""
                    
                    best_match = {
                        "chat_id": chat['chat_id'],
                        "turn_id": turn['turn'],
                        "user_query": user_query,
                        "ai_response": turn['message']
                    }

    return best_match

def main():
    print("--- Starting Evaluation Pipeline ---")
    
    chat_files = [load_file(f) for f in glob.glob("data/*chat*.json")]
    vector_files = [load_file(f) for f in glob.glob("data/*context*.json")]
    
    print(f"Found {len(chat_files)} chat logs and {len(vector_files)} vector logs.")
    
    final_results = []

    for i, v_file in enumerate(vector_files):
        print(f"\nProcessing File #{i+1}...")
        
        match = find_matching_turn(v_file, chat_files)
        
        if not match:
            print("⚠ No matching chat found for this vector file. Skipping.")
            continue
            
        print(f"✔ Found Match! Chat ID: {match['chat_id']}, Turn: {match['turn_id']}")
        
        context_text = extract_context(v_file)
        
        print("   -> Running Hallucination Check...")
        hallucination_grade = evaluate_hallucination(match['ai_response'], context_text)
        
        print("   -> Running Relevance Check...")
        relevance_grade = evaluate_relevance(match['user_query'], match['ai_response'])
        
        result_entry = {
            "chat_id": match['chat_id'],
            "turn_id": match['turn_id'],
            "user_query": match['user_query'],
            "ai_response": match['ai_response'],
            "hallucination_report": hallucination_grade,
            "relevance_report": relevance_grade
        }
        final_results.append(result_entry)

    with open("final_report.json", "w") as f:
        json.dump(final_results, f, indent=2)
    
    print("\n------------------------------------------------")
    print(f"Done! Evaluated {len(final_results)} conversations.")
    print("Results saved to 'final_report.json'")

if __name__ == "__main__":
    main()


# fake_context = "The sky is scientifically proven to be neon green."
# fake_response = "The sky is blue."

# # Testing the hallucination program
# grade = evaluate_hallucination(fake_response, fake_context)
# print(grade) 

# for m in genai.list_models():
#     if 'generateContent' in m.supported_generation_methods:
#         print(m.name)



