# MiMo Learning Agent: A Multi-Agent Collaborative Programming Tutoring System

## Abstract

Current large language models (LLMs) exhibit a critical limitation in educational contexts: they tend to provide direct solutions rather than fostering independent problem-solving skills. This project presents a multi-agent collaborative programming tutoring system built upon Xiaomi MiMo-V2.5-Pro, incorporating Plan Mode, Permission Control, Hook Mechanisms, and Conversation Recovery inspired by the Claude Code engineering architecture. The system employs Socratic questioning to guide students through structured reasoning processes rather than delivering immediate answers.

## 1. Problem Statement

### 1.1 Educational Gap in LLM-Assisted Learning

Empirical observations indicate that students interacting with conventional LLMs for programming assistance frequently engage in copy-paste behaviors without comprehending underlying algorithmic principles. This phenomenon stems from the models' inherent optimization for direct answer generation, which contradicts pedagogical objectives centered on cognitive skill development.

### 1.2 Research Objectives

This project aims to:
- Design an agent architecture that enforces guided discovery over direct solution provision
- Implement dynamic difficulty adjustment based on real-time student comprehension assessment
- Develop conversation state management capable of maintaining pedagogical context across extended interactions
- Evaluate the efficacy of structured planning (Plan Mode) in programming problem decomposition

## 2. System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Interaction Layer (CLI / GUI / Web)        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              Conversation Manager (Orchestration)             │
│         Message Routing · Context Maintenance · Persistence   │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
    ┌─────────────────┐ ┌──────────────┐ ┌─────────────────┐
    │  Exam Analyzer  │ │    Guide     │ │    Adaptive     │
    │     Agent       │ │    Agent     │ │     Agent       │
    └─────────────────┘ └──────────────┘ └─────────────────┘
              │               │               │
              └───────────────┼───────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              MiMo API Client (MiMoClient)                     │
│         Unified API Interface · Retry Logic · Token Tracking  │
└─────────────────────────────────────────────────────────────┘
```

### Agent Specifications

| Agent | Function | Core Capabilities |
|-------|----------|-------------------|
| **Exam Analyzer** | Problem decomposition and knowledge point extraction | Intent recognition, knowledge graph mapping |
| **Socratic Guide** | Step-by-step reasoning guidance through questioning | Long-chain reasoning, few-shot prompting |
| **Adaptive Tutor** | Response evaluation and strategy adjustment | Contextual understanding, personalized adaptation |

## 3. Advanced Mechanisms

### 3.1 Plan Mode
Generates structured solution plans prior to execution. Students can confirm, modify, or bypass the proposed plan.

### 3.2 Permission System
Fine-grained permission framework constrains agent behavior: complete code and direct answers are forbidden; guiding questions and concept explanations are allowed. Permissions dynamically adjust based on comprehension level.

### 3.3 Hook Mechanism
Custom logic injection at critical execution points: pre-process (intent classification), post-agent (content filtering), pre-response (difficulty adjustment), post-response (learning tracking).

### 3.4 Conversation Recovery
Persistent conversation state management with automatic snapshots, compression support, and multiple context compression strategies (sliding window, summarization, key turn retention).

### 3.5 Tool Use Framework
Agents register as callable tools with defined input/output schemas, enabling parallel execution and standardized interaction patterns.

### 3.6 Comprehension State Machine
Student understanding modeled as a finite state machine with levels 0-10, triggering permission recalibration and hint level adjustment at each transition.

## 4. Implementation

```
mimo-learning-agent/
├── agents/              # Agent implementations
├── core/                # Core infrastructure (API client, conversation, state)
├── planning/            # Plan Mode implementation
├── permissions/         # Permission framework
├── hooks/               # Hook mechanism
├── recovery/            # Conversation recovery
├── tools/               # Tool schema definitions
├── utils/               # Configuration and logging
├── gui.py               # Desktop GUI client (tkinter)
├── main.py              # CLI entry point
└── build.py             # Build script for exe packaging
```

## 5. Quick Start

```bash
git clone https://github.com/shiguangyilunhui/mimo-learning-agent.git
cd mimo-learning-agent
pip install -r requirements.txt

# CLI mode
python main.py

# GUI mode
python gui.py

# Build exe
python build.py
```

## License

MIT
