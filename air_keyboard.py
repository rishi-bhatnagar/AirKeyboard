import cv2
import mediapipe as mp
import pyautogui
import tkinter as tk
from PIL import Image, ImageTk, Image
import time
import math

# ---------------- Hand Tracking ----------------
class HandTracker:
    def __init__(self, max_hands=2, detection_conf=0.7):
        self.mp_hands = mp.solutions.hands
        self.mp_draw = mp.solutions.drawing_utils
        self.hands = self.mp_hands.Hands(max_num_hands=max_hands, min_detection_confidence=detection_conf)

    @staticmethod
    def distance(p1, p2):
        return math.hypot(p1[0]-p2[0], p1[1]-p2[1])

    def get_hands(self, frame):
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return self.hands.process(rgb_frame)

# ---------------- Keyboard ----------------
class VirtualKeyboard:
    THEMES = {
        "Dark": {"bg": "#111111", "key_fill": "#222222", "key_outline": "#00FFFF",
                 "highlight": "#00FF00", "text": "#00FFFF", "flash": "#00FF00"},
        "Pink": {"bg": "#1e001e", "key_fill": "#330033", "key_outline": "#ff66ff",
                 "highlight": "#ff00ff", "text": "#ff99ff", "flash": "#ff00ff"},
        "Neon": {"bg": "#000000", "key_fill": "#111111", "key_outline": "#39ff14",
                 "highlight": "#00ffff", "text": "#39ff14", "flash": "#00ffff"},
        "Cyber": {"bg": "#0d0d0d", "key_fill": "#1a1a1a", "key_outline": "#ff1493",
                  "highlight": "#ff69b4", "text": "#ff69b4", "flash": "#ff69b4"}
    }

    KEYS = [
        ['`','1','2','3','4','5','6','7','8','9','0','-','=', 'TAB'],
        ['Q','W','E','R','T','Y','U','I','O','P','[',']','\\'],
        ['CAPS','A','S','D','F','G','H','J','K','L',';','\''],
        ['SHIFT','Z','X','C','V','B','N','M',',','.','/','SHIFT'],
        ['SPACE','BACK','ENTER']
    ]

    KEY_SIZE = (55, 55)
    SPECIAL_SIZE = {'SPACE': (300, 45), 'BACK': (75, 45), 'ENTER': (75, 45),
                    'SHIFT': (65, 40), 'TAB': (65, 40), 'CAPS': (65, 40)}

    SHIFT_MAP = {'`':'~','1':'!','2':'@','3':'#','4':'$','5':'%','6':'^','7':'&',
                 '8':'*','9':'(','0':')','-':'_','=':'+','[':'{',']':'}','\\':'|',
                 ';':':','\'':'"','<':',','>':'.','/':'?'}

    def __init__(self, root, theme="Dark"):
        self.root = root
        self.current_theme = self.THEMES[theme]
        self.key_rects = {}
        self.key_texts = {}
        self.pressed_flash = {}
        self.prev_key = None
        self.last_time = 0
        self.caps_lock = False
        self.shift_active = False

        self.canvas_width = 1300
        self.canvas_height = 400
        self.canvas = tk.Canvas(root, width=self.canvas_width, height=self.canvas_height,
                                bg=self.current_theme["bg"], highlightthickness=0)
        self.canvas.pack()

        self.start_x = 15
        self.start_y = 15
        self.key_spacing = 7
        self.create_keys()
        self.keyboard_right_edge = self.start_x + max([sum([self.SPECIAL_SIZE.get(k,self.KEY_SIZE)[0]+self.key_spacing for k in row]) for row in self.KEYS])

        self.make_draggable()
        self.add_theme_menu()
        self.add_exit_button()

    def create_keys(self):
        y = self.start_y
        for row in self.KEYS:
            x = self.start_x
            for key in row:
                w, h = self.SPECIAL_SIZE.get(key, self.KEY_SIZE)
                self.key_rects[key] = (x, y, x+w, y+h)
                self.pressed_flash[key] = 0
                text_size = 12 if len(key) == 1 else 10
                self.key_texts[key] = self.canvas.create_text(
                    x+w//2, y+h//2, text=key, fill=self.current_theme["text"], font=("Arial", text_size, "bold"), tags="keytext"
                )
                x += w + self.key_spacing
            y += self.KEY_SIZE[1] + self.key_spacing

    def make_draggable(self):
        def start_move(event):
            self.root.x = event.x
            self.root.y = event.y
        def stop_move(event):
            self.root.x = None
            self.root.y = None
        def do_move(event):
            dx = event.x - self.root.x
            dy = event.y - self.root.y
            x = self.root.winfo_x() + dx
            y = self.root.winfo_y() + dy
            self.root.geometry(f"+{x}+{y}")

        self.canvas.bind("<Button-1>", start_move)
        self.canvas.bind("<ButtonRelease-1>", stop_move)
        self.canvas.bind("<B1-Motion>", do_move)

    def add_theme_menu(self):
        theme_menu = tk.OptionMenu(self.root, tk.StringVar(value="Dark"), *self.THEMES.keys(),
                                   command=self.change_theme)
        theme_menu.config(bg="#222222", fg="#00FFFF", font=("Arial",10,"bold"))
        theme_menu.place(x=self.canvas_width-200, y=10)

    def change_theme(self, theme_name):
        self.current_theme = self.THEMES[theme_name]
        self.canvas.config(bg=self.current_theme["bg"])
        for key, text_id in self.key_texts.items():
            self.canvas.itemconfig(text_id, fill=self.current_theme["text"])

    def add_exit_button(self):
        tk.Button(self.root, text="❌", command=self.exit_app,
                  bg=self.current_theme["key_fill"], fg="#FF0000").place(x=self.canvas_width-50, y=10)

    def exit_app(self):
        self.root.quit()

    def handle_key_press(self, key):
        char = key
        if key == "CAPS":
            self.caps_lock = not self.caps_lock
        elif key == "SHIFT":
            self.shift_active = True
        elif key == "SPACE":
            pyautogui.press("space")
        elif key == "BACK":
            pyautogui.press("backspace")
        elif key == "ENTER":
            pyautogui.press("enter")
        elif key == "TAB":
            pyautogui.press("tab")
        else:
            if self.shift_active:
                char = self.SHIFT_MAP.get(char,char.upper())
            elif self.caps_lock and char.isalpha():
                char = char.upper()
            else:
                char = char.lower()
            pyautogui.press(char)
        self.pressed_flash[key] = 5
        self.prev_key = key
        self.last_time = time.time()
        self.shift_active = False

    def update_flash(self):
        self.canvas.delete("flash")
        for key, dur in self.pressed_flash.items():
            if dur > 0:
                x1, y1, x2, y2 = self.key_rects[key]
                color = self.current_theme["flash"]
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="", tags="flash")
                self.pressed_flash[key] -= 1
        self.highlight_special_keys()

    def highlight_key(self, key):
        x1,y1,x2,y2 = self.key_rects[key]
        self.canvas.create_rectangle(x1,y1,x2,y2, outline=self.current_theme["highlight"], width=3, tags="highlight")

    def highlight_special_keys(self):
        # Highlight CAPS and SHIFT if active
        for key, active in [("CAPS", self.caps_lock), ("SHIFT", self.shift_active)]:
            x1,y1,x2,y2 = self.key_rects[key]
            color = "#FFFF00" if active else self.current_theme["key_fill"]
            self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline=self.current_theme["key_outline"], width=3, tags="special_highlight")

    def draw_hint(self):
        self.canvas.delete("hint_text")
        self.canvas.create_text(50,20,text="🤏 Pinch to type", fill=self.current_theme["text"], font=("Arial",16,"bold"), tag="hint_text")

