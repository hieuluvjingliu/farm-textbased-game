import socket
import threading
import sqlite3
import tkinter as tk
from tkinter import scrolledtext
import random
import time
import re
from datetime import datetime
from wcwidth import wcswidth
import threading
# === Thiết lập cơ bản ===
HOST = '0.0.0.0'
PORT = 5000

# === Kết nối DB ===
conn = sqlite3.connect("farm_game_username.db", check_same_thread=False)
cur = conn.cursor()

import threading

# Khai báo lock toàn cục
lock = threading.Lock()

# ... (phần còn lại của mã, ví dụ: clients, update_gui, send_to_client, v.v.)
# Kiểm tra và tạo bảng nếu chưa tồn tại
cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    money INTEGER DEFAULT 1000,
    stages INTEGER DEFAULT 0,
    current_stage INTEGER DEFAULT 0,
    island_name TEXT DEFAULT 'Đảo chưa đặt tên'
)
""")
cur.execute("""
CREATE TABLE IF NOT EXISTS user_pots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    pot_name TEXT,
    stage INTEGER DEFAULT 0,
    FOREIGN KEY(username) REFERENCES users(username)
)
""")
cur.execute("""
CREATE TABLE IF NOT EXISTS placed_pots (
    username TEXT,
    pot_name TEXT,
    stage INTEGER,
    slot INTEGER,
    plant_type TEXT,
    plant_growth INTEGER DEFAULT 0,
    plant_time INTEGER DEFAULT 0,
    mutation_level TEXT DEFAULT NULL,
    FOREIGN KEY(username) REFERENCES users(username)
)
""")
cur.execute("""
CREATE TABLE IF NOT EXISTS user_seeds (
    username TEXT,
    plant_type TEXT,
    quantity INTEGER DEFAULT 0,
    mature INTEGER DEFAULT 0,
    mutation_level TEXT DEFAULT NULL,
    FOREIGN KEY(username) REFERENCES users(username)
)
""")
cur.execute("""
CREATE TABLE IF NOT EXISTS admins (
    username TEXT PRIMARY KEY
)
""")
cur.execute("""
CREATE TABLE IF NOT EXISTS coop_invitations (
    inviter TEXT,
    invitee TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (inviter, invitee),
    FOREIGN KEY(inviter) REFERENCES users(username),
    FOREIGN KEY(invitee) REFERENCES users(username)
)
""")
conn.commit()

# Thêm admin mặc định
cur.execute("""
    CREATE TABLE IF NOT EXISTS admins (
        username TEXT PRIMARY KEY
    )
