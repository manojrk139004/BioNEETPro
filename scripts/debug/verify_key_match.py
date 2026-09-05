"""Check whether the key in .env.local byte-matches the dashboard key.

Usage:  python verify_key_match.py
Then paste the FULL key from the NaraRouter dashboard when prompted
(input is hidden, nothing is printed except MATCH/MISMATCH + lengths).

Security: key material is never printed, logged, or written anywhere.
"""
import getpass

configured = ""
for line in open(".env.local", encoding="utf-8-sig").read().splitlines():
    s = line.strip()
    if s.startswith("OPENROUTER_API_KEY"):
        configured = s.split("=", 1)[1].strip().strip('"').strip("'")

typed = getpass.getpass("Paste dashboard key (hidden): ").strip()
print("configured len:", len(configured), "| pasted len:", len(typed))
print("MATCH:", typed == configured and len(configured) > 0)
if typed != configured:
    print("MISMATCH: copy the full key again (click reveal -> copy) or rotate it,")
    print("then update ONLY the value after OPENROUTER_API_KEY= in .env.local")
