import os
import pandas as pd
import numpy as np
import faiss  # Local FAISS usage for building a temporary index
from django.conf import settings
from langchain.vectorstores import FAISS as LC_FAISS  # Global FAISS index if needed elsewhere
from langchain_huggingface import HuggingFaceEmbeddings
from multiprocessing.pool import ThreadPool

# EXCLUDE_FIELDS: keys to skip during metadata comparison
EXCLUDE_FIELDS = [
    "Subject", "test_case_id", "Test Name", "Pre-Condition", "Description", 
    "No of Steps", "Designer", "Type", "Major Functional Area", "Business Unit", 
    "test_steps", "Remaining", "Transactions", "Transaction_Count", "Condition", "Processed_Steps"
]

def compare_metadata(meta1, meta2):
    differences = {}
    for key in meta1:
        if key in EXCLUDE_FIELDS:
            continue
        val1 = str(meta1.get(key, ""))
        val2 = str(meta2.get(key, ""))
        if val1 != val2:
            differences[key] = f"{val1}:{val2}"
    return differences

def check_semantic_containment(profile_df, diff_df, jaccard_threshold=0.5):
    if profile_df.empty or diff_df.empty:
        return pd.DataFrame()  # Return empty DataFrame if no test cases to process

    embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    # Ensure Processed_Steps are string
    profile_df["Processed_Steps"] = profile_df["Processed_Steps"].fillna("").astype(str)

    # Generate embeddings only for test cases in diff_df
    test_case_embeddings = {}
    for _, row in profile_df.iterrows():
        test_case_embeddings[row["test_case_id"]] = (
            embedding_model.embed_query(row["Processed_Steps"]) if row["Processed_Steps"].strip() else np.zeros(384)
        )

    contained_results = []

    def jaccard_similarity(text1, text2):
        set1, set2 = set(text1.lower().split()), set(text2.lower().split())
        return len(set1 & set2) / len(set1 | set2) if set1 | set2 else 0

    # Process only the pairs in diff_df
    for _, row in diff_df.iterrows():
        tc1_id, tc2_id = str(row["Test Case 1"]), str(row["Test Case 2"])
        tc1_steps = profile_df.loc[profile_df["test_case_id"] == tc1_id, "Processed_Steps"].values
        tc2_steps = profile_df.loc[profile_df["test_case_id"] == tc2_id, "Processed_Steps"].values

        if tc1_id in test_case_embeddings and tc2_id in test_case_embeddings:
            embedding1, embedding2 = test_case_embeddings[tc1_id], test_case_embeddings[tc2_id]
            
            # FAISS distance computation
            index = faiss.IndexFlatL2(384)
            index.add(np.array([embedding1]))
            D, _ = index.search(np.array([embedding2]), 1)
            
            jaccard_score = jaccard_similarity(tc1_steps[0], tc2_steps[0]) if tc1_steps.size and tc2_steps.size else 0

            print(f"Comparing {tc1_id} with {tc2_id} - Jaccard: {jaccard_score:.3f}, FAISS Distance: {D[0][0]:.3f}")

            if jaccard_score >= jaccard_threshold:
                contained_results.append({
                    "Test Case 1": tc1_id,
                    "Test Case 2": tc2_id,
                    "Contained?": "Yes" if jaccard_score >= jaccard_threshold else "No",
                    "Jaccard Score": round(jaccard_score, 3),
                    "FAISS Distance": round(D[0][0], 3),
                    "Feedback": ""
                })

    return pd.DataFrame(contained_results)

