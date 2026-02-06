# Autonomous Coding Agent (Tool-Driven Test Repair Loop)


A tool-driven coding agent that reads a local project, diagnoses failing `pytest` tests, writes patches to **application code**, and reruns tests until the suite passes.


It demonstrates a practical autonomous repair loop:


**Read → Plan → Act → Validate → Repair**


---


## What This Agent Does


### Inputs
- A local project directory under `./projects/<project_name>/`
- Each project contains:
  - application code
  - `pytest` tests


### Core Loop
1. Inspect codebase  
   Tools: `ListProjectFiles`, `ReadFile`, `SearchInFile`
2. Implement fixes in application code  
   Tool: `WriteCode`
3. Validate via tests  
   Tool: `RunTests`
4. Iterate until:
   - all tests pass, or
   - iteration / safety limits are reached


### Key Constraints (Important)
- Tests are **readable** and treated as the **specification**
- Tests are **read-only**
  - the agent is blocked from writing under `tests/`
- Fixes must be made in **application code only**


---


## Why This Is Production-Minded (Not Just a Demo)


- **Traceability:** every tool response is tagged (e.g., `[ReadFile]`, `[RunTests]`) so you can follow the agent’s decisions.
- **Strict tool input protocol:** `WriteCode` and `SearchInFile` accept a KV-block format parsed by a dedicated parser (reduces prompt injection / malformed calls).
- **Safety guardrails:**
  - `tests/` enforced read-only at tool level
  - `pytest` executed without `shell=True` to reduce shell-injection risk
  - test execution timeout (`120s`) to prevent hangs
- **Token & UX controls:** file tree listing is directory-first sorted and truncated.
- **State/fixture awareness:** notes in the prompt warn about `pytest` tests importing globals directly; reset logic should mutate in-place instead of rebinding.


---


## Demo


Demo video :


`https://www.loom.com/share/3c9bb906438d465eb932ab45d77bf41b`

---


## Setup


### Install Dependencies
```bash
pip install -r requirements.txt

Required packages include:

python-dotenv

langchain

langchain-openai

pytest

Environment Variables

Create a .env file in the repository root (do not commit it):

OPENAI_API_KEY=YOUR_KEY

The program uses python-dotenv to load environment variables. ChatOpenAI reads OPENAI_API_KEY from the environment automatically.

Add this to .gitignore:

.env
Run

Place projects under:

./projects/<project_name>/

Run:

python Autonomous Coding Agent.py

The agent iterates each project directory, inspects code, writes fixes (excluding tests), and reruns pytest until completion or limits are reached.
