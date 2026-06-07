#!/usr/bin/env python3
"""
AI Training Tutorial Generator — Chunked LLM approach
Generates 5 lesson pages per day, one lesson at a time via separate API calls.
Usage: python3 generate_day.py <day_number>
"""
import sys, os, json, time, subprocess, urllib.request, urllib.error, re

BASE = '/home/mrotatori/ai-training'
TUTORIAL_DIR = os.path.join(BASE, 'tutorials')
STATE_FILE = os.path.join(BASE, 'scripts', 'state.json')
GENERATED_FILE = os.path.join(BASE, 'generated.json')

# Read API key
env_path = os.path.expanduser('~/.hermes/.env')
API_KEY = None
with open(env_path) as f:
    for line in f:
        line = line.strip()
        if line.startswith('OPENROUTER_API_KEY=') and not line.startswith('#'):
            API_KEY = line.split('=', 1)[1].strip()
            break

if not API_KEY:
    print("ERROR: OPENROUTER_API_KEY not found in .env")
    sys.exit(1)

def llm_call(prompt, max_tokens=6000, retries=5):
    """Make a single LLM API call with retries using curl for reliability."""
    data = json.dumps({
        "model": "owl-alpha",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0.7
    })

    for attempt in range(retries):
        try:
            result = subprocess.run([
                'curl', '-s', '--connect-timeout', '30', '--max-time', '300',
                '--retry', '2', '--retry-delay', '5',
                'https://openrouter.ai/api/v1/chat/completions',
                '-H', 'Content-Type: application/json',
                '-H', f'Authorization: Bearer {API_KEY}',
                '-d', data
            ], capture_output=True, text=True, timeout=310)

            if result.returncode != 0:
                print(f"  curl error (attempt {attempt+1}/{retries}): {result.stderr[:200]}")
                if attempt < retries - 1:
                    time.sleep(10 * (attempt + 1))
                continue

            response = json.loads(result.stdout)
            if 'choices' in response and len(response['choices']) > 0:
                return response['choices'][0]['message']['content']
            elif 'error' in response:
                err = response['error']
                if isinstance(err, dict):
                    err = err.get('message', str(err))
                print(f"  API error (attempt {attempt+1}/{retries}): {err}")
            if attempt < retries - 1:
                wait = 10 * (attempt + 1)
                print(f"  Waiting {wait}s...")
                time.sleep(wait)
        except subprocess.TimeoutExpired:
            print(f"  Timeout (attempt {attempt+1}/{retries})")
            if attempt < retries - 1:
                time.sleep(15)
        except Exception as e:
            print(f"  Unexpected error: {e}")
            if attempt < retries - 1:
                time.sleep(10)
    return None

def slug(day, lesson):
    return str(day).zfill(2) + str(lesson).zfill(2)

