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

Create a .env file:

OPENAI_API_KEY=YOUR_KEY

The program uses python-dotenv to load environment variables. ChatOpenAI reads OPENAI_API_KEY from the environment automatically.

Place projects under:

./projects/<project_name>/

Run:

python Autonomous Coding Agent.py

The agent iterates each project directory, inspects code, writes fixes (excluding tests), and reruns pytest until completion or limits are reached.


