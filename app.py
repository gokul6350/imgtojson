import streamlit as st
from together import Together
from dotenv import load_dotenv
import os
import base64
import json

# Load environment variables from .env file
load_dotenv()

# Retrieve the API key from the environment
api_key = os.getenv("TOGETHER_API_KEY")

if not api_key:
    st.error("API key not found. Please set it in the .env file.")
else:
    # Initialize the Together client with the API key
    client = Together(api_key=api_key)

    # Your application logic here
    st.title("Image to JSON Converter")

    # Define the prompt for JSON conversion
    getDescriptionPrompt = """
    You are an AI model that converts images into structured JSON data. 
    Analyze the attached image and provide a JSON representation of its contents. 
    Include details such as objects, text, colors, and layout. 
    Ensure the JSON is well-structured and includes all relevant information.
    """

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
        base64_image = base64.b64encode(open(save_path, "rb").read()).decode('utf-8')

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

        # Option to save the JSON to history
        if st.button("Add to History"):
            with open("history.json", "a") as history_file:
                history_file.write(json.dumps(json_data) + "\n")
            st.success("Added to history!")

    # Display the history in an expandable section
    with st.expander("View History"):
        if os.path.exists("history.json"):
            with open("history.json", "r") as history_file:
                for line in history_file:
                    st.json(json.loads(line))
        else:
            st.write("No history available.")