def get_curriculum():
    """Return the full 60-day, 5-lessons-per-day curriculum."""
    return [
        # Day 1
        (1, 1, 1, "What is an AI Agent?"),
        (1, 2, 1, "The Agent Loop"),
        (1, 3, 1, "Agents vs Chatbots vs Assistants"),
        (1, 4, 1, "Real-World Agent Examples"),
        (1, 5, 1, "Your First Agent Plan"),
        # Day 2
        (2, 1, 1, "Choosing an LLM Provider"),
        (2, 2, 1, "Setting Up Your API Key"),
        (2, 3, 1, "Understanding Messages & Roles"),
        (2, 4, 1, "Temperature, Tokens & Parameters"),
        (2, 5, 1, "Building a Conversational Agent"),
        # Day 3
        (3, 1, 1, "Why System Prompts Matter"),
        (3, 2, 1, "Anatomy of a Great System Prompt"),
        (3, 3, 1, "Few-Shot Prompting"),
        (3, 4, 1, "Setting Boundaries & Constraints"),
        (3, 5, 1, "Prompt Engineering Anti-Patterns"),
        # Day 4
        (4, 1, 1, "What is a Tool?"),
        (4, 2, 1, "Defining Your First Tool"),
        (4, 3, 1, "The Agent Loop with Tools"),
        (4, 4, 1, "Multiple Tools & Tool Selection"),
        (4, 5, 1, "Error Handling for Tools"),
        # Day 5
        (5, 1, 1, "Function Schemas Deep Dive"),
        (5, 2, 1, "Schema Best Practices"),
        (5, 3, 1, "Multi-Step Tool Workflows"),
        (5, 4, 1, "Parallel Tool Calls"),
        (5, 5, 1, "Production Tool Agent Pattern"),
        # Day 6
        (6, 1, 1, "Why Agents Need Memory"),
        (6, 2, 1, "Short-Term Memory"),
        (6, 3, 1, "Memory Summarization"),
        (6, 4, 1, "External Memory Storage"),
        (6, 5, 1, "Building a Memory-Aware Agent"),
        # Day 7
        (7, 1, 1, "What is Agent Chaining?"),
        (7, 2, 1, "Linear Chains"),
        (7, 3, 1, "Conditional Chains"),
        (7, 4, 1, "Building a Content Pipeline"),
        (7, 5, 1, "Debugging Chains"),
        # Day 8
        (8, 1, 1, "Types of Agent Failures"),
        (8, 2, 1, "Retry Patterns"),
        (8, 3, 1, "Fallback Strategies"),
        (8, 4, 1, "Circuit Breakers"),
        (8, 5, 1, "Building a Resilient Agent"),
        # Day 9
        (9, 1, 1, "Why Stream?"),
        (9, 2, 1, "Server-Sent Events (SSE)"),
        (9, 3, 1, "Streaming with OpenAI API"),
        (9, 4, 1, "Building a Streaming Chat UI"),
        (9, 5, 1, "Streaming + Tool Calls"),
        # Day 10
        (10, 1, 1, "Designing Your Personal Assistant"),
        (10, 2, 1, "Building the Core Loop"),
        (10, 3, 1, "Adding Calendar & Email Tools"),
        (10, 4, 1, "Memory & Context"),
        (10, 5, 1, "Testing Your Assistant"),
        # Days 11-16 (Intermediate)
        (11, 1, 2, "Why Agents Need RAG"),
        (11, 2, 2, "How RAG Works"),
        (11, 3, 2, "Embeddings Explained"),
        (11, 4, 2, "Chunking Strategies"),
        (11, 5, 2, "RAG as an Agent Tool"),
        (12, 1, 2, "Document Ingestion"),
        (12, 2, 2, "Text Splitting & Chunking"),
        (12, 3, 2, "Embedding & Storage"),
        (12, 4, 2, "Retrieval & Reranking"),
        (12, 5, 2, "End-to-End RAG Pipeline"),
        (13, 1, 2, "Vector DB Overview"),
        (13, 2, 2, "Chroma DB Setup"),
        (13, 3, 2, "Indexing & Searching"),
        (13, 4, 2, "Metadata Filtering"),
        (13, 5, 2, "Production Vector DB Patterns"),
        (14, 1, 2, "Beyond Pure Vector Search"),
        (14, 2, 2, "BM25 Keyword Search"),
        (14, 3, 2, "Hybrid Search"),
        (14, 4, 2, "Reranking with Cross-Encoders"),
        (14, 5, 2, "Building a Hybrid Search Agent"),
        (15, 1, 2, "Why Multiple Agents?"),
        (15, 2, 2, "Orchestrator Pattern"),
        (15, 3, 2, "Peer-to-Peer Pattern"),
        (15, 4, 2, "Pipeline Pattern"),
        (15, 5, 2, "Choosing the Right Pattern"),
        (16, 1, 2, "Communication Patterns"),
        (16, 2, 2, "Message Passing"),
        (16, 3, 2, "Shared State"),
        (16, 4, 2, "Negotiation & Consensus"),
        (16, 5, 2, "Building a Multi-Agent Chat"),
        # Days 17-20
        (17, 1, 2, "Designing a Research Agent"),
        (17, 2, 2, "Web Search & Scraping Tools"),
        (17, 3, 2, "Source Evaluation"),
        (17, 4, 2, "Synthesis & Summarization"),
        (17, 5, 2, "Building the Full Research Agent"),
        (18, 1, 2, "Designing a Code Review Agent"),
        (18, 2, 2, "Reading Code & Diffs"),
        (18, 3, 2, "Static Analysis Integration"),
        (18, 4, 2, "Writing Review Comments"),
        (18, 5, 2, "Building the Full Code Review Agent"),
        (19, 1, 2, "Designing a Support Agent"),
        (19, 2, 2, "Knowledge Base Integration"),
        (19, 3, 2, "Intent Classification"),
        (19, 4, 2, "Escalation & Handoff"),
        (19, 5, 2, "Building the Full Support Agent"),
        (20, 1, 2, "Why Evaluate Agents?"),
        (20, 2, 2, "Defining Success Metrics"),
        (20, 3, 2, "LLM-as-Judge"),
        (20, 4, 2, "Building Eval Datasets"),
        (20, 5, 2, "Running Evaluations"),
        # Days 21-25 (Frameworks)
        (21, 1, 2, "LangChain Overview"),
        (21, 2, 2, "Building a Chain"),
        (21, 3, 2, "LangChain Tools & Agents"),
        (21, 4, 2, "LangChain Memory"),
        (21, 5, 2, "LangChain RAG Agent"),
        (22, 1, 2, "LlamaIndex Overview"),
        (22, 2, 2, "Building an Index"),
        (22, 3, 2, "Query Engines"),
        (22, 4, 2, "LlamaIndex Agents"),
        (22, 5, 2, "LlamaIndex + LangChain Together"),
        (23, 1, 2, "CrewAI Overview"),
        (23, 2, 2, "Defining Agents & Roles"),
        (23, 3, 2, "Tasks & Workflows"),
        (23, 4, 2, "Building a Content Crew"),
        (23, 5, 2, "Advanced Crew Patterns"),
        (24, 1, 2, "AutoGen Overview"),
        (24, 2, 2, "AssistantAgent & UserProxyAgent"),
        (24, 3, 2, "Group Chat"),
        (24, 4, 2, "Code Execution Agents"),
        (24, 5, 2, "Building a Dev Team with AutoGen"),
        (25, 1, 2, "OpenAI Agents SDK Overview"),
        (25, 2, 2, "Building an Agent"),
        (25, 3, 2, "Handoffs"),
        (25, 4, 2, "Guardrails"),
        (25, 5, 2, "Multi-Agent Workflow"),
        # Days 26-30
        (26, 1, 2, "Why Planning Matters"),
        (26, 2, 2, "Chain-of-Thought"),
        (26, 3, 2, "ReAct Pattern"),
        (26, 4, 2, "Tree-of-Thought"),
        (26, 5, 2, "Building a Planning Agent"),
        (27, 1, 2, "Web Scraping Fundamentals"),
        (27, 2, 2, "Scraping Tools for Agents"),
        (27, 3, 2, "Handling JavaScript Pages"),
        (27, 4, 2, "Structured Data Extraction"),
        (27, 5, 2, "Building a Scraping Agent"),
        (28, 1, 2, "API Integration Patterns"),
        (28, 2, 2, "Authentication & API Keys"),
        (28, 3, 2, "Building API Tools"),
        (28, 4, 2, "Rate Limiting & Pagination"),
        (28, 5, 2, "Building an API Integration Agent"),
        (29, 1, 2, "Document Types & Challenges"),
        (29, 2, 2, "PDF Processing"),
        (29, 3, 2, "OCR & Image Processing"),
        (29, 4, 2, "Structured Extraction"),
        (29, 5, 2, "Building a Document Agent"),
        (30, 1, 2, "Designing a Data Agent"),
        (30, 2, 2, "SQL & Database Tools"),
        (30, 3, 2, "Data Visualization"),
        (30, 4, 2, "Statistical Analysis"),
        (30, 5, 2, "Building the Full Data Agent"),
        # Days 31-35
        (31, 1, 2, "Long-Term Memory Architecture"),
        (31, 2, 2, "Episodic Memory"),
        (31, 3, 2, "Semantic Memory"),
        (31, 4, 2, "Memory Retrieval Patterns"),
        (31, 5, 2, "Building a Long-Term Memory Agent"),
        (32, 1, 2, "Designing a Writing Agent"),
        (32, 2, 2, "Blog Post Generation"),
        (32, 3, 2, "Social Media Content"),
        (32, 4, 2, "Marketing Copy"),
        (32, 5, 2, "Building the Full Writing Agent"),
        (33, 1, 2, "Email Agent Architecture"),
        (33, 2, 2, "Email Parsing & Understanding"),
        (33, 3, 2, "Drafting Responses"),
        (33, 4, 2, "Email Organization"),
        (33, 5, 2, "Building the Full Email Agent"),
        (34, 1, 2, "Scheduling Agent Architecture"),
        (34, 2, 2, "Calendar Integration"),
        (34, 3, 2, "Availability & Conflict Detection"),
        (34, 4, 2, "Meeting Scheduling Logic"),
        (34, 5, 2, "Building the Full Scheduling Agent"),
        (35, 1, 2, "Capstone Planning"),
        (35, 2, 2, "Building the Orchestrator"),
        (35, 3, 2, "Building Specialist Agents"),
        (35, 4, 2, "Integration & Testing"),
        (35, 5, 2, "Capstone Presentation"),
        # Days 36-40 (Advanced)
        (36, 1, 3, "Framework Comparison Criteria"),
        (36, 2, 3, "LangChain vs LlamaIndex"),
        (36, 3, 3, "CrewAI vs AutoGen"),
        (36, 4, 3, "Raw API vs Frameworks"),
        (36, 5, 3, "Building a Framework-Agnostic Agent"),
        (37, 1, 3, "What is Self-Improvement?"),
        (37, 2, 3, "Reflection Pattern"),
        (37, 3, 3, "Self-Correction"),
        (37, 4, 3, "Learning from Feedback"),
        (37, 5, 3, "Building a Self-Improving Agent"),
        (38, 1, 3, "Why Guardrails Matter"),
        (38, 2, 3, "Input Validation"),
        (38, 3, 3, "Output Filtering"),
        (38, 4, 3, "PII Detection & Redaction"),
        (38, 5, 3, "Building a Guardrail System"),
        (39, 1, 3, "Understanding Agent Costs"),
        (39, 2, 3, "Caching Strategies"),
        (39, 3, 3, "Model Routing"),
        (39, 4, 3, "Token Budgeting"),
        (39, 5, 3, "Building a Cost-Optimized Agent"),
        (40, 1, 3, "Production Readiness Checklist"),
        (40, 2, 3, "Containerization"),
        (40, 3, 3, "Serverless Deployment"),
        (40, 4, 3, "Environment Management"),
        (40, 5, 3, "CI/CD for Agents"),
        # Days 41-45
        (41, 1, 3, "What to Monitor"),
        (41, 2, 3, "Logging Agent Traces"),
        (41, 3, 3, "Alerting"),
        (41, 4, 3, "Dashboards"),
        (41, 5, 3, "Building a Monitoring Stack"),
        (42, 1, 3, "Agent as a Product"),
        (42, 2, 3, "User Onboarding"),
        (42, 3, 3, "Feedback Loops"),
        (42, 4, 3, "Pricing & Monetization"),
        (42, 5, 3, "Go-to-Market Strategy"),
        (43, 1, 3, "Why Agent Auth Matters"),
        (43, 2, 3, "API Key Management"),
        (43, 3, 3, "Role-Based Access Control"),
        (43, 4, 3, "OAuth & SSO"),
        (43, 5, 3, "Building an Auth Layer"),
        (44, 1, 3, "Why Rate Limit?"),
        (44, 2, 3, "Rate Limiting Algorithms"),
        (44, 3, 3, "Queue Management"),
        (44, 4, 3, "Backpressure & Load Shedding"),
        (44, 5, 3, "Building a Rate-Limited Agent"),
        (45, 1, 3, "Designing a Dev Agent"),
        (45, 2, 3, "Code Reading & Analysis"),
        (45, 3, 3, "Automated Code Review"),
        (45, 4, 3, "PR Creation & Management"),
        (45, 5, 3, "Building the Full Dev Agent"),
        # Days 46-50
        (46, 1, 3, "Designing a Sales Agent"),
        (46, 2, 3, "Lead Research & Qualification"),
        (46, 3, 3, "Outreach Generation"),
        (46, 4, 3, "CRM Integration"),
        (46, 5, 3, "Building the Full Sales Agent"),
        (47, 1, 3, "Designing a Legal Agent"),
        (47, 2, 3, "Legal Document Processing"),
        (47, 3, 3, "Case Law Search"),
        (47, 4, 3, "Contract Analysis"),
        (47, 5, 3, "Building the Full Legal Agent"),
        (48, 1, 3, "Designing a Triage Agent"),
        (48, 2, 3, "Medical Knowledge Integration"),
        (48, 3, 3, "Symptom Assessment Logic"),
        (48, 4, 3, "Safety & Disclaimers"),
        (48, 5, 3, "Building the Full Triage Agent"),
        (49, 1, 3, "Designing a Finance Agent"),
        (49, 2, 3, "Financial Data Sources"),
        (49, 3, 3, "Analysis & Insights"),
        (49, 4, 3, "Report Generation"),
        (49, 5, 3, "Building the Full Finance Agent"),
        (50, 1, 3, "Designing an Education Agent"),
        (50, 2, 3, "Knowledge Base & Curriculum"),
        (50, 3, 3, "Adaptive Questioning"),
        (50, 4, 3, "Quiz Generation"),
        (50, 5, 3, "Building the Full Education Agent"),
        # Days 51-55
        (51, 1, 3, "Testing Agent Logic"),
        (51, 2, 3, "Integration Testing"),
        (51, 3, 3, "Eval Datasets & Benchmarks"),
        (51, 4, 3, "Regression Testing"),
        (51, 5, 3, "Building a Test Suite"),
        (52, 1, 3, "What is Prompt Injection?"),
        (52, 2, 3, "Injection Techniques"),
        (52, 3, 3, "Defense Strategies"),
        (52, 4, 3, "Jailbreak Prevention"),
        (52, 5, 3, "Building a Security Layer"),
        (53, 1, 3, "When to Fine-Tune"),
        (53, 2, 3, "Preparing Training Data"),
        (53, 3, 3, "Fine-Tuning Process"),
        (53, 4, 3, "Evaluating Fine-Tuned Models"),
        (53, 5, 3, "Building a Fine-Tuned Agent"),
        (54, 1, 3, "Why Go Local?"),
        (54, 2, 3, "Ollama Setup"),
        (54, 3, 3, "llama.cpp & GGUF"),
        (54, 4, 3, "vLLM for Production"),
        (54, 5, 3, "Building a Local Agent"),
        (55, 1, 3, "Scaling Challenges"),
        (55, 2, 3, "Workflow Engines"),
        (55, 3, 3, "Load Balancing"),
        (55, 4, 3, "State Management"),
        (55, 5, 3, "Building a Scalable Orchestrator"),
        # Days 56-60
        (56, 1, 3, "Agent Marketplace Concept"),
        (56, 2, 3, "Agent Packaging"),
        (56, 3, 3, "Discovery & Search"),
        (56, 4, 3, "Billing & Usage Tracking"),
        (56, 5, 3, "Building a Marketplace"),
        (57, 1, 3, "Voice Agent Architecture"),
        (57, 2, 3, "Speech-to-Text"),
        (57, 3, 3, "Text-to-Speech"),
        (57, 4, 3, "Real-Time Voice"),
        (57, 5, 3, "Building a Voice Agent"),
        (58, 1, 3, "Vision Agent Architecture"),
        (58, 2, 3, "Image Understanding"),
        (58, 3, 3, "Screenshot & UI Analysis"),
        (58, 4, 3, "Video Processing"),
        (58, 5, 3, "Building a Vision Agent"),
        (59, 1, 3, "Agent UX Principles"),
        (59, 2, 3, "Conversational Patterns"),
        (59, 3, 3, "Feedback & Confidence"),
        (59, 4, 3, "Error Recovery UX"),
        (59, 5, 3, "Designing Agent Interfaces"),
        (60, 1, 3, "Capstone Planning"),
        (60, 2, 3, "Core Agent Build"),
        (60, 3, 3, "Memory & RAG"),
        (60, 4, 3, "Testing & Hardening"),
        (60, 5, 3, "Capstone Launch"),
    ]

