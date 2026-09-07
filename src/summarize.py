# Runs on a schedule after fetch.py finishes.
# Passes current database state to the LLM (Gemini/Groq) to write a text overview of the FBS[cite: 1].
# Outputs to data/summary.md.
# STATUS: SOURCE data. Must be committed to git[cite: 1].