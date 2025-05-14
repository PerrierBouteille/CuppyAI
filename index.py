import os
import subprocess
import re
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
import streamlit as st
import os
os.environ["STREAMLIT_WATCHER_TYPE"] = "none"

# === Load LLaMA 4 ===
st.set_page_config(page_title="AI Coding Agent", layout="wide")
st.title("🤖 AI Coding Agent")

@st.cache_resource
def load_model():
    model_name = "deepseek-ai/deepseek-coder-6.7b-instruct"
    tokenizer = AutoTokenizer.from_pretrained(model_name,trust_remote_code=True,local_files_only=False)
    model = AutoModelForCausalLM.from_pretrained(model_name, torch_dtype=torch.float16, device_map="auto")
    return model, tokenizer

model, tokenizer = load_model()

def chat(prompt):
    inputs = tokenizer(prompt, return_tensors="pt").to("cuda")
    outputs = model.generate(**inputs, max_new_tokens=1024, do_sample=True, temperature=0.7)
    return tokenizer.decode(outputs[0], skip_special_tokens=True)

# === Utilities ===
def write_file(filename, content):
    os.makedirs(os.path.dirname(filename), exist_ok=True) if '/' in filename else None
    with open(filename, 'w') as f:
        f.write(content)
    return f"[+] File written: {filename}"

def run_shell(command):
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return result.stdout + result.stderr

def parse_response(response):
    actions = []
    file_blocks = re.findall(r'FILE: (.*?)\n(.*?)\n(?=FILE:|SHELL:|MESSAGE:|DONE|$)', response, re.DOTALL)
    shell_blocks = re.findall(r'SHELL:\n(.*?)\n(?=FILE:|SHELL:|MESSAGE:|DONE|$)', response, re.DOTALL)
    message_blocks = re.findall(r'MESSAGE:\n(.*?)\n(?=FILE:|SHELL:|MESSAGE:|DONE|$)', response, re.DOTALL)

    for fname, code in file_blocks:
        actions.append(('file', fname.strip(), code.strip()))
    for cmd in shell_blocks:
        actions.append(('shell', None, cmd.strip()))
    for msg in message_blocks:
        actions.append(('message', None, msg.strip()))

    return actions

# === Streamlit Interface ===
def agent_loop_ui(user_prompt):
    context = f"""
SYSTEM:
You are an autonomous coding agent. You can write files, run shell commands, and build software projects. 
Respond only with ACTION blocks:

FILE: <filename>
<code>

SHELL:
<command>

MESSAGE:
<message>

Type DONE when the task is complete.
USER TASK:
{user_prompt}
"""
    output_area = st.empty()
    console_output = ""
    generated_files = {}

    col1, col2 = st.columns([1, 2])
    file_browser = col1.empty()
    code_viewer = col2.empty()

    while True:
        response = chat(context)
        console_output += "\n=== MODEL RESPONSE ===\n" + response + "\n"
        actions = parse_response(response)

        for kind, name, content in actions:
            if kind == 'file':
                msg = write_file(name, content)
                generated_files[name] = content
                console_output += msg + "\n"
            elif kind == 'shell':
                output = run_shell(content)
                context += f"\nSHELL OUTPUT:\n{output}"
                console_output += output + "\n"
            elif kind == 'message':
                console_output += f"[AI MESSAGE] {content}\n"

        output_area.text(console_output)

        if 'DONE' in response:
            console_output += "[✓] Task Complete\n"
            break

    if generated_files:
        selected_file = file_browser.selectbox("Generated Files:", list(generated_files.keys()))
        code_viewer.code(generated_files[selected_file], language="python")

# === Main UI ===
prompt = st.text_area("Enter your software project description:", height=150)
if st.button("Run Agent") and prompt.strip():
    agent_loop_ui(prompt)
