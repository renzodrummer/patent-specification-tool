# import os, sys; sys.path.append(os.path.dirname(os.path.abspath(__file__)))
# from functions.utils import extract_info, fetch_patent_details, saveToGoogleSheet, generate_output, action_steps, access_token, get_authorization_code, st, PyPDF2, re
import os
import sys

# Add the parent directory of 'pages' to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from pages.functions.utils import saveToGoogleSheet, generate_output, st, PyPDF2, re, prepare_image_for_bedrock

def main():
    try:
       
        col1, col2, col3 = st.columns(3)

        with col1:
            st.write(' ')

        with col2:
            # Display the logo
            st.image("logo.png")

        with col3:
            st.write(' ')
            
        st.title("AI-powered Patent Specification Tool")
        
        uploaded_file = st.file_uploader("Upload Claims PDF", type="pdf")

        if uploaded_file is not None:
            
            with st.spinner('Please wait extracting claims'):

                pdf_reader = PyPDF2.PdfReader(uploaded_file)
                print("pdf_reader 1 working")
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text()
                
                text = re.sub(r'(?<!\n)(?<!\t) +', ' ', text)
            
            uploaded_drawings = st.file_uploader("Upload Drawings PDF", type="pdf")
            
            if uploaded_drawings is not None:
                
                with st.spinner('Please wait extracting images'):
                    
                    pdf_reader = PyPDF2.PdfReader(uploaded_drawings)
                    
                    # Collect all images from all pages
                    all_images = []
                    for page in pdf_reader.pages:
                        all_images.extend(page.images)
                    
                    if all_images:
                        try:
                            # Process images in batches of 20
                            batch_size = 20
                            all_contents = []
                            
                            # Prepare batches
                            for batch_start in range(0, len(all_images), batch_size):
                                batch_end = min(batch_start + batch_size, len(all_images))
                                batch_images = all_images[batch_start:batch_end]
                                
                                # Prepare content for this batch
                                content = []
                                for idx, image_file_object in enumerate(batch_images):
                                    image_bytes = image_file_object.data
                                    base64_image = prepare_image_for_bedrock(image_bytes)
                                    
                                    # Add image and separator to content
                                    content.extend([
                                        {
                                            "type": "image",
                                            "source": {
                                                "type": "base64",
                                                "media_type": "image/jpeg",
                                                "data": base64_image
                                            }
                                        },
                                        {
                                            "type": "text",
                                            "text": f"\nImage {batch_start + idx + 1}:\n"
                                        }
                                    ])
                                
                                # Add instruction for this batch
                                content.append({
                                    "type": "text",
                                    "text": f"Analyze the images above (Images {batch_start + 1} to {batch_end}) and provide a detailed description of what you see in each one. Please separate your analysis for each image clearly."
                                })
                                
                                all_contents.append(content)
                                
                        except Exception as e:
                            st.error(f"Error processing images: {str(e)}")
                            
                    # Display Extracted Claims
                    with st.expander("Claims"):
                        st.markdown(text, unsafe_allow_html=True) 
                    
                    # Display Extracted Images
                    with st.expander("Extracted Images"):
                        for page_num, page in enumerate(pdf_reader.pages):
                            # Create a row for each page
                            st.write(f"Page {page_num + 1}")
                            # Create columns for multiple images in a row
                            cols = st.columns(3)  # Display up to 3 images per row
                            col_idx = 0
                            
                            for image_file_object in page.images:
                                # Convert image data to bytes
                                image_bytes = image_file_object.data
                                
                                # Display image in the current column
                                with cols[col_idx]:
                                    st.image(image_bytes)
                                    col_idx = (col_idx + 1) % 3  # Move to next column, wrap around after 3
                            
                            if page.images:
                                st.markdown("---")  # Add separator between pages
                            else:
                                st.write("No images found on this page")
                                
                    with st.expander("Generating output"):           
                    # generate output function
                        output = generate_output(text, all_contents)
                        st.markdown(output, unsafe_allow_html=True) 
                        saveToGoogleSheet(output)
                    
                st.success("Successful!")
                
    except Exception as e:
        st.error(f"An error occurred main: {str(e)}")
        st.exception(e)

if __name__ == "__main__":
    main()