def build_curriculum_js():
    """Build the JavaScript CURRICULUM array."""
    lines = []
    for day, lesson, phase, title in get_curriculum():
        lines.append(f'  {{day:{day},lesson:{lesson},phase:{phase},title:"{title}"}},')
    return '\n'.join(lines)

def generate_lesson_content(day, lesson, phase, title):
    """Generate the HTML content for a single lesson via LLM."""
    phase_names = ['', 'Foundations', 'Intermediate', 'Advanced']
    phase_name = phase_names[phase]

    prompt = f"""Write the HTML content for a tutorial lesson page about AI agents. Output ONLY the HTML content that goes between the lesson header and the navigation section.

Lesson: Day {day}, Lesson {lesson} — "{title}"
Phase: {phase} ({phase_name})

The content should include:
- Multiple <h2> and <h3> sections explaining concepts clearly
- <p> paragraphs with clear, beginner-friendly explanations
- <pre><code> blocks with real Python code examples
- <ul>/<ol> lists where appropriate
- Callout boxes using: <div class="callout callout-info">, <div class="callout callout-tip">, <div class="callout callout-warn">
- At least one coding exercise with a revealable answer using: <div class="exercise"><div class="exercise-header">Exercise</div><div class="exercise-body">...</div></div> and <div class="answer-reveal"><button class="btn" onclick="toggleAnswer('answer-1')">Show Answer</button><div class="answer-content" id="answer-1">...</div></div>
- A comparison table using <table> where relevant
- A "Key Takeaways" section at the end with <ul> bullet points
- A brief "In the next lesson..." paragraph at the end

IMPORTANT: Output ONLY the raw HTML content. No markdown, no code fences, no explanations before or after. Start with the first <h2> tag and end after the Key Takeaways section."""

    return llm_call(prompt, max_tokens=6000)

