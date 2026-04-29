# **Musician 2.0**

## **A Professional Command-Line Music Player & Library Manager**

**Code by _aaaaa_**

**Musician 2.0** is a command-line-controlled music player designed for coders and power users. It goes beyond simple playback, offering NetEase cache decryption, Kugou downloads, a dynamic tagging system, and a highly customizable CLI experience.

---

## **1. Installation & Setup**

### **Installation**
1. Run the `Musician_Installer.exe`.
2. **Program Path**: Where `musician.exe` resides.
3. **BGM Data Path**: Where your music library, tags, and settings are stored.
   * *Note: The installer automatically configures your `settings.json` paths.*

### **First-Time Configuration**
Open Musician and use the `set` command to configure your NetEase cache path:
`>> set netease_cache C:\Users\YourName\AppData\Local\Netease\CloudMusic\Cache\Cache`

---

## **2. Command Reference**

### **General Commands**
| Command | Shortcut | Action |
| :--- | :--- | :--- |
| `quit` / `exit` | `:q` | Safely exit the program. |
| `help` | `:h` | Show all available commands. |
| `set` | | View or modify configuration (e.g., `set volume 0.5`). |
| `common` | | Manage/view common commands. Use **Up/Down arrows** to select. |
| `history` | `:his` | View listening history. |
| `?` | `:?` | Show current song info. |

### **Music Sources (Downloads & Decryption)**
#### **NetEase Cloud Music (163)**
*   `check163` (`:163_cache`): List your current NetEase desktop cache.
*   `decode <#>` (`:d <#>`): Decrypt specific songs (e.g., `decode 1-3 5`).
*   `clear163` (`:163_clear`): Clear NetEase cache folder.

#### **Kugou Music**
*   `search <name>` (`/s <name>`): Search songs on Kugou.
*   `download <#>` (`/d <#>`): Download from search results.

#### **Savelist Management**
*   `savelist` (`:sl`): Show recently downloaded/decrypted songs.
*   `save <tags>` (`:s <tags>`): Move songs to library and apply tags (e.g., `save pop rock`).
*   `clear` (`:cl`): Clear the current savelist.

### **Playback Controls**
*   `play` (`:p`): Toggle Play/Pause.
*   `play <#>`: Play songs by index from current list.
*   `play <tag>`: Play all songs associated with a tag.
*   `stop` (`:st`): Stop playback.
*   `next` (`:n`) / `last` (`:prev`): Skip tracks.
*   `restart` (`:r`): Replay current song.
*   `volume <0-100>` (`:vol`): Set volume.
*   `mode <s/c/r>` (`:m`): Set mode (Single/Cycle/Random).

### **Tag & Library Management**
Musician 2.0 uses a **Tag System** instead of folders.
*   `library` (`:lib`): Browse your entire local BGM collection.
*   `lookup <name>` (`:lu`): Search for a song in your library.
*   `tag`: List all tags and song counts.
*   `tag <name>`: List songs under a specific tag.
*   `tag -a <tag> <#>`: Add a tag to songs (e.g., `tag -a gym 1-5`).
*   `tag -d <tag>`: Delete a tag from the system.
*   `tag -d <tag> <#>`: Remove a tag from specific songs.

---

## **3. Advanced Features**

### **Command Chaining (Flags)**
The `play` command now supports flags to save time:
*   `play -m s`: Switch to single-cycle and start.
*   `play -v 40`: Play and set volume to 40%.
*   `play -t 60`: Play and set a 60-minute sleep timer.
*   *Example:* `play 1-10 -m r -v 30` (Play songs 1-10 randomly at 30% volume).

### **Smart Timelimit**
*   `timelimit <min>`: Stop after X minutes.
*   `timelimit <HH:MM>`: Stop at a specific time (e.g., `timelimit 23:30`).

### **In-App Help**
Add `-h` after any command to see its specific usage:
`>> tag -h`

---

## **4. File Structure**
```
BGM/
├── Download&Decode/   # Temp folder for processing
├── Settings/          # history.txt, tags.json, common_commands.json
└── (Music Files)      # Your .mp3 library
```

---

**Enjoy your journey with Musician 2.0!** 🎵
