# 🧠 AI Based E-COMMERECE Agent

## 🔧 Setup Instructions

Follow these steps to set up and run the project:

### 1. Clone the Repository
```bash
git clone https://github.com/moazzimali843/E-Commerce-Agent
cd E-Commerce-Agent
```

### 2. Create a virtual environment
```bash
python -m venv myenv
```
### 3. Activate it (Windows)
```bash
myenv\Scripts\activate
```

### For macOS/Linux
```bash
source myenv/bin/activate
```

### 5. Install Dependencies
```bash
pip install -r requirements.txt
```
### 6. Set Up Environment Variables
Rename the .env.example file to .env and add your OpenAI API key:
```bash
OPENAI_API_KEY=your-api-key-here
```
## 🚀 Running the Application
### 1. Start the FastAPI Backend
```bash
uvicorn app.main:app --reload
```

### 2. Start the Streamlit Frontend
In a new terminal (with the virtual environment activated in that terminal as well):
```bash
streamlit run frontend/app.py
```

# Demo Screenshot
![image](https://github.com/user-attachments/assets/90bf1229-5042-4a54-986b-4583dd53ede6)
