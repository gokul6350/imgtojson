import streamlit as st
from together import Together
import os
import base64
import json

# Initialize the Together client with the API key
client = Together(api_key="1abf00331355c8d852969c565b6bb5a9d16e7d9d16c0c095db73d6ebd59da9d5")  # Replace with your actual API key
print("starting bitch")
# Define the prompt for JSON conversion
getDescriptionPrompt = """
You are an AI model that converts images into structured JSON data. 
Analyze the attached image and provide a JSON representation of its contents. 
Include details such as objects, text, colors, and layout. 
Ensure the JSON is well-structured and includes all relevant information.
"""

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

# Streamlit app
st.title("Image to JSON Converter")

# File uploader
uploaded_file = st.file_uploader("Choose an image...", type=["png", "jpg", "jpeg"])

if uploaded_file is not None:
    # Display the uploaded image
    st.image(uploaded_file, caption='Uploaded Image.', use_container_width=True)
    
    # Save the uploaded file to a local directory
    if not os.path.exists("uploaded_images"):
        os.makedirs("uploaded_images")
    save_path = os.path.join("uploaded_images", uploaded_file.name)
    with open(save_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    # Encode the image in base64
    base64_image = encode_image(save_path)

    # Create a request to get the JSON description
    response = client.chat.completions.create(
        model="meta-llama/Llama-3.2-11B-Vision-Instruct-Turbo",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": getDescriptionPrompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}",
                        },
                    },
                ],
            }
        ]
    )

    # Extract the JSON description from the response
    json_description = response.choices[0].message.content

    # Parse the content into a JSON object
    try:
        json_data = json.loads(json_description)
    except json.JSONDecodeError:
        # If the content is not a valid JSON, wrap it in a JSON structure
        json_data = {"description": json_description}

    # Display the JSON description
    st.json(json_data)