def generate_day(day_num):
    """Generate all 5 lessons for a given day."""
    curriculum = get_curriculum()
    day_lessons = [(d, l, p, t) for d, l, p, t in curriculum if d == day_num]

    if not day_lessons:
        print(f"ERROR: Day {day_num} not found in curriculum")
        return False

    print(f"Generating Day {day_num} ({len(day_lessons)} lessons)...")

    # Check which lessons already exist
    existing = []
    for d, l, p, t in day_lessons:
        fpath = os.path.join(TUTORIAL_DIR, slug(d, l) + '.html')
        if os.path.exists(fpath) and os.path.getsize(fpath) > 100:
            existing.append(slug(d, l))
            print(f"  {slug(d,l)}.html already exists ({os.path.getsize(fpath):,} bytes), skipping")

    if len(existing) == 5:
        print(f"  All 5 lessons for Day {day_num} already exist!")
        return True

    curriculum_js = build_curriculum_js()

    for d, l, p, t in day_lessons:
        fname = slug(d, l) + '.html'
        fpath = os.path.join(TUTORIAL_DIR, fname)

        if os.path.exists(fpath) and os.path.getsize(fpath) > 100:
            continue

        print(f"  Generating {fname} ({t})...")

        # Get content from LLM
        content = generate_lesson_content(d, l, p, t)
        if not content:
            print(f"  FAILED to generate content for {fname}")
            continue

        # Clean up content - remove markdown code fences if present
        content = content.strip()
        if content.startswith('```html'):
            content = content[7:]
        if content.startswith('```'):
            content = content[3:]
        if content.endswith('```'):
            content = content[:-3]
        content = content.strip()

        # Build prev/next links
        prev_link = ""
        next_link = ""
        if l > 1:
            prev_file = slug(d, l-1) + '.html'
            prev_titles = [title for dd, ll, pp, title in day_lessons if ll == l-1]
            prev_title = prev_titles[0] if prev_titles else f"Lesson {l-1}"
            prev_link = f'<a href="{prev_file}" class="btn btn-secondary">&larr; Previous: {prev_title}</a>'
        elif d > 1:
            prev_file = slug(d-1, 5) + '.html'
            prev_link = f'<a href="{prev_file}" class="btn btn-secondary">&larr; Previous: Day {d-1}, Lesson 5</a>'

        if l < 5:
            next_file = slug(d, l+1) + '.html'
            next_titles = [title for dd, ll, pp, title in day_lessons if ll == l+1]
            next_title = next_titles[0] if next_titles else f"Lesson {l+1}"
            next_link = f'<a href="{next_file}" class="btn btn-secondary">Next: {next_title} &rarr;</a>'
        elif d < 60:
            next_file = slug(d+1, 1) + '.html'
            next_link = f'<a href="{next_file}" class="btn btn-secondary">Next: Day {d+1}, Lesson 1 &rarr;</a>'

        phase_names = ['', 'Foundations', 'Intermediate', 'Advanced']
        phase_name = phase_names[p]

        # Build full HTML page
        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{t} — AI Training</title>
