import socket
import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext, Toplevel
import re


class FarmClient:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Farm Text-Based Online - Client")
        self.window.attributes('-fullscreen', True)
        self.window.configure(bg="#f0f0f0")
        self.window.minsize(650, 550)
        self.socket = None
        self.receive_thread = None
        self.username = None
        self.shop_data = {"pots": [], "seeds": [], "mature_seeds": []}
        self.inventory_seeds = []  # Lưu danh sách hạt giống trong túi
        self.inventory_pots = []  # Lưu danh sách chậu trong túi
        self.command_history = []
        self.history_index = -1
        self.window.bind('<Escape>', lambda e: self.toggle_fullscreen())
        self.create_login_ui()
        self.window.mainloop()

    def toggle_fullscreen(self):
        current_state = self.window.attributes('-fullscreen')
        self.window.attributes('-fullscreen', not current_state)
        if not current_state:
            self.window.geometry("650x550")
        else:
            self.window.state('normal')

    def create_login_ui(self):
        self.clear_window()
        tk.Label(self.window, text="IP Máy chủ:", bg="#f0f0f0", font=("Arial", 12)).pack(pady=5)
        self.entry_ip = tk.Entry(self.window, font=("Arial", 12))
        self.entry_ip.insert(0, "127.0.0.1")
        self.entry_ip.pack(pady=2)

        tk.Label(self.window, text="Tên tài khoản:", bg="#f0f0f0", font=("Arial", 12)).pack(pady=5)
        self.entry_username = tk.Entry(self.window, font=("Arial", 12))
        self.entry_username.pack(pady=2)

        tk.Button(self.window, text="Kết nối", command=self.connect_to_server, font=("Arial", 12)).pack(pady=10)

    def connect_to_server(self):
        ip = self.entry_ip.get().strip()
        self.username = self.entry_username.get().strip()

        if not self.username or not re.match("^[a-zA-Z0-9_]{3,16}$", self.username):
            messagebox.showerror("Lỗi", "Tên tài khoản phải từ 3-16 ký tự, chỉ chứa chữ, số hoặc _.")
            return
        if not re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", ip):
            messagebox.showerror("Lỗi", "Địa chỉ IP không hợp lệ. Nhập theo định dạng: xxx.xxx.xxx.xxx")
            return

        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((ip, 5000))
            self.socket.send(self.username.encode())

            self.clear_window()
            self.create_chat_ui()

            self.receive_thread = threading.Thread(target=self.receive_messages)
            self.receive_thread.daemon = True
            self.receive_thread.start()
        except Exception as e:
            messagebox.showerror("Kết nối thất bại", str(e))
            if self.socket:
                self.socket.close()
                self.socket = None

    def clear_window(self):
        for widget in self.window.winfo_children():
            widget.destroy()

    def create_chat_ui(self):
        self.status_frame = tk.Frame(self.window, bg="#f0f0f0")
        self.status_frame.pack(fill=tk.X, padx=10, pady=5)
        self.weather_label = tk.Label(self.status_frame, text="📍 Đang tải trạng thái...", bg="#f0f0f0", fg="#4682B4",
                                      font=("Arial", 11, "bold"), wraplength=630)
        self.weather_label.pack(anchor="w", pady=1)
        self.island_label = tk.Label(self.status_frame, text="🏝️ Đảo: Đang tải...", bg="#f0f0f0", fg="#FF4500",
                                     font=("Arial", 11, "bold"), wraplength=630)
        self.island_label.pack(anchor="w", pady=1)
        self.money_label = tk.Label(self.status_frame, text="", bg="#f0f0f0", fg="#228B22", font=("Arial", 11, "bold"),
                                    wraplength=630)
        self.money_label.pack(anchor="w", pady=1)
        self.stage_label = tk.Label(self.status_frame, text="", bg="#f0f0f0", fg="#8B4513", font=("Arial", 11, "bold"),
                                    wraplength=630)
        self.stage_label.pack(anchor="w", pady=1)
        self.coop_label = tk.Label(self.status_frame, text="", bg="#f0f0f0", fg="#9932CC", font=("Arial", 11, "bold"),
                                   wraplength=630)
        self.coop_label.pack(anchor="w", pady=1)
        self.pots_label = tk.Label(self.status_frame, text="", bg="#f0f0f0", fg="#6A5ACD", font=("Arial", 11),
                                   wraplength=630)
        self.pots_label.pack(anchor="w", pady=1)
        self.seeds_label = tk.Label(self.status_frame, text="", bg="#f0f0f0", fg="#2E8B57", font=("Arial", 11),
                                    wraplength=630)
        self.seeds_label.pack(anchor="w", pady=1)
        self.farm_labels = []
        self.chat_area = scrolledtext.ScrolledText(self.window, height=15, state="disabled", wrap=tk.WORD,
                                                   font=("Arial", 11), bg="#FFFFFF", fg="black")
        self.chat_area.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)
        self.chat_area.tag_configure("system", foreground="blue")
        self.chat_area.tag_configure("chat", foreground="green")
        self.chat_area.tag_configure("error", foreground="red")
        self.chat_area.tag_configure("tips", foreground="purple", font=("Arial", 11, "bold"))
        self.chat_area.tag_configure("status", foreground="blue", font=("Arial", 11, "bold"))
        self.chat_area.tag_configure("shop", foreground="purple", font=("Arial", 11, "bold"))
        frame = tk.Frame(self.window, bg="#f0f0f0")
        frame.pack(fill=tk.X, padx=10, pady=5)
        self.entry_message = tk.Entry(frame, font=("Arial", 12))
        self.entry_message.pack(side=tk.LEFT, fill=tk.X, expand=True, pady=5)
        self.entry_message.bind("<Return>", lambda event: self.send_message())
        send_button = tk.Button(frame, text="Gửi", command=self.send_message, font=("Arial", 12), bg="#D3D3D3",
                                activebackground="#ADD8E6")
        send_button.pack(side=tk.RIGHT, padx=5)
        send_button.bind("<Enter>", lambda e: send_button.config(bg="#ADD8E6"))
        send_button.bind("<Leave>", lambda e: send_button.config(bg="#D3D3D3"))
        plant_button = tk.Button(frame, text="Trồng cây", command=self.open_plant_window, font=("Arial", 12),
                                 bg="#32CD32", activebackground="#228B22")
        plant_button.pack(side=tk.RIGHT, padx=5)
        plant_button.bind("<Enter>", lambda e: plant_button.config(bg="#228B22"))
        plant_button.bind("<Leave>", lambda e: plant_button.config(bg="#32CD32"))

        harvest_button = tk.Button(frame, text="Thu hoạch", command=self.send_harvest, font=("Arial", 12), bg="#FFD700",
                                   activebackground="#FFA500")
        harvest_button.pack(side=tk.RIGHT, padx=5)
        harvest_button.bind("<Enter>", lambda e: harvest_button.config(bg="#FFA500"))
        harvest_button.bind("<Leave>", lambda e: harvest_button.config(bg="#FFD700"))
        bag_button = tk.Button(frame, text="Mở balo", command=self.send_bag, font=("Arial", 12), bg="#FFFF99",
                               activebackground="#FFC107")
        bag_button.pack(side=tk.RIGHT, padx=5)
        bag_button.bind("<Enter>", lambda e: bag_button.config(bg="#FFC107"))
        bag_button.bind("<Leave>", lambda e: bag_button.config(bg="#FFFF99"))
        shop_button = tk.Button(frame, text="Shop", command=self.open_shop, font=("Arial", 12), bg="#90EE90",
                                activebackground="#3CB371")
        shop_button.pack(side=tk.RIGHT, padx=5)
        shop_button.bind("<Enter>", lambda e: shop_button.config(bg="#3CB371"))
        shop_button.bind("<Leave>", lambda e: shop_button.config(bg="#90EE90"))
        place_pot_button = tk.Button(frame, text="Đặt chậu", command=self.open_place_pot_window, font=("Arial", 12),
                                     bg="#FFA500", activebackground="#FF8C00")
        place_pot_button.pack(side=tk.RIGHT, padx=5)
        place_pot_button.bind("<Enter>", lambda e: place_pot_button.config(bg="#FF8C00"))
        place_pot_button.bind("<Leave>", lambda e: place_pot_button.config(bg="#FFA500"))
        self.entry_message.bind("<Up>", self.on_arrow_up)
        self.entry_message.bind("<Down>", self.on_arrow_down)

    def send_message(self):
        if not self.socket:
            self.append_message("❌ Không có kết nối đến server.", "error")
            return
        msg = self.entry_message.get().strip()
        if msg:
            if not re.match(
                    r"^[\w\s/ăâđêôơưàáảãạèéẻẽẹìíỉĩịòóỏõọùúủũụỳýỷỹỵĂÂĐÊÔƠƯÀÁẢÃẠÈÉẺẼẸÌÍỈĨỊÒÓỎÕỌÙÚỦŨỤỲÝỶỸỴ.,!?]{1,200}$",
                    msg):
                self.append_message(
                    "❌ Tin nhắn/lệnh không hợp lệ (chỉ cho phép chữ, số, khoảng trắng, và một số ký tự đặc biệt).",
                    "error")
                return
            try:
                self.socket.send(msg.encode('utf-8'))
                print(f"[Debug] Gửi: {msg}")  # Log tin nhắn gửi đi
                if not self.command_history or self.command_history[-1] != msg:
                    self.command_history.append(msg)
                    if len(self.command_history) > 100:
                        self.command_history.pop(0)
                self.history_index = len(self.command_history)
                self.entry_message.delete(0, tk.END)
            except ConnectionError as e:
                print(f"[Debug] Lỗi kết nối khi gửi: {e}")
                self.append_message(f"[Kết nối đã bị mất]: {e}", "error")
                if self.socket:
                    try:
                        self.socket.close()
                    except:
                        pass
                    self.socket = None
                self.window.after(0, self.show_reconnect)
            except Exception as e:
                print(f"[Debug] Lỗi gửi: {e}")
                self.append_message(f"[Lỗi gửi]: {e}", "error")

    def send_harvest(self):
        if not self.socket:
            self.append_message("❌ Không có kết nối đến server.", "error")
            return
        try:
            self.socket.send("/thuhoach".encode())
            self.append_message("🌾 Đã gửi lệnh thu hoạch.", "system")
        except Exception as e:
            self.append_message(f"[Lỗi gửi /thuhoach]: {e}", "error")

    def send_bag(self):
        if not self.socket:
            self.append_message("❌ Không có kết nối đến server.", "error")
            return
        try:
            self.socket.send("/balo".encode())
            self.append_message("🎒 Đã gửi lệnh mở balo.", "system")
        except Exception as e:
            self.append_message(f"[Lỗi gửi /balo]: {e}", "error")

    def open_shop(self):
        if not self.socket:
            self.append_message("❌ Không có kết nối đến server.", "error")
            return
        try:
            self.socket.send("/shop".encode())
            self.append_message("🏪 Đã gửi lệnh xem cửa hàng.", "system")
        except Exception as e:
            self.append_message(f"[Lỗi gửi /shop]: {e}", "error")
            return

        shop_window = Toplevel(self.window)
        shop_window.title("Shop")
        shop_window.geometry("400x600")
        shop_window.configure(bg="#f0f0f0")

        canvas = tk.Canvas(shop_window, bg="#f0f0f0")
        scrollbar = tk.Scrollbar(shop_window, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#f0f0f0")

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        def update_shop_display():
            for widget in scrollable_frame.winfo_children():
                widget.destroy()

            tk.Label(scrollable_frame, text="🪴 Chậu:", bg="#f0f0f0", font=("Arial", 12, "bold")).pack(pady=5,
                                                                                                      anchor="w",
                                                                                                      padx=10)
            for pot in self.shop_data["pots"]:
                frame = tk.Frame(scrollable_frame, bg="#f0f0f0")
                frame.pack(fill=tk.X, padx=10, pady=2)
                tk.Label(frame, text=f"{pot['name']} ({pot['emoji']}): {pot['desc']} - Giá: {pot['price']} xu",
                         bg="#f0f0f0", fg="#6A5ACD", font=("Arial", 11)).pack(side="left")
                tk.Button(frame, text="Mua", font=("Arial", 10),
                          command=lambda p=pot['name']: self.send_buy_command(f"/buypot {p}")).pack(side="right",
                                                                                                    padx=5)

            tk.Label(scrollable_frame, text="🌱 Hạt giống:", bg="#f0f0f0", font=("Arial", 12, "bold")).pack(pady=5,
                                                                                                           anchor="w",
                                                                                                           padx=10)
            for seed in self.shop_data["seeds"]:
                frame = tk.Frame(scrollable_frame, bg="#f0f0f0")
                frame.pack(fill=tk.X, padx=10, pady=2)
                tk.Label(frame, text=f"{seed['name']} ({seed['emoji']}): Giá {seed['price']} xu",
                         bg="#f0f0f0", fg="#2E8B57", font=("Arial", 11)).pack(side="left")
                tk.Button(frame, text="Mua", font=("Arial", 10),
                          command=lambda s=seed['name']: self.send_buy_command(f"/buyseed {s}")).pack(side="right",
                                                                                                      padx=5)

            tk.Label(scrollable_frame, text="🌳 Cây trưởng thành:", bg="#f0f0f0", font=("Arial", 12, "bold")).pack(
                pady=5, anchor="w", padx=10)
            for seed in self.shop_data["mature_seeds"]:
                frame = tk.Frame(scrollable_frame, bg="#f0f0f0")
                frame.pack(fill=tk.X, padx=10, pady=2)
                display_name = f"{seed['name']} {seed['mutation']}" if seed[
                    'mutation'] else f"{seed['name']} Trưởng thành"
                tk.Label(frame, text=f"{display_name} ({seed['emoji']}): Giá {seed['price']} xu",
                         bg="#f0f0f0", fg="#2E8B57", font=("Arial", 11)).pack(side="left")
                command = f"/buyseed {seed['name']} {seed['mutation']}" if seed[
                    'mutation'] else f"/buyseed {seed['name']} mature"
                tk.Button(frame, text="Mua", font=("Arial", 10),
                          command=lambda cmd=command: self.send_buy_command(cmd)).pack(side="right", padx=5)

            tk.Button(scrollable_frame, text="Đóng", command=shop_window.destroy, font=("Arial", 12),
                      bg="#D3D3D3").pack(pady=10)

        update_shop_display()
        self.update_shop_display = update_shop_display

    def send_buy_command(self, command):
        if not self.socket:
            self.append_message("❌ Không có kết nối đến server.", "error")
            return
        try:
            self.socket.send(command.encode())
            self.append_message(f"> {command}", "system")
        except Exception as e:
            self.append_message(f"[Lỗi gửi {command}]: {e}", "error")

    def send_set_island_name(self):
        island_name = self.entry_message.get().strip()
        if not island_name:
            self.append_message("❌ Vui lòng nhập tên đảo.", "error")
            return
        if not re.match(r"^[\w\săâđêôơưàáảãạèéẻẽẹìíỉĩịòóỏõọùúủũụỳýỷỹỵĂÂĐÊÔƠƯÀÁẢÃẠÈÉẺẼẸÌÍỈĨỊÒÓỎÕỌÙÚỦŨỤỲÝỶỸỴ.,!?]{1,50}$",
                        island_name):
            self.append_message(
                "❌ Tên đảo không hợp lệ (chỉ cho phép chữ, số, khoảng trắng, và một số ký tự đặc biệt, tối đa 50 ký tự).",
                "error")
            return
        try:
            self.socket.send(f"/setislandname {island_name}".encode())
            self.append_message(f"> /setislandname {island_name}", "system")
            self.entry_message.delete(0, tk.END)
        except Exception as e:
            self.append_message(f"[Lỗi gửi /setislandname]: {e}", "error")

    def open_plant_window(self):
        if not self.socket:
            self.append_message("❌ Không có kết nối đến server.", "error")
            return
        # Gửi lệnh /balo
        try:
            self.socket.send("/balo".encode())
            self.append_message("🌱 Đã gửi lệnh lấy danh sách hạt giống.", "system")
        except Exception as e:
            self.append_message(f"[Lỗi gửi /balo]: {e}", "error")
            return

        # Chờ phản hồi từ server
        def check_inventory_and_open(attempts=5):
            if attempts == 0:
                self.append_message("❌ Không nhận được phản hồi từ /balo.", "error")
                return
            print(f"[Debug] Current inventory_seeds: {self.inventory_seeds}")  # Debug
            if hasattr(self, 'inventory_seeds') and self.inventory_seeds is not None:
                plant_window = tk.Toplevel(self.window)
                plant_window.title("Trồng cây")
                plant_window.geometry("400x500")
                plant_window.configure(bg="#f0f0f0")

                tk.Label(plant_window, text="Chọn hạt giống:", bg="#f0f0f0", font=("Arial", 12, "bold")).pack(pady=5)
                seed_var = tk.StringVar()
                seed_frame = tk.Frame(plant_window, bg="#f0f0f0")
                seed_frame.pack(fill=tk.X, padx=10, pady=5)

                has_valid_seeds = False
                for seed in self.inventory_seeds:
                    if seed["quantity"] > 0 and not seed["mature"]:
                        tk.Radiobutton(seed_frame, text=f"{seed['name']} ({seed['quantity']})", variable=seed_var,
                                       value=seed['name'], bg="#f0f0f0", font=("Arial", 11)).pack(anchor="w")
                        has_valid_seeds = True
                if not has_valid_seeds:
                    tk.Label(seed_frame, text="Không có hạt giống hợp lệ trong túi.", bg="#f0f0f0", fg="red",
                             font=("Arial", 11)).pack(anchor="w")

                tk.Label(plant_window, text="Chọn ô để trồng (1-10):", bg="#f0f0f0", font=("Arial", 12, "bold")).pack(
                    pady=5)
                slot_vars = [tk.BooleanVar() for _ in range(10)]
                slot_frame = tk.Frame(plant_window, bg="#f0f0f0")
                slot_frame.pack(fill=tk.X, padx=10, pady=5)
                for i in range(10):
                    tk.Checkbutton(slot_frame, text=f"Ô {i + 1}", variable=slot_vars[i], bg="#f0f0f0",
                                   font=("Arial", 11)).grid(row=i // 5, column=i % 5, padx=5, pady=2)

                def confirm_plant():
                    selected_seed = seed_var.get()
                    selected_slots = [str(i + 1) for i, var in enumerate(slot_vars) if var.get()]
                    if not selected_seed:
                        self.append_message("❌ Vui lòng chọn một loại hạt giống.", "error")
                        plant_window.destroy()
                        return
                    if not selected_slots:
                        self.append_message("❌ Vui lòng chọn ít nhất một ô.", "error")
                        plant_window.destroy()
                        return
                    command = f"/plant {selected_seed} {' '.join(selected_slots)}"
                    try:
                        self.socket.send(command.encode())
                        self.append_message(f"> {command}", "system")
                        plant_window.destroy()
                    except Exception as e:
                        self.append_message(f"[Lỗi gửi {command}]: {e}", "error")
                        plant_window.destroy()

                tk.Button(plant_window, text="Xác nhận", command=confirm_plant, font=("Arial", 12), bg="#32CD32",
                          activebackground="#228B22").pack(pady=10)
                tk.Button(plant_window, text="Hủy", command=plant_window.destroy, font=("Arial", 12),
                          bg="#D3D3D3").pack(pady=5)
            else:
                self.window.after(100, lambda: check_inventory_and_open(attempts - 1))

        self.window.after(100, lambda: check_inventory_and_open(5))

    def receive_messages(self):
        while True:
            try:
                message = self.socket.recv(8192).decode('utf-8')
                print(f"[Debug] Nhận: {message}")
                if not message:
                    self.append_message("[!] Server ngắt kết nối.", "error")
                    break
                if message.startswith("🏪 **Cửa hàng**"):
                    self.shop_data = {"pots": [], "seeds": [], "mature_seeds": []}
                    lines = message.split("\n")
                    current_section = None
                    for line in lines:
                        if line.startswith("📦 **Chậu**:"):
                            current_section = "pots"
                            continue
                        elif line.startswith("🌱 **Hạt giống**:"):
                            current_section = "seeds"
                            continue
                        elif line.startswith("🌳 **Cây trưởng thành**:"):
                            current_section = "mature_seeds"
                            continue
                        elif line.startswith("💡") or not line.strip():
                            continue
                        if current_section == "pots" and line:
                            match = re.match(r"(\w+)\s+\((.+?)\):\s+(.+?)\s+-\s+Giá:\s+(\d+)\s+xu", line)
                            if match:
                                self.shop_data["pots"].append({
                                    "name": match.group(1),
                                    "emoji": match.group(2),
                                    "desc": match.group(3),
                                    "price": int(match.group(4))
                                })
                        elif current_section == "seeds" and line:
                            match = re.match(r"(.+?)\s+\((.+?)\):\s+Giá\s+(\d+)\s+xu", line)
                            if match:
                                self.shop_data["seeds"].append({
                                    "name": match.group(1),
                                    "emoji": match.group(2),
                                    "price": int(match.group(3))
                                })
                        elif current_section == "mature_seeds" and line:
                            match = re.match(r"(.+?)(?:\s+(\w+))?\s+\((.+?)\):\s+Giá\s+(\d+)\s+xu", line)
                            if match:
                                self.shop_data["mature_seeds"].append({
                                    "name": match.group(1),
                                    "mutation": match.group(2) if match.group(2) else None,
                                    "emoji": match.group(3),
                                    "price": int(match.group(4))
                                })
                    if hasattr(self, "update_shop_display"):
                        self.window.after(0, self.update_shop_display)
                elif message.startswith("🎒 **Balo**") or message.startswith("🎒 Balo của"):
                    self.inventory_seeds = []
                    self.inventory_pots = []
                    lines = message.split("\n")
                    for line in lines:
                        if line.startswith("🪴 Chậu trong túi:"):
                            pot_line = line[len("🪴 Chậu trong túi: "):].strip()
                            if pot_line and pot_line != "Chưa có chậu trong túi":
                                pots = pot_line.split(", ")
                                for pot in pots:
                                    match = re.match(r"(.+?)\s*:\s*(\d+)", pot)
                                    if match:
                                        name = match.group(1).strip()
                                        quantity = int(match.group(2))
                                        self.inventory_pots.append({
                                            "name": name,
                                            "quantity": quantity
                                        })
                                        print(f"[Debug] Parsed pot: {pot}, Result: {self.inventory_pots[-1]}")
                        elif line.startswith("🌱 Hạt giống & Cây trưởng thành:"):
                            seed_line = line[len("🌱 Hạt giống & Cây trưởng thành: "):].strip()
                            if seed_line and seed_line != "Chưa có hạt giống hoặc cây trưởng thành":
                                seeds = seed_line.split(", ")
                                for seed in seeds:
                                    match = re.match(r"(.+?)(?:\s+(\w+)\s+Trưởng thành)?\s*:\s*(\d+)", seed)
                                    if match:
                                        name = match.group(1).strip()
                                        mutation = match.group(2) if match.group(2) else None
                                        quantity = int(match.group(3))
                                        mature = bool(mutation or "Trưởng thành" in seed)
                                        self.inventory_seeds.append({
                                            "name": name,
                                            "quantity": quantity,
                                            "mature": mature,
                                            "mutation": mutation
                                        })
                                        print(f"[Debug] Parsed seed: {seed}, Result: {self.inventory_seeds[-1]}")
                    print(f"[Debug] Final inventory_pots after /balo: {self.inventory_pots}")
                    print(f"[Debug] Final inventory_seeds after /balo: {self.inventory_seeds}")

                else:
                    tag = "chat" if message.startswith("💬") else "tips" if message.startswith(
                        "📜") else "status" if message.startswith("📍") else "system"
                    if tag == "status":
                        for label in self.farm_labels:
                            label.destroy()
                        self.farm_labels.clear()
                        lines = message.split("\n")
                        for line in lines:
                            if line.startswith("📍 ☁️ Thời tiết:"):
                                self.weather_label.config(text=line)
                            elif line.startswith("🏝️ Đảo:") or line.startswith("🏝️ Đảo của"):
                                self.island_label.config(text=line)
                            elif line.startswith("💵 Tiền:"):
                                self.money_label.config(text=line)
                            elif line.startswith("🏢 Tầng:") or line.startswith("📍 Đang ở tầng:"):
                                self.stage_label.config(text=line)
                            elif line.startswith("🤝 Trạng thái:"):
                                self.coop_label.config(text=line)
                            elif line.startswith("🪴 Chậu trong túi:"):
                                self.pots_label.config(text=line)
                            elif line.startswith("🌱 Hạt giống & Cây trưởng thành:"):
                                self.seeds_label.config(text=line)
                                # Cập nhật inventory_seeds từ trạng thái
                                seed_line = line[len("🌱 Hạt giống & Cây trưởng thành: "):].strip()
                                if seed_line and seed_line != "Chưa có hạt giống hoặc cây trưởng thành":
                                    seeds = seed_line.split(", ")
                                    for seed in seeds:
                                        match = re.match(r"(.+?)(?:\s+(\w+)\s+Trưởng thành)?\s*:\s*(\d+)", seed)
                                        if match:
                                            name = match.group(1).strip()
                                            mutation = match.group(2) if match.group(2) else None
                                            quantity = int(match.group(3))
                                            mature = bool(mutation or "Trưởng thành" in seed)
                                            self.inventory_seeds.append({
                                                "name": name,
                                                "quantity": quantity,
                                                "mature": mature,
                                                "mutation": mutation
                                            })
                            elif line.startswith("🎭 Nông trại:") or line.startswith("☁️"):
                                farm_label = tk.Label(self.status_frame, text=line.lstrip(), bg="#f0f0f0", fg="#000000",
                                                      font=("Arial", 11), wraplength=630)
                                farm_label.pack(anchor="w", pady=1)
                                self.farm_labels.append(farm_label)
                    self.append_message(message, tag)
            except Exception as e:
                self.append_message(f"[Kết nối đã bị mất]: {e}", "error")
                if self.socket:
                    try:
                        self.socket.close()
                    except:
                        pass
                    self.socket = None
                    self.window.after(0, self.show_reconnect)
                break

    def append_message(self, message, tag="system"):
        self.chat_area.configure(state="normal")
        self.chat_area.insert(tk.END, message + "\n", tag)
        self.chat_area.configure(state="disabled")
        self.chat_area.see(tk.END)

    def show_reconnect(self):
        self.clear_window()
        tk.Label(self.window, text="Mất kết nối với server!", bg="#f0f0f0", fg="red", font=("Arial", 12)).pack(pady=10)
        tk.Button(self.window, text="Kết nối lại", command=self.create_login_ui, font=("Arial", 12)).pack(pady=10)

    def on_arrow_up(self, event):
        if self.command_history:
            if self.history_index > 0:
                self.history_index -= 1
            self.entry_message.delete(0, tk.END)
            self.entry_message.insert(0, self.command_history[self.history_index])

    def on_arrow_down(self, event):
        if self.command_history:
            if self.history_index < len(self.command_history) - 1:
                self.history_index += 1
            else:
                self.history_index = len(self.command_history)
                self.entry_message.delete(0, tk.END)
                return
            self.entry_message.delete(0, tk.END)
            self.entry_message.insert(0, self.command_history[self.history_index])

    def open_place_pot_window(self):
        if not self.socket:
            self.append_message("❌ Không có kết nối đến server.", "error")
            return
        # Gửi lệnh /balo để lấy danh sách chậu
        try:
            self.socket.send("/balo".encode())
            self.append_message("🪴 Đã gửi lệnh lấy danh sách chậu.", "system")
        except Exception as e:
            self.append_message(f"[Lỗi gửi /balo]: {e}", "error")
            return

        # Chờ phản hồi từ server
        def check_inventory_and_open(attempts=15):  # Tăng số lần thử lên 15
            if attempts == 0:
                self.append_message("❌ Không nhận được phản hồi từ /balo.", "error")
                # Tạo giao diện ngay cả khi không nhận được phản hồi
                create_place_pot_window([])
                return
            print(f"[Debug] Current inventory_pots: {self.inventory_pots}, Attempts left: {attempts}")  # Debug
            if hasattr(self, 'inventory_pots') and self.inventory_pots is not None:
                create_place_pot_window(self.inventory_pots)
            else:
                self.window.after(300, lambda: check_inventory_and_open(attempts - 1))  # Tăng thời gian chờ lên 300ms

        def create_place_pot_window(pots):
            print("[Debug] Bắt đầu tạo giao diện Đặt chậu")  # Debug
            place_pot_window = tk.Toplevel(self.window)
            place_pot_window.title("Đặt chậu")
            place_pot_window.geometry("400x500")
            place_pot_window.configure(bg="#f0f0f0")

            # Phần chọn chậu
            tk.Label(place_pot_window, text="Chọn chậu:", bg="#f0f0f0", font=("Arial", 12, "bold")).pack(pady=5)
            pot_var = tk.StringVar()
            pot_frame = tk.Frame(place_pot_window, bg="#f0f0f0")
            pot_frame.pack(fill=tk.X, padx=10, pady=5)

            has_valid_pots = False
            for pot in pots:
                if pot.get("quantity", 0) > 0:
                    tk.Radiobutton(pot_frame, text=f"{pot['name']} ({pot['quantity']})", variable=pot_var,
                                   value=pot['name'], bg="#f0f0f0", font=("Arial", 11)).pack(anchor="w")
                    has_valid_pots = True
                    print(f"[Debug] Thêm chậu: {pot['name']}")  # Debug
            if not has_valid_pots:
                tk.Label(pot_frame, text="Không có chậu hợp lệ trong túi.", bg="#f0f0f0", fg="red",
                         font=("Arial", 11)).pack(anchor="w")
                print("[Debug] Không có chậu hợp lệ")  # Debug

            # Phần chọn ô
            print("[Debug] Bắt đầu tạo checkbox cho ô")  # Debug
            tk.Label(place_pot_window, text="Chọn ô để đặt (1-10):", bg="#f0f0f0", font=("Arial", 12, "bold")).pack(pady=5)
            slot_vars = [tk.BooleanVar() for _ in range(10)]
            slot_frame = tk.Frame(place_pot_window, bg="#f0f0f0")
            slot_frame.pack(fill=tk.X, padx=10, pady=5)
            for i in range(10):
                tk.Checkbutton(slot_frame, text=f"Ô {i + 1}", variable=slot_vars[i], bg="#f0f0f0",
                               font=("Arial", 11), selectcolor="#ADD8E6").grid(row=i // 5, column=i % 5, padx=5, pady=2)
                print(f"[Debug] Thêm checkbox Ô {i + 1}")  # Debug

            # Hàm xác nhận
            def confirm_place_pot():
                selected_pot = pot_var.get()
                selected_slots = [str(i + 1) for i, var in enumerate(slot_vars) if var.get()]
                print(f"[Debug] Chậu được chọn: {selected_pot}, Ô được chọn: {selected_slots}")  # Debug
                if not selected_pot:
                    self.append_message("❌ Vui lòng chọn một loại chậu.", "error")
                    place_pot_window.destroy()
                    return
                if not selected_slots:
                    self.append_message("❌ Vui lòng chọn ít ít một ô.", "error")
                    place_pot_window.destroy()
                    return
                command = f"/datchau {selected_pot} {' '.join(selected_slots)}"
                try:
                    self.socket.send(command.encode())
                    self.append_message(f"> {command}", "system")
                    place_pot_window.destroy()
                except Exception as e:
                    self.append_message(f"[Lỗi gửi {command}]: {e}", "error")
                    place_pot_window.destroy()

            # Nút điều khiển
            print("[Debug] Thêm nút Xác nhận và Hủy")  # Debug
            tk.Button(place_pot_window, text="Xác nhận", command=confirm_place_pot, font=("Arial", 12),
                      bg="#FFA500", activebackground="#FF8C00").pack(pady=10)
            tk.Button(place_pot_window, text="Hủy", command=place_pot_window.destroy, font=("Arial", 12),
                      bg="#D3D3D3").pack(pady=5)
            print("[Debug] Hoàn tất tạo giao diện Đặt chậu")  # Debug

        self.window.after(300, lambda: check_inventory_and_open(15))  # Tăng thời gian chờ ban đầu

    def send_place_pot(self):
        if not self.socket:
            self.append_message("❌ Không có kết nối đến server.", "error")
            return
        try:
            self.socket.send("/datchau".encode())
            self.append_message("🪴 Đã gửi lệnh đặt chậu.", "system")
        except Exception as e:
            self.append_message(f"[Lỗi gửi /datchau]: {e}", "error")

if __name__ == "__main__":
    FarmClient()