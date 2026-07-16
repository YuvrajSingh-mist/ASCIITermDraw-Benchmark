# TermDraw-Bench: Task Specification

This file records the current benchmark tasks in a detailed review format.
It is meant to make task auditing easy from one place.

If this file and the repo ever disagree, the repo files under `tasks/` and `scripts/benchmark/data/` are authoritative.

## Current Benchmark Rules

- Each category now contains `20` tasks arranged progressively as `10 easy`, `5 medium`, and `5 hard`.
- Task folders are nested by difficulty within each category.
- Every generated `prompt.txt` begins with `Draw an ASCII diagram illustrating ...`.
- Category 3 tasks are editing tasks and include both `source.ascii` and `source.png`.
- Editing prompts explicitly require applying only the requested edits and making no unrelated changes.
- The VLM judge uses one shared reward contract across all tasks.
- Final judge score is `structural_score + semantics_score`.
- Structural judging uses assertion-aligned binary components instead of per-task judge checklists.
- For editing tasks, the judge sees three images in order: source image, reference image, rendered model-output image.
- For tasks with arrows, generated `prompt.txt` files include shared wording for centered/aligned arrows, slightly elevated arrow labels, and components sized clearly enough to support fan-in/fan-out attachment points.

## Difficulty Buckets

- Tasks `.1` to `.10` within a category are the easy bucket.
- Tasks `.11` to `.15` within a category are the medium bucket.
- Tasks `.16` to `.20` within a category are the hard bucket.
- On disk these live under `easy/`, `medium/`, and `hard/` subdirectories inside each category folder.

## Category 1: Box Layout Basics

### Task 1.1
**difficulty:** `easy`

**prompt.txt:** Draw an ASCII diagram illustrating a single ASCII box with the label "API Gateway" centered inside it. Return only the final ASCII diagram in plain text. Do not include markdown fences, explanations, or any extra text.

**assertions.json:**
```json
{
  "required_labels": [
    "API Gateway"
  ],
  "forbidden_labels": [],
  "entity_count": 1,
  "required_edges": [],
  "required_edge_labels": [],
  "preserved_elements": []
}
```

### Task 1.2
**difficulty:** `easy`

**prompt.txt:** Draw an ASCII diagram illustrating three boxes labeled "Input", "Process", "Output" connected left-to-right with arrows. When arrows are required, make them centered and aligned cleanly to their source and target. If an arrow has a label, place the label a little above the arrow rather than inside the arrow line. Any component with incoming or outgoing arrows should be sized wide or tall enough to make those connections visually unambiguous, so it is clear where arrows originate and where they terminate. If one component fans out to multiple arrows, or multiple arrows converge into one component, its width or height should clearly support those attachment points. Return only the final ASCII diagram in plain text. Do not include markdown fences, explanations, or any extra text.

**assertions.json:**
```json
{
  "required_labels": [
    "Input",
    "Process",
    "Output"
  ],
  "forbidden_labels": [],
  "entity_count": 3,
  "required_edges": [
    {
      "from": "Input",
      "to": "Process"
    },
    {
      "from": "Process",
      "to": "Output"
    }
  ],
  "required_edge_labels": [],
  "preserved_elements": []
}
```

### Task 1.3
**difficulty:** `easy`

**prompt.txt:** Draw an ASCII diagram illustrating four boxes stacked vertically: "Load Balancer", "App Server", "Cache", "Database". Connect them top-to-bottom with downward arrows. When arrows are required, make them centered and aligned cleanly to their source and target. If an arrow has a label, place the label a little above the arrow rather than inside the arrow line. Any component with incoming or outgoing arrows should be sized wide or tall enough to make those connections visually unambiguous, so it is clear where arrows originate and where they terminate. If one component fans out to multiple arrows, or multiple arrows converge into one component, its width or height should clearly support those attachment points. Return only the final ASCII diagram in plain text. Do not include markdown fences, explanations, or any extra text.

**assertions.json:**
```json
{
  "required_labels": [
    "Load Balancer",
    "App Server",
    "Cache",
    "Database"
  ],
  "forbidden_labels": [],
  "entity_count": 4,
  "required_edges": [
    {
      "from": "Load Balancer",
      "to": "App Server"
    },
    {
      "from": "App Server",
      "to": "Cache"
    },
    {
      "from": "Cache",
      "to": "Database"
    }
  ],
  "required_edge_labels": [],
  "preserved_elements": []
}
```

### Task 1.4
**difficulty:** `easy`

**prompt.txt:** Draw an ASCII diagram illustrating a two-column layout. Left column: one box labeled "Client". Right column: two stacked boxes labeled "Primary DB" on top and "Replica DB" below. Connect the Client to both DB boxes with arrows pointing right. When arrows are required, make them centered and aligned cleanly to their source and target. If an arrow has a label, place the label a little above the arrow rather than inside the arrow line. Any component with incoming or outgoing arrows should be sized wide or tall enough to make those connections visually unambiguous, so it is clear where arrows originate and where they terminate. If one component fans out to multiple arrows, or multiple arrows converge into one component, its width or height should clearly support those attachment points. Return only the final ASCII diagram in plain text. Do not include markdown fences, explanations, or any extra text.

**assertions.json:**
```json
{
  "required_labels": [
    "Client",
    "Primary DB",
    "Replica DB"
  ],
  "forbidden_labels": [],
  "entity_count": 3,
  "required_edges": [
    {
      "from": "Client",
      "to": "Primary DB"
    },
    {
      "from": "Client",
      "to": "Replica DB"
    }
  ],
  "required_edge_labels": [],
  "preserved_elements": []
}
```

### Task 1.5
**difficulty:** `easy`

**prompt.txt:** Draw an ASCII diagram illustrating two boxes "Service A" and "Service B" side by side with a bidirectional arrow between them showing data flows both ways. When arrows are required, make them centered and aligned cleanly to their source and target. If an arrow has a label, place the label a little above the arrow rather than inside the arrow line. Any component with incoming or outgoing arrows should be sized wide or tall enough to make those connections visually unambiguous, so it is clear where arrows originate and where they terminate. If one component fans out to multiple arrows, or multiple arrows converge into one component, its width or height should clearly support those attachment points. Return only the final ASCII diagram in plain text. Do not include markdown fences, explanations, or any extra text.

**assertions.json:**
```json
{
  "required_labels": [
    "Service A",
    "Service B"
  ],
  "forbidden_labels": [],
  "entity_count": 2,
  "required_edges": [
    {
      "from": "Service A",
      "to": "Service B"
    },
    {
      "from": "Service B",
      "to": "Service A"
    }
  ],
  "required_edge_labels": [],
  "preserved_elements": []
}
```

### Task 1.6
**difficulty:** `easy`

**prompt.txt:** Draw an ASCII diagram illustrating two boxes "Producer" and "Consumer" connected by a centered right-pointing arrow from the middle of the Producer box to the middle of the Consumer box. Place the label "events" a little above the arrow line, not inside it. When arrows are required, make them centered and aligned cleanly to their source and target. If an arrow has a label, place the label a little above the arrow rather than inside the arrow line. Any component with incoming or outgoing arrows should be sized wide or tall enough to make those connections visually unambiguous, so it is clear where arrows originate and where they terminate. If one component fans out to multiple arrows, or multiple arrows converge into one component, its width or height should clearly support those attachment points. Return only the final ASCII diagram in plain text. Do not include markdown fences, explanations, or any extra text.

**assertions.json:**
```json
{
  "required_labels": [
    "Producer",
    "Consumer",
    "events"
  ],
  "forbidden_labels": [],
  "entity_count": 2,
  "required_edges": [
    {
      "from": "Producer",
      "to": "Consumer"
    }
  ],
  "required_edge_labels": [
    "events"
  ],
  "preserved_elements": []
}
```

### Task 1.7
**difficulty:** `easy`

**prompt.txt:** Draw an ASCII diagram illustrating one box "API Server" at the top. Below it, draw three boxes in a row: "Users DB", "Products DB", "Orders DB". Connect the API Server to each of the three boxes with downward arrows. When arrows are required, make them centered and aligned cleanly to their source and target. If an arrow has a label, place the label a little above the arrow rather than inside the arrow line. Any component with incoming or outgoing arrows should be sized wide or tall enough to make those connections visually unambiguous, so it is clear where arrows originate and where they terminate. If one component fans out to multiple arrows, or multiple arrows converge into one component, its width or height should clearly support those attachment points. Return only the final ASCII diagram in plain text. Do not include markdown fences, explanations, or any extra text.

**assertions.json:**
```json
{
  "required_labels": [
    "API Server",
    "Users DB",
    "Products DB",
    "Orders DB"
  ],
  "forbidden_labels": [],
  "entity_count": 4,
  "required_edges": [
    {
      "from": "API Server",
      "to": "Users DB"
    },
    {
      "from": "API Server",
      "to": "Products DB"
    },
    {
      "from": "API Server",
      "to": "Orders DB"
    }
  ],
  "required_edge_labels": [],
  "preserved_elements": []
}
```

### Task 1.8
**difficulty:** `easy`

**prompt.txt:** Draw an ASCII diagram illustrating three boxes in a row at the top: "Web", "Mobile", "CLI". Below them, draw one box "GraphQL Gateway". Connect each of the three top boxes to the Gateway with downward arrows. When arrows are required, make them centered and aligned cleanly to their source and target. If an arrow has a label, place the label a little above the arrow rather than inside the arrow line. Any component with incoming or outgoing arrows should be sized wide or tall enough to make those connections visually unambiguous, so it is clear where arrows originate and where they terminate. If one component fans out to multiple arrows, or multiple arrows converge into one component, its width or height should clearly support those attachment points. Return only the final ASCII diagram in plain text. Do not include markdown fences, explanations, or any extra text.

**assertions.json:**
```json
{
  "required_labels": [
    "Web",
    "Mobile",
    "CLI",
    "GraphQL Gateway"
  ],
  "forbidden_labels": [],
  "entity_count": 4,
  "required_edges": [
    {
      "from": "Web",
      "to": "GraphQL Gateway"
    },
    {
      "from": "Mobile",
      "to": "GraphQL Gateway"
    },
    {
      "from": "CLI",
      "to": "GraphQL Gateway"
    }
  ],
  "required_edge_labels": [],
  "preserved_elements": []
}
```

### Task 1.9
**difficulty:** `easy`

**prompt.txt:** Draw an ASCII diagram illustrating an ASCII box representing a database table called "users". Use a horizontal divider line inside the box to separate the table name (top section) from three fields listed below it: "id (PK)", "email", "created_at". Return only the final ASCII diagram in plain text. Do not include markdown fences, explanations, or any extra text.

**assertions.json:**
```json
{
  "required_labels": [
    "users",
    "id (PK)",
    "email",
    "created_at"
  ],
  "forbidden_labels": [],
  "entity_count": 1,
  "required_edges": [],
  "required_edge_labels": [],
  "preserved_elements": []
}
```

### Task 1.10
**difficulty:** `easy`

**prompt.txt:** Draw an ASCII diagram illustrating a clean flowchart decision diamond labeled "Is auth?" with firm, symmetric edges using / and \ characters. Add a "Yes" exit path going right to a box labeled "Dashboard", with the "Yes" label a little above the arrow. Add a "No" exit path going down to a box labeled "Login Page". Return only the final ASCII diagram in plain text. Do not include markdown fences, explanations, or any extra text.

**assertions.json:**
```json
{
  "required_labels": [
    "Is auth?",
    "Yes",
    "No",
    "Dashboard",
    "Login Page"
  ],
  "forbidden_labels": [],
  "entity_count": 3,
  "required_edges": [],
  "required_edge_labels": [],
  "preserved_elements": []
}
```

### Task 1.11
**difficulty:** `medium`

**prompt.txt:** Draw an ASCII diagram illustrating a single ASCII box labeled "Config" containing two lines of content: "host: localhost" on the first line and "port: 8080" on the second line. Return only the final ASCII diagram in plain text. Do not include markdown fences, explanations, or any extra text.

**assertions.json:**
```json
{
  "required_labels": [
    "Config",
    "host: localhost",
    "port: 8080"
  ],
  "forbidden_labels": [],
  "entity_count": 1,
  "required_edges": [],
  "required_edge_labels": [],
  "preserved_elements": []
}
```

### Task 1.12
**difficulty:** `medium`

**prompt.txt:** Draw an ASCII diagram illustrating three boxes in an L-shape: "Node A" on the top-left, "Node B" to the right of Node A, and "Node C" below Node B. Connect A to B with a right arrow, and B to C with a downward arrow. When arrows are required, make them centered and aligned cleanly to their source and target. If an arrow has a label, place the label a little above the arrow rather than inside the arrow line. Any component with incoming or outgoing arrows should be sized wide or tall enough to make those connections visually unambiguous, so it is clear where arrows originate and where they terminate. If one component fans out to multiple arrows, or multiple arrows converge into one component, its width or height should clearly support those attachment points. Return only the final ASCII diagram in plain text. Do not include markdown fences, explanations, or any extra text.

**assertions.json:**
```json
{
  "required_labels": [
    "Node A",
    "Node B",
    "Node C"
  ],
  "forbidden_labels": [],
  "entity_count": 3,
  "required_edges": [
    {
      "from": "Node A",
      "to": "Node B"
    },
    {
      "from": "Node B",
      "to": "Node C"
    }
  ],
  "required_edge_labels": [],
  "preserved_elements": []
}
```

### Task 1.13
**difficulty:** `medium`

**prompt.txt:** Draw an ASCII diagram illustrating a fan-in layout. At the top, place three boxes in a row labeled "Worker A", "Worker B", and "Worker C". Below them, place one box labeled "Leader". Connect all three top boxes downward into the single Leader box with aligned arrows. When arrows are required, make them centered and aligned cleanly to their source and target. If an arrow has a label, place the label a little above the arrow rather than inside the arrow line. Any component with incoming or outgoing arrows should be sized wide or tall enough to make those connections visually unambiguous, so it is clear where arrows originate and where they terminate. If one component fans out to multiple arrows, or multiple arrows converge into one component, its width or height should clearly support those attachment points. Return only the final ASCII diagram in plain text. Do not include markdown fences, explanations, or any extra text.

**assertions.json:**
```json
{
  "required_labels": [
    "Worker A",
    "Worker B",
    "Worker C",
    "Leader"
  ],
  "forbidden_labels": [],
  "entity_count": 4,
  "required_edges": [
    {
      "from": "Worker A",
      "to": "Leader"
    },
    {
      "from": "Worker B",
      "to": "Leader"
    },
    {
      "from": "Worker C",
      "to": "Leader"
    }
  ],
  "required_edge_labels": [],
  "preserved_elements": []
}
```

### Task 1.14
**difficulty:** `medium`

**prompt.txt:** Draw an ASCII diagram illustrating two boxes "Client" and "Server" side by side. Between them show two arrows: one going right labeled "request" and one going left labeled "response". When arrows are required, make them centered and aligned cleanly to their source and target. If an arrow has a label, place the label a little above the arrow rather than inside the arrow line. Any component with incoming or outgoing arrows should be sized wide or tall enough to make those connections visually unambiguous, so it is clear where arrows originate and where they terminate. If one component fans out to multiple arrows, or multiple arrows converge into one component, its width or height should clearly support those attachment points. Return only the final ASCII diagram in plain text. Do not include markdown fences, explanations, or any extra text.

**assertions.json:**
```json
{
  "required_labels": [
    "Client",
    "Server",
    "request",
    "response"
  ],
  "forbidden_labels": [],
  "entity_count": 2,
  "required_edges": [
    {
      "from": "Client",
      "to": "Server"
    },
    {
      "from": "Server",
      "to": "Client"
    }
  ],
  "required_edge_labels": [
    "request",
    "response"
  ],
  "preserved_elements": []
}
```

### Task 1.15
**difficulty:** `medium`

**prompt.txt:** Draw an ASCII diagram illustrating a circle node labeled "Start" using ( ) notation, connected with a right arrow to a rectangular box labeled "Process". When arrows are required, make them centered and aligned cleanly to their source and target. If an arrow has a label, place the label a little above the arrow rather than inside the arrow line. Any component with incoming or outgoing arrows should be sized wide or tall enough to make those connections visually unambiguous, so it is clear where arrows originate and where they terminate. If one component fans out to multiple arrows, or multiple arrows converge into one component, its width or height should clearly support those attachment points. Return only the final ASCII diagram in plain text. Do not include markdown fences, explanations, or any extra text.

**assertions.json:**
```json
{
  "required_labels": [
    "Start",
    "Process"
  ],
  "forbidden_labels": [],
  "entity_count": 2,
  "required_edges": [
    {
      "from": "Start",
      "to": "Process"
    }
  ],
  "required_edge_labels": [],
  "preserved_elements": []
}
```

### Task 1.16
**difficulty:** `hard`

**prompt.txt:** Draw an ASCII diagram illustrating one outer ASCII box labeled "Pod". Inside it, place two inner boxes side by side labeled "App Container" and "Log Sidecar". Center the text "shared volume" below the two inner boxes but still inside the Pod box. Return only the final ASCII diagram in plain text. Do not include markdown fences, explanations, or any extra text.

**assertions.json:**
```json
{
  "required_labels": [
    "Pod",
    "App Container",
    "Log Sidecar",
    "shared volume"
  ],
  "forbidden_labels": [],
  "entity_count": 3,
  "required_edges": [],
  "required_edge_labels": [],
  "preserved_elements": []
}
```

### Task 1.17
**difficulty:** `hard`

**prompt.txt:** Draw an ASCII diagram illustrating a two-column service card. Left column has two stacked boxes: "Frontend" above "BFF". Right column has one outer box labeled "Backend Cluster" containing two stacked inner boxes: "API-1" and "API-2". Connect Frontend downward to BFF. From BFF, draw two separate right-pointing arrows that align cleanly to the API-1 and API-2 boxes. When arrows are required, make them centered and aligned cleanly to their source and target. If an arrow has a label, place the label a little above the arrow rather than inside the arrow line. Any component with incoming or outgoing arrows should be sized wide or tall enough to make those connections visually unambiguous, so it is clear where arrows originate and where they terminate. If one component fans out to multiple arrows, or multiple arrows converge into one component, its width or height should clearly support those attachment points. Return only the final ASCII diagram in plain text. Do not include markdown fences, explanations, or any extra text.

**assertions.json:**
```json
{
  "required_labels": [
    "Frontend",
    "BFF",
    "Backend Cluster",
    "API-1",
    "API-2"
  ],
  "forbidden_labels": [],
  "entity_count": 5,
  "required_edges": [
    {
      "from": "Frontend",
      "to": "BFF"
    },
    {
      "from": "BFF",
      "to": "API-1"
    },
    {
      "from": "BFF",
      "to": "API-2"
    }
  ],
  "required_edge_labels": [],
  "preserved_elements": []
}
```

### Task 1.18
**difficulty:** `hard`

**prompt.txt:** Draw an ASCII diagram illustrating a two-lane sequence diagram. Left lane labeled "Client", right lane labeled "Server". Put a "( Start )" node at the top of the Client lane. Show three messages from top to bottom: "connect" from Client to Server, "ack" from Server to Client, and "payload" from Client to Server. Place each message label a little above its arrow, not inside the arrow line. When arrows are required, make them centered and aligned cleanly to their source and target. If an arrow has a label, place the label a little above the arrow rather than inside the arrow line. Any component with incoming or outgoing arrows should be sized wide or tall enough to make those connections visually unambiguous, so it is clear where arrows originate and where they terminate. If one component fans out to multiple arrows, or multiple arrows converge into one component, its width or height should clearly support those attachment points. Return only the final ASCII diagram in plain text. Do not include markdown fences, explanations, or any extra text.

**assertions.json:**
```json
{
  "required_labels": [
    "Start",
    "Client",
    "Server",
    "connect",
    "ack",
    "payload"
  ],
  "forbidden_labels": [],
  "entity_count": 3,
  "required_edges": [
    {
      "from": "Client",
      "to": "Server"
    },
    {
      "from": "Server",
      "to": "Client"
    }
  ],
  "required_edge_labels": [
    "connect",
    "ack",
    "payload"
  ],
  "preserved_elements": []
}
```

### Task 1.19
**difficulty:** `hard`

**prompt.txt:** Draw an ASCII diagram illustrating a table-style box for "users table" with a title row, a divider, and four rows: "id (PK)", "org_id", "email", and "created_at". To the right of it place a separate note box labeled "index: email". Return only the final ASCII diagram in plain text. Do not include markdown fences, explanations, or any extra text.

**assertions.json:**
```json
{
  "required_labels": [
    "users table",
    "id (PK)",
    "org_id",
    "email",
    "created_at",
    "index: email"
  ],
  "forbidden_labels": [],
  "entity_count": 2,
  "required_edges": [],
  "required_edge_labels": [],
  "preserved_elements": []
}
```

