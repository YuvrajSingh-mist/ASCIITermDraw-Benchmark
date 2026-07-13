from __future__ import annotations


ONESHOT_EXAMPLES = {
    "c1_example.txt": """
EXAMPLE PROMPT:
Draw two boxes "Alpha" and "Beta" connected left-to-right with an arrow.

EXAMPLE OUTPUT:
+---------+     +--------+
|  Alpha  |---->|  Beta  |
+---------+     +--------+
""",
    "c2_example.txt": """
EXAMPLE PROMPT:
Draw a simple client-server diagram: one "Browser" box connecting with an arrow to one "Web Server" box.

EXAMPLE OUTPUT:
+-----------+          +------------+
|  Browser  |--------->| Web Server |
+-----------+          +------------+
""",
    "c3_example.txt": """
EXAMPLE:
You will be shown an image of an ASCII diagram. Apply the given instruction
and output the modified diagram as plain text.

EXAMPLE SOURCE DIAGRAM:
+---------+     +---------+
| Alpha   |---->|  Beta   |
+---------+     +---------+

EXAMPLE INSTRUCTION:
Add a box labeled "Gamma" to the right of Beta, connected from Beta.

EXAMPLE OUTPUT:
+---------+     +---------+     +---------+
| Alpha   |---->|  Beta   |---->|  Gamma  |
+---------+     +---------+     +---------+
""",
    "c4_example.txt": """
EXAMPLE PROMPT:
Draw a 2-tier architecture: "Client" on the left sends requests to "Web Server" on the right.

EXAMPLE OUTPUT:
+--------+     HTTP      +------------+
| Client |-------------->| Web Server |
+--------+               +------------+
""",
}
