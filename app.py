import streamlit as st
import pypdfium2 as pdfium
from io import BytesIO
import base64
from together import Together
import json
from PIL import Image
import sqlite3
import os
import google.generativeai as genai

def initialize_db():
    conn = sqlite3.connect('bills.db')
    cursor = conn.cursor()
    

    # Create new table with bill_date instead of upload_date
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_number TEXT NOT NULL,
            company_name TEXT NOT NULL,
            total_cost REAL NOT NULL,
            bill_date DATE NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def add_bill_to_db(invoice_number, company_name, total_cost, bill_date):
    conn = sqlite3.connect('bills.db')
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO bills (invoice_number, company_name, total_cost, bill_date)
        VALUES (?, ?, ?, ?)
    """, (invoice_number, company_name, total_cost, bill_date))
    conn.commit()
    conn.close()

def remove_json_markers(text):
    # Remove ```json from the beginning
    if text.startswith("```json"):
        text = text.replace("```json", "")
    # Remove ``` from the end
    
        text = text.replace("\n```", "")
        return text.strip()
    else:
        return text
# Example usage


def main():
    # Initialize the database
    initialize_db()
    
    st.set_page_config(
        page_title="Bill Analyzer",
        page_icon="📄",
        layout="wide"
    )
    
    st.title("📄 Bill Analyzer")
    
    # Add a sidebar with info and API key input
    with st.sidebar:
        st.info("This app converts PDF pages or images to JSON by analyzing them.")
        ai_service = st.radio("Select AI Service:", ["Test ai model 1", "Test ai model 2"])
        
        if ai_service == "Together AI":
            ey = st.text_input("Enter your Together AI API key:", type="password")
        else:
            ey = st.text_input("Enter your Gemini AI API key:", type="password")
            if ey:
                os.environ["GEMINI_API_KEY"] = ey
                genai.configure(api_key=ey)
                
   
    
    if not ey:
        st.warning("Please enter your Together AI API key to proceed.")
        return
    
    # Initialize Together AI client
    together = Together(api_key=ey)
    
    # Define the prompt for JSON conversion
    getDescriptionPrompt = """
        You are an AI model working for Global Autotech Limited that extracts billing information from images.
        Analyze the attached bill/invoice image and provide ONLY a JSON response with the following case-sensitive fields:
        - vendor_name: Name of the company/vendor
        - bill_date: Date of the bill
        - total_amount: Total amount of the bill
        - invoice_number: Invoice number of the bill
        Ensure the JSON is well-structured, includes only these fields, and contains no additional information.
        Do not include any text, explanations, or code blocks. Respond with pure "JSON" only.
    """
    
    # File uploader accepts PDF and image files
    uploaded_file = st.file_uploader(
        "Choose a PDF or Image file",
        type=["pdf", "png", "jpg", "jpeg"],
        help="Upload a PDF or Image file to convert and analyze"
    )
    
    if uploaded_file is not None and ey:
        try:
            # Show progress bar
            with st.spinner('Processing and analyzing...'):
                file_type = uploaded_file.type
                if file_type == "application/pdf":
                    # Process PDF file
                    pdf = pdfium.PdfDocument(uploaded_file.read())
                    
                    # Show total pages
                    total_pages = len(pdf)
                    st.info(f"Total pages: {total_pages}")
                    
                    # Convert each page
                    for page_number in range(total_pages):
                        # Create two columns for image and analysis
                        col1, col2 = st.columns(2)
                        
                        # Load and process the page
                        page = pdf[page_number]
                        bitmap = page.render(scale=1.0, rotation=0)
                        pil_image = bitmap.to_pil()
                        
                        # Left column: Display image and download button
                        with col1:
                            st.subheader(f"Page {page_number + 1}")
                            st.image(pil_image, caption=f"Page {page_number + 1}", use_container_width=True)
                            
                            # Create download button
                            buf = BytesIO()
                            pil_image.save(buf, format="PNG")
                            
                            st.download_button(
                                label=f"⬇️ Download Page {page_number + 1}",
                                data=buf.getvalue(),
                                file_name=f"page_{page_number + 1}.png",
                                mime="image/png",
                                key=f"download_{page_number}"
                            )
                        
                        # Right column: Together AI analysis
                        with col2:
                            st.subheader(f"Analysis of Page {page_number + 1}")
                            
                            # Convert image to base64
                            buffered = BytesIO()
                            pil_image.save(buffered, format="PNG", encoding='utf-8')
                            base64_image = base64.b64encode(buffered.getvalue()).decode('utf-8')
                            
                            # Get analysis based on selected AI service
                            if ai_service == "Together AI":
                                response = together.chat.completions.create(
                                    model="meta-llama/Llama-3.2-11B-Vision-Instruct-Turbo",
                                    messages=[
                                        {
                                            "role": "user",
                                            "content": [
                                                {"type": "text", "text": getDescriptionPrompt},
                                                {
                                                    "type": "image_url",
                                                    "image_url": {
                                                        "url": f"data:image/png;base64,{base64_image}",
                                                    },
                                                },
                                            ],
                                        }
                                    ]
                                )
                                json_description = response.choices[0].message.content.strip()
                            else:
                                # Configure Gemini
                                generation_config = {
                                    "temperature": 1,
                                    "top_p": 0.95,
                                    "top_k": 40,
                                    "max_output_tokens": 8192,
                                }
                                model = genai.GenerativeModel("gemini-1.5-pro", generation_config=generation_config)
                                
                                # Convert PIL Image to bytes
                                buffered = BytesIO()
                                pil_image.save(buffered, format="PNG")
                                image_bytes = buffered.getvalue()
                                
                                # Create content parts with image bytes
                                content_parts = [
                                    {
                                        "mime_type": "image/png",
                                        "data": image_bytes
                                    },
                                    getDescriptionPrompt
                                ]
                                
                                # Generate response
                                response = model.generate_content(content_parts)
                                json_description = response.text.strip()
                            
                            print("============")
                            print(json_description)
                            print("============")
                            try:
                                json_data = json.loads(remove_json_markers(json_description))
                                # Validate that only required fields are present
                                valid_keys = {"vendor_name", "bill_date", "total_amount", "invoice_number"}
                                json_data = {k: v for k, v in json_data.items() if k in valid_keys}
                            except json.JSONDecodeError:
                                json_data = {"error": "Invalid JSON response from AI model."}
                            
                            if "error" not in json_data:
                                form_key = f"form_page_{page_number}"
                                with st.form(key=form_key):
                                    st.markdown("### Edit Extracted Data")
                                    company_name = st.text_input("Company Name", value=json_data.get("vendor_name", ""))
                                    bill_date = st.text_input("Bill Date", value=json_data.get("bill_date", ""))
                                    # Clean the total_amount string by removing commas before converting to float
                                    total_amount_str = str(json_data.get("total_amount", "0.0")).replace(",", "")
                                    total_cost = st.number_input("Total Cost", value=float(total_amount_str), format="%.2f")
                                    invoice_number = st.text_input("Invoice Number", value=json_data.get("invoice_number", ""))
                                    
                                    submit_button = st.form_submit_button("Add to Database")
                                    
                                    if submit_button:
                                        add_bill_to_db(
                                            invoice_number=invoice_number,
                                            company_name=company_name,
                                            total_cost=total_cost,
                                            bill_date=bill_date
                                        )
                                        st.success("✅ Added to database!")
                            else:
                                st.error(json_data["error"])
                            
                            st.json(json_data)
                        
                        st.divider()
                
                elif file_type in ["image/png", "image/jpg", "image/jpeg"]:
                    # Process Image file
                    pil_image = Image.open(uploaded_file)
                    
                    # Create two columns for image and analysis
                    col1, col2 = st.columns(2)
                    
                    # Left column: Display image
                    with col1:
                        st.subheader("Uploaded Image")
                        st.image(pil_image, caption="Uploaded Image", use_container_width=True)
                        
                        # Create download button
                        buf = BytesIO()
                        pil_image.save(buf, format="PNG")
                        
                        st.download_button(
                            label="⬇️ Download Image",
                            data=buf.getvalue(),
                            file_name="uploaded_image.png",
                            mime="image/png",
                            key="download_image"
                        )
                    
                    # Right column: Together AI analysis
                    with col2:
                        st.subheader("Analysis of Uploaded Image")
                        
                        # Convert image to base64
                        buffered = BytesIO()
                        pil_image.save(buffered, format="PNG", encoding='utf-8')
                        base64_image = base64.b64encode(buffered.getvalue()).decode('utf-8')
                        
                        # Get analysis based on selected AI service
                        if ai_service == "Together AI":
                            response = together.chat.completions.create(
                                model="meta-llama/Llama-3.2-11B-Vision-Instruct-Turbo",
                                messages=[
                                    {
                                        "role": "user",
                                        "content": [
                                            {"type": "text", "text": getDescriptionPrompt},
                                            {
                                                "type": "image_url",
                                                "image_url": {
                                                    "url": f"data:image/png;base64,{base64_image}",
                                                },
                                            },
                                        ],
                                    }
                                ]
                            )
                            json_description = response.choices[0].message.content.strip()
                        else:
                            # Configure Gemini
                            generation_config = {
                                "temperature": 1,
                                "top_p": 0.95,
                                "top_k": 40,
                                "max_output_tokens": 8192,
                            }
                            model = genai.GenerativeModel("gemini-1.5-pro", generation_config=generation_config)
                            
                            # Convert PIL Image to bytes
                            buffered = BytesIO()
                            pil_image.save(buffered, format="PNG")
                            image_bytes = buffered.getvalue()
                            
                            # Create content parts with image bytes
                            content_parts = [
                                {
                                    "mime_type": "image/png",
                                    "data": image_bytes
                                },
                                getDescriptionPrompt
                            ]
                            
                            # Generate response
                            response = model.generate_content(content_parts)
                            json_description = response.text.strip()
                        
                        print("============")
                        print(json_description)
                        print("============")
                        try:
                            json_data = json.loads(remove_json_markers(json_description))
                            # Validate that only required fields are present
                            valid_keys = {"vendor_name", "bill_date", "total_amount", "invoice_number"}
                            json_data = {k: v for k, v in json_data.items() if k in valid_keys}
                        except json.JSONDecodeError:
                            json_data = {"error": "Invalid JSON response from AI model."}
                        
                        if "error" not in json_data:
                            with st.form(key="form_image"):
                                st.markdown("### Edit Extracted Data")
                                company_name = st.text_input("Company Name", value=json_data.get("vendor_name", ""))
                                bill_date = st.text_input("Bill Date", value=json_data.get("bill_date", ""))
                                # Clean the total_amount string by removing commas before converting to float
                                total_amount_str = str(json_data.get("total_amount", "0.0")).replace(",", "")
                                total_cost = st.number_input("Total Cost", value=float(total_amount_str), format="%.2f")
                                invoice_number = st.text_input("Invoice Number", value=json_data.get("invoice_number", ""))
                                
                                submit_button = st.form_submit_button("Add to Database")
                                
                                if submit_button:
                                    add_bill_to_db(
                                        invoice_number=invoice_number,
                                        company_name=company_name,
                                        total_cost=total_cost,
                                        bill_date=bill_date
                                    )
                                    st.success("✅ Added to database!")
                        else:
                                st.error(json_data["error"])
                        
                        st.json(json_data)
                    
                    st.divider()
                
                else:
                    st.error("Unsupported file type.")
            
            st.success("✅ Conversion and analysis completed!")
                
        except Exception as e:
            st.error(f"❌ An error occurred: {str(e)}")
            st.warning("Please try again with a different file.")

if __name__ == "__main__":
    main()
