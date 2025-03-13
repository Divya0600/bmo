
# import os
# import pandas as pd
# import traceback
# import numpy as np
# from concurrent.futures import ThreadPoolExecutor, as_completed
# from django.conf import settings
# from langchain_huggingface import HuggingFaceEmbeddings
# from langchain.vectorstores import FAISS
# import faiss
# from langchain.storage import InMemoryStore
# from langchain.schema import Document

# # Paths
# FAISS_DB_PATH = FAISS_DB_PATH = os.path.join(settings.MEDIA_ROOT, "models", "faiss_vector_store")


# # Initialize Embeddings Model
# embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# # Function to clean and preprocess test steps
# def clean_test_steps(test_steps):
#     if not isinstance(test_steps, str):
#         return ""
#     step_list = test_steps.split('|')
#     step_list = [step.strip() for step in step_list if step.strip()]
#     processed_steps = [
#         (f"Step {idx + 1}: {step.split('~', 1)[0].strip()}",
#          f"Expected result {idx + 1}: {step.split('~', 1)[1].strip()}" if '~' in step else "No expected result")
#         for idx, step in enumerate(step_list)
#     ]
#     return "\n".join([f"{step} | {expected}" for step, expected in processed_steps])

# # Function to process and embed a single test case row
# def process_and_embed_row(index, test_cases_df):
#     test_case_id = test_cases_df.loc[index, 'test_case_id']
#     description = test_cases_df.loc[index, 'Description']
#     transaction_type = test_cases_df.loc[index, 'Transactions']
#     steps_text = test_cases_df.loc[index, 'Processed_Steps'] if pd.notna(test_cases_df.loc[index, 'Processed_Steps']) else ""
#     combined_text = f"Test ID:{test_case_id} Description:{description} Transaction:{transaction_type} Steps: {steps_text}"
#     embedding = np.array(embedding_model.embed_documents([combined_text])[0])
#     return combined_text, embedding, {"test_case_id": test_case_id, "Transaction": transaction_type}

# # Function to load or create FAISS index
# def load_or_create_faiss():
#     if os.path.exists(FAISS_DB_PATH):
#         print("🔄 Loading existing FAISS index...")
#         return FAISS.load_local(FAISS_DB_PATH, embeddings=embedding_model, allow_dangerous_deserialization=True)
#     else:
#         print("🆕 Creating new FAISS index...")
#         dimension = 384  # Adjust based on embedding model
#         index = faiss.IndexFlatL2(dimension)
#         return index  # Return raw FAISS index

# # Function to add embeddings to FAISS index
# def add_embeddings_to_faiss(texts, embeddings, metadata_list):
#     """Add embeddings to FAISS index and save it correctly."""
#     vector_store = load_or_create_faiss()
#     # Ensure embeddings are in NumPy format
#     embeddings_np = np.array(embeddings, dtype=np.float32)

#     # Create FAISS index
#     faiss_index = faiss.IndexFlatL2(embeddings_np.shape[1])
#     faiss_index.add(embeddings_np)

#     # Convert metadata to LangChain Document format
#     documents = {str(i): Document(page_content=texts[i], metadata=metadata_list[i]) for i in range(len(texts))}

#     # Use InMemoryStore to store metadata
#     docstore = InMemoryStore()
#     docstore.mset(list(documents.items()))
#     # Map FAISS index IDs to metadata store
#     index_to_docstore_id = {i: str(i) for i in range(len(embeddings))}

#     # Create FAISS vector store
#     vector_store = FAISS(embedding_model, faiss_index, docstore, index_to_docstore_id)

#     # Save FAISS index and metadata
#     vector_store.save_local(FAISS_DB_PATH)

#     print(f"FAISS index updated and saved at {FAISS_DB_PATH}")

# # Main function to preprocess test cases and generate embeddings
# def pre_process_test_cases(input_file, transaction_type):
#     try:
#         sheet_name = "Matched Labels" if transaction_type == "mapped" else "Unmatched Labels"
#         test_cases_df = pd.read_excel(input_file, sheet_name=sheet_name)
#         with ThreadPoolExecutor() as executor:
#             futures = {executor.submit(clean_test_steps, test_cases_df.loc[i, 'test_steps']): i for i in range(len(test_cases_df))}
#             for future in as_completed(futures):
#                 processed_steps_str = future.result()
#                 index = futures[future]
#                 test_cases_df.at[index, 'Processed_Steps'] = processed_steps_str
#         output_filename = f"processed_test_cases_{transaction_type}.csv"
#         output_file = os.path.join(settings.MEDIA_ROOT, output_filename)
#         test_cases_df.to_csv(output_file, index=False)
        
#         combined_texts, combined_vectors, metadata_list = [], [], []
#         with ThreadPoolExecutor() as executor:
#             futures = {executor.submit(process_and_embed_row, i, test_cases_df): i for i in range(len(test_cases_df))}
#             for future in as_completed(futures):
#                 text, vector, metadata = future.result()
#                 combined_texts.append(text)
#                 combined_vectors.append(vector)
#                 metadata_list.append(metadata)
        
#         if combined_vectors:
#             add_embeddings_to_faiss(combined_texts, combined_vectors, metadata_list)
        
