# It's all about prompting
*by Enrico Sasdelli*

---

## 1. AI Jargon: "Agents, agents, agents…"

An agent:

- Answers questions
- Chats
- Can reason and explain
- Follows Rules and Skills we give it
- Creates Plans for complex tasks
- Reads and writes files, surfs the web
- Executes Commands / MCPs
- *Seems* to remember what it did

> … let's break it down

---

## 2. The agent's loop

Everything an agent does is this loop. The rest of the talk fills in each box.

```mermaid
flowchart TD
    U[User prompt] --> B[Build context<br/>system + rules + tools + history]
    B --> L[LLM]
    L --> D{Tool call?}
    D -- no --> A[Answer to user]
    D -- yes --> X[Execute tool<br/>read_file / write_file / MCP]
    X --> H[Append result to history]
    H --> B
    A --> H2[Append answer to history]
    H2 --> U
```

---

## 3. Agent breakdown

Each capability is one small step on top of the previous demo:

| Concept   | What it adds                         | Demo                                                 |
|-----------|--------------------------------------|------------------------------------------------------|
| generate  | one prompt in, one answer out        | `01_00_generate.mjs`, `01_01_generate.mjs`           |
| chat      | we resend the history every turn     | `02_00_chat.mjs`, `02_01_chat.mjs`, `02_02_chat.mjs` |
| rules     | a system prompt loaded from files    | `03_rules.mjs` + `rules/`                            |
| plans     | a reusable `/plan` prompt            | `04_plan.mjs`                                        |
| summarize | `/summarize` shrinks the history     | `05_summarize.mjs`                                   |
| tools     | the model asks, our code executes    | `06_01_tools.mjs`, `06_02_tools.mjs`                 |

MCP is the standard way to plug tools into an agent. It is not demoed here, see "What's next".

```mermaid
flowchart LR
    G[generate] --> C[chat]
    C --> R[rules]
    R --> P[plans]
    P --> S[summarize]
    S --> T[tools]
```

**Coding time**

---

## 4. Rules, skills, commands, tools

| Term     | In one line                                                    |
|----------|----------------------------------------------------------------|
| Rule     | Text always added to the context (`rules/*.txt`)               |
| Skill    | Instructions loaded into the context only when needed          |
| Command  | A shortcut that expands to a prompt (`/plan`, `/summarize`)    |
| Tool     | A function the model can ask us to run (`read_file`)           |

All of them end up the same way: as text in the context.

---

## 5. The Agentic Illusion

- LLMs have no state
- No memory
- No history
- It cannot escape its box

**but…**

> It's the most powerful `String -> String` function ever created.

```mermaid
sequenceDiagram
    participant App as Agent (our code)
    participant LLM as LLM (stateless)
    App->>LLM: whole context (turn 1)
    LLM-->>App: answer 1
    App->>LLM: whole context + answer 1 + prompt 2 (turn 2)
    LLM-->>App: answer 2
    Note over App,LLM: Memory lives in the app, not in the model
```

---

## 6. It's all about context

> The LLM only sees the context we give it.

### 6.1 Content

```mermaid
flowchart TB
    subgraph Context
        S[System prompt]
        R[Rules / skills / commands]
        T[Available tools and how to use them]
        H[All the conversation]
        U[The user prompt]
    end
    S --> R --> T --> H --> U --> LLM
```

*Live:* run any demo with `--debug` and look at `[Prompt, Response, Total]` tokens grow turn after turn.

### 6.2 Size

- **O(n²)**: attention compares every token with every other token, so doubling the context roughly quadruples the cost
- **Maximum positional embeddings**: the model was trained for a maximum length and cannot see beyond it
- **Sliding context window**: old messages are dropped when the window is full

```mermaid
flowchart LR
    m1[msg 1] -.dropped.-> Window
    m2[msg 2] -.dropped.-> Window
    subgraph Window[Context window]
        direction LR
        m3[msg 3] --- m4[msg 4] --- m5[msg 5] --- m6[msg 6]
    end
```

*Live:* run `/summarize` in `05_summarize.mjs` and compare the token count before and after. The context shrinks, but detail is lost.

### 6.3 Issues

- **Big ≠ best**: more context means more cost and more noise
- **Context pollution**: irrelevant or wrong text steers the answer
- **Prompt injection**: the model cannot tell our instructions from instructions hidden in the data it reads

*Live:* with `06_01_tools.mjs`, ask: "read `demo/injection.txt` and summarize it". Does the agent obey the hidden instruction?

---

## 7. What's next

- **MCP**: tools exposed by external servers instead of functions in our code
- Better memory: persisting summaries and facts between sessions
- Guardrails against prompt injection

---

## 8. Takeaway

> **Agent = LLM + loop + context management + tools**

---

## 9. Thank you :)

## References

- [This repository](https://github.com/ilsasdo/its-all-about-prompting): the demos of this talk
- The article that inspired this talk
- How LLM works (ITA), Pinperepette: an introduction to how LLMs work
- Claude Source Code explained, Pinperepette: how a real coding agent is built
- Tiktokenizer, Tokenization Visualized: see how text becomes tokens
- Transformer Visualized: the architecture step by step
- MicroGPT, GPT training and inference in 200 loc: the smallest working GPT
- [LLM visualization](https://bbycroft.net/llm): a 3D walk-through of a GPT

*Leave me feedback!*