### Task 1.20
**difficulty:** `hard`

**prompt.txt:** Draw an ASCII diagram illustrating a mini deployment map. One top box labeled "Router". Below it, draw two outer boxes side by side: "AZ-A" and "AZ-B". Inside "AZ-A" place one box labeled "App-A". Inside "AZ-B" place one box labeled "App-B". Connect Router to both inner app boxes while keeping each app inside its availability zone boundary. When arrows are required, make them centered and aligned cleanly to their source and target. If an arrow has a label, place the label a little above the arrow rather than inside the arrow line. Any component with incoming or outgoing arrows should be sized wide or tall enough to make those connections visually unambiguous, so it is clear where arrows originate and where they terminate. If one component fans out to multiple arrows, or multiple arrows converge into one component, its width or height should clearly support those attachment points. Return only the final ASCII diagram in plain text. Do not include markdown fences, explanations, or any extra text.

**assertions.json:**
```json
{
  "required_labels": [
    "Router",
    "AZ-A",
    "AZ-B",
    "App-A",
    "App-B"
  ],
  "forbidden_labels": [],
  "entity_count": 5,
  "required_edges": [
    {
      "from": "Router",
      "to": "App-A"
    },
    {
      "from": "Router",
      "to": "App-B"
    }
  ],
  "required_edge_labels": [],
  "preserved_elements": []
}
```

## Category 2: Network Topology Diagrams

### Task 2.1
**difficulty:** `easy`

**prompt.txt:** Draw an ASCII diagram illustrating a basic bus topology. Show four nodes labeled "Node-1", "Node-2", "Node-3", and "Node-4" attached to one shared horizontal backbone labeled "Bus". Return only the final ASCII diagram in plain text. Do not include markdown fences, explanations, or any extra text.

**assertions.json:**
```json
{
  "required_labels": [
    "Node-1",
    "Node-2",
    "Node-3",
    "Node-4",
    "Bus"
  ],
  "forbidden_labels": [],
  "entity_count": 5,
  "required_edges": [],
  "required_edge_labels": [],
  "preserved_elements": []
}
```

### Task 2.2
**difficulty:** `easy`

**prompt.txt:** Draw an ASCII diagram illustrating a ring network with 4 nodes: "Node-A", "Node-B", "Node-C", "Node-D". Connect them in a ring: A→B→C→D→A. When arrows are required, make them centered and aligned cleanly to their source and target. If an arrow has a label, place the label a little above the arrow rather than inside the arrow line. Any component with incoming or outgoing arrows should be sized wide or tall enough to make those connections visually unambiguous, so it is clear where arrows originate and where they terminate. If one component fans out to multiple arrows, or multiple arrows converge into one component, its width or height should clearly support those attachment points. Return only the final ASCII diagram in plain text. Do not include markdown fences, explanations, or any extra text.

**assertions.json:**
```json
{
  "forbidden_labels": [],
  "required_edge_labels": [],
  "preserved_elements": [],
  "required_labels": [
    "Node-A",
    "Node-B",
    "Node-C",
    "Node-D"
  ],
  "entity_count": 4,
  "required_edges": [
    {
      "from": "Node-A",
      "to": "Node-B"
    },
    {
      "from": "Node-B",
      "to": "Node-C"
    },
    {
      "from": "Node-C",
      "to": "Node-D"
    },
    {
      "from": "Node-D",
      "to": "Node-A"
    }
  ]
}
```

### Task 2.3
**difficulty:** `easy`

**prompt.txt:** Draw an ASCII diagram illustrating DNS resolution. "Browser" → "Local Resolver" → "Root NS" → "TLD NS (.com)" → "Auth NS (example.com)" → "IP Address returned". Linear chain left to right. When arrows are required, make them centered and aligned cleanly to their source and target. If an arrow has a label, place the label a little above the arrow rather than inside the arrow line. Any component with incoming or outgoing arrows should be sized wide or tall enough to make those connections visually unambiguous, so it is clear where arrows originate and where they terminate. If one component fans out to multiple arrows, or multiple arrows converge into one component, its width or height should clearly support those attachment points. Return only the final ASCII diagram in plain text. Do not include markdown fences, explanations, or any extra text.

**assertions.json:**
```json
{
  "required_labels": [
    "Browser",
    "Local Resolver",
    "Root NS",
    "TLD NS (.com)",
    "Auth NS (example.com)",
    "IP Address returned"
  ],
  "forbidden_labels": [],
  "entity_count": 6,
  "required_edges": [
    {
      "from": "Browser",
      "to": "Local Resolver"
    },
    {
      "from": "Local Resolver",
      "to": "Root NS"
    },
    {
      "from": "Root NS",
      "to": "TLD NS (.com)"
    },
    {
      "from": "TLD NS (.com)",
      "to": "Auth NS (example.com)"
    },
    {
      "from": "Auth NS (example.com)",
      "to": "IP Address returned"
    }
  ],
  "required_edge_labels": [],
  "preserved_elements": []
}
```

### Task 2.4
**difficulty:** `easy`

**prompt.txt:** Draw an ASCII diagram illustrating a basic ring topology. Place four nodes labeled "Node-A", "Node-B", "Node-C", and "Node-D" in a loop so each node connects to the next and the last connects back to the first. When arrows are required, make them centered and aligned cleanly to their source and target. If an arrow has a label, place the label a little above the arrow rather than inside the arrow line. Any component with incoming or outgoing arrows should be sized wide or tall enough to make those connections visually unambiguous, so it is clear where arrows originate and where they terminate. If one component fans out to multiple arrows, or multiple arrows converge into one component, its width or height should clearly support those attachment points. Return only the final ASCII diagram in plain text. Do not include markdown fences, explanations, or any extra text.

**assertions.json:**
```json
{
  "required_labels": [
    "Node-A",
    "Node-B",
    "Node-C",
    "Node-D"
  ],
  "forbidden_labels": [],
  "entity_count": 4,
  "required_edges": [
    {
      "from": "Node-A",
      "to": "Node-B"
    },
    {
      "from": "Node-B",
      "to": "Node-C"
    },
    {
      "from": "Node-C",
      "to": "Node-D"
    },
    {
      "from": "Node-D",
      "to": "Node-A"
    }
  ],
  "required_edge_labels": [],
  "preserved_elements": []
}
```

### Task 2.5
**difficulty:** `easy`

**prompt.txt:** Draw an ASCII diagram illustrating a basic star topology. Put one central node labeled "Hub" in the middle. Around it place four outer nodes labeled "Node-1", "Node-2", "Node-3", and "Node-4". Connect each outer node directly to the Hub. When arrows are required, make them centered and aligned cleanly to their source and target. If an arrow has a label, place the label a little above the arrow rather than inside the arrow line. Any component with incoming or outgoing arrows should be sized wide or tall enough to make those connections visually unambiguous, so it is clear where arrows originate and where they terminate. If one component fans out to multiple arrows, or multiple arrows converge into one component, its width or height should clearly support those attachment points. Return only the final ASCII diagram in plain text. Do not include markdown fences, explanations, or any extra text.

**assertions.json:**
```json
{
  "required_labels": [
    "Hub",
    "Node-1",
    "Node-2",
    "Node-3",
    "Node-4"
  ],
  "forbidden_labels": [],
  "entity_count": 5,
  "required_edges": [
    {
      "from": "Hub",
      "to": "Node-1"
    },
    {
      "from": "Hub",
      "to": "Node-2"
    },
    {
      "from": "Hub",
      "to": "Node-3"
    },
    {
      "from": "Hub",
      "to": "Node-4"
    }
  ],
  "required_edge_labels": [],
  "preserved_elements": []
}
```

### Task 2.6
**difficulty:** `easy`

**prompt.txt:** Draw an ASCII diagram illustrating a Raspberry Pi PoE cluster. "Internet" at top connects to "Router". Router connects to "TP-Link Switch". The switch connects to four Pi nodes: "Pi-1", "Pi-2", "Pi-3", and "Pi-4". Label each switch-to-Pi arrow "Cat5E/6". When arrows are required, make them centered and aligned cleanly to their source and target. If an arrow has a label, place the label a little above the arrow rather than inside the arrow line. Any component with incoming or outgoing arrows should be sized wide or tall enough to make those connections visually unambiguous, so it is clear where arrows originate and where they terminate. If one component fans out to multiple arrows, or multiple arrows converge into one component, its width or height should clearly support those attachment points. Return only the final ASCII diagram in plain text. Do not include markdown fences, explanations, or any extra text.

**assertions.json:**
```json
{
  "required_labels": [
    "Internet",
    "Router",
    "TP-Link Switch",
    "Pi-1",
    "Pi-2",
    "Pi-3",
    "Pi-4",
    "Cat5E/6"
  ],
  "forbidden_labels": [],
  "entity_count": 7,
  "required_edges": [
    {
      "from": "Internet",
      "to": "Router"
    },
    {
      "from": "Router",
      "to": "TP-Link Switch"
    },
    {
      "from": "TP-Link Switch",
      "to": "Pi-1"
    },
    {
      "from": "TP-Link Switch",
      "to": "Pi-2"
    },
    {
      "from": "TP-Link Switch",
      "to": "Pi-3"
    },
    {
      "from": "TP-Link Switch",
      "to": "Pi-4"
    }
  ],
  "required_edge_labels": [
    "Cat5E/6"
  ],
  "preserved_elements": []
}
```

### Task 2.7
**difficulty:** `easy`

**prompt.txt:** Draw an ASCII diagram illustrating a pub/sub diagram. "Order Service" publishes to "Kafka". "Inventory Service" and "Notification Service" both subscribe from Kafka. Label the arrow from Order Service to Kafka "publish". Label arrows from Kafka to subscribers "subscribe". When arrows are required, make them centered and aligned cleanly to their source and target. If an arrow has a label, place the label a little above the arrow rather than inside the arrow line. Any component with incoming or outgoing arrows should be sized wide or tall enough to make those connections visually unambiguous, so it is clear where arrows originate and where they terminate. If one component fans out to multiple arrows, or multiple arrows converge into one component, its width or height should clearly support those attachment points. Return only the final ASCII diagram in plain text. Do not include markdown fences, explanations, or any extra text.

**assertions.json:**
```json
{
  "forbidden_labels": [],
  "required_edge_labels": [
    "publish",
    "subscribe"
  ],
  "preserved_elements": [],
  "required_labels": [
    "Order Service",
    "Kafka",
    "Inventory Service",
    "Notification Service",
    "publish",
    "subscribe"
  ],
  "entity_count": 4,
  "required_edges": [
    {
      "from": "Order Service",
      "to": "Kafka"
    },
    {
      "from": "Kafka",
      "to": "Inventory Service"
    },
    {
      "from": "Kafka",
      "to": "Notification Service"
    }
  ]
}
```

### Task 2.8
**difficulty:** `easy`

**prompt.txt:** Draw an ASCII diagram illustrating a basic star topology. Put one central node labeled "Hub" in the middle. Around it place four outer nodes labeled "Node-1", "Node-2", "Node-3", and "Node-4". Connect each outer node directly to the Hub. When arrows are required, make them centered and aligned cleanly to their source and target. If an arrow has a label, place the label a little above the arrow rather than inside the arrow line. Any component with incoming or outgoing arrows should be sized wide or tall enough to make those connections visually unambiguous, so it is clear where arrows originate and where they terminate. If one component fans out to multiple arrows, or multiple arrows converge into one component, its width or height should clearly support those attachment points. Return only the final ASCII diagram in plain text. Do not include markdown fences, explanations, or any extra text.

**assertions.json:**
```json
{
  "required_labels": [
    "Hub",
    "Node-1",
    "Node-2",
    "Node-3",
    "Node-4"
  ],
  "forbidden_labels": [],
  "entity_count": 5,
  "required_edges": [
    {
      "from": "Hub",
      "to": "Node-1"
    },
    {
      "from": "Hub",
      "to": "Node-2"
    },
    {
      "from": "Hub",
      "to": "Node-3"
    },
    {
      "from": "Hub",
      "to": "Node-4"
    }
  ],
  "required_edge_labels": [],
  "preserved_elements": []
}
```

### Task 2.9
**difficulty:** `easy`

**prompt.txt:** Draw an ASCII diagram illustrating a primary-replica database setup. One "Primary DB" on the left. Three replicas to the right: "Replica-1", "Replica-2", "Replica-3". Show arrows from Primary to each Replica labeled "async sync". When arrows are required, make them centered and aligned cleanly to their source and target. If an arrow has a label, place the label a little above the arrow rather than inside the arrow line. Any component with incoming or outgoing arrows should be sized wide or tall enough to make those connections visually unambiguous, so it is clear where arrows originate and where they terminate. If one component fans out to multiple arrows, or multiple arrows converge into one component, its width or height should clearly support those attachment points. Return only the final ASCII diagram in plain text. Do not include markdown fences, explanations, or any extra text.

**assertions.json:**
```json
{
  "required_labels": [
    "Primary DB",
    "Replica-1",
    "Replica-2",
    "Replica-3",
    "async sync"
  ],
  "forbidden_labels": [],
  "entity_count": 4,
  "required_edges": [
    {
      "from": "Primary DB",
      "to": "Replica-1"
    },
    {
      "from": "Primary DB",
      "to": "Replica-2"
    },
    {
      "from": "Primary DB",
      "to": "Replica-3"
    }
  ],
  "required_edge_labels": [
    "async sync"
  ],
  "preserved_elements": []
}
```

### Task 2.10
**difficulty:** `easy`

**prompt.txt:** Draw an ASCII diagram illustrating a full mesh topology with four boxed nodes labeled "A", "B", "C", and "D" arranged like a square. Connect every node directly to every other node, including both diagonals, and make the diagonals visibly intersect at the center like a classic full-mesh diagram. When arrows are required, make them centered and aligned cleanly to their source and target. If an arrow has a label, place the label a little above the arrow rather than inside the arrow line. Any component with incoming or outgoing arrows should be sized wide or tall enough to make those connections visually unambiguous, so it is clear where arrows originate and where they terminate. If one component fans out to multiple arrows, or multiple arrows converge into one component, its width or height should clearly support those attachment points. Return only the final ASCII diagram in plain text. Do not include markdown fences, explanations, or any extra text.

**assertions.json:**
```json
{
  "forbidden_labels": [],
  "required_edge_labels": [],
  "preserved_elements": [],
  "required_labels": [
    "A",
    "B",
    "C",
    "D"
  ],
  "entity_count": 4,
  "required_edges": [
    {
      "from": "A",
      "to": "B"
    },
    {
      "from": "A",
      "to": "C"
    },
    {
      "from": "A",
      "to": "D"
    },
    {
      "from": "B",
      "to": "C"
    },
    {
      "from": "B",
      "to": "D"
    },
    {
      "from": "C",
      "to": "D"
    }
  ]
}
```

### Task 2.11
**difficulty:** `medium`

**prompt.txt:** Draw an ASCII diagram illustrating a Kubernetes-style control plane architecture. Put "Client" at the top flowing down into "API Server". From the API Server, connect to "etcd", "Scheduler", and "Controller Manager". Below the Controller Manager, place three worker boxes labeled "Worker-1", "Worker-2", and "Worker-3". Inside each worker box include three lines: "kubelet", "kube-proxy", and "Pods". When arrows are required, make them centered and aligned cleanly to their source and target. If an arrow has a label, place the label a little above the arrow rather than inside the arrow line. Any component with incoming or outgoing arrows should be sized wide or tall enough to make those connections visually unambiguous, so it is clear where arrows originate and where they terminate. If one component fans out to multiple arrows, or multiple arrows converge into one component, its width or height should clearly support those attachment points. Return only the final ASCII diagram in plain text. Do not include markdown fences, explanations, or any extra text.

**assertions.json:**
```json
{
  "forbidden_labels": [],
  "required_edge_labels": [],
  "preserved_elements": [],
  "required_labels": [
    "Client",
    "API Server",
    "etcd",
    "Scheduler",
    "Controller Manager",
    "Worker-1",
    "Worker-2",
    "Worker-3",
    "kubelet",
    "kube-proxy",
    "Pods"
  ],
  "entity_count": 8,
  "required_edges": [
    {
      "from": "Client",
      "to": "API Server"
    },
    {
      "from": "API Server",
      "to": "etcd"
    },
    {
      "from": "API Server",
      "to": "Scheduler"
    },
    {
      "from": "API Server",
      "to": "Controller Manager"
    },
    {
      "from": "Controller Manager",
      "to": "Worker-1"
    },
    {
      "from": "Controller Manager",
      "to": "Worker-2"
    },
    {
      "from": "Controller Manager",
      "to": "Worker-3"
    }
  ]
}
```

### Task 2.12
**difficulty:** `medium`

**prompt.txt:** Draw an ASCII diagram illustrating a pipeline-parallel distributed training diagram. Put "Input Queue" on the left feeding four stage nodes in a row: "Stage-1 GPU", "Stage-2 GPU", "Stage-3 GPU", and "Stage-4 GPU". Label the arrow from Input Queue to Stage-1 GPU "micro-batch". Label the arrows between stage nodes "activations". Then directly below those forward links, add a second row of reverse-direction arrows mirroring the same three stage-to-stage connections, and label those reverse arrows "gradients". When arrows are required, make them centered and aligned cleanly to their source and target. If an arrow has a label, place the label a little above the arrow rather than inside the arrow line. Any component with incoming or outgoing arrows should be sized wide or tall enough to make those connections visually unambiguous, so it is clear where arrows originate and where they terminate. If one component fans out to multiple arrows, or multiple arrows converge into one component, its width or height should clearly support those attachment points. Return only the final ASCII diagram in plain text. Do not include markdown fences, explanations, or any extra text.

**assertions.json:**
```json
{
  "required_labels": [
    "Input Queue",
    "Stage-1 GPU",
    "Stage-2 GPU",
    "Stage-3 GPU",
    "Stage-4 GPU",
    "micro-batch",
    "activations",
    "gradients"
  ],
  "forbidden_labels": [],
  "entity_count": 5,
  "required_edges": [
    {
      "from": "Input Queue",
      "to": "Stage-1 GPU"
    },
    {
      "from": "Stage-1 GPU",
      "to": "Stage-2 GPU"
    },
    {
      "from": "Stage-2 GPU",
      "to": "Stage-3 GPU"
    },
    {
      "from": "Stage-3 GPU",
      "to": "Stage-4 GPU"
    },
    {
      "from": "Stage-4 GPU",
      "to": "Stage-3 GPU"
    },
    {
      "from": "Stage-3 GPU",
      "to": "Stage-2 GPU"
    },
    {
      "from": "Stage-2 GPU",
      "to": "Stage-1 GPU"
    }
  ],
  "required_edge_labels": [
    "micro-batch",
    "activations",
    "gradients"
  ],
  "preserved_elements": []
}
```

### Task 2.13
**difficulty:** `medium`

**prompt.txt:** Draw an ASCII diagram illustrating a service mesh with sidecars. Three services in a row: "Service A", "Service B", "Service C". Each has a small sidecar box directly below it labeled "Proxy". All Proxy boxes connect to a central "Control Plane" box below. Return only the final ASCII diagram in plain text. Do not include markdown fences, explanations, or any extra text.

**assertions.json:**
```json
{
  "required_labels": [
    "Service A",
    "Service B",
    "Service C",
    "Proxy",
    "Control Plane"
  ],
  "forbidden_labels": [],
  "entity_count": 7,
  "required_edges": [],
  "required_edge_labels": [],
  "preserved_elements": []
}
```

### Task 2.14
**difficulty:** `medium`

**prompt.txt:** Draw an ASCII diagram illustrating a three-level Fat Tree network with one boxed Core switch, two boxed Aggregation switches, six boxed Top-of-Rack switches, and four boxed Hosts. Label the aggregation switches "Agg1" and "Agg2", the six ToR switches "ToR-1" through "ToR-6", and the four hosts "Host-1" through "Host-4". Arrange it like the provided structure with Core at the top, Agg1 and Agg2 below, three ToR switches under each aggregation switch, and hosts hanging below the outer two ToR switches on each side. Connect every layer vertically. When arrows are required, make them centered and aligned cleanly to their source and target. If an arrow has a label, place the label a little above the arrow rather than inside the arrow line. Any component with incoming or outgoing arrows should be sized wide or tall enough to make those connections visually unambiguous, so it is clear where arrows originate and where they terminate. If one component fans out to multiple arrows, or multiple arrows converge into one component, its width or height should clearly support those attachment points. Return only the final ASCII diagram in plain text. Do not include markdown fences, explanations, or any extra text.

