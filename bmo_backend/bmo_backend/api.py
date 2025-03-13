# api.py
import os
from django.core.files.storage import FileSystemStorage, default_storage
from django.core.files.base import ContentFile
import json
from django.http import JsonResponse
import pandas as pd
from django.conf import settings
from rest_framework.views import APIView
from django.core.paginator import Paginator
from rest_framework.response import Response
from rest_framework import status
from .input_dissect import process_test_cases
from .process_labels import process_labels
from .pre_process import pre_process_test_cases
from .test_case_comparison import compare_test_cases
from .feedback import feedback


class UploadFileAPIView(APIView):
    def post(self, request, format=None):
        if 'file' not in request.FILES:
            return Response(
                {'error': 'No file provided.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        # Save the uploaded file
        uploaded_file = request.FILES['file']
        fs = FileSystemStorage()
        filename = fs.save(uploaded_file.name, uploaded_file)
        print("File saved:", filename)
        file_url = fs.url(filename)
        print("File URL:", file_url)
        # Use the filename to build the file path
        file_path = os.path.join(settings.MEDIA_ROOT, filename)
        print("File path:", file_path)
        
        # Process the file using the helper function
        result = process_test_cases(file_path)
        print("Processing result:", result)
        if 'error' in result:
            return Response({'error': result['error']}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'file_url': file_url,
            'processing_result': result['message'],
            'output_file_path': result['output_file_path']
        }, status=status.HTTP_201_CREATED)

class DissectTestCasesAPIView(APIView):
    def get(self, request, format=None):
        file_url = request.GET.get('file_url')
        if not file_url:
            return Response({'error': 'No file URL provided.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Remove MEDIA_URL prefix if present
        if file_url.startswith(settings.MEDIA_URL):
            relative_file_path = file_url[len(settings.MEDIA_URL):]
        else:
            relative_file_path = file_url.lstrip('/')
        
        file_path = os.path.join(settings.MEDIA_ROOT, relative_file_path)
        result = process_test_cases(file_path)
        if 'error' in result:
            return Response({'error': result['error']}, status=status.HTTP_400_BAD_REQUEST)
        
        data_list = result['data']  # List of processed records

        # Convert the processed file path to a URL (assuming it's saved in MEDIA_ROOT)
        processed_file_path = result.get('output_file_path')
        processed_file_url = (settings.MEDIA_URL + os.path.basename(processed_file_path)) if processed_file_path else None

        # Check if the "all" flag is provided in the query string
        if request.GET.get('all', 'false').lower() == 'true':
            return Response({
                'data': data_list,
                'processed_file_url': processed_file_url,
            }, status=status.HTTP_200_OK)
        
        # Otherwise, return paginated results
        page_number = request.GET.get('page', 1)
        paginator = Paginator(data_list, 10)  # 10 records per page
        page_obj = paginator.get_page(page_number)
        
        paginated_data = {
            'current_page': page_obj.number,
            'total_pages': paginator.num_pages,
            'data': list(page_obj.object_list),
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
            'processed_file_url': processed_file_url,
        }
        return Response(paginated_data, status=status.HTTP_200_OK)

class ProcessLabelsAPIView(APIView):
    def post(self, request, format=None):
        csv_file_url = request.data.get("csv_file_url")
        metadata_url = request.data.get("metadata_url")
        #frontend_synonyms = request.data.get("synonyms", {})
        #print("Synnonyms:", frontend_synonyms)
        if not csv_file_url or not metadata_url:
            return Response({"error": "Both csv_file_url and metadata_url are required."},
                            status=status.HTTP_400_BAD_REQUEST)
        
        # Convert file URLs to file paths.
        if csv_file_url.startswith(settings.MEDIA_URL):
            csv_relative_path = csv_file_url[len(settings.MEDIA_URL):]
        else:
            csv_relative_path = csv_file_url.lstrip('/')
        csv_file_path = os.path.join(settings.MEDIA_ROOT, csv_relative_path)
        
        if metadata_url.startswith(settings.MEDIA_URL):
            meta_relative_path = metadata_url[len(settings.MEDIA_URL):]
        else:
            meta_relative_path = metadata_url.lstrip('/')
        metadata_file_path = os.path.join(settings.MEDIA_ROOT, meta_relative_path)
        
        if not os.path.exists(csv_file_path):
            return Response({"error": f"CSV file not found: {csv_file_path}"}, status=status.HTTP_404_NOT_FOUND)
        if not os.path.exists(metadata_file_path):
            return Response({"error": f"Metadata file not found: {metadata_file_path}"}, status=status.HTTP_404_NOT_FOUND)
        
        result = process_labels(csv_file_path, metadata_file_path)
        print("result from processlabel api",result)
        if "error" in result:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)
        return Response(result, status=status.HTTP_200_OK)
    
class UploadMetadataAPIView(APIView):
    def post(self, request, format=None):
        if 'file' not in request.FILES:
            return Response({'error': 'No file provided.'}, status=status.HTTP_400_BAD_REQUEST)
        uploaded_file = request.FILES['file']
        fs = FileSystemStorage()
        filename = fs.save(uploaded_file.name, uploaded_file)
        file_url = fs.url(filename)
        return Response({'file_url': file_url}, status=status.HTTP_201_CREATED)
    
class GetTransactionSummaryAPIView(APIView):
    def get(self, request, format=None):
        try:
            summary_file = os.path.join(settings.MEDIA_ROOT, 'transaction_summary.xlsx')
            if not os.path.exists(summary_file):
                return Response({'error': 'Summary file not found.'},
                                status=status.HTTP_404_NOT_FOUND)
            baseline_file_url = request.GET.get('metadata_url')
            if not baseline_file_url:
                return Response({'error': 'Baseline file URL must be provided.'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Build the full file path for the baseline file
            if baseline_file_url.startswith(settings.MEDIA_URL):
                baseline_relative_path = baseline_file_url[len(settings.MEDIA_URL):]
            else:
                baseline_relative_path = baseline_file_url.lstrip('/')
            baseline_file_path = os.path.join(settings.MEDIA_ROOT, baseline_relative_path)
            
            # Check if the baseline file exists
            if not os.path.exists(baseline_file_path):
                return Response({'error': 'Baseline file not found.'}, status=status.HTTP_404_NOT_FOUND)
            
            # Read the baseline sheet to get canonical transaction types
            baseline_df = pd.read_excel(baseline_file_path)
            if baseline_df.empty:
                return Response({'error': 'Baseline sheet is empty.'}, status=status.HTTP_400_BAD_REQUEST)
            if "Transaction" not in baseline_df.columns:
                return Response({'error': 'Expected column "Baselined Transactions" not found in baseline sheet.'}, status=status.HTTP_400_BAD_REQUEST)
            baselined_list = baseline_df["Transaction"].dropna().unique().tolist()
            print(f"Baselined List: {baselined_list}")
            # Read the "Matched Labels" and "Not Matched Labels" sheets.
            matched_df = pd.read_excel(summary_file, sheet_name='Matched Labels')
            not_matched_df = pd.read_excel(summary_file, sheet_name='Not Matched Labels')
            
            # Check for the expected "Transactions" column in both sheets.
            if 'Transactions' not in matched_df.columns or 'Transactions' not in not_matched_df.columns:
                return Response({'error': 'Expected column "Transactions" not found in one or both sheets.'},
                                status=status.HTTP_400_BAD_REQUEST)
            
            # Process the "Transactions" column by splitting on '|' and exploding to separate rows.
            matched_series = matched_df['Transactions'].dropna().str.split("|").explode()
            not_matched_series = not_matched_df['Transactions'].dropna().str.split("|").explode()
            
            # Group the transactions and count occurrences.
            mapped_counts = matched_series.value_counts().reset_index()
            mapped_counts.columns = ['transaction', 'count']
            
            unmapped_counts = not_matched_series.value_counts().reset_index()
            unmapped_counts.columns = ['transaction', 'count']
            
            mapped_list = mapped_counts.to_dict(orient='records')
            unmapped_list = unmapped_counts.to_dict(orient='records')
            print(f"Mapped List: {mapped_list}, Unmapped List: {unmapped_list}, Baselined List: {baselined_list}")
            return Response({
                'mapped': mapped_list,
                'unmapped': unmapped_list,
                'baselined': baselined_list
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
class UpdateTransactionMappingAPIView(APIView):
    
    def post(self, request, format=None):
        data = request.data
        print("Received data:", data)
        csv_file_path = data.get("csv_file_url")
        metadata_file_path = data.get("metadata_url")
        if not csv_file_path or not metadata_file_path:
            return Response({"error": "Both csv_file_url and metadata_url are required."},
                            status=status.HTTP_400_BAD_REQUEST)
        synonyms = data.get("synonyms", {})
        if isinstance(synonyms, list):  # Convert list to dictionary format if needed
            synonyms = {item["source_transaction"]: item["target_transaction"] for item in synonyms if "source_transaction" in item and "target_transaction" in item}
        
        if not synonyms:
            return Response({"error": "Synonyms are required."},
                            status=status.HTTP_400_BAD_REQUEST)
        # Convert file URLs to file paths.
        if csv_file_path.startswith(settings.MEDIA_URL):
            csv_relative_path = csv_file_path[len(settings.MEDIA_URL):]
        else:
            csv_relative_path = csv_file_path.lstrip('/')
        csv_file_path = os.path.join(settings.MEDIA_ROOT, csv_relative_path)
        if metadata_file_path.startswith(settings.MEDIA_URL):
            meta_relative_path = metadata_file_path[len(settings.MEDIA_URL):]
        else:
            meta_relative_path = metadata_file_path.lstrip('/')
        metadata_file_path = os.path.join(settings.MEDIA_ROOT, meta_relative_path)
        if not os.path.exists(csv_file_path):
            return Response({"error": f"CSV file not found: {csv_file_path}"}, status=status.HTTP_404_NOT_FOUND)
        if not os.path.exists(metadata_file_path):
            return Response({"error": f"Metadata file not found: {metadata_file_path}"}, status=status.HTTP_404_NOT_FOUND)
        
        # Process the labels
        result = process_labels(csv_file_path, metadata_file_path, synonyms)
        
        if "error" in result:
            return Response({"error": result["error"]}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(result, status=status.HTTP_200_OK)

class PreProcessTestCasesAPI(APIView):

    def post(self, request):
        print("Received request data:", request.body)
        try:
                request_data = json.loads(request.body)
        except json.JSONDecodeError:
                return Response({"error": "Invalid JSON format."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            transaction_type = request.data.get("transaction_type", None)
            if not transaction_type:
                return Response({"error": "Missing transaction_type parameter."}, status=status.HTTP_400_BAD_REQUEST)

            # Fetch the latest summary file from the media folder
            media_path = settings.MEDIA_ROOT
    
            summary_files = [f for f in os.listdir(media_path) if f.startswith("transaction_summary") and f.endswith(".xlsx")]
            print("Summary files:", summary_files)
            if not summary_files:
                return Response({"error": "No summary file found."}, status=status.HTTP_400_BAD_REQUEST)

            # Get the latest summary file based on creation time
            latest_summary_file = max(summary_files, key=lambda f: os.path.getctime(os.path.join(media_path, f)))
            print("Latest summary file:", latest_summary_file)
            input_file_path = os.path.join(media_path, latest_summary_file)
            print("Input file path:", input_file_path)
            print("Transaction type:", transaction_type)
            # Process test cases with the selected transaction type
            output_file, message = pre_process_test_cases(input_file_path, transaction_type)

            if output_file:
                file_url = os.path.join(settings.MEDIA_URL, os.path.basename(output_file))
                return Response({"message": message, "processed_file_url": file_url}, status=status.HTTP_200_OK)

            return Response({"error": message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class GetProcessedTestCasesAPI(APIView):
    def get(self, request, format=None):
        try:
            file_url = request.GET.get('file_url')
            print("file_url:", file_url)

            if not file_url:
                return JsonResponse({"error": "File URL is required."}, status=status.HTTP_400_BAD_REQUEST)

            # Ensure file_url doesn't have leading slashes
            file_url = file_url.lstrip('/media/')
            print("Processed file URL:", file_url)
            # Construct the full file path
            file_path = os.path.join(settings.MEDIA_ROOT, file_url)
            print("File path:", file_path)
            # Check if the file exists
            if not os.path.exists(file_path):
                return JsonResponse({"error": "File not found."}, status=status.HTTP_404_NOT_FOUND)

            # If file exists, process and send the content
            with open(file_path, 'r', encoding='utf-8') as file:
                # Read the content and process it
                df = pd.read_csv(file)
                processed_data = df.fillna('').to_dict(orient='records')
                
                return JsonResponse({"processed_data": processed_data}, status=status.HTTP_200_OK)
            
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CompareTestCasesAPI(APIView):
    def get(self, request, format=None):
        try:
            file_url = request.GET.get('file_url')
            print("file_url:", file_url)

            if not file_url:
                return JsonResponse({"error": "File URL is required."}, status=status.HTTP_400_BAD_REQUEST)

            # Ensure file_url doesn't have leading slashes
            file_url = file_url.lstrip('/media/')
            print("Processed file URL:", file_url)
            # Construct the full file path
            file_path = os.path.join(settings.MEDIA_ROOT, file_url)
            print("File path from compare:", file_path)
            # Check if the file exists
            if not os.path.exists(file_path):
                return JsonResponse({"error": "File not found."}, status=status.HTTP_404_NOT_FOUND)
            
            comparison_results_json, comparison_results_file,excel_output_path = compare_test_cases(file_path)
            excel_output_path = os.path.basename(excel_output_path)
            # Return the results in the response
            return JsonResponse({
                "comparison_results_file": comparison_results_file,
                "comparison_results": comparison_results_json,
                "excel_output_path":excel_output_path
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class Feedback(APIView):
    def post(self, request, format=None):
        try:
            # Check if file is in request.FILES
            if "feedback_file" not in request.FILES:
                return JsonResponse({"error": "No file uploaded."}, status=status.HTTP_400_BAD_REQUEST)
            
            file = request.FILES["feedback_file"]
            file_path = f"feedback_files/{file.name}"  # Store in feedback_files folder

            # Save the file
            saved_path = default_storage.save(file_path, ContentFile(file.read()))
            feedback_json = feedback(saved_path)
            print("Feedback JSON:", feedback_json)
            return JsonResponse({
                "message": "Feedback file uploaded successfully",
                "file_path": saved_path,
                "feedback_json":feedback_json
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class SaveFeedback(APIView):
    def post(self, request, format=None):
        try:
            feedback_data = request.data.get("feedback_json", [])

            if not feedback_data:
                return JsonResponse({"error": "No feedback data received"}, status=status.HTTP_400_BAD_REQUEST)

            # Save the updated feedback to a JSON file (or database)
            feedback_dir = r"feedback_files"
            file_path = os.path.join(settings.MEDIA_ROOT,feedback_dir, "updated_feedback.json")
            print("File path for saving feedback:", file_path)
            with open(file_path, "w") as f:
                json.dump(feedback_data, f, indent=4)

            return JsonResponse({"message": "Feedback saved successfully", "file_path": file_path}, status=status.HTTP_200_OK)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
