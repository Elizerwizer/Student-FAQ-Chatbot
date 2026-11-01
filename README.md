# AIOU Student FAQ Chatbot

A Python chatbot that answers student questions about admissions, assignments, examinations, scholarships, academic integrity and student services. It is designed primarily for students of Allama Iqbal Open University (AIOU), with Higher Education Commission (HEC) guidance used where relevant. The bot is built to run as a small web service and to be embedded in a webpage.

---

## 1. Project Information

| Item | Details |
|---|---|
| Project name | AIOU Student FAQ Chatbot |
| Language | Python 3 (backend), HTML/CSS/JavaScript (chat widget) |
| Framework | FastAPI (web API) |
| Matching method | Keyword, synonym and fuzzy matching (no external AI service required) |
| Target users | AIOU students |
| Intended deployment | Frontend on GitHub Pages, backend on a free Python host |
| Status | Working prototype. Knowledge base contains 10 starter records. |

### What the chatbot does
- Detects the intent of a question through keywords and question patterns.
- Retrieves the most relevant official guideline or FAQ entry.
- Returns a direct answer with the official source link and a contact point.
- Escalates to official AIOU/HEC contacts when the question is personal, time-sensitive or uncertain.
- Refuses requests to write assignments or exam answers, and refuses help with academic dishonesty.

---

## 2. Where the Information Came From

### 2.1 Project requirements
All behaviour, structure and rules came from the document **"Student FAQ & Answer AI — Build Instructions"**, supplied as the project brief. That document defined:
- The purpose and core behaviour of the assistant (Sections 1 and 2)
- Keyword and intent detection, including the keyword table and synonym mapping (Section 3)
- The knowledge-base record format and required metadata (Section 4)
- The topic and subtopic map (Section 5)
- The response templates (Section 6)
- The guardrails (Section 7) and escalation rules (Section 8)
- Quality checks and the maintenance plan (Sections 9 and 10)

### 2.2 Knowledge-base content
The facts stored in `knowledge_base.json` were taken only from statements made in the build-instructions document. No deadlines, fees or exam dates were invented.

| Knowledge-base topic | Fact taken from |
|---|---|
| Assignment submission (AAGHI LMS for BS/BEd/MA/MSc, postal for SSC/HSSC/AD(BA)) | Build instructions, Section 4.1 and 5.3, citing the AIOU CMS Guide for Students |
| Assignments counting toward results and exam eligibility | Build instructions, Section 5.3 |
| Online and manual admission | Build instructions, Section 5.1 |
| Passing marks differing by program level | Build instructions, Section 5.4 |
| Support email and phone numbers | Build instructions, Sections 4.1 and 8 |
| Student advisory office location | Build instructions, Section 8 |
| HEC scholarships | Build instructions, Section 5.7 |
| HEC plagiarism policy scope and similarity reports | Build instructions, Section 5.8 |

The build-instructions document marks its facts with reference numbers (for example [1], [5], [10]), but the matching URLs were not included in the document. Because of this, only one exact source link is available, and the other records point to the official AIOU and HEC home pages until exact pages are verified.

### 2.3 Hosting information
Hosting recommendations were gathered from web articles published in 2026:
- 7 Best FREE Platforms to Host Machine Learning Models (KDnuggets)
- 5 Free Ways to Host a Python Application (KDnuggets)
- Best Python Hosting Providers in 2026 (Fly.io)
- How to Host a Python Web App for Free in 2026 (SnapDeploy)
- Deployment platforms notes (tds.s-anand.net)

---

## 3. Links

### Official sources
| Purpose | Link |
|---|---|
| AIOU CMS Guide for Students (July 2026) | https://aiou.edu.pk/sites/default/files/2026-07/Student%20CMS%20Guide%20July%202026.pdf |
| AIOU official website | https://aiou.edu.pk |
| HEC official website | https://www.hec.gov.pk |

### Official contacts
| Office | Email | Phone |
|---|---|---|
| AIOU Support | support@aiou.edu.pk | 051-111-112-468 |
| AIOU Examination Support | exam@aiou.edu.pk | 051-9571701 |
| Directorate of Students Advisory & Counselling Services | Gateway Block, Sector H-8, Islamabad | – |

### Hosting references
| Topic | Link |
|---|---|
| Free ML and Python hosting platforms | https://www.kdnuggets.com/7-best-free-platforms-to-host-machine-learning-models |
| Free ways to host a Python application | https://www.kdnuggets.com/5-free-ways-to-host-a-python-application |
| Python hosting providers compared | https://fly.io/learn/python-hosting.md |
| Free Python web app hosting guide | https://snapdeploy.dev/blog/host-python-web-app-free-2026-guide |
| Deployment platform notes | https://tds.s-anand.net/2026-02/docs/week-2/07-deployment-platforms/ |

---

## 4. Project Structure

```
aiou_chatbot/
├── chatbot.py            # Chatbot engine (matching, guardrails, escalation)
├── knowledge_base.json   # Knowledge-base records
├── app.py                # FastAPI web server
├── index.html            # Chat widget / demo page
├── requirements.txt      # Python dependencies
└── README.md             # This file
```

---

## 5. How the Project Was Created (Step by Step)

### Step 1: Requirements were analysed
The build-instructions document was read to identify the required features: intent detection, a structured knowledge base, response templates, guardrails and escalation. The requirement to use the chatbot later in a webpage led to the choice of a web-API design.

