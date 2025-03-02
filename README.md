# 🚀 AI Financial Assistant

AI Financial Assistant is an interactive tool that provides financial insights based on user-provided data. The assistant is built using **FLAN-T5**, powered by **Streamlit**, and enables real-time Q&A about personal finance.

## 🌟 Features
- **Chat-Based Interface**: Ask financial questions and get AI-powered responses.
- **User Financial Data Input**: Provide your balance, expenses, and investments for personalized answers.
- **Powered by FLAN-T5**: Uses a lightweight yet powerful transformer model.
- **Web App with Streamlit**: Easy-to-use interactive UI.
- **Customizable & Extendable**: Modify the model or data handling as needed.

---

## 📂 Project Structure
```
ai_financial_assistant/
│── app.py                    # Streamlit web app
│── assistant.py               # (Optional) CLI-based assistant
│── requirements.txt           # Dependencies for installation
│── README.md                  # Project documentation
│── models/                    # (Optional) Store model weights
│── data/                      # (Optional) Store user financial data
│── logs/                      # (Optional) Debugging logs
│── .env/                      # (Optional) Virtual environment
```

---

## 🚀 Installation & Setup

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/yourusername/ai_financial_assistant.git
cd ai_financial_assistant
```

### 2️⃣ Create a Virtual Environment (Optional but Recommended)
```bash
python -m venv .env
source .env/bin/activate  # On macOS/Linux
.env\Scripts\activate     # On Windows
```

### 3️⃣ Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 📌 Usage

### ✅ Run the Streamlit Web App
```bash
streamlit run app.py
```
This will open the app in your browser, allowing you to chat with the assistant.

### ✅ Run the Assistant in Command Line (Optional)
```bash
python assistant.py
```

---

## ⚙️ Configuration
Modify **`app.py`** to adjust model parameters or integrate additional financial data sources.

---

## 🛠 Future Enhancements
- ✅ Fine-tune FLAN-T5 with financial datasets
- ✅ Integrate external financial APIs (e.g., stock market data)
- ✅ Add a chatbot memory for contextual conversations

---

## 🤝 Contributing
Pull requests are welcome! Feel free to open issues and suggest improvements.

---

## 📝 License
This project is licensed under the **MIT License**.

---

### 🎯 Author
**RAJBIR RAY** – [LinkedIn](https://www.linkedin.com/in/rajbir-ray-9608852b5/)

