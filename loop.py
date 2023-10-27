import argparse
from utils import (
    get_program,
    get_test_cases,
    get_llm_asm,
    get_gcc_asm,
    get_binary,
    test_binary,
)

def main(args):
    n_pass = 0
    n_fail = 0
    n_invalid = 0
    n_total = 0
    while True:
        examples = []
        for i in range(args.num_examples):
            example_program, example_gcc_asm, _ = get_program()
            examples.append((example_program, example_gcc_asm))
            print(f"=== Few shot example {i}:")
            print("Generated C code:")
            print(example_program)
            print("GCC x86:")
            print(example_gcc_asm)
        program, gcc_asm, num_c_retries = get_program()
        print(f"=== Query C program (took {num_c_retries} retries):")
        print("Generated C code:")
        print(program)
        llm_asm, valid = get_llm_asm(program, examples=examples, max_retries=args.max_retries)
        print("Generated x86:")
        print(llm_asm)
        if not valid:
            n_invalid += 1
            print("=== Verdict: Invalid x86.")
        else:
            get_binary(llm_asm, "./llm_code")
            get_binary(gcc_asm, "./gcc_code")
            tests = get_test_cases(program)
            tests_passed = 0
            print("Generated valid x86.")
            print("=== Running test cases:")
            print(tests)
            for test in tests:
                print("Input:", test)
                print("LLM stdout:")
                llm_stdout = test_binary('./llm_code', test)
                print(llm_stdout)
                print("GCC stdout:")
                gcc_stdout = test_binary('./gcc_code', test)
                print(gcc_stdout)
                if llm_stdout == gcc_stdout:
                    tests_passed += 1
            if tests_passed == len(tests):
                n_pass += 1
                print("=== Verdict: Correct x86!")
            else:
                n_fail += 1
                print("=== Verdict: Valid but incorrect x86.")
        n_total += 1
        print(f"[{args.num_examples}-shot][{args.max_retries} retries] Passed: {n_pass}/{n_total}. Valid+Failed: {n_fail}/{n_total}. Invalid: {n_invalid}/{n_total}.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--num_examples", type=int, default=1)
    parser.add_argument("--max_retries", type=int, default=3)
    args = parser.parse_args()
    main(args)
