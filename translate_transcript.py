#!/usr/bin/env python3
"""Translate transcript to Ukrainian using Claude CLI, chunk by chunk with resume support."""

import subprocess
import os
import sys
import time

INPUT = "/home/user/openclaw/transcript_n8n_full_course_2026.txt"
OUTPUT = "/home/user/openclaw/transcript_n8n_full_course_2026_uk.txt"
PROGRESS = "/home/user/openclaw/translate_progress.txt"
CHUNK_LINES = 250
PROMPT = "Translate the following English text to Ukrainian. Return ONLY the Ukrainian translation, no explanations, no English text:"

def read_progress():
    if os.path.exists(PROGRESS):
        with open(PROGRESS) as f:
            return int(f.read().strip())
    return 0

def save_progress(line_num):
    with open(PROGRESS, "w") as f:
        f.write(str(line_num))

def translate_chunk(text):
    result = subprocess.run(
        ["claude", "-p", PROMPT],
        input=text, capture_output=True, text=True, timeout=120
    )
    if result.returncode != 0:
        raise RuntimeError(f"Claude CLI error: {result.stderr[:200]}")
    return result.stdout.strip()

with open(INPUT) as f:
    lines = f.readlines()

total_lines = len(lines)
start_line = read_progress()

if start_line >= total_lines:
    print("Already complete.")
    sys.exit(0)

mode = "a" if start_line > 0 else "w"
print(f"Total lines: {total_lines}, starting from line {start_line}")

with open(OUTPUT, mode) as out:
    chunk_num = start_line // CHUNK_LINES
    line = start_line
    while line < total_lines:
        end = min(line + CHUNK_LINES, total_lines)
        chunk = "".join(lines[line:end])
        chunk_num += 1
        print(f"Chunk {chunk_num}: lines {line+1}-{end} ({end-line} lines)...", flush=True)
        try:
            translated = translate_chunk(chunk)
            out.write(translated + "\n")
            out.flush()
            save_progress(end)
            line = end
            print(f"  -> OK ({len(translated)} chars)", flush=True)
        except Exception as e:
            print(f"  -> ERROR: {e}, retrying in 5s...", flush=True)
            time.sleep(5)
            try:
                translated = translate_chunk(chunk)
                out.write(translated + "\n")
                out.flush()
                save_progress(end)
                line = end
                print(f"  -> OK on retry ({len(translated)} chars)", flush=True)
            except Exception as e2:
                print(f"  -> FATAL: {e2}, skipping chunk", flush=True)
                out.write(chunk)  # write original if translation fails
                out.flush()
                save_progress(end)
                line = end

print(f"Done! Output: {OUTPUT}")
if os.path.exists(PROGRESS):
    os.remove(PROGRESS)
