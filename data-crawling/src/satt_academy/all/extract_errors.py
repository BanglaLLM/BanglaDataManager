import os
import re
import pickle

errors = {}
if os.path.exists('errors.pkl'):
    with open('errors.pkl', 'rb') as f:
        errors = pickle.load(f)

def find_error_set(filepath):
    errors = set()
    with open(filepath) as f:
        for line in f:
            # replace id with \d+ to match any number of digits
            # print(line)
            line = re.sub(r"Error at ID: \d+", "Error at ID: {ID}", line)
            line = re.sub(r"ques_id=\d+", "ques_id={ID}", line)
            errors.add(line)

    for e in list(errors):
        print(e)
    print(f"Total errors: {len(errors)}")

def extract_404(filepath):
    cnt = 0
    pattern = "Error at ID: (\d+) - 404 Not Found"
    errors["404"] = []
    with open(filepath) as f:
        for line in f:
            match = re.search(pattern, line)
            if match:
                cnt += 1
                id_number = match.group(1)
                errors["404"].append(id_number)
    print(f"Total 404 errors: {cnt}")


def extract_qna_not_found(filepath):
    cnt = 0
    pattern = "Error at ID: (\d+) - Question or answer not found"
    errors["qna_not_found"] = []
    with open(filepath) as f:
        for line in f:
            match = re.search(pattern, line)
            if match:
                cnt += 1
                id_number = match.group(1)
                errors["qna_not_found"].append(id_number)
    print(f"Total QNA not found errors: {cnt}")

files = os.listdir('.')
for file in files:
    if file.endswith('.log') and file.startswith('error_'):
        print(file)
        find_error_set(file)
        extract_404(file)
        extract_qna_not_found(file)

for k, v in errors.items():
    errors[k] = list(set(v))

for k, v in errors.items():
    print(f"{k}: {len(v)}")

with open('errors.pkl', 'wb') as f:
    pickle.dump(errors, f)