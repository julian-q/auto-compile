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
    n_total = 0
    while True:
        examples = []
        for i in range(args.num_examples):
            example_program, example_gcc_asm = get_program()
            examples.append((example_program, example_gcc_asm))
        program, gcc_asm = get_program()
        llm_asm, valid = get_llm_asm(program, examples=examples, max_retries=args.max_retries)
        print(llm_asm)
        if not valid:
            print("LLM assembly is invalid.")
        else:
            get_binary(llm_asm, "./llm_code")
            get_binary(gcc_asm, "./gcc_code")
            tests = get_test_cases(program)
            tests_passed = 0
            for test in tests:
                print("Trying input:", test)
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
                print("Pass!")
        n_total += 1
        print(f"[{args.num_examples}-shot][{args.max_retries} retries] Passed {n_pass}/{n_total}.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--num_examples", type=int, default=1)
    parser.add_argument("--max_retries", type=int, default=3)
    args = parser.parse_args()
    main(args)
