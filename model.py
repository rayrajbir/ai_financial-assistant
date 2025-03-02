from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

class FinancialAssistant:
    def __init__(self, model_name="google/flan-t5-base"):
        print("Loading Financial Assistant AI...")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

    def generate_response(self, query):
        inputs = self.tokenizer(query, return_tensors="pt")
        output = self.model.generate(**inputs, max_length=150)
        return self.tokenizer.decode(output[0], skip_special_tokens=True)

# Initialize Assistant
assistant = FinancialAssistant()

# Interactive Mode
print("\n🔹 AI Financial Assistant (Type 'exit' to quit) 🔹")
while True:
    user_input = input("\n💬 Ask a finance question: ")
    if user_input.lower() == "exit":
        print("👋 Goodbye!")
        break
    response = assistant.generate_response(user_input)
    print("\n🤖 AI Advice:", response)
