import inspect
import json
import os

from dotenv import load_dotenv
from pathlib import Path
from typing import Any, Dict, List, Tuple

from ollama import chat
from ollama import ChatResponse

# https://youtu.be/s7ZzkdvCMDY -- How to code Claude Code in ~200 lines of code -- The Modern Software Developer

# 
# ollama run qwen3:8b
# ollama serve
# ollama stop qwen3:8b
#
# uv run .\coding_agent_from_scratch_lecture__qwen.py
# 

load_dotenv()

SYSTEM_PROMPT = """
You are a coding assistant whose goal it is to help us solve coding tasks. 
You have access to a series of tools you can execute. Here are the tools you can execute:

{tool_list_repr}

When you want to use a tool, reply with exactly one line in the format: 'tool: TOOL_NAME({{JSON_ARGS}})' and nothing else.
Use compact single-line JSON with double quotes. After receiving a tool_result(...) message, continue the task.
If no tool is needed, respond normally.

Example: tool: read_file({{"filename": "readme.md"}})

"""


YOU_COLOR = "\u001b[94m"
ASSISTANT_COLOR = "\u001b[93m"
RESET_COLOR = "\u001b[0m"

ROOT = Path.cwd().resolve()

def resolve_abs_path(path_str: str) -> Path:
    """
    file.py -> /Users/home/mihail/modern-software-dev-lectures/file.py
    """
    path = Path(path_str).expanduser()
    if not path.is_absolute():
        path = (Path.cwd() / path).resolve()
    return path

def read_file_tool(filename: str) -> Dict[str, Any]:
    """
    Gets the full content of a file provided by the user.
    :param filename: The name of the file to read.
    :return: The full content of the file.
    """
    full_path = resolve_abs_path(filename)
    print(full_path)
    with open(str(full_path), "r") as f:
        content = f.read()
    return {
        "file_path": str(full_path),
        "content": content
    }

def edit_file_tool(path: str, old_str: str, new_str: str) -> Dict[str, Any]:
    """
    Replaces first occurrence of old_str with new_str in file. If old_str is empty,
    create/overwrite file with new_str.
    :param path: The path to the file to edit.
    :param old_str: The string to replace.
    :param new_str: The string to replace with.
    :return: A dictionary with the path to the file and the action taken.
    """
    full_path = resolve_abs_path(path)
    if old_str == "":
        full_path.write_text(new_str, encoding="utf-8")
        return {
            "path": str(full_path),
            "action": "created_file"
        }
    original = full_path.read_text(encoding="utf-8")
    if original.find(old_str) == -1:
        return {
            "path": str(full_path),
            "action": "old_str not found"
        }
    edited = original.replace(old_str, new_str, 1)
    full_path.write_text(edited, encoding="utf-8")
    return {
        "path": str(full_path),
        "action": "edited"
    }

def file_exists_in_dir(path: str) -> bool:
    """
    Checks if the path exists in current directory or children
    :param path: the path to the file
    :return: is path in current_path
    """

    return check_path(path, os.getcwd())

def check_path(path: str, current_path: str) -> bool:
    """
    Checks if the path exists in current directory or children
    :param path: the path to the file
    :param current_path: the path to compare against
    :return: is path in current_path
    """

    resolved = (ROOT / path).resolve()
    if not resolved.is_relative_to(ROOT):
        return False

    return True

def list_files_tool(path: str) -> Dict[str, Any]:
    """
    Lists the files in a directory provided by the user.
    :param path: The path to a directory to list files from.
    :return: A list of files in the directory.
    """
    full_path = resolve_abs_path(path)
    all_files = []
    for item in full_path.iterdir():
        all_files.append({
            "filename": item.name,
            "type": "file" if item.is_file() else "dir"
        })
    return {
        "path": str(full_path),
        "files": all_files
    } 

TOOL_REGISTRY = {
    "read_file": read_file_tool,
    "list_files": list_files_tool,
    "edit_file": edit_file_tool 
}

def get_tool_str_representation(tool_name: str) -> str:
    tool = TOOL_REGISTRY[tool_name]
    return f"""
    Name: {tool_name}
    Description: {tool.__doc__}
    Signature: {inspect.signature(tool)}
    """

def get_full_system_prompt():
    tool_str_repr = ""
    for tool_name in TOOL_REGISTRY:
        tool_str_repr += "TOOL\n===" + get_tool_str_representation(tool_name)
        tool_str_repr += f"\n{"="*15}\n"
    return SYSTEM_PROMPT.format(tool_list_repr=tool_str_repr)

def extract_tool_invocations(text: str) -> List[Tuple[str, Dict[str, Any]]]:
    """
    Return list of (tool_name, args) requested in 'tool: name({...})' lines.
    The parser expects single-line, compact JSON in parentheses.
    """
    invocations = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line.startswith("tool:"):
            continue
        try:
            after = line[len("tool:"):].strip()
            name, rest = after.split("(", 1)
            name = name.strip()
            if not rest.endswith(")"):
                continue
            json_str = rest[:-1].strip()
            args = json.loads(json_str)
            invocations.append((name, args))
        except Exception:
            continue
    return invocations

def execute_llm_call(conversation: List[Dict[str, str]]) -> str:
    response: ChatResponse = chat(
        model='qwen3:8b',
        messages=conversation,
        think=False,                    # skip the reasoning tokens
        options={'num_ctx': 8192},      # default 4096 is tight with tool schemas
    )
    return response.message.content


def run_coding_agent_loop():
    print(get_full_system_prompt())
    conversation = [{"role": "system", "content": get_full_system_prompt()}]
    while True:
        try:
            user_input = input(f"{YOU_COLOR}You:{RESET_COLOR}:")
        except (KeyboardInterrupt, EOFError):
            break
        conversation.append({"role": "user", "content": user_input.strip()})
        while True:
            assistant_response = execute_llm_call(conversation)
            conversation.append({"role": "assistant", "content": assistant_response})
            tool_invocations = extract_tool_invocations(assistant_response)
            if not tool_invocations:
                print(f"{ASSISTANT_COLOR}Assistant:{RESET_COLOR}: {assistant_response}")
                break
            for name, args in tool_invocations:
                tool = TOOL_REGISTRY.get(name)
                if tool is None:
                    resp = {"error": f"unknown tool {name}"}
                else:
                    if not isinstance(args, dict):
                        resp = {"error": f"args must be a JSON object like {{\"filename\": \"x.py\"}}, got {type(args).__name__}"}
                    else:
                        try:
                            resp = tool(**args)
                        except TypeError as e:
                            resp = {"error": f"bad arguments: {e}. Expected signature: {inspect.signature(tool)}"}
                        except Exception as e:
                            resp = {"error": str(e)}

                print("name: " + name, args)
                print("RESULT:", resp)
                conversation.append({
                    "role": "user",
                    "content": f"tool_result({json.dumps(resp)})"
                })
                
if __name__ == "__main__":
    run_coding_agent_loop()