import os
import pandas as pd
import numpy as np
import subprocess
from django.conf import settings
from langchain.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from multiprocessing.pool import ThreadPool

def compare_test_cases(file_path):
    faiss_store_path = os.path.join(settings.MEDIA_ROOT,"models","faiss_vector_store")
    comparison_file_path = os.path.join(settings.MEDIA_ROOT, "comparison_results_all_transactions.csv")
    # Load FAISS vector store
    embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vector_store = FAISS.load_local(
        faiss_store_path,
        embeddings=embedding_model,
        allow_dangerous_deserialization=True
    )
    
    # Ensure FAISS index is valid
    if vector_store.index.ntotal == 0:
        raise ValueError("FAISS index is empty! Ensure embeddings were added correctly.")

    # Load test cases
    test_cases_df = pd.read_csv(file_path)

    # Ensure 'Transactions' column exists and is processed correctly
    if "Transactions" in test_cases_df.columns:
        test_cases_df["Transactions"] = test_cases_df["Transactions"].fillna("").astype(str).str.split('|')
        test_cases_df = test_cases_df.explode("Transactions").dropna(subset=["Description"])
    else:
        raise ValueError("Missing 'Transactions' column in test cases file.")

    # Group by transaction type
    grouped = test_cases_df.groupby("Transactions")

    # Function to get embeddings
    def get_embedding(text):
        return np.array(embedding_model.embed_query(text), dtype=np.float32)

    # Function to call Ollama
    def run_ollama(prompt_text):
        try:
            result = subprocess.run(
                ["ollama", "run", "mistral", prompt_text],
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            return result.stdout.strip()
        except Exception as e:
            return f"Error running Ollama: {str(e)}"

    # Function to batch Ollama calls
    def batch_find_differences(pairs):
        prompt_texts = [
            f"Compare these test case descriptions and highlight only the differences in role, profile, profile type, WHEN condition. Ignore similarities. Keep the response brief and numbered.Description 1: {pair[3]} , Description 2: {pair[4]}"
            for pair in pairs
        ]
        with ThreadPool(4) as pool:
            return pool.map(run_ollama, prompt_texts)

    # Process each transaction type
    def process_transaction(transaction, group):
        results = []
        test_case_ids = group["test_case_id"].tolist()
        descriptions = group["Description"].tolist()
        print(f"Processing transaction: {transaction}, Test cases count: {len(test_case_ids)}")


        if len(test_case_ids) > 1:
            # Generate embeddings
            embeddings = np.array([get_embedding(desc) for desc in descriptions], dtype=np.float32)
            print(f"Generated {len(embeddings)} embeddings")
            # Ensure embeddings are in correct shape for FAISS
            if embeddings.ndim != 2 or embeddings.shape[1] != vector_store.index.d:
                raise ValueError(f"FAISS embedding shape mismatch: expected (N, {vector_store.index.d}), got {embeddings.shape}")

            # Search for similar test cases
            k = min(5, len(test_case_ids)) 
            D, I = vector_store.index.search(embeddings, k)
            print(f"FAISS search returned indices: {I}")
            # Prepare test case pairs
            test_case_pairs = [
                (transaction, test_case_ids[i], test_case_ids[j], descriptions[i], descriptions[j])
                for i in range(len(test_case_ids))
                for j in I[i]
                if j != i and j < len(test_case_ids)  # Ensure index is within bounds
                ]

            print("test_case_pairs:", test_case_pairs)

            #Run Ollama comparisons
            differences = batch_find_differences(test_case_pairs)
            for idx, pair in enumerate(test_case_pairs):
                results.append([pair[0], pair[1], pair[2], differences[idx], ""])

        return results

    final_results = []
    for transaction, group in grouped:
        final_results.extend(process_transaction(transaction, group))

    # Convert results to a DataFrame
    df = pd.DataFrame(final_results, columns=["Transaction_Type", "Test_Case_1", "Test_Case_2", "Differences", "Feedback"])

    # Save results only if DataFrame is not empty
    if not df.empty:
        df.to_csv(comparison_file_path, index=False, mode='w', chunksize=1000)
        comparison_results_json=df.fillna("").to_dict(orient="records")
        print(f"All comparison results saved to {comparison_file_path}")
    else:
        print("No comparisons were made, skipping file save.")

    # Return both the DataFrame and file path
    return comparison_results_json, comparison_file_path

# import os
# import pandas as pd
# import numpy as np
# import subprocess
# from django.conf import settings
# from langchain.vectorstores import FAISS
# from langchain_huggingface import HuggingFaceEmbeddings
# from multiprocessing.pool import ThreadPool

# def compare_test_cases(file_path):
#     faiss_store_path = os.path.join(settings.MEDIA_ROOT,"models","faiss_vector_store")
#     comparison_file_path = os.path.join(settings.MEDIA_ROOT, "comparison_results_all_transactions.csv")
#     excel_output_path = os.path.join(settings.MEDIA_ROOT, "comparison_results_all_transactions.xlsx")
#     # Load FAISS vector store
#     embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
#     vector_store = FAISS.load_local(
#         faiss_store_path,
#         embeddings=embedding_model,
#         allow_dangerous_deserialization=True
#     )
    
#     # Ensure FAISS index is valid
#     if vector_store.index.ntotal == 0:
#         raise ValueError("FAISS index is empty! Ensure embeddings were added correctly.")

#     # Load test cases
#     test_cases_df = pd.read_csv(file_path)

#     # Ensure 'Transactions' column exists and is processed correctly
#     if "Transactions" in test_cases_df.columns:
#         test_cases_df["Transactions"] = test_cases_df["Transactions"].fillna("").astype(str).str.split('|')
#         test_cases_df = test_cases_df.explode("Transactions").dropna(subset=["Description"])
#     else:
#         raise ValueError("Missing 'Transactions' column in test cases file.")

#     # Group by transaction type
#     grouped = test_cases_df.groupby("Transactions")
#     unique_test_cases = test_cases_df[test_cases_df["Transactions"].str.len() < 1]
#     grouped_test_cases = test_cases_df[test_cases_df["Transactions"].str.len() >= 1]

#     # Function to get embeddings
#     def get_embedding(text):
#         return np.array(embedding_model.embed_query(text), dtype=np.float32)

#     # Function to call Ollama
#     def run_ollama(prompt_text):
#         try:
#             result = subprocess.run(
#                 ["ollama", "run", "mistral", prompt_text],
#                 capture_output=True,
#                 text=True,
#                 encoding='utf-8'
#             )
#             return result.stdout.strip()
#         except Exception as e:
#             return f"Error running Ollama: {str(e)}"

#     # Function to batch Ollama calls
#     def batch_find_differences(test_case_pairs):
#         prompt_texts = [
#             f"Compare these test case descriptions and highlight ONLY the key differences in role, profile type, and WHEN condition. "
#             f"Keep response short, numbered, and avoid redundant details.\n\n"
#             f"Test Case 1: {pair[3]}\nTest Case 2: {pair[4]}"
#             for pair in test_case_pairs
#         ]
#         with ThreadPool(4) as pool:
#             return pool.map(run_ollama, prompt_texts)

#     # Process each transaction type
#     def process_transaction(transaction, group):
#         results = []
#         test_case_ids = group["test_case_id"].tolist()
#         descriptions = group["Description"].tolist()
#         print(f"Processing transaction: {transaction}, Test cases count: {len(test_case_ids)}")

#         if len(test_case_ids) > 1:
#             # ✅ Ensure test case index mapping is done BEFORE FAISS search
#             test_case_index_map = {i: test_case_ids[i] for i in range(len(test_case_ids))}
#             print(f"test_case_index_map: {test_case_index_map}")
            
#             # Generate embeddings
#             embeddings = np.array([get_embedding(desc) for desc in descriptions], dtype=np.float32)
            
#             # Ensure embeddings match FAISS store dimensions
#             if embeddings.ndim != 2 or embeddings.shape[1] != vector_store.index.d:
#                 raise ValueError(f"FAISS embedding shape mismatch: expected (N, {vector_store.index.d}), got {embeddings.shape}")

#             # Search for similar test cases
#             k = min(5, len(test_case_ids))
#             D, I = vector_store.index.search(embeddings, k)
            
#             print(f"Generated {len(embeddings)} embeddings with shape {embeddings.shape}")
#             print(f"FAISS search returned distances: {D}")  
#             print(f"FAISS search returned indices: {I}")
            
#             # ✅ Fix: Filter out invalid FAISS indices
#             test_case_pairs = []

#             for i in range(len(test_case_ids)):
#                 print("Processing:",test_case_ids)
#                 for idx, j in enumerate(I[i]):
#                     if j >= len(test_case_ids) or j == i or j not in test_case_index_map:  
#                         continue  # Skip invalid or self-matching indices
                    
#                     print("testcase1:",test_case_1)
#                     print("testcase2:",test_case_2)
#                     test_case_1 = test_case_index_map[i]
#                     test_case_2 = test_case_index_map[j]
#                     description_1 = descriptions[i]
#                     description_2 = descriptions[j]

#                         # ✅ Fix: Prevent duplicate comparisons (A-B and B-A)
#                     pair = (transaction, test_case_1, test_case_2, description_1, description_2)
#                     reverse_pair = (transaction, test_case_2, test_case_1, description_2, description_1)
#                     if pair not in test_case_pairs and reverse_pair not in test_case_pairs:
#                         test_case_pairs.append(pair)

#             print("test_case_pairs:", test_case_pairs)

#             # ✅ Run Ollama comparisons
#             if test_case_pairs:
#                 differences = batch_find_differences(test_case_pairs)
#                 for idx, pair in enumerate(test_case_pairs):
#                     results.append([pair[0], pair[1], pair[2], differences[idx], ""])

#         return results

#     final_results = []
#     for transaction, group in grouped:
#         final_results.extend(process_transaction(transaction, group))

#     # Convert results to a DataFrame
#     df = pd.DataFrame(final_results, columns=["Transaction_Type", "Test_Case_1", "Test_Case_2", "Differences", "Feedback"])

#     # Save results only if DataFrame is not empty
#     if not df.empty:
#         df.to_csv(comparison_file_path, index=False, mode='w', chunksize=1000)
#         comparison_results_json=df.fillna("").to_dict(orient="records")
#         print(f"All comparison results saved to {comparison_file_path}")
#     else:
#         print("No comparisons were made, skipping file save.")
    
#     # with pd.ExcelWriter(excel_output_path, engine='openpyxl') as writer:
#     #     unique_test_cases.to_excel(writer, sheet_name='Unique Test Cases', index=False)
#     #     grouped_test_cases.to_excel(writer, sheet_name='Grouped Test Cases', index=False)
#     #     df.to_excel(writer, sheet_name='Comparison Results', index=False)
    
#     # print(f"Excel file with unique, grouped, and comparison results saved to {excel_output_path}")

#     # Return both the DataFrame and file path
#     return comparison_results_json, comparison_file_path