<link rel="stylesheet" href="../assets/style.css">
</head>
<body>

<button class="sidebar-toggle" onclick="toggleSidebar()">&#9776;</button>
<div class="sidebar-overlay" id="sidebarOverlay" onclick="toggleSidebar()"></div>

<nav class="sidebar" id="sidebar">
  <div class="sidebar-header">
    <h1>&#x1F916; AI Training</h1>
    <p>Learn to Build AI Agents</p>
  </div>
  <div class="progress-bar-container">
    <div class="progress-label">
      <span>Progress</span>
      <span id="progressText">0%</span>
    </div>
    <div class="progress-bar">
      <div class="progress-fill" id="progressFill"></div>
    </div>
  </div>
  <div id="nav-items"></div>
</nav>

<main class="main">
<div class="content">

<div class="lesson active" id="lesson-{d}-{l}">
  <div class="lesson-header">
    <div class="breadcrumb"><a href="../index.html">Home</a> / <a href="../index.html#phase-{p}">Phase {p}</a> / Day {d}, Lesson {l}</div>
    <div class="lesson-number">Day {d}, Lesson {l} of 5</div>
    <h1 class="lesson-title">{t}</h1>
    <p class="lesson-desc">Learn about {t.lower()}.</p>
  </div>

{content}

  <div class="lesson-nav">
    {prev_link}
    {next_link}
  </div>

  <div class="mark-complete">
    <div class="status" id="status-{d}-{l}">
      <span>&#x2610;</span> Mark this lesson complete
    </div>
    <button class="btn btn-primary" onclick="markLessonComplete({d}, {l})">
      Mark Complete
    </button>
  </div>
