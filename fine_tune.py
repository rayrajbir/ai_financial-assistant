import json
import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer, Trainer, TrainingArguments, DataCollatorForSeq2Seq
from datasets import Dataset

# Load Dataset
with open("finance_data.json", "r") as f:
    data = json.load(f)

dataset = Dataset.from_list(data)

# Load Tokenizer and Model
model_name = "google/flan-t5-base"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

# Tokenize Data
def preprocess_data(examples):
    inputs = tokenizer(examples["question"], padding="max_length", truncation=True, max_length=512)
    targets = tokenizer(examples["answer"], padding="max_length", truncation=True, max_length=512)
    inputs["labels"] = targets["input_ids"]
    return inputs

tokenized_dataset = dataset.map(preprocess_data, batched=True)

# Training Arguments
training_args = TrainingArguments(
    output_dir="./models",
    per_device_train_batch_size=4,
    num_train_epochs=3,
    save_steps=500,
    save_total_limit=2,
    logging_dir="./logs",
    logging_steps=100,
    evaluation_strategy="no"
)

# Trainer
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_dataset,
    tokenizer=tokenizer,
    data_collator=DataCollatorForSeq2Seq(tokenizer)
)

# Train Model
trainer.train()

# Save Fine-Tuned Model
model.save_pretrained("./models")
tokenizer.save_pretrained("./models")