**assertions.json:**
```json
{
  "required_labels": [
    "Core",
    "Agg1",
    "Agg2",
    "ToR-1",
    "ToR-2",
    "ToR-3",
    "ToR-4",
    "ToR-5",
    "ToR-6",
    "Host-1",
    "Host-2",
    "Host-3",
    "Host-4"
  ],
  "forbidden_labels": [],
  "entity_count": 13,
  "required_edges": [
    {
      "from": "Core",
      "to": "Agg1"
    },
    {
      "from": "Core",
      "to": "Agg2"
    },
    {
      "from": "Agg1",
      "to": "ToR-1"
    },
    {
      "from": "Agg1",
      "to": "ToR-2"
    },
    {
      "from": "Agg1",
      "to": "ToR-3"
    },
    {
      "from": "Agg2",
      "to": "ToR-4"
    },
    {
      "from": "Agg2",
      "to": "ToR-5"
    },
    {
      "from": "Agg2",
      "to": "ToR-6"
    },
    {
      "from": "ToR-1",
      "to": "Host-1"
    },
    {
      "from": "ToR-2",
      "to": "Host-2"
    },
    {
      "from": "ToR-4",
      "to": "Host-3"
    },
    {
      "from": "ToR-5",
      "to": "Host-4"
    }
  ],
  "required_edge_labels": [],
  "preserved_elements": []
}
```

### Task 2.15
**difficulty:** `medium`

**prompt.txt:** Draw an ASCII diagram illustrating a two-stage butterfly-style crossed-connection diagram with boxed endpoint nodes. Put the label "Input" on the left and the label "Output" on the right. Show one clean butterfly crossing where boxed nodes "A" and "B" feed into a centered crossing labeled "XX" and emerge as boxed nodes "A'" and "B'". Below it, show a second matching butterfly crossing where boxed nodes "C" and "D" feed into another centered crossing labeled "XX" and emerge as boxed nodes "C'" and "D'". Keep the crossing geometry clean and symmetric like a classic butterfly diagram. When arrows are required, make them centered and aligned cleanly to their source and target. If an arrow has a label, place the label a little above the arrow rather than inside the arrow line. Any component with incoming or outgoing arrows should be sized wide or tall enough to make those connections visually unambiguous, so it is clear where arrows originate and where they terminate. If one component fans out to multiple arrows, or multiple arrows converge into one component, its width or height should clearly support those attachment points. Return only the final ASCII diagram in plain text. Do not include markdown fences, explanations, or any extra text.

**assertions.json:**
```json
{
  "required_labels": [
    "Input",
    "Output",
    "A",
    "B",
    "C",
    "D",
    "A'",
    "B'",
    "C'",
    "D'",
    "XX"
  ],
  "forbidden_labels": [],
  "entity_count": 8,
  "required_edges": [
    {
      "from": "A",
      "to": "A'"
    },
    {
      "from": "B",
      "to": "B'"
    },
    {
      "from": "C",
      "to": "C'"
    },
    {
      "from": "D",
      "to": "D'"
    }
  ],
  "required_edge_labels": [],
  "preserved_elements": []
}
```

### Task 2.16
**difficulty:** `hard`

**prompt.txt:** Draw an ASCII diagram illustrating a roomy hybrid home inference cluster. Put "Internet" at the top connected bidirectionally to a boxed "Router". The router connects bidirectionally to both "MacBook M1 (Orchestrator)" and a boxed "Switch" using links labeled "Cat5E/6", with each label placed a little above its arrow line. The orchestrator connects bidirectionally to "Mac Mini M4 Worker-1" via a link labeled "Thunderbolt", and "Mac Mini M4 Worker-2" plus "Mac Mini M4 Worker-3" each connect bidirectionally to Worker-1 via "Thunderbolt". The switch connects bidirectionally to four inference nodes, "Jetson Orin Nano-1", "Jetson Orin Nano-2", "Jetson Orin Nano-3", and "Jetson Orin Nano-4", and each of those switch links should also be labeled "Cat5E/6" above the arrow. When arrows are required, make them centered and aligned cleanly to their source and target. If an arrow has a label, place the label a little above the arrow rather than inside the arrow line. Any component with incoming or outgoing arrows should be sized wide or tall enough to make those connections visually unambiguous, so it is clear where arrows originate and where they terminate. If one component fans out to multiple arrows, or multiple arrows converge into one component, its width or height should clearly support those attachment points. Return only the final ASCII diagram in plain text. Do not include markdown fences, explanations, or any extra text.

**assertions.json:**
```json
{
  "required_labels": [
    "Internet",
    "Router",
    "MacBook M1 (Orchestrator)",
    "Mac Mini M4 Worker-1",
    "Mac Mini M4 Worker-2",
    "Mac Mini M4 Worker-3",
    "Switch",
    "Jetson Orin Nano-1",
    "Jetson Orin Nano-2",
    "Jetson Orin Nano-3",
    "Jetson Orin Nano-4",
    "Thunderbolt",
    "Cat5E/6"
  ],
  "forbidden_labels": [],
  "entity_count": 11,
  "required_edges": [
    {
      "from": "Internet",
      "to": "Router"
    },
    {
      "from": "Router",
      "to": "Internet"
    },
    {
      "from": "Router",
      "to": "MacBook M1 (Orchestrator)"
    },
    {
      "from": "MacBook M1 (Orchestrator)",
      "to": "Router"
    },
    {
      "from": "Router",
      "to": "Switch"
    },
    {
      "from": "Switch",
      "to": "Router"
    },
    {
      "from": "MacBook M1 (Orchestrator)",
      "to": "Mac Mini M4 Worker-1"
    },
    {
      "from": "Mac Mini M4 Worker-1",
      "to": "MacBook M1 (Orchestrator)"
    },
    {
      "from": "Mac Mini M4 Worker-2",
      "to": "Mac Mini M4 Worker-1"
    },
    {
      "from": "Mac Mini M4 Worker-1",
      "to": "Mac Mini M4 Worker-2"
    },
    {
      "from": "Mac Mini M4 Worker-3",
      "to": "Mac Mini M4 Worker-1"
    },
    {
      "from": "Mac Mini M4 Worker-1",
      "to": "Mac Mini M4 Worker-3"
    },
    {
      "from": "Switch",
      "to": "Jetson Orin Nano-1"
    },
    {
      "from": "Jetson Orin Nano-1",
      "to": "Switch"
    },
    {
      "from": "Switch",
      "to": "Jetson Orin Nano-2"
    },
    {
      "from": "Jetson Orin Nano-2",
      "to": "Switch"
    },
    {
      "from": "Switch",
      "to": "Jetson Orin Nano-3"
    },
    {
      "from": "Jetson Orin Nano-3",
      "to": "Switch"
    },
    {
      "from": "Switch",
      "to": "Jetson Orin Nano-4"
    },
    {
      "from": "Jetson Orin Nano-4",
      "to": "Switch"
    }
  ],
  "required_edge_labels": [
    "Thunderbolt",
    "Cat5E/6"
  ],
  "preserved_elements": []
}
```

### Task 2.17
**difficulty:** `hard`

**prompt.txt:** Draw an ASCII diagram illustrating an ASCII diagram of the BitTorrent architecture. Place a box labeled "Tracker" at the top center. Below it, arrange four peer nodes in a square: "Peer A (Leecher)", "Peer B (Leecher)", "Peer C (Leecher)", and "Seed (100%)". Connect each peer to the Tracker using arrows labeled "announce". Draw bidirectional arrows between neighboring peers to represent direct peer-to-peer file piece exchange, and show a direct connection from the Seed to each Leecher. Add a caption below the diagram: "Tracker coordinates peer discovery; peers exchange file pieces directly." When arrows are required, make them centered and aligned cleanly to their source and target. If an arrow has a label, place the label a little above the arrow rather than inside the arrow line. Any component with incoming or outgoing arrows should be sized wide or tall enough to make those connections visually unambiguous, so it is clear where arrows originate and where they terminate. If one component fans out to multiple arrows, or multiple arrows converge into one component, its width or height should clearly support those attachment points. Return only the final ASCII diagram in plain text. Do not include markdown fences, explanations, or any extra text.

**assertions.json:**
```json
{
  "required_labels": [
    "Tracker",
    "Peer A (Leecher)",
    "Peer B (Leecher)",
    "Peer C (Leecher)",
    "Seed (100%)",
    "announce",
    "Tracker coordinates peer discovery; peers exchange file pieces directly."
  ],
  "forbidden_labels": [],
  "entity_count": 5,
  "required_edges": [
    {
      "from": "Peer A (Leecher)",
      "to": "Tracker"
    },
    {
      "from": "Peer B (Leecher)",
      "to": "Tracker"
    },
    {
      "from": "Peer C (Leecher)",
      "to": "Tracker"
    },
    {
      "from": "Seed (100%)",
      "to": "Tracker"
    },
    {
      "from": "Peer A (Leecher)",
      "to": "Peer B (Leecher)"
    },
    {
      "from": "Peer B (Leecher)",
      "to": "Peer A (Leecher)"
    },
    {
      "from": "Peer A (Leecher)",
      "to": "Peer C (Leecher)"
    },
    {
      "from": "Peer C (Leecher)",
      "to": "Peer A (Leecher)"
    },
    {
      "from": "Peer B (Leecher)",
      "to": "Seed (100%)"
    },
    {
      "from": "Seed (100%)",
      "to": "Peer B (Leecher)"
    },
    {
      "from": "Peer C (Leecher)",
      "to": "Seed (100%)"
    },
    {
      "from": "Seed (100%)",
      "to": "Peer C (Leecher)"
    },
    {
      "from": "Peer A (Leecher)",
      "to": "Seed (100%)"
    },
    {
      "from": "Seed (100%)",
      "to": "Peer A (Leecher)"
    }
  ],
  "required_edge_labels": [
    "announce"
  ],
  "preserved_elements": []
}
```

### Task 2.18
**difficulty:** `hard`

**prompt.txt:** Draw an ASCII diagram illustrating a DiLoCo training diagram. Put a box labeled "Outer Optimizer" at the top. Below it, arrange four worker boxes in a row labeled "Worker-1", "Worker-2", "Worker-3", and "Worker-4". Inside each worker box, show stacked lines for "Local", "Model", "AdamW", "grad g", and "N steps". Draw downward arrows from the Outer Optimizer to each worker labeled "updated weights". Then show the workers sending "parameter deltas" back upward to the Outer Optimizer every N local steps. Add the title "DiLoCo" above the whole diagram. When arrows are required, make them centered and aligned cleanly to their source and target. If an arrow has a label, place the label a little above the arrow rather than inside the arrow line. Any component with incoming or outgoing arrows should be sized wide or tall enough to make those connections visually unambiguous, so it is clear where arrows originate and where they terminate. If one component fans out to multiple arrows, or multiple arrows converge into one component, its width or height should clearly support those attachment points. Return only the final ASCII diagram in plain text. Do not include markdown fences, explanations, or any extra text.

**assertions.json:**
```json
{
  "required_labels": [
    "DiLoCo",
    "Outer Optimizer",
    "Worker-1",
    "Worker-2",
    "Worker-3",
    "Worker-4",
    "Local",
    "Model",
    "AdamW",
    "grad g",
    "N steps",
    "updated weights",
    "parameter deltas"
  ],
  "forbidden_labels": [],
  "entity_count": 5,
  "required_edges": [
    {
      "from": "Outer Optimizer",
      "to": "Worker-1"
    },
    {
      "from": "Outer Optimizer",
      "to": "Worker-2"
    },
    {
      "from": "Outer Optimizer",
      "to": "Worker-3"
    },
    {
      "from": "Outer Optimizer",
      "to": "Worker-4"
    },
    {
      "from": "Worker-1",
      "to": "Outer Optimizer"
    },
    {
      "from": "Worker-2",
      "to": "Outer Optimizer"
    },
    {
      "from": "Worker-3",
      "to": "Outer Optimizer"
    },
    {
      "from": "Worker-4",
      "to": "Outer Optimizer"
    }
  ],
  "required_edge_labels": [
    "updated weights",
    "parameter deltas"
  ],
  "preserved_elements": []
}
```

### Task 2.19
**difficulty:** `hard`

**prompt.txt:** Draw an ASCII diagram illustrating a peer discovery diagram. Six Pi nodes in two rows of three: top row "Pi-1", "Pi-2", "Pi-3"; bottom row "Pi-4", "Pi-5", "Pi-6". Show dotted broadcast lines (using ...) between all Pi nodes representing mDNS multicast. One "Tracker" node to the side connected only to Pi-1. Return only the final ASCII diagram in plain text. Do not include markdown fences, explanations, or any extra text.

**assertions.json:**
```json
{
  "required_labels": [
    "Pi-1",
    "Pi-2",
    "Pi-3",
    "Pi-4",
    "Pi-5",
    "Pi-6",
    "Tracker"
  ],
  "forbidden_labels": [],
  "entity_count": 7,
  "required_edges": [],
  "required_edge_labels": [],
  "preserved_elements": []
}
```

### Task 2.20
**difficulty:** `hard`

**prompt.txt:** Draw an ASCII diagram illustrating a parameter server architecture. One "Parameter Server" at the top. Four "Worker" boxes below it. Show bidirectional arrows between PS and each worker labeled "push gradients" (Worker→PS) and "pull params" (PS→Worker). When arrows are required, make them centered and aligned cleanly to their source and target. If an arrow has a label, place the label a little above the arrow rather than inside the arrow line. Any component with incoming or outgoing arrows should be sized wide or tall enough to make those connections visually unambiguous, so it is clear where arrows originate and where they terminate. If one component fans out to multiple arrows, or multiple arrows converge into one component, its width or height should clearly support those attachment points. Return only the final ASCII diagram in plain text. Do not include markdown fences, explanations, or any extra text.

**assertions.json:**
```json
{
  "required_labels": [
    "Parameter Server",
    "Worker",
    "push gradients",
    "pull params"
  ],
  "forbidden_labels": [],
  "entity_count": 5,
  "required_edges": [
    {
      "from": "Parameter Server",
      "to": "Worker-1"
    },
    {
      "from": "Parameter Server",
      "to": "Worker-2"
    },
    {
      "from": "Parameter Server",
      "to": "Worker-3"
    },
    {
      "from": "Parameter Server",
      "to": "Worker-4"
    },
    {
      "from": "Worker-1",
      "to": "Parameter Server"
    },
    {
      "from": "Worker-2",
      "to": "Parameter Server"
    },
    {
      "from": "Worker-3",
      "to": "Parameter Server"
    },
    {
      "from": "Worker-4",
      "to": "Parameter Server"
    }
  ],
  "required_edge_labels": [
    "push gradients",
    "pull params"
  ],
  "preserved_elements": []
}
```

## Category 3: Diagram Editing

### Proposed Medium/Hard Refresh For Category 3

This section is a design note only for future task upgrades. It does not change the current benchmark tasks under `tasks/`.

#### Proposed Difficulty Rule

- `easy`: at most `1` meaningful edit.
- `medium`: about `3` coordinated edits in one diagram.
- `hard`: `4+` coordinated edits, usually spanning structure, labels, layout, and connections together.

#### Medium Task Direction

Medium tasks should feel like real diagram maintenance work rather than one small patch. A good medium task should usually require exactly three coordinated changes such as:

- add one node, reroute one existing connection, and remove one obsolete connection
- rename a component, resize its box, and realign one or more arrows
- split one box into two boxes, preserve upstream/downstream nodes, and reconnect the flow correctly
- add multiline text inside an existing node, widen that node, and keep surrounding arrows aligned
- insert an intermediate service layer between two existing layers, remove the old direct edge, and preserve the rest of the layout
- add a grouping/region box, move one node inside it, and keep the original internal topology unchanged

#### Proposed Medium Task Ideas

##### Medium Idea A: Split One Node Into Two And Reroute Flow

**source:**
```text
+--------+     +-----+
| Client |---->| API |---->+----+
+--------+     +-----+     | DB |
                            +----+
```

**reference:**
```text
+--------+   +-------------+   +-------------+   +----+
| Client |-->| API Gateway |-->| App Service |-->| DB |
+--------+   +-------------+   +-------------+   +----+
```

Why this is medium:
- split one box into two
- remove one old direct edge
- add two new edges while preserving endpoints

##### Medium Idea B: Add A Side Cache Branch With One Labeled Edge

**source:**
```text
+-----+     +----+
| App |---->| DB |
+-----+     +----+
```

**reference:**
```text
                read-through
+-----+------->+-------+
| App |        | Cache |
+-----+--+     +-------+
         |
         v
       +----+
       | DB |
       +----+
```

Why this is medium:
- add one new node
- preserve the original DB path
- add one new labeled edge with layout-sensitive branching

##### Medium Idea C: Move To Multiline Node Content Without Breaking Flow

**source:**
```text
+----------+     +---------+
| Browser  |---->| Worker  |
+----------+     +---------+
```

**reference:**
```text
+----------+     +-------------+
| Browser  |---->| Worker      |
+----------+     | v2.4        |
                 | healthy     |
                 +-------------+
```

Why this is medium:
- add two internal text lines
- resize the box
- preserve the existing arrow alignment

##### Medium Idea D: Replace A Middle Node And Reconnect Both Sides

**source:**
```text
+----------+     +-------+     +----------+
| Producer |---->| Queue |---->| Consumer |
+----------+     +-------+     +----------+
```

**reference:**
```text
+----------+     +--------+     +----------+
| Producer |---->| Broker |---->| Consumer |
+----------+     +--------+     +----------+
```

Why this is medium:
- remove one node
- add one replacement node
- reconnect both sides without disturbing the outer nodes

#### Hard Task Direction

Hard tasks should stop feeling like local edits and start feeling like controlled refactors. A good hard task should usually require four or more coordinated changes, with at least one structural rewrite and at least one layout-sensitive preservation requirement.

Hard tasks should often combine:

- node addition/removal
- node rename or merge/split
- rerouting multiple edges
- preserving unrelated layers exactly
- multiline text updates inside nodes
- rebalancing layout so arrows remain centered and non-ambiguous

#### Proposed Hard Task Ideas

##### Hard Idea A: Replace One Database With Replicated Storage

**source:**
```text
     +---------+
     | API App |
     +---------+
          |
          v
     +----------+
     | Database |
     +----------+
      /        \
     v          v
+---------+  +-----------+
| Billing |  | Analytics |
+---------+  +-----------+
```

**reference:**
```text
            +---------+
            | API App |
            +---------+
             /      \
            v        v
   +---------------+   +--------------+
   | Write Primary |-->| Read Replica |
   +---------------+   +--------------+
        |                    |
        v                    v
   +---------+          +-----------+
   | Billing |          | Analytics |
   +---------+          +-----------+
```

Why this is hard:
- replace one node with two nodes
- add a replication edge
- preserve two downstream consumers
- reroute the upstream app across a new two-node storage layer

##### Hard Idea B: Merge Two Services Into One Shared Identity Layer

**source:**
```text
+--------+     +---------+
| Auth   |     | Session |
+--------+     +---------+
    |               |
    v               v
+----------+   +-------------+
| Users DB |   | Sessions DB |
+----------+   +-------------+
```

**reference:**
```text
        +------------------+
        | Identity Service |
        +------------------+
           /           \
          v             v
    +----------+   +-------------+
    | Users DB |   | Sessions DB |
    +----------+   +-------------+
```

Why this is hard:
- remove two boxes and introduce one merged box
- relabel the service layer
- preserve both databases
- rebuild the connections cleanly with a different topology

##### Hard Idea C: Insert A Full Observability Layer

**source:**
```text
+-----------+   +-----------+   +-----------+
| Service A |-->| Service B |-->| Service C |
+-----------+   +-----------+   +-----------+
```

**reference:**
```text
+-----------+   +-----------+   +-----------+
| Service A |-->| Service B |-->| Service C |
+-----------+   +-----------+   +-----------+
      |               |               |
      v               v               v
+---------+      +------+        +---------+
| Metrics |      | Logs |        | Tracing |
+---------+      +------+        +---------+
```

Why this is hard:
- preserve the original service chain exactly
- add three new sink nodes
- add three new vertical edges
- rebalance spacing so the new lower layer still reads cleanly

##### Hard Idea D: Refactor Star Into Two-Layer Hierarchy

**source:**
```text
               +--------+
               | Leader |
               +--------+
            /    |    |    \
           v     v    v     v
+------------+ +------------+ +------------+ +------------+
| Follower-1 | | Follower-2 | | Follower-3 | | Follower-4 |
+------------+ +------------+ +------------+ +------------+
```

**reference:**
```text
               +--------+
               | Leader |
               +--------+
                    |
                    v
            +--------------+
            | Aggregator   |
            +--------------+
          /    |      |     \
         v     v      v      v
+------------+ +------------+ +------------+ +------------+
| Follower-1 | | Follower-2 | | Follower-3 | | Follower-4 |
+------------+ +------------+ +------------+ +------------+
```

