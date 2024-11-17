
import steps

import sys

# if __name__ == "__main__":
if len(sys.argv) < 3:
    print("Usage: script.py <output_directory> <input_pdf_1> [input_pdf_2] ...", file=sys.stderr)
    sys.exit(1)

output_dir = sys.argv[1]
input_paths = list(sys.argv[2:])

print('input:',input_paths)
steps.pdf_prep(input_paths)
print('pdf prep complete. 0 ')
exts, ext_tables = steps.step_1(input_paths)
print('step 1 complete ',exts,ext_tables)

success = steps.step_2(exts, ext_tables, output_dir)
print('step 2 complete ')

sys.exit(0 if success else 1)
