import customtkinter
from repetiscan.gui import SimilarityApp

if __name__ == "__main__":
    root = customtkinter.CTk()
    app = SimilarityApp(root)
    root.mainloop()