Why this is hard:
- add a new middle layer
- remove the old fan-out from leader
- reroute all follower edges through the new node
- preserve the follower layer while changing the hierarchy

#### What Medium/Hard Should Avoid

- medium tasks that are effectively just one rename plus a resize
- hard tasks that are only bigger because there are more boxes, but not more edit types
- tasks where one edit dominates and the rest are trivial visual cleanup
- tasks that let the model redraw the whole diagram without being penalized for breaking preserved structure

#### Suggested Category 3 Shape

- `3.1` to `3.10`: easy, one edit max
- `3.11` to `3.15`: medium, roughly three edits each
- `3.16` to `3.20`: hard, four or more edits each

The strongest medium/hard tasks should make the model prove that it can preserve existing structure while performing multiple precise coordinated edits.

### Task 3.1
**difficulty:** `easy`

**prompt.txt:** Draw an ASCII diagram illustrating add a "Database" box to the right of the Server box. Connect Server to Database with a right-pointing arrow. Do not change anything else. When arrows are required, make them centered and aligned cleanly to their source and target. If an arrow has a label, place the label a little above the arrow rather than inside the arrow line. Any component with incoming or outgoing arrows should be sized wide or tall enough to make those connections visually unambiguous, so it is clear where arrows originate and where they terminate. If one component fans out to multiple arrows, or multiple arrows converge into one component, its width or height should clearly support those attachment points. Strictly apply only the requested edits and do not make any other changes outside them. Return only the final ASCII diagram in plain text. Do not include markdown fences, explanations, or any extra text.

**source.ascii:**
```text
+----------+     +----------+
|  Client  |---->|  Server  |
+----------+     +----------+
```

**assertions.json:**
```json
{
  "required_labels": [
    "Client",
    "Server",
    "Database"
  ],
  "forbidden_labels": [],
  "entity_count": 3,
  "required_edges": [
    {
      "from": "Client",
      "to": "Server"
    },
    {
      "from": "Server",
      "to": "Database"
    }
  ],
  "editing": {
    "required_edge_labels": [],
    "preserved_elements": [
      "Client",
      "Server"
    ]
  }
}
```

### Task 3.2
**difficulty:** `easy`

**prompt.txt:** Draw an ASCII diagram illustrating remove the Cache box and its connections. Connect Web directly to DB with an arrow. When arrows are required, make them centered and aligned cleanly to their source and target. If an arrow has a label, place the label a little above the arrow rather than inside the arrow line. Any component with incoming or outgoing arrows should be sized wide or tall enough to make those connections visually unambiguous, so it is clear where arrows originate and where they terminate. If one component fans out to multiple arrows, or multiple arrows converge into one component, its width or height should clearly support those attachment points. Strictly apply only the requested edits and do not make any other changes outside them. Return only the final ASCII diagram in plain text. Do not include markdown fences, explanations, or any extra text.

**source.ascii:**
```text
+-------+     +-------+     +------+
|  Web  |---->| Cache |---->|  DB  |
+-------+     +-------+     +------+
```

**assertions.json:**
```json
{
  "required_labels": [
    "Web",
    "DB"
  ],
  "forbidden_labels": [
    "Cache"
  ],
  "entity_count": 2,
  "required_edges": [
    {
      "from": "Web",
      "to": "DB"
    }
  ],
  "editing": {
    "required_edge_labels": [],
    "preserved_elements": [
      "Web",
      "DB"
    ]
  }
}
```

### Task 3.3
**difficulty:** `easy`

**prompt.txt:** Draw an ASCII diagram illustrating rename "App Srv" to "FastAPI". Resize the box to fit the new label. Keep everything else exactly the same. When arrows are required, make them centered and aligned cleanly to their source and target. If an arrow has a label, place the label a little above the arrow rather than inside the arrow line. Any component with incoming or outgoing arrows should be sized wide or tall enough to make those connections visually unambiguous, so it is clear where arrows originate and where they terminate. If one component fans out to multiple arrows, or multiple arrows converge into one component, its width or height should clearly support those attachment points. Strictly apply only the requested edits and do not make any other changes outside them. Return only the final ASCII diagram in plain text. Do not include markdown fences, explanations, or any extra text.

**source.ascii:**
```text
+--------+     +---------+
|  Nginx |---->| App Srv |
+--------+     +---------+
```

**assertions.json:**
```json
{
  "required_labels": [
    "Nginx",
    "FastAPI"
  ],
  "forbidden_labels": [
    "App Srv"
  ],
  "entity_count": 2,
  "required_edges": [
    {
      "from": "Nginx",
      "to": "FastAPI"
    }
  ],
  "editing": {
    "required_edge_labels": [],
    "preserved_elements": [
      "Nginx"
    ]
  }
}
```

### Task 3.4
**difficulty:** `easy`

**prompt.txt:** Draw an ASCII diagram illustrating reverse the arrow direction. It should now point from NodeB to NodeA. When arrows are required, make them centered and aligned cleanly to their source and target. If an arrow has a label, place the label a little above the arrow rather than inside the arrow line. Any component with incoming or outgoing arrows should be sized wide or tall enough to make those connections visually unambiguous, so it is clear where arrows originate and where they terminate. If one component fans out to multiple arrows, or multiple arrows converge into one component, its width or height should clearly support those attachment points. Strictly apply only the requested edits and do not make any other changes outside them. Return only the final ASCII diagram in plain text. Do not include markdown fences, explanations, or any extra text.

**source.ascii:**
```text
+---------+     +---------+
|  NodeA  |---->|  NodeB  |
+---------+     +---------+
```

**assertions.json:**
```json
{
  "required_labels": [
    "NodeA",
    "NodeB"
  ],
  "forbidden_labels": [],
  "entity_count": 2,
  "required_edges": [
    {
      "from": "NodeB",
      "to": "NodeA"
    }
  ],
  "editing": {
    "required_edge_labels": [],
    "preserved_elements": [
      "NodeA",
      "NodeB"
    ]
  }
}
```

### Task 3.5
**difficulty:** `easy`

**prompt.txt:** Draw an ASCII diagram illustrating add a bidirectional arrow between Service and Monitor labeled "metrics" above the arrow line. When arrows are required, make them centered and aligned cleanly to their source and target. If an arrow has a label, place the label a little above the arrow rather than inside the arrow line. Any component with incoming or outgoing arrows should be sized wide or tall enough to make those connections visually unambiguous, so it is clear where arrows originate and where they terminate. If one component fans out to multiple arrows, or multiple arrows converge into one component, its width or height should clearly support those attachment points. Strictly apply only the requested edits and do not make any other changes outside them. Return only the final ASCII diagram in plain text. Do not include markdown fences, explanations, or any extra text.

**source.ascii:**
```text
+---------+          +---------+
| Service |          | Monitor |
+---------+          +---------+
```

**assertions.json:**
```json
{
  "required_labels": [
    "Service",
    "Monitor",
    "metrics"
  ],
  "forbidden_labels": [],
  "entity_count": 2,
  "required_edges": [
    {
      "from": "Service",
      "to": "Monitor"
    },
    {
      "from": "Monitor",
      "to": "Service"
    }
  ],
  "editing": {
    "required_edge_labels": [
      "metrics"
    ],
    "preserved_elements": [
      "Service",
      "Monitor"
    ]
  }
}
```

### Task 3.6
**difficulty:** `easy`

**prompt.txt:** Draw an ASCII diagram illustrating add an internal section below the title. Use a horizontal divider (+-...+) to separate. Add two endpoints below the divider: "/login" and "/refresh". Strictly apply only the requested edits and do not make any other changes outside them. Return only the final ASCII diagram in plain text. Do not include markdown fences, explanations, or any extra text.

**source.ascii:**
```text
+------------------+
|   Auth Service   |
+------------------+
```

**assertions.json:**
```json
{
  "required_labels": [
    "Auth Service",
    "/login",
    "/refresh"
  ],
  "forbidden_labels": [],
  "entity_count": 1,
  "required_edges": [],
  "editing": {
    "required_edge_labels": [],
    "preserved_elements": [
      "Auth Service"
    ]
  }
}
```

### Task 3.7
**difficulty:** `easy`

**prompt.txt:** Draw an ASCII diagram illustrating mark the Server as a failure point: change its corner characters from + to * and add the label "FAILED" directly below the Server box. When arrows are required, make them centered and aligned cleanly to their source and target. If an arrow has a label, place the label a little above the arrow rather than inside the arrow line. Any component with incoming or outgoing arrows should be sized wide or tall enough to make those connections visually unambiguous, so it is clear where arrows originate and where they terminate. If one component fans out to multiple arrows, or multiple arrows converge into one component, its width or height should clearly support those attachment points. Strictly apply only the requested edits and do not make any other changes outside them. Return only the final ASCII diagram in plain text. Do not include markdown fences, explanations, or any extra text.

**source.ascii:**
```text
+--------+     +--------+     +------+
| Client |---->| Server |---->|  DB  |
+--------+     +--------+     +------+
```

**assertions.json:**
```json
{
  "required_labels": [
    "Client",
    "Server",
    "DB",
    "FAILED"
  ],
  "forbidden_labels": [],
  "entity_count": 3,
  "required_edges": [
    {
      "from": "Client",
      "to": "Server"
    },
    {
      "from": "Server",
      "to": "DB"
    }
  ],
  "editing": {
    "required_edge_labels": [],
    "preserved_elements": [
      "Client",
      "DB"
    ]
  }
}
```

### Task 3.8
**difficulty:** `easy`

**prompt.txt:** Draw an ASCII diagram illustrating insert an "API Server" between Browser and Database. Remove the direct Browser-to-Database arrow. Add Browser→API Server and API Server→Database arrows. When arrows are required, make them centered and aligned cleanly to their source and target. If an arrow has a label, place the label a little above the arrow rather than inside the arrow line. Any component with incoming or outgoing arrows should be sized wide or tall enough to make those connections visually unambiguous, so it is clear where arrows originate and where they terminate. If one component fans out to multiple arrows, or multiple arrows converge into one component, its width or height should clearly support those attachment points. Strictly apply only the requested edits and do not make any other changes outside them. Return only the final ASCII diagram in plain text. Do not include markdown fences, explanations, or any extra text.

**source.ascii:**
```text
+---------+     +----------+
| Browser |---->| Database |
+---------+     +----------+
```

**assertions.json:**
```json
{
  "required_labels": [
    "Browser",
    "API Server",
    "Database"
  ],
  "forbidden_labels": [],
  "entity_count": 3,
  "required_edges": [
    {
      "from": "Browser",
      "to": "API Server"
    },
    {
      "from": "API Server",
      "to": "Database"
    }
  ],
  "editing": {
    "required_edge_labels": [],
    "preserved_elements": [
      "Browser",
      "Database"
    ]
  }
}
```

### Task 3.9
**difficulty:** `easy`

**prompt.txt:** Draw an ASCII diagram illustrating add protocol labels to the existing arrows only: "HTTP" on Browser→API, "gRPC" on API→Worker, "SQL" on Worker→DB, and "cache" on Worker→Redis. When arrows are required, make them centered and aligned cleanly to their source and target. If an arrow has a label, place the label a little above the arrow rather than inside the arrow line. Any component with incoming or outgoing arrows should be sized wide or tall enough to make those connections visually unambiguous, so it is clear where arrows originate and where they terminate. If one component fans out to multiple arrows, or multiple arrows converge into one component, its width or height should clearly support those attachment points. Strictly apply only the requested edits and do not make any other changes outside them. Return only the final ASCII diagram in plain text. Do not include markdown fences, explanations, or any extra text.

**source.ascii:**
```text
+-----------+     +-----------+
|  Browser  |---->|    API    |
+-----------+     +-----------+
                     |
                     v
                +-----------+
                |  Worker   |
                +-----------+
                 /         \
                v           v
          +----------+   +----------+
          |    DB    |   |  Redis   |
          +----------+   +----------+
```

**assertions.json:**
```json
{
  "required_labels": [
    "Browser",
    "API",
    "Worker",
    "DB",
    "Redis",
    "HTTP",
    "gRPC",
    "SQL",
    "cache"
  ],
  "forbidden_labels": [],
  "entity_count": 5,
  "required_edges": [
    {
      "from": "Browser",
      "to": "API"
    },
    {
      "from": "API",
      "to": "Worker"
    },
    {
      "from": "Worker",
      "to": "DB"
    },
    {
      "from": "Worker",
      "to": "Redis"
    }
  ],
  "editing": {
    "required_edge_labels": [
      "HTTP",
      "gRPC",
      "SQL",
      "cache"
    ],
    "preserved_elements": [
      "Browser",
      "API",
      "Worker",
      "DB",
      "Redis"
    ]
  }
}
```

### Task 3.10
**difficulty:** `easy`

**prompt.txt:** Draw an ASCII diagram illustrating remove "Follower-3" and its connection from the cluster, while preserving the remaining follower layout. Strictly apply only the requested edits and do not make any other changes outside them. Return only the final ASCII diagram in plain text. Do not include markdown fences, explanations, or any extra text.

**source.ascii:**
```text
               +--------+
               | Leader |
               +--------+
          /   /   |   \   \
         v   v    v    v   v
+------------+ +------------+ +------------+ +------------+ +------------+
| Follower-1 | | Follower-2 | | Follower-3 | | Follower-4 | | Follower-5 |
+------------+ +------------+ +------------+ +------------+ +------------+
```

**assertions.json:**
```json
{
  "required_labels": [
    "Leader",
    "Follower-1",
    "Follower-2",
    "Follower-4",
    "Follower-5"
  ],
  "forbidden_labels": [
    "Follower-3"
  ],
  "entity_count": 5,
  "required_edges": [],
  "editing": {
    "required_edge_labels": [],
    "preserved_elements": [
      "Leader",
      "Follower-1",
      "Follower-2",
      "Follower-4",
      "Follower-5"
    ]
  }
}
```

### Task 3.11
**difficulty:** `medium`

**prompt.txt:** Draw an ASCII diagram illustrating preserve `Client`, `API`, `Worker`, `DB`, and `Metrics`, but make three coordinated edits. First, replace the single middle `API` box with two boxes in sequence: `API Gateway` and `App Service`. Second, insert a new `Auth` box directly below `API Gateway` with a downward arrow from `API Gateway` to `Auth`. Third, remove the old direct `API -> Worker` edge and reconnect the main path as `Client -> API Gateway -> App Service -> Worker`, keep `DB` below `Worker`, and place the `Metrics` box as a left-side sidecar below `Client`. Keep the diagram layered and left-to-right where appropriate. When arrows are required, make them centered and aligned cleanly to their source and target. If an arrow has a label, place the label a little above the arrow rather than inside the arrow line. Any component with incoming or outgoing arrows should be sized wide or tall enough to make those connections visually unambiguous, so it is clear where arrows originate and where they terminate. If one component fans out to multiple arrows, or multiple arrows converge into one component, its width or height should clearly support those attachment points. Strictly apply only the requested edits and do not make any other changes outside them. Return only the final ASCII diagram in plain text. Do not include markdown fences, explanations, or any extra text.

**source.ascii:**
```text
+--------+     +-----+     +----------+
| Client |---->| API |---->|  Worker  |
+--------+     +-----+     +----------+
                               |      |
                               v      v
                           +------+ +---------+
                           |  DB  | | Metrics |
                           +------+ +---------+
```

**reference.ascii:**
```text
+--------+   +-------------+   +-------------+   +----------+
| Client |-->| API Gateway |-->| App Service |-->|  Worker  |
+--------+   +-------------+   +-------------+   +----------+
    |            |                                            |
    v            v                                            v
+---------+   +------+                                      +------+
| Metrics |   | Auth |                                      |  DB  |
+---------+   +------+                                      +------+
```

**why medium:** the base diagram is larger, and the edit combines splitting a core node, inserting a new auth dependency, rerouting the main service path, and preserving a downstream fan-out layer.

### Task 3.12
**difficulty:** `medium`

**prompt.txt:** Draw an ASCII diagram illustrating insert an `Aggregator` node between `Leader` and the follower layer. Preserve `Follower-1`, `Follower-2`, `Follower-3`, and `Follower-4`. Remove the old direct fan-out from `Leader` to the followers, connect `Leader -> Aggregator`, and then connect `Aggregator` to all four followers. Also add a `Standby Leader` box to the right of `Leader` connected by a bidirectional link to show a backup leader pair. Keep the follower row unchanged. When arrows are required, make them centered and aligned cleanly to their source and target. If an arrow has a label, place the label a little above the arrow rather than inside the arrow line. Any component with incoming or outgoing arrows should be sized wide or tall enough to make those connections visually unambiguous, so it is clear where arrows originate and where they terminate. If one component fans out to multiple arrows, or multiple arrows converge into one component, its width or height should clearly support those attachment points. Strictly apply only the requested edits and do not make any other changes outside them. Return only the final ASCII diagram in plain text. Do not include markdown fences, explanations, or any extra text.

**source.ascii:**
```text
        +--------------+
        |    Leader    |
        +--------------+
           /     |   |     \
          v      v   v      v
+------------+ +------------+ +------------+ +------------+
| Follower-1 | | Follower-2 | | Follower-3 | | Follower-4 |
+------------+ +------------+ +------------+ +------------+
```

**reference.ascii:**
```text
        +--------------+<------->+----------------+
        |    Leader    |         | Standby Leader |
        +--------------+         +----------------+
                |
                v
          +--------------+
          |  Aggregator  |
          +--------------+
           /     |   |     \
          v      v   v      v
+------------+ +------------+ +------------+ +------------+
| Follower-1 | | Follower-2 | | Follower-3 | | Follower-4 |
+------------+ +------------+ +------------+ +------------+
```

**why medium:** add two nodes, remove the old fan-out, rebuild the follower topology through a new middle tier, and add a peer coordination edge.

### Task 3.13
**difficulty:** `medium`

**prompt.txt:** Draw an ASCII diagram illustrating preserve `Browser`, `API`, `Worker`, `DB`, and `Redis`, but make three coordinated edits of a different kind. First, split the single `Worker` box into two side-by-side boxes: `Worker-A` and `Worker-B`. Second, connect `API` downward to both workers with separate arrows, removing the old single `API -> Worker` path. Third, move `Redis` so it sits centered below the two workers and connect both `Worker-A` and `Worker-B` down to `Redis`, while keeping `Worker-A -> DB` and `Worker-B -> DB` present. Add a multiline second line `v2.4` inside both worker boxes. Keep the overall diagram layered top-to-bottom. When arrows are required, make them centered and aligned cleanly to their source and target. If an arrow has a label, place the label a little above the arrow rather than inside the arrow line. Any component with incoming or outgoing arrows should be sized wide or tall enough to make those connections visually unambiguous, so it is clear where arrows originate and where they terminate. If one component fans out to multiple arrows, or multiple arrows converge into one component, its width or height should clearly support those attachment points. Strictly apply only the requested edits and do not make any other changes outside them. Return only the final ASCII diagram in plain text. Do not include markdown fences, explanations, or any extra text.

**source.ascii:**
```text
+-----------+
|  Browser  |
+-----------+
      |
      v
+-----------+
|    API    |
+-----------+
      |
      v
+-----------+
|  Worker   |
+-----------+
   /   \
  v     v
+----+ +-------+
| DB | | Redis |
+----+ +-------+
```

**reference.ascii:**
```text
+-----------+
|  Browser  |
+-----------+
      |
      v
+-----------+
|    API    |
+-----------+
   /         \
  v           v
+-----------+ +-----------+
| Worker-A  | | Worker-B  |
| v2.4      | | v2.4      |
+-----------+ +-----------+
   |    \       /    |
   |     \     /     |
   v      v   v      v
+----+   +-------+   +----+
| DB |   | Redis |   | DB |
+----+   +-------+   +----+
```

**why medium:** this is no longer the same edit family as `3.11`; it splits one worker into a two-node parallel layer, reroutes fan-out and fan-in edges, moves a shared dependency, and adds multiline content.

### Task 3.14
**difficulty:** `medium`

**prompt.txt:** Draw an ASCII diagram illustrating preserve the existing three-layer architecture, but make three coordinated edits. First, wrap the entire architecture in an outer grouping box labeled `Region: EU`. Second, rename `API Layer` to `API Gateway` and resize its box to fit. Third, add a new `Cache` box to the right of `API Gateway` with a horizontal arrow from `API Gateway` to `Cache`, while preserving the original `Frontend -> API Gateway -> DB Layer` flow and the lower `DB Layer -> Analytics` edge. Keep the inner layout readable and layered. When arrows are required, make them centered and aligned cleanly to their source and target. If an arrow has a label, place the label a little above the arrow rather than inside the arrow line. Any component with incoming or outgoing arrows should be sized wide or tall enough to make those connections visually unambiguous, so it is clear where arrows originate and where they terminate. If one component fans out to multiple arrows, or multiple arrows converge into one component, its width or height should clearly support those attachment points. Strictly apply only the requested edits and do not make any other changes outside them. Return only the final ASCII diagram in plain text. Do not include markdown fences, explanations, or any extra text.

