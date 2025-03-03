import os
import time
import base64
import threading
import tempfile
import queue
import numpy as np
import sounddevice as sd
import scipy.io.wavfile as wavfile
from datetime import datetime
from PIL import Image, ImageDraw
from dotenv import load_dotenv
import pystray
from pystray import MenuItem as item
import tkinter as tk
from tkinter import messagebox

# Load environment variables
load_dotenv()

# Get API key from environment
API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    tk.Tk().withdraw()
    messagebox.showerror("Error", "GEMINI_API_KEY not found in environment variables or .env file")
    exit(1)

# Get configuration from environment variables (with defaults)
SAMPLE_RATE = int(os.environ.get("SAMPLE_RATE", "16000"))
PROCESSING_INTERVAL = int(os.environ.get("PROCESSING_INTERVAL", "5"))
TRANSCRIPT_FILE = os.environ.get("TRANSCRIPT_FILE", "live_transcript.md")

try:
    from google import generativeai as genai
    genai.configure(api_key=API_KEY)
    print("Gemini API configured successfully")
except ImportError:
    tk.Tk().withdraw()
    messagebox.showerror("Error", "Failed to import Google Generative AI library. Install with: pip install google-generativeai")
    exit(1)

# Global variables
recording = False
audio_queue = queue.Queue()
transcription_thread = None
processing_thread = None
icon = None
accumulated_audio = []
full_transcript = ""
last_processed_time = 0

