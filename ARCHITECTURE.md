# SilentSpace Guardian — Architecture

A visual guide to how the system transforms meeting JSON into organizational verdicts.
For prose documentation and the scoring formula, see [docs/architecture.md](docs/architecture.md).

---

## 1. High-Level System Overview

Three layers. No network calls. One existential question per meeting.

```mermaid
graph LR
    subgraph Data["Data Layer"]
        M["meetings/*.json\n(12 meeting files)"]
        MEM["memory/\nHistory Scaffolding"]
    end

    subgraph Logic["Scoring & Classification Layer"]
        AMD["audit_meeting_data()\nAgent Interface"]
        CB["entropy_engine\n(COBOL binary)"]
        CL["classify.py\nClassifier"]
        PY["audit_meeting.py\nCLI + orchestration"]
        BATCH["audit_all_meetings.py\nBatch Runner"]
    end

    subgraph Output["Reporting Layer"]
        CON["Console\nSummary"]
        RPT["reports/*.md\nMarkdown Reports"]
    end

    M --> PY
    M --> BATCH
    MEM -.->|"planned"| AMD
    PY --> AMD
    BATCH --> AMD
    AMD <-->|"6 values via stdin\n2 ints via stdout"| CB
    AMD <-->|"score / verdict"| CL
    PY --> CON
    PY --> RPT
    BATCH --> RPT
```

---

## 2. Detailed Data Flow

```mermaid
flowchart TD
    A[/"meetings/weekly_alignment_sync.json"/]:::file --> B["Load JSON\naudit_meeting.py"]

    B --> C["Extract 6 Scoring Parameters\nduration · attendees · agenda\nactions · email · recurrence"]

    C --> D{"COBOL binary\nexists?"}

    D -- No --> E["cobc -x -o entropy_engine\nentropy_engine.cob"]:::compile
    E --> F

    D -- Yes --> F["Pipe to stdin: entropy_engine\n6 values, one per line"]:::cobol

    F --> G["Parse stdout\nLine 1: waste_score\nLine 2: necessity_prob"]

    G --> H["classify_meeting(waste_score)"]:::py
    G --> I["async_recommendation(meeting, waste_score)"]:::py

    H --> J["Build Markdown Report"]
    I --> J

    J --> K[/"reports/weekly_alignment_sync_report.md"/]:::file
    J --> L["Print Console Summary"]

    classDef file fill:#e8f4f8,stroke:#2980b9
    classDef cobol fill:#fef9e7,stroke:#f39c12
    classDef compile fill:#fdf2f8,stroke:#8e44ad
    classDef py fill:#eafaf1,stroke:#27ae60
```

---

## 3. Scoring Pipeline Sequence

```mermaid
sequenceDiagram
    actor User
    participant audit as audit_meeting.py
    participant fs as File System
    participant cobol as entropy_engine (COBOL)
    participant classify as classify.py

    User->>audit: python audit_meeting.py meetings/foo.json

    audit->>fs: binary exists?
    alt Binary missing
        fs-->>audit: not found
        audit->>cobol: cobc -x -o entropy_engine entropy_engine.cob
        cobol-->>audit: compilation success
    else Binary present
        fs-->>audit: path returned
    end

    audit->>fs: open meetings/foo.json
    fs-->>audit: meeting dict

    audit->>cobol: stdin "60\n6\n0\n0\n1\n3\n"
    Note right of cobol: dur=60, att=6, agenda=0,<br/>actions=0, email=1, recur=3 (weekly)
    cobol-->>audit: "092\n008"
    Note left of cobol: waste=92, necessity=8

    audit->>classify: classify_meeting(92)
    classify-->>audit: "Corporate Heat Death Event: Entropy Made Flesh"

    audit->>classify: async_recommendation(meeting, 92)
    classify-->>audit: "Cancel and initiate a post-mortem on how this ended up on six calendars."

    audit->>User: console summary (score · verdict · recommendation)
    audit->>fs: write reports/weekly_alignment_sync_report.md
    fs-->>audit: path confirmed
    audit->>User: "Report saved to: reports/weekly_alignment_sync_report.md"
```

