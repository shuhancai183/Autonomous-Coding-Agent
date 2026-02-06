\section*{Autonomous Coding Agent (Tool-Driven Test Repair Loop)}

A tool-driven coding agent that reads a project, diagnoses failing tests, writes patches to application code, and reruns test until the suite passes. It demonstrates a practical autonomous repair loop: Read $\rightarrow$ Plan $\rightarrow$ Act $\rightarrow$ Validate $\rightarrow$ Repair.

\subsection*{What This Agent Does}

\textbf{Inputs}
\begin{itemize}
\item A local project directory under \texttt{./projects/<project\_name>/} containing application code and pytest tests.
\end{itemize}

\textbf{Loop}
\begin{enumerate}
\item Inspect codebase (ListProjectFiles, ReadFile, SearchInFile)
\item Implement fixes (WriteCode)
\item Validate via tests (RunTests)
\item Iterate until tests pass or limits are reached
\end{enumerate}

\textbf{Key Constraints}
\begin{itemize}
\item Tests are \textbf{readable} for spec inference
\item Tests are \textbf{read-only} (agent is blocked from writing under \texttt{tests/})
\item Fixes must be made in application code only
\end{itemize}

\subsection*{Why This Is Production-Minded (Not Just a Demo)}

\begin{itemize}
\item Tool output tagging: every tool response is prefixed (e.g., [ReadFile], [RunTests]) for traceability.
\item Strict tool input protocol: WriteCode and SearchInFile accept a KV-block format parsed by a dedicated parser.
\item Safety guardrails:
\begin{itemize}
\item \texttt{tests/} is enforced read-only at tool level.
\item pytest executed without shell=True to avoid shell injection risk.
\item Test execution timeout (120s) prevents hangs.
\end{itemize}
\item Token and UX controls: file tree listing is directory-first sorted and truncated.
\item State and fixture awareness: prompt warns about pytest tests importing globals directly; reset logic should mutate in-place instead of rebinding.
\end{itemize}

\subsection*{Demo}

Demo video (3--5 minutes recommended):

\texttt{[<YOUR\_LOOM\_LINK\_HERE>](https://www.loom.com/share/3c9bb906438d465eb932ab45d77bf41b)}

Suggested demo flow:
\begin{enumerate}
\item Show repository structure
\item Run the agent on one sample project
\item Highlight tool calls, repair iterations, and final pytest pass
\end{enumerate}

\subsection*{Setup}

\textbf{Install Dependencies}
\begin{verbatim}
pip install -r requirements.txt
\end{verbatim}

Required packages include:
\begin{itemize}
\item python-dotenv
\item langchain
\item langchain-openai
\item pytest
\end{itemize}

\textbf{Environment Variables}

Create a \texttt{.env} file in the repository root (do not commit it):

\begin{verbatim}
OPENAI_API_KEY=YOUR_KEY
\end{verbatim}

The program uses python-dotenv to load environment variables. ChatOpenAI reads OPENAI\_API\_KEY from the environment automatically.

Add to \texttt{.gitignore}:
\begin{verbatim}
.env
\end{verbatim}

\subsection*{Run}

Place projects under:

\begin{verbatim}
./projects/<project_name>/
\end{verbatim}

Run:

\begin{verbatim}
python agent.py
\end{verbatim}

The agent will iterate each project directory, inspect code, write fixes (excluding tests), and rerun pytest until completion or limits are reached.

\subsection*{Tooling Interface}

\textbf{ReadFile}

Reads file content. Accepts raw path or KV format:
\begin{verbatim}
file_path: path/to/file.py
\end{verbatim}

\textbf{SearchInFile}

\begin{verbatim}
file_path: path/to/file.py
keyword: TOKEN
\end{verbatim}

\textbf{WriteCode (Strict Protocol)}

\begin{verbatim}
file_path: path/to/file.py
code:
<full file content>
#FINISH
\end{verbatim}

Notes:
\begin{itemize}
\item Content after \#FINISH is ignored.
\item Any path under tests/ is rejected (read-only).
\end{itemize}

\textbf{RunTests}

Executes:
\begin{verbatim}
python -m pytest --junitxml=unit.xml
\end{verbatim}

Captures stdout and stderr with a 120-second timeout.

\subsection*{Design Notes (Interview Ready)}

\textbf{Why ReAct-style agent?}

This workflow is tool-driven and iterative. The model must reason step-by-step and choose tools based on observations. ReAct matches the inspect--patch--validate loop naturally.

\textbf{Why enforce tests as read-only?}

Tests represent the specification. Preventing test modification ensures the agent cannot ``cheat'' by weakening requirements.