</div>

</div>
</main>

<script src="../assets/app.js"></script>
<script>
const CURRICULUM = [
{curriculum_js}
];

const CURRENT_DAY = {d};
const CURRENT_LESSON = {l};

function lessonSlug(d, l) {{
  return String(d).padStart(2,'0') + String(l).padStart(2,'0');
}}

function buildNav() {{
  const container = document.getElementById('nav-items');
  let html = '';
  let currentPhase = 0;
  let currentDay = 0;
  CURRICULUM.forEach(t => {{
    if (t.phase !== currentPhase) {{
      if (currentPhase > 0) html += '</div>';
      currentPhase = t.phase;
      currentDay = 0;
      const labels = ['','Foundations','Intermediate','Advanced'];
      html += '<div class="nav-section"><div class="nav-section-title">Phase ' + t.phase + ': ' + labels[t.phase] + '</div>';
    }}
    if (t.day !== currentDay) {{
      if (currentDay > 0) html += '</div>';
      currentDay = t.day;
      html += '<div class="nav-day-group' + (t.day === CURRENT_DAY ? ' open' : '') + '" id="nav-day-' + t.day + '">';
      html += '<div class="nav-day-header" onclick="toggleNavDay(' + t.day + ')">Day ' + t.day + '</div>';
      html += '<div class="nav-lessons" id="nav-lessons-' + t.day + '">';
    }}
    const active = (t.day === CURRENT_DAY && t.lesson === CURRENT_LESSON) ? ' active' : '';
    const file = lessonSlug(t.day, t.lesson) + '.html';
    html += '<a class="nav-item' + active + '" href="' + file + '" data-day="' + t.day + '" data-lesson="' + t.lesson + '">';
    html += '<span class="nav-check" id="check-' + t.day + '-' + t.lesson + '">&#10003;</span> ';
    html += '<span class="nav-lesson-num">' + t.lesson + '</span> ' + t.title + '</a>';
  }});
  html += '</div></div>';
  container.innerHTML = html;
}}

