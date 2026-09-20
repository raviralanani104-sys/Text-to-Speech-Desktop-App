import tkinter as tk
from tkinter import filedialog, messagebox
import pyttsx3

# --- Functions ---
def speak_text():
    """Convert entered text into speech"""
    text = text_entry.get("1.0", tk.END).strip()
    if text:
        # Re-initialize engine fresh each time
        engine = pyttsx3.init()
        engine.setProperty('rate', speed_slider.get())
        engine.setProperty('volume', volume_slider.get())

        voices = engine.getProperty('voices')
        if voice_var.get() == "Male":
            engine.setProperty('voice', voices[0].id)
        elif len(voices) > 1:
            engine.setProperty('voice', voices[1].id)

        engine.say(text)
        engine.runAndWait()
        engine.stop()  # clear engine after speaking
    else:
        messagebox.showwarning("Warning", "Please enter some text!")

def stop_speech():
    """Stop ongoing speech immediately"""
    # Create a fresh engine and stop it to clear any queue
    engine = pyttsx3.init()
    engine.stop()

def save_audio():
    """Save entered text as audio file"""
    text = text_entry.get("1.0", tk.END).strip()
    if text:
        file_path = filedialog.asksaveasfilename(defaultextension=".mp3",
                                                 filetypes=[("Audio Files", "*.mp3")])
        if file_path:
            engine = pyttsx3.init()
            engine.setProperty('rate', speed_slider.get())
            engine.setProperty('volume', volume_slider.get())

            voices = engine.getProperty('voices')
            if voice_var.get() == "Male":
                engine.setProperty('voice', voices[0].id)
            elif len(voices) > 1:
                engine.setProperty('voice', voices[1].id)

            engine.save_to_file(text, file_path)
            engine.runAndWait()
            engine.stop()
            messagebox.showinfo("Saved", f"Audio saved as {file_path}")
    else:
        messagebox.showwarning("Warning", "Please enter some text!")

# --- GUI Setup ---
root = tk.Tk()
root.title("Text-to-Speech App")
root.geometry("500x400")

# Text input
tk.Label(root, text="Enter Text:").pack()
text_entry = tk.Text(root, height=8, width=50)
text_entry.pack()

# Buttons
tk.Button(root, text="Speak", command=speak_text).pack(pady=5)
tk.Button(root, text="Stop", command=stop_speech).pack(pady=5)
tk.Button(root, text="Save Audio", command=save_audio).pack(pady=5)

# Voice selection
voice_var = tk.StringVar(value="Male")
tk.Label(root, text="Select Voice:").pack()
tk.OptionMenu(root, voice_var, "Male", "Female").pack()

# Speed control
tk.Label(root, text="Speed:").pack()
speed_slider = tk.Scale(root, from_=100, to=200, orient="horizontal")
speed_slider.set(150)
speed_slider.pack()

# Volume control
tk.Label(root, text="Volume:").pack()
volume_slider = tk.Scale(root, from_=0, to=1, resolution=0.1, orient="horizontal")
volume_slider.set(0.9)
volume_slider.pack()

root.mainloop()




