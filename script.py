import zipfile, os, random
from collections import defaultdict, Counter

# -------- SETTINGS --------
times = int(input("How many sequences do you want to generate?: "))
difficulty_choice = input("Enter difficulty (easy / medium / hard): ").strip().lower()

data_folder = "/Users/Coop/Dropbox/oldseq3/c4a/ai"
sequence = ""
content = ""

SEQUENCE_LENGTH = (12, 15)

BANNED_CALLS = [
    "right and left grand",
    "dixie grand",
    "left allemande",
    "promenade",
    "you're home"
]

# -------- STEP 1: READ DATA --------
def extract_calls_from_zip(zip_path):
    calls = []
    sequences = []

    with zipfile.ZipFile(zip_path, 'r') as z:
        for file_name in z.namelist():
            current_sequence = []
            skip_count = 0

            with z.open(file_name) as f:
                for line in f:
                    line = line.decode('utf-8').strip()

                    if not line:
                        continue

                    if skip_count > 0:
                        skip_count -= 1
                        continue

                    if "Sd" in line:
                        skip_count = 1
                        continue

                    if "Warning:" in line:
                        continue

                    if any(bad in line.lower() for bad in BANNED_CALLS):
                        if len(current_sequence) >= 3:
                            sequences.append(current_sequence)

                        current_sequence = []  # start fresh
                        continue

                    current_sequence.append(line)

            if len(current_sequence) >= 3:
                sequences.append(current_sequence)
                calls.extend(current_sequence)

    return calls, sequences

# -------- STEP 2: BUILD WEIGHTED 2-STEP MARKOV --------
def build_markov_chain(sequences):
    chain = defaultdict(Counter)
    starters = []

    for seq in sequences:
        starters.append(seq[0])

        for j in range(len(seq) - 2):
            key = (seq[j], seq[j + 1])
            next_call = seq[j + 2]
            chain[key][next_call] += 1 # weighting happens here

    return chain, starters

# -------- STEP 3: WEIGHTED RANDOM CHOICE --------
def weighted_choice(counter_dict):
    total = sum(counter_dict.values())
    r = random.uniform(0, total)
    upto = 0

    for item, weight in counter_dict.items():
        upto += weight
        if upto >= r:
            return item

# -------- STEP 4: GENERATE SEQUENCE --------
def generate_sequence(chain, starters):
    global sequence
    length = random.randint(*SEQUENCE_LENGTH)

    # Pick a valid starting call
    first_call = random.choice(starters)

    # Find a valid second call that exists with it
    possible_keys = [k for k in chain.keys() if k[0] == first_call]

    if not possible_keys:
        start_key = random.choice(list(chain.keys()))
    else:
        start_key = random.choice(possible_keys)

    sequence = [start_key[0], start_key[1]]

    while len(sequence) < length:
        key = (sequence[-2], sequence[-1])

        if key not in chain:
            # restart safely (APPEND, don't reset)
            new_first = random.choice(starters)
            new_keys = [k for k in chain.keys() if k[0] == new_first]

            if not new_keys:
                continue

            new_key = random.choice(new_keys)

            sequence.append(new_key[0])
            sequence.append(new_key[1])
            continue

        next_call = weighted_choice(chain[key])

        # Avoid immediate repeats
        if next_call == sequence[-1]:
            continue

        sequence.append(next_call)

    return sequence[:length]

# -------- MAIN --------
def main():
    global sequence
    global difficulty_choice
    global content

    matching_files = [
        f for f in os.listdir(data_folder)
        if f.endswith(".zip") and difficulty_choice in f.lower()
    ]

    if not matching_files:
        print("No matching ZIP files found for that difficulty.")
        return

    print(f"\nUsing files:")
    for f in matching_files:
        print("-", f)

    all_sequences = []

    # Load only matching files
    for file in matching_files:
        print(f"\nProcessing {file}...")
        full_path = os.path.join(data_folder, file)
        _, sequences = extract_calls_from_zip(full_path)
        all_sequences.extend(sequences)

    if not all_sequences:
        print("No valid sequences found.")
        return

    # Build model from filtered data
    chain, starters = build_markov_chain(all_sequences)

    sequence = generate_sequence(chain, starters)

    print("\nGenerated Sequence:\n")
    for i, call in enumerate(sequence, 1):
        print(f"{i}. {call}")
        content += f"\n{call}"




if __name__ == "__main__":
    for x in range(times):
        main()
        content += "\n"

    while True:
        new_file_name = input("\nEnter name for new sequence file: ")
        path = os.path.join(data_folder, new_file_name)

        try:
            with open(path, "x") as f:
                f.write(content)
            break
        except FileExistsError:
            print("File already exists! please choose another name.")