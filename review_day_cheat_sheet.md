# BioNEET Pro - Final Review Day Cheat Sheet

This is your ultimate quick-reference guide for tomorrow's review. Keep this open during your presentation!

---

## 🚀 1. The 60-Second Project Walkthrough

If the examiner asks: **"Explain your project from start to finish."**

> *"**BioNEET Pro** is a modern preparation portal for NEET Biology aspirants. It is built as a cross-platform desktop app using **Electron** and a web application using **React**. 
>
> **The student flow works like this:**
> 1. The student logs in (real authentication via **Firebase Auth** or offline via **Demo Mode**).
> 2. They access a dashboard showing study streaks, NCERT syllabus progress, and study plans.
> 3. They practice timed chapter-wise or mixed mock tests with a customized **OMR Answer Sheet** and keyboard hotkeys (`1-4`) for quick responses.
> 4. If they get stuck, they query our **AI Tutor** which gives context-aware, NCERT-focused doubt solving.
> 5. They review active-recall **Flashcards** managed by a **Leitner spaced repetition system** (1, 3, 7, 14, 30 days) to lock in memory.
> 6. All scores are processed by a **Score Predictor** that runs a weighted NEET algorithm to output target scores and confidence intervals, and their results are posted to a real-time global **Leaderboard**."*

---

## 💻 2. What Tech Stack Did You Use?

If the examiner asks: **"What technologies did you use to build this?"**

Tell them:
1.  **Frontend (UI):** **HTML5**, **CSS3 (Vanilla CSS)** for premium layouts/animations, **React 18** with **TypeScript** for type-safe, component-driven logic, and **Vite** as our build/dev runner.
2.  **Desktop Container:** **Electron**, which wraps our React build bundle into a native Windows desktop executable.
3.  **Backend & Algorithmic Engine:** **Python 3** with **Flask**, **scikit-learn**, and **pandas** running our local Information Retrieval and Knowledge Tracing engine.
4.  **Local Datasets:** Kaggle-compatible NCERT knowledge base (`data/neet_knowledge_base.csv`), concept dependency graph (`data/concept_dependency_graph.csv`), and real-time student learning trajectory tracker (`data/student_learning_tracker.csv`).
5.  **Database & Cloud:** **Google Firebase (Authentication & Cloud Firestore)** for user profiles, synced test scores, and leaderboard tracking.

---

## 🤖 3. How Does the AI Tutor Work? (Addressing Reviewer Feedback)

If the examiner asks: **"What work are you doing in the AI tutor? Are you just using an external API?"**

Tell them:
> *"**No, sir/ma'am.** In response to your guidance, we developed our own **Local Algorithmic Intelligent Tutoring System (ITS)** that runs 100% offline on the laptop without needing any external cloud API:*
> 
> 1. **Local Dataset (`data/neet_knowledge_base.csv`):** A curated 12-column dataset covering core NCERT concepts across all chapters, containing formal definitions, biological mechanism steps, high-yield NEET traps, and diagnostic questions.
> 2. **Algorithm 1: Semantic Concept Mapping via Vector Space Model ($\text{TF-IDF} \times \text{Cosine Similarity}$):**
>    - Preprocesses the student's natural language query using unigram + bigram n-grams.
>    - Computes vector dot-product cosine similarity against all concept rows in our local CSV:
>      $$\cos(\theta) = \frac{\mathbf{q} \cdot \mathbf{d}}{\|\mathbf{q}\|_2 \|\mathbf{d}\|_2}$$
>    - Maps to the exact NCERT concept in under 15 milliseconds on the local CPU.
> 3. **Algorithm 2: 4-Step Socratic Pedagogical State Machine:**
>    - Instead of a single text dump, the system tracks learning step-by-step:
>      $$\text{Step 1: Concept Anchor} \rightarrow \text{Step 2: Mechanism} \rightarrow \text{Step 3: NEET Traps} \rightarrow \text{Step 4: Diagnostic Quiz}$$
> 4. **Algorithm 3: Bayesian Knowledge Tracing (BKT):**
>    - Evaluates student answers in Step 4 to dynamically update their concept mastery probability $P(L_t)$:
>      $$P(L_t \mid \text{Action}) \rightarrow P(L_t) = P(L_t \mid \text{Action}) + (1 - P(L_t \mid \text{Action})) \cdot P(T)$$
> 5. **Local Step-by-Step Tracking (`data/student_learning_tracker.csv`):**
>    - Every single query, similarity score, step transition, and updated mastery score is appended to local disk in CSV format for auditability.
> 6. **Cloud Fallback:** An optional LLM gateway is kept purely as an optional auxiliary mode, but all core intelligence, retrieval, and tracking are executed by our own local Python algorithms."*

---

## 🏆 4. Top 5 Expected Viva Questions & Answers

### Q1: Why did you choose Firestore over SQL databases?
> [!NOTE]
> *Firestore is a NoSQL Document Database that supports real-time synchronization. In a student platform, features like active leaderboards and syllabus updates need instant, live updates on the client side without constant polling. Firestore handles this out of the box using live snapshots.*

### Q2: What is the benefit of the Electron container?
> [!IMPORTANT]
> *It allows us to compile the web application into a native desktop app (.exe for Windows). It runs locally on the student's machine with native desktop performance, allows offline access to cached MCQ sheets, and encapsulates all web code inside a secure local sandbox.*

### Q3: How did you handle CORS errors during development?
> [!TIP]
> *Since our frontend runs on Live Server (port 5500) or Vite (port 5173), and the Flask backend runs on port 5000, browsers block requests due to cross-origin security rules. We resolved this by configuring `flask-cors` on the backend and specifying our frontend ports in the `ALLOWED_ORIGINS` setting inside `.env.local`.*

### Q4: Why use TypeScript instead of plain JavaScript?
> [!NOTE]
> *TypeScript adds strict type definitions to JavaScript at compile-time. This prevents common bugs (like accessing undefined properties or passing wrong arguments) before the app even runs, ensuring our MCQ engine and scoring data structures are completely type-safe.*

### Q5: How does the Leitner system in flashcards improve memory?
> [!TIP]
> *It is a spaced-repetition algorithm. Flashcards are sorted into boxes 1 to 5 representing study intervals (1, 3, 7, 14, 30 days). Correct answers move cards to higher boxes (longer delays), while any incorrect answer resets the card instantly back to Box 1. This prioritizes studying weak concepts frequently.*
