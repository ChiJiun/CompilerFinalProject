import os
import subprocess
import sys

def run_tests():
    test_dir = "public_test_data"
    minilisp_path = "minilisp.py"

    print("Starting Mini-LISP Python Test Suite...\n")

    # 確保 minilisp.py 存在
    if not os.path.exists(minilisp_path):
        print(f"Error: {minilisp_path} not found in the current directory.")
        sys.exit(1)

    lsp_files = sorted([f for f in os.listdir(test_dir) if f.endswith(".lsp")])

    for lsp_file in lsp_files:
        full_path = os.path.join(test_dir, lsp_file)
        print(f"================================\nRunning {lsp_file}...")

        try:
            # 執行 python minilisp.py <test_file>
            result = subprocess.run(
                [sys.executable, minilisp_path, full_path],
                capture_output=True,
                text=True,
                check=False
            )

            # 顯示標準輸出
            if result.stdout:
                sys.stdout.write(result.stdout)
            
            # 顯示標準錯誤 (如果有)
            if result.stderr:
                sys.stderr.write(result.stderr)

        except Exception as e:
            print(f"An unexpected error occurred: {e}")
        
        print("--------------------------------")

    print("\nAll tests completed.")

if __name__ == "__main__":
    run_tests()
