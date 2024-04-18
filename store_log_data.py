import csv

def count_word_occurrences(file_paths, search_words):
    # This dictionary will hold the counts of each word in each file.
    # The format will be {file_path: {search_word: count}}
    counts = {file_path: {search_word: 0 for search_word in search_words} for file_path in file_paths}
    
    # Loop through each file and each word to search and count occurrences.
    for file_path in file_paths:
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                file_content = file.read().lower()
                for search_word in search_words:
                    counts[file_path][search_word] = file_content.count(search_word.lower())
        except FileNotFoundError:
            print(f"File {file_path} not found. Skipping...")
    
    return counts

def write_counts_to_csv(counts, output_csv_path):
    # Write the counts to a CSV file.
    with open(output_csv_path, 'w', newline='', encoding='utf-8') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(['File Path', 'Search Word', 'Count'])
        
        for file_path, words_counts in counts.items():
            for word, count in words_counts.items():
                writer.writerow([file_path, word, count])

file_paths = ['/home/uom/howe0427/SeQUeNCe/multi_node_framework_log 0.log', '/home/uom/howe0427/SeQUeNCe/multi_node_framework_log 1.log']  # file paths here
search_words = ['successful entanglement', 'failed entanglement']
output_csv_path = 'word_counts.csv'

counts = count_word_occurrences(file_paths, search_words)
write_counts_to_csv(counts, output_csv_path)