**source.ascii:**
```text
+-----------+   +-----------+
| Frontend  |-->| API Layer |
+-----------+   +-----------+
                    |
                    v
              +-----------+
              |  DB Layer |
              +-----------+
                    |
                    v
              +-----------+
              | Analytics |
              +-----------+
```

**reference.ascii:**
```text
+--------------------------------------------------+
|                    Region: EU                    |
| +-----------+   +-------------+   +---------+   |
| | Frontend  |-->| API Gateway |-->| Cache   |   |
| +-----------+   +-------------+   +---------+   |
|                        |                         |
|                        v                         |
|                  +-----------+                   |
|                  |  DB Layer |                   |
|                  +-----------+                   |
|                        |                         |
|                        v                         |
|                  +-----------+                   |
|                  | Analytics |                   |
|                  +-----------+                   |
+--------------------------------------------------+
```

**why medium:** the base task is larger, and the edit now has to preserve a 4-node layered flow while simultaneously adding a group box, renaming/resizing one node, and branching a new cache dependency.

### Task 3.15
**difficulty:** `medium`

**prompt.txt:** Draw an ASCII diagram illustrating keep `Gateway`, the three outgoing arrows, and the three databases present, but make three coordinated edits. First, convert each service box into a multiline box by adding a version line: `v2.1` under `Auth Service`, `v1.8` under `User Service`, and `v3.0` under `Order Service`. Second, add another internal line `healthy` inside each of the three service boxes. Third, add a new shared `Metrics` box centered below the full service row and connect each of the three services downward to `Metrics`, while preserving the original service-to-database edges. Resize the top `Gateway` box wide enough so its three arrows meet the three service boxes cleanly. Keep both the service row and the lower database row aligned. When arrows are required, make them centered and aligned cleanly to their source and target. If an arrow has a label, place the label a little above the arrow rather than inside the arrow line. Any component with incoming or outgoing arrows should be sized wide or tall enough to make those connections visually unambiguous, so it is clear where arrows originate and where they terminate. If one component fans out to multiple arrows, or multiple arrows converge into one component, its width or height should clearly support those attachment points. Strictly apply only the requested edits and do not make any other changes outside them. Return only the final ASCII diagram in plain text. Do not include markdown fences, explanations, or any extra text.

**source.ascii:**
```text
+------------------------------------------------------+
|                       Gateway                        |
+------------------------------------------------------+
        /                    |                    \
       v                     v                     v
+--------------+      +--------------+      +---------------+
| Auth Service |      | User Service |      | Order Service |
+--------------+      +--------------+      +---------------+
      |                     |                     |
      v                     v                     v
+---------+           +---------+           +---------+
| UsersDB |           | UserDB  |           | OrderDB |
+---------+           +---------+           +---------+
```

**reference.ascii:**
```text
+------------------------------------------------------+
|                       Gateway                        |
+------------------------------------------------------+
        /                    |                    \
       v                     v                     v
+--------------+      +--------------+      +---------------+
| Auth Service |      | User Service |      | Order Service |
| v2.1         |      | v1.8         |      | v3.0          |
| healthy      |      | healthy      |      | healthy       |
+--------------+      +--------------+      +---------------+
      |   \                 |   |                 /   |
      |    \                |   |                /    |
      v     \               v   v               /     v
 +---------+  +----------------+    +---------+  +---------+
 | UsersDB |  |    Metrics     |    | UserDB  |  | OrderDB |
 +---------+  +----------------+    +---------+  +---------+
```

**why medium:** the source graph is larger, the top fan-out now has an alignment requirement, and the edit combines multiline box changes with a new shared dependency while preserving both the gateway fan-out and the existing database layer.

### Task 3.16
**difficulty:** `hard`

**prompt.txt:** Draw an ASCII diagram illustrating preserve `Client`, `Gateway`, `Worker`, `DB`, and `Cache`, but make a hard multi-step edit. Replace the single `Gateway` box with two boxes in sequence: `Edge LB` and `API Gateway`. Add a new `Auth` box directly below `API Gateway`. Split the single `Worker` box into two side-by-side boxes labeled `Worker-A` and `Worker-B`, and add a second line `v2.2` inside both worker boxes. Reconnect the main path as `Client -> Edge LB -> API Gateway`, then fan out from `API Gateway` to both workers. Keep `DB` below `Worker-A` and `Cache` below `Worker-B`. When arrows are required, make them centered and aligned cleanly to their source and target. If an arrow has a label, place the label a little above the arrow rather than inside the arrow line. Any component with incoming or outgoing arrows should be sized wide or tall enough to make those connections visually unambiguous, so it is clear where arrows originate and where they terminate. If one component fans out to multiple arrows, or multiple arrows converge into one component, its width or height should clearly support those attachment points. Strictly apply only the requested edits and do not make any other changes outside them. Return only the final ASCII diagram in plain text. Do not include markdown fences, explanations, or any extra text.

**source.ascii:**
```text
+-----------+   +---------+   +----------+
|  Client   |-->| Gateway |-->|  Worker  |
+-----------+   +---------+   +----------+
                                  |      |
                                  v      v
                              +------+ +-------+
                              |  DB  | | Cache |
                              +------+ +-------+
```

**reference.ascii:**
```text
+-----------+   +---------+   +-------------+
|  Client   |-->| Edge LB |-->| API Gateway |
+-----------+   +---------+   +-------------+
                                   |      \
                                   v       v
                               +------+ +-----------+   +-----------+
                               | Auth | | Worker-A  | | Worker-B  |
                               +------+ | v2.2      | | v2.2      |
                                        +-----------+ +-----------+
                                             |             |
                                             v             v
                                          +------+      +-------+
                                          |  DB  |      | Cache |
                                          +------+      +-------+
```

**why hard:** replace the gateway layer, insert a new auth dependency, split one worker into two multiline boxes, reroute the full main path, and preserve the lower storage layer with new placements.

### Task 3.17
**difficulty:** `hard`

**prompt.txt:** Draw an ASCII diagram illustrating preserve the four follower boxes, but make a hard topology rewrite. Add a new `Standby Leader` box to the right of `Leader` connected by a bidirectional link. Insert a `Control Bus` box below Leader. Replace the old one-to-four fan-out with two mid-layer boxes labeled `Aggregator-A` and `Aggregator-B` connected downward from Control Bus. Add a bidirectional sync link between `Aggregator-A` and `Aggregator-B`. Reconnect `Aggregator-A` to `Follower-1` and `Follower-2`, and reconnect `Aggregator-B` to `Follower-3` and `Follower-4`. When arrows are required, make them centered and aligned cleanly to their source and target. If an arrow has a label, place the label a little above the arrow rather than inside the arrow line. Any component with incoming or outgoing arrows should be sized wide or tall enough to make those connections visually unambiguous, so it is clear where arrows originate and where they terminate. If one component fans out to multiple arrows, or multiple arrows converge into one component, its width or height should clearly support those attachment points. Strictly apply only the requested edits and do not make any other changes outside them. Return only the final ASCII diagram in plain text. Do not include markdown fences, explanations, or any extra text.

**source.ascii:**
```text
        +--------------+
        |    Leader    |
        +--------------+
           /     |   |     \
          v      v   v      v
+------------+ +------------+ +------------+ +------------+
| Follower-1 | | Follower-2 | | Follower-3 | | Follower-4 |
+------------+ +------------+ +------------+ +------------+
```

**reference.ascii:**
```text
        +--------------+<------->+----------------+
        |    Leader    |         | Standby Leader |
        +--------------+         +----------------+
                |
                v
          +--------------+
          | Control Bus  |
          +--------------+
             /                    \
            v                      v
     +--------------+<---------->+--------------+
     | Aggregator-A |            | Aggregator-B |
     +--------------+            +--------------+
        /        \                  /        \
       v          v                v          v
+------------+ +------------+ +------------+ +------------+
| Follower-1 | | Follower-2 | | Follower-3 | | Follower-4 |
+------------+ +------------+ +------------+ +------------+
```

**why hard:** add a peer leader, insert two new middle tiers, replace a one-to-four fan-out with a two-branch topology, and add a bidirectional sync dependency between the aggregators.

### Task 3.18
**difficulty:** `hard`

**prompt.txt:** Draw an ASCII diagram illustrating preserve `Client`, `Ingest API`, and `Warehouse`, but make a hard streaming-pipeline edit. Replace the single `Processor` box with a streaming layer. Insert a new `Kafka` box directly below `Ingest API`. Add a new `DLQ` box to the right of Kafka connected horizontally from Kafka. Split the old processor into two boxes in sequence: `Parser` and `Enricher`. Add a second line `stateless` inside both Parser and Enricher. Reconnect the main path as `Client -> Ingest API -> Kafka -> Parser -> Enricher -> Warehouse`. When arrows are required, make them centered and aligned cleanly to their source and target. If an arrow has a label, place the label a little above the arrow rather than inside the arrow line. Any component with incoming or outgoing arrows should be sized wide or tall enough to make those connections visually unambiguous, so it is clear where arrows originate and where they terminate. If one component fans out to multiple arrows, or multiple arrows converge into one component, its width or height should clearly support those attachment points. Strictly apply only the requested edits and do not make any other changes outside them. Return only the final ASCII diagram in plain text. Do not include markdown fences, explanations, or any extra text.

**source.ascii:**
```text
+--------+   +------------+   +-----------+
| Client |-->| Ingest API |-->| Processor |
+--------+   +------------+   +-----------+
                                   |
                                   v
                              +-----------+
                              | Warehouse |
                              +-----------+
```

**reference.ascii:**
```text
+--------+   +------------+
| Client |-->| Ingest API |
+--------+   +------------+
                  |
                  v
            +-----------+------->+-----+
            |   Kafka   |        | DLQ |
            +-----------+        +-----+
                  |
                  v
            +-----------+    +-----------+
            |  Parser   |--->| Enricher  |
            | stateless |    | stateless |
            +-----------+    +-----------+
                                  |
                                  v
                             +-----------+
                             | Warehouse |
                             +-----------+
```

**why hard:** preserve the client, ingress, and warehouse endpoints, insert a new queueing layer, add a DLQ branch, split one processor into two stages, and add multiline node text while rerouting the full processing path.

### Task 3.19
**difficulty:** `hard`

**prompt.txt:** Draw an ASCII diagram illustrating preserve the existing API and worker boxes, but make a hard orchestration edit. Wrap the full diagram in one outer box labeled `Region: Batch Ops`. Insert a new box labeled `Scheduler` directly below `API`. Add a new box labeled `Audit Log` to the right of `Scheduler` connected by a horizontal arrow from Scheduler. Move `Queue` to the left and `Cache` to the right below Scheduler. Reconnect the lower edges so Queue points to `WorkerB` and Cache points to `WorkerA`. When arrows are required, make them centered and aligned cleanly to their source and target. If an arrow has a label, place the label a little above the arrow rather than inside the arrow line. Any component with incoming or outgoing arrows should be sized wide or tall enough to make those connections visually unambiguous, so it is clear where arrows originate and where they terminate. If one component fans out to multiple arrows, or multiple arrows converge into one component, its width or height should clearly support those attachment points. Strictly apply only the requested edits and do not make any other changes outside them. Return only the final ASCII diagram in plain text. Do not include markdown fences, explanations, or any extra text.

**source.ascii:**
```text
+---------+
|   API   |
+---------+
  /     \
 v       v
+-------+ +-------+
| Cache | | Queue |
+-------+ +-------+
  |           |
  v           v
+---------+ +---------+
| WorkerA | | WorkerB |
+---------+ +---------+
```

**reference.ascii:**
```text
+--------------------------------------------------+
|                Region: Batch Ops                 |
|            +---------+                           |
|            |   API   |                           |
|            +---------+                           |
|                 |                                |
|                 v                                |
|            +-----------+      +-----------+      |
|            | Scheduler |----->| Audit Log |      |
|            +-----------+      +-----------+      |
|              /       \                          |
|             v         v                          |
|        +-------+  +-------+                     |
|        | Queue |  | Cache |                     |
|        +-------+  +-------+                     |
|           |           |                         |
|           v           v                         |
|       +---------+ +---------+                   |
|       | WorkerB | | WorkerA |                   |
|       +---------+ +---------+                   |
+--------------------------------------------------+
```

**why hard:** preserve the top and bottom layers, wrap the whole system in a region box, insert a new orchestration node, add a side log dependency, and reroute the full middle layer.

### Task 3.20
**difficulty:** `hard`

**prompt.txt:** Draw an ASCII diagram illustrating preserve `API App`, `Billing`, and `Analytics`, but make a hard database-topology edit. Insert a new box labeled `API Gateway` between `API App` and the database layer. Replace the single `Database` box with two boxes side by side: `Write Primary` on the left and `Read Replica` on the right. Add an arrow from `Write Primary` to `Read Replica` labeled `replication`. Add a new box labeled `CDC Queue` below `Read Replica`. Connect `API Gateway` down to both database boxes. Keep `Billing` below `Write Primary`, and reconnect `Analytics` so it sits below `CDC Queue` instead of directly below the old `Database` box. When arrows are required, make them centered and aligned cleanly to their source and target. If an arrow has a label, place the label a little above the arrow rather than inside the arrow line. Any component with incoming or outgoing arrows should be sized wide or tall enough to make those connections visually unambiguous, so it is clear where arrows originate and where they terminate. If one component fans out to multiple arrows, or multiple arrows converge into one component, its width or height should clearly support those attachment points. Strictly apply only the requested edits and do not make any other changes outside them. Return only the final ASCII diagram in plain text. Do not include markdown fences, explanations, or any extra text.

**source.ascii:**
```text
     +----------+
     | API App  |
     +----------+
          |
          v
     +----------+
     | Database |
     +----------+
      /       \
     v         v
+----------+ +-----------+
| Billing  | | Analytics |
+----------+ +-----------+
```

**reference.ascii:**
```text
           +----------+
           | API App  |
           +----------+
                |
                v
         +-------------+
         | API Gateway |
         +-------------+
             /      \
            v        v
+---------------+ replication +--------------+
| Write Primary |----------->| Read Replica |
+---------------+            +--------------+
      |                              |
      v                              v
+----------+                   +-----------+
| Billing  |                   | CDC Queue |
+----------+                   +-----------+
                                      |
                                      v
                                 +-----------+
                                 | Analytics |
                                 +-----------+
```

**why hard:** insert a new gateway layer, replace one database node with two, add a labeled replication edge, introduce a CDC stage, and reroute the downstream analytics path.

## Category 4: Software Architecture Diagrams

### Task 4.1
**difficulty:** `easy`

**prompt.txt:** Draw a modern web application architecture with a user traffic path from "Client (Browser)" to "CDN / WAF" to "Load Balancer". Place two app nodes, "App-1" and "App-2", below the load balancer. Both apps must connect to both "Redis Session Cache" and "PostgreSQL" in a storage layer below them.

**assertions.json:**
```json
{
  "required_labels": [
    "Client (Browser)",
    "CDN / WAF",
    "Load Balancer",
    "App-1",
    "App-2",
    "Redis Session Cache",
    "PostgreSQL"
  ],
  "forbidden_labels": [],
  "entity_count": 7,
  "required_edges": [
    {
      "from": "Client (Browser)",
      "to": "CDN / WAF"
    },
    {
      "from": "CDN / WAF",
      "to": "Load Balancer"
    },
    {
      "from": "Load Balancer",
      "to": "App-1"
    },
    {
      "from": "Load Balancer",
      "to": "App-2"
    },
    {
      "from": "App-1",
      "to": "Redis Session Cache"
    },
    {
      "from": "App-2",
      "to": "Redis Session Cache"
    },
    {
      "from": "App-1",
      "to": "PostgreSQL"
    },
    {
      "from": "App-2",
      "to": "PostgreSQL"
    }
  ],
  "required_edge_labels": [],
  "preserved_elements": []
}
```

**reference.ascii:**
```text
+------------------+     +-------------+     +---------------+
| Client (Browser) |---->|  CDN / WAF  |---->| Load Balancer |
+------------------+     +-------------+     +---------------+
                                                  |       |
                                                  v       v
                                             +---------+ +---------+
                                             |  App-1  | |  App-2  |
                                             +---------+ +---------+
                                                |   \     /   |
                                                |    \   /    |
                                                v     v v     v
                                        +---------------------+  +------------+
                                        | Redis Session Cache |  | PostgreSQL |
                                        +---------------------+  +------------+
```

### Task 4.2
**difficulty:** `easy`

**prompt.txt:** Draw a read-heavy orders API architecture with "Client App" calling "Orders API" using an arrow labeled "HTTPS request". Orders API writes to "Primary MySQL" using an arrow labeled "write". Make the "Primary MySQL" box wide enough so each outgoing arrow clearly attaches to a distinct point on the box. Primary MySQL must replicate to both "Read Replica-1" and "Read Replica-2" using arrows labeled "async replication". Primary MySQL must also connect down to "Snapshot Worker" using an arrow labeled "snapshot job", and Snapshot Worker must write to "S3 Backup" using an arrow labeled "backup upload". Keep the primary centered above the snapshot worker and the two replicas on its left and right.

**assertions.json:**
```json
{
  "required_labels": [
    "Client App",
    "Orders API",
    "Primary MySQL",
    "Read Replica-1",
    "Read Replica-2",
    "Snapshot Worker",
    "S3 Backup",
    "HTTPS request",
    "write",
    "async replication",
    "snapshot job",
    "backup upload"
  ],
  "forbidden_labels": [],
  "entity_count": 7,
  "required_edges": [
    {
      "from": "Client App",
      "to": "Orders API"
    },
    {
      "from": "Orders API",
      "to": "Primary MySQL"
    },
    {
      "from": "Primary MySQL",
      "to": "Read Replica-1"
    },
    {
      "from": "Primary MySQL",
      "to": "Read Replica-2"
    },
    {
      "from": "Primary MySQL",
      "to": "Snapshot Worker"
    },
    {
      "from": "Snapshot Worker",
      "to": "S3 Backup"
    }
  ],
  "required_edge_labels": [
    "HTTPS request",
    "write",
    "async replication",
    "snapshot job",
    "backup upload"
  ],
  "preserved_elements": []
}
```

**reference.ascii:**
```text
+------------+      HTTPS request      +------------+
| Client App |------------------------>| Orders API |
+------------+                         +------------+
                                              |
                                            write
                                              v
                          +-----------------------------------+
                          |           Primary MySQL           |
                          +-----------------------------------+
                               |               |               |
                       async replication  snapshot job  async replication
                               v               v               v
                     +----------------+ +-----------------+ +----------------+
                     | Read Replica-1 | | Snapshot Worker | | Read Replica-2 |
                     +----------------+ +-----------------+ +----------------+
                                               |
                                          backup upload
                                               v
                                         +-----------+
                                         | S3 Backup |
                                         +-----------+
```


### Task 4.3
**difficulty:** `easy`

**prompt.txt:** Draw an event-driven checkout architecture. Put "Web Client" on the left, then "API Gateway", then "Order Service". Below Order Service, place "Orders DB" and "Kafka". Kafka must fan out to "Payment Worker", "Inventory Worker", and "Email Worker" on the bottom row. Order Service writes to Orders DB and publishes to Kafka.

**assertions.json:**
```json
{
  "required_labels": [
    "Web Client",
    "API Gateway",
    "Order Service",
    "Orders DB",
    "Kafka",
    "Payment Worker",
    "Inventory Worker",
    "Email Worker"
  ],
  "forbidden_labels": [],
  "entity_count": 8,
  "required_edges": [
    {
      "from": "Web Client",
      "to": "API Gateway"
    },
    {
      "from": "API Gateway",
      "to": "Order Service"
    },
    {
      "from": "Order Service",
      "to": "Orders DB"
    },
    {
      "from": "Order Service",
      "to": "Kafka"
    },
    {
      "from": "Kafka",
      "to": "Payment Worker"
    },
    {
      "from": "Kafka",
      "to": "Inventory Worker"
    },
    {
      "from": "Kafka",
      "to": "Email Worker"
    }
  ],
  "required_edge_labels": [],
  "preserved_elements": []
}
```

