import pandas as pd
import os
import tkinter as tk
from tkinter import filedialog, messagebox
import uuid

selected_folder = None
unblind_new_files_var = None  # Tkinter IntVar for checkbox


def blind_folders(base_folder):
    if not os.path.exists(base_folder):
        messagebox.showerror("Error", f"The folder '{base_folder}' does not exist.")
        return

    for root, dirs, files in os.walk(base_folder):
        for name in dirs + files:
            if 'New_File' in name or 'New_Folder' in name:
                messagebox.showerror("Warning", "These files appear to have already been randomized")
                return

    entries = os.listdir(base_folder)
    sub_folders = [entry for entry in entries if os.path.isdir(os.path.join(base_folder, entry))]
    files = [entry for entry in entries if os.path.isfile(os.path.join(base_folder, entry)) and entry != '.DS_Store']

    blinding_key = []

    if sub_folders:
        for folder_name in sub_folders:
            folder_path = os.path.join(base_folder, folder_name)
            new_folder_name = f'New_Folder_{uuid.uuid4()}'
            new_folder_path = os.path.join(base_folder, new_folder_name)
            os.rename(folder_path, new_folder_path)
            blinding_key.append({'Original': folder_name, 'Blinded': new_folder_name})

            for file_name in os.listdir(new_folder_path):
                if file_name != '.DS_Store':
                    old_file_path = os.path.join(new_folder_path, file_name)
                    new_file_name = f'New_File_{uuid.uuid4()}{os.path.splitext(file_name)[1]}'
                    new_file_path = os.path.join(new_folder_path, new_file_name)
                    os.rename(old_file_path, new_file_path)
                    blinding_key.append({'Original': file_name, 'Blinded': new_file_name})

    if files:
        for file_name in files:
            old_file_path = os.path.join(base_folder, file_name)
            new_file_name = f'New_File_{uuid.uuid4()}{os.path.splitext(file_name)[1]}'
            new_file_path = os.path.join(base_folder, new_file_name)
            os.rename(old_file_path, new_file_path)
            blinding_key.append({'Original': file_name, 'Blinded': new_file_name})

    blinding_key_df = pd.DataFrame(blinding_key)
    blinding_key_df.to_csv(os.path.join(base_folder, 'blinding_key.csv'), index=False)
    messagebox.showinfo("Success", "Blinding complete. Blinding key saved.")


def unblind_folders(base_folder, unblind_new=False):
    csv_path = os.path.join(base_folder, 'blinding_key.csv')
    if not os.path.exists(csv_path):
        messagebox.showerror("Error", "blinding_key.csv not found in the selected folder.")
        return

    try:
        blinding_key_df = pd.read_csv(csv_path)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to read blinding_key.csv:\n{e}")
        return

    blinding_key_df['is_folder'] = blinding_key_df['Blinded'].str.startswith('New_Folder_')
    blinding_key_df_sorted = blinding_key_df.sort_values(by='is_folder')

    errors = []

    # Unblind renamed files/folders
    for _, row in blinding_key_df_sorted.iterrows():
        blinded_name = row['Blinded']
        original_name = row['Original']

        blinded_path = os.path.join(base_folder, blinded_name)
        original_path = os.path.join(base_folder, original_name)

        if os.path.exists(blinded_path):
            try:
                os.rename(blinded_path, original_path)
            except Exception as e:
                errors.append(f"Failed to rename '{blinded_name}' to '{original_name}': {e}")
        else:
            found = False
            for root, dirs, files in os.walk(base_folder):
                if blinded_name in files:
                    full_blinded_path = os.path.join(root, blinded_name)
                    full_original_path = os.path.join(root, original_name)
                    try:
                        os.rename(full_blinded_path, full_original_path)
                        found = True
                        break
                    except Exception as e:
                        errors.append(f"Failed to rename '{blinded_name}' to '{original_name}': {e}")
                        found = True
                        break
                elif blinded_name in dirs:
                    full_blinded_path = os.path.join(root, blinded_name)
                    full_original_path = os.path.join(root, original_name)
                    try:
                        os.rename(full_blinded_path, full_original_path)
                        found = True
                        break
                    except Exception as e:
                        errors.append(f"Failed to rename folder '{blinded_name}' to '{original_name}': {e}")
                        found = True
                        break
            if not found:
                errors.append(f"Could not find '{blinded_name}' to rename.")

    # 🔁 Handle newly generated files that include blinded names
    if unblind_new:
        name_map = dict(zip(blinding_key_df['Blinded'], blinding_key_df['Original']))
        for root, dirs, files in os.walk(base_folder):
            for file in files:
                file_path = os.path.join(root, file)
                for blinded_name, original_name in name_map.items():
                    # Only replace if the base name matches (without extension)
                    blinded_stem, _ = os.path.splitext(blinded_name)
                    original_stem, _ = os.path.splitext(original_name)
                    if blinded_stem in file:
                        new_file = file.replace(blinded_stem, original_stem)
                        new_path = os.path.join(root, new_file)
                        try:
                            os.rename(file_path, new_path)
                            break  # Done processing this file
                        except Exception as e:
                            errors.append(f"Failed to rename '{file}' to '{new_file}': {e}")


    if errors:
        messagebox.showerror("Errors occurred during unblinding", "\n".join(errors))
    else:
        messagebox.showinfo("Success", "Unblinding complete.")
        
        
