import os
import subprocess
import re
import torch
import streamlit as st
from transformers import AutoModelForCausalLM, AutoTokenizer

# Prevent Streamlit file watch errors
os.environ["STREAMLIT_WATCHER_TYPE"] = "none"

st.set_page_config(page_title="AI Coding Agent", layout="wide")
st.title("🤖 AI Coding Agent")

# === Load Model ===
@st.cache_resource
def load_model():
    model_name = "deepseek-ai/deepseek-coder-6.7b-instruct"
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True, local_files_only=False)
    model = AutoModelForCausalLM.from_pretrained(
        model_name, torch_dtype=torch.float16, device_map="auto"
    )
    return model, tokenizer

model, tokenizer = load_model()

def chat(prompt):
    if(not(torch.cuda.is_available())):
        exit("No GPU available")
    inputs = tokenizer(prompt, return_tensors="pt").to("cuda" if torch.cuda.is_available() else "cpu")
    outputs = model.generate(
        **inputs,
        max_new_tokens=1024,
        temperature=0.3,
        do_sample=False,
        top_p=0.95,
        repetition_penalty=1.2
    )
    return tokenizer.decode(outputs[0], skip_special_tokens=True)

# === Utilities ===
def write_file(filename, content):
    # Reject filenames that are clearly too long or contain unexpected characters
    if not filename or len(filename) > 255 or not re.match(r'^[\w.\-/]+$', filename):
        return f"[!] Skipped invalid filename: {filename}"
    if '/' in filename:
        os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, 'w') as f:
        f.write(content)
    return f"[+] File written: {filename}"

def run_shell(command):
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return result.stdout + result.stderr

def parse_response(response):
    actions = []
    file_blocks = re.findall(r'FILE:\s*([^\n\r]+)\n<code>\n(.*?)</code>', response, re.DOTALL)
    shell_blocks = re.findall(r'SHELL:\s*<code>\n(.*?)</code>', response, re.DOTALL)
    message_blocks = re.findall(r'MESSAGE:\s*(.*?)\n', response)

    for fname, code in file_blocks:
        actions.append(('file', fname.strip(), code.strip()))
    for cmd in shell_blocks:
        actions.append(('shell', None, cmd.strip()))
    for msg in message_blocks:
        actions.append(('message', None, msg.strip()))

    return actions

def detect_language_from_extension(filename):
    ext = os.path.splitext(filename)[-1].lower()
    return {
        '.py': 'python',
        '.html': 'html',
        '.css': 'css',
        '.js': 'javascript',
        '.sh': 'bash',
        '.txt': 'text',
        '.md': 'markdown'
    }.get(ext, 'text')

# === Streamlit Agent Loop ===
def agent_loop_ui(user_prompt):
    context = f"""
SYSTEM:
You are an autonomous coding agent. You can write files, run shell commands, and build software projects.
Respond strictly using ACTION blocks.
Avoid summarizing or skipping steps. Your job is to build everything needed, including full file contents.
Important:
- DO NOT escape HTML tags. Use raw HTML with < and >.
- DO NOT repeat characters or special entities like &lt; or &gt;.
- DO NOT use placeholder names like filename.ext.

WARNING: DO NOT use "filename.ext" literally. Replace it with the actual name of the file (e.g., "index.html", "main.py").

Use this exact format (with real filenames):

FILE: index.html
<code>
<!DOCTYPE html>
<html>
...
</code>

SHELL:
<code>
echo 'hello'
</code>

MESSAGE:
Informational message here

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
                st.session_state["files"][name] = content
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
        st.session_state["generated"] = list(generated_files.keys())

# === Main UI ===
if "files" not in st.session_state:
    st.session_state["files"] = {}
if "generated" not in st.session_state:
    st.session_state["generated"] = []

prompt = st.text_area("Enter your software project description:", height=150)
if st.button("Run Agent") and prompt.strip():
    agent_loop_ui(prompt)

# === File Explorer & Code Editor ===
if st.session_state["generated"]:
    col1, col2 = st.columns([1, 2])
    with col1:
        selected_file = st.radio("📁 Files", st.session_state["generated"], key="file_selector")

    with col2:
        content = st.session_state["files"].get(selected_file, "")
        language = detect_language_from_extension(selected_file)
        edited_code = st.text_area("✏️ Edit Code", value=content, height=400, key=f"editor_{selected_file}")

        if st.button("💾 Save Changes", key=f"save_{selected_file}"):
            st.session_state["files"][selected_file] = edited_code
            write_file(selected_file, edited_code)
            st.success(f"{selected_file} saved!")

        # Preview
        if language == "html":
            from html import unescape
            st.markdown("### 🔍 Live Preview")
            st.components.v1.html(unescape(edited_code), height=500, scrolling=True)
        elif language == "markdown":
            st.markdown("### 🔍 Live Preview")
            st.markdown(edited_code, unsafe_allow_html=True)

        st.download_button("⬇️ Download File", edited_code, file_name=selected_file)

st.write("Created by [Cup'Code](https://cupcode.fr/) with ❤️")
