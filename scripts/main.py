# Imports
import gradio as gr
from modules import script_callbacks, shared
from modules.call_queue import wrap_gradio_gpu_call
from modules.shared import cmd_opts
from modules.ui import setup_progressbar
import threading, time, os

# Default file name
file_name = "completion_sound.wav"

# Default file path (this script's path by default)
file_path = os.path.dirname(os.path.abspath(__file__))

# File path for notification audio file
filePath = os.path.join(file_path, file_name)

# How many seconds should have elapsed before a notification is played?
notificationTime = 0

# Store current generation status
isIdle = True
isEnabled = True
exit_event = threading.Event()

# Play completion sound when generation is complete
def play_completion_sound(args):
    if is_valid_audio_file(filePath):
        from playsound import playsound
        playsound(filePath)
    else:
        print('[Notifications] Invalid file or filepath!')


def start():
    # Install playsound if necessary
    from launch import is_installed, run_pip
    if not is_installed("playsound"):
        # Install soundfile using pip
        print('[Notifications] Playsound is missing! Installing...')
        run_pip("install playsound")

    # Stop the previous thread if it exists
    close_thread()

    # Start monitoring generation state
    global exit_event
    exit_event = threading.Event()
    state_watcher = threading.Thread(target=state_watcher_thread, args=(exit_event,), daemon=False)
    state_watcher.start()




# Monitor generation state for completion
def state_watcher_thread(exit_event):
    global isIdle

    start_time = None

    while not exit_event.is_set():
        if shared.state.job_count == 0:
            if not isIdle:
                isIdle = True
                if isEnabled:
                    
                    if start_time:
                        end_time = time.time()
                        elapsed_time = end_time - start_time
                        if elapsed_time >= notificationTime:
                           play_completion_sound(None)

                        # Print the time for funsies
                        # print(f"Generation completed in {elapsed_time:.2f} seconds!")
                        start_time = None
        else:
            isIdle = False
            if start_time is None:
                start_time = time.time()

        time.sleep(0.1)


def close_thread():
    exit_event.set()


def toggle_enable(enabled):
    global isEnabled
    isEnabled = enabled
    if isEnabled:
        print('[Notifications] Enabled!')
    else:
        print('[Notifications] Disabled!')

def save_settings(enabled, path, delay):
    global isEnabled, filePath, notificationTime
    isEnabled = enabled
    filePath = path
    notificationTime = delay
    print('[Notifications] Settings Saved!')

def set_filepath(path):
    global filePath
    filePath = path
    print('[Notifications] Filepath updated! Be sure to test with the Preview button.')

def set_delay(delay):
    global notificationTime
    notificationTime = delay

def is_valid_audio_file(file_path):
    if not os.path.exists(file_path):
        return False

    file_extension = os.path.splitext(file_path)[1].lower()
    if file_extension in ['.mp3', '.wav']:
        return True

    return False

def on_ui_tabs():
    # Set the state of the extension
    def toggle_enabled():
        global isEnabled
        isEnabled = nt_enabled  # Update the isEnabled variable with the checkbox value

    # Update the file directory for the audio file
    def update_source():
        global file_name
        file_name = nt_src.value
    
    start()
    with gr.Blocks() as notification_interface:
        with gr.Row(equal_height=True):
            with gr.Column(variant="panel"):
                # Checkbox to enable/disable the sound effect
                nt_enabled = gr.Checkbox(label="Audio Notification Enabled", value=isEnabled)

                # Text box to set the path to the audio file
                nt_src = gr.Textbox(label='Notification Sound', value=filePath, info="Full path of the notification audio file to play (.mp3/.wav)")

                # Number field for seconds
                nt_delay = gr.Number(value=notificationTime,label="Minimum generation time",info="Notifications will only play if the generation took more seconds than this")

                with gr.Row():
                    # Button to preview the sound effect
                    sp_preview = gr.Button(value="Preview")

                    # Button to save latest values
                    sp_save = gr.Button(value="Save", variant='primary')
                    
        nt_enabled.change(fn=toggle_enable, inputs=nt_enabled)
        sp_preview.click(fn=lambda:play_completion_sound(None))
        sp_save.click(fn=set_filepath, inputs=nt_src)
        nt_delay.change(fn=set_delay,inputs=nt_delay)


    return (notification_interface, "Notifications", "notification_interface"),

script_callbacks.on_ui_tabs(on_ui_tabs)
script_callbacks.on_before_reload(close_thread)