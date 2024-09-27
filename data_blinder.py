import os
import random
import pandas as pd
import os
import shutil
import pandas as pd
import random
import os
import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox
import uuid



def blind_folders(base_folder):
    # Check if the base folder exists
    if not os.path.exists(base_folder):
        print(f"Error: The folder '{base_folder}' does not exist.")
        return
    # Check if the base folder contains sub-folders or files
    entries = os.listdir(base_folder)
    sub_folders = [entry for entry in entries if os.path.isdir(os.path.join(base_folder, entry))]
    files = [entry for entry in entries if os.path.isfile(os.path.join(base_folder, entry)) and entry != '.DS_Store']

    # Prepare a list to hold the original and new names
    blinding_key = []

    if sub_folders:
        # Process sub-folders
        for folder_name in sub_folders:
            folder_path = os.path.join(base_folder, folder_name)

            # Rename the folder
            new_folder_name = f'New_Folder_{uuid.uuid4()}'
            new_folder_path = os.path.join(base_folder, new_folder_name)
            os.rename(folder_path, new_folder_path)

            # Add to the blinding key for the folder
            blinding_key.append({'Original': folder_name, 'Blinded': new_folder_name})

            # Process files within the sub-folder
            for file_name in os.listdir(new_folder_path):
                if file_name != '.DS_Store':
                    old_file_path = os.path.join(new_folder_path, file_name)
                    new_file_name = f'New_File_{random.randint(1000, 9999)}{os.path.splitext(file_name)[1]}'
                    new_file_path = os.path.join(new_folder_path, new_file_name)
                    os.rename(old_file_path, new_file_path)

                    # Add to the blinding key
                    blinding_key.append({'Original': file_name, 'Blinded': new_file_name})

    if files:
        # Process files directly in the base folder
        for file_name in files:
            old_file_path = os.path.join(base_folder, file_name)
            new_file_name = f'New_File_{random.randint(1000, 9999)}{os.path.splitext(file_name)[1]}'
            new_file_path = os.path.join(base_folder, new_file_name)
            os.rename(old_file_path, new_file_path)

            # Add to the blinding key
            blinding_key.append({'Original': file_name, 'Blinded': new_file_name})

    # Convert the list of dicts to a DataFrame
    blinding_key_df = pd.DataFrame(blinding_key)

    # Save the results
    blinding_key_df.to_csv(os.path.join(base_folder, 'blinding_key.csv'), index=False)





def select_folder():
    folder_path = filedialog.askdirectory()
    if folder_path:
        blind_folders(folder_path)

# Create the GUI
root = tk.Tk()
root.title("Blinding Application")
root.geometry("300x150")

label = tk.Label(root, text="Select a folder to blind:")
label.pack(pady=10)

button = tk.Button(root, text="Browse", command=select_folder)
button.pack(pady=20)

root.mainloop()