def reblind_folders(base_folder):
    csv_path = os.path.join(base_folder, 'blinding_key.csv')
    if not os.path.exists(csv_path):
        messagebox.showerror("Error", "blinding_key.csv not found in the selected folder.")
        return

    try:
        blinding_key_df = pd.read_csv(csv_path)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to read blinding_key.csv:\n{e}")
        return

    # Sort to rename files before folders (avoid path collisions)
    blinding_key_df['is_folder'] = blinding_key_df['Original'].str.startswith('New_Folder_')
    blinding_key_df_sorted = blinding_key_df.sort_values(by='is_folder')

    errors = []

    for _, row in blinding_key_df_sorted.iterrows():
        original_name = row['Original']
        blinded_name = row['Blinded']

        original_path = os.path.join(base_folder, original_name)
        blinded_path = os.path.join(base_folder, blinded_name)

        if os.path.exists(original_path):
            try:
                os.rename(original_path, blinded_path)
            except Exception as e:
                errors.append(f"Failed to rename '{original_name}' to '{blinded_name}': {e}")
        else:
            # Try to find file/folder inside subfolders
            found = False
            for root, dirs, files in os.walk(base_folder):
                if original_name in files:
                    full_original_path = os.path.join(root, original_name)
                    full_blinded_path = os.path.join(root, blinded_name)
                    try:
                        os.rename(full_original_path, full_blinded_path)
                        found = True
                        break
                    except Exception as e:
                        errors.append(f"Failed to rename '{original_name}' to '{blinded_name}': {e}")
                        found = True
                        break
                elif original_name in dirs:
                    full_original_path = os.path.join(root, original_name)
                    full_blinded_path = os.path.join(root, blinded_name)
                    try:
                        os.rename(full_original_path, full_blinded_path)
                        found = True
                        break
                    except Exception as e:
                        errors.append(f"Failed to rename folder '{original_name}' to '{blinded_name}': {e}")
                        found = True
                        break
            if not found:
                errors.append(f"Could not find '{original_name}' to rename.")

    if errors:
        messagebox.showerror("Errors occurred during reblinding", "\n".join(errors))
    else:
        messagebox.showinfo("Success", "Reblinding complete.")


def select_folder():
    global selected_folder
    folder_path = filedialog.askdirectory()
    if folder_path:
        selected_folder = folder_path
        folder_label.config(text=f"Selected:\n{folder_path}")


def run_blinding():
    if selected_folder:
        blind_folders(selected_folder)
    else:
        messagebox.showerror("Error", "Please select a folder first.")


def run_unblinding():
    if selected_folder:
        unblind_folders(selected_folder, unblind_new=bool(unblind_new_files_var.get()))
    else:
        messagebox.showerror("Error", "Please select a folder first.")

def run_reblinding():
    if selected_folder:
        reblind_folders(selected_folder)
    else:
        messagebox.showerror("Error", "Please select a folder first.")


# Create the GUI
root = tk.Tk()
root.title("Blinding Application")
root.geometry("450x280")

label = tk.Label(root, text="Select a folder to blind or unblind:")
label.pack(pady=10)

button_browse = tk.Button(root, text="Browse", command=select_folder)
button_browse.pack()

folder_label = tk.Label(root, text="No folder selected", wraplength=400, fg="gray")
folder_label.pack(pady=5)

button_blind = tk.Button(root, text="Blind", command=run_blinding)
button_blind.pack(pady=10)

button_reblind = tk.Button(root, text="Reblind", command=run_reblinding)
button_reblind.pack(pady=5)

button_unblind = tk.Button(root, text="Unblind", command=run_unblinding)
button_unblind.pack(pady=5)

# Add checkbox for "Unblind new files"
unblind_new_files_var = tk.IntVar()
checkbox = tk.Checkbutton(root, text="Unblind new files", variable=unblind_new_files_var)
checkbox.pack()

root.mainloop()
