# The project

These are my follow-up code and notes for Stanfords CS146S materials ([link here](https://themodernsoftware.dev/))

agent.py is 90-99% based on CS146S video How to code Claude Code in ~200 lines of code by The Modern Software Developer, here: https://youtu.be/s7ZzkdvCMDY

I just changed the model to a small local one, added a small harness thingy for my own sanity (only files in the follow-up folders can be touched by the agent), and a few tests

## Requirements
- Ollama
  - https://ollama.com/
- qwen3:8b for Ollama
  - https://ollama.com/library/qwen3:8b
- uv
  - https://docs.astral.sh/uv/

## Nice to have, but not required
- Task
  - https://taskfile.dev/


## Running
First, download qwen3:8b
```
ollama pull qwen3:8b
```

Then
```
uv sync

task run

# or

uv run agent.py

```


## Example
````
You::what's in test-files/test.py
D:\t\agents\CS146S The Modern Software Developer\omat\test-files\test.py
name: read_file {'filename': 'test-files/test.py'}
RESULT: {'file_path': 'D:\\t\\agents\\CS146S The Modern Software Developer\\notes_and_code\\test-files\\test.py', 'content': "from ollama import chat\nfrom ollama import ChatResponse\n\nresponse: ChatResponse = chat(\n  model='qwen3:8b',\n  messages=[\n    {\n      'role': 'user',\n      'content': 'Why is the sky blue?',\n    },\n  ],\n)\nprint(response['message']['content'])\n# or access fields directly from the response object\nprint(response.message.content)\n\n"}
Assistant:: The content of `test-files/test.py` is:

```python
from ollama import chat
from ollama import ChatResponse

response: ChatResponse = chat(
  model='qwen3:8b',
  messages=[
    {
      'role': 'user',
      'content': 'Why is the sky blue?',
    },
  ],
)
print(response['message']['content'])
# or access fields directly from the response object
print(response.message.content)
```

````



