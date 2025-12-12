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
    git clone <repo-url>
    cd <repo-folder>
    ```

2.  **Create a virtual environment (Optional but recommended):**
    ```bash
    python -m venv venv
    or
    uv venv (if you use uv instead of pip)
    # Windows:
    venv\Scripts\activate
    source .venv/Scripts/activate (for uv users)
    # Mac/Linux:
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    or
    uv pip install -r requirements.txt
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
```

## Architecture of the Evaluation Pipeline

The pipeline is designed as an automated **"LLM-as-a-Judge" system** that audits the quality of a RAG (Retrieval-Augmented Generation) chatbot. It follows a four-stage architecture:

### 1. Ingestion & Linkage (The Bridge)
* The system ingests raw logs from two disconnected sources: **Chat Logs** (User-AI conversations) and **Vector Context Logs** (RAG retrieval data).
* Since these logs lack a shared unique identifier, a **Fuzzy Matching Engine** (using Python's `difflib`) scans the datasets. It uses the AI’s response text as a unique "fingerprint" to reconstruct the session, linking a specific Chat Turn to its corresponding Source Context with >85% confidence.

### 2. Context Reconstruction
* Once linked, the pipeline isolates the specific "Ground Truth."
* It extracts only the `vectors_used`—the specific text chunks the AI retrieved from the database—discarding unused noise to create a clean context window for evaluation.

### 3. The Evaluation Engine
* The reconstructed data is passed to the **Judge** (latest gemini flash model available).
* **Hallucination Check:** A strict prompt compares the AI's answer against the Source Context to detect unsupported claims.
* **Relevance Check:** A separate prompt evaluates if the AI's answer actually addresses the User's query.

### 4. Structured Reporting
* The system enforces **JSON Mode** on the LLM output, ensuring that qualitative evaluations are converted into quantitative data (scores 0.0–1.0) for automated reporting and analytics.

```mermaid
graph TD
    A[Raw Chat JSON] --> C{Fuzzy Linker}
    B[Raw Vector JSON] --> C
    
    C -->|Match Found| D[Reconstructed Session]
    D --> E[Context Builder]
    
    E --> F[LLM Judge (Gemini 1.5 Flash)]
    
    F -->|Prompt: Truthfulness| G[Hallucination Score]
    F -->|Prompt: Helpfulness| H[Relevance Score]
    
    G --> I[Final JSON Report]
    H --> I

## Handling Scaling in future

Currently running through every chat between the chatbot and user through ai would be classified as a Ddos attack. To handle this scale, I would make certain changes to the code structure, likewise:

1. Changing the request rate:
The current script utilizes Python's asyncio library, so instead of processing conversations sequentially (i.e. one at a time), the system would fire API requests in parallel. This will reduce the total processing time from hours to minutes, limited only by the API rate limits set by the organisation.
2. Sampling strategy:
Instead of using all the 1 million converstaion, I would implement a sampling strategy to make sure the high risk topic (for eg. pricing, medical information etc.) are the ones that are being trageted frequently
3. Decoupled Architecture:
In a live system with millions of users, running a complex evaluation script instantly for every message would make the chatbot slow and laggy for the user. To fix this, I propose a **Decoupled Architecture**:

* **The "Waiting Room" Concept:** Instead of grading the AI immediately, the Chatbot simply pushes the log into a **Message Queue** (like Kafka or RabbitMQ) and instantly responds to the user. It does not wait for the evaluation.
* **Background Processing:** My evaluation script acts as a "Worker" that sits in the background. It pulls logs from the queue and grades them asynchronously at its own pace.
* **Benefit:** This ensures the user **never experiences lag**, and if traffic spikes (e.g., millions of users), we can simply add more "Worker" scripts to clear the queue faster without changing the chatbot code. 
