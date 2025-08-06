import os
from CTkMessagebox import CTkMessagebox
from repetiscan.language import t
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3
import difflib
from repetiscan.blacklist import clean_title

def get_mp3_titles(folder):
    songs = []
    for filename in os.listdir(folder):
        if filename.lower().endswith('.mp3'):
            filepath = os.path.join(folder, filename)
            try:
                audio = MP3(filepath, ID3=EasyID3)
                title = audio.get("title", [os.path.splitext(filename)[0]])[0]
                artist = audio.get("artist", [""])[0]
                songs.append((title, filepath, artist))
            except Exception as e:
                print(f"Error leyendo {filename}: {e}")
    return songs

def group_songs_by_title(songs):
    grouped = {}
    for title, path, artist in songs:
        if title not in grouped:
            grouped[title] = []
        grouped[title].append((title, path, artist))
    return list(grouped.values())

def find_similar_groups_by_ratio(songs, threshold, blacklist):
    groups = []
    seen = set()
    for i in range(len(songs)):
        title_i, file_i, artist_i = songs[i]
        if file_i in seen:
            continue
        group = [(title_i, file_i, artist_i)]
        seen.add(file_i)
        clean_i = clean_title(title_i, blacklist)
        for j in range(i+1, len(songs)):
            title_j, file_j, artist_j = songs[j]
            if file_j in seen:
                continue
            clean_j = clean_title(title_j, blacklist)
            similarity = difflib.SequenceMatcher(None, clean_i, clean_j).ratio()
            if similarity >= threshold:
                group.append((title_j, file_j, artist_j))
                seen.add(file_j)
        if len(group) > 1:
            groups.append(group)
    return groups

def find_similar_groups_by_words(songs, min_overlap, blacklist):
    groups = []
    seen = set()
    for i in range(len(songs)):
        title_i, file_i, artist_i = songs[i]
        if file_i in seen:
            continue
        group = [(title_i, file_i, artist_i)]
        words_i = set(clean_title(title_i, blacklist).split())
        seen.add(file_i)
        for j in range(i+1, len(songs)):
            title_j, file_j, artist_j = songs[j]
            if file_j in seen:
                continue
            words_j = set(clean_title(title_j, blacklist).split())
            if len(words_i & words_j) >= min_overlap:
                group.append((title_j, file_j, artist_j))
                seen.add(file_j)
        if len(group) > 1:
            groups.append(group)
    return groups

def analyze_by_ratio(self):
    self.current_mode = "ratio"
    if not self.folder:
        CTkMessagebox(title="Error", message=t("folder_error", self.lang, self.translations), icon="warning")
        return
    songs = get_mp3_titles(self.folder)
    self.groups = find_similar_groups_by_ratio(songs, self.threshold.get(), self.blacklist)
    self.show_groups_in_tree(self.groups)

def analyze_by_words(self):
    self.current_mode = "words"
    if not self.folder:
        CTkMessagebox(title="Error", message=t("folder_error", self.lang, self.translations), icon="warning")
        return
    songs = get_mp3_titles(self.folder)
    self.groups = find_similar_groups_by_words(songs, self.min_overlap.get(), self.blacklist)
    self.show_groups_in_tree(self.groups)

def analyze_excluding_artist(self):
    self.current_mode = "not_artist"
    if not self.folder:
        CTkMessagebox(title="Error", message=t("folder_error", self.lang, self.translations), icon="warning")
        return
    songs = get_mp3_titles(self.folder)
    songs = [s for s in songs if self.excluded_artist.get().strip().lower() not in (s[2] or '').lower()]
    self.groups = group_songs_by_title(songs)
    # Formatear mostrando artista
    self.show_groups_in_tree(self.groups, formatter=lambda group: ",  ".join([f"{t} ({a})" for t, _, a in group]))