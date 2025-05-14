import json
import os
from datetime import datetime

def consolidate_results():
    results_dir = "tests/results"
    consolidated = {
        "consolidated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "results": []
    }
    
    # Get all JSON files except the summary
    json_files = [f for f in os.listdir(results_dir) if f.endswith('.json') and f != 'test_summary.json']
    
    # Sort files by timestamp in filename
    json_files.sort()
    
    for filename in json_files:
        file_path = os.path.join(results_dir, filename)
        try:
            with open(file_path, 'r') as f:
                result = json.load(f)
                # Add filename as a comment in the result
                result["source_file"] = filename
                consolidated["results"].append(result)
        except Exception as e:
            print(f"Error reading {filename}: {e}")
    
    # Save consolidated results
    output_file = os.path.join(results_dir, "consolidated_results.json")
    with open(output_file, 'w') as f:
        json.dump(consolidated, f, indent=2)
    
    print(f"\nConsolidated {len(json_files)} result files into: {output_file}")
    print("Summary file (test_summary.json) was left unchanged.")

if __name__ == "__main__":
    consolidate_results() 