### Step 2: The technology was chosen
Python was selected as the main language. The matching engine was written without external libraries (only the standard `difflib`, `json`, `re` and `pathlib` modules), so that it stays lightweight and easy to host. FastAPI was selected for the web layer because it is simple, fast and suited to a JSON chat API.

### Step 3: The knowledge base was created (`knowledge_base.json`)
Each record follows the format from Section 4.1 of the build instructions:
- `id`, `topic`, `subtopic`
- `keywords` and applicable `programs`
- `answer`
- `source` (title and URL)
- `last_verified`
- `contact` (name, email, phone)
- `confidence` level (high, medium or low)

Two extra optional flags were added: `time_sensitive` (adds a warning to check the latest notification) and `needs_program` (asks the student for their program before giving a program-dependent answer). The `last_verified` field was set to `TO_VERIFY` for every record, because the facts still have to be checked against the live official pages.

### Step 4: The chatbot engine was written (`chatbot.py`)
The engine follows the matching process from Section 3.1 of the build instructions:
1. **Normalisation.** Text is lowercased, punctuation and extra spaces are removed, and common spelling errors (for example "asignment") are corrected.
2. **Synonym mapping.** Variants are converted to a standard word (for example "homework" and "TMA" become "assignment", "enrollment" becomes "admission").
3. **Scoring.** Each knowledge-base record is scored. An exact phrase match scores highest. Fuzzy word matching (using `difflib`) handles small typing errors.
4. **Selection.** The highest-scoring record is chosen if its score passes a minimum threshold. Otherwise the "could not verify" message is returned.
5. **Response building.** The answer is formatted with the template from Section 6.1: answer, important note, official source and contact.

### Step 5: The guardrails were added
Guardrails from Section 7 of the build instructions were implemented as pattern checks that run before any lookup:
- Requests such as "write my assignment" are refused. The bot offers explanations, structure suggestions and citation help instead.
- The bot never claims access to personal student data.

### Step 6: The escalation rules were added
Escalation rules from Section 8 were implemented as pattern checks. Questions about personal results, payment or login problems, appeals or misconduct, and document verification or issuing trigger a referral to the correct official contact. Examination-related cases go to AIOU Examination Support. All other cases go to AIOU Support.

### Step 7: The web API was built (`app.py`)
A FastAPI application was created with:
- `POST /chat` to receive `{"message": "..."}` and return the reply text, source, contact, confidence and an `escalate` flag
- `GET /health` to confirm the service is running
- `GET /` to serve the demo page
- CORS middleware so that a webpage hosted on another domain can call the API

### Step 8: The chat widget was built (`index.html`)
A single-page chat interface was created using plain HTML, CSS and JavaScript. It sends messages to the `/chat` endpoint, displays replies, and converts the simple formatting (bold text and links) into HTML. All text is escaped before display to prevent script injection. The `API_URL` setting at the top of the script controls which backend address is called.

### Step 9: The project was tested
The engine was tested with sample student questions covering assignment submission, misspelled words, passing marks (with and without a program), scholarships, date sheets, similarity reports, cheating requests, off-topic questions and personal result complaints.

One problem was found during testing: a question about a personal result with no matching topic returned the generic "could not verify" message without any escalation. The engine was corrected so that personal-record questions are now escalated to the correct official contact even when no knowledge-base record matches.

## 6. How to Run the Project

### Install
```bash
pip install -r requirements.txt
```

### Start the server
```bash
uvicorn app:app --reload --port 8000
```
The demo page is available at `http://localhost:8000`.

### Use in the terminal only
```bash
python chatbot.py
```

### Test the API
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "How do I submit my assignment?"}'
```

### Example response fields
| Field | Meaning |
|---|---|
| `text` | Formatted reply shown to the student |
| `kind` | `answer`, `need_info`, `escalation`, `guardrail`, `no_match` or `empty` |
| `id` | Knowledge-base record used |
| `confidence` | Confidence level of that record |
| `escalate` | `true` when the student is directed to a human contact |
| `source` | Official source title and URL |
| `contact` | Contact details shown to the student |

---

## 8. Adding or Updating Knowledge

New topics are added by copying an existing record in `knowledge_base.json` and changing its fields. Each record needs:
- A unique ID (for example `AIOU-FEE-001`)
- Keywords (including common alternative wording)
- An answer taken only from an official source
- The exact source title and URL
- A real `last_verified` date
- A contact point and confidence level

Topics still to be added from the build-instructions topic map include fees and challans, results and transcripts, degree and certificate services, tutor and workshop details, and HEC graduate education requirements.

---

## 9. Known Limitations and Next Steps

- All `last_verified` values are `TO_VERIFY` and must be replaced after checking the official pages.
- Most source links point to the AIOU and HEC home pages and must be replaced with exact pages.
- The knowledge base contains only 10 records, so many valid questions will return the "could not verify" message.
- Matching is keyword-based and does not understand context in long or complex questions.
- Urdu and Roman Urdu support (mentioned as optional in the build instructions) has not been added.
- No logging of unanswered questions has been added yet. The maintenance plan recommends this to find missing topics.
- The semester review of AIOU sources and the twice-yearly review of HEC policies described in the maintenance plan still need to be scheduled.

---

## 10. Guardrails Summary

The chatbot does not:
- Invent deadlines, fee amounts, exam dates or policy rules
- Give legal, immigration, medical or financial investment advice
- Write assignments, exam answers or plagiarised content
- Help bypass institutional rules or support academic dishonesty
- Claim access to personal student data
- Make final decisions on appeals, misconduct cases, scholarships or degree issuance

For official decisions and personal records, students are always directed to AIOU or HEC.
