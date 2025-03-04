import sqlite3
from datetime import datetime

def print_analytics():
    """Print all analytics entries in a formatted way."""
    with sqlite3.connect("analytics.db") as conn:
        cursor = conn.cursor()
        
        # Get all entries
        cursor.execute("""
            SELECT source_file, timestamp, file_size, token_count, 
                   estimated_cost, user_feedback, was_edited 
            FROM file_operations 
            ORDER BY timestamp DESC
        """)
        
        rows = cursor.fetchall()
        
        if not rows:
            print("No analytics data found")
            return
            
        print("\n=== Analytics Report ===")
        for row in rows:
            source_file, timestamp, file_size, tokens, cost, feedback, edited = row
            print(f"\nFile: {source_file}")
            print(f"Time: {timestamp}")
            print(f"Size: {file_size} bytes")
            print(f"Tokens: {tokens}")
            print(f"Cost: ${cost:.4f}")
            if edited:
                print(f"Feedback: {feedback}")
            print("-" * 40)
        
        # Print summary
        print("\n=== Summary ===")
        cursor.execute("""
            SELECT COUNT(*) as total,
                   SUM(token_count) as total_tokens,
                   SUM(estimated_cost) as total_cost,
                   SUM(CASE WHEN was_edited THEN 1 ELSE 0 END) as edited_count
            FROM file_operations
        """)
        total, total_tokens, total_cost, edited_count = cursor.fetchone()
        print(f"Total operations: {total}")
        print(f"Total tokens used: {total_tokens}")
        print(f"Total cost: ${total_cost:.4f}")
        print(f"Files edited: {edited_count}")

if __name__ == "__main__":
    print_analytics() 