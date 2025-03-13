"""
URL configuration for bmo_backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""


from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.conf import settings
from django.conf.urls.static import static
from .api import UploadFileAPIView, DissectTestCasesAPIView, ProcessLabelsAPIView, UploadMetadataAPIView, GetTransactionSummaryAPIView,UpdateTransactionMappingAPIView,PreProcessTestCasesAPI,GetProcessedTestCasesAPI,CompareTestCasesAPI,Feedback,SaveFeedback
from .input_dissect import download_file
urlpatterns = [

    path('api/upload/', UploadFileAPIView.as_view(), name='upload_file_api'),
    path('api/dissect-test-cases/', DissectTestCasesAPIView.as_view(), name='dissect_test_cases_api'),
    path('download/', download_file, name='download_file'),
    path('api/process-labels/', ProcessLabelsAPIView.as_view(), name='process_labels_api'),
    path('api/upload-metadata/', UploadMetadataAPIView.as_view(), name='upload_metadata'),
    path('api/get-transaction-summary/', GetTransactionSummaryAPIView.as_view(), name='get_transaction_summary'),
    path('api/update-transaction-summary/', UpdateTransactionMappingAPIView.as_view(), name='update_transaction_mapping'),
    path('api/pre-process-test-cases/', PreProcessTestCasesAPI.as_view(), name='preprocess-test-cases'),
    path('api/get-processed-test-cases/', GetProcessedTestCasesAPI.as_view(), name='get-processed-test-cases'),
    path('api/compare-test-cases/', CompareTestCasesAPI.as_view(), name='compare_test_cases'),
    path('api/upload-feedback/', Feedback.as_view(), name='feedback'),
    path('api/save-feedback/',SaveFeedback.as_view(),name='save-feedback'),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
