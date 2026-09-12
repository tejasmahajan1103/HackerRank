"""
HackerRank entry point - main.py
"""
import sys
import os
from pathlib import Path

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent))

from core.engine import create_engine


def find_dataset_path() -> str:
    """Find the dataset directory robustly."""
    # Try current directory
    current = Path.cwd()
    dataset = current / "dataset"
    if dataset.exists():
        return str(dataset)
    
    # Try parent directory
    parent = current.parent
    dataset = parent / "dataset"
    if dataset.exists():
        return str(dataset)
    
    # Try relative to this file
    script_dir = Path(__file__).parent
    dataset = script_dir.parent / "dataset"
    if dataset.exists():
        return str(dataset)
    
    raise FileNotFoundError("Could not find dataset directory")


def main():
    print("Starting Buy or Wait financial analysis...")
    
    try:
        dataset_path = find_dataset_path()
        print(f"Using dataset: {dataset_path}")
        
        engine = create_engine(dataset_path)
        
        print("Analyzing all requests...")
        results = engine.analyze_all_requests()
        
        print(f"Processed {len(results)} requests")
        
        # Output to root-level output.csv
        output_path = Path.cwd() / "output.csv"
        engine.export_to_csv(results, str(output_path))
        print(f"Results written to {output_path}")
        
        # Print usage report
        usage = engine.get_usage_report()
        print("\nAI Usage Report:")
        print(f"  Provider: {usage['provider']}")
        print(f"  Model: {usage['model']}")
        print(f"  Total calls: {usage['total_calls']}")
        print(f"  Total tokens: {usage['total_tokens']}")
        print(f"  Estimated cost: ${usage['estimated_total_cost']:.6f}")
        
        # Validate output
        print("\nValidating output...")
        validate_output(results, engine.loader)
        
        print("Done!")
        return 0
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


def validate_output(results, loader):
    """Validate all output rows."""
    from core.validator import OutputValidator
    
    validator = OutputValidator(loader)
    all_valid = True
    
    for result in results:
        request = loader.get_request(result.request_id)
        if not request:
            print(f"  WARNING: Request {result.request_id} not found in loader")
            continue
        
        row = {
            "request_id": result.request_id,
            "amount_safe_to_pay": str(result.amount_safe_to_pay),
            "affordability_status": result.affordability_status,
            "recommended_payment_method": result.recommended_payment_method,
            "payment_plan": result.payment_plan,
            "earliest_date_for_full_payment": result.earliest_date_for_full_payment,
            "spending_changes_needed": result.spending_changes_needed,
            "decision_explanation": result.decision_explanation,
        }
        
        validation = validator.validate_output_row(row, request)
        if not validation.is_valid:
            print(f"  INVALID {result.request_id}: {validation.errors}")
            all_valid = False
    
    if all_valid:
        print("  All rows valid!")
    else:
        print("  Some rows have validation errors!")
        sys.exit(1)


if __name__ == "__main__":
    sys.exit(main())