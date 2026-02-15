""" A script that looks into a folder,
     finds all .txt files, reads the text,
       and generates a summary report in a .csv file"""

import os
import csv
import glob


def summarize_text_files(folder_path, output_csv):
    # Get all .txt files in the specified folder
    txt_files = glob.glob(os.path.join(folder_path, '*.txt'))
    # Prepare a list to hold summary data
    summary_data = []
    for txt_file in txt_files:
        with open(txt_file, encoding='utf-8', mode='r',
                  errors='ignore') as file:
            text = file.read()
            word_count = len(text.split())
            char_count = len(text)
            summary_data.append({
                'filename': os.path.basename(txt_file),
                'word_count': word_count,
                'char_count': char_count
            })
    # Write the summary data to a CSV file
    with open(output_csv, 'w', newline='', encoding='utf-8',
              errors='ignore') as csvfile:
        fieldnames = ['filename', 'word_count', 'char_count']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for data in summary_data:
            writer.writerow(data)


if __name__ == "__main__":
    folder_path = (
        r"C:\Users\mrsat\Documents\Programming_Devloping"
        r"\python-engineering-lab\tests"
    )
    output_csv = 'summary_report.csv'
    summarize_text_files(folder_path, output_csv)
    print(f"Summary report generated: {output_csv}")
