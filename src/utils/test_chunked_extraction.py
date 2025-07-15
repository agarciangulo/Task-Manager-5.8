#!/usr/bin/env python3
"""
Test script for chunked async task extraction using Celery.
"""
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from celery import current_app as celery_app
celery_app.conf.task_always_eager = True
celery_app.conf.task_eager_propagates = True

from celery.result import AsyncResult
from src.core.tasks.ai_tasks import extract_tasks_chunked_async
from src.core.ai.extractors import chunk_email_text, extract_tasks_from_update

# Example long email with multiple sections
email_text = """
Here are my tasks for today:
- Attornato:
     - Worked with Paula to continue building outreach emails and supporting documentation for nonprofits
     - Connect with Emiliana on the emails
- Task Manager AI Agent:
     - Ran a healthcheck that the end to end process worked. Found some bugs I needed to fix (embedding manager, coaching insights generator, PostgreSQL connection with gmail processor) and worked with cursor to fix them. All works as expected now
     - Started evolving the PostgreSQL database to connect with a cloudbased storage where the bodies of the emails will be stored. This will help with speed of processing and storage capabilities
     - Went through the conversations and notes we've taken and put together immediate next steps for the tool to do on the short term
     - Follow up with Daniel on who will be taking over and start setting up time with them
- BCG:
     - Ran through two cases with Ana and gathered a lot of feedback. Printed more copies to be ready to do 2 - 3 a day with her and keep training
     - Read a chapter and a half of Hacking the Case Interview and a learning block from RocketBlock
Grad School Preparation
     - Received more information on the loan structure / amount that I will be able to apply for and am working to set up a call with student funding to answer some outstanding questions I have
     - Think about the position and start brainstorming / writing the application, discuss with daniel and review linkedin profiles of people that have gone through it
- Admin:
     - Went back to the T-Mobile store to get my new phone but they told me they couldn't because the phone was damaged so I submitted a new claim with the insurance and they said they'd fix it
"""

def main():
    print("🚀 Testing chunked extraction (synchronous, no Celery)...")
    chunks = chunk_email_text(email_text, 20)
    print(f"Total chunks: {len(chunks)}")
    all_tasks = []
    for idx, chunk in enumerate(chunks, 1):
        print(f"\n--- Chunk {idx} ---\n{chunk[:200]}{'...' if len(chunk) > 200 else ''}")
        tasks = extract_tasks_from_update(chunk)
        print(f"Extracted {len(tasks)} tasks from chunk {idx}")
        all_tasks.extend(tasks)
    print(f"\n✅ Extraction complete!")
    print(f"Total tasks extracted: {len(all_tasks)}")
    for i, task in enumerate(all_tasks, 1):
        print(f"  {i}. {task.get('task', '')} (Category: {task.get('category', '')})")

if __name__ == "__main__":
    main() 