""")
cur.execute("""
CREATE TABLE IF NOT EXISTS coop_invitations (
    inviter TEXT,
    invitee TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (inviter, invitee),
    FOREIGN KEY(inviter) REFERENCES users(username),
    FOREIGN KEY(invitee) REFERENCES users(username)
)
""")
conn.commit()
# Thêm admin mặc định
cur.execute("INSERT OR IGNORE INTO admins (username) VALUES (?)", ("admin",))
conn.commit()

# Kiểm tra và thêm cột thiếu
try:
    cur.execute("SELECT mutation_level FROM user_seeds LIMIT 1")
except sqlite3.OperationalError:
    cur.execute("ALTER TABLE user_seeds ADD COLUMN mutation_level TEXT DEFAULT NULL")
try:
    cur.execute("SELECT stage FROM user_pots LIMIT 1")
except sqlite3.OperationalError:
    cur.execute("ALTER TABLE user_pots ADD COLUMN stage INTEGER DEFAULT 0")
try:
    cur.execute("SELECT plant_time FROM placed_pots LIMIT 1")
except sqlite3.OperationalError:
    cur.execute("ALTER TABLE placed_pots ADD COLUMN plant_time INTEGER DEFAULT 0")
try:
    cur.execute("SELECT quantity FROM user_seeds LIMIT 1")
except sqlite3.OperationalError:
    cur.execute("ALTER TABLE user_seeds ADD COLUMN quantity INTEGER DEFAULT 0")
try:
    cur.execute("SELECT mature FROM user_seeds LIMIT 1")
except sqlite3.OperationalError:
    cur.execute("ALTER TABLE user_seeds ADD COLUMN mature INTEGER DEFAULT 0")
try:
    cur.execute("SELECT id FROM user_pots LIMIT 1")
except sqlite3.OperationalError:
    cur.execute(
        "CREATE TABLE temp_user_pots (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, pot_name TEXT, stage INTEGER DEFAULT 0)")
    cur.execute(
        "INSERT INTO temp_user_pots (username, pot_name, stage) SELECT username, pot_name, stage FROM user_pots")
    cur.execute("DROP TABLE user_pots")
    cur.execute("ALTER TABLE temp_user_pots RENAME TO user_pots")
try:
    cur.execute("SELECT mutation_level FROM placed_pots LIMIT 1")
except sqlite3.OperationalError:
    cur.execute("ALTER TABLE placed_pots ADD COLUMN mutation_level TEXT DEFAULT NULL")

# Danh sách các nguyên tố cây trồng
plant_types = [
    "Water", "Fire", "Earth", "Wind", "Steam", "Mud", "Smoke", "Wave", "Dust", "Lava",
    "Geyser", "Brick", "Wall", "House", "Fireplace", "Flooded House", "Blown House", "Stone",
    "Sand", "Glass", "Bottle", "Message", "Paper Plane", "Crash", "Mountain", "River", "Lake",
    "Ocean", "Island", "Volcano", "Eruption", "Ash", "Soap", "Bubble", "Balloon", "Kite",
    "Glider", "Plane", "Airport", "City", "Fire Station", "Plumbing", "Windmill", "Construction",
    "Building", "Leak", "Fire Alarm", "Skyscraper", "Office", "Email", "Internet", "Social Media",
    "Digital Heat", "Streaming", "Online Community", "Networking", "AI Interface", "Live Stream",
    "Viral Video", "Meme", "Viral Trend", "Water Meme", "Whisper", "Graffiti", "Stream Platform",
    "Internet Culture", "Firewall", "Cybersecurity", "Antivirus", "Protected Network", "Info System",
    "Data Platform", "Cloud Service", "SaaS", "Productivity Tool", "Remote Work", "Virtual Assistant",
    "Personal AI", "Interactive Bot", "Game AI", "AI Opponent", "Competitive Match", "Esports",
    "Tournament", "Spectator", "Online Audience", "Internet Fandom", "Fanbase", "Online Star",
    "Scandal", "Controversy", "Viral Controversy", "Media Storm", "Breaking News", "Rumor",
    "Suspicion", "Thriller Plot", "Web Series", "Fandom", "Idol", "Brand Ambassador", "Ad Campaign",
    "Influencer Marketing", "Sponsored Post", "Viral Sponsorship", "Trend Trigger", "Launch Event",
    "Fireworks", "Celebration", "Feast", "Gathering", "Concert", "Excitement", "Buzz",
    "Internet Meme", "Online Debate", "Message Board", "Participant", "Chat Interaction",
    "Reaction GIF", "Trend Spread", "Blaze", "Wildfire", "Ash Cloud", "Acid Rain", "Corrosion",
    "Rust", "Decay", "Desert", "Sandstorm", "Dune Shift", "Oasis", "Palm Tree", "Date Fruit",
    "Fruit Drink", "Smoothie", "Refreshment", "Fertile Land", "Agriculture", "Irrigation",
    "Crop", "Food", "Dish", "Banquet", "Fair", "Entertainment", "Virtual Reality", "VR Game",
    "Immersive Play", "Adaptive Game", "Personalized Game", "Gaming Ecosystem", "Gaming Industry",
    "Economy", "Civilization", "Innovation", "Tech Revolution", "Next-Gen Society", "Singularity",
    "Transcendence", "Enlightenment", "Consciousness", "Multiverse", "Alternate Reality",
    "Fiction", "Myth", "Folklore", "Tradition", "Heritage", "Nation", "Symbol", "Patriotism",
    "Passion", "Masterpiece", "Classic", "Novel", "Bookworm", "Archive", "Archive Lore",
    "Knowledge Base", "Wiki", "Collaborator", "Collective", "Reform", "Legislation", "Governance",
    "Republic", "Country", "Treaty", "Peace", "Harmony", "Anthem", "Rally", "Movement",
    "Revolution Legacy", "Monument", "Colosseum", "Spectacle", "Holiday", "Bonfire", "Campfire Tale"
]

# Chuẩn hóa plant_type trong DB
plant_type_mapping = {pt: pt for pt in plant_types}
plant_type_mapping.update({
    "Nước": "Water", "Nuoc": "Water",
    "Lửa": "Fire", "Lua": "Fire",
    "Gió": "Wind", "Gio": "Wind",
    "Đất": "Earth", "Dat": "Earth",
    "Hơi nước": "Steam", "Hoinuoc": "Steam",
    "Khói": "Smoke", "Khoi": "Smoke",
    "Sóng": "Wave", "Song": "Wave",
    "Bụi": "Dust", "Bui": "Dust"

})

for old_type, new_type in plant_type_mapping.items():
    cur.execute("UPDATE placed_pots SET plant_type=? WHERE plant_type=?", (new_type, old_type))
    cur.execute("UPDATE user_seeds SET plant_type=? WHERE plant_type=?", (new_type, old_type))
conn.commit()

# Emoji cho các nguyên tố
plant_emojis = {pt: ["🌱", "🌿", "🌳"] for pt in plant_types}
plant_emojis.update({
    "Water": ["💧", "🌊", "🌧️"],
    "Fire": ["🔥", "🧨", "💥"],
    "Wind": ["💨", "🌬️", "🌪️"],
    "Earth": ["🌍", "⛰️", "🏞️"],
    "Steam": ["💨", "🌫️", "☁️"],
    "Mud": ["💦", "🟤", "🌾"],
    "Smoke": ["💨", "🌫️", "🌬️"],
    "Wave": ["🌊", "🏄", "🌬️"],
    "Dust": ["🏜️", "💨", "🌪️"],
    "Lava": ["🌋", "🔥", "🪨"],
    "Geyser": ["💨", "🌊", "♨️"],
    "Brick": ["🧱", "🏛️", "🛠️"],
    "Wall": ["🧱", "🏯", "🏰"],
    "House": ["🏠", "🏡", "🏘️"],
    "Fireplace": ["🔥", "🏠", "🪵"],
    "Flooded House": ["🏠", "💧", "🌊"],
    "Blown House": ["🏠", "💨", "🌪️"],
    "Stone": ["🪨", "⛰️", "🛡️"],
    "Sand": ["🏜️", "⏳", "🏖️"],
    "Glass": ["🥛", "🪞", "🔍"],
    "Bottle": ["🍾", "🍼", "🥂"],
    "Message": ["📜", "💬", "✉️"],
    "Paper Plane": ["✈️", "📄", "🛫"],
    "Crash": ["💥", "🛬", "🔥"],
    "Mountain": ["⛰️", "🏔️", "🗻"],
    "River": ["🏞️", "🌊", "🛶"],
    "Lake": ["💧", "🌅", "🏞️"],
    "Ocean": ["🌊", "🌊", "🏝️"],
    "Island": ["🏝️", "🌴", "🏖️"],
    "Volcano": ["🌋", "🔥", "🪨"],
    "Eruption": ["🌋", "💥", "🔥"],
    "Ash": ["🌫️", "🔥", "🛡️"],
    "Soap": ["🧼", "🫧", "🧽"],
    "Bubble": ["🫧", "🌬️", "🎈"],
    "Balloon": ["🎈", "🎉", "🎈"],
    "Kite": ["🪁", "🌬️", "🎏"],
    "Glider": ["🪂", "✈️", "🛩️"],
    "Plane": ["✈️", "🛫", "🛬"],
    "Airport": ["🛩️", "🏙️", "🛬"],
    "City": ["🏙️", "🌆", "🏯"],
    "Fire Station": ["🚒", "🔥", "🏢"],
    "Plumbing": ["🚽", "💧", "🛠️"],
    "Windmill": ["🌬️", "🏚️", "⚙️"],
    "Construction": ["🏗️", "🛠️", "🚧"],
    "Building": ["🏢", "🏬", "🏠"],
    "Leak": ["💧", "🚽", "🛠️"],
    "Fire Alarm": ["🚨", "🔥", "🔔"],
    "Skyscraper": ["🏙️", "🏢", "🌆"],
    "Office": ["🏢", "💼", "🖥️"],
    "Email": ["✉️", "📧", "💻"],
    "Internet": ["🌐", "💻", "📱"],
    "Social Media": ["📱", "🌐", "👥"],
    "Digital Heat": ["🔥", "💻", "⚡️"],
    "Streaming": ["📺", "🌐", "🎥"],
    "Online Community": ["👥", "🌐", "💬"],
    "Networking": ["🌐", "🤝", "💼"],
    "AI Interface": ["🤖", "🖥️", "🧠"],
    "Live Stream": ["📹", "🌐", "🎮"],
    "Viral Video": ["🎥", "🔥", "📈"],
    "Meme": ["😂", "📱", "🌐"],
    "Viral Trend": ["🔥", "📈", "🌟"],
    "Water Meme": ["💧", "😂", "📱"],
    "Whisper": ["🗣️", "💬", "🤫"],
    "Graffiti": ["🎨", "🖌️", "🏚️"],
    "Stream Platform": ["📺", "🎮", "🌐"],
    "Internet Culture": ["🌐", "😂", "📱"],
    "Firewall": ["🛡️", "🌐", "🔒"],
    "Cybersecurity": ["🔒", "🛡️", "💻"],
    "Antivirus": ["🛡️", "🦠", "💻"],
    "Protected Network": ["🌐", "🔒", "🛡️"],
    "Info System": ["💾", "🌐", "🖥️"],
    "Data Platform": ["💽", "🌐", "📊"],
    "Cloud Service": ["☁️", "🌐", "💻"],
    "SaaS": ["💻", "🌐", "📈"],
    "Productivity Tool": ["🛠️", "💼", "📱"],
    "Remote Work": ["🏠", "💻", "🌐"],
    "Virtual Assistant": ["🤖", "📱", "🧠"],
    "Personal AI": ["🤖", "🧠", "👤"],
    "Interactive Bot": ["🤖", "💬", "🌐"],
    "Game AI": ["🎮", "🤖", "🧠"],
    "AI Opponent": ["🤖", "🎮", "⚔️"],
    "Competitive Match": ["🎮", "⚔️", "🏆"],
    "Esports": ["🎮", "🏆", "📺"],
    "Tournament": ["🏆", "🎮", "👥"],
    "Spectator": ["👥", "👀", "🎮"],
    "Online Audience": ["👥", "🌐", "📺"],
    "Internet Fandom": ["🌐", "👥", "🌟"],
    "Fanbase": ["👥", "🌟", "🎤"],
    "Online Star": ["🌟", "📱", "🎤"],
    "Scandal": ["📰", "😱", "🖤"],
    "Controversy": ["😤", "🗣️", "🔥"],
    "Viral Controversy": ["🔥", "📈", "🗣️"],
    "Media Storm": ["📰", "🌪️", "📺"],
    "Breaking News": ["📰", "📺", "🚨"],
    "Rumor": ["🗣️", "💬", "🤔"],
    "Suspicion": ["🕵️", "🤔", "❓"],
    "Thriller Plot": ["📖", "🕵️", "🎬"],
    "Web Series": ["📺", "🎬", "🌐"],
    "Fandom": ["👥", "🌟", "🎤"],
    "Idol": ["🌟", "🎤", "👤"],
    "Brand Ambassador": ["🌟", "🤝", "📈"],
    "Ad Campaign": ["📣", "📈", "🌐"],
    "Influencer Marketing": ["📱", "🌟", "📈"],
    "Sponsored Post": ["📱", "💰", "🌟"],
    "Viral Sponsorship": ["🔥", "📈", "💰"],
    "Trend Trigger": ["📈", "🌟", "🔥"],
    "Launch Event": ["🎉", "📣", "🌟"],
    "Fireworks": ["🎆", "🔥", "🌌"],
    "Celebration": ["🎉", "🎊", "🥳"],
    "Feast": ["🍽️", "🥂", "🎉"],
    "Gathering": ["👥", "🏡", "🎉"],
    "Concert": ["🎤", "🎶", "👥"],
    "Excitement": ["🎉", "🔥", "😄"],
    "Buzz": ["📣", "🔥", "🌐"],
    "Internet Meme": ["😂", "🌐", "📱"],
    "Online Debate": ["🗣️", "🌐", "📝"],
    "Message Board": ["💬", "📜", "🌐"],
    "Participant": ["👤", "🤝", "💬"],
    "Chat Interaction": ["💬", "📱", "🌐"],
    "Reaction GIF": ["😂", "📱", "🎬"],
    "Trend Spread": ["📈", "🌐", "🔥"],
    "Blaze": ["🔥", "💥", "🌪️"],
    "Wildfire": ["🔥", "🌲", "💥"],
    "Ash Cloud": ["🌫️", "🔥", "☁️"],
    "Acid Rain": ["🌧️", "☣️", "🛢️"],
    "Corrosion": ["🛢️", "⚙️", "🧪"],
    "Rust": ["🧪", "⚙️", "🟤"],
    "Decay": ["🕰️", "🧪", "🏚️"],
    "Desert": ["🏜️", "🌞", "🏜️"],
    "Sandstorm": ["🌪️", "🏜️", "💨"],
    "Dune Shift": ["🏜️", "🌬️", "⏳"],
    "Oasis": ["🏝️", "💧", "🌴"],
    "Palm Tree": ["🌴", "🌳", "🏝️"],
    "Date Fruit": ["🍇", "🌴", "🍎"],
    "Fruit Drink": ["🥤", "🍎", "🧃"],
    "Smoothie": ["🥤", "🍓", "🧊"],
    "Refreshment": ["🥤", "❄️", "😊"],
    "Fertile Land": ["🌾", "🌍", "🌱"],
    "Agriculture": ["🚜", "🌾", "🌱"],
    "Irrigation": ["💧", "🌾", "🚿"],
    "Crop": ["🌾", "🌱", "🍂"],
    "Food": ["🍽️", "🥕", "🍎"],
    "Dish": ["🍽️", "🍲", "🥗"],
    "Banquet": ["🍽️", "🎉", "🥂"],
    "Fair": ["🎡", "🎉", "🏁"],
    "Entertainment": ["🎭", "🎬", "🎮"],
    "Virtual Reality": ["🕶️", "🌐", "🎮"],
    "VR Game": ["🎮", "🕶️", "🌌"],
    "Immersive Play": ["🎮", "🧠", "🌌"],
    "Adaptive Game": ["🎮", "🤖", "🧠"],
    "Personalized Game": ["🎮", "👤", "🌟"],
    "Gaming Ecosystem": ["🎮", "🌐", "📈"],
    "Gaming Industry": ["🎮", "💼", "📈"],
    "Economy": ["💰", "📈", "🏦"],
    "Civilization": ["🏰", "🏙️", "🌍"],
    "Innovation": ["💡", "🛠️", "🌟"],
    "Tech Revolution": ["🚀", "🌐", "💻"],
    "Next-Gen Society": ["🌌", "🤖", "🏙️"],
    "Singularity": ["🧠", "🌌", "♾️"],
    "Transcendence": ["✨", "🧘", "🌌"],
    "Enlightenment": ["💡", "🧘", "✨"],
    "Consciousness": ["🧠", "✨", "🌌"],
    "Multiverse": ["🌌", "♾️", "🪐"],
    "Alternate Reality": ["🌌", "🌀", "📖"],
    "Fiction": ["📖", "🦄", "🌌"],
    "Myth": ["📜", "🦁", "🌟"],
    "Folklore": ["📖", "🏞️", "📜"],
    "Tradition": ["🎎", "🏛️", "📜"],
    "Heritage": ["🏛️", "📜", "🌍"],
    "Nation": ["🌍", "🏳️", "👥"],
    "Symbol": ["🏳️", "🌟", "🛡️"],
    "Patriotism": ["🏳️", "❤️", "🌍"],
    "Passion": ["❤️", "🔥", "🌹"],
    "Masterpiece": ["🖼️", "🎨", "🌟"],
    "Classic": ["📜", "🖼️", "🎻"],
    "Novel": ["📖", "✍️", "📚"],
    "Bookworm": ["📚", "👓", "📖"],
    "Archive": ["📚", "🏛️", "📜"],
    "Archive Lore": ["📜", "🏛️", "📖"],
    "Knowledge Base": ["📚", "🧠", "💾"],
    "Wiki": ["🌐", "📚", "🧠"],
    "Collaborator": ["🤝", "👥", "🛠️"],
    "Collective": ["👥", "🌐", "🤝"],
    "Reform": ["📜", "✊", "🌟"],
    "Legislation": ["📜", "⚖️", "🏛️"],
    "Governance": ["🏛️", "⚖️", "📜"],
    "Republic": ["🏛️", "🗳️", "🌍"],
    "Country": ["🌍", "🏳️", "🗺️"],
    "Treaty": ["📜", "🤝", "🌍"],
    "Peace": ["🕊️", "🌍", "🤝"],
    "Harmony": ["☯️", "🎶", "🌍"],
    "Anthem": ["🎶", "🏳️", "🌍"],
    "Rally": ["✊", "👥", "🏳️"],
    "Movement": ["✊", "🌍", "📣"],
    "Revolution Legacy": ["📜", "🌍", "🌟"],
    "Monument": ["🗿", "🏛️", "🌍"],
    "Colosseum": ["🏛️", "🦁", "🎭"],
    "Spectacle": ["🎭", "🌟", "👥"],
    "Holiday": ["🎉", "🏖️", "🎄"],
    "Bonfire": ["🔥", "🪵", "🌌"],
    "Campfire Tale": ["🔥", "📖", "🌌"]
})

# Bảng công thức lai tạo
breeding_recipes = {
    ("Fire", "Water"): "Steam",
    ("Earth", "Water"): "Mud",
    ("Lava", "Dust"):"Glass",
    ("Fire", "Wind"): "Smoke",
    ("Water", "Wind"): "Wave",
    ("Earth", "Wind"): "Dust",
    ("Earth", "Fire"): "Lava",
    ("Steam", "Earth"): "Geyser",
    ("Mud", "Fire"): "Brick",
    ("Brick", "Brick"): "Wall",
    ("Wall", "Wall"): "House",
    ("House", "Fire"): "Fireplace",
    ("House", "Water"): "Flooded House",
    ("House", "Wind"): "Blown House",
    ("Lava", "Water"): "Stone",
    ("Stone", "Wind"): "Sand",
    ("Sand", "Fire"): "Glass",
    ("Glass", "Water"): "Bottle",
    ("Bottle", "Smoke"): "Message",
    ("Message", "Wind"): "Paper Plane",
    ("Paper Plane", "Fire"): "Crash",
    ("Stone", "Stone"): "Mountain",
    ("Mountain", "Water"): "River",
    ("River", "River"): "Lake",
    ("Lake", "Water"): "Ocean",
    ("Ocean", "Wind"): "Wave",
    ("Ocean", "Fire"): "Steam",
    ("Ocean", "Earth"): "Island",
    ("Island", "Smoke"): "Volcano",
    ("Volcano", "Mountain"): "Eruption",
    ("Eruption", "Dust"): "Ash",
    ("Ash", "Water"): "Soap",
    ("Soap", "Wind"): "Bubble",
    ("Bubble", "Fire"): "Balloon",
    ("Balloon", "Wind"): "Kite",
    ("Kite", "Mountain"): "Glider",
    ("Glider", "Steam"): "Plane",
    ("Plane", "Island"): "Airport",
    ("Airport", "River"): "City",
    ("City", "Fire"): "Fire Station",
    ("City", "Water"): "Plumbing",
    ("City", "Wind"): "Windmill",
    ("City", "Earth"): "Construction",
    ("Construction", "Brick"): "Building",
    ("Building", "Water"): "Leak",
    ("Building", "Fire"): "Fire Alarm",
    ("Building", "Smoke"): "Skyscraper",
    ("Skyscraper", "Glass"): "Office",
    ("Office", "Paper Plane"): "Email",
    ("Email", "Message"): "Internet",
    ("Internet", "Bubble"): "Social Media",
    ("Internet", "Fire"): "Digital Heat",
    ("Internet", "Water"): "Streaming",
    ("Social Media", "Water"): "Online Community",
    ("Social Media", "Internet"): "Networking",
    ("Networking", "Digital Heat"): "AI Interface",
    ("Networking", "Streaming"): "Live Stream",
    ("Live Stream", "Internet"): "Viral Video",
    ("Viral Video", "Social Media"): "Meme",
    ("Meme", "Fire"): "Viral Trend",
    ("Meme", "Water"): "Water Meme",
    ("Meme", "Wind"): "Whisper",
    ("Meme", "Earth"): "Graffiti",
    ("Live Stream", "Live Stream"): "Stream Platform",
    ("Meme", "Meme"): "Internet Culture",
    ("Digital Heat", "Smoke"): "Firewall",
    ("Firewall", "Firewall"): "Cybersecurity",
    ("Cybersecurity", "AI Interface"): "Antivirus",
    ("Antivirus", "Internet"): "Protected Network",
    ("Protected Network", "Streaming"): "Info System",
    ("Info System", "Networking"): "Data Platform",
    ("Data Platform", "Data Platform"): "Cloud Service",
    ("Cloud Service", "Internet"): "SaaS",
    ("SaaS", "SaaS"): "Productivity Tool",
    ("Productivity Tool", "Internet"): "Remote Work",
    ("Remote Work", "AI Interface"): "Virtual Assistant",
    ("Virtual Assistant", "Virtual Assistant"): "Personal AI",
    ("Personal AI", "Streaming"): "Interactive Bot",
    ("Interactive Bot", "Interactive Bot"): "Game AI",
    ("Game AI", "Game AI"): "AI Opponent",
    ("AI Opponent", "AI Opponent"): "Competitive Match",
    ("Competitive Match", "Streaming"): "Esports",
    ("Esports", "Live Stream"): "Tournament",
    ("Tournament", "Tournament"): "Spectator",
    ("Spectator", "Internet"): "Online Audience",
    ("Online Audience", "Meme"): "Internet Fandom",
    ("Internet Fandom", "Internet Fandom"): "Fanbase",
    ("Fanbase", "Social Media"): "Online Star",
    ("Online Star", "Online Star"): "Scandal",
    ("Scandal", "Scandal"): "Controversy",
    ("Controversy", "Social Media"): "Viral Controversy",
    ("Viral Controversy", "Internet"): "Media Storm",
    ("Media Storm", "Media Storm"): "Breaking News",
    ("Breaking News", "Smoke"): "Rumor",
    ("Rumor", "Whisper"): "Suspicion",
    ("Suspicion", "Suspicion"): "Thriller Plot",
    ("Thriller Plot", "Streaming"): "Web Series",
    ("Web Series", "Fanbase"): "Fandom",
    ("Fandom", "Fandom"): "Idol",
    ("Idol", "Idol"): "Brand Ambassador",
    ("Brand Ambassador", "Brand Ambassador"): "Ad Campaign",
    ("Ad Campaign", "Internet"): "Influencer Marketing",
    ("Influencer Marketing", "Influencer Marketing"): "Sponsored Post",
    ("Sponsored Post", "Meme"): "Viral Sponsorship",
    ("Viral Sponsorship", "Social Media"): "Trend Trigger",
    ("Trend Trigger", "Live Stream"): "Launch Event",
    ("Launch Event", "Fire"): "Fireworks",
    ("Fireworks", "Fireworks"): "Celebration",
    ("Celebration", "Food"): "Feast",
    ("Feast", "Feast"): "Gathering",
    ("Gathering", "Gathering"): "Concert",
    ("Concert", "Concert"): "Excitement",
    ("Excitement", "Internet"): "Buzz",
    ("Buzz", "Meme"): "Internet Meme",
    ("Internet Meme", "Scandal"): "Online Debate",
    ("Online Debate", "Online Debate"): "Message Board",
    ("Message Board", "Message Board"): "Participant",
    ("Participant", "Streaming"): "Chat Interaction",
    ("Chat Interaction", "Meme"): "Reaction GIF",
    ("Reaction GIF", "Social Media"): "Trend Spread",
    ("Trend Spread", "Fire"): "Blaze",
    ("Blaze", "Wind"): "Wildfire",
    ("Wildfire", "Smoke"): "Ash Cloud",
    ("Ash Cloud", "Ash Cloud"): "Acid Rain",
    ("Acid Rain", "Earth"): "Corrosion",
    ("Corrosion", "Corrosion"): "Rust",
    ("Rust", "Rust"): "Decay",
    ("Decay", "Dust"): "Desert",
    ("Desert", "Wind"): "Sandstorm",
    ("Sandstorm", "Sandstorm"): "Dune Shift",
    ("Dune Shift", "Water"): "Oasis",
    ("Oasis", "Oasis"): "Palm Tree",
    ("Palm Tree", "Palm Tree"): "Date Fruit",
    ("Date Fruit", "Water"): "Fruit Drink",
    ("Fruit Drink", "Fruit Drink"): "Smoothie",
    ("Smoothie", "Smoothie"): "Refreshment",
    ("Oasis", "Oasis"): "Fertile Land",
    ("Fertile Land", "Fertile Land"): "Agriculture",
    ("Agriculture", "Water"): "Irrigation",
    ("Irrigation", "Irrigation"): "Crop",
    ("Crop", "Crop"): "Food",
    ("Food", "Food"): "Dish",
    ("Dish", "Feast"): "Banquet",
    ("Banquet", "Banquet"): "Fair",
    ("Fair", "Fair"): "Entertainment",
    ("Entertainment", "Entertainment"): "Virtual Reality",
    ("Virtual Reality", "Virtual Reality"): "VR Game",
    ("VR Game", "VR Game"): "Immersive Play",
    ("Immersive Play", "AI Interface"): "Adaptive Game",
    ("Adaptive Game", "Adaptive Game"): "Personalized Game",
    ("Personalized Game", "Personalized Game"): "Gaming Ecosystem",
    ("Gaming Ecosystem", "Gaming Ecosystem"): "Gaming Industry",
    ("Gaming Industry", "Gaming Industry"): "Economy",
    ("Economy", "Economy"): "Civilization",
    ("Civilization", "Civilization"): "Innovation",
    ("Innovation", "Internet"): "Tech Revolution",
    ("Tech Revolution", "Tech Revolution"): "Next-Gen Society",
    ("Next-Gen Society", "AI Interface"): "Singularity",
    ("Singularity", "Singularity"): "Transcendence",
    ("Transcendence", "Transcendence"): "Enlightenment",
    ("Enlightenment", "Enlightenment"): "Consciousness",
    ("Consciousness", "Consciousness"): "Multiverse",
    ("Multiverse", "Multiverse"): "Alternate Reality",
    ("Alternate Reality", "Alternate Reality"): "Fiction",
    ("Fiction", "Fiction"): "Myth",
    ("Myth", "Myth"): "Folklore",
    ("Folklore", "Folklore"): "Tradition",
    ("Tradition", "Tradition"): "Heritage",
    ("Heritage", "Heritage"): "Nation",
    ("Nation", "Nation"): "Symbol",
    ("Symbol", "Symbol"): "Patriotism",
    ("Patriotism", "Fire"): "Passion",
    ("Passion", "Passion"): "Masterpiece",
    ("Masterpiece", "Masterpiece"): "Classic",
    ("Classic", "Classic"): "Novel",
    ("Novel", "Novel"): "Bookworm",
    ("Bookworm", "Bookworm"): "Archive",
    ("Archive", "Archive"): "Archive Lore",
    ("Archive Lore", "Archive Lore"): "Knowledge Base",
    ("Knowledge Base", "Internet"): "Wiki",
    ("Wiki", "Wiki"): "Collaborator",
    ("Collaborator", "Collaborator"): "Collective",
    ("Collective", "Collective"): "Reform",
    ("Reform", "Reform"): "Legislation",
    ("Legislation", "Legislation"): "Governance",
    ("Governance", "Governance"): "Republic",
    ("Republic", "Nation"): "Country",
    ("Country", "Country"): "Treaty",
    ("Treaty", "Treaty"): "Peace",
    ("Peace", "Peace"): "Harmony",
    ("Harmony", "Harmony"): "Anthem",
    ("Anthem", "Anthem"): "Rally",
    ("Rally", "Passion"): "Movement",
    ("Movement", "Movement"): "Revolution Legacy",
    ("Revolution Legacy", "Revolution Legacy"): "Monument",
    ("Monument", "Stone"): "Colosseum",
    ("Colosseum", "Entertainment"): "Spectacle",
    ("Spectacle", "Spectacle"): "Festival",
    ("Festival", "Tradition"): "Holiday",
    ("Holiday", "Fire"): "Bonfire",
    ("Bonfire", "Bonfire"): "Campfire Tale"
}

# Danh sách 50 chậu mới
available_pots = {
    "ch1": {"desc": "Chậu cơ bản", "effect": None, "price": 50000, "emoji": "🪴"},
    "ch2": {"desc": "Tăng tốc 10%", "effect": "speed_up_10", "price": 200000, "emoji": "⚡"},
    "ch3": {"desc": "Tăng vàng 10%", "effect": "gold_bonus_10", "price": 400000, "emoji": "💰"},
    "ch4": {"desc": "Tăng đột biến 5%", "effect": "mutate_chance_5", "price": 600000, "emoji": "🦠"},
    "ch5": {"desc": "Kháng thời tiết", "effect": "weather_resist", "price": 800000, "emoji": "⛅"},
    "ch6": {"desc": "Tăng tốc 20%", "effect": "speed_up_20", "price": 1500000, "emoji": "🏃"},
    "ch7": {"desc": "Tăng vàng 20%", "effect": "gold_bonus_20", "price": 2000000, "emoji": "🪙"},
    "ch8": {"desc": "Tăng đột biến 10%", "effect": "mutate_chance_10", "price": 3000000, "emoji": "🧬"},
    "ch9": {"desc": "Giảm chi phí lai 10%", "effect": "breeding_cost_10", "price": 320000, "emoji": "🤝"},
    "ch10": {"desc": "Tăng chất lượng cây", "effect": "plant_quality", "price": 350000, "emoji": "🌟"},
    "ch11": {"desc": "Tăng tốc 30%", "effect": "speed_up_30", "price": 400000, "emoji": "🚀"},
    "ch12": {"desc": "Tăng vàng 30%", "effect": "gold_bonus_30", "price": 420000, "emoji": "💸"},
    "ch13": {"desc": "Tăng đột biến 15%", "effect": "mutate_chance_15", "price": 450000, "emoji": "🧪"},
    "ch14": {"desc": "Kháng bão", "effect": "storm_resist", "price": 470000, "emoji": "🌪️"},
    "ch15": {"desc": "Giảm chi phí lai 20%", "effect": "breeding_cost_20", "price": 500000, "emoji": "💑"},
    "ch16": {"desc": "Tăng tốc mưa 50%", "effect": "rain_speed_50", "price": 550000, "emoji": "🌧️"},
    "ch17": {"desc": "Tăng vàng nắng 50%", "effect": "sun_gold_50", "price": 570000, "emoji": "☀️"},
    "ch18": {"desc": "Tăng đột biến bão 20%", "effect": "storm_mutate_20", "price": 600000, "emoji": "⚡"},
    "ch19": {"desc": "Kháng tuyết", "effect": "snow_resist", "price": 620000, "emoji": "❄️"},
    "ch20": {"desc": "Tăng chất lượng cao", "effect": "plant_quality_high", "price": 650000, "emoji": "✨"},
    "ch21": {"desc": "Tăng tốc 40%", "effect": "speed_up_40", "price": 700000, "emoji": "🌠"},
    "ch22": {"desc": "Tăng vàng 40%", "effect": "gold_bonus_40", "price": 720000, "emoji": "💎"},
    "ch23": {"desc": "Tăng đột biến 20%", "effect": "mutate_chance_20", "price": 750000, "emoji": "🧫"},
    "ch24": {"desc": "Giảm chi phí lai 30%", "effect": "breeding_cost_30", "price": 770000, "emoji": "👥"},
    "ch25": {"desc": "Tăng cây hiếm", "effect": "rare_plant", "price": 800000, "emoji": "🌺"},
    "ch26": {"desc": "Tăng tốc gió 50%", "effect": "wind_speed_50", "price": 850000, "emoji": "💨"},
    "ch27": {"desc": "Tăng vàng tuyết 50%", "effect": "snow_gold_50", "price": 870000, "emoji": "🏔️"},
    "ch28": {"desc": "Tăng đột biến nắng 20%", "effect": "sun_mutate_20", "price": 900000, "emoji": "🌞"},
    "ch29": {"desc": "Kháng âm u", "effect": "cloud_resist", "price": 920000, "emoji": "☁️"},
    "ch30": {"desc": "Tăng chất lượng siêu", "effect": "plant_quality_super", "price": 950000, "emoji": "💫"},
    "ch31": {"desc": "Tăng tốc 50%", "effect": "speed_up_50", "price": 1000000, "emoji": "⚡"},
    "ch32": {"desc": "Tăng vàng 50%", "effect": "gold_bonus_50", "price": 1050000, "emoji": "🤑"},
    "ch33": {"desc": "Tăng đột biến 25%", "effect": "mutate_chance_25", "price": 1100000, "emoji": "🧬"},
    "ch34": {"desc": "Giảm chi phí lai 40%", "effect": "breeding_cost_40", "price": 1150000, "emoji": "💞"},
    "ch35": {"desc": "Tăng cây siêu hiếm", "effect": "ultra_rare_plant", "price": 1200000, "emoji": "🪷"},
    "ch36": {"desc": "Tăng tốc bão 50%", "effect": "storm_speed_50", "price": 1250000, "emoji": "🌩️"},
    "ch37": {"desc": "Tăng vàng mưa 50%", "effect": "rain_gold_50", "price": 1300000, "emoji": "💧"},
    "ch38": {"desc": "Tăng đột biến tuyết 20%", "effect": "snow_mutate_20", "price": 1350000, "emoji": "❄️"},
    "ch39": {"desc": "Kháng tất cả", "effect": "all_weather_resist", "price": 1400000, "emoji": "🌈"},
    "ch40": {"desc": "Tăng chất lượng tối đa", "effect": "plant_quality_max", "price": 1450000, "emoji": "🌟"},
    "ch41": {"desc": "Tăng tốc 60%", "effect": "speed_up_60", "price": 1500000, "emoji": "🚀"},
    "ch42": {"desc": "Tăng vàng 60%", "effect": "gold_bonus_60", "price": 1550000, "emoji": "💰"},
    "ch43": {"desc": "Tăng đột biến 30%", "effect": "mutate_chance_30", "price": 1600000, "emoji": "🧪"},
    "ch44": {"desc": "Giảm chi phí lai 50%", "effect": "breeding_cost_50", "price": 1650000, "emoji": "🤝"},
    "ch45": {"desc": "Tăng cây huyền thoại", "effect": "legendary_plant", "price": 1700000, "emoji": "🪴"},
    "ch46": {"desc": "Tăng tốc nắng 75%", "effect": "sun_speed_75", "price": 1800000, "emoji": "☀️"},
    "ch47": {"desc": "Tăng vàng bão 75%", "effect": "storm_gold_75", "price": 1900000, "emoji": "⚡"},
    "ch48": {"desc": "Tăng đột biến mưa 30%", "effect": "rain_mutate_30", "price": 2000000, "emoji": "🌧️"},
    "ch49": {"desc": "Tăng chất lượng vĩnh cửu", "effect": "plant_quality_eternal", "price": 2500000, "emoji": "✨"},
    "ch50": {"desc": "Tất cả hiệu ứng tối đa", "effect": "all_max", "price": 1, "emoji": "🌌"}
}


# === Tạo GUI Server ===
root = tk.Tk()
root.title("🌾 Farm Server")
text_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=60, height=25, bg="#f0f0f0")
text_area.pack(padx=10, pady=10)
text_area.insert(tk.END, "Server đã khởi động...\n")

# Thêm nhãn số lượng người chơi online
online_label = tk.Label(root, text="👥 Số người online: 0", bg="#f0f0f0", font=("Arial", 12))
online_label.pack(pady=5)

# Khung nhập lệnh admin
admin_frame = tk.Frame(root, bg="#f0f0f0")
admin_frame.pack(fill=tk.X, padx=10, pady=5)
admin_entry = tk.Entry(admin_frame, font=("Arial", 12))
admin_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, pady=5)
admin_entry.bind("<Return>", lambda event: handle_admin_command(admin_entry.get()))
admin_button = tk.Button(admin_frame, text="Gửi lệnh", command=lambda: handle_admin_command(admin_entry.get()),
                        font=("Arial", 12))
admin_button.pack(side=tk.RIGHT, padx=5)

# === Biến toàn cục ===
coop_sessions = {}
clients = {}  # username -> socket
weather_list = ["Nắng", "Mưa", "Gió", "Bão", "Âm u", "Tuyết"]
current_weather = random.choice(weather_list)
weather_effects = {
    "Nắng": {"growth": 1.2, "gold": 1.0, "mutation_chance": 0.5},
    "Mưa": {"growth": 1.5, "gold": 0.8, "mutation_chance": 0.5},
    "Gió": {"growth": 0.9, "gold": 1.0, "mutation_chance": 1.0},
    "Bão": {"growth": 0.5, "gold": 0.7, "mutation_chance": 2.0},
    "Âm u": {"growth": 0.8, "gold": 0.9, "mutation_chance": 1.0},
    "Tuyết": {"growth": 0.3, "gold": 0.5, "mutation_chance": 2.0}
}
seed_price = 50  # Giá mỗi hạt giống
mature_plant_price = 150  # Giá bán mỗi cây trưởng thành
breeding_cost = 200  # Chi phí lai
mutation_levels = {
    "Green": {"chance": 0.1, "value": 1, "multiplier": 2},
    "Blue": {"chance": 0.08, "value": 2, "multiplier": 3},
    "Red": {"chance": 0.05, "value": 3, "multiplier": 4},
    "Yellow": {"chance": 0.04, "value": 4, "multiplier": 5},
    "Rainbow": {"chance": 0.01, "value": 5, "multiplier": 6}
}

# Thay hàm broadcast tại khoảng dòng 649–653
def broadcast(message):
    for username, client in list(clients.items()):  # Dùng list để tránh lỗi khi clients thay đổi
        try:
            client.send(message.encode('utf-8'))
        except Exception as e:
            update_gui(f"[Lỗi broadcast] Không gửi được tới {username}: {e}")
            clients.pop(username, None)  # Xóa client lỗi
            update_online_count()
def send_to_client(client_socket, message):
    try:
        client_socket.send(message.encode('utf-8'))
    except UnicodeEncodeError as e:
        update_gui(f"[!] Lỗi mã hóa khi gửi: {e}")
        update_gui(f"[!] Tin nhắn gây lỗi: {message[:100]}...")  # Giới hạn log để tránh dài
    except Exception as e:
        update_gui(f"[!] Lỗi gửi tới client: {e}")

def update_gui(text):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    text_area.insert(tk.END, f"[{timestamp}] {text}\n")
    text_area.see(tk.END)

def update_online_count():
    online_count = len(clients)
    online_label.config(text=f"👥 Số người online: {online_count}")
def get_effective_stage_owner(username):
    """Lấy username của người sở hữu tầng (người mời nếu trong co-op, hoặc chính người chơi)."""
    return coop_sessions.get(username, username)

def get_effective_stage(username):
    """Lấy tầng hiện tại của người sở hữu tầng."""
    effective_username = get_effective_stage_owner(username)
    cur.execute("SELECT current_stage FROM users WHERE username=?", (effective_username,))
    result = cur.fetchone()
    return result[0] if result else 0
def normalize_plant_type(plant_type):
    """Chuẩn hóa plant_type thành dạng không dấu."""
    if not plant_type:
        return None
    plant_type = plant_type.strip().title()
    return plant_type_mapping.get(plant_type, plant_type)
def pad_cell(cell, width):  # Thêm
    pad = width - wcswidth(cell)
    return cell + " " * max(0, pad)
def send_status(username, conn=None):
    if conn is None:
        conn = sqlite3.connect("farm_game.db", check_same_thread=False)
    local_cur = conn.cursor()
    try:
        effective_username = get_effective_stage_owner(username)
        local_cur.execute("SELECT money, stages, current_stage, island_name FROM users WHERE username=?", (username,))
        result = local_cur.fetchone()
        if not result:
            send_to_client(clients[username], "❌ Tài khoản không tồn tại.\n")
            return
        money, stages, _, user_island_name = result
        local_cur.execute("SELECT current_stage, island_name FROM users WHERE username=?", (effective_username,))
        effective_result = local_cur.fetchone()
        effective_stage = effective_result[0] if effective_result else 0
        effective_island_name = effective_result[1] if effective_result else "Đảo chưa đặt tên"

        # Lấy danh sách chậu đã đặt
        local_cur.execute("SELECT username, pot_name, slot, plant_type, plant_growth, mutation_level FROM placed_pots WHERE stage=? AND username IN (?, ?)",
                         (effective_stage, effective_username, username))
        pots = local_cur.fetchall()
        update_gui(f"[Debug] {username}: Found {len(pots)} pots in stage {effective_stage} for users {effective_username}, {username}")

        # Tạo giao diện nông trại
        repeat_count = 5  # 5 cụm mỗi hàng
        duplicate_count = 2  # 2 hàng cây
        farm_display = []

        # Tạo cặp hàng cây và chậu
        for row_idx in range(duplicate_count):
            top_row = []
            bottom_row = []
            start_slot = 1 + row_idx * 5
            end_slot = start_slot + 5
            for slot in range(start_slot, end_slot):
                pot_data = next((p for p in pots if p[2] == slot), None)
                if pot_data:
                    _, pot_name, _, plant_type, growth, mutation = pot_data
                    mutation_emoji = f"[{mutation}]" if mutation else "[]"
                    if plant_type:
                        normalized_plant_type = normalize_plant_type(plant_type)
                        if normalized_plant_type not in plant_emojis:
                            update_gui(f"[Cảnh báo] plant_type không hợp lệ: {plant_type} cho {effective_username} tại slot {slot}")
                            top_row += ["[]", "", "", " "]
                            bottom_row += ["", "", "", " "]
                            continue
                        growth_level = min(growth // 34, 2)
                        plant_emoji = plant_emojis[normalized_plant_type][growth_level]
                        status = "✅" if growth >= 100 else "🌱" if growth > 0 else ""
                        top_row += [mutation_emoji, plant_emoji, status, " "]
                        bottom_row += ["", available_pots[pot_name]["emoji"], "", " "]
                    else:
                        top_row += [mutation_emoji, "", "", " "]  # Ô có chậu nhưng chưa trồng
                        bottom_row += ["", available_pots[pot_name]["emoji"], "", " "]
                else:
                    top_row += ["[]", "", "", " "]  # Ô trống hoàn toàn
                    bottom_row += ["", "", "", " "]
            farm_display.append(top_row)
            farm_display.append(bottom_row)

        # Tính độ rộng hiển thị lớn nhất
        max_width = max(wcswidth(cell) for row in farm_display for cell in row) if farm_display else 1
        update_gui(f"[Debug] {username}: Max width calculated as {max_width}")

        # Chèn hàng mây
        cloud_row = ["☁️"] * (repeat_count * 4)
        insert_indices = [0, 2, 6]
        for offset, idx in enumerate(insert_indices):
            if idx + offset <= len(farm_display):
                farm_display.insert(idx + offset, cloud_row)

        # Căn chỉnh các ô
        aligned_display = ["".join(pad_cell(cell, max_width) for cell in row) for row in farm_display]

        # Lấy danh sách hạt giống và chậu
        local_cur.execute("SELECT plant_type, quantity, mature, mutation_level FROM user_seeds WHERE username=?", (username,))
        seeds = local_cur.fetchall()
        seed_list = []
        for plant_type, quantity, mature, mutation in seeds:
            display_type = f"{normalize_plant_type(plant_type)} {mutation if mutation else ''} Trưởng thành".strip() if mature else normalize_plant_type(plant_type)
            seed_list.append(f"{display_type}: {quantity}")
        seed_str = ", ".join(seed_list) if seed_list else "Chưa có hạt giống hoặc cây trưởng thành"

        local_cur.execute("SELECT pot_name, COUNT(*) FROM user_pots WHERE username=? AND stage=0 GROUP BY pot_name", (username,))
        pot_counts = local_cur.fetchall()
        pot_str = ", ".join([f"{pot_name}: {count}" for pot_name, count in pot_counts]) if pot_counts else "Chưa có chậu trong túi"

        # Tạo thông điệp trạng thái
        coop_status = "Chủ sở hữu chính"
        if username in coop_sessions:
            inviter = coop_sessions[username]
            coop_status = f"Đồng sở hữu đảo của {inviter}: {effective_island_name}"
        message = [
            f"📍 ☁️ Thời tiết: {current_weather} {weather_effects[current_weather].get('emoji', '🌤️')}",
            f"🏝️ Đảo: {user_island_name} (của {effective_username})",
            f"💵 Tiền: {money} xu",
            f"🏢 Tầng: {effective_stage}/{stages}",
            f"🤝 Trạng thái: {coop_status}",
            f"🪴 Chậu trong túi: {pot_str}",
            f"🌱 Hạt giống & Cây trưởng thành: {seed_str}",
            "🎭 Nông trại:"
        ]
        message.extend(aligned_display)
        response = "\n".join(message)
        send_to_client(clients[username], response)
        update_gui(f"[{username}] Trạng thái:\n{response}")
    except Exception as e:
        update_gui(f"[Lỗi /status] {username}: {str(e)}")
        send_to_client(clients[username], "❌ Lỗi khi hiển thị trạng thái. Vui lòng thử lại.\n")
    finally:
        if conn != sqlite3.connect("farm_game.db", check_same_thread=False):
            conn.close()

def weather_updater():
    global current_weather
    counter = 0
    while True:
        time.sleep(300)
        counter += 1
        if counter >= 10:
            broadcast(
                "📜 Danh sách lệnh:\n"
                "• /join – vào đảo\n"
                "• /chat <nội dung> – chat toàn server\n"
                "• /stage hoặc /tang <số tầng> – chuyển tầng\n"
                "• /buystage <số tầng> – mua tầng mới\n"
                "• /datchau hoặc /placepot <tên chậu> <ô1> [<ô2> ...] – đặt nhiều chậu lên tầng\n"
                "• /xoachau hoặc /removepot <tên chậu> <ô> – gỡ chậu\n"
                "• /chau hoặc /pots – xem các chậu, hạt giống và cây trưởng thành\n"
                "• /balo – xem balo (chậu, hạt giống, cây trưởng thành)\n"
                "• /buypot hoặc /buychau <tên chậu> [số lượng] – mua chậu\n"
                "• /buyseed <loại cây> [số lượng] – mua hạt giống\n"
                "• /plant <loại cây> <ô1> [<ô2> ...] – trồng nhiều cây\n"
                "• /thuhoach – thu hoạch tất cả cây trưởng thành\n"
                "• /sell <loại cây> [số lượng] [loại đột biến] – bán cây trưởng thành\n"
                "• /lai <ô1> <ô2> – lai hai cây trưởng thành\n"
                "• /trade <người nhận> <item> <số lượng> [tên item] – trao đổi item\n"
                "• /invite <tên người dùng> – mời người chơi làm đồng sở hữu\n"
                "• /accept <tên người mời> – chấp nhận làm đồng sở hữu\n"
                "• /setislandname <tên đảo> – đặt tên cho đảo\n"
                "• /coopstatus – kiểm tra trạng thái đồng sở hữu\n"
                "• /shop – xem cửa hàng\n"
                "• /addadmin <user> – (admin) thêm admin\n"
                "• /removeadmin <user> – (admin) xóa admin\n"
                "• /chochau <user> <tên chậu> – (admin) tặng chậu\n"
                "• /giveseed <user> <loại cây> <số lượng> [mature] – (admin) tặng hạt giống hoặc cây trưởng thành\n"
                "• /addmoney <user> <số tiền> – (admin) cộng tiền\n"
                "• /setstage <user> <số tầng> – (admin) đặt số tầng\n"
                "🌦️ Thời tiết thay đổi sau mỗi 30 giây, ảnh hưởng cây trồng!"
            )
            counter = 0
        current_weather = random.choice(weather_list)
        broadcast(f"🌦️ Thời tiết đã thay đổi! Hiện tại là: {current_weather}\n")
        update_gui(f"[Thời tiết] Đã cập nhật: {current_weather}")
        for username in clients:
            send_status(username)

threading.Thread(target=weather_updater, daemon=True).start()

def plant_growth_updater():
    while True:
        time.sleep(30)  # Cập nhật mỗi 10 giây
        try:
            cur.execute(
                "SELECT username, stage, slot, plant_type, plant_growth, pot_name FROM placed_pots WHERE plant_type IS NOT NULL")
            growing_plants = cur.fetchall()
            for username, stage, slot, plant_type, growth, pot_name in growing_plants:
                if username not in clients:
                    continue
                # Tính toán tăng trưởng dựa trên thời tiết
                weather_effect = weather_effects[current_weather]
                growth_rate = weather_effect["growth"]
                mutation_chance_base = weather_effect["mutation_chance"]

                # Áp dụng hiệu ứng từ chậu (nếu có)
                pot_effect = available_pots[pot_name].get("effect")
                if pot_effect and "mutate_chance" in pot_effect:
                    mutation_bonus = float(pot_effect.split("_")[-1]) / 100  # Lấy phần trăm từ effect
                    mutation_chance_base += mutation_bonus

                # Tăng trưởng
                new_growth = growth + (10 * growth_rate)  # Tăng 10 đơn vị mỗi lần, nhân với hiệu ứng thời tiết
                mutation_roll = random.random() * 100  # Tạo số ngẫu nhiên từ 0-100

                # Kiểm tra đột biến
                mutation_applied = False
                for mutation_level, details in mutation_levels.items():
                    if mutation_roll <= (details["chance"] * 100 * mutation_chance_base):
                        cur.execute(
                            "UPDATE placed_pots SET plant_growth=?, mutation_level=? WHERE username=? AND stage=? AND slot=?",
                            (new_growth, mutation_level, username, stage, slot))
                        mutation_applied = True
                        send_to_client(clients[username],
                                      f"🌟 Cây ở tầng {stage}, ô {slot} đã đột biến thành cấp {mutation_level}!\n")
                        update_gui(f"[{username}] cây ở tầng {stage}, ô {slot} đột biến thành {mutation_level}.")
                        break

                if not mutation_applied and new_growth < 100:
                    cur.execute(
                        "UPDATE placed_pots SET plant_growth=? WHERE username=? AND stage=? AND slot=?",
                        (new_growth, username, stage, slot))

                # Đánh dấu cây trưởng thành nếu đạt 100
                if new_growth >= 100 and not mutation_applied:
                    cur.execute(
                        "UPDATE placed_pots SET plant_growth=100 WHERE username=? AND stage=? AND slot=?",
                        (username, stage, slot))
                    send_to_client(clients[username],
                                  f"🌳 Cây ở tầng {stage}, ô {slot} đã trưởng thành!\n")
                    update_gui(f"[{username}] cây ở tầng {stage}, ô {slot} đã trưởng thành.")

            conn.commit()
            # Cập nhật trạng thái cho tất cả người chơi
            for username in clients:
                send_status(username)
        except Exception as e:
            update_gui(f"[Lỗi plant_growth_updater]: {str(e)}")
        time.sleep(30)  # Đợi thêm 10 giây trước khi lặp lại

threading.Thread(target=plant_growth_updater, daemon=True).start()

def handle_admin_command(command):
    command = command.strip()
    if not command:
        update_gui("[ADMIN] Lệnh trống.")
        admin_entry.delete(0, tk.END)
        return

    update_gui(f"[ADMIN] Nhập lệnh: {command}")
    parts = command.split()

    try:
        # Kiểm tra quyền admin
        cur.execute("SELECT username FROM admins WHERE username=?", (parts[1] if len(parts) > 1 else "",))
        if not cur.fetchone() and parts[0] in ["/addadmin", "/removeadmin", "/chochau", "/giveseed", "/addmoney", "/setstage"]:
            update_gui("[ADMIN] Lệnh yêu cầu quyền admin.")
            admin_entry.delete(0, tk.END)
            return

        if command.startswith("/addadmin"):
            if len(parts) == 2:
                target_user = parts[1]
                if target_user in clients:
                    cur.execute("INSERT OR IGNORE INTO admins (username) VALUES (?)", (target_user,))
                    conn.commit()
                    send_to_client(clients[target_user], "🎉 Bạn đã được cấp quyền admin!\n")
                    update_gui(f"[ADMIN] Đã cấp quyền admin cho {target_user}.")
                else:
                    update_gui("[ADMIN] Người dùng không trực tuyến.")
            else:
                update_gui("[ADMIN] Vui lòng nhập: /addadmin <user>")

        elif command.startswith("/removeadmin"):
            if len(parts) == 2:
                target_user = parts[1]
                if target_user != "admin":  # Ngăn xóa admin mặc định
                    cur.execute("DELETE FROM admins WHERE username=?", (target_user,))
                    conn.commit()
                    if cur.rowcount > 0:
                        if target_user in clients:
                            send_to_client(clients[target_user], "⚠️ Quyền admin của bạn đã bị xóa.\n")
                        update_gui(f"[ADMIN] Đã xóa quyền admin của {target_user}.")
                    else:
                        update_gui("[ADMIN] Người dùng không phải admin.")
                else:
                    update_gui("[ADMIN] Không thể xóa admin mặc định.")
            else:
                update_gui("[ADMIN] Vui lòng nhập: /removeadmin <user>")

        elif command.startswith("/chochau"):
            if len(parts) >= 3:
                target_user, pot_name = parts[1], parts[2].lower()
                if target_user in clients and pot_name in available_pots:
                    cur.execute("INSERT INTO user_pots (username, pot_name, stage) VALUES (?, ?, 0)",
                                (target_user, pot_name))
                    conn.commit()
                    send_to_client(clients[target_user], f"🎁 Admin đã tặng bạn chậu {pot_name}!\n")
                    update_gui(f"[ADMIN] Đã tặng chậu {pot_name} cho {target_user}.")
                else:
                    update_gui("[ADMIN] Người dùng hoặc chậu không tồn tại.")
            else:
                update_gui("[ADMIN] Vui lòng nhập: /chochau <user> <tên chậu>")

        elif command.startswith("/giveseed"):
            if len(parts) >= 4 and parts[3].isdigit():
                target_user, plant_type, quantity = parts[1], normalize_plant_type(parts[2]), int(parts[3])
                mature = 1 if len(parts) == 5 and parts[4].lower() == "mature" else 0
                if target_user in clients and plant_type in plant_types and quantity > 0:
                    cur.execute("SELECT quantity FROM user_seeds WHERE username=? AND plant_type=? AND mature=?",
                                (target_user, plant_type, mature))
                    result = cur.fetchone()
                    if result:
                        cur.execute("UPDATE user_seeds SET quantity=quantity+? WHERE username=? AND plant_type=? AND mature=?",
                                    (quantity, target_user, plant_type, mature))
                    else:
                        cur.execute("INSERT INTO user_seeds (username, plant_type, quantity, mature) VALUES (?, ?, ?, ?)",
                                    (target_user, plant_type, quantity, mature))
                    conn.commit()
                    item_name = f"{plant_type} {'Trưởng thành' if mature else ''}"
                    send_to_client(clients[target_user],
                                   f"🎁 Admin đã tặng bạn {quantity} {item_name}!\n")
                    update_gui(f"[ADMIN] Đã tặng {quantity} {item_name} cho {target_user}.")
                else:
                    update_gui("[ADMIN] Người dùng, loại cây không hợp lệ hoặc số lượng phải > 0.")
            else:
                update_gui("[ADMIN] Vui lòng nhập: /giveseed <user> <loại cây> <số lượng> [mature]")

        elif command.startswith("/addmoney"):
            if len(parts) >= 3 and parts[2].isdigit():
                target_user, amount = parts[1], int(parts[2])
                if target_user in clients:
                    cur.execute("UPDATE users SET money=money+? WHERE username=?", (amount, target_user))
                    conn.commit()
                    send_to_client(clients[target_user], f"🎁 Admin đã cộng {amount} xu vào tài khoản của bạn!\n")
                    update_gui(f"[ADMIN] Đã cộng {amount} xu cho {target_user}.")
                    send_status(target_user)
                else:
                    update_gui("[ADMIN] Người dùng không tồn tại.")
            else:
                update_gui("[ADMIN] Vui lòng nhập: /addmoney <user> <số tiền>")

        elif command.startswith("/setstage"):
            if len(parts) >= 3 and parts[2].isdigit():
                target_user, stage = parts[1], int(parts[2])
                if target_user in clients:
                    cur.execute("UPDATE users SET stages=?, current_stage=? WHERE username=?",
                                (stage, stage, target_user))
                    conn.commit()
                    send_to_client(clients[target_user], f"🏢 Admin đã đặt số tầng của bạn thành {stage}!\n")
                    update_gui(f"[ADMIN] Đã đặt số tầng của {target_user} thành {stage}.")
                    send_status(target_user)
                else:
                    update_gui("[ADMIN] Người dùng không tồn tại.")
            else:
                update_gui("[ADMIN] Vui lòng nhập: /setstage <user> <số tầng>")

        else:
            update_gui("[ADMIN] Lệnh không hợp lệ. Dùng: /addadmin, /removeadmin, /chochau, /giveseed, /addmoney, /setstage")
    except Exception as e:
        update_gui(f"[Lỗi handle_admin_command]: {str(e)}")

    admin_entry.delete(0, tk.END)

def handle_client(client_socket):
    global clients
    try:
        username = client_socket.recv(1024).decode('utf-8').strip()
        update_gui(f"[Debug] Nhận username: {username}")
        if not re.match(r'^[a-zA-Z0-9_]{3,32}$', username):
            send_to_client(client_socket, "Tên tài khoản không hợp lệ\n")
            client_socket.close()
            return
        with lock:
            if username in clients:
                old_socket = clients[username]
                try:
                    # Kiểm tra xem socket cũ có còn hoạt động không
                    old_socket.send(b"")  # Gửi gói rỗng để kiểm tra
                except (ConnectionError, OSError):
                    update_gui(f"[Debug] Socket cũ của {username} đã đóng, cho phép kết nối mới")
                    clients.pop(username, None)  # Xóa phiên cũ
                else:
                    send_to_client(client_socket, "Tên tài khoản đã tồn tại\n")
                    client_socket.close()
                    return
            clients[username] = client_socket
        update_online_count()
        update_gui(f"[+] {username} đã kết nối.")
        broadcast(f"💬 {username} đã tham gia game.\n")
        # Lưu thông tin user vào database
        cur.execute("INSERT INTO users (username) VALUES (?)", (username,))
        conn.commit()
        update_gui(f"[Debug] Đã thêm user {username} vào database")

        # Thêm client vào danh sách
        clients[username] = client_socket
        update_online_count()
        broadcast(f"💬 {username} đã tham gia game!\n")
        update_gui(f"[+] {username} đã kết nối.")

        # Xử lý các lệnh từ client
        while True:
            try:
                data = client_socket.recv(8192).decode('utf-8').strip()
                if not data:
                    update_gui(f"[Debug] Client {username} ngắt kết nối")
                    break
                update_gui(f"[Debug] Nhận lệnh từ {username}: {data}")

                if data.startswith("/join"):
                    try:
                        # Đặt người chơi vào tầng 1
                        cur.execute("UPDATE users SET current_stage=1 WHERE username=?", (username,))
                        conn.commit()
                        send_to_client(client_socket, "🎉 Bạn đã tham gia trò chơi và được đưa đến tầng 1!\n")
                        update_gui(f"[{username}] Tham gia trò chơi, đặt tầng 1.")
                        send_status(username)
                    except Exception as e:
                        update_gui(f"[Lỗi /join] {username}: {str(e)}")
                        send_to_client(client_socket, "❌ Lỗi khi tham gia trò chơi. Vui lòng thử lại.\n")

                elif data.startswith("/status"):
                    send_status(username)

                elif data.startswith("/chat"):
                    message = data[5:].strip()
                    if message:
                        broadcast(f"💬 {username}: {message}\n")
                        update_gui(f"[{username}] chat: {message}")
                    else:
                        send_to_client(client_socket, "❓ Vui lòng nhập nội dung chat, ví dụ: /chat Xin chào\n")

                elif data.startswith("/stage") or data.startswith("/tang"):
                    parts = data.split()
                    if len(parts) == 2 and parts[1].isdigit():
                        stage = int(parts[1])
                        try:
                            cur.execute("SELECT stages FROM users WHERE username=?", (username,))
                            max_stages = cur.fetchone()[0]
                            if stage > max_stages:
                                send_to_client(client_socket, f"❌ Bạn chỉ có {max_stages} tầng, không thể chuyển đến tầng {stage}.\n")
                                continue
                            cur.execute("UPDATE users SET current_stage=? WHERE username=?", (stage, username))
                            conn.commit()
                            send_to_client(client_socket, f"🏢 Đã chuyển đến tầng {stage}.\n")
                            update_gui(f"[{username}] chuyển đến tầng {stage}.")
                            send_status(username)
                        except Exception as e:
                            update_gui(f"[Lỗi /stage] {username}: {str(e)}")
                            send_to_client(client_socket, "❌ Lỗi khi chuyển tầng. Vui lòng thử lại.\n")
                    else:
                        send_to_client(client_socket, "❓ Vui lòng nhập: /stage <số tầng> hoặc /tang <số tầng>\n")

                elif data.startswith("/buystage"):
                    parts = data.split()
                    if len(parts) == 2 and parts[1].isdigit():
                        stages = int(parts[1])
                        try:
                            cur.execute("SELECT money, stages FROM users WHERE username=?", (username,))
                            result = cur.fetchone()
                            money, current_stages = result
                            stage_cost = 1000 * stages
                            if money < stage_cost:
                                send_to_client(client_socket, f"❌ Không đủ tiền (cần {stage_cost} xu, bạn có {money} xu).\n")
                                continue
                            cur.execute("UPDATE users SET money=money-?, stages=stages+?, current_stage=? WHERE username=?",
                                        (stage_cost, stages, current_stages + stages, username))
                            conn.commit()
                            send_to_client(client_socket, f"🏢 Đã mua {stages} tầng mới, tổng cộng {current_stages + stages} tầng!\n")
                            update_gui(f"[{username}] mua {stages} tầng, tổng {current_stages + stages} tầng.")
                            send_status(username)
                        except Exception as e:
                            update_gui(f"[Lỗi /buystage] {username}: {str(e)}")
                            send_to_client(client_socket, "❌ Lỗi khi mua tầng. Vui lòng thử lại.\n")
                    else:
                        send_to_client(client_socket, "❓ Vui lòng nhập: /buystage <số tầng>\n")

                elif data.startswith("/datchau") or data.startswith("/placepot"):
                    parts = data.split()
                    if len(parts) >= 3 and all(slot.isdigit() for slot in parts[2:]):
                        pot_name = parts[1].lower()
                        slots = [int(slot) for slot in parts[2:]]
                        if not all(1 <= slot <= 10 for slot in slots):
                            send_to_client(client_socket, "❌ Tất cả ô phải từ 1 đến 10.\n")
                            continue
                        if pot_name not in available_pots:
                            send_to_client(client_socket, f"❌ Chậu {pot_name} không tồn tại.\n")
                            continue
                        try:
                            effective_username = get_effective_stage_owner(username)
                            effective_stage = get_effective_stage(username)
                            if effective_stage == 0:
                                send_to_client(client_socket, "❌ Bạn chưa ở tầng nào. Dùng /join hoặc /stage.\n")
                                continue
                            cur.execute("SELECT COUNT(*) FROM user_pots WHERE username=? AND pot_name=? AND stage=0",
                                        (username, pot_name))
                            available_count = cur.fetchone()[0]
                            if available_count < len(slots):
                                send_to_client(client_socket, f"❌ Không đủ chậu {pot_name} (cần {len(slots)}, có {available_count}).\n")
                                continue
                            placed_slots = []
                            for slot in slots:
                                cur.execute("SELECT pot_name FROM placed_pots WHERE stage=? AND slot=? AND username IN (?, ?)",
                                            (effective_stage, slot, effective_username, username))
                                existing_pot = cur.fetchone()
                                if existing_pot:
                                    send_to_client(client_socket, f"❌ Ô {slot} trên tầng {effective_stage} đã có chậu.\n")
                                    continue
                                cur.execute("SELECT id FROM user_pots WHERE username=? AND pot_name=? AND stage=0 ORDER BY id ASC LIMIT 1",
                                            (username, pot_name))
                                pot_id = cur.fetchone()
                                if pot_id:
                                    cur.execute("UPDATE user_pots SET stage=? WHERE id=?", (effective_stage, pot_id[0]))
                                    cur.execute("INSERT INTO placed_pots (username, pot_name, stage, slot) VALUES (?, ?, ?, ?)",
                                                (username, pot_name, effective_stage, slot))
                                    placed_slots.append(slot)
                            if placed_slots:
                                conn.commit()
                                placed_str = ", ".join(str(slot) for slot in placed_slots)
                                send_to_client(client_socket, f"🪴 Đã đặt chậu {pot_name} ở tầng {effective_stage}, ô: {placed_str}.\n")
                                update_gui(f"[{username}] đặt chậu {pot_name} ở tầng {effective_stage}, ô: {placed_str}.")
                                send_status(username)
                            else:
                                send_to_client(client_socket, "❌ Không thể đặt chậu ở bất kỳ ô nào.\n")
                        except Exception as e:
                            update_gui(f"[Lỗi /datchau] {username}: {str(e)}")
                            send_to_client(client_socket, "❌ Lỗi khi đặt chậu. Vui lòng thử lại.\n")
                    else:
                        send_to_client(client_socket, "❓ Vui lòng nhập: /datchau <tên chậu> <ô1> [<ô2> ...] hoặc /placepot <tên chậu> <ô1> [<ô2> ...]\n")

                elif data.startswith("/xoachau") or data.startswith("/removepot"):
                    parts = data.split()
                    if len(parts) == 3 and parts[2].isdigit():
                        pot_name = parts[1].lower()
                        slot = int(parts[2])
                        if not (1 <= slot <= 10):
                            send_to_client(client_socket, "❌ Ô phải từ 1 đến 10.\n")
                            continue
                        if pot_name not in available_pots:
                            send_to_client(client_socket, f"❌ Chậu {pot_name} không tồn tại.\n")
                            continue
                        try:
                            effective_username = get_effective_stage_owner(username)
                            effective_stage = get_effective_stage(username)
                            if effective_stage == 0:
                                send_to_client(client_socket, "❌ Bạn chưa ở tầng nào. Dùng /join hoặc /stage.\n")
                                continue
                            cur.execute("SELECT username, plant_type, pot_name FROM placed_pots WHERE stage=? AND slot=? AND username IN (?, ?)",
                                        (effective_stage, slot, effective_username, username))
                            pot = cur.fetchone()
                            if not pot:
                                send_to_client(client_socket, f"❌ Ô {slot} trên tầng {effective_stage} không có chậu.\n")
                                continue
                            pot_owner, plant_type, existing_pot_name = pot
                            if pot_name != existing_pot_name:
                                send_to_client(client_socket, f"❌ Ô {slot} không phải chậu {pot_name}.\n")
                                continue
                            if plant_type:
                                send_to_client(client_socket, f"❌ Ô {slot} đang có cây, không thể gỡ chậu.\n")
                                continue
                            cur.execute("DELETE FROM placed_pots WHERE username=? AND stage=? AND slot=?",
                                        (pot_owner, effective_stage, slot))
                            cur.execute("INSERT INTO user_pots (username, pot_name, stage) VALUES (?, ?, 0)",
                                        (username, pot_name))
                            conn.commit()
                            send_to_client(client_socket, f"🪴 Đã gỡ chậu {pot_name} ở tầng {effective_stage}, ô {slot} và thêm vào túi.\n")
                            update_gui(f"[{username}] gỡ chậu {pot_name} ở tầng {effective_stage}, ô {slot}.")
                            send_status(username)
                        except Exception as e:
                            update_gui(f"[Lỗi /xoachau] {username}: {str(e)}")
                            send_to_client(client_socket, "❌ Lỗi khi gỡ chậu. Vui lòng thử lại.\n")
                    else:
                        send_to_client(client_socket, "❓ Vui lòng nhập: /xoachau <tên chậu> <ô> hoặc /removepot <tên chậu> <ô>\n")

                elif data.startswith("/pots") or data.startswith("/chau"):
                    try:
                        cur.execute("SELECT pot_name, COUNT(*) FROM user_pots WHERE username=? AND stage=0 GROUP BY pot_name",
                                    (username,))
                        pot_counts = cur.fetchall()
                        pot_str = ", ".join([f"{pot_name}: {count}" for pot_name, count in pot_counts]) if pot_counts else "Chưa có chậu trong túi"
                        cur.execute("SELECT plant_type, quantity, mature, mutation_level FROM user_seeds WHERE username=?", (username,))
                        seeds = cur.fetchall()
                        seed_list = []
                        for plant_type, quantity, mature, mutation in seeds:
                            display_type = f"{normalize_plant_type(plant_type)} {mutation if mutation else ''} Trưởng thành".strip() if mature else normalize_plant_type(plant_type)
                            seed_list.append(f"{display_type}: {quantity}")
                        seed_str = ", ".join(seed_list) if seed_list else "Chưa có hạt giống hoặc cây trưởng thành"
                        response = f"🎒 Danh sách tài sản của {username}:\n🪴 Chậu trong túi: {pot_str}\n🌱 Hạt giống & Cây trưởng thành: {seed_str}\n"
                        send_to_client(client_socket, response)
                        update_gui(f"[{username}] xem danh sách chậu và hạt giống.")
                    except Exception as e:
                        update_gui(f"[Lỗi /pots] {username}: {str(e)}")
                        send_to_client(client_socket, "❌ Lỗi khi xem danh sách chậu và hạt giống. Vui lòng thử lại.\n")

                elif data.startswith("/balo"):
                    try:
                        cur.execute("SELECT pot_name, COUNT(*) FROM user_pots WHERE username=? AND stage=0 GROUP BY pot_name",
                                    (username,))
                        pot_counts = cur.fetchall()
                        pot_str = ", ".join([f"{pot_name}: {count}" for pot_name, count in pot_counts]) if pot_counts else "Chưa có chậu trong túi"
                        cur.execute("SELECT plant_type, quantity, mature, mutation_level FROM user_seeds WHERE username=?", (username,))
                        seeds = cur.fetchall()
                        seed_list = []
                        for plant_type, quantity, mature, mutation in seeds:
                            display_type = f"{normalize_plant_type(plant_type)} {mutation if mutation else ''} Trưởng thành".strip() if mature else normalize_plant_type(plant_type)
                            seed_list.append(f"{display_type}: {quantity}")
                        seed_str = ", ".join(seed_list) if seed_list else "Chưa có hạt giống hoặc cây trưởng thành"
                        response = f"🎒 Balo của {username}:\n🪴 Chậu trong túi: {pot_str}\n🌱 Hạt giống & Cây trưởng thành: {seed_str}\n"
                        send_to_client(client_socket, response)
                        update_gui(f"[{username}] xem balo.")
                    except Exception as e:
                        update_gui(f"[Lỗi /balo] {username}: {str(e)}")
                        send_to_client(client_socket, "❌ Lỗi khi mở balo. Vui lòng thử lại.\n")

                elif data.startswith("/buypot") or data.startswith("/buychau"):
                    parts = data.split()
                    if len(parts) >= 2 and (len(parts) == 2 or parts[2].isdigit()):
                        pot_name = parts[1].lower()
                        quantity = int(parts[2]) if len(parts) == 3 else 1
                        if pot_name not in available_pots:
                            send_to_client(client_socket, f"❌ Chậu {pot_name} không tồn tại.\n")
                            continue
                        if quantity < 1:
                            send_to_client(client_socket, "❌ Số lượng phải lớn hơn 0.\n")
                            continue
                        try:
                            cur.execute("SELECT money FROM users WHERE username=?", (username,))
                            money = cur.fetchone()[0]
                            pot_price = available_pots[pot_name]["price"] * quantity
                            if money < pot_price:
                                send_to_client(client_socket, f"❌ Không đủ tiền (cần {pot_price} xu, bạn có {money} xu).\n")
                                continue
                            for _ in range(quantity):
                                cur.execute("INSERT INTO user_pots (username, pot_name, stage) VALUES (?, ?, 0)",
                                            (username, pot_name))
                            cur.execute("UPDATE users SET money=money-? WHERE username=?", (pot_price, username))
                            conn.commit()
                            send_to_client(client_socket, f"🪴 Đã mua {quantity} chậu {pot_name} với giá {pot_price} xu.\n")
                            update_gui(f"[{username}] mua {quantity} chậu {pot_name}, giá {pot_price} xu.")
                            send_status(username)
                        except Exception as e:
                            update_gui(f"[Lỗi /buypot] {username}: {str(e)}")
                            send_to_client(client_socket, "❌ Lỗi khi mua chậu. Vui lòng thử lại.\n")
                    else:
                        send_to_client(client_socket, "❓ Vui lòng nhập: /buypot <tên chậu> [số lượng] hoặc /buychau <tên chậu> [số lượng]\n")

                elif data.startswith("/buyseed"):
                    parts = data.split()
                    if len(parts) >= 2 and (len(parts) == 2 or parts[2].isdigit()):
                        plant_type = normalize_plant_type(parts[1])
                        quantity = int(parts[2]) if len(parts) == 3 else 1
                        if plant_type not in plant_types:
                            send_to_client(client_socket, f"❌ Loại cây {plant_type} không tồn tại. Chọn: {', '.join(plant_types)}\n")
                            continue
                        if quantity < 1:
                            send_to_client(client_socket, "❌ Số lượng phải lớn hơn 0.\n")
                            continue
                        try:
                            cur.execute("SELECT money FROM users WHERE username=?", (username,))
                            money = cur.fetchone()[0]
                            total_cost = seed_price * quantity
                            if money < total_cost:
                                send_to_client(client_socket, f"❌ Không đủ tiền (cần {total_cost} xu, bạn có {money} xu).\n")
                                continue
                            cur.execute("SELECT quantity FROM user_seeds WHERE username=? AND plant_type=? AND mature=0",
                                        (username, plant_type))
                            result = cur.fetchone()
                            if result:
                                cur.execute("UPDATE user_seeds SET quantity=quantity+? WHERE username=? AND plant_type=? AND mature=0",
                                            (quantity, username, plant_type))
                            else:
                                cur.execute("INSERT INTO user_seeds (username, plant_type, quantity, mature) VALUES (?, ?, ?, 0)",
                                            (username, plant_type, quantity))
                            cur.execute("UPDATE users SET money=money-? WHERE username=?", (total_cost, username))
                            conn.commit()
                            send_to_client(client_socket, f"🌱 Đã mua {quantity} hạt giống {plant_type} với giá {total_cost} xu.\n")
                            update_gui(f"[{username}] mua {quantity} hạt giống {plant_type}, giá {total_cost} xu.")
                            send_status(username)
                        except Exception as e:
                            update_gui(f"[Lỗi /buyseed] {username}: {str(e)}")
                            send_to_client(client_socket, "❌ Lỗi khi mua hạt giống. Vui lòng thử lại.\n")
                    else:
                        send_to_client(client_socket, "❓ Vui lòng nhập: /buyseed <loại cây> [số lượng]\n")

                elif data.startswith("/plant"):
                    parts = data.split()
                    if len(parts) >= 3 and all(slot.isdigit() for slot in parts[2:]):
                        plant_type = normalize_plant_type(parts[1])
                        slots = [int(slot) for slot in parts[2:]]
                        if not all(1 <= slot <= 10 for slot in slots):
                            send_to_client(client_socket, "❌ Tất cả ô phải từ 1 đến 10.\n")
                            continue
                        if plant_type not in plant_types:
                            send_to_client(client_socket, f"❌ Loại cây {plant_type} không tồn tại. Chọn: {', '.join(plant_types)}\n")
                            continue
                        try:
                            effective_username = get_effective_stage_owner(username)
                            effective_stage = get_effective_stage(username)
                            if effective_stage == 0:
                                send_to_client(client_socket, "❌ Bạn chưa ở tầng nào. Dùng /join hoặc /stage.\n")
                                continue
                            cur.execute("SELECT quantity FROM user_seeds WHERE username=? AND plant_type=? AND mature=0",
                                        (username, plant_type))
                            seed_result = cur.fetchone()
                            if not seed_result or seed_result[0] < len(slots):
                                send_to_client(client_socket, f"❌ Không đủ hạt giống {plant_type} (cần {len(slots)}, có {seed_result[0] if seed_result else 0}).\n")
                                continue
                            planted_slots = []
                            for slot in slots:
                                cur.execute("SELECT username, pot_name, plant_type FROM placed_pots WHERE stage=? AND slot=? AND username IN (?, ?)",
                                            (effective_stage, slot, effective_username, username))
                                pot = cur.fetchone()
                                if not pot:
                                    send_to_client(client_socket, f"❌ Ô {slot} trên tầng {effective_stage} chưa có chậu.\n")
                                    continue
                                pot_owner, pot_name, current_plant = pot
                                if current_plant:
                                    send_to_client(client_socket, f"❌ Ô {slot} trên tầng {effective_stage} đã có cây.\n")
                                    continue
                                cur.execute("UPDATE user_seeds SET quantity=quantity-1 WHERE username=? AND plant_type=? AND mature=0",
                                            (username, plant_type))
                                cur.execute("UPDATE placed_pots SET plant_type=?, plant_growth=0, plant_time=?, mutation_level=NULL WHERE username=? AND stage=? AND slot=?",
                                            (plant_type, int(time.time()), pot_owner, effective_stage, slot))
                                planted_slots.append(slot)
                            if planted_slots:
                                conn.commit()
                                planted_str = ", ".join(str(slot) for slot in planted_slots)
                                send_to_client(client_socket, f"🌱 Đã trồng cây {plant_type} ở tầng {effective_stage}, ô: {planted_str}.\n")
                                update_gui(f"[{username}] trồng cây {plant_type} ở tầng {effective_stage}, ô: {planted_str}.")
                                send_status(username)
                            else:
                                send_to_client(client_socket, "❌ Không thể trồng cây ở bất kỳ ô nào.\n")
                        except Exception as e:
                            update_gui(f"[Lỗi /plant] {username}: {str(e)}")
                            send_to_client(client_socket, "❌ Lỗi khi trồng cây. Vui lòng thử lại.\n")
                    else:
                        send_to_client(client_socket, "❓ Vui lòng nhập: /plant <loại cây> <ô1> [<ô2> ...], ví dụ: /plant Nuoc 1 2 3\n")

                elif data.startswith("/thuhoach"):
                    try:
                        effective_username = get_effective_stage_owner(username)
                        effective_stage = get_effective_stage(username)
                        if effective_stage == 0:
                            send_to_client(client_socket, "❌ Bạn chưa ở tầng nào. Dùng /join hoặc /stage.\n")
                            continue
                        cur.execute("SELECT username, stage, slot, plant_type, pot_name, mutation_level FROM placed_pots WHERE stage=? AND username IN (?, ?) AND plant_growth>=100",
                                    (effective_stage, effective_username, username))
                        mature_plants = cur.fetchall()
                        if not mature_plants:
                            send_to_client(client_socket, "❌ Không có cây nào trưởng thành để thu hoạch.\n")
                            continue
                        harvested = []
                        total_gold = 0
                        for pot_owner, stage, slot, plant_type, pot_name, mutation in mature_plants:
                            normalized_plant_type = normalize_plant_type(plant_type)
                            cur.execute("SELECT quantity FROM user_seeds WHERE username=? AND plant_type=? AND mature=1 AND mutation_level IS ?",
                                        (username, normalized_plant_type, mutation))
                            seed_result = cur.fetchone()
                            if seed_result:
                                cur.execute("UPDATE user_seeds SET quantity=quantity+1 WHERE username=? AND plant_type=? AND mature=1 AND mutation_level IS ?",
                                            (username, normalized_plant_type, mutation))
                            else:
                                cur.execute("INSERT INTO user_seeds (username, plant_type, quantity, mature, mutation_level) VALUES (?, ?, 1, 1, ?)",
                                            (username, normalized_plant_type, mutation))
                            base_gold = 100
                            multiplier = mutation_levels.get(mutation, {"multiplier": 1})["multiplier"]
                            gold = int(base_gold * multiplier * weather_effects[current_weather]["gold"])
                            pot_effect = available_pots[pot_name].get("effect")
                            if pot_effect and "gold_bonus" in pot_effect:
                                try:
                                    gold_percentage = int(pot_effect.split("_")[-1]) / 100
                                    gold = int(gold * (1 + gold_percentage))
                                except (ValueError, IndexError):
                                    update_gui(f"[Cảnh báo] Hiệu ứng chậu {pot_name} không hợp lệ: {pot_effect}")
                            cur.execute("UPDATE placed_pots SET plant_type=NULL, plant_growth=0, plant_time=0, mutation_level=NULL WHERE username=? AND stage=? AND slot=?",
                                        (pot_owner, stage, slot))
                            total_gold += gold
                            harvested.append(f"{normalized_plant_type} {mutation if mutation else ''} Trưởng thành (tầng {stage}, ô {slot})")
                        cur.execute("UPDATE users SET money=money+? WHERE username=?", (total_gold, username))
                        conn.commit()
                        harvested_str = ", ".join(harvested)
                        send_to_client(client_socket, f"🌾 Đã thu hoạch: {harvested_str}\n💰 Nhận được {total_gold} xu.\n🎍 Các cây trưởng thành đã được thêm vào túi. Dùng /pots để xem.\n💸 Bạn muốn bán cây trưởng thành? Dùng: /sell <loại cây> [số lượng], ví dụ: /sell Nuoc 2\n")
                        update_gui(f"[{username}] thu hoạch: {harvested_str}, nhận {total_gold} xu.")
                        send_status(username)
                    except Exception as e:
                        update_gui(f"[Lỗi /thuhoach] {username}: {str(e)}")
                        send_to_client(client_socket, "❌ Lỗi khi thu hoạch. Vui lòng thử lại.\n")

                elif data.startswith("/sell"):
                    parts = data.split()
                    if len(parts) >= 2 and len(parts) <= 4 and (len(parts) == 2 or parts[2].isdigit()):
                        plant_type = normalize_plant_type(parts[1])
                        quantity = int(parts[2]) if len(parts) >= 3 else 1
                        mutation_level = parts[3].title() if len(parts) == 4 else None
                        if plant_type not in plant_types:
                            send_to_client(client_socket, f"❌ Loại cây {plant_type} không tồn tại. Chọn: {', '.join(plant_types)}\n")
                            update_gui(f"[Debug /sell] {username} cố bán cây không tồn tại: {plant_type}")
                            continue
                        if mutation_level and mutation_level not in mutation_levels:
                            send_to_client(client_socket, f"❌ Loại đột biến {mutation_level} không hợp lệ. Chọn: {', '.join(mutation_levels.keys())}\n")
                            update_gui(f"[Debug /sell] {username} cố bán đột biến không hợp lệ: {mutation_level}")
                            continue
                        if quantity < 1:
                            send_to_client(client_socket, "❌ Số lượng phải lớn hơn 0.\n")
                            update_gui(f"[Debug /sell] {username} nhập số lượng không hợp lệ: {quantity}")
                            continue
                        try:
                            cur.execute("SELECT quantity FROM user_seeds WHERE username=? AND plant_type=? AND mature=1 AND mutation_level IS ?",
                                        (username, plant_type, mutation_level))
                            result = cur.fetchone()
                            current_quantity = result[0] if result else 0
                            if current_quantity < quantity:
                                display_type = f"{plant_type} {'Trưởng thành' if not mutation_level else mutation_level + ' Trưởng thành'}"
                                send_to_client(client_socket, f"❌ Không đủ {display_type} (có {current_quantity}).\n")
                                update_gui(f"[Debug /sell] {username} không đủ {display_type}: cần {quantity}, có {current_quantity}")
                                continue
                            multiplier = mutation_levels.get(mutation_level, {"multiplier": 1})["multiplier"]
                            sell_price = mature_plant_price * quantity * multiplier
                            cur.execute("UPDATE user_seeds SET quantity=quantity-? WHERE username=? AND plant_type=? AND mature=1 AND mutation_level IS ?",
                                        (quantity, username, plant_type, mutation_level))
                            cur.execute("UPDATE users SET money=money+? WHERE username=?", (sell_price, username))
                            conn.commit()
                            display_type = f"{plant_type} {'Trưởng thành' if not mutation_level else mutation_level + ' Trưởng thành'}"
                            send_to_client(client_socket, f"💸 Đã bán {quantity} {display_type}, nhận {sell_price} xu.\n")
                            update_gui(f"[{username}] bán {quantity} {display_type}, nhận {sell_price} xu.")
                            send_status(username)
                        except Exception as e:
                            update_gui(f"[Lỗi /sell] {username}: {str(e)}")
                            send_to_client(client_socket, "❌ Lỗi khi bán cây trưởng thành. Vui lòng thử lại.\n")
                    else:
                        send_to_client(client_socket, "❓ Vui lòng nhập: /sell <loại cây> [số lượng] [loại đột biến], ví dụ: /sell Water 2 Green hoặc /sell Water 1\n")

                elif data.startswith("/lai"):
                    parts = data.split()
                    if len(parts) == 3 and all(slot.isdigit() for slot in parts[1:]):
                        slot1, slot2 = int(parts[1]), int(parts[2])
                        if not (1 <= slot1 <= 10 and 1 <= slot2 <= 10):
                            send_to_client(client_socket, "❌ Ô trồng phải từ 1 đến 10.\n")
                            update_gui(f"[Debug /lai] {username} nhập ô không hợp lệ: {slot1}, {slot2}")
                            continue
                        try:
                            cur.execute("SELECT current_stage FROM users WHERE username=?", (username,))
                            result = cur.fetchone()
                            if not result:
                                send_to_client(client_socket, "❌ Tài khoản không tồn tại.\n")
                                update_gui(f"[Debug /lai] Tài khoản {username} không tồn tại")
                                continue
                            current_stage = result[0]
                            if current_stage == 0:
                                send_to_client(client_socket, "❌ Bạn chưa ở tầng nào. Dùng /join hoặc /stage.\n")
                                update_gui(f"[Debug /lai] {username} chưa ở tầng nào")
                                continue
                            cur.execute("SELECT pot_name, plant_type, plant_growth, mutation_level FROM placed_pots WHERE username=? AND stage=? AND slot=?",
                                        (username, current_stage, slot1))
                            pot1 = cur.fetchone()
                            cur.execute("SELECT pot_name, plant_type, plant_growth, mutation_level FROM placed_pots WHERE username=? AND stage=? AND slot=?",
                                        (username, current_stage, slot2))
                            pot2 = cur.fetchone()
                            if not pot1 or not pot2 or pot1[1] is None or pot2[1] is None or pot1[2] < 100 or pot2[2] < 100:
                                send_to_client(client_socket, "❌ Cả hai ô phải có cây trưởng thành để lai.\n")
                                update_gui(f"[Debug /lai] {username} không có cây trưởng thành ở ô {slot1} hoặc {slot2}")
                                continue
                            if pot1[3] != pot2[3]:
                                send_to_client(client_socket, "❌ Hai cây phải có cùng cấp đột biến (hoặc không đột biến) để lai.\n")
                                update_gui(f"[Debug /lai] {username} lai cây có mutation_level khác nhau: {pot1[3]} vs {pot2[3]}")
                                continue
                            plant_type1, plant_type2 = normalize_plant_type(pot1[1]), normalize_plant_type(pot2[1])
                            multiplier = mutation_levels.get(pot1[3], {"multiplier": 1})["multiplier"]
                            current_breeding_cost = breeding_cost * multiplier
                            cur.execute("SELECT money FROM users WHERE username=?", (username,))
                            money = cur.fetchone()[0]
                            if money < current_breeding_cost:
                                display_type1 = f"{plant_type1} {pot1[3] if pot1[3] else 'Trưởng thành'}"
                                send_to_client(client_socket, f"❌ Không đủ tiền để lai {display_type1} (cần {current_breeding_cost} xu, có {money} xu).\n")
                                update_gui(f"[Debug /lai] {username} không đủ tiền: cần {current_breeding_cost}, có {money}")
                                continue
                            new_seed = breeding_recipes.get((plant_type1, plant_type2)) or breeding_recipes.get((plant_type2, plant_type1))
                            if not new_seed:
                                display_type1 = f"{plant_type1} {pot1[3] if pot1[3] else 'Trưởng thành'}"
                                display_type2 = f"{plant_type2} {pot2[3] if pot2[3] else 'Trưởng thành'}"
                                send_to_client(client_socket, f"❌ Không thể lai {display_type1} và {display_type2}. Vui lòng báo cho ADMIN để cập nhật & nhận thưởng\n")
                                update_gui(f"[Debug /lai] {username} lai thất bại: {display_type1} + {display_type2}")
                                continue
                            mutation_result = pot1[3]
                            pot_effect = available_pots.get(pot1[0], {}).get("effect", None)
                            mutation_chance = weather_effects[current_weather]["mutation_chance"]
                            if pot_effect and "mutate_chance" in pot_effect:
                                try:
                                    mutation_percentage = int(pot_effect.split("_")[-1]) / 100
                                    mutation_chance += mutation_chance * mutation_percentage
                                except (ValueError, IndexError):
                                    update_gui(f"[Cảnh báo] Hiệu ứng chậu {pot1[0]} không hợp lệ: {pot_effect}")
                            if random.random() < mutation_chance and mutation_result != "Rainbow":
                                available_mutations = [m for m in mutation_levels if mutation_levels[m]["value"] > mutation_levels.get(mutation_result, {"value": 0})["value"]]
                                if available_mutations:
                                    mutation_result = random.choices(available_mutations, weights=[mutation_levels[m]["chance"] for m in available_mutations], k=1)[0]
                            cur.execute("UPDATE users SET money=money-? WHERE username=?", (current_breeding_cost, username))
                            cur.execute("UPDATE placed_pots SET plant_type=NULL, plant_growth=0, plant_time=0, mutation_level=NULL WHERE username=? AND stage=? AND slot IN (?, ?)",
                                        (username, current_stage, slot1, slot2))
                            cur.execute("SELECT quantity FROM user_seeds WHERE username=? AND plant_type=? AND mature=0 AND mutation_level IS ?",
                                        (username, new_seed, mutation_result))
                            result = cur.fetchone()
                            if result:
                                cur.execute("UPDATE user_seeds SET quantity=quantity+1 WHERE username=? AND plant_type=? AND mature=0 AND mutation_level IS ?",
                                            (username, new_seed, mutation_result))
                            else:
                                cur.execute("INSERT INTO user_seeds (username, plant_type, quantity, mature, mutation_level) VALUES (?, ?, 1, 0, ?)",
                                            (username, new_seed, mutation_result))
                            conn.commit()
                            display_seed = f"{new_seed} {mutation_result if mutation_result else 'Trưởng thành'}".strip()
                            display_type1 = f"{plant_type1} {pot1[3] if pot1[3] else 'Trưởng thành'}"
                            display_type2 = f"{plant_type2} {pot2[3] if pot2[3] else 'Trưởng thành'}"
                            send_to_client(client_socket, f"🌱 Đã lai thành công {display_type1} và {display_type2}! Nhận được 1 hạt giống {display_seed} (trừ {current_breeding_cost} xu).\n")
                            update_gui(f"[{username}] lai {display_type1} + {display_type2} = {display_seed} ở tầng {current_stage}, ô {slot1} và {slot2}, chi phí {current_breeding_cost} xu.")
                            send_status(username)
                        except Exception as e:
                            update_gui(f"[Lỗi /lai] {username}: {str(e)}")
                            send_to_client(client_socket, "❌ Lỗi khi lai cây. Vui lòng thử lại.\n")
                    else:
                        send_to_client(client_socket, "❓ Vui lòng nhập: /lai <ô1> <ô2>, ví dụ: /lai 1 2\n")

                elif data.startswith("/trade"):
                    parts = data.split()
                    if len(parts) >= 4 and parts[3].isdigit():
                        target_user, item_type, quantity = parts[1], parts[2].lower(), int(parts[3])
                        if target_user not in clients:
                            send_to_client(client_socket, "❌ Người nhận không trực tuyến.\n")
                            continue
                        if quantity < 1:
                            send_to_client(client_socket, "❌ Số lượng phải lớn hơn 0.\n")
                            continue
                        try:
                            if item_type == "pots":
                                cur.execute("SELECT pot_name, COUNT(*) FROM user_pots WHERE username=? AND stage=0 GROUP BY pot_name",
                                            (username,))
                                pots = cur.fetchall()
                                pot_name = parts[4].lower() if len(parts) > 4 else None
                                if not pot_name or pot_name not in available_pots:
                                    send_to_client(client_socket, f"❌ Chậu {pot_name} không tồn tại.\n")
                                    continue
                                total_pots = sum(count for _, count in pots if _ == pot_name)
                                if total_pots < quantity:
                                    send_to_client(client_socket, f"❌ Không đủ chậu {pot_name} (có {total_pots}).\n")
                                    continue
                                for _ in range(quantity):
                                    cur.execute("SELECT id FROM user_pots WHERE username=? AND pot_name=? AND stage=0 ORDER BY id ASC LIMIT 1",
                                                (username, pot_name))
                                    pot_id = cur.fetchone()
                                    if pot_id:
                                        cur.execute("UPDATE user_pots SET username=? WHERE id=?", (target_user, pot_id[0]))
                                conn.commit()
                                send_to_client(clients[username], f"🎁 Đã gửi {quantity} chậu {pot_name} cho {target_user}.\n")
                                send_to_client(clients[target_user], f"🎁 {username} đã gửi bạn {quantity} chậu {pot_name}.\n")
                                update_gui(f"[{username}] gửi {quantity} chậu {pot_name} cho {target_user}.")
                            elif item_type == "seeds":
                                plant_type = normalize_plant_type(parts[4]) if len(parts) > 4 else None
                                mature = 0
                                if not plant_type or plant_type not in plant_types:
                                    send_to_client(client_socket, f"❌ Loại hạt giống {plant_type} không tồn tại.\n")
                                    continue
                                cur.execute("SELECT quantity FROM user_seeds WHERE username=? AND plant_type=? AND mature=?", (username, plant_type, mature))
                                result = cur.fetchone()
                                if not result or result[0] < quantity:
                                    send_to_client(client_socket, f"❌ Không đủ hạt giống {plant_type} (có {result[0] if result else 0}).\n")
                                    continue
                                cur.execute("UPDATE user_seeds SET quantity=quantity-? WHERE username=? AND plant_type=? AND mature=?",
                                            (quantity, username, plant_type, mature))
                                cur.execute("SELECT quantity FROM user_seeds WHERE username=? AND plant_type=? AND mature=?",
                                            (target_user, plant_type, mature))
                                target_result = cur.fetchone()
                                if target_result:
                                    cur.execute("UPDATE user_seeds SET quantity=quantity+? WHERE username=? AND plant_type=? AND mature=?",
                                                (quantity, target_user, plant_type, mature))
                                else:
                                    cur.execute("INSERT INTO user_seeds (username, plant_type, quantity, mature) VALUES (?, ?, ?, ?)",
                                                (target_user, plant_type, quantity, mature))
                                conn.commit()
                                send_to_client(clients[username], f"🌱 Đã gửi {quantity} hạt giống {plant_type} cho {target_user}.\n")
                                send_to_client(clients[target_user], f"🌱 {username} đã gửi bạn {quantity} hạt giống {plant_type}.\n")
                                update_gui(f"[{username}] gửi {quantity} hạt giống {plant_type} cho {target_user}.")
                            elif item_type == "mature_seeds":
                                plant_type = normalize_plant_type(parts[4]) if len(parts) > 4 else None
                                mature = 1
                                if not plant_type or plant_type not in plant_types:
                                    send_to_client(client_socket, f"❌ Loại cây trưởng thành {plant_type} không tồn tại.\n")
                                    continue
                                cur.execute("SELECT quantity FROM user_seeds WHERE username=? AND plant_type=? AND mature=?", (username, plant_type, mature))
                                result = cur.fetchone()
                                if not result or result[0] < quantity:
                                    send_to_client(client_socket, f"❌ Không đủ {plant_type} Trưởng thành (có {result[0] if result else 0}).\n")
                                    continue
                                cur.execute("UPDATE user_seeds SET quantity=quantity-? WHERE username=? AND plant_type=? AND mature=?",
                                            (quantity, username, plant_type, mature))
                                cur.execute("SELECT quantity FROM user_seeds WHERE username=? AND plant_type=? AND mature=?",
                                            (target_user, plant_type, mature))
                                target_result = cur.fetchone()
                                if target_result:
                                    cur.execute("UPDATE user_seeds SET quantity=quantity+? WHERE username=? AND plant_type=? AND mature=?",
                                                (quantity, target_user, plant_type, mature))
                                else:
                                    cur.execute("INSERT INTO user_seeds (username, plant_type, quantity, mature) VALUES (?, ?, ?, ?)",
                                                (target_user, plant_type, quantity, mature))
                                conn.commit()
                                send_to_client(clients[username], f"🌳 Đã gửi {quantity} {plant_type} Trưởng thành cho {target_user}.\n")
                                send_to_client(clients[target_user], f"🌳 {username} đã gửi bạn {quantity} {plant_type} Trưởng thành.\n")
                                update_gui(f"[{username}] gửi {quantity} {plant_type} Trưởng thành cho {target_user}.")
                            else:
                                send_to_client(client_socket, "❌ Loại item không hợp lệ. Dùng: pots, seeds, mature_seeds.\n")
                        except Exception as e:
                            update_gui(f"[Lỗi /trade] {username}: {str(e)}")
                            send_to_client(client_socket, "❌ Lỗi khi trao đổi. Vui lòng thử lại.\n")
                    else:
                        send_to_client(client_socket, "❓ Vui lòng nhập: /trade <người nhận> <item> <số lượng> [tên item], ví dụ: /trade player2 pots 1 chaucoban hoặc /trade player2 seeds 2 Nuoc\n")

                elif data.startswith("/invite"):
                    parts = data.split()
                    if len(parts) == 2:
                        invitee = parts[1]
                        if invitee not in clients:
                            send_to_client(client_socket, "❌ Người được mời không trực tuyến.\n")
                            continue
                        if invitee == username:
                            send_to_client(client_socket, "❌ Không thể tự mời chính mình.\n")
                            continue
                        if invitee in coop_sessions:
                            send_to_client(client_socket, f"❌ {invitee} đã ở trong một phiên co-op.\n")
                            continue
                        try:
                            cur.execute("SELECT inviter FROM coop_invitations WHERE invitee=?", (invitee,))
                            if cur.fetchone():
                                send_to_client(client_socket, f"❌ {invitee} đã có lời mời từ người khác.\n")
                                continue
                            cur.execute("INSERT INTO coop_invitations (inviter, invitee) VALUES (?, ?)", (username, invitee))
                            conn.commit()
                            send_to_client(clients[username], f"📩 Đã gửi lời mời co-op đến {invitee}.\n")
                            send_to_client(clients[invitee], f"📩 {username} đã mời bạn làm đồng sở hữu đảo. Dùng /accept {username} để chấp nhận.\n")
                            update_gui(f"[{username}] gửi lời mời co-op đến {invitee}.")
                        except Exception as e:
                            update_gui(f"[Lỗi /invite] {username}: {str(e)}")
                            send_to_client(client_socket, "❌ Lỗi khi gửi lời mời. Vui lòng thử lại.\n")
                    else:
                        send_to_client(client_socket, "❓ Vui lòng nhập: /invite <tên người dùng>\n")

                elif data.startswith("/accept"):
                    parts = data.split()
                    if len(parts) == 2:
                        inviter = parts[1]
                        if inviter not in clients:
                            send_to_client(client_socket, "❌ Người mời không trực tuyến.\n")
                            continue
                        if username in coop_sessions:
                            send_to_client(client_socket, "❌ Bạn đã ở trong một phiên co-op. Dùng /leavecoop để rời.\n")
                            continue
                        try:
                            cur.execute("SELECT inviter FROM coop_invitations WHERE inviter=? AND invitee=?", (inviter, username))
                            result = cur.fetchone()
                            if not result:
                                send_to_client(client_socket, f"❌ Không tìm thấy lời mời từ {inviter}.\n")
                                continue
                            coop_sessions[username] = inviter
                            cur.execute("SELECT current_stage FROM users WHERE username=?", (inviter,))
                            stage = cur.fetchone()[0]
                            cur.execute("UPDATE users SET current_stage=? WHERE username=?", (stage, username))
                            cur.execute("DELETE FROM coop_invitations WHERE inviter=? AND invitee=?", (inviter, username))
                            conn.commit()
                            send_to_client(clients[username], f"🤝 Bạn đã tham gia chế độ co-op với {inviter}, sử dụng các tầng của họ!\n")
                            send_to_client(clients[inviter], f"🤝 {username} đã chấp nhận lời mời co-op!\n")
                            broadcast(f"💬 {username} đã tham gia co-op với {inviter}.\n")
                            update_gui(f"[Co-op] {username} chấp nhận lời mời từ {inviter}.")
                            send_status(username)
                        except Exception as e:
                            update_gui(f"[Lỗi /accept] {username}: {str(e)}")
                            send_to_client(client_socket, "❌ Lỗi khi chấp nhận lời mời. Vui lòng thử lại.\n")
                    else:
                        send_to_client(client_socket, "❓ Vui lòng nhập: /accept <tên người mời>\n")

                elif data.startswith("/setislandname"):
                    parts = data.split(maxsplit=1)
                    if len(parts) == 2:
                        island_name = parts[1].strip()
                        if len(island_name) > 50:
                            send_to_client(client_socket, "❌ Tên đảo không được dài quá 50 ký tự.\n")
                            continue
                        try:
                            cur.execute("UPDATE users SET island_name=? WHERE username=?", (island_name, username))
                            conn.commit()
                            send_to_client(client_socket, f"🏝️ Đã đặt tên đảo của bạn thành: {island_name}\n")
                            update_gui(f"[{username}] đặt tên đảo thành {island_name}.")
                            send_status(username)
                        except Exception as e:
                            update_gui(f"[Lỗi /setislandname] {username}: {str(e)}")
                            send_to_client(client_socket, "❌ Lỗi khi đặt tên đảo. Vui lòng thử lại.\n")
                    else:
                        send_to_client(client_socket, "❓ Vui lòng nhập: /setislandname <tên đảo>\n")

                elif data.startswith("/coopstatus"):
                    try:
                        coop_status = "Chủ sở hữu chính"
                        if username in coop_sessions:
                            inviter = coop_sessions[username]
                            cur.execute("SELECT island_name FROM users WHERE username=?", (inviter,))
                            island_name = cur.fetchone()[0]
                            coop_status = f"Đồng sở hữu đảo của {inviter}: {island_name}"
                        send_to_client(client_socket, f"🤝 Trạng thái: {coop_status}\n")
                    except Exception as e:
                        update_gui(f"[Lỗi /coopstatus] {username}: {str(e)}")
                        send_to_client(client_socket, "❌ Lỗi khi kiểm tra trạng thái. Vui lòng thử lại.\n")

                elif data.startswith("/leavecoop"):
                    if username not in coop_sessions:
                        send_to_client(client_socket, "❌ Bạn không ở trong chế độ co-op.\n")
                        continue
                    try:
                        inviter = coop_sessions.pop(username)
                        cur.execute("SELECT stages FROM users WHERE username=?", (username,))
                        stages = cur.fetchone()[0]
                        cur.execute("UPDATE users SET current_stage=? WHERE username=?", (stages, username))
                        conn.commit()
                        send_to_client(clients[username], f"👋 Bạn đã rời chế độ co-op với {inviter}.\n")
                        if inviter in clients:
                            send_to_client(clients[inviter], f"👋 {username} đã rời chế độ co-op.\n")
                        broadcast(f"💬 {username} đã rời chế độ co-op với {inviter}.\n")
                        update_gui(f"[Co-op] {username} rời chế độ co-op với {inviter}.")
                        send_status(username)
                    except Exception as e:
                        update_gui(f"[Lỗi /leavecoop] {username}: {str(e)}")
                        send_to_client(client_socket, "❌ Lỗi khi rời co-op. Vui lòng thử lại.\n")

                elif data.startswith("/chochau") and username == "ADMIN":
                    parts = data.split()
                    if len(parts) >= 3:
                        target_user, pot_name = parts[1], parts[2].lower()
                        if target_user in clients and pot_name in available_pots:
                            try:
                                cur.execute("INSERT INTO user_pots (username, pot_name, stage) VALUES (?, ?, 0)", (target_user, pot_name))
                                conn.commit()
                                send_to_client(clients[target_user], f"🎁 Admin đã tặng bạn chậu {pot_name}!\n")
                                send_to_client(client_socket, f"🎁 Đã tặng chậu {pot_name} cho {target_user}.\n")
                                update_gui(f"[ADMIN] {username} tặng chậu {pot_name} cho {target_user}.")
                            except Exception as e:
                                update_gui(f"[Lỗi /chochau] {username}: {str(e)}")
                                send_to_client(client_socket, "❌ Lỗi khi tặng chậu. Vui lòng thử lại.\n")
                        else:
                            send_to_client(client_socket, "❌ Người dùng hoặc chậu không tồn tại.\n")
                    else:
                        send_to_client(client_socket, "❓ Vui lòng nhập: /chochau <user> <tên chậu>\n")

                elif data.startswith("/giveseed") and username == "ADMIN":
                    parts = data.split()
                    if len(parts) >= 4 and parts[3].isdigit():
                        target_user, plant_type, quantity = parts[1], normalize_plant_type(parts[2]), int(parts[3])
                        mature = 1 if len(parts) == 5 and parts[4].lower() == "mature" else 0
                        if target_user in clients and plant_type in plant_types and quantity > 0:
                            try:
                                cur.execute("SELECT quantity FROM user_seeds WHERE username=? AND plant_type=? AND mature=?", (target_user, plant_type, mature))
                                result = cur.fetchone()
                                if result:
                                    cur.execute("UPDATE user_seeds SET quantity=quantity+? WHERE username=? AND plant_type=? AND mature=?", (quantity, target_user, plant_type, mature))
                                else:
                                    cur.execute("INSERT INTO user_seeds (username, plant_type, quantity, mature) VALUES (?, ?, ?, ?)", (target_user, plant_type, quantity, mature))
                                conn.commit()
                                item_name = f"{plant_type} {'Trưởng thành' if mature else ''}"
                                send_to_client(clients[target_user], f"🎁 Admin đã tặng bạn {quantity} {item_name}!\n")
                                send_to_client(client_socket, f"🎁 Đã tặng {quantity} {item_name} cho {target_user}.\n")
                                update_gui(f"[ADMIN] {username} tặng {quantity} {item_name} cho {target_user}.")
                            except Exception as e:
                                update_gui(f"[Lỗi /giveseed] {username}: {str(e)}")
                                send_to_client(client_socket, "❌ Lỗi khi tặng hạt giống hoặc cây trưởng thành. Vui lòng thử lại.\n")
                        else:
                            send_to_client(client_socket, f"❌ Người dùng, loại cây không hợp lệ hoặc số lượng phải > 0. Chọn: {', '.join(plant_types)}\n")
                    else:
                        send_to_client(client_socket, "❓ Vui lòng nhập: /giveseed <user> <loại cây> <số lượng> [mature], ví dụ: /giveseed player1 Nuoc 3 mature\n")

                elif data.startswith("/addmoney") and username == "ADMIN":
                    parts = data.split()
                    if len(parts) >= 3 and parts[2].isdigit():
                        target_user, amount = parts[1], int(parts[2])
                        if target_user in clients:
                            try:
                                cur.execute("UPDATE users SET money=money+? WHERE username=?", (amount, target_user))
                                conn.commit()
                                send_to_client(clients[target_user], f"🎁 Admin đã cộng {amount} xu vào tài khoản của bạn!\n")
                                send_to_client(client_socket, f"🎁 Đã cộng {amount} xu cho {target_user}.\n")
                                update_gui(f"[ADMIN] {username} cộng {amount} xu cho {target_user}.")
                                send_status(target_user)
                            except Exception as e:
                                update_gui(f"[Lỗi /addmoney] {username}: {str(e)}")
                                send_to_client(client_socket, "❌ Lỗi khi cộng tiền. Vui lòng thử lại.\n")
                        else:
                            send_to_client(client_socket, "❌ Người dùng không tồnبیat.\n")
                    else:
                        send_to_client(client_socket, "❓ Vui lòng nhập: /addmoney <user> <số tiền>\n")

                elif data == "/check_session":
                    with lock:
                        if username in clients:
                            try:
                                clients[username].send(b"")  # Kiểm tra socket
                                send_to_client(client_socket, "Phiên đang hoạt động\n")
                            except (ConnectionError, OSError):
                                clients.pop(username, None)
                                send_to_client(client_socket, "Phiên cũ đã hết, bạn có thể tiếp tục\n")
                                clients[username] = client_socket
                        else:
                            send_to_client(client_socket, "Không có phiên hiện tại\n")
                            clients[username] = client_socket

                elif data.startswith("/setstage") and username == "ADMIN":
                    parts = data.split()
                    if len(parts) >= 3 and parts[2].isdigit():
                        target_user, stage = parts[1], int(parts[2])
                        if target_user in clients:
                            try:
                                cur.execute("UPDATE users SET stages=?, current_stage=? WHERE username=?", (stage, stage, target_user))
                                conn.commit()
                                send_to_client(clients[target_user], f"🏢 Admin đã đặt số tầng của bạn thành {stage}!\n")
                                send_to_client(client_socket, f"🏢 Đã đặt số tầng của {target_user} thành {stage}.\n")
                                update_gui(f"[ADMIN] {username} đặt số tầng của {target_user} thành {stage}.")
                                send_status(target_user)
                            except Exception as e:
                                update_gui(f"[Lỗi /setstage] {username}: {str(e)}")
                                send_to_client(client_socket, "❌ Lỗi khi đặt số tầng. Vui lòng thử lại.\n")
                        else:
                            send_to_client(client_socket, "❌ Người dùng không tồn tại.\n")
                    else:
                        send_to_client(client_socket, "❓ Vui lòng nhập: /setstage <user> <số tầng>\n")

                else:
                    send_to_client(client_socket, f"❓ Lệnh không hợp lệ. Dùng: /join, /status, /chat, /stage, /buystage, /datchau, /xoachau, /pots, /balo, /buypot, /buyseed, /plant, /thuhoach, /sell, /lai, /trade, /invite, /accept, /setislandname, /coopstatus, /leavecoop\n")

            except Exception as e:
                update_gui(f"[Lỗi xử lý lệnh] {username}: {str(e)}")
                send_to_client(client_socket, "❌ Lỗi khi xử lý lệnh. Vui lòng thử lại.\n")

    except Exception as e:
        update_gui(f"[!] Lỗi từ {username if username else '???'}: {str(e)}")
    finally:
        if username:
            update_gui(f"[-] {username} đã ngắt kết nối.")
            for invitee, inviter in list(coop_sessions.items()):
                if inviter == username:
                    coop_sessions.pop(invitee, None)
                    update_gui(f"[Co-op] Kết thúc co-op của {invitee} do {username} ngắt kết nối.")
                    broadcast(f"💬 Đồng sở hữu {invitee} bị ngắt kết nối khỏi đảo của {username}.\n")
                    cur.execute("SELECT stages FROM users WHERE username=?", (invitee,))
                    stages = cur.fetchone()[0]
                    cur.execute("UPDATE users SET current_stage=? WHERE username=?", (stages, invitee))
                    conn.commit()
                    if invitee in clients:
                        send_to_client(clients[invitee], f"👋 Bạn đã bị ngắt kết nối khỏi đảo của {username} do họ rời game.\n")
                        send_status(invitee)
            clients.pop(username, None)
            update_online_count()
            broadcast(f"💬 {username} đã rời game.\n")
        client_socket.close()
def check_inactive_clients():
    while True:
        with lock:
            for username, sock in list(clients.items()):
                try:
                    sock.send(b"")  # Ping để kiểm tra
                except (ConnectionError, OSError):
                    clients.pop(username, None)
                    update_gui(f"[Debug] Xóa {username} do không hoạt động")
                    broadcast(f"💬 {username} đã rời game do mất kết nối.\n")
        time.sleep(30)
threading.Thread(target=check_inactive_clients, daemon=True).start()
def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()
    update_gui(f"Đang lắng nghe tại {HOST}:{PORT}...")
    while True:
        client_socket, addr = server.accept()
        update_gui(f"[Kết nối mới] Từ {addr}")
        threading.Thread(target=handle_client, args=(client_socket,), daemon=True).start()

threading.Thread(target=start_server, daemon=True).start()
root.mainloop()