#         return output_file, f"Preprocessed {transaction_type} test cases saved successfully, and FAISS index updated."
#     except Exception as e:
#         return None, f"❌ Error: {str(e)}\n{traceback.format_exc()}"

import os
import pandas as pd
import traceback
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
from django.conf import settings
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
import faiss
from langchain.storage import InMemoryStore
from langchain.schema import Document

# Paths
FAISS_DB_PATH = os.path.join(settings.MEDIA_ROOT, "models", "faiss_vector_store")

# Initialize Embeddings Model
embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# Function to clean and preprocess test steps
def clean_test_steps(test_steps):
    if not isinstance(test_steps, str):
        return ""
    step_list = test_steps.split('|')
    step_list = [step.strip() for step in step_list if step.strip()]
    processed_steps = [
        (f"Step {idx + 1}: {step.split('~', 1)[0].strip()}",
         f"Expected result {idx + 1}: {step.split('~', 1)[1].strip()}" if '~' in step else "No expected result")
        for idx, step in enumerate(step_list)
    ]
    return "\n".join([f"{step} | {expected}" for step, expected in processed_steps])

# Updated function to process and embed a single test case row with full metadata
def process_and_embed_row(index, test_cases_df):
    test_case_id = test_cases_df.loc[index, 'test_case_id']
    description = test_cases_df.loc[index, 'Description']
    transaction_type = test_cases_df.loc[index, 'Transactions']
    steps_text = test_cases_df.loc[index, 'Processed_Steps'] if pd.notna(test_cases_df.loc[index, 'Processed_Steps']) else ""
    combined_text = f"Test ID:{test_case_id} Description:{description} Transaction:{transaction_type} Steps: {steps_text}"
    embedding = np.array(embedding_model.embed_documents([combined_text])[0])
    # Extract all columns as metadata (convert NaN to empty strings)
    metadata = test_cases_df.loc[index].fillna("").to_dict()
    return combined_text, embedding, metadata

# Function to load or create FAISS index
def load_or_create_faiss():
    if os.path.exists(FAISS_DB_PATH):
        print("🔄 Loading existing FAISS index...")
        return FAISS.load_local(FAISS_DB_PATH, embeddings=embedding_model, allow_dangerous_deserialization=True)
    else:
        print("🆕 Creating new FAISS index...")
        dimension = 384  # Adjust based on embedding model
        index = faiss.IndexFlatL2(dimension)
        return index  # Return raw FAISS index

# Function to add embeddings to FAISS index
def add_embeddings_to_faiss(texts, embeddings, metadata_list):
    """Add embeddings to FAISS index and save it correctly."""
    vector_store = load_or_create_faiss()
    # Ensure embeddings are in NumPy format
    embeddings_np = np.array(embeddings, dtype=np.float32)

    # Create FAISS index
    faiss_index = faiss.IndexFlatL2(embeddings_np.shape[1])
    faiss_index.add(embeddings_np)

    # Convert metadata to LangChain Document format
    documents = {str(i): Document(page_content=texts[i], metadata=metadata_list[i]) for i in range(len(texts))}

    # Use InMemoryStore to store metadata
    docstore = InMemoryStore()
    docstore.mset(list(documents.items()))
    # Map FAISS index IDs to metadata store
    index_to_docstore_id = {i: str(i) for i in range(len(embeddings))}

    # Create FAISS vector store
    vector_store = FAISS(embedding_model, faiss_index, docstore, index_to_docstore_id)

    # Save FAISS index and metadata
    vector_store.save_local(FAISS_DB_PATH)

    print(f"FAISS index updated and saved at {FAISS_DB_PATH}")

# Main function to preprocess test cases and generate embeddings
def pre_process_test_cases(input_file, transaction_type):
    try:
        sheet_name = "Matched Labels" if transaction_type == "mapped" else "Unmatched Labels"
        test_cases_df = pd.read_excel(input_file, sheet_name=sheet_name)
        with ThreadPoolExecutor() as executor:
            futures = {executor.submit(clean_test_steps, test_cases_df.loc[i, 'test_steps']): i for i in range(len(test_cases_df))}
            for future in as_completed(futures):
                processed_steps_str = future.result()
                index = futures[future]
                test_cases_df.at[index, 'Processed_Steps'] = processed_steps_str
        output_filename = f"processed_test_cases_{transaction_type}.csv"
        output_file = os.path.join(settings.MEDIA_ROOT, output_filename)
        test_cases_df.to_csv(output_file, index=False)
        
        combined_texts, combined_vectors, metadata_list = [], [], []
        with ThreadPoolExecutor() as executor:
            futures = {executor.submit(process_and_embed_row, i, test_cases_df): i for i in range(len(test_cases_df))}
            for future in as_completed(futures):
                text, vector, metadata = future.result()
                combined_texts.append(text)
                combined_vectors.append(vector)
                metadata_list.append(metadata)
        
        if combined_vectors:
            add_embeddings_to_faiss(combined_texts, combined_vectors, metadata_list)
        
        return output_file, f"Preprocessed {transaction_type} test cases saved successfully, and FAISS index updated."
    except Exception as e:
        return None, f"❌ Error: {str(e)}\n{traceback.format_exc()}"

