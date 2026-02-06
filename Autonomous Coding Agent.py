import logging
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List, Dict

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.agents import initialize_agent, Tool

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("coding_agent")


def _tag(tool: str, msg: str) -> str:
    """Prefix all tool outputs with tool name for easy debugging."""
    return f"[{tool}] {msg}"


def _parse_kv_block(text: str) -> Dict[str, Optional[str]]:
    """
    Strictly parse the tool input protocol:

    WriteCode/SearchInFile protocol:
      file_path: <path>
      keyword: <keyword>      (optional; used by SearchInFile)
      code:
      <multiline code...>     (used by WriteCode)
    """
    text = (text or "").replace("\r\n", "\n").replace("\r", "\n")

    fp_match = re.search(r"(?im)^\s*file_path\s*:\s*(.+?)\s*$", text)
    file_path = fp_match.group(1).strip() if fp_match else None

    kw_match = re.search(r"(?im)^\s*keyword\s*:\s*(.*?)\s*$", text)
    keyword = kw_match.group(1).strip() if kw_match else None

    code_match = re.search(r"(?ims)^\s*code\s*:\s*$\n(?P<code>.*)\Z", text)
    code = code_match.group("code") if code_match else None

    return {"file_path": file_path, "keyword": keyword, "code": code}


def _safe_relpath(p: Path, base: Path) -> str:
    try:
        return str(p.relative_to(base))
    except Exception:
        return str(p)


def _is_tests_path(path_like: str) -> bool:
    """
    Policy:
    - tests/ directory is READABLE (we allow the agent to read it)
    - tests/ directory is NOT WRITABLE (agent must never modify it)
    """
    p = Path(path_like)
    parts_lower = [x.lower() for x in p.parts]
    norm = p.as_posix().lower()

    if "tests" in parts_lower:
        return True
    if "/tests/" in norm or norm.startswith("tests/") or norm.endswith("/tests"):
        return True
    return False


def read_file(file_path: str) -> str:
    """
    Read content of a file.

    Accepts either:
      - a raw path string:  projects\\x\\y.py
      - or a KV block:      file_path: projects\\x\\y.py
    """
    tool = "ReadFile"
    try:
        # Compat: if model mistakenly sends KV format, extract file_path
        if isinstance(file_path, str):
            m = re.search(r"(?im)^\s*file_path\s*:\s*(.+?)\s*$", file_path.strip())
            if m:
                file_path = m.group(1).strip()

        path = Path(file_path)
        if not path.exists():
            return _tag(tool, f"File not found: {file_path}")
        if path.is_dir():
            return _tag(tool, f"Error: {file_path} is a directory, not a file.")
        return _tag(tool, path.read_text(encoding="utf-8", errors="replace"))
    except Exception as e:
        return _tag(tool, f"Error reading file: {e}")


def search_in_file(command: str) -> str:
    """
    Input format:
      file_path: xxx
      keyword: yyy

    Tests are readable.
    """
    tool = "SearchInFile"
    try:
        parsed = _parse_kv_block(command)
        file_path = parsed["file_path"]
        keyword = parsed["keyword"]

        if not file_path:
            return _tag(tool, "Error: Missing 'file_path: ...'")
        if keyword is None or keyword == "":
            return _tag(tool, "Error: Missing 'keyword: ...'")

        path = Path(file_path)
        if not path.exists():
            return _tag(tool, f"File not found: {file_path}")
        if path.is_dir():
            return _tag(tool, f"Error: {file_path} is a directory, not a file.")

        results: List[str] = []
        for i, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
            if keyword in line:
                results.append(f"{i}: {line}")

        return _tag(tool, "\n".join(results) if results else "No matches found.")
    except Exception as e:
        return _tag(tool, f"Error searching file: {e}")


def write_code(command: str) -> str:
    """
    Input format:
      file_path: xxx
      code:
      <full code>

    Policy:
      - tests/ is READ-ONLY (writing forbidden)
    """
    tool = "WriteCode"
    try:
        parsed = _parse_kv_block(command)
        file_path = parsed["file_path"]
        code = parsed["code"]

        if not file_path:
            return _tag(tool, "Error: Missing 'file_path: ...'")
        if code is None:
            return _tag(tool, "Error: Missing 'code:' block.")

        if _is_tests_path(file_path):
            return _tag(tool, "Error: Modifying anything under tests/ is forbidden. Read-only access is allowed; fix application code instead.")

        code = code.split("#FINISH")[0].rstrip() + "\n"

        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(code, encoding="utf-8")

        return _tag(tool, f"[WRITE_CODE_DONE]✅ Code written to {file_path} ({len(code.splitlines())} lines)")
    except Exception as e:
        return _tag(tool, f"Error writing code: {e}")