# ---------------- Main App ----------------
class AirKeyboardApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Air Keyboard")
        self.root.geometry("1300x400+200+200")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-transparentcolor", "black")
        self.root.attributes("-alpha", 0.92)

        self.keyboard = VirtualKeyboard(self.root)
        self.tracker = HandTracker()

        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        self.update_camera()
        self.root.bind("<Escape>", lambda e: self.exit_app())
        self.root.mainloop()

    def exit_app(self):
        self.cap.release()
        self.root.destroy()

    def update_camera(self):
        success, img = self.cap.read()
        if success:
            img = cv2.flip(img, 1)
            h,w,c = img.shape
            hands = self.tracker.get_hands(img)
            self.keyboard.canvas.delete("highlight")

            if hands.multi_hand_landmarks:
                for hand in hands.multi_hand_landmarks:
                    self.tracker.mp_draw.draw_landmarks(img, hand, self.tracker.mp_hands.HAND_CONNECTIONS)
                    index_tip = hand.landmark[8]
                    thumb_tip = hand.landmark[4]

                    x_index = int(index_tip.x*w)
                    y_index = int(index_tip.y*h)
                    x_thumb = int(thumb_tip.x*w)
                    y_thumb = int(thumb_tip.y*h)
                    pinch_distance = self.tracker.distance((x_index, y_index), (x_thumb, y_thumb))

                    for key, (kx1,ky1,kx2,ky2) in self.keyboard.key_rects.items():
                        if kx1 < x_index < kx2 and ky1 < y_index < ky2:
                            self.keyboard.highlight_key(key)
                            if pinch_distance < 40 and (key != self.keyboard.prev_key or time.time()-self.keyboard.last_time>0.4):
                                self.keyboard.handle_key_press(key)

            # Camera overlay
            cam_width = 500
            cam_height = int(h/w*cam_width)
            img = cv2.resize(img, (cam_width, cam_height))
            im_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)).convert("RGBA")
            overlay = Image.new("RGBA", im_pil.size, (0,0,0,120))
            im_pil = Image.alpha_composite(im_pil, overlay)
            imgtk = ImageTk.PhotoImage(im_pil)
            self.keyboard.canvas.imgtk = imgtk
            self.keyboard.canvas.delete("camera")
            self.keyboard.canvas.create_image(self.keyboard.keyboard_right_edge + 20, 15, anchor="nw", image=imgtk, tag="camera")

            self.keyboard.update_flash()
            self.keyboard.draw_hint()

        self.keyboard.canvas.after(20, self.update_camera)

# ---------------- Run ----------------
if __name__ == "__main__":
    AirKeyboardApp()
