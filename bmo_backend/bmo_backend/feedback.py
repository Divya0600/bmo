import os
from django.conf import settings
import pandas as pd
import subprocess

#ollama_path = r'C:\Users\yuvaranjani.mani\AppData\Local\Programs\Ollama\ollama.exe'

def classify_feedback_with_ollama(transaction_type, test_case_1, test_case_2, feedback):
    prompt = f"""
    You are an AI assistant evaluating user feedback on test case similarity.
    The user has provided feedback for the following test cases:
    - Transaction_type: {transaction_type}
    - Test Case 1: {test_case_1}
    - Test Case 2: {test_case_2}
    User Feedback: "{feedback}"
    Based on the feedback, classify it into one of two categories:
    1. BOOST - If the feedback indicates that the test cases are similar with minor wording changes or format differences.
    2. PENALIZE - If the feedback indicates major differences in functionality, steps, or transaction type.
    Respond with ONLY "BOOST" or "PENALIZE" and nothing else.
    """
    
    result = subprocess.run(["ollama", "run", "mistral", prompt], capture_output=True, text=True, encoding='utf-8')
    classification = result.stdout.strip().upper()
    if classification not in ["BOOST", "PENALIZE"]:
        classification = "UNKNOWN"
    
    return classification    

def feedback(file_path):
    file_path = os.path.basename(file_path)
    feedback_file = os.path.join(settings.MEDIA_ROOT, "feedback_files", file_path)
    print("file", feedback_file)
    feedback_df = pd.read_excel(feedback_file, engine='openpyxl', sheet_name="Differences")
    feedback_present = feedback_df[feedback_df['Feedback'].notna()]
    feedback_dict = feedback_present.to_dict(orient='records')
    print("feedback_dict", feedback_dict)
    
    feedback_results = []
    for feedback in feedback_dict:
        filtered_feedback = {key: feedback[key] for key in ['Transaction_Type', 'Test Case 1', 'Test Case 2', 'Feedback'] if key in feedback}
        classification = classify_feedback_with_ollama(
            filtered_feedback.get('Transaction_Type'),
            filtered_feedback.get('Test Case 1'),
            filtered_feedback.get('Test Case 2'),
            filtered_feedback.get('Feedback')
        )
        feedback_json = {
            "Transaction_Type": filtered_feedback.get('Transaction_Type'),
            "Test_Case_1": filtered_feedback.get('Test Case 1'),
            "Test_Case_2": filtered_feedback.get('Test Case 2'),
            "Feedback": filtered_feedback.get('Feedback'),
            "Classification": classification
        }
        print("feedback form backend:", feedback_json)
        feedback_results.append(feedback_json)
    
    return feedback_results