def compare_test_cases(file_path):
    # Output paths for CSV and Excel files
    comparison_file_path = os.path.join(settings.MEDIA_ROOT, "comparison_results_all_transactions.csv")
    excel_output_path = os.path.join(settings.MEDIA_ROOT, "comparison_results_all_transactions.xlsx")
    
    # Load global FAISS vector store (if needed elsewhere)
    faiss_store_path = os.path.join(settings.MEDIA_ROOT, "models", "faiss_vector_store")
    embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    global_vector_store = LC_FAISS.load_local(
        faiss_store_path,
        embeddings=embedding_model,
        allow_dangerous_deserialization=True
    )
    if global_vector_store.index.ntotal == 0:
        raise ValueError("FAISS index is empty! Ensure embeddings were added correctly.")

    # Load test cases CSV
    test_cases_df = pd.read_csv(file_path)
    mapped_transactions = test_cases_df.copy()
    if "Transactions" in test_cases_df.columns:
        test_cases_df["Transactions"] = test_cases_df["Transactions"].fillna("").astype(str).str.split('|')
        test_cases_df = test_cases_df.explode("Transactions").dropna(subset=["Description"])
    else:
        raise ValueError("Missing 'Transactions' column in test cases file.")
    # Process each transaction group to perform metadata comparison
    grouped = test_cases_df.groupby("Transactions")
    final_results = []  # Will hold the differences for Sheet4

    # Function to compute an embedding from a text using embed_query
    def get_embedding(text):
        return np.array(embedding_model.embed_query(text), dtype=np.float32)

    def process_transaction(transaction, group):
        results = []
        test_case_ids = group["test_case_id"].tolist()
        descriptions = group["Description"].tolist()
        # Get full metadata for each row in this group
        metadata_records = group.to_dict('records')
        print(f"Processing transaction: {transaction}, Test cases count: {len(test_case_ids)}")
        if len(test_case_ids) > 1:
            # Compute embeddings (based on descriptions)
            embeddings = np.array([get_embedding(desc) for desc in descriptions], dtype=np.float32)
            if embeddings.ndim != 2:
                raise ValueError("Embeddings must be a 2D array.")
            dimension = embeddings.shape[1]
            # Build a local FAISS index for this transaction group
            index_local = faiss.IndexFlatL2(dimension)
            index_local.add(embeddings)
            # Search local index for each test case (k nearest neighbors)
            k = min(5, len(test_case_ids))
            D, I = index_local.search(embeddings, k)
            print(f"Local FAISS search returned distances:\n{D}")
            print(f"Local FAISS search returned indices:\n{I}")
            # Create unique pairs based on FAISS results
            seen_pairs = set()
            test_case_pairs = []
            for i in range(len(test_case_ids)):
                for j_idx, j in enumerate(I[i]):
                    if j == i:
                        continue  # Skip self-comparison
                    test_case_1 = test_case_ids[i]
                    test_case_2 = test_case_ids[j]
                    faiss_distance = D[i][j_idx]
                    similarity_score = 1 / (1 + faiss_distance)
                    meta1 = metadata_records[i]
                    meta2 = metadata_records[j]
                    normalized_pair = tuple(sorted((test_case_1, test_case_2)))
                    if normalized_pair not in seen_pairs:
                        seen_pairs.add(normalized_pair)
                        test_case_pairs.append((transaction, test_case_1, test_case_2, meta1, meta2,faiss_distance, similarity_score))
            print("Test case pairs (with metadata):", test_case_pairs)
            # For each pair, compare metadata
            for pair in test_case_pairs:
                transaction_val, tc1, tc2, meta1, meta2, faiss_dist, sim_score = pair
                diff_dict = compare_metadata(meta1, meta2)
                result_row = {
                    "Transaction_Type": transaction_val,
                    "Test Case 1": tc1,
                    "Test Case 2": tc2,
                    "Similarity FAISS Distance": round(faiss_dist, 4),
                    "Similarity Score": round(sim_score, 4)
                }
                result_row.update(diff_dict)
                results.append(result_row)
                print(f"Compared Test Case {tc1} with Test Case {tc2}:\nDifferences: {diff_dict}\n")
        return results

    for transaction, group in grouped:
        final_results.extend(process_transaction(transaction, group))
    
    # Create a DataFrame for differences (Sheet4)
    diff_df = pd.DataFrame(final_results)
    # Convert mapped transactions to DataFrame
    mapped_transactions_df = pd.DataFrame(mapped_transactions)
    similar_test_cases = mapped_transactions_df[mapped_transactions_df["test_case_id"].isin(diff_df["Test Case 1"].tolist() + diff_df["Test Case 2"].tolist())]
    unique_test_cases = mapped_transactions_df[~mapped_transactions_df["test_case_id"].isin(similar_test_cases["test_case_id"].tolist())]
    # Check for differences in the 'Profile' column where one value is NaN
    if not diff_df.empty:
        profile_diff_df = diff_df[
            diff_df['Profile'].apply(lambda x: pd.isna(x) or 'nan' in str(x).lower())
        ]

        profile_diff_test_case_ids = profile_diff_df["Test Case 1"].tolist() + profile_diff_df["Test Case 2"].tolist()
        # Ensure IDs are in correct format for comparison
        test_cases_df["test_case_id"] = test_cases_df["test_case_id"].astype(str)
        profile_diff_test_case_ids = list(map(str, profile_diff_test_case_ids))

        # Extract matching records
        profile_test_case_records = test_cases_df[test_cases_df["test_case_id"].isin(profile_diff_test_case_ids)]
        profile_df = profile_test_case_records.drop_duplicates(subset=["test_case_id"]).copy()

        print("Filtered unique profile_df test_case_ids:", profile_df.columns)
        if not profile_df.empty:
            print("yes")
            contained_df = check_semantic_containment(profile_df, diff_df) if not profile_df.empty else pd.DataFrame()
            print("contained_df:",contained_df)
        else:
            contained_df = pd.DataFrame()
        print("Columns in contained_df:", contained_df.columns)
        
    if not diff_df.empty:
        print("Columns in diff_df before merging:", diff_df.columns)
        
        # Ensure contained_df has required columns
        required_columns = {"Test Case 1", "Test Case 2", "Contained?", "Jaccard Score", "FAISS Distance"}
        missing_columns = required_columns - set(contained_df.columns)
        
        if missing_columns:
            print(f"🚨 Missing columns in contained_df: {missing_columns}")

        if not contained_df.empty:
            # Ensure matching data types
            contained_df["Test Case 1"] = contained_df["Test Case 1"].astype(str)
            contained_df["Test Case 2"] = contained_df["Test Case 2"].astype(str)
            diff_df["Test Case 1"] = diff_df["Test Case 1"].astype(str)
            diff_df["Test Case 2"] = diff_df["Test Case 2"].astype(str)
            
            # Merge containment info
            merged_df = diff_df.merge(contained_df, on=["Test Case 1", "Test Case 2"], how="left")
            
            # Fill missing containment info
            merged_df["Contained?"] = merged_df["Contained?"].fillna("No")
            merged_df["Jaccard Score"] = merged_df["Jaccard Score"].fillna(0.0)
            merged_df["FAISS Distance"] = merged_df["FAISS Distance"].fillna(0.0)
        else:
            print("⚠️ Warning: contained_df is empty. No containment info added.")
            merged_df = diff_df  # Use original diff_df if contained_df is empty
    else:
        print("⚠️ Warning: diff_df is empty. Skipping merge.")
        merged_df = pd.DataFrame()

    # Write merged results to CSV & Excel
    merged_df.to_csv(comparison_file_path, index=False)
    comparison_results_json = merged_df.fillna("").to_dict(orient="records")
    with pd.ExcelWriter(excel_output_path, engine='openpyxl') as writer:
        mapped_transactions.to_excel(writer, sheet_name="Mapped_Transactions", index=False)
        unique_test_cases.to_excel(writer, sheet_name="Unique_transaction", index=False)
        similar_test_cases.to_excel(writer, sheet_name="Similar_transaction", index=False)
        merged_df.to_excel(writer, sheet_name="Differences", index=False)
        if not contained_df.empty:
            contained_df.to_excel(writer, sheet_name="Containment_Check", index=False)

    print(f"✅ Comparison results saved to {comparison_file_path} and {excel_output_path}")
    return comparison_results_json, comparison_file_path, excel_output_path
