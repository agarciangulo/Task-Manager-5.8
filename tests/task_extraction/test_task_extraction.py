import json
import sys
import argparse
import os
from datetime import datetime
from core.task_extractor import extract_tasks_from_update
from core.gemini_client import client
from config import CHAT_MODEL

def split_test_files(input_file, output_dir):
    """Split a master test file into individual test files."""
    print(f"\nSplitting master test file: {input_file}")
    print(f"Output directory: {output_dir}")
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    with open(input_file, 'r') as f:
        content = f.read()
    
    # Split by file markers
    files = content.split('## FILE: ')
    
    split_files = []
    for file_section in files[1:]:  # Skip the first empty section
        lines = file_section.strip().split('\n')
        filename = lines[0].strip()
        file_content = '\n'.join(lines[1:]).strip()
        
        # Create the output file
        output_path = os.path.join(output_dir, filename)
        with open(output_path, 'w') as f:
            f.write(file_content)
        
        split_files.append(filename)
        print(f"Created: {filename}")
    
    print(f"\nSplit {len(split_files)} files successfully!")
    return split_files

def save_results(input_text, prompt, raw_response, processed_tasks, output_dir):
    """Save test results to a file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    result = {
        "timestamp": timestamp,
        "input_text": input_text,
        "prompt": prompt,
        "raw_response": raw_response,
        "processed_tasks": processed_tasks
    }
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Save results
    output_file = os.path.join(output_dir, f"test_result_{timestamp}.json")
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"\nResults saved to: {output_file}")
    return output_file

def test_task_extraction(sample_text=None, save_output=True, results_dir="tests/task_extraction/results"):
    # If no sample text provided, use default
    if sample_text is None:
        sample_text = """
        From: John Doe
        Date: 2024-03-20
        
        Completed Activities:
        - Updated the resume with new skills and experience
        - Worked on VC University modules
        - Meeting with team about project timeline
        
        Planned Activities:
        - Start working on the new feature
        - Review pull requests
        """
    
    print("\n=== Input Text ===")
    print(sample_text)
    
    # Get the prompt that would be sent to ChatGPT
    from core.ai.prompt_builder import build_task_extraction_prompt
    prompt = build_task_extraction_prompt(sample_text)
    
    print("\n=== Prompt Sent to ChatGPT ===")
    print(prompt)
    
    # Get raw response from ChatGPT
    print("\n=== Raw ChatGPT Response ===")
    response_text = client.generate_content(
        prompt,
        temperature=0.3
    )
    print(response_text)
    
    # Get processed tasks
    print("\n=== Processed Tasks ===")
    tasks = extract_tasks_from_update(sample_text)
    print(json.dumps(tasks, indent=2))
    
    # Save results if requested
    if save_output:
        return save_results(sample_text, prompt, response_text, tasks, results_dir)
    return None

def process_sample_files(input_dir, output_dir):
    """Process all sample files in the input directory."""
    results = []
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Process each file in the input directory
    for filename in os.listdir(input_dir):
        if filename.endswith('.txt'):
            input_path = os.path.join(input_dir, filename)
            print(f"\nProcessing file: {filename}")
            
            with open(input_path, 'r') as f:
                sample_text = f.read()
            
            # Run test and save results
            output_file = test_task_extraction(sample_text, save_output=True, results_dir=output_dir)
            if output_file:
                results.append({
                    "input_file": filename,
                    "output_file": os.path.basename(output_file)
                })
    
    # Save summary of all tests
    summary = {
        "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "tests_run": results
    }
    
    summary_file = os.path.join(output_dir, "test_summary.json")
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\nTest summary saved to: {summary_file}")

def main():
    parser = argparse.ArgumentParser(description='Test task extraction with custom input text')
    parser.add_argument('--text', '-t', type=str, help='Input text to test task extraction')
    parser.add_argument('--file', '-f', type=str, help='Path to file containing input text')
    parser.add_argument('--dir', '-d', type=str, help='Directory containing sample input files')
    parser.add_argument('--split', '-s', type=str, help='Path to master test file to split and process')
    parser.add_argument('--no-save', action='store_true', help='Do not save results to file')
    
    args = parser.parse_args()
    
    if args.split:
        # Infer test_case from master file name
        test_case = os.path.splitext(os.path.basename(args.split))[0]
        # Set up organized output directories
        split_dir = f"tests/task_extraction/sample_inputs_archive/{test_case}"
        results_dir = f"tests/task_extraction/results_archive/{test_case}"
        consolidated_dir = f"tests/task_extraction/consolidated_results/{test_case}"
        os.makedirs(split_dir, exist_ok=True)
        os.makedirs(results_dir, exist_ok=True)
        os.makedirs(consolidated_dir, exist_ok=True)
        # Split the master file and then process the split files
        split_files = split_test_files(args.split, split_dir)
        if split_files:
            print("\nRunning tests on split files...")
            process_sample_files(split_dir, results_dir)
            # Move summary to consolidated dir
            summary_file = os.path.join(results_dir, "test_summary.json")
            if os.path.exists(summary_file):
                os.rename(summary_file, os.path.join(consolidated_dir, "test_summary.json"))
    elif args.dir:
        process_sample_files(args.dir, "tests/task_extraction/results")
    elif args.file:
        try:
            with open(args.file, 'r') as f:
                sample_text = f.read()
            test_task_extraction(sample_text, not args.no_save)
        except Exception as e:
            print(f"Error reading file: {e}")
            sys.exit(1)
    elif args.text:
        test_task_extraction(args.text, not args.no_save)
    else:
        test_task_extraction(None, not args.no_save)

if __name__ == "__main__":
    main() 