function toggleNavDay(day) {{
  const el = document.getElementById('nav-lessons-' + day);
  if (el) el.classList.toggle('collapsed');
}}

function markLessonComplete(day, lesson) {{
  try {{
    const key = 'ai_training_completed';
    let completed = JSON.parse(localStorage.getItem(key) || '[]');
    const lessonKey = day + '-' + lesson;
    if (!completed.includes(lessonKey)) {{
      completed.push(lessonKey);
      localStorage.setItem(key, JSON.stringify(completed));
    }}
    const status = document.getElementById('status-' + day + '-' + lesson);
    if (status) {{ status.innerHTML = '<span>\\u2705</span> Completed'; status.classList.add('done'); }}
    const total = 300;
    const pct = Math.round((completed.length / total) * 100);
    const fill = document.getElementById('progressFill');
    const text = document.getElementById('progressText');
    if (fill) fill.style.width = pct + '%';
    if (text) text.textContent = pct + '%';
    const check = document.getElementById('check-' + day + '-' + lesson);
    if (check) {{ check.innerHTML = '\\u2713'; check.style.color = 'var(--green)'; }}
  }} catch(e) {{}}
}}

document.addEventListener('DOMContentLoaded', function() {{
  buildNav();
  try {{
    const completed = JSON.parse(localStorage.getItem('ai_training_completed') || '[]');
    const pct = Math.round((completed.length / 300) * 100);
    const fill = document.getElementById('progressFill');
    const text = document.getElementById('progressText');
    if (fill) fill.style.width = pct + '%';
    if (text) text.textContent = pct + '%';
    completed.forEach(key => {{
      const parts = key.split('-');
      if (parts.length === 2) {{
        const check = document.getElementById('check-' + parts[0] + '-' + parts[1]);
        const nav = document.querySelector('.nav-item[data-day="' + parts[0] + '"][data-lesson="' + parts[1] + '"]');
        if (check) {{ check.innerHTML = '\\u2713'; check.style.color = 'var(--green)'; }}
        if (nav) nav.classList.add('completed');
      }}
    }});
    const status = document.getElementById('status-' + CURRENT_DAY + '-' + CURRENT_LESSON);
    if (status && completed.includes(CURRENT_DAY + '-' + CURRENT_LESSON)) {{
      status.innerHTML = '<span>\\u2705</span> Completed';
      status.classList.add('done');
    }}
  }} catch(e) {{}}
}});
</script>
</body>
</html>'''

        # Write file
        with open(fpath, 'w') as f:
            f.write(html)

        fsize = os.path.getsize(fpath)
        print(f"  Written {fname} ({fsize:,} bytes)")

        # Small delay between API calls
        time.sleep(3)

    return True

def update_state(day_num):
    """Update state.json to next day."""
    state = {"next_day": day_num + 1, "next_lesson": 1}
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)
    print(f"Updated state.json: next_day={day_num + 1}")

def update_generated(day_num):
    """Update generated.json with new lessons."""
    if os.path.exists(GENERATED_FILE):
        with open(GENERATED_FILE) as f:
            data = json.load(f)
    else:
        data = {"lessons": [], "last_updated": ""}

    for l in range(1, 6):
        s = slug(day_num, l)
        if s not in data["lessons"]:
            data["lessons"].append(s)

    data["last_updated"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    with open(GENERATED_FILE, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Updated generated.json: {len(data['lessons'])} total lessons")

def git_push(day_num):
    """Git add, commit, and push."""
    os.chdir(BASE)
    subprocess.run(['git', 'add', '.'], check=True)
    result = subprocess.run(
        ['git', 'commit', '-m', f'Generate Day {day_num} lessons 1-5 ({time.strftime("%Y-%m-%d")})'],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        print(f"Git committed successfully")
    else:
        print(f"Git commit: {result.stderr}")

    result = subprocess.run(['git', 'push', 'origin', 'main'], capture_output=True, text=True)
    if result.returncode == 0:
        print(f"Git pushed successfully")
    else:
        print(f"Git push error: {result.stderr}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 generate_day.py <day_number>")
        sys.exit(1)

    day_num = int(sys.argv[1])
    if day_num < 1 or day_num > 60:
        print("Day must be between 1 and 60")
        sys.exit(1)

    print(f"=== AI Training Generator: Day {day_num} ===")
    print(f"OpenRouter API key: {API_KEY[:10]}...")

    success = generate_day(day_num)
    if success:
        update_state(day_num)
        update_generated(day_num)
        git_push(day_num)
        print(f"\nDay {day_num} complete!")
    else:
        print(f"\nDay {day_num} generation failed!")
        sys.exit(1)
