# BeyondChats LLM Evaluation

## Local Setup Instructions

Follow these steps to set up and run the evaluation pipeline on your local machine.

### 1. Prerequisites
* Python 3.8 or higher
* A Google Cloud Project with the **Gemini API** enabled
* A valid API Key from [Google AI Studio](https://aistudio.google.com/app/apikey)

### 2. Installation
1.  **Clone the repository:**
    ```bash
    git clone <your-repo-url>
    cd <your-repo-folder>
    ```

2.  **Create a virtual environment (Optional but recommended):**
    ```bash
    python -m venv venv
    # Windows:
    venv\Scripts\activate
    # Mac/Linux:
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install google-generativeai python-dotenv
    ```

### 3. Configuration
1.  Create a `.env` file in the root directory.
2.  Add your Gemini API key:
    ```env
    GEMINI_API_KEY=your_actual_api_key_here
    ```

### IMPORTANT
In my testing and working around with the json files (uploaded in the data folder), I found out that the sample-chat-2 and sample-vector-2 are mismatched, so I left it as it is

### 4. Running the Pipeline
Execute the main script:
```bash
python judge.py

