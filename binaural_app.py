import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import numpy as np
import sounddevice as sd
import soundfile as sf
import threading
import time
from scipy.signal import butter, lfilter
import os
import json
import queue

class BinauralApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PYnaural - Binaural Beat Generator")
        self.root.geometry("800x600")
        self.root.configure(bg="#f0f0f0")
        
        # Audio settings
        self.sample_rate = 44100
        self.block_size = 1024
        self.stream = None
        self.is_playing = False
        self.tracks = []
        self.track_counter = 0
        self.volume = 0.5
        self.duration = 180
        self.current_sample = 0
        self.phase_accumulator = {}
        self.audio_lock = threading.Lock()
        self.audio_queue = queue.Queue(maxsize=4)
        self.last_buffer = None  # Store last buffer for smooth transitions
        
        # Create main container frames
        self.left_panel = ttk.Frame(self.root)
        self.left_panel.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        
        # Create UI components
        self.create_control_panel()
        self.create_tracks_panel()
        
        # Ensure clean shutdown
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def audio_callback(self, outdata, frames, time, status):
        try:
            if self.is_playing:
                # Calculate time values for this block
                t = np.arange(self.current_sample, self.current_sample + frames) / self.sample_rate
                
                # Generate audio
                data = self.generate_audio(t)
                
                # Apply volume
                data *= self.volume
                
                # Update sample counter
                self.current_sample += frames
                
                # Write to output buffer
                outdata[:] = data
            else:
                outdata.fill(0)
                
        except Exception as e:
            print(f"Callback error: {e}")
            outdata.fill(0)
    
    def start_playback(self):
        if not self.tracks:
            messagebox.showinfo("No Tracks", "Please add at least one track first.")
            return
            
        self.is_playing = True
        self.play_button.config(text="Stop")
        self.current_sample = 0
        self.phase_accumulator = {}  # Reset phase accumulator
        self.last_buffer = None  # Reset last buffer
        
        try:
            # Start the audio stream with specific settings
            self.stream = sd.OutputStream(
                channels=2,
                samplerate=self.sample_rate,
                blocksize=self.block_size,
                callback=self.audio_callback,
                dtype='float32',
                latency='low',
                prime_output_buffers_using_stream_callback=True
            )
            self.stream.start()
            
        except Exception as e:
            print(f"Error starting playback: {e}")
            self.stop_playback()
    
    def stop_playback(self):
        self.is_playing = False
        self.play_button.config(text="▶ Play")
        
        if self.stream is not None:
            self.stream.stop()
            self.stream.close()
            self.stream = None
            self.last_buffer = None
    
    def on_closing(self):
        self.stop_playback()
        self.root.destroy()
    
    def create_control_panel(self):
        # Main control panel frame in left panel
        control_panel = ttk.LabelFrame(self.left_panel, text="Control Panel")
        control_panel.pack(fill="x", padx=5, pady=5)
        
        # Style configuration
        style = ttk.Style()
        style.configure("Play.TButton", padding=10)
        
        # Playback controls
        playback_frame = ttk.Frame(control_panel)
        playback_frame.pack(fill="x", padx=5, pady=5)
        
        # Play/Pause button with larger size
        self.play_button = ttk.Button(playback_frame, text="▶ Play", 
                                     command=self.toggle_play, style="Play.TButton")
        self.play_button.pack(side="left", padx=5)
        
        # Volume control
        ttk.Label(playback_frame, text="Volume:").pack(side="left", padx=(15, 5))
        volume_frame = ttk.Frame(playback_frame)
        volume_frame.pack(side="left", padx=5)
        
        self.volume_slider = ttk.Scale(volume_frame, from_=0, to=1, value=0.5, 
                                     orient="horizontal", length=150)
        self.volume_slider.pack(side="left")
        
        self.volume_entry = ttk.Entry(volume_frame, width=5)
        self.volume_entry.pack(side="left", padx=5)
        self.volume_entry.insert(0, "50%")
        
        # Bind events for volume control
        self.volume_slider.configure(command=self.update_volume_from_slider)
        self.volume_entry.bind('<Return>', self.update_volume_from_entry)
        self.volume_entry.bind('<FocusOut>', self.update_volume_from_entry)
        
        # Duration control
        duration_frame = ttk.Frame(control_panel)
        duration_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(duration_frame, text="Duration (seconds):").pack(side="left", padx=5)
        
        self.duration_var = tk.StringVar(value=str(self.duration))
        self.duration_entry = ttk.Entry(duration_frame, textvariable=self.duration_var, width=8)
        self.duration_entry.pack(side="left", padx=5)
        
        self.duration_slider = ttk.Scale(duration_frame, from_=10, to=600, value=self.duration,
                                        orient="horizontal", length=300, command=self.set_duration_from_slider)
        self.duration_slider.pack(side="left", padx=5, fill="x", expand=True)
        
        # Set duration button
        ttk.Button(duration_frame, text="Set", command=self.set_duration_from_entry).pack(side="left", padx=5)
        
        # Export WAV button
        export_frame = ttk.Frame(control_panel)
        export_frame.pack(fill="x", padx=5, pady=5)
        
        self.export_button = ttk.Button(export_frame, text="Export to WAV", command=self.export_wav)
        self.export_button.pack(side="right", padx=5)
        
    def create_tracks_panel(self):
        # Tracks panel in left panel
        tracks_panel = ttk.LabelFrame(self.left_panel, text="Tracks")
        tracks_panel.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Track controls
        controls_frame = ttk.Frame(tracks_panel)
        controls_frame.pack(fill="x", padx=5, pady=5)
        
        # Add track buttons
        ttk.Button(controls_frame, text="➕ Binaural Beat", 
                  command=lambda: self.add_track("binaural")).pack(side="left", padx=5)
                  
        ttk.Button(controls_frame, text="➕ White Noise", 
                  command=lambda: self.add_track("noise")).pack(side="left", padx=5)
                  
        ttk.Button(controls_frame, text="➕ Tone", 
                  command=lambda: self.add_track("tone")).pack(side="left", padx=5)
        
        # Import/Export buttons
        ttk.Button(controls_frame, text="Import Settings", 
                  command=self.import_settings).pack(side="right", padx=5)
        ttk.Button(controls_frame, text="Export Settings", 
                  command=self.export_settings).pack(side="right", padx=5)
        
        # Tracks container with scrollbar
        self.tracks_canvas = tk.Canvas(tracks_panel, bg="#f0f0f0")
        scrollbar = ttk.Scrollbar(tracks_panel, orient="vertical", command=self.tracks_canvas.yview)
        self.tracks_frame = ttk.Frame(self.tracks_canvas)
        
        self.tracks_frame.bind("<Configure>", 
                              lambda e: self.tracks_canvas.configure(scrollregion=self.tracks_canvas.bbox("all")))
        
        self.tracks_canvas.create_window((0, 0), window=self.tracks_frame, anchor="nw")
        self.tracks_canvas.configure(yscrollcommand=scrollbar.set)
        
        self.tracks_canvas.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scrollbar.pack(side="right", fill="y")
        
    def update_volume_from_slider(self, value):
        self.volume = float(value)
        self.volume_entry.delete(0, tk.END)
        self.volume_entry.insert(0, f"{int(self.volume * 100)}%")
    
    def update_volume_from_entry(self, event=None):
        try:
            value = self.volume_entry.get().rstrip('%')
            volume = float(value) / 100
            if 0 <= volume <= 1:
                self.volume = volume
                self.volume_slider.set(volume)
            else:
                raise ValueError
        except ValueError:
            self.volume_entry.delete(0, tk.END)
            self.volume_entry.insert(0, f"{int(self.volume * 100)}%")
    
    def create_slider_with_entry(self, parent, text, from_, to, variable, width=8, unit=""):
        frame = ttk.Frame(parent)
        frame.pack(fill="x", padx=5, pady=2)
        
        ttk.Label(frame, text=text).pack(side="left", padx=5)
        
        slider = ttk.Scale(frame, from_=from_, to=to, variable=variable, orient="horizontal")
        slider.pack(side="left", fill="x", expand=True, padx=5)
        
        entry = ttk.Entry(frame, width=width)
        entry.pack(side="left", padx=5)
        
        def update_entry(val):
            entry.delete(0, tk.END)
            entry.insert(0, f"{float(val):.2f}{unit}")
            
        def update_slider(event=None):
            try:
                val = float(entry.get().rstrip(unit))
                if from_ <= val <= to:
                    variable.set(val)
                else:
                    raise ValueError
            except ValueError:
                update_entry(variable.get())
        
        slider.configure(command=update_entry)
        entry.bind('<Return>', update_slider)
        entry.bind('<FocusOut>', update_slider)
        
        # Initial value
        update_entry(variable.get())
        
        return slider, entry
    
    def set_duration_from_slider(self, value):
        self.duration = int(float(value))
        self.duration_var.set(str(self.duration))
    
    def set_duration_from_entry(self):
        try:
            duration = int(float(self.duration_var.get()))
            if 1 <= duration <= 3600:  # Limit to reasonable range
                self.duration = duration
                self.duration_slider.set(min(duration, 600))  # Slider max is 600
            else:
                messagebox.showwarning("Invalid Duration", 
                                      "Please enter a duration between 1 and 3600 seconds.")
                self.duration_var.set(str(self.duration))
        except ValueError:
            messagebox.showwarning("Invalid Input", "Please enter a valid number.")
            self.duration_var.set(str(self.duration))
    
    def toggle_play(self):
        if self.is_playing:
            self.stop_playback()
        else:
            self.start_playback()
    
    def soft_clip(self, data, threshold=0.8):
        """Apply soft clipping to prevent harsh digital clipping"""
        # Apply tanh-based soft clipping with smoother transition
        return np.tanh(data * threshold) / threshold
    
    def generate_audio(self, t):
        """Generate audio for all active tracks"""
        with self.audio_lock:
            if not self.tracks:
                return np.zeros((len(t), 2))
            
            # Initialize output buffer
            output = np.zeros((len(t), 2))
            
            # Generate each track
            for track in self.tracks:
                if not track['enabled'].get():
                    continue
                    
                track_type = track['type']
                track_volume = track['volume'].get()
                
                if track_type == 'binaural':
                    track_data = self.generate_binaural(t, track)
                elif track_type == 'noise':
                    track_data = self.generate_noise(len(t), track)
                elif track_type == 'tone':
                    track_data = self.generate_tone(t, track)
                else:
                    continue
                
                # Apply track volume and add to mix
                output += track_data * track_volume
            
            return output
    
    def generate_binaural(self, t, track):
        base_freq = track["base_freq"].get()
        beat_freq = track["beat_freq"].get()
        
        # Simple sine wave generation
        left_freq = base_freq - beat_freq/2
        right_freq = base_freq + beat_freq/2
        
        left_channel = np.sin(2 * np.pi * left_freq * t) * 0.5
        right_channel = np.sin(2 * np.pi * right_freq * t) * 0.5
        
        return np.column_stack((left_channel, right_channel))
    
    def generate_noise(self, num_samples, track):
        # Simple white noise
        noise = np.random.normal(0, 0.5, num_samples)
        return np.column_stack((noise, noise))
    
    def generate_tone(self, t, track):
        frequency = track["frequency"].get()
        
        # Simple sine wave generation
        tone = np.sin(2 * np.pi * frequency * t) * 0.5
        
        return np.column_stack((tone, tone))
    
    def apply_panning(self, stereo_data, t, track):
        pan_mode = track["pan_mode"].get()
        
        if pan_mode == "center":
            return stereo_data
        elif pan_mode == "hard-left":
            return np.column_stack((stereo_data[:, 0], np.zeros_like(stereo_data[:, 1])))
        elif pan_mode == "hard-right":
            return np.column_stack((np.zeros_like(stereo_data[:, 0]), stereo_data[:, 1]))
        else:  # auto-pan
            pan_speed = track["pan_speed"].get()
            pan_depth = track["pan_depth"].get()
            pan_direction = track["pan_direction"].get()
            
            # Create panning envelope
            if pan_direction == "left-to-right":
                pan_env = pan_depth * np.sin(2 * np.pi * pan_speed * t)
            elif pan_direction == "right-to-left":
                pan_env = -pan_depth * np.sin(2 * np.pi * pan_speed * t)
            else:  # alternate
                pan_env = pan_depth * np.sin(2 * np.pi * pan_speed * t)
            
            # Apply panning using equal power law
            pan_pos = np.clip(pan_env, -1, 1)
            angle = (pan_pos + 1) * np.pi / 4  # Convert -1..1 to 0..π/2
            
            left_gain = np.cos(angle)
            right_gain = np.sin(angle)
            
            # Apply the gains to create the stereo effect
            panned_data = np.zeros_like(stereo_data)
            panned_data[:, 0] = stereo_data[:, 0] * left_gain
            panned_data[:, 1] = stereo_data[:, 1] * right_gain
            
            return panned_data

    def export_wav(self):
        """Export the current audio to a WAV file"""
        if not self.tracks:
            messagebox.showinfo("No Tracks", "Please add at least one track first.")
            return
            
        # Get save location
        file_path = filedialog.asksaveasfilename(
            defaultextension=".wav",
            filetypes=[("WAV files", "*.wav"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
            
        try:
            # Calculate total samples
            total_samples = int(self.duration * self.sample_rate)
            
            # Create progress window
            progress_window = tk.Toplevel(self.root)
            progress_window.title("Exporting...")
            progress_window.geometry("300x100")
            progress_window.transient(self.root)
            progress_window.grab_set()
            
            progress_var = tk.DoubleVar()
            progress_bar = ttk.Progressbar(progress_window, variable=progress_var, maximum=100)
            progress_bar.pack(fill="x", padx=10, pady=10)
            
            status_label = ttk.Label(progress_window, text="Generating audio...")
            status_label.pack(pady=5)
            
            def update_progress(current, total, status_text="Generating audio..."):
                progress = (current / total) * 100
                progress_var.set(progress)
                status_label.config(text=status_text)
                progress_window.update()
            
            def do_export():
                try:
                    # Generate audio in chunks to prevent memory issues
                    chunk_size = 44100  # 1 second chunks
                    audio_data = np.zeros((total_samples, 2))
                    
                    for i in range(0, total_samples, chunk_size):
                        chunk_end = min(i + chunk_size, total_samples)
                        t = np.arange(i, chunk_end) / self.sample_rate
                        
                        # Generate chunk
                        chunk = self.generate_audio(t)
                        
                        # Apply soft clipping to prevent harsh digital clipping
                        chunk = self.soft_clip(chunk)
                        
                        # Store chunk
                        audio_data[i:chunk_end] = chunk
                        
                        # Update progress
                        update_progress(chunk_end, total_samples)
                    
                    # Normalize the final audio
                    max_val = np.max(np.abs(audio_data))
                    if max_val > 1.0:
                        audio_data /= max_val
                    
                    # Save to file
                    update_progress(total_samples, total_samples, "Saving file...")
                    sf.write(file_path, audio_data, self.sample_rate)
                    
                    progress_window.destroy()
                    messagebox.showinfo("Success", "Audio exported successfully!")
                    
                except Exception as e:
                    progress_window.destroy()
                    messagebox.showerror("Error", f"Failed to export audio: {str(e)}")
            
            # Start export in a separate thread
            threading.Thread(target=do_export, daemon=True).start()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export audio: {str(e)}")
    
    def export_settings(self):
        if not self.tracks:
            messagebox.showinfo("No Tracks", "Please add at least one track first.")
            return
            
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Export Settings"
        )
        
        if not file_path:
            return
            
        settings = {
            "volume": self.volume,
            "duration": self.duration,
            "tracks": []
        }
        
        for track in self.tracks:
            track_data = {
                "type": track["type"],
                "title": track["title"].get(),
                "enabled": track["enabled"].get(),
                "volume": track["volume"].get(),
                "pan_mode": track["pan_mode"].get()
            }
            
            # Add pan settings if auto-pan is enabled
            if track["pan_mode"].get() == "auto-pan":
                track_data.update({
                    "pan_direction": track["pan_direction"].get(),
                    "pan_speed": track["pan_speed"].get(),
                    "pan_depth": track["pan_depth"].get()
                })
            
            if track["type"] == "binaural":
                track_data.update({
                    "base_freq": track["base_freq"].get(),
                    "beat_freq": track["beat_freq"].get()
                })
            elif track["type"] == "noise":
                track_data.update({
                    "noise_type": track["noise_type"].get(),
                    "low_cut": track["low_cut"].get(),
                    "high_cut": track["high_cut"].get()
                })
            elif track["type"] == "tone":
                track_data.update({
                    "frequency": track["frequency"].get(),
                    "iso_enabled": track["iso_enabled"].get(),
                    "iso_freq": track["iso_freq"].get(),
                    "iso_depth": track["iso_depth"].get(),
                    "mod_enabled": track["mod_enabled"].get(),
                    "min_freq": track["min_freq"].get(),
                    "max_freq": track["max_freq"].get(),
                    "mod_speed": track["mod_speed"].get()
                })
            
            settings["tracks"].append(track_data)
        
        try:
            with open(file_path, 'w') as f:
                json.dump(settings, f, indent=2)
            messagebox.showinfo("Export Complete", f"Settings saved to:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Export Failed", f"Error: {str(e)}")
            
    def import_settings(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Import Settings"
        )
        
        if not file_path:
            return
            
        try:
            with open(file_path, 'r') as f:
                settings = json.load(f)
            
            # Clear existing tracks
            for track in self.tracks:
                track["frame"].destroy()
            self.tracks.clear()
            self.track_counter = 0
            
            # Set global settings
            self.volume = settings["volume"]
            self.volume_slider.set(self.volume)
            self.volume_entry.delete(0, tk.END)
            self.volume_entry.insert(0, f"{int(self.volume * 100)}%")
            
            self.duration = settings["duration"]
            self.duration_slider.set(min(self.duration, 600))
            self.duration_var.set(str(self.duration))
            
            # Create tracks
            for track_data in settings["tracks"]:
                self.add_track(track_data["type"], track_data)
                
            messagebox.showinfo("Import Complete", "Settings imported successfully")
        except Exception as e:
            messagebox.showerror("Import Failed", f"Error: {str(e)}")

    def add_track(self, track_type, settings=None):
        # Create a new track frame
        track_id = self.track_counter
        frame = ttk.LabelFrame(self.tracks_frame, text=f"Track {track_id+1}: {track_type.title()}")
        frame.pack(fill="x", padx=5, pady=5)
        
        # Common controls
        controls_frame = ttk.Frame(frame)
        controls_frame.pack(fill="x", padx=5, pady=5)
        
        # Track title
        title = settings["title"] if settings else f"{track_type.title()} {track_id+1}"
        title_var = tk.StringVar(value=title)
        title_entry = ttk.Entry(controls_frame, textvariable=title_var, width=20)
        title_entry.pack(side="left", padx=5)
        
        # Remove button
        remove_btn = ttk.Button(controls_frame, text="Remove", 
                               command=lambda tid=track_id: self.remove_track(tid))
        remove_btn.pack(side="right", padx=5)
        
        # Track-specific controls
        track_data = {
            "id": track_id,
            "type": track_type,
            "frame": frame,
            "title": title_var,
            "enabled": tk.BooleanVar(value=settings["enabled"] if settings else True),
            "volume": tk.DoubleVar(value=settings["volume"] if settings else 1.0)
        }
        
        # Add Enable checkbox
        enable_check = ttk.Checkbutton(controls_frame, text="Enable", 
                                      variable=track_data["enabled"])
        enable_check.pack(side="right", padx=5)
        
        # Add volume control
        volume_frame = ttk.Frame(frame)
        volume_frame.pack(fill="x", padx=5, pady=2)
        ttk.Label(volume_frame, text="Volume:").pack(side="left", padx=5)
        volume_slider = ttk.Scale(volume_frame, from_=0, to=1, 
                                 variable=track_data["volume"],
                                 orient="horizontal")
        volume_slider.pack(side="left", fill="x", expand=True, padx=5)
        
        # Specific controls based on track type
        if track_type == "binaural":
            self.setup_binaural_controls(frame, track_data, settings)
        elif track_type == "noise":
            self.setup_noise_controls(frame, track_data, settings)
        elif track_type == "tone":
            self.setup_tone_controls(frame, track_data, settings)
        
        # Add pan controls for all track types
        self.setup_pan_controls(frame, track_data, settings)
        
        # Add to tracks list
        self.tracks.append(track_data)
        self.track_counter += 1
        
    def remove_track(self, track_id):
        for i, track in enumerate(self.tracks):
            if track["id"] == track_id:
                track["frame"].destroy()
                self.tracks.pop(i)
                break
                
    def setup_binaural_controls(self, frame, track_data, settings=None):
        controls = ttk.Frame(frame)
        controls.pack(fill="x", padx=5, pady=2)
        
        # Base frequency control
        base_freq = tk.DoubleVar(value=settings["base_freq"] if settings else 200.0)
        track_data["base_freq"] = base_freq
        self.create_slider_with_entry(controls, "Base Frequency:", 20, 1000, base_freq, unit=" Hz")
        
        # Beat frequency control
        beat_freq = tk.DoubleVar(value=settings["beat_freq"] if settings else 7.83)
        track_data["beat_freq"] = beat_freq
        self.create_slider_with_entry(controls, "Beat Frequency:", 0.5, 40.0, beat_freq, unit=" Hz")
        
    def setup_noise_controls(self, frame, track_data, settings=None):
        controls = ttk.Frame(frame)
        controls.pack(fill="x", padx=5, pady=2)
        
        # Noise type selection
        ttk.Label(controls, text="Noise Type:").pack(side="left", padx=5)
        noise_type = tk.StringVar(value=settings["noise_type"] if settings else "white")
        track_data["noise_type"] = noise_type
        noise_combo = ttk.Combobox(controls, textvariable=noise_type, 
                                  values=["white", "pink", "brown"],
                                  state="readonly", width=10)
        noise_combo.pack(side="left", padx=5)
        
        # Frequency controls
        low_cut = tk.DoubleVar(value=settings["low_cut"] if settings else 20.0)
        track_data["low_cut"] = low_cut
        self.create_slider_with_entry(frame, "Low Cut:", 20, 20000, low_cut, unit=" Hz")
        
        high_cut = tk.DoubleVar(value=settings["high_cut"] if settings else 20000.0)
        track_data["high_cut"] = high_cut
        self.create_slider_with_entry(frame, "High Cut:", 20, 20000, high_cut, unit=" Hz")
        
    def setup_tone_controls(self, frame, track_data, settings=None):
        # Basic frequency control
        frequency = tk.DoubleVar(value=settings["frequency"] if settings else 432.0)
        track_data["frequency"] = frequency
        self.create_slider_with_entry(frame, "Frequency:", 20, 20000, frequency, unit=" Hz")
        
        # Isochronic controls
        iso_frame = ttk.Frame(frame)
        iso_frame.pack(fill="x", padx=5, pady=2)
        
        # Enable isochronic checkbox
        iso_enabled = tk.BooleanVar(value=settings["iso_enabled"] if settings else False)
        track_data["iso_enabled"] = iso_enabled
        ttk.Checkbutton(iso_frame, text="Enable Isochronic Pulses", 
                       variable=iso_enabled).pack(side="left", padx=5)
        
        # Isochronic parameters
        iso_freq = tk.DoubleVar(value=settings["iso_freq"] if settings else 7.83)
        track_data["iso_freq"] = iso_freq
        self.create_slider_with_entry(frame, "Pulse Rate:", 0.5, 40.0, iso_freq, unit=" Hz")
        
        iso_depth = tk.DoubleVar(value=settings["iso_depth"] if settings else 1.0)
        track_data["iso_depth"] = iso_depth
        self.create_slider_with_entry(frame, "Pulse Depth:", 0.0, 1.0, iso_depth)
        
        # Frequency modulation controls
        mod_frame = ttk.Frame(frame)
        mod_frame.pack(fill="x", padx=5, pady=2)
        
        # Enable modulation checkbox
        mod_enabled = tk.BooleanVar(value=settings["mod_enabled"] if settings else False)
        track_data["mod_enabled"] = mod_enabled
        ttk.Checkbutton(mod_frame, text="Enable Frequency Modulation", 
                       variable=mod_enabled).pack(side="left", padx=5)
        
        # Modulation parameters
        min_freq = tk.DoubleVar(value=settings["min_freq"] if settings else 20.0)
        track_data["min_freq"] = min_freq
        self.create_slider_with_entry(frame, "Min Freq:", 20, 20000, min_freq, unit=" Hz")
        
        max_freq = tk.DoubleVar(value=settings["max_freq"] if settings else 1000.0)
        track_data["max_freq"] = max_freq
        self.create_slider_with_entry(frame, "Max Freq:", 20, 20000, max_freq, unit=" Hz")
        
        mod_speed = tk.DoubleVar(value=settings["mod_speed"] if settings else 0.5)
        track_data["mod_speed"] = mod_speed
        self.create_slider_with_entry(frame, "Mod Speed:", 0.1, 10.0, mod_speed, unit=" Hz")
        
    def setup_pan_controls(self, frame, track_data, settings=None):
        pan_frame = ttk.Frame(frame)
        pan_frame.pack(fill="x", padx=5, pady=2)
        
        # Pan mode selection
        ttk.Label(pan_frame, text="Pan Mode:").pack(side="left", padx=5)
        pan_mode = tk.StringVar(value=settings["pan_mode"] if settings else "center")
        track_data["pan_mode"] = pan_mode
        mode_combo = ttk.Combobox(pan_frame, textvariable=pan_mode,
                                 values=["center", "hard-left", "hard-right", "auto-pan"],
                                 state="readonly", width=12)
        mode_combo.pack(side="left", padx=5)
        
        # Auto-pan controls frame
        auto_pan_frame = ttk.Frame(frame)
        auto_pan_frame.pack(fill="x", padx=5, pady=2)
        
        # Pan direction
        ttk.Label(auto_pan_frame, text="Direction:").pack(side="left", padx=5)
        pan_direction = tk.StringVar(value=settings["pan_direction"] if settings else "alternate")
        track_data["pan_direction"] = pan_direction
        direction_combo = ttk.Combobox(auto_pan_frame, textvariable=pan_direction,
                                     values=["left-to-right", "right-to-left", "alternate"],
                                     state="readonly", width=12)
        direction_combo.pack(side="left", padx=5)
        
        # Pan speed and depth
        pan_speed = tk.DoubleVar(value=settings["pan_speed"] if settings else 0.5)
        track_data["pan_speed"] = pan_speed
        self.create_slider_with_entry(frame, "Speed:", 0.1, 2.0, pan_speed, unit=" Hz")
        
        pan_depth = tk.DoubleVar(value=settings["pan_depth"] if settings else 0.5)
        track_data["pan_depth"] = pan_depth
        self.create_slider_with_entry(frame, "Depth:", 0.0, 1.0, pan_depth)
        
        # Function to toggle auto-pan controls visibility
        def update_pan_controls(*args):
            if pan_mode.get() == "auto-pan":
                auto_pan_frame.pack(fill="x", padx=5, pady=2)
            else:
                auto_pan_frame.pack_forget()
        
        # Bind the update function to pan mode changes
        pan_mode.trace_add("write", update_pan_controls)
        # Initial state
        update_pan_controls()

    def apply_anti_aliasing(self, data):
        """Apply a simple anti-aliasing filter"""
        # Simple 2-pole lowpass filter
        alpha = 0.1  # Filter coefficient
        filtered = np.zeros_like(data)
        filtered[0] = data[0]
        for i in range(1, len(data)):
            filtered[i] = alpha * data[i] + (1 - alpha) * filtered[i-1]
        return filtered

def main():
    root = tk.Tk()
    app = BinauralApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()