import requests
from bs4 import BeautifulSoup
import json
from io import BytesIO
import os
import time
import gspread
from google.oauth2.service_account import Credentials
import base64

import streamlit as st
import PyPDF2
import re
import tempfile

import io
import math

# AWS
import boto3
from botocore.exceptions import ClientError
from botocore.config import Config
# Load the .env file
from dotenv import load_dotenv
load_dotenv()

def saveToGoogleSheet(data):

    encoded_credentials = os.getenv("gsheets")
    if not encoded_credentials:
        st.error("gsheets environment variable not set")
        return None

    # Open the Google Sheet

    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

        # Decode the base64 string to JSON
        credentials_json = base64.b64decode(encoded_credentials).decode("utf-8")
        credentials_info = json.loads(credentials_json)
        
        creds = Credentials.from_service_account_info(credentials_info, scopes=scope)
        client = gspread.authorize(creds)

        spreadsheet = client.open("PDF upload")
        worksheet = spreadsheet.worksheet("Sheet3")

        result = worksheet.append_row([data])
        print(f"Data saved to Google Sheet: {result}")
    except gspread.exceptions.APIError as api_error:
        print(f"API Error: {api_error}")
    except Exception as e:
        print(f"Error occurred {e}")

def generate_output(claims_content, drawing_content):

    try:
        
        all_analyses = []
        
        for batch_num, batch_content in enumerate(drawing_content):
            
            response = claude_ai(batch_content)
            
            all_analyses.append(response)

        if all_analyses:
            # Here you can add your additional prompt or processing
            prompt = f""" 
                You are an expert Australian patent attorney tasked with writing several sections of a complete patent specification. Your primary goal is to provide a comprehensive, technically accurate, and legally sound description of the invention based on the provided information.

                First, carefully review the Brief Description of Drawings:

                <brief_description_of_drawings>
                    {'\n'.join(all_analyses)}
                </brief_description_of_drawings>

                Here are the claims for reference:

                <claims>
                    {claims_content}
                </claims>

                Your task is to expand on this information to create a detailed patent specification that would satisfy the requirements of the Australian Patent Office. You will generate the following sections:

                1. Background
                2. Summary of the Invention
                3. Detailed Description
                4. Industrial Applicability
                5. Variations

                For each section, first plan your approach inside <section_analysis> tags. Then, write the corresponding section of the specification based on your planning. Remember to exclude all tags <section_planning>, </section_analysis>  from your final output.

                Here are the instructions for each section:

                1. Background:
                <section_analysis>
                - List key elements from the Brief Description of Drawings relevant to this section
                - Identify the technical field of the invention
                - Discuss relevant prior art
                - Highlight problems or limitations in the prior art that the invention addresses
                </section_analysis>
                [Write the Background section here]

                2. Summary of the Invention:
                <section_analysis>
                - List key elements from the Brief Description of Drawings relevant to this section
                - Summarize the key aspects of the invention
                - Highlight the main advantages or improvements over prior art
                - Briefly mention the main components or steps of the invention
                </section_analysis>
                [Write the Summary of the Invention section here]

                3. Detailed Description:
                For this section, follow these steps:
                a) Drawing Analysis
                b) Component Description
                c) Sub-component Analysis
                d) Functional Integration
                e) Technical Specifications
                f) Manufacturing Considerations

                For each step:
                <section_analysis>
                - List key elements from the Brief Description of Drawings relevant to this section
                - Create a bulleted list of components and their relationships
                - Identify any gaps or assumptions that need to be made
                - Outline a structure for this section, including relevant details as described in the original prompt
                </section_analysis>
                [Write the corresponding part of the Detailed Description here]

                4. Industrial Applicability:
                <section_analysis>
                - List key elements from the Brief Description of Drawings relevant to this section
                - Identify potential industries or fields where the invention could be applied
                - Describe practical applications of the invention
                - Highlight any economic or environmental benefits
                </section_analysis>
                [Write the Industrial Applicability section here]

                5. Variations:
                <section_analysis>
                - List key elements from the Brief Description of Drawings relevant to this section
                - Consider potential modifications or alternative embodiments of the invention
                - Discuss how these variations might affect the function or performance of the invention
                - Ensure these variations are supported by the original disclosure
                </section_analysis>
                [Write the Variations section here]

                Throughout your description:
                - Maintain proper antecedent basis and use consistent terminology aligned with the claims.
                - Provide detailed explanations and examples where appropriate to enhance clarity and comprehensiveness.
                - Cross-reference different aspects of the invention to create a cohesive description.
                - Use technical language appropriate for patent specifications while ensuring clarity for a skilled reader in the field.

                Your final output should be a cohesive, detailed patent specification incorporating all the analyzed elements into a logical and comprehensive narrative. The content should be suitable for direct export to a Google Doc with basic formatting (section headings, paragraphs, and numbered lists where appropriate).
                
                Remember to exclude all section tags from your final output. The final format should look like this:

                1. Background
                [Content of Background section]

                2. Summary of the Invention
                [Content of Summary of the Invention section]

                3. Detailed Description
                [Content of Detailed Description section, including subsections a-f]

                4. Industrial Applicability
                [Content of Industrial Applicability section]

                5. Variations
                [Content of Variations section]

                Please proceed with your planning and writing of the patent specification.
            """
            
            final_response = claude_ai(prompt)
            # You might want to do something with this prompt
            # For example, make another API call or process the result
            
            return final_response
        else:
            return "No drawings result generated"
            
    except Exception as e:
        print(f"Error generating output: {str(e)}")
        return None
   
def claude_ai(prompt):
    
    config = Config(read_timeout=1000)
    
    # aws bedrock client
    client = boto3.client("bedrock-runtime", region_name=os.environ.get("aws_region"), aws_access_key_id=os.environ.get("aws_accesskey"), aws_secret_access_key=os.environ.get("aws_secretkey"), config=config)
    model_id = "anthropic.claude-3-sonnet-20240229-v1:0"
    
    # Format the request payload using the model's native structure.
    native_request = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 2000,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    }
    
    # print(native_request)

    # Convert the native request to JSON.
    request = json.dumps(native_request)
    
    try:
        # Invoke the model with the request.
        response = client.invoke_model(modelId=model_id, body=request)
        
        # Decode the response body.
        model_response = json.loads(response["body"].read())

        # Extract and print the response text.
        response_text = model_response["content"][0]["text"]
        
        return response_text

    except (ClientError, Exception) as e:
        print(f"ERROR: Can't invoke '{model_id}'. Reason: {e}")
        st.markdown(f"ERROR: Can't invoke '{model_id}'. Reason: {e}", unsafe_allow_html=True)
        exit(1) 
                  
def format_output(response):

    response
    
    return response

def prepare_image_for_bedrock(image_bytes):
    """
    Convert image bytes to base64 string format required by Bedrock.
    Args:
        image_bytes: Raw bytes of the image
    Returns:
        str: Base64 encoded string of the image
    """
    # Convert image bytes to base64 string
    base64_image = base64.b64encode(image_bytes).decode('utf-8')
    return base64_image