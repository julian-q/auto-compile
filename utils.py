import os
import re
import requests
import subprocess

s = requests.Session()
api_base = os.getenv("OPENAI_API_BASE")
token = os.getenv("OPENAI_API_KEY")
url = f"{api_base}/chat/completions"

def query(prompt, system="You are a helpful assistant.", delimiter=None):
    body = {
        "model": "codellama/CodeLlama-34b-Instruct-hf",
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt}
        ],
        "temperature": 1,
    }

    while True:
        with s.post(url, headers={"Authorization": f"Bearer {token}"}, json=body) as resp:
            if not resp.ok:
                print("Query response not OK, retrying.")
                continue
            response = resp.json()["choices"][0]["message"]["content"]
            if delimiter is None:
                return response
            pattern = r"\n?" + delimiter + r".*\n"
            if len(re.findall(pattern, response)) < 2:
                print("Retrying query due to missing delimiters.")
                continue
            response = re.split(pattern, response)[1]
            return response

def get_program():
    program_message = """Hello!
Could you please write a C program that reads from standard input, performs a fun numerical calculation, and writes the results to standard output?"""
    program = query(program_message, delimiter="```")
    gcc_asm = get_gcc_asm(program)
    while gcc_asm is None:
        program = query(program_message, delimiter="```")
        gcc_asm = get_gcc_asm(program)
    return program, gcc_asm

def get_test_cases(program):
    test_message = f"""Hello!
Below is a C program that reads from standard input, performs a fun numerical calculation, and writes the results to standard output. Could you please give me examples of good test inputs for this program, one on each line?

C program:
```c
{program}
```

Please format your answer as follows:
'''
# Explanation
...
# Standard input examples
```
...
```
'''"""
    test_cases = query(test_message, delimiter="```")
    while not test_cases[0].isdigit():
        test_cases = query(test_message, delimiter="```")
    return test_cases.split("\n")

def get_llm_asm(program, examples=[], max_retries=3):
    if len(examples) > 0:
        examples_list = "\n".join([f"""
# Example Input:
```c
{c}
```

# Example Output:
```assembly
{asm}
```""" for c, asm in examples])
        examples_string = f"""{examples_list}

# Your turn:"""
    else:
        examples_string = ""
    compile_message_few_shot = f"""Hello!
Could you please compile the following C code to an x86-64 assembly program for the GAS assembler (using AT&T syntax)?
{examples_string}
```c
{program}
```"""
    print(compile_message_few_shot)
    asm = query(compile_message_few_shot, delimiter="```")
    valid_asm = get_binary(asm, "./llm_code")
    retries = 0
    while not valid_asm and retries < max_retries:
        print(f"LLM assembly generation failed. Retrying... ({retries + 1}/{max_retries})")
        asm = query(compile_message_few_shot, delimiter="```")
        valid_asm = get_binary(asm, "./llm_code")
        retries += 1
    return asm, valid_asm

def get_gcc_asm(program):
    with open("code.c", "w") as file:
        file.write(program)
    result = subprocess.run("gcc -S code.c -o gcc_code.s", stderr=subprocess.PIPE, shell=True, text=True)
    if result.returncode != 0:
        print(f"Compile error: {result.stderr}")
        asm = None
    else:
        print("Compilation successful")
        with open("gcc_code.s", "r") as file:
            asm = file.read()
    return asm
    
def get_binary(asm, out_path="code"):
    with open(f"{out_path}.s", "w") as file:
        file.write(asm)
    result = subprocess.run(f"as {out_path}.s -o {out_path}.o", stderr=subprocess.PIPE, shell=True, text=True)
    if result.returncode != 0:
        print(f'Assembler error: {result.stderr}')
        return False
    else:
        print('Assembly successful')
    result = subprocess.run(f"gcc {out_path}.o -o {out_path}", stderr=subprocess.PIPE, shell=True, text=True)
    if result.returncode != 0:
        print(f'Linker error: {result.stderr}')
        return False
    else:
        print('Linking successful')
        return True

def test_binary(binary_path, stdin):
    result = subprocess.run(f"echo '{stdin}' | {binary_path}", stdout=subprocess.PIPE, shell=True, text=True)
    return result.stdout

