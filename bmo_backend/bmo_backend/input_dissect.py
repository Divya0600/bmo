import os
import re
import difflib
import pandas as pd
import spacy
import numpy as np
from django.conf import settings
from django.shortcuts import render
from django.core.paginator import Paginator
from django.http import Http404, HttpResponse, FileResponse

# Load spaCy model once (at module level)
nlp = spacy.load("en_core_web_sm")

def process_test_cases(file_path):
    if not os.path.exists(file_path):
        return {'error': 'File not found'}

    # Read CSV file
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        return {'error': f"Error reading CSV: {str(e)}"}

    # Ensure necessary columns exist
    necessary_columns = ['Description', 'test_steps']
    for column in necessary_columns:
        if column not in df.columns:
            return {'error': f"Missing necessary column: {column}"}

    # Initialize new columns
    df[['GIVEN', 'WHEN', 'THEN', 'Condition', 'Remaining']] = ""

    # Define helper functions (normalize_label, get_canonical_label, etc.)
    def normalize_label(label):
        label = label.lower().strip()
        label = re.sub(r"[-]", " ", label)
        label = re.sub(r"[^\w\s]", "", label)
        if label.endswith("s"):
            label = label[:-1]
        return label

    def get_canonical_label(label, canonical_dict, cutoff=0.8):
        normalized = normalize_label(label)
        if not canonical_dict:
            canonical_dict[normalized] = label
            return label
        matches = difflib.get_close_matches(normalized, canonical_dict.keys(), n=1, cutoff=cutoff)
        if matches:
            return canonical_dict[matches[0]]
        else:
            canonical_dict[normalized] = label
            return label

    def extract_labels(text, canonical_dict):
        labels = {}
        lines = text.split("\n")
        def add_label(label, value):
            if label and value:
                canonical = get_canonical_label(label, canonical_dict)
                if canonical in labels:
                    if not isinstance(labels[canonical], list):
                        labels[canonical] = [labels[canonical]]
                    labels[canonical].append(value)
                else:
                    labels[canonical] = value
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if ":" in line:
                key, value = map(str.strip, line.split(":", 1))
                add_label(key, value)
        return labels

    def extract_all_transactions(text):
        sentences = text.split('|')
        transaction_types = []
        for sentence in sentences:
            if 'transaction' in sentence.lower():
                pattern = re.compile(r"Transaction\s*[:=]\s*([\s\S]+?)(?=\s*(?:\n|[|~]|$))", re.IGNORECASE)
                matches = pattern.findall(text)
                if matches:
                    transaction_types = [re.sub(r"\s+", " ", m).strip() for m in matches if m.strip()]
                    return " | ".join(transaction_types)
                fallback_pattern = re.compile(r"(\S+)\s+transaction", re.IGNORECASE | re.DOTALL)
                fallback_matches = fallback_pattern.findall(text)
                if fallback_matches:
                    fallback_matches = [m.strip() for m in fallback_matches if m.strip()]
                    return " | ".join(fallback_matches)
                return ""
        return ""

    # Process each row in the DataFrame
    canonical_dict = {}
    for i, row in df.iterrows():
        description = row['Description']
        if pd.isna(description) or not isinstance(description, str):
            continue
        description = re.sub(r'\n\s*\n', '\n', description)
        doc = nlp(description)
        given_text, when_text, then_text, condition_text, remaining_text = "", "", "", "", ""
        start_index = None
        for token in doc:
            if "design" in token.text.lower():
                remaining_text = doc[:token.i].text
                start_index = None
            elif "given" in token.text.lower():
                start_index = token.i
            elif "when" in token.text.lower() and start_index is not None:
                given_text = doc[start_index:token.i].text
                start_index = token.i
            elif "then" in token.text.lower() and start_index is not None:
                when_text = doc[start_index:token.i].text
                start_index = token.i
            elif "condition" in token.text.lower() and start_index is not None:
                then_text = doc[start_index:token.i].text
                condition_text = description[token.idx:]
                start_index = None

        df.at[i, 'GIVEN'] = given_text.strip()
        df.at[i, 'WHEN'] = when_text.strip()
        df.at[i, 'THEN'] = then_text.strip()
        df.at[i, 'Condition'] = condition_text.strip()
        df.at[i, 'Remaining'] = remaining_text.strip()

        # Extract labels from remaining text
        extracted_labels = extract_labels(remaining_text, canonical_dict)
        for label, value in extracted_labels.items():
            df.at[i, label] = value

        # Extract transaction types from test_steps
        transactions = extract_all_transactions(row['test_steps'])
        df.at[i, 'Transactions'] = transactions

        # Extract additional labels from condition text if necessary
        example_pattern = re.compile(r'\b(e\.?g\.?|ex|example)\b', re.IGNORECASE)
        if not example_pattern.search(condition_text):
            extract_from_condition = extract_labels(condition_text, canonical_dict)
            for label, value in extract_from_condition.items():
                df.at[i, label] = value

        # Extract gateway type from condition text
        gateway_pattern = re.compile(r'\bgateway\s*[:\-]\s*(\S+)', re.IGNORECASE)
        gateway_match = gateway_pattern.search(condition_text)
        df.at[i, 'Gateway'] = gateway_match.group(1).strip() if gateway_match else 'No'

    # Save updated DataFrame to a new CSV file
    output_file_path = os.path.join(settings.MEDIA_ROOT, 'Admin_with_gwt_conditions.csv')
    df.to_csv(output_file_path, index=False)

    # Sanitize the DataFrame:
    # Replace NaN, inf, -inf with None so that JSON serialization works properly
    df.replace([np.inf, -np.inf], None, inplace=True)
    df = df.where(pd.notnull(df), None)

    return {
        'message': "Processing complete. Data saved to 'Admin_with_gwt_conditions.csv'.",
        'output_file_path': output_file_path,
        'data': df.to_dict('records')
    }

def dissect_test_cases(request):
    file_url = request.GET.get('file_url')
    if not file_url:
        return render(request, 'upload.html', {'error': 'No file URL provided'})
    file_path = os.path.join(settings.MEDIA_ROOT, file_url.lstrip('/'))

    result = process_test_cases(file_path)
    if 'error' in result:
        return render(request, 'upload.html', {'error': result['error']})

    # Paginate the processed data
    paginator = Paginator(result['data'], 10)  # 10 records per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'dissected_test_cases.html', {
        'page_obj': page_obj,
        'message': result['message']
    })

def download_file(request):
    """
    Download a file from the media folder.
    Expects a query parameter 'file_url' (e.g., /media/Admin_with_gwt_conditions.csv).
    """
    file_url = request.GET.get('file_url')
    if not file_url:
        return HttpResponse("No file specified", status=400)
    
    # Remove MEDIA_URL prefix if present
    if file_url.startswith(settings.MEDIA_URL):
        relative_file_path = file_url[len(settings.MEDIA_URL):]
    else:
        relative_file_path = file_url.lstrip('/')
    
    file_path = os.path.join(settings.MEDIA_ROOT, relative_file_path)
    
    if not os.path.exists(file_path):
        raise Http404("File not found")
    
    return FileResponse(open(file_path, 'rb'),
                        as_attachment=True,
                        filename=os.path.basename(file_path))