# Initialize transcript file
def initialize_transcript_file():
    """Initialize or reset the transcript file."""
    with open(TRANSCRIPT_FILE, 'w') as f:
        f.write(f"# Live Audio Transcript\n\n")
        f.write(f"*Started on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
        f.write(f"## Content\n\n")
    print(f"Initialized transcript file: {TRANSCRIPT_FILE}")

def create_icon():
    """Create a simple microphone icon for the taskbar."""
    width = 64
    height = 64
    color = (0, 0, 255)  # Blue
    
    image = Image.new('RGB', (width, height), color=(255, 255, 255))
    dc = ImageDraw.Draw(image)
    
    # Draw microphone shape
    dc.rectangle((24, 16, 40, 40), fill=color)
    dc.rectangle((20, 40, 44, 44), fill=color)
    dc.rectangle((28, 44, 36, 52), fill=color)
    dc.rectangle((20, 52, 44, 56), fill=color)
    
    # When recording, use a red icon instead
    if recording:
        color = (255, 0, 0)  # Red
        dc.rectangle((24, 16, 40, 40), fill=color)
        dc.rectangle((20, 40, 44, 44), fill=color)
        dc.rectangle((28, 44, 36, 52), fill=color)
        dc.rectangle((20, 52, 44, 56), fill=color)
    
    return image

def audio_callback(indata, frames, time, status):
    """Callback function for the audio stream."""
    if status:
        print(f"Audio callback status: {status}")
    
    # Add audio to the queue and accumulated buffer
    audio_queue.put(indata.copy())
    accumulated_audio.append(indata.copy())

def start_transcription():
    """Start recording and transcribing audio."""
    global recording, transcription_thread, processing_thread, accumulated_audio, full_transcript, last_processed_time
    
    if recording:
        return
    
    # Clear any previous accumulated audio and transcript
    accumulated_audio = []
    full_transcript = ""
    
    # Initialize the transcript file
    initialize_transcript_file()
    
    # Set recording flag to True
    recording = True
    last_processed_time = time.time()
    
    # Update the icon to show recording state
    icon.icon = create_icon()
    
    # Start the transcription thread
    transcription_thread = threading.Thread(target=transcription_worker)
    transcription_thread.daemon = True
    transcription_thread.start()
    
    # Start the processing thread
    processing_thread = threading.Thread(target=processing_worker)
    processing_thread.daemon = True
    processing_thread.start()
    
    print("Transcription started - recording from microphone...")
    print(f"Processing audio every {PROCESSING_INTERVAL} seconds")
    print(f"Live transcript is being saved to {TRANSCRIPT_FILE}")
    print("Speak clearly into your microphone...")

def stop_transcription():
    """Stop recording and save the transcription."""
    global recording, accumulated_audio, full_transcript
    
    if not recording:
        return
    
    # Set recording flag to False to stop the worker threads
    recording = False
    
    # Update the icon to show non-recording state
    icon.icon = create_icon()
    
    print("Transcription stopped")
    
    # Wait for the threads to finish
    if transcription_thread and transcription_thread.is_alive():
        transcription_thread.join(timeout=1.0)
    
    if processing_thread and processing_thread.is_alive():
        processing_thread.join(timeout=1.0)
    
    # Process any remaining audio
    process_audio_segment()
    
    # Save the final transcript
    if full_transcript:
        # Append a final marker to the transcript file
        with open(TRANSCRIPT_FILE, 'a') as f:
            f.write("\n\n---\n*Transcription completed on: ")
            f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")
        
        print(f"Transcription complete and saved to {TRANSCRIPT_FILE}")
    
    # Clear the accumulated audio
    accumulated_audio = []

def transcription_worker():
    """Background thread to handle audio recording."""
    global recording
    
    try:
        # Open the audio stream
        stream = sd.InputStream(
            callback=audio_callback,
            channels=1,
            samplerate=SAMPLE_RATE,
            dtype='float32'
        )
        
        with stream:
            print("Audio stream opened")
            
            # Keep the stream open until recording is set to False
            while recording:
                time.sleep(0.1)
            
            print("Audio stream closing")
    
    except Exception as e:
        print(f"Error in transcription worker: {str(e)}")
        recording = False

def processing_worker():
    """Background thread to periodically process audio segments."""
    global recording, last_processed_time
    
    try:
        while recording:
            current_time = time.time()
            elapsed = current_time - last_processed_time
            
            # Process audio every PROCESSING_INTERVAL seconds
            if elapsed >= PROCESSING_INTERVAL:
                process_audio_segment()
                last_processed_time = current_time
            
            # Sleep briefly to avoid consuming too much CPU
            time.sleep(0.5)
    
    except Exception as e:
        print(f"Error in processing worker: {str(e)}")

def process_audio_segment():
    """Process accumulated audio and get transcription."""
    global accumulated_audio, full_transcript
    
    # Check if we have enough audio to process
    if not accumulated_audio:
        return
    
    try:
        # Make a copy of the current audio and clear the buffer
        audio_to_process = accumulated_audio.copy()
        accumulated_audio = []
        
        # Print a status message
        print("\nProcessing audio segment...", end="", flush=True)
        
        # Combine audio chunks
        if audio_to_process:
            # Combine all accumulated audio chunks
            all_audio = np.vstack(audio_to_process)
            
            # Create temporary file for the audio
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_filename = temp_file.name
            
            # Save the audio to the temp file
            wavfile.write(temp_filename, SAMPLE_RATE, all_audio)
            
            try:
                # Transcribe the audio segment
                segment_transcript = transcribe_audio(temp_filename)
                
                # If we got a transcript, add it to the full transcript
                if segment_transcript and segment_transcript != "No transcription text was returned by the API.":
                    if segment_transcript.startswith("Error:"):
                        print(f"\nTranscription error: {segment_transcript}")
                    else:
                        # Add to full transcript with spacing
                        if full_transcript:
                            full_transcript += " " + segment_transcript
                        else:
                            full_transcript = segment_transcript
                        
                        # Print the new segment
                        print(f" Done\nTranscript: \"{segment_transcript}\"")
                        
                        # Append to the transcript file
                        with open(TRANSCRIPT_FILE, 'a') as f:
                            f.write(segment_transcript + " ")
                else:
                    print(f" No speech detected")
            
            finally:
                # Clean up the temporary file
                try:
                    os.remove(temp_filename)
                except:
                    pass
    
    except Exception as e:
        print(f"\nError processing audio segment: {str(e)}")
        import traceback
        traceback.print_exc()

def transcribe_audio(audio_file):
    """Transcribe audio using Gemini Flash 2.0."""
    # Read audio file
    with open(audio_file, 'rb') as f:
        audio_data = f.read()
    
    # Base64 encode audio data
    b64_audio = base64.b64encode(audio_data).decode('utf-8')
    
    # Initialize Gemini model
    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash-exp"
    )
    
    # Create request payload with instructions as text, followed by audio
    # Using the correct format expected by the API
    request_data = {
        "parts": [
            {"text": "Transcribe the following audio verbatim. Provide only the exact words spoken, with no interpretation, summary, or additional context."},
            {
                "inline_data": {
                    "mime_type": "audio/wav", 
                    "data": b64_audio
                }
            }
        ]
    }
    
    # Call Gemini API
    try:
        response = model.generate_content(request_data)
        
        if hasattr(response, 'text') and response.text:
            # Remove any remaining interpretation phrases just in case
            transcript = response.text.strip()
            interpretation_phrases = [
                "This sounds like", 
                "The audio appears to", 
                "I hear what sounds like",
                "The sound appears to be",
                "Sounds like",
                "I'm sorry, I can't understand"
            ]
            
            for phrase in interpretation_phrases:
                if transcript.startswith(phrase):
                    # Try to extract just the quoted content if available
                    import re
                    quotes = re.findall(r'"([^"]*)"', transcript)
                    if quotes:
                        return quotes[0]
                    else:
                        # If no quotes, just remove the interpretation prefix
                        parts = transcript.split(":", 1)
                        if len(parts) > 1:
                            return parts[1].strip()
            
            return transcript
        else:
            return "No transcription text was returned by the API."
    except Exception as e:
        print(f"Error calling Gemini API: {str(e)}")
        return f"Error: {str(e)}"
    
def exit_app():
    """Exit the application."""
    if recording:
        stop_transcription()
    
    icon.stop()

def setup_menu():
    """Create the taskbar menu."""
    return pystray.Menu(
        item('Start Transcription', start_transcription, enabled=lambda item: not recording),
        item('Stop Transcription', stop_transcription, enabled=lambda item: recording),
        pystray.Menu.SEPARATOR,
        item('Exit', exit_app)
    )

def main():
    """Main function to run the taskbar app."""
    global icon
    
    # Print configuration settings
    print(f"Using sample rate: {SAMPLE_RATE} Hz")
    print(f"Processing interval: {PROCESSING_INTERVAL} seconds")
    print(f"Transcript file: {TRANSCRIPT_FILE}")
    
    # Create the icon
    icon = pystray.Icon("transcriber", create_icon(), "Gemini Transcriber", setup_menu())
    
    # Run the icon
    icon.run()

if __name__ == "__main__":
    main()