**reference.ascii:**
```text
+------------+     +-------------+     +---------------+
| Web Client |---->| API Gateway |---->| Order Service |
+------------+     +-------------+     +---------------+
                                             |       |
                                             v       v
                                       +-----------+ +-------+
                                       | Orders DB | | Kafka |
                                       +-----------+ +-------+
                                                     |   |   |
                                                     v   v   v
                                            +--------------+ +------------------+ +--------------+
                                            | Payment Worker| | Inventory Worker | | Email Worker |
                                            +--------------+ +------------------+ +--------------+
```

### Task 4.4
**difficulty:** `easy`

**prompt.txt:** Draw a CDN delivery architecture with "Users (Global)" sending traffic to "Geo DNS". From Geo DNS, route to two edge nodes, "Edge Cache (US)" and "Edge Cache (EU)", using arrows labeled "cached". Both edge caches connect to "Origin API" using arrows labeled "cache miss". Origin API then reads from "Object Store" below it.

**assertions.json:**
```json
{
  "required_labels": [
    "Users (Global)",
    "Geo DNS",
    "Edge Cache (US)",
    "Edge Cache (EU)",
    "Origin API",
    "Object Store",
    "cached",
    "cache miss"
  ],
  "forbidden_labels": [],
  "entity_count": 6,
  "required_edges": [
    {
      "from": "Users (Global)",
      "to": "Geo DNS"
    },
    {
      "from": "Geo DNS",
      "to": "Edge Cache (US)"
    },
    {
      "from": "Geo DNS",
      "to": "Edge Cache (EU)"
    },
    {
      "from": "Edge Cache (US)",
      "to": "Origin API"
    },
    {
      "from": "Edge Cache (EU)",
      "to": "Origin API"
    },
    {
      "from": "Origin API",
      "to": "Object Store"
    }
  ],
  "required_edge_labels": [
    "cached",
    "cache miss"
  ],
  "preserved_elements": []
}
```

**reference.ascii:**
```text
+----------------+     +----------+
| Users (Global) |---->| Geo DNS  |
+----------------+     +----------+
                           |    |
                    cached |    | cached
                           v    v
                  +-----------------+   +-----------------+
                  | Edge Cache (US) |   | Edge Cache (EU) |
                  +-----------------+   +-----------------+
                           \               /
                            \             /
                       cache miss\       //cache miss
                              \     //
                               v   v
                           +------------+
                           | Origin API |
                           +------------+
                                 |
                                 v
                           +--------------+
                           | Object Store |
                           +--------------+
```

### Task 4.5
**difficulty:** `easy`

**prompt.txt:** Draw a URL shortener architecture with "Client" calling "API Gateway", which forwards to a single "Shortener Service". Shortener Service must check "Redis Cache" first using a path labeled "cache hit", query "Cassandra DB" using a path labeled "cache miss", and publish click events to "Kafka". Kafka then sends events to "Analytics Worker".

**assertions.json:**
```json
{
  "required_labels": [
    "Client",
    "API Gateway",
    "Shortener Service",
    "Redis Cache",
    "Cassandra DB",
    "Kafka",
    "Analytics Worker",
    "cache hit",
    "cache miss"
  ],
  "forbidden_labels": [],
  "entity_count": 7,
  "required_edges": [
    {
      "from": "Client",
      "to": "API Gateway"
    },
    {
      "from": "API Gateway",
      "to": "Shortener Service"
    },
    {
      "from": "Shortener Service",
      "to": "Redis Cache"
    },
    {
      "from": "Shortener Service",
      "to": "Cassandra DB"
    },
    {
      "from": "Shortener Service",
      "to": "Kafka"
    },
    {
      "from": "Kafka",
      "to": "Analytics Worker"
    }
  ],
  "required_edge_labels": [
    "cache hit",
    "cache miss"
  ],
  "preserved_elements": []
}
```

**reference.ascii:**
```text
+--------+     +-------------+     +-------------------+
| Client |---->| API Gateway |---->| Shortener Service |
+--------+     +-------------+     +-------------------+
                                          |      |      |
                                          v      v      v
                                  +-------------+ +--------------+ +-------+
                                  | Redis Cache | | Cassandra DB | | Kafka |
                                  +-------------+ +--------------+ +-------+
                                    cache hit      cache miss         |
                                                                      v
                                                            +------------------+
                                                            | Analytics Worker |
                                                            +------------------+
```

### Task 4.6
**difficulty:** `easy`

**prompt.txt:** Draw an API protection architecture with "Client" on the left, "API Gateway" in the middle, and "App Service" leading to "PostgreSQL" on the right. Inside the API Gateway box, add a centered second line reading "Auth + RL". Place "Redis Counters" below the gateway. Show rejected traffic returning from API Gateway back to Client labeled "401 / 429".

**assertions.json:**
```json
{
  "required_labels": [
    "Client",
    "API Gateway",
    "Auth + RL",
    "Redis Counters",
    "App Service",
    "PostgreSQL",
    "401 / 429"
  ],
  "forbidden_labels": [],
  "entity_count": 5,
  "required_edges": [
    {
      "from": "Client",
      "to": "API Gateway"
    },
    {
      "from": "API Gateway",
      "to": "Redis Counters"
    },
    {
      "from": "API Gateway",
      "to": "App Service"
    },
    {
      "from": "App Service",
      "to": "PostgreSQL"
    },
    {
      "from": "API Gateway",
      "to": "Client"
    }
  ],
  "required_edge_labels": [
    "401 / 429"
  ],
  "preserved_elements": []
}
```

**reference.ascii:**
```text
+--------+     +---------------+     +-------------+     +------------+
| Client |---->|  API Gateway  |---->| App Service |---->| PostgreSQL |
+--------+     |   Auth + RL   |     +-------------+     +------------+
     ^         +---------------+
     |                |
401 / 429             v
     |         +----------------+
     +---------| Redis Counters |
               +----------------+
```

### Task 4.7
**difficulty:** `easy`

**prompt.txt:** Draw a notification delivery architecture where "Order Service", "Payment Service", and "Shipping Service" all publish into "Kafka". Kafka feeds "Notification Service". Notification Service must connect to five components below it: "Email Service", "SMS Service", "Push Service", "User Preferences DB", and "Template Store". Then connect Email Service to "SendGrid", SMS Service to "Twilio", and Push Service to "FCM".

**assertions.json:**
```json
{
  "required_labels": [
    "Order Service",
    "Payment Service",
    "Shipping Service",
    "Kafka",
    "Notification Service",
    "User Preferences DB",
    "Template Store",
    "Email Service",
    "SMS Service",
    "Push Service",
    "SendGrid",
    "Twilio",
    "FCM"
  ],
  "forbidden_labels": [],
  "entity_count": 13,
  "required_edges": [
    {
      "from": "Order Service",
      "to": "Kafka"
    },
    {
      "from": "Payment Service",
      "to": "Kafka"
    },
    {
      "from": "Shipping Service",
      "to": "Kafka"
    },
    {
      "from": "Kafka",
      "to": "Notification Service"
    },
    {
      "from": "Notification Service",
      "to": "User Preferences DB"
    },
    {
      "from": "Notification Service",
      "to": "Template Store"
    },
    {
      "from": "Notification Service",
      "to": "Email Service"
    },
    {
      "from": "Notification Service",
      "to": "SMS Service"
    },
    {
      "from": "Notification Service",
      "to": "Push Service"
    },
    {
      "from": "Email Service",
      "to": "SendGrid"
    },
    {
      "from": "SMS Service",
      "to": "Twilio"
    },
    {
      "from": "Push Service",
      "to": "FCM"
    }
  ],
  "required_edge_labels": [],
  "preserved_elements": []
}
```

**reference.ascii:**
```text
+---------------+ +-----------------+ +------------------+
| Order Service | | Payment Service | | Shipping Service |
+---------------+ +-----------------+ +------------------+
        \               |                //
         \              |               //
          v             v              v
                  +-------+
                  | Kafka |
                  +-------+
                      |
                      v
     +---------------------------------------------------------------+
     |                     Notification Service                       |
     +---------------------------------------------------------------+
       |          |          |              |                 |
       v          v          v              v                 v
+---------------+ +-------------+ +--------------+ +---------------------+ +----------------+
| Email Service | | SMS Service | | Push Service | | User Preferences DB | | Template Store |
+---------------+ +-------------+ +--------------+ +---------------------+ +----------------+
      |                |                |
      v                v                v
+----------+      +--------+      +------+
| SendGrid |      | Twilio |      | FCM  |
+----------+      +--------+      +------+
```

### Task 4.8
**difficulty:** `easy`

**prompt.txt:** Draw a microservices gateway architecture with "Mobile Client" and "Web Client" both connecting into "API Gateway". Inside the API Gateway box, add centered internal lines for "Auth Middleware" and "Rate Limiter". The gateway must route independently to "User Service", "Catalog Service", and "Order Service", and each service must connect to its own database: "Users DB", "Products DB", and "Orders DB".

**assertions.json:**
```json
{
  "required_labels": [
    "Mobile Client",
    "Web Client",
    "API Gateway",
    "Auth Middleware",
    "Rate Limiter",
    "User Service",
    "Users DB",
    "Catalog Service",
    "Products DB",
    "Order Service",
    "Orders DB"
  ],
  "forbidden_labels": [],
  "entity_count": 11,
  "required_edges": [
    {
      "from": "Mobile Client",
      "to": "API Gateway"
    },
    {
      "from": "Web Client",
      "to": "API Gateway"
    },
    {
      "from": "API Gateway",
      "to": "User Service"
    },
    {
      "from": "API Gateway",
      "to": "Catalog Service"
    },
    {
      "from": "API Gateway",
      "to": "Order Service"
    },
    {
      "from": "User Service",
      "to": "Users DB"
    },
    {
      "from": "Catalog Service",
      "to": "Products DB"
    },
    {
      "from": "Order Service",
      "to": "Orders DB"
    }
  ],
  "required_edge_labels": [],
  "preserved_elements": []
}
```

**reference.ascii:**
```text
+---------------+      +-------------------------------+
| Mobile Client |----->|          API Gateway          |
+---------------+      |       Auth Middleware         |
                       |         Rate Limiter          |
+------------+-------->|                               |
| Web Client |         +-------------------------------+
+------------+              |        |        |
                             v        v        v
                      +--------------+ +----------------+ +---------------+
                      | User Service | | Catalog Service| | Order Service |
                      +--------------+ +----------------+ +---------------+
                             |                |                 |
                             v                v                 v
                        +----------+     +-------------+    +-----------+
                        | Users DB |     | Products DB |    | Orders DB |
                        +----------+     +-------------+    +-----------+
```

### Task 4.9
**difficulty:** `easy`

**prompt.txt:** Draw a file storage architecture with "Client (Desktop)" uploading into "Upload Service". Upload Service must write to both "S3 (Block Store)" and "Metadata DB (PostgreSQL)", and also send files to "Virus Scan Worker". Place "Download Service" below so it reads from both S3 and Metadata DB. Separately, place "Sync Service" feeding into "Notification Queue (Kafka)", which notifies the client.

**assertions.json:**
```json
{
  "required_labels": [
    "Client (Desktop)",
    "Upload Service",
    "S3 (Block Store)",
    "Metadata DB (PostgreSQL)",
    "Virus Scan Worker",
    "Download Service",
    "Sync Service",
    "Notification Queue (Kafka)"
  ],
  "forbidden_labels": [],
  "entity_count": 8,
  "required_edges": [
    {
      "from": "Client (Desktop)",
      "to": "Upload Service"
    },
    {
      "from": "Upload Service",
      "to": "S3 (Block Store)"
    },
    {
      "from": "Upload Service",
      "to": "Metadata DB (PostgreSQL)"
    },
    {
      "from": "Upload Service",
      "to": "Virus Scan Worker"
    },
    {
      "from": "Download Service",
      "to": "S3 (Block Store)"
    },
    {
      "from": "Download Service",
      "to": "Metadata DB (PostgreSQL)"
    },
    {
      "from": "Sync Service",
      "to": "Notification Queue (Kafka)"
    },
    {
      "from": "Notification Queue (Kafka)",
      "to": "Client (Desktop)"
    }
  ],
  "required_edge_labels": [],
  "preserved_elements": []
}
```

**reference.ascii:**
```text
+------------------+     +----------------+
| Client (Desktop) |---->| Upload Service |
+------------------+     +----------------+
                              |      |      |
                              v      v      v
                   +------------------+ +--------------------------+ +------------------+
                   | S3 (Block Store) | | Metadata DB (PostgreSQL) | | Virus Scan Worker|
                   +------------------+ +--------------------------+ +------------------+
                              ^                 ^
                              |                 |
                       +---------------------------+
                       |     Download Service      |
                       +---------------------------+

                 +-------------+     +---------------------------+     +------------------+
                 | Sync Service |---->| Notification Queue (Kafka)|---->| Client (Desktop) |
                 +-------------+     +---------------------------+     +------------------+
```

### Task 4.10
**difficulty:** `easy`

**prompt.txt:** Draw a search autocomplete architecture where "User" sends requests to "Search API" and receives responses back. Search API checks "Trie Cache (In-Memory)" and "Prefix Index (Elasticsearch)" below it. Under those, place "Index Builder", and below that place "Query Logs DB" and "Product Catalog". Query Logs DB and Product Catalog both feed Index Builder, and Index Builder rebuilds both the Trie Cache and Prefix Index.

**assertions.json:**
```json
{
  "required_labels": [
    "User",
    "Search API",
    "Trie Cache (In-Memory)",
    "Prefix Index (Elasticsearch)",
    "Index Builder",
    "Query Logs DB",
    "Product Catalog"
  ],
  "forbidden_labels": [],
  "entity_count": 7,
  "required_edges": [
    {
      "from": "User",
      "to": "Search API"
    },
    {
      "from": "Search API",
      "to": "User"
    },
    {
      "from": "Search API",
      "to": "Trie Cache (In-Memory)"
    },
    {
      "from": "Search API",
      "to": "Prefix Index (Elasticsearch)"
    },
    {
      "from": "Index Builder",
      "to": "Trie Cache (In-Memory)"
    },
    {
      "from": "Index Builder",
      "to": "Prefix Index (Elasticsearch)"
    },
    {
      "from": "Query Logs DB",
      "to": "Index Builder"
    },
    {
      "from": "Product Catalog",
      "to": "Index Builder"
    }
  ],
  "required_edge_labels": [],
  "preserved_elements": []
}
```

**reference.ascii:**
```text
+------+<----+------------+
| User |---->| Search API |
+------+     +------------+
               |      |
               v      v
  +-----------------------+   +-----------------------------+
  | Trie Cache (In-Memory)|   | Prefix Index (Elasticsearch)|
  +-----------------------+   +-----------------------------+
               ^                     ^
               |                     |
          +-------------------------------+
          |          Index Builder        |
          +-------------------------------+
               ^                     ^
               |                     |
      +---------------+      +----------------+
      | Query Logs DB |      | Product Catalog|
      +---------------+      +----------------+
```

### Task 4.11
**difficulty:** `medium`

**prompt.txt:** Draw the Twitter/X news feed architecture using a hybrid fan-out strategy. At the top left, place a box labeled "User". Connect it to a box labeled "Tweet Service" with an arrow labeled "Post Tweet". Connect "Tweet Service" to "Tweets DB (Cassandra)" with an arrow labeled "Store Tweet". Also connect "Tweet Service" to "Kafka" with an arrow labeled "Publish Tweet Event". Connect "Kafka" to "Fan-out Service" with an arrow labeled "Consume Event". From "Fan-out Service", draw an arrow to "Social Graph DB" labeled "Lookup Followers". Then draw an arrow from "Fan-out Service" to "Feed Cache (Redis)" labeled "fan-out on write". For timeline reads, place a "Feed Service" box below. Connect "User" to "Feed Service" with an arrow labeled "Read Timeline". Connect "Feed Service" to "Feed Cache (Redis)" with an arrow labeled "Read Feed". Also connect "Feed Service" directly to "Tweets DB (Cassandra)" with an arrow labeled "fan-out on read (celebrities / cache miss)". Finally, draw an arrow from "Feed Service" back to "User" labeled "Return Timeline". Do not draw any direct connection from "User" to "Kafka", "Tweets DB (Cassandra)", "Feed Cache (Redis)", or "Social Graph DB". Use only ASCII boxes, arrows, and text labels.

**assertions.json:**
```json
{
  "required_labels": [
    "User",
    "Tweet Service",
    "Tweets DB (Cassandra)",
    "Kafka",
    "Fan-out Service",
    "Social Graph DB",
    "Feed Cache (Redis)",
    "Feed Service",
    "Post Tweet",
    "Store Tweet",
    "Publish Tweet Event",
    "Consume Event",
    "Lookup Followers",
    "fan-out on write",
    "Read Timeline",
    "Read Feed",
    "fan-out on read (celebrities / cache miss)",
    "Return Timeline"
  ],
  "forbidden_labels": [],
  "entity_count": 8,
  "required_edges": [
    {
      "from": "User",
      "to": "Tweet Service"
    },
    {
      "from": "Tweet Service",
      "to": "Tweets DB (Cassandra)"
    },
    {
      "from": "Tweet Service",
      "to": "Kafka"
    },
    {
      "from": "Kafka",
      "to": "Fan-out Service"
    },
    {
      "from": "Fan-out Service",
      "to": "Social Graph DB"
    },
    {
      "from": "Fan-out Service",
      "to": "Feed Cache (Redis)"
    },
    {
      "from": "User",
      "to": "Feed Service"
    },
    {
      "from": "Feed Service",
      "to": "Feed Cache (Redis)"
    },
    {
      "from": "Feed Service",
      "to": "Tweets DB (Cassandra)"
    },
    {
      "from": "Feed Service",
      "to": "User"
    }
  ],
  "required_edge_labels": [
    "Post Tweet",
    "Store Tweet",
    "Publish Tweet Event",
    "Consume Event",
    "Lookup Followers",
    "fan-out on write",
    "Read Timeline",
    "Read Feed",
    "fan-out on read (celebrities / cache miss)",
    "Return Timeline"
  ],
  "preserved_elements": []
}
```

**reference.ascii:**
```text
+------+      Post Tweet      +---------------+
| User |--------------------->| Tweet Service |
+------+                      +---------------+
   |                                  |
   |                           Store Tweet
   |                                  v
   |                     +------------------------+
   |                     | Tweets DB (Cassandra)  |
   |                     +------------------------+
   |                                  ^
   |                          Publish Tweet Event
   |                                  |
   |                              +-------+
   |                              | Kafka |
   |                              +-------+
   |                                  |
   |                            Consume Event
   |                                  v
   |                         +-----------------+
   |                         | Fan-out Service |
   |                         +-----------------+
   |                            |           |
   |                    Lookup Followers  fan-out on write
   |                            v           v
   |               +-------------------+ +-------------------+
   |               |  Social Graph DB  | | Feed Cache (Redis)|
   |               +-------------------+ +-------------------+
   |                                         ^
   |                                     Read Feed
   |                                         |
   |          Read Timeline          +--------------+
   +-------------------------------->| Feed Service |
                                      +--------------+
                                            |
           Return Timeline                  |  fan-out on read (celebrities / cache miss)
<-------------------------------------------+------------------------------+
                                                                    |
                                                                    v
                                                         +------------------------+
                                                         | Tweets DB (Cassandra)  |
                                                         +------------------------+
```


### Task 4.12
**difficulty:** `medium`

**prompt.txt:** Draw a video upload and streaming pipeline for a production system where direct end-user access to storage has been removed. "User" uploads raw video to "Upload Service". Upload Service stores in "Raw Storage (S3)" using an arrow labeled "store raw" and queues a job in "Transcoding Queue (Kafka)" using an arrow labeled "enqueue job". Three "Transcoder Worker" boxes consume from Kafka using arrows labeled "consume" and write output to "Processed Storage (S3)" using arrows labeled "transcode output". "CDN" pulls from Processed Storage using an arrow labeled "origin pull" and serves video to User using an arrow labeled "stream video". "Metadata Service" receives stage updates from "Upload Service", "Transcoding Queue (Kafka)", and "Processed Storage (S3)" using arrows labeled "stage update", then updates "Video DB" using an arrow labeled "upsert metadata". Do not show the user talking directly to S3 or bypassing the upload or streaming services.