def run_tests(project_dir: str) -> str:
    tool = "RunTests"
    try:
        project_dir = (project_dir or "").strip().strip('"').strip("'")
        project_path = Path(project_dir)

        if not project_path.exists():
            return _tag(tool, f"Error: project_dir not found: {project_dir}")
        if not project_path.is_dir():
            return _tag(tool, f"Error: project_dir is not a directory: {project_dir}")

        cmd = ["python", "-m", "pytest", "--junitxml=unit.xml"]
        result = subprocess.run(
            cmd,
            cwd=str(project_path),
            text=True,
            capture_output=True,
            timeout=120,
        )
        output = (
            f"EXIT_CODE: {result.returncode}\n\n"
            f"STDOUT:\n{result.stdout}\n\n"
            f"STDERR:\n{result.stderr}"
        )
        return _tag(tool, output.strip())
    except subprocess.TimeoutExpired:
        return _tag(tool, "Error running tests: TimeoutExpired (pytest exceeded 120s)")
    except Exception as e:
        return _tag(tool, f"Error running tests: {e}")


def list_project_files(project_dir: str) -> str:
    """List project file structure (sorted, directory-first). (tests are visible/readable)"""
    tool = "ListProjectFiles"
    try:
        project_path = Path(project_dir)
        if not project_path.exists():
            return _tag(tool, f"Project directory not found: {project_dir}")

        paths = list(project_path.rglob("*"))
        paths.sort(key=lambda p: (0 if p.is_dir() else 1, _safe_relpath(p, project_path).lower()))

        lines: List[str] = []
        for p in paths:
            rel = _safe_relpath(p, project_path)
            lines.append(f"[DIR] {rel}" if p.is_dir() else rel)

        if len(lines) > 500:
            lines = lines[:500] + [f"... (truncated, total items: {len(paths)})"]

        return _tag(tool, "\n".join(lines))
    except Exception as e:
        return _tag(tool, f"Error listing project files: {e}")


# Agent
@dataclass
class AgentLimits:
    max_iterations: int = 30
    max_execution_time: int = 300  # seconds


class CodingAgent:
    def __init__(
        self,
        model_name: str = "gpt-4.1-mini",
        temperature: float = 0.0,
        limits: AgentLimits = AgentLimits(),
    ):
        logger.info("Initializing CodingAgent | model=%s", model_name)

        self.llm = ChatOpenAI(
            model=model_name,
            temperature=temperature,
            base_url="https://api.chatanywhere.org/v1",
        )

        self.tools = [
            Tool(
                name="ReadFile",
                func=read_file,
                description="Read the content of a given file path. Accepts raw path or 'file_path: ...'. Tests are readable.",
            ),
            Tool(
                name="SearchInFile",
                func=search_in_file,
                description="Search for a keyword in a file. Input format:\nfile_path: xxx\nkeyword: yyy\nTests are readable.",
            ),
            Tool(
                name="WriteCode",
                func=write_code,
                description="Write or overwrite a file. Input format(must include file_path):\nfile_path: xxx\ncode:\n<full code>\n#FINISH\nPolicy: tests/ is read-only.",
            ),
            Tool(
                name="RunTests",
                func=run_tests,
                description="Run pytest inside the given project directory. Action Input MUST be a project directory path string.",
            ),
            Tool(
                name="ListProjectFiles",
                func=list_project_files,
                description="Recursively list the project file structure. Tests are visible/readable.",
            ),
        ]

        self.agent = initialize_agent(
            tools=self.tools,
            llm=self.llm,
            agent="zero-shot-react-description",
            verbose=True,
            max_iterations=limits.max_iterations,
            max_execution_time=limits.max_execution_time,
        )

    def run(self, project_dir: str, task: Optional[str] = None) -> str:
        prompt = f"""
You are a software development AI assistant.
Goal: Implement missing functionality in the project located at {project_dir}.

Constraints:
- You MAY read tests/ to understand expected behavior.
- You MUST NEVER modify tests/ or any file under tests/ (read-only).
- Fix application code only.

Important note:
- Tests might import globals directly (e.g., 'from store import PRODUCTS').
  If so, avoid rebinding those globals in reset_state(); mutate in-place (clear/update) so imported references stay valid.

Steps:
1) Use ReadFile to read project README.
2) Use ListProjectFiles/ReadFile/SearchInFile to understand the codebase (including tests if needed).
3) Use WriteCode to modify or create application files (never tests).
4) Use RunTests to run tests.
5) Iterate until tests pass.
6) Always run RunTests again before declaring completion and before exit.
7) You cannot exit until you pass all the tests.

Rules:
- After every tool call, you MUST wait for Observation before deciding the next step.
- Do not call multiple tools in a row.
"""
        if task:
            prompt += f"\nAdditional task:\n{task}\n"

        return self.agent.run(prompt)


def iter_projects(base_dir: Path) -> List[Path]:
    if not base_dir.exists():
        return []
    return sorted([p for p in base_dir.iterdir() if p.is_dir()], key=lambda p: p.name.lower())


if __name__ == "__main__":
    load_dotenv()
    logger.info("Running CodingAgent across projects under ./projects")

    agent = CodingAgent()
    base_dir = Path("./projects")

    projects = iter_projects(base_dir)
    if not projects:
        logger.warning("No project directories found under %s", base_dir.resolve())
        raise SystemExit(0)

    for project in projects:
        logger.info("Processing project: %s", project.name)
        try:
            result = agent.run(str(project))
            logger.info("DONE: %s\n%s", project.name, result)
        except Exception as e:
            logger.exception("Failed to process %s: %s", project.name, e)