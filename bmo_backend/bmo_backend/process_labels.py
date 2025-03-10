import os
import re
import pandas as pd
from symspellpy.symspellpy import SymSpell
from django.conf import settings

# Initialize SymSpell for spell correction
DICTIONARY_PATH = os.path.join(settings.MEDIA_ROOT, "models", "frequency_dictionary_BMO.txt")

sym_spell = SymSpell(max_dictionary_edit_distance=2, prefix_length=100)
sym_spell.load_dictionary(DICTIONARY_PATH, term_index=0, count_index=1)

# Global synonym mapping
CUSTOM_SYNONYMS = {}

def normalize_label(label):
    """Normalize transaction labels using spell correction and regex cleanup."""
    if not isinstance(label, str) or not label.strip():
        return None
    
    # Apply spell correction
    suggestions = sym_spell.lookup_compound(label, max_edit_distance=2)
    label = suggestions[0].term if suggestions else label
    
    # Convert to lowercase and remove special characters
    label = label.lower().strip()
    label = re.sub(r"[-]", " ", label)  # Replace hyphens with spaces
    label = re.sub(r"[^\w\s]", "", label)  # Remove non-alphanumeric characters
    label = re.sub(r"\s+", " ", label).strip()  # Remove extra spaces
    
    # Remove trailing 's' (simple pluralization handling)
    if label.endswith("s"):
        label = label[:-1]
    
    return label

def process_labels(csv_file_path, metadata_file_path, synonyms=None):
    """Process transaction labels by normalizing and mapping to known metadata labels."""
    print(f"Processing labels from {csv_file_path} and {metadata_file_path}")
    
    global CUSTOM_SYNONYMS
    previous_synonyms = CUSTOM_SYNONYMS.copy()  # Keep a copy of existing synonyms

    # Update the global synonym dictionary if new synonyms are provided
    if synonyms:
        CUSTOM_SYNONYMS.update(synonyms)

    try:
        labeled_data = pd.read_csv(csv_file_path)
        if "Transactions" not in labeled_data.columns:
            return {"error": "CSV file is missing required 'Transactions' column."}
    except Exception as e:
        return {"error": f"Error reading CSV file: {e}"}

    try:
        transaction_metadata = pd.read_excel(metadata_file_path)
        if "Transaction" not in transaction_metadata.columns:
            return {"error": "Metadata file is missing required 'Transaction' column."}
    except Exception as e:
        return {"error": f"Error reading metadata file: {e}"}

    # Extract metadata labels and normalize for lookup
    metadata_labels = set(transaction_metadata["Transaction"].dropna().unique())
    normalized_metadata = {normalize_label(label): label for label in metadata_labels}

    def apply_synonyms(label):
        """Replace transactions using the synonym dictionary."""
        if pd.isna(label):
            return None
        transactions = label.split("|")
        updated_transactions = [
            CUSTOM_SYNONYMS.get(trans.strip(), trans.strip())  # Replace if synonym exists
            for trans in transactions
        ]
        return "|".join(updated_transactions)

    def map_labels(label_string):
        """Map input labels to known metadata labels using normalization and synonyms."""
        if pd.isna(label_string):
            return None
        
        labels = label_string.split("|")
        corrected_labels = []
        
        for label in labels:
            label = label.strip()
            
            # Apply synonyms first
            if label in CUSTOM_SYNONYMS:
                corrected_labels.append(CUSTOM_SYNONYMS[label])
                continue
            
            # Direct match in metadata
            if label in metadata_labels:
                corrected_labels.append(label)
                continue
            
            # Normalize and look up in metadata
            normalized = normalize_label(label)
            matched_label = normalized_metadata.get(normalized, label)
            corrected_labels.append(matched_label)
        
        return "|".join(corrected_labels)

    # Apply synonyms only if new ones were provided
    if synonyms:
        labeled_data["Transactions"] = labeled_data["Transactions"].map(apply_synonyms)

    # Normalize and map transactions
    labeled_data["Transactions"] = labeled_data["Transactions"].map(map_labels)

    # Compute transaction counts
    transaction_counts = labeled_data["Transactions"].str.split("|").explode().value_counts()
    labeled_data["Transaction_Count"] = labeled_data["Transactions"].map(
        lambda x: sum(transaction_counts.get(label, 0) for label in x.split('|')) if pd.notna(x) else 0
    )

    # Categorize records
    matched_mask = labeled_data["Transactions"].apply(
        lambda x: any(label in metadata_labels for label in x.split('|')) if pd.notna(x) else False
    )

    matched_records = labeled_data[matched_mask]
    not_matched_records = labeled_data[~matched_mask & labeled_data["Transactions"].notna()]
    no_transaction_records = labeled_data[labeled_data["Transactions"].isna()]

    # Aggregate transaction counts
    matched_counts = matched_records["Transactions"].str.split("|").explode().value_counts()
    not_matched_counts = not_matched_records["Transactions"].str.split("|").explode().value_counts()

    matched_summary = matched_counts.reset_index().rename(columns={"index": "Matched Transactions", 0: "Count"})
    not_matched_summary = not_matched_counts.reset_index().rename(columns={"index": "Not Matched Transactions", 0: "Count"})

    # **Save updated CSV only if synonyms changed**
    updated_csv_path = csv_file_path
    if synonyms and previous_synonyms != CUSTOM_SYNONYMS:
        updated_csv_path = csv_file_path.replace(".csv", "_updated.csv")
        labeled_data.to_csv(updated_csv_path, index=False)

    # Write summary report to Excel
    output_filename = "transaction_summary.xlsx"
    output_file_path = os.path.join(settings.MEDIA_ROOT, output_filename)

    try:
        with pd.ExcelWriter(output_file_path, engine="openpyxl") as writer:
            pd.DataFrame(list(metadata_labels), columns=["Baselined Transactions"]).to_excel(
                writer, sheet_name="Transaction Summary", startrow=1, index=False
            )
            matched_records.to_excel(writer, sheet_name="Matched Labels", index=False)
            not_matched_records.to_excel(writer, sheet_name="Not Matched Labels", index=False)
            no_transaction_records.to_excel(writer, sheet_name="No Transactions", index=False)
            matched_summary.to_excel(writer, sheet_name="Transaction Summary", startrow=len(metadata_labels) + 5, startcol=0, index=False)
            not_matched_summary.to_excel(writer, sheet_name="Transaction Summary", startrow=len(metadata_labels) + 5, startcol=3, index=False)
    except Exception as e:
        return {"error": f"Error writing Excel file: {e}"}

    return {
        "message": "Transactions updated and summary saved successfully!",
        "updated_csv": updated_csv_path,
        "processed_file_url": settings.MEDIA_URL + output_filename
    }