**assertions.json:**
```json
{
  "required_labels": [
    "User",
    "Upload Service",
    "Raw Storage (S3)",
    "Transcoding Queue (Kafka)",
    "Transcoder Worker",
    "Processed Storage (S3)",
    "CDN",
    "Metadata Service",
    "Video DB",
    "store raw",
    "enqueue job",
    "consume",
    "transcode output",
    "origin pull",
    "stream video",
    "stage update",
    "upsert metadata"
  ],
  "forbidden_labels": [],
  "entity_count": 11,
  "required_edges": [
    {
      "from": "User",
      "to": "Upload Service"
    },
    {
      "from": "Upload Service",
      "to": "Raw Storage (S3)"
    },
    {
      "from": "Upload Service",
      "to": "Transcoding Queue (Kafka)"
    },
    {
      "from": "Upload Service",
      "to": "Metadata Service"
    },
    {
      "from": "Transcoding Queue (Kafka)",
      "to": "Metadata Service"
    },
    {
      "from": "Transcoding Queue (Kafka)",
      "to": "Transcoder Worker"
    },
    {
      "from": "Transcoder Worker",
      "to": "Processed Storage (S3)"
    },
    {
      "from": "Processed Storage (S3)",
      "to": "Metadata Service"
    },
    {
      "from": "Metadata Service",
      "to": "Video DB"
    },
    {
      "from": "Processed Storage (S3)",
      "to": "CDN"
    },
    {
      "from": "CDN",
      "to": "User"
    }
  ],
  "required_edge_labels": [
    "store raw",
    "enqueue job",
    "consume",
    "transcode output",
    "origin pull",
    "stream video",
    "stage update",
    "upsert metadata"
  ],
  "preserved_elements": []
}
```

**reference.ascii:**
```text
+------+      upload raw video      +----------------+      stage update      +------------------+
| User |--------------------------->| Upload Service |------------------------>| Metadata Service |
+------+                            +----------------+                         +------------------+
                                         |         |                                   |
                                     store raw  enqueue job                       upsert metadata
                                         v         v                                   v
                           +------------------+  +----------------------------+    +----------+
                           | Raw Storage (S3) |  | Transcoding Queue (Kafka)  |    | Video DB |
                           +------------------+  +----------------------------+    +----------+
                                                      |            |            |
                                                   consume       consume      consume
                                                      v            v            v
                                           +-------------------+ +-------------------+ +-------------------+
                                           | Transcoder Worker | | Transcoder Worker | | Transcoder Worker |
                                           +-------------------+ +-------------------+ +-------------------+
                                                      |            |            |
                                               transcode output transcode output transcode output
                                                      v            v            v
                                               +------------------------+
                                               | Processed Storage (S3) |
                                               +------------------------+
                                                   |                 |
                                             stage update       origin pull
                                                   |                 v
                                                   +--------->+-----+
                                                              | CDN |
                                                              +-----+
                                                                 |
                                                            stream video
                                                                 v
                                                              +------+
                                                              | User |
                                                              +------+
```


### Task 4.13
**difficulty:** `medium`

**prompt.txt:** Draw a real-time chat system. Place "User A" on the left and "User B" on the right, with both connected bidirectionally to "Chat Gateway" via arrows labeled "WebSocket". Chat Gateway must query "Presence Service" using an arrow labeled "presence check", and Presence Service stores online status in "Presence Cache (Redis)". Chat Gateway must also publish messages to "Message Queue (Kafka)" using an arrow labeled "publish message". A "Delivery Service" consumes from Kafka using an arrow labeled "consume", writes message history to "Messages DB (Cassandra)" using an arrow labeled "persist history", delivers online messages back to connected clients using an arrow labeled "online delivery", and routes offline deliveries to "Push Notification Service" using an arrow labeled "offline delivery". Push Notification Service then sends to "APNs / FCM" using an arrow labeled "push send". Keep the online and offline delivery paths visually distinct and do not connect users directly to Kafka or the databases.

**assertions.json:**
```json
{
  "required_labels": [
    "User A",
    "User B",
    "Chat Gateway",
    "Presence Service",
    "Presence Cache (Redis)",
    "Message Queue (Kafka)",
    "Delivery Service",
    "Messages DB (Cassandra)",
    "Push Notification Service",
    "APNs / FCM",
    "WebSocket",
    "presence check",
    "publish message",
    "consume",
    "persist history",
    "online delivery",
    "offline delivery",
    "push send"
  ],
  "forbidden_labels": [],
  "entity_count": 10,
  "required_edges": [
    {
      "from": "User A",
      "to": "Chat Gateway"
    },
    {
      "from": "Chat Gateway",
      "to": "User A"
    },
    {
      "from": "User B",
      "to": "Chat Gateway"
    },
    {
      "from": "Chat Gateway",
      "to": "User B"
    },
    {
      "from": "Chat Gateway",
      "to": "Presence Service"
    },
    {
      "from": "Presence Service",
      "to": "Presence Cache (Redis)"
    },
    {
      "from": "Chat Gateway",
      "to": "Message Queue (Kafka)"
    },
    {
      "from": "Message Queue (Kafka)",
      "to": "Delivery Service"
    },
    {
      "from": "Delivery Service",
      "to": "Messages DB (Cassandra)"
    },
    {
      "from": "Delivery Service",
      "to": "User B"
    },
    {
      "from": "Delivery Service",
      "to": "Push Notification Service"
    },
    {
      "from": "Push Notification Service",
      "to": "APNs / FCM"
    }
  ],
  "required_edge_labels": [
    "WebSocket",
    "presence check",
    "publish message",
    "consume",
    "persist history",
    "online delivery",
    "offline delivery",
    "push send"
  ],
  "preserved_elements": []
}
```

**reference.ascii:**
```text
+--------+      WebSocket      +--------------+      WebSocket      +--------+
| User A |<------------------->| Chat Gateway |<------------------->| User B |
+--------+                     +--------------+                     +--------+
                                      |                 |
                               presence check     publish message
                                      v                 v
                           +----------------+   +-----------------------+
                           | Presence Service|   | Message Queue (Kafka)|
                           +----------------+   +-----------------------+
                                      |                 |
                                      v              consume
                           +----------------------+      v
                           | Presence Cache       | +------------------+   online delivery   +--------+
                           | (Redis)              | | Delivery Service |-------------------->| User B |
                           +----------------------+ +------------------+                     +--------+
                                                         |             |
                                                  persist history  offline delivery
                                                         v             v
                                      +--------------------------+ +--------------------------+
                                      | Messages DB (Cassandra)  | | Push Notification Service|
                                      +--------------------------+ +--------------------------+
                                                                             |
                                                                        push send
                                                                             v
                                                                        +-----------+
                                                                        | APNs / FCM|
                                                                        +-----------+
```


### Task 4.14
**difficulty:** `medium`

**prompt.txt:** Draw a ride-sharing backend for an Uber-style system. Put "API Gateway" near the top center, with "Rider App" and "Driver App" both connecting into it. "Driver App" also sends live GPS pings to "Location Service" using an arrow labeled "WebSocket GPS", and Location Service stores to "Location Cache (Redis)" using an arrow labeled "geohash". API Gateway routes dispatch lookups to "Matching Service", trip requests to "Trip Service", and payment requests to "Payment Service". Matching Service reads from Location Cache using an arrow labeled "nearby search" and sends assignments to Trip Service using an arrow labeled "assign driver". Trip Service writes to "Trips DB" using an arrow labeled "write trip" and emits status updates to "Notification Service". Payment Service writes to "Payments DB" using an arrow labeled "write payment" and calls external "Stripe" using an arrow labeled "call PSP". Notification Service sends updates back to both Rider App and Driver App using arrows labeled "notify rider" and "notify driver".

**assertions.json:**
```json
{
  "required_labels": [
    "Rider App",
    "Driver App",
    "API Gateway",
    "Location Service",
    "Location Cache (Redis)",
    "Matching Service",
    "Trip Service",
    "Trips DB",
    "Payment Service",
    "Payments DB",
    "Stripe",
    "Notification Service",
    "WebSocket GPS",
    "geohash",
    "nearby search",
    "assign driver",
    "write trip",
    "payment request",
    "write payment",
    "call PSP",
    "notify rider",
    "notify driver"
  ],
  "forbidden_labels": [],
  "entity_count": 12,
  "required_edges": [
    {
      "from": "Rider App",
      "to": "API Gateway"
    },
    {
      "from": "Driver App",
      "to": "API Gateway"
    },
    {
      "from": "Driver App",
      "to": "Location Service"
    },
    {
      "from": "Location Service",
      "to": "Location Cache (Redis)"
    },
    {
      "from": "API Gateway",
      "to": "Matching Service"
    },
    {
      "from": "API Gateway",
      "to": "Trip Service"
    },
    {
      "from": "API Gateway",
      "to": "Payment Service"
    },
    {
      "from": "Matching Service",
      "to": "Location Cache (Redis)"
    },
    {
      "from": "Matching Service",
      "to": "Trip Service"
    },
    {
      "from": "Trip Service",
      "to": "Trips DB"
    },
    {
      "from": "Trip Service",
      "to": "Notification Service"
    },
    {
      "from": "Payment Service",
      "to": "Payments DB"
    },
    {
      "from": "Payment Service",
      "to": "Stripe"
    },
    {
      "from": "Notification Service",
      "to": "Rider App"
    },
    {
      "from": "Notification Service",
      "to": "Driver App"
    }
  ],
  "required_edge_labels": [
    "WebSocket GPS",
    "geohash",
    "nearby search",
    "assign driver",
    "write trip",
    "payment request",
    "write payment",
    "call PSP",
    "notify rider",
    "notify driver"
  ],
  "preserved_elements": []
}
```

**reference.ascii:**
```text
+-----------+      rider requests      +-------------+      driver app      +------------+
| Rider App |------------------------->| API Gateway |<------------------| Driver App |
+-----------+                          +-------------+                   +------------+
                                            |              |                |
                                     dispatch lookup   payment request  WebSocket GPS
                                            v              v                v
                                  +------------------+  +-----------------+  +------------------+
                                  | Matching Service |  | Payment Service |  | Location Service |
                                  +------------------+  +-----------------+  +------------------+
                                            |              |                |
                                      assign driver   write payment      geohash
                                            v              v                v
                                      +--------------+ +-------------+ +------------------------+
                                      | Trip Service | | Payments DB | | Location Cache (Redis) |
                                      +--------------+ +-------------+ +------------------------+
                                            |              |                ^
                                        write trip      call PSP      nearby search
                                            v              v                |
                                        +----------+   +--------+         |
                                        | Trips DB |   | Stripe |         |
                                        +----------+   +--------+         |
                                            |                             |
                                       emits status                       |
                                            v                             |
                                  +----------------------+                |
                                  | Notification Service |                |
                                  +----------------------+                |
                                          |            |                  |
                                     notify rider  notify driver          |
                                          v            v                  |
                                   +-----------+   +------------+         |
                                   | Rider App |   | Driver App |---------+
                                   +-----------+   +------------+
```


### Task 4.15
**difficulty:** `medium`

**prompt.txt:** Draw a Lambda architecture data pipeline. Three data sources publish into "Kafka (Event Stream)": "App Events" using an arrow labeled "publish", "DB Change Stream" using an arrow labeled "CDC", and "IoT Sensors" using an arrow labeled "telemetry". From Kafka, draw the speed layer to "Stream Processor (Flink)" using an arrow labeled "speed layer", then to "Time-Series DB" using an arrow labeled "serve metrics". Also from Kafka, draw the batch layer to "Batch Processor (Spark)" using an arrow labeled "batch layer", then to "Data Warehouse (BigQuery)" using an arrow labeled "serve analytics". Both storage outputs feed "Analytics Dashboard" using arrows labeled "realtime view" and "historical view". Add a "Data Catalog" that connects to both storage layers using arrows labeled "catalog sync". Label every required arrow cleanly.

**assertions.json:**
```json
{
  "required_labels": [
    "App Events",
    "DB Change Stream",
    "IoT Sensors",
    "Kafka (Event Stream)",
    "Stream Processor (Flink)",
    "Time-Series DB",
    "Batch Processor (Spark)",
    "Data Warehouse (BigQuery)",
    "Analytics Dashboard",
    "Data Catalog",
    "publish",
    "CDC",
    "telemetry",
    "speed layer",
    "batch layer",
    "serve metrics",
    "serve analytics",
    "realtime view",
    "historical view",
    "catalog sync"
  ],
  "forbidden_labels": [],
  "entity_count": 10,
  "required_edges": [
    {
      "from": "App Events",
      "to": "Kafka (Event Stream)"
    },
    {
      "from": "DB Change Stream",
      "to": "Kafka (Event Stream)"
    },
    {
      "from": "IoT Sensors",
      "to": "Kafka (Event Stream)"
    },
    {
      "from": "Kafka (Event Stream)",
      "to": "Stream Processor (Flink)"
    },
    {
      "from": "Kafka (Event Stream)",
      "to": "Batch Processor (Spark)"
    },
    {
      "from": "Stream Processor (Flink)",
      "to": "Time-Series DB"
    },
    {
      "from": "Batch Processor (Spark)",
      "to": "Data Warehouse (BigQuery)"
    },
    {
      "from": "Time-Series DB",
      "to": "Analytics Dashboard"
    },
    {
      "from": "Data Warehouse (BigQuery)",
      "to": "Analytics Dashboard"
    },
    {
      "from": "Data Catalog",
      "to": "Time-Series DB"
    },
    {
      "from": "Data Catalog",
      "to": "Data Warehouse (BigQuery)"
    }
  ],
  "required_edge_labels": [
    "publish",
    "CDC",
    "telemetry",
    "speed layer",
    "batch layer",
    "serve metrics",
    "serve analytics",
    "realtime view",
    "historical view",
    "catalog sync"
  ],
  "preserved_elements": []
}
```

**reference.ascii:**
```text
+------------+      publish      +----------------------------+
| App Events |------------------->|    Kafka (Event Stream)    |
+------------+                    +----------------------------+

+------------------+      CDC      +----------------------------+
| DB Change Stream |-------------->|    Kafka (Event Stream)    |
+------------------+               +----------------------------+

+-------------+      telemetry      +----------------------------+
| IoT Sensors |-------------------->|    Kafka (Event Stream)    |
+-------------+                     +----------------------------+
                                           |               |
                                     speed layer      batch layer
                                           v               v
                              +------------------------+  +---------------------------+
                              | Stream Processor       |  | Batch Processor           |
                              | (Flink)                |  | (Spark)                   |
                              +------------------------+  +---------------------------+
                                           |               |
                                      serve metrics   serve analytics
                                           v               v
                                +----------------+   +-----------------------------+
                                | Time-Series DB |   | Data Warehouse (BigQuery)  |
                                +----------------+   +-----------------------------+
                                           |               |
                                    catalog sync     catalog sync
                                           v               v
                                      +----------------------+
                                      |     Data Catalog     |
                                      +----------------------+

                                +----------------+   realtime view   +-----------------------+   historical view   +-----------------------------+
                                | Time-Series DB |------------------>| Analytics Dashboard   |<--------------------| Data Warehouse (BigQuery)  |
                                +----------------+                   +-----------------------+                     +-----------------------------+
```


### Task 4.16
**difficulty:** `hard`

**prompt.txt:**
- Draw an ASCII diagram illustrating a multi-region active-active orders API.
- Put "Global DNS + WAF" at the top routing to "API Gateway A" and "API Gateway B" using arrows labeled "route traffic".
- Under each gateway place an "Auth Service" and an "Orders Service" in the same region.
- Each gateway connects to both regional services using arrows labeled "auth check" and "order writes".
- Each orders service must connect to a regional Redis cache using arrows labeled "hot reads", to a regional PostgreSQL database using arrows labeled "state writes", and to a regional Kafka outbox using arrows labeled "outbox events".
- Show bidirectional replication between "PostgreSQL A" and "PostgreSQL B" labeled "CDC replication", and bidirectional mirroring between "Kafka Outbox A" and "Kafka Outbox B" labeled "MirrorMaker".
- When arrows are required, make them centered and aligned cleanly to their source and target.
- If an arrow has a label, place the label a little above the arrow rather than inside the arrow line.
- For any label or text inside a node, box, or icon, center it within that component whenever possible.
- Any component with incoming or outgoing arrows should be sized wide or tall enough to make those connections visually unambiguous, so it is clear where arrows originate and where they terminate.
- If one component fans out to multiple arrows, or multiple arrows converge into one component, its width or height should clearly support those attachment points.
- Return only the final ASCII diagram in plain text.
- Do not include markdown fences, explanations, or any extra text.

**assertions.json:**
```json
{
  "required_labels": [
    "Global DNS + WAF",
    "API Gateway A",
    "API Gateway B",
    "Auth Service A",
    "Orders Service A",
    "Auth Service B",
    "Orders Service B",
    "Redis A",
    "Redis B",
    "PostgreSQL A",
    "PostgreSQL B",
    "Kafka Outbox A",
    "Kafka Outbox B",
    "route traffic",
    "auth check",
    "order writes",
    "hot reads",
    "state writes",
    "outbox events",
    "CDC replication",
    "MirrorMaker"
  ],
  "forbidden_labels": [],
  "entity_count": 13,
  "required_edges": [
    {
      "from": "Global DNS + WAF",
      "to": "API Gateway A"
    },
    {
      "from": "Global DNS + WAF",
      "to": "API Gateway B"
    },
    {
      "from": "API Gateway A",
      "to": "Auth Service A"
    },
    {
      "from": "API Gateway A",
      "to": "Orders Service A"
    },
    {
      "from": "API Gateway B",
      "to": "Auth Service B"
    },
    {
      "from": "API Gateway B",
      "to": "Orders Service B"
    },
    {
      "from": "Orders Service A",
      "to": "Redis A"
    },
    {
      "from": "Orders Service A",
      "to": "PostgreSQL A"
    },
    {
      "from": "Orders Service A",
      "to": "Kafka Outbox A"
    },
    {
      "from": "Orders Service B",
      "to": "Redis B"
    },
    {
      "from": "Orders Service B",
      "to": "PostgreSQL B"
    },
    {
      "from": "Orders Service B",
      "to": "Kafka Outbox B"
    },
    {
      "from": "PostgreSQL A",
      "to": "PostgreSQL B"
    },
    {
      "from": "PostgreSQL B",
      "to": "PostgreSQL A"
    },
    {
      "from": "Kafka Outbox A",
      "to": "Kafka Outbox B"
    },
    {
      "from": "Kafka Outbox B",
      "to": "Kafka Outbox A"
    }
  ],
  "required_edge_labels": [
    "route traffic",
    "auth check",
    "order writes",
    "hot reads",
    "state writes",
    "outbox events",
    "CDC replication",
    "MirrorMaker"
  ],
  "preserved_elements": []
}
```

**reference.ascii:**
```text
              +------------------+
              | Global DNS + WAF |
              +------------------+
              /                  \
       route traffic         route traffic
            v                      v
    +---------------+      +---------------+
    | API Gateway A |      | API Gateway B |
    +---------------+      +---------------+
       |         |            |         |
  auth check order writes auth check order writes
       v         v            v         v
+--------------+ +----------------+ +--------------+ +----------------+
| Auth Service | | Orders Service | | Auth Service | | Orders Service |
|      A       | |       A        | |      B       | |       B        |
+--------------+ +----------------+ +--------------+ +----------------+
                  /    |    \                        /    |    \
            hot reads state writes outbox events hot reads state writes outbox events
                v       v       v                  v       v       v
           +---------+ +--------------+      +---------+ +--------------+
           | Redis A | | PostgreSQL A |      | Redis B | | PostgreSQL B |
           +---------+ +--------------+      +---------+ +--------------+
                           CDC replication
           +--------------+<------------------------->+--------------+
           | PostgreSQL A |                           | PostgreSQL B |
           +--------------+                           +--------------+

        +----------------+      MirrorMaker       +----------------+
        | Kafka Outbox A |<---------------------->| Kafka Outbox B |
        +----------------+                        +----------------+
```

### Task 4.17
**difficulty:** `hard`

**prompt.txt:**
- Draw an ASCII diagram illustrating an advanced production RAG system with both serving and indexing paths.
- Place "User" on the left sending a request to "Chat API", then to "Query Rewriter", then to "Hybrid Retriever" using arrows labeled "ask", "rewrite query", and "hybrid search".
- Hybrid Retriever must query three stores to its right: "Summary Index" using an arrow labeled "coarse search", "Chunk Index" using an arrow labeled "vector hit", and "Metadata DB" using an arrow labeled "metadata filter".
- Place "Reranker" directly below "Hybrid Retriever" with a downward connector labeled "candidates".
- Below "Reranker", stack "Prompt Builder", "Safety Filter", and "LLM Gateway" vertically using arrows labeled "grounded prompt", "policy check", and "generate answer".
- "LLM Gateway" must return to "Chat API" using a connector labeled "model response", and "Chat API" must return to "User" with an arrow labeled "answer".
- Also add an indexing pipeline on the right: "Document Store" feeds "Parser + Chunker" using an arrow labeled "parse docs".
- Parser + Chunker writes summaries to "Summary Index" using an arrow labeled "write summaries", writes metadata to "Metadata DB" using an arrow labeled "write metadata", and feeds "Embedding Jobs" using an arrow labeled "chunk batches".
- Embedding Jobs updates "Chunk Index" using an arrow labeled "upsert vectors".
- When arrows are required, make them centered and aligned cleanly to their source and target.
- If an arrow has a label, place the label a little above the arrow rather than inside the arrow line.
- For any label or text inside a node, box, or icon, center it within that component whenever possible.
- Any component with incoming or outgoing arrows should be sized wide or tall enough to make those connections visually unambiguous, so it is clear where arrows originate and where they terminate.
- If one component fans out to multiple arrows, or multiple arrows converge into one component, its width or height should clearly support those attachment points.
- Return only the final ASCII diagram in plain text.
- Do not include markdown fences, explanations, or any extra text.

**assertions.json:**
```json
{
  "required_labels": [
    "User",
    "Chat API",
    "Query Rewriter",
    "Hybrid Retriever",
    "Summary Index",
    "Chunk Index",
    "Metadata DB",
    "Reranker",
    "Prompt Builder",
    "Safety Filter",
    "LLM Gateway",
    "Document Store",
    "Parser + Chunker",
    "Embedding Jobs",
    "ask",
    "rewrite query",
    "hybrid search",
    "coarse search",
    "vector hit",
    "metadata filter",
    "candidates",
    "grounded prompt",
    "policy check",
    "generate answer",
    "model response",
    "answer",
    "parse docs",
    "write summaries",
    "write metadata",
    "chunk batches",
    "upsert vectors"
  ],
  "forbidden_labels": [],
  "entity_count": 14,
  "required_edges": [
    {
      "from": "User",
      "to": "Chat API"
    },
    {
      "from": "Chat API",
      "to": "Query Rewriter"
    },
    {
      "from": "Query Rewriter",
      "to": "Hybrid Retriever"
    },
    {
      "from": "Hybrid Retriever",
      "to": "Summary Index"
    },
    {
      "from": "Hybrid Retriever",
      "to": "Chunk Index"
    },
    {
      "from": "Hybrid Retriever",
      "to": "Metadata DB"
    },
    {
      "from": "Hybrid Retriever",
      "to": "Reranker"
    },
    {
      "from": "Reranker",
      "to": "Prompt Builder"
    },
    {
      "from": "Prompt Builder",
      "to": "Safety Filter"
    },
    {
      "from": "Safety Filter",
      "to": "LLM Gateway"
    },
    {
      "from": "LLM Gateway",
      "to": "Chat API"
    },
    {
      "from": "Chat API",
      "to": "User"
    },
    {
      "from": "Document Store",
      "to": "Parser + Chunker"
    },
    {
      "from": "Parser + Chunker",
      "to": "Summary Index"
    },
    {
      "from": "Parser + Chunker",
      "to": "Metadata DB"
    },
    {
      "from": "Parser + Chunker",
      "to": "Embedding Jobs"
    },
    {
      "from": "Embedding Jobs",
      "to": "Chunk Index"
    }
  ],
  "required_edge_labels": [
    "ask",
    "rewrite query",
    "hybrid search",
    "coarse search",
    "vector hit",
    "metadata filter",
    "candidates",
    "grounded prompt",
    "policy check",
    "generate answer",
    "model response",
    "answer",
    "parse docs",
    "write summaries",
    "write metadata",
    "chunk batches",
    "upsert vectors"
  ],
  "preserved_elements": []
}
```

**reference.ascii:**
```text
+------+      ask      +----------+   rewrite query   +----------------+   hybrid search   +------------------+
| User |-------------->| Chat API |------------------>| Query Rewriter |------------------>| Hybrid Retriever |
+------+               +----------+                   +----------------+                   +------------------+
   ^                      ^                                                                      /       |       \
   |                      |                                                                  coarse    vector   metadata
   |                      |                                                                  search      hit     filter
   +------- answer -------+                                                                    v         v         v
                          |                                                             +-----------+ +-----------+ +-------------+
                          |                                                             | Summary   | | Chunk     | | Metadata DB |
                          |                                                             |  Index    | |  Index    | +-------------+
                          |                                                             +-----------+ +-----------+
                          |                                                                  ^             ^
                          |                                                             write summaries  upsert vectors
                          |                                                                  |             ^
                          |                                                          +----------------+   |
                          |                                                          | Embedding Jobs |---+
                          |                                                          +----------------+
                          |                                                                  ^
                          |                                                             chunk batches
                          |                                                                  |
                          |                                                          +------------------+
                          |                                                          | Parser + Chunker |
                          |                                                          +------------------+
                          |                                                                  ^
                          |                                                             parse docs
                          |                                                                  |
                          |                                                          +------------------+
                          |                                                          |  Document Store  |
                          |                                                          +------------------+
                          |
                          |                                                             candidates
                          |                                                                  v
                          |                                                             +----------+
                          |                                                             | Reranker |
                          |                                                             +----------+
                          |                                                                  |
                          |                                                             grounded prompt
                          |                                                                  v
                          |                                                       +----------------+
                          |                                                       | Prompt Builder |
                          |                                                       +----------------+
                          |                                                                  |
                          |                                                             policy check
                          |                                                                  v
                          |                                                       +---------------+
                          |                                                       | Safety Filter |
                          |                                                       +---------------+
                          |                                                                  |
                          |                                                             generate answer
                          |                                                                  v
                     model response                                             +-------------+
                          +<----------------------------------------------------| LLM Gateway |
                                                                                +-------------+
```

### Task 4.18
**difficulty:** `hard`

**prompt.txt:**
- Draw an ASCII diagram illustrating an event-driven checkout saga with fraud and fulfillment.
- Put "Web Client" on the left calling "Checkout API" with an arrow labeled "place order".
- Checkout API must call "Order Orchestrator" using an arrow labeled "start saga".
- Order Orchestrator must call "Inventory Service" using an arrow labeled "reserve stock", call "Payment Service" using an arrow labeled "authorize payment", and write to "Orders DB" using an arrow labeled "saga state".
- Inventory Service must update "Inventory DB" using an arrow labeled "stock hold".
- "Inventory DB" must publish to "Event Bus" using an arrow labeled "inventory events".
- Payment Service must publish to "Event Bus" using an arrow labeled "payment events", call "Fraud Scorer" using an arrow labeled "risk check", and call "PSP" using an arrow labeled "capture".
- Event Bus must fan out to "Notification Service" using an arrow labeled "customer updates", to "Fulfillment Worker" using an arrow labeled "ready to ship", and to "Dead Letter Queue" using an arrow labeled "failed events".
- When arrows are required, make them centered and aligned cleanly to their source and target.
- If an arrow has a label, place the label a little above the arrow rather than inside the arrow line.
- For any label or text inside a node, box, or icon, center it within that component whenever possible.
- Any component with incoming or outgoing arrows should be sized wide or tall enough to make those connections visually unambiguous, so it is clear where arrows originate and where they terminate.
- If one component fans out to multiple arrows, or multiple arrows converge into one component, its width or height should clearly support those attachment points.
- Return only the final ASCII diagram in plain text.
- Do not include markdown fences, explanations, or any extra text.

**assertions.json:**
```json
{
  "required_labels": [
    "Web Client",
    "Checkout API",
    "Order Orchestrator",
    "Inventory Service",
    "Inventory DB",
    "Payment Service",
    "Orders DB",
    "Fraud Scorer",
    "PSP",
    "Event Bus",
    "Notification Service",
    "Fulfillment Worker",
    "Dead Letter Queue",
    "place order",
    "start saga",
    "reserve stock",
    "authorize payment",
    "saga state",
    "stock hold",
    "inventory events",
    "risk check",
    "capture",
    "payment events",
    "customer updates",
    "ready to ship",
    "failed events"
  ],
  "forbidden_labels": [],
  "entity_count": 13,
  "required_edges": [
    {
      "from": "Web Client",
      "to": "Checkout API"
    },
    {
      "from": "Checkout API",
      "to": "Order Orchestrator"
    },
    {
      "from": "Order Orchestrator",
      "to": "Inventory Service"
    },
    {
      "from": "Order Orchestrator",
      "to": "Payment Service"
    },
    {
      "from": "Order Orchestrator",
      "to": "Orders DB"
    },
    {
      "from": "Inventory Service",
      "to": "Inventory DB"
    },
    {
      "from": "Inventory DB",
      "to": "Event Bus"
    },
    {
      "from": "Payment Service",
      "to": "Fraud Scorer"
    },
    {
      "from": "Payment Service",
      "to": "PSP"
    },
    {
      "from": "Payment Service",
      "to": "Event Bus"
    },
    {
      "from": "Event Bus",
      "to": "Notification Service"
    },
    {
      "from": "Event Bus",
      "to": "Fulfillment Worker"
    },
    {
      "from": "Event Bus",
      "to": "Dead Letter Queue"
    }
  ],
  "required_edge_labels": [
    "place order",
    "start saga",
    "reserve stock",
    "authorize payment",
    "saga state",
    "stock hold",
    "inventory events",
    "risk check",
    "capture",
    "payment events",
    "customer updates",
    "ready to ship",
    "failed events"
  ],
  "preserved_elements": []
}
```

**reference.ascii:**
```text
+------------+   place order   +--------------+   start saga   +--------------------+
| Web Client |---------------->| Checkout API |--------------->| Order Orchestrator |
+------------+                 +--------------+                +--------------------+
                                                               /      |       \
                                                        reserve stock saga state authorize payment
                                                             v        v         v
                                                     +----------------+ +-----------+ +-----------------+
                                                     |   Inventory    | | Orders DB | | Payment Service |
                                                     |    Service     | +-----------+ +-----------------+
                                                     +----------------+                      /      |      \
                                                            |                         payment   risk    capture
                                                       stock hold                       events   check
                                                            v                             v       v       v
                                                             inventory events
                                                     +--------------+----------->+------------------------------+ +--------------+ +------+
                                                     | Inventory DB |            |          Event Bus           | | Fraud Scorer | | PSP  |
                                                     +--------------+            +------------------------------+ +--------------+ +------+
                                                                                     |         |         |
                                                                              customer    ready to    failed
                                                                               updates      ship      events
                                                                                     v         v         v
                                                                  +--------------------+ +--------------------+ +--------------------+
                                                                  |    Notification    | |    Fulfillment    | |    Dead Letter    |
                                                                  |      Service       | |       Worker       | |       Queue        |
                                                                  +--------------------+ +--------------------+ +--------------------+
```

### Task 4.19
**difficulty:** `hard`

**prompt.txt:**
- Draw an ASCII diagram illustrating a production ML feature platform with separate batch and streaming paths.
- Put "Batch Warehouse" and "Clickstream Kafka" on the left.
- "Batch Warehouse" feeds "Batch Feature Jobs" using an arrow labeled "historical compute", and "Clickstream Kafka" feeds "Stream Feature Jobs" using an arrow labeled "realtime transforms".
- Place "Feature Registry" above the two job boxes and connect it to both using arrows labeled "feature defs".
- Batch Feature Jobs writes to "Offline Feature Store" using an arrow labeled "backfill features" and also materializes to "Online Feature Store" using an arrow labeled "batch materialize".
- Stream Feature Jobs writes to Online Feature Store using an arrow labeled "fresh features".
- Offline Feature Store feeds "Training Pipeline" using an arrow labeled "training set".
- Training Pipeline publishes to "Model Registry" using an arrow labeled "publish model", and Model Registry loads into "Model Server" using an arrow labeled "load model".
- "Online Inference API" must query Online Feature Store using an arrow labeled "online lookup", call Model Server using an arrow labeled "score request", and write to "Prediction Log" using an arrow labeled "prediction events".
- When arrows are required, make them centered and aligned cleanly to their source and target.
- If an arrow has a label, place the label a little above the arrow rather than inside the arrow line.
- For any label or text inside a node, box, or icon, center it within that component whenever possible.
- Any component with incoming or outgoing arrows should be sized wide or tall enough to make those connections visually unambiguous, so it is clear where arrows originate and where they terminate.
- If one component fans out to multiple arrows, or multiple arrows converge into one component, its width or height should clearly support those attachment points.
- Return only the final ASCII diagram in plain text.
- Do not include markdown fences, explanations, or any extra text.

**assertions.json:**
```json
{
  "required_labels": [
    "Batch Warehouse",
    "Clickstream Kafka",
    "Feature Registry",
    "Batch Feature Jobs",
    "Stream Feature Jobs",
    "Offline Feature Store",
    "Online Feature Store",
    "Training Pipeline",
    "Model Registry",
    "Model Server",
    "Online Inference API",
    "Prediction Log",
    "historical compute",
    "realtime transforms",
    "feature defs",
    "backfill features",
    "batch materialize",
    "fresh features",
    "training set",
    "publish model",
    "load model",
    "online lookup",
    "score request",
    "prediction events"
  ],
  "forbidden_labels": [],
  "entity_count": 12,
  "required_edges": [
    {
      "from": "Batch Warehouse",
      "to": "Batch Feature Jobs"
    },
    {
      "from": "Clickstream Kafka",
      "to": "Stream Feature Jobs"
    },
    {
      "from": "Feature Registry",
      "to": "Batch Feature Jobs"
    },
    {
      "from": "Feature Registry",
      "to": "Stream Feature Jobs"
    },
    {
      "from": "Batch Feature Jobs",
      "to": "Offline Feature Store"
    },
    {
      "from": "Batch Feature Jobs",
      "to": "Online Feature Store"
    },
    {
      "from": "Stream Feature Jobs",
      "to": "Online Feature Store"
    },
    {
      "from": "Offline Feature Store",
      "to": "Training Pipeline"
    },
    {
      "from": "Training Pipeline",
      "to": "Model Registry"
    },
    {
      "from": "Model Registry",
      "to": "Model Server"
    },
    {
      "from": "Online Inference API",
      "to": "Online Feature Store"
    },
    {
      "from": "Online Inference API",
      "to": "Model Server"
    },
    {
      "from": "Online Inference API",
      "to": "Prediction Log"
    }
  ],
  "required_edge_labels": [
    "historical compute",
    "realtime transforms",
    "feature defs",
    "backfill features",
    "batch materialize",
    "fresh features",
    "training set",
    "publish model",
    "load model",
    "online lookup",
    "score request",
    "prediction events"
  ],
  "preserved_elements": []
}
```

**reference.ascii:**
```text
                                   +----------------+
                                   | Feature Registry|
                                   +----------------+
                                      |         |
                                feature defs  feature defs
                                      v         v
+-----------------+   historical compute   +--------------------+     +--------------------+   realtime transforms   +------------------+
| Batch Warehouse |----------------------->| Batch Feature Jobs |     | Stream Feature Jobs |<----------------------| Clickstream Kafka|
+-----------------+                        +--------------------+     +--------------------+                       +------------------+
                                                   |        \\                  |
                                          backfill features  batch materialize  fresh features
                                                   v          v                  v
                                       +------------------------+      +------------------------+<----- online lookup -----+
                                       | Offline Feature Store  |      | Online Feature Store   |                           |
                                       +------------------------+      +------------------------+                           |
                                                   |                                                                    +----------------------+
                                              training set                                                              | Online Inference API |
                                                   v                                                                    +----------------------+
                                           +------------------+                                                                  |
                                           | Training Pipeline |                                                            prediction events
                                           +------------------+                                                                  v
                                                   |                                                                    +----------------+
                                              publish model                                                             | Prediction Log |
                                                   v                                                                    +----------------+
                                           +----------------+
                                           | Model Registry |
                                           +----------------+
                                                   |
                                              load model
                                                   v
                                           +--------------+<-------------------------- score request --------------------------+
                                           | Model Server |
                                           +--------------+
```

### Task 4.20
**difficulty:** `hard`

**prompt.txt:**
- Draw an ASCII diagram illustrating a real-world OpenTelemetry gateway pipeline.
- Put three application boxes on the top row: "Service A", "Service B", and "Service C".
- Each service must send to its own agent collector below it: "OTel Agent A", "OTel Agent B", and "OTel Agent C" using arrows labeled "OTLP".
- All three agents send into one central "OTel Gateway" using arrows labeled "forward OTLP".
- OTel Gateway fans out to three processing paths: "Tail Sampling" using an arrow labeled "traces", "Metrics Pipeline" using an arrow labeled "metrics", and "Logs Pipeline" using an arrow labeled "logs".
- Tail Sampling exports to "Tempo" using an arrow labeled "sampled spans".
- Metrics Pipeline exports to "Mimir" using an arrow labeled "remote write".
- Logs Pipeline exports to "Loki" using an arrow labeled "log push".
- Mimir must also connect to "Alertmanager" using an arrow labeled "rule alerts".
- Finally, "Grafana" must read from Tempo, Mimir, and Loki.
- When arrows are required, make them centered and aligned cleanly to their source and target.
- If an arrow has a label, place the label a little above the arrow rather than inside the arrow line.
- For any label or text inside a node, box, or icon, center it within that component whenever possible.
- Any component with incoming or outgoing arrows should be sized wide or tall enough to make those connections visually unambiguous, so it is clear where arrows originate and where they terminate.
- If one component fans out to multiple arrows, or multiple arrows converge into one component, its width or height should clearly support those attachment points.
- Return only the final ASCII diagram in plain text.
- Do not include markdown fences, explanations, or any extra text.

**assertions.json:**
```json
{
  "required_labels": [
    "Service A",
    "Service B",
    "Service C",
    "OTel Agent A",
    "OTel Agent B",
    "OTel Agent C",
    "OTel Gateway",
    "Tail Sampling",
    "Metrics Pipeline",
    "Logs Pipeline",
    "Tempo",
    "Mimir",
    "Loki",
    "Alertmanager",
    "Grafana",
    "OTLP",
    "forward OTLP",
    "traces",
    "metrics",
    "logs",
    "sampled spans",
    "remote write",
    "log push",
    "rule alerts"
  ],
  "forbidden_labels": [],
  "entity_count": 15,
  "required_edges": [
    {
      "from": "Service A",
      "to": "OTel Agent A"
    },
    {
      "from": "Service B",
      "to": "OTel Agent B"
    },
    {
      "from": "Service C",
      "to": "OTel Agent C"
    },
    {
      "from": "OTel Agent A",
      "to": "OTel Gateway"
    },
    {
      "from": "OTel Agent B",
      "to": "OTel Gateway"
    },
    {
      "from": "OTel Agent C",
      "to": "OTel Gateway"
    },
    {
      "from": "OTel Gateway",
      "to": "Tail Sampling"
    },
    {
      "from": "OTel Gateway",
      "to": "Metrics Pipeline"
    },
    {
      "from": "OTel Gateway",
      "to": "Logs Pipeline"
    },
    {
      "from": "Tail Sampling",
      "to": "Tempo"
    },
    {
      "from": "Metrics Pipeline",
      "to": "Mimir"
    },
    {
      "from": "Logs Pipeline",
      "to": "Loki"
    },
    {
      "from": "Mimir",
      "to": "Alertmanager"
    },
    {
      "from": "Tempo",
      "to": "Grafana"
    },
    {
      "from": "Mimir",
      "to": "Grafana"
    },
    {
      "from": "Loki",
      "to": "Grafana"
    }
  ],
  "required_edge_labels": [
    "OTLP",
    "forward OTLP",
    "traces",
    "metrics",
    "logs",
    "sampled spans",
    "remote write",
    "log push",
    "rule alerts"
  ],
  "preserved_elements": []
}
```

**reference.ascii:**
```text
+-----------+          +-----------+          +-----------+
| Service A |          | Service B |          | Service C |
+-----------+          +-----------+          +-----------+
      |                      |                      |
     OTLP                   OTLP                   OTLP
      v                      v                      v
+--------------+       +--------------+       +--------------+
| OTel Agent A |       | OTel Agent B |       | OTel Agent C |
+--------------+       +--------------+       +--------------+
      \                     |                     /
       \               forward OTLP             /
        \                   |                  /
         v                  v                 v
              +---------------------------+
              |        OTel Gateway       |
              +---------------------------+
                 /            |            \
              traces       metrics         logs
                v            v              v
      +----------------+ +------------------+ +---------------+
      | Tail Sampling  | | Metrics Pipeline | | Logs Pipeline |
      +----------------+ +------------------+ +---------------+
                |              |                     |
          sampled spans   remote write            log push
                v              v                     v
          +---------+     +--------+           +--------+
          |  Tempo  |     | Mimir  |           |  Loki  |
          +---------+     +--------+           +--------+
                              |
                         rule alerts
                              v
                      +--------------+
                      | Alertmanager |
                      +--------------+

          +---------+                    +---------+                    +--------+
          |  Tempo  |------------------->|         |<-------------------| Mimir  |
          +---------+                    | Grafana |                    +--------+
                                         |         |
          +--------+-------------------->|         |
          |  Loki  |                     +---------+
          +--------+
```
               +--------------+
               |   Grafana    |
               +--------------+
```