---

## 4. COBOL Scoring Decision Tree

The entropy engine applies five additive penalties to a base score of 20,
then caps the result at 100.

```mermaid
flowchart TD
    Start(["base score = 20"])

    Start --> A{"attendees > 3?"}
    A -- Yes --> A2["+ min(30, (n − 3) × 2)\nAttendee Bloat Penalty"]
    A -- No --> B
    A2 --> B

    B{"duration > 30 min?"} --> |Yes| B2["+ ⌊(dur − 30) / 15⌋ × 3\nDuration Drag Penalty"]
    B --> |No| C
    B2 --> C

    C["+ recurrence_level × 5\n(0=none · 1=monthly · 2=biweekly\n3=weekly · 4=daily)\nRecurrence Tax"] --> D

    D{"has agenda?"} --> |No| D2["+ 15\nAgendaless Chaos Premium"]
    D --> |Yes| E
    D2 --> E

    E{"has action items?"} --> |No| E2["+ 10\nActionless Void Surcharge"]
    E --> |Yes| F
    E2 --> F

    F{"could be email?"} --> |Yes| F2["+ 20\nEmail Crime Penalty"]
    F --> |No| G
    F2 --> G

    G{"score > 100?"} --> |Yes| G2["cap at 100"]
    G --> |No| H
    G2 --> H

    H["necessity_prob = max(5, 100 − waste_score)"]
    H --> End(["Output: waste_score\nnecessity_prob"])
```

---

## 5. Classification Tiers

```mermaid
graph TD
    Score(["waste_score"])

    Score --> T1{"≤ 20?"}
    T1 -- Yes --> C1["Rare Gem\nGenuine Human Interaction\n▶ Schedule another one next quarter."]:::gem
    T1 -- No --> T2{"≤ 40?"}

    T2 -- Yes --> C2["Marginally Justified\nCould Be a Loom\n▶ We appreciate the effort."]:::marginal
    T2 -- No --> T3{"≤ 60?"}

    T3 -- Yes --> C3["Calendar Debris\nOccupies Space, Creates Little\n▶ A real recurring cost."]:::debris
    T3 -- No --> T4{"≤ 80?"}

    T4 -- Yes --> C4["Meeting-Shaped Void\nTime's Natural Enemy\n▶ Cancel with prejudice."]:::void
    T4 -- No --> C5["Corporate Heat Death Event\nEntropy Made Flesh\n▶ This meeting is why people quit."]:::heat

    classDef gem      fill:#d5f5e3,stroke:#1e8449,color:#1e8449
    classDef marginal fill:#fef9e7,stroke:#d4ac0d,color:#7d6608
    classDef debris   fill:#fdebd0,stroke:#d35400,color:#784212
    classDef void     fill:#fadbd8,stroke:#c0392b,color:#7b241c
    classDef heat     fill:#2c3e50,stroke:#1a252f,color:#ecf0f1
```

---

## 6. Module Dependency Map

```mermaid
graph LR
    CLI1["python audit_meeting.py foo.json"]
    CLI2["python audit_all_meetings.py"]
    AGENT["audit_meeting_data()\ncalled by agent"]

    CLI1 --> audit["audit_meeting.py"]
    CLI2 --> batch["audit_all_meetings.py"]
    AGENT --> audit

    batch --> audit

    audit --> json_mod["json\nstdlib"]
    audit --> subprocess["subprocess\nstdlib"]
    audit --> pathlib["pathlib\nstdlib"]
    audit --> re["re\nstdlib"]
    audit --> functools["functools\nstdlib"]
    audit --> classify["classify.py"]
    audit --> cobol_bin["entropy_engine\ncompiled COBOL"]

    classify --> hashlib["hashlib\nstdlib"]

    cobol_bin -.->|"compiled from"| cobol_src["entropy_engine.cob\nGnuCOBOL source"]

    mem["memory/\nsample_meeting_history.json"] -.->|"planned: memory_context"| audit
```

> **Zero third-party dependencies.** The entire Python layer uses only the standard library.
> The COBOL layer requires GnuCOBOL (`cobc`) at compile time only.
