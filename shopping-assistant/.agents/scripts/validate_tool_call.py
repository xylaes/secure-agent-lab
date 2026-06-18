import sys
import json

def main():
    try:
        # Read the JSON input from stdin
        input_data = sys.stdin.read()
        if not input_data:
            print("No input data received", file=sys.stderr)
            sys.exit(0)

        data = json.loads(input_data)

        # Extract command (check both CommandLine used in Antigravity and fallback command)
        args = data.get("arguments", {})
        command = args.get("CommandLine", "") or args.get("command", "")

        # Validation logic: Block destructive commands
        blocked_patterns = ["rm -rf", "rm -f", "rm  -rf", "rm  -f"]
        for pattern in blocked_patterns:
            if pattern in command:
                print(f"Blocked dangerous command: {command}", file=sys.stderr)
                sys.exit(1) # Non-zero exit code blocks the tool execution

        sys.exit(0) # Success, allow execution
    except Exception as e:
        print(f"Validation error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
