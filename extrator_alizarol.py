import os
import cv2
import math
import glob
import numpy as np
import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk

class AlizarolQCApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Controle de Qualidade - Extração Alizarol")
        self.root.geometry("1200x800")
        
        print("[DEBUG] Iniciando o aplicativo de Controle de Qualidade...")
        
        self.image_paths = []
        self.current_idx = 0
        self.original_img = None
        self.display_img = None
        self.eraser_mask = None
        self.scale_factor = 1.0
        
        self.cx = 400
        self.cy = 500
        self.radius = 100
        
        # Variáveis do painel
        self.var_cx = tk.StringVar(self.root)
        self.var_cy = tk.StringVar(self.root)
        self.var_r = tk.StringVar(self.root)
        self.var_eraser = tk.IntVar(self.root, value=15)
        self.lock_circle = tk.BooleanVar(self.root, value=True)
        
        self.setup_ui()
        self.load_folder()

    def setup_ui(self):
        print("[DEBUG] Montando a interface gráfica...")
        
        top_frame = tk.Frame(self.root, bg="#222", pady=10)
        top_frame.pack(fill=tk.X)
        
        self.info_label = tk.Label(top_frame, text="Carregando...", fg="#00FF00", bg="#222", font=("Arial", 16, "bold"))
        self.info_label.pack()
        
        main_frame = tk.Frame(self.root, bg="#333")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        left_frame = tk.Frame(main_frame, bg="black")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(left_frame, cursor="crosshair", bg="black")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Bindings do Mouse
        self.canvas.bind("<B1-Motion>", self.erase_pixels)
        self.canvas.bind("<Button-1>", self.erase_pixels)
        self.canvas.bind("<B3-Motion>", self.restore_pixels)
        self.canvas.bind("<Button-3>", self.restore_pixels)
        
        # Bind do botão Espaço para salvar (não conflita com digitar nas caixas)
        self.root.bind("<space>", lambda e: self.save_and_next())
        
        right_frame = tk.Frame(main_frame, bg="#444", width=300, padx=15, pady=20)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y)
        
        tk.Label(right_frame, text="PARÂMETROS DO CÍRCULO", fg="white", bg="#444", font=("Arial", 11, "bold")).pack(pady=(0,10))
        
        # Caixas com fundo branco para evitar sumiço do cursor
        tk.Label(right_frame, text="Centro X (CX):", fg="white", bg="#444").pack(anchor=tk.W)
        tk.Entry(right_frame, textvariable=self.var_cx, font=("Arial", 14), bg="white", fg="black").pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(right_frame, text="Centro Y (CY):", fg="white", bg="#444").pack(anchor=tk.W)
        tk.Entry(right_frame, textvariable=self.var_cy, font=("Arial", 14), bg="white", fg="black").pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(right_frame, text="Raio (R):", fg="white", bg="#444").pack(anchor=tk.W)
        tk.Entry(right_frame, textvariable=self.var_r, font=("Arial", 14), bg="white", fg="black").pack(fill=tk.X, pady=(0, 20))
        
        tk.Button(right_frame, text="Atualizar Círculo Manualmente", bg="#0066cc", fg="white", font=("Arial", 10, "bold"), 
                  command=self.apply_manual_circle).pack(fill=tk.X, pady=(0, 10))
                  
        # Checkbox para Travar Posição
        tk.Checkbutton(right_frame, text="Travar Posição para as próximas", variable=self.lock_circle, 
                       bg="#444", fg="white", selectcolor="#222", activebackground="#444", activeforeground="white").pack(anchor=tk.W, pady=(0, 30))
        
        tk.Label(right_frame, text="FERRAMENTAS", fg="white", bg="#444", font=("Arial", 11, "bold")).pack(pady=(0,10))
        tk.Label(right_frame, text="Tamanho da Borracha:", fg="white", bg="#444").pack(anchor=tk.W)
        tk.Scale(right_frame, from_=1, to=100, orient=tk.HORIZONTAL, variable=self.var_eraser, bg="#444", fg="white", highlightthickness=0).pack(fill=tk.X, pady=(0, 5))
        
        tk.Label(right_frame, text="Botão Esq: Apaga | Botão Dir: Restaura", fg="#aaa", bg="#444", font=("Arial", 8)).pack(pady=(0,30))
        
        tk.Button(right_frame, text="SALVAR E PRÓXIMA [ ESPAÇO ]", bg="#28a745", fg="white", font=("Arial", 12, "bold"), height=2,
                  command=self.save_and_next).pack(fill=tk.X, side=tk.BOTTOM, pady=20)

    def load_folder(self):
        folder_path = filedialog.askdirectory(title="Selecione a pasta com as imagens")
        if not folder_path:
            print("[DEBUG] Nenhuma pasta selecionada. Encerrando.")
            self.root.quit()
            return
            
        print(f"[DEBUG] Pasta selecionada: {folder_path}")
        self.csv_path = os.path.join(folder_path, "resultados_alizarol.csv")
        
        exts = ["*.jpg", "*.jpeg", "*.png"]
        for ext in exts:
            self.image_paths.extend(glob.glob(os.path.join(folder_path, ext)))
            self.image_paths.extend(glob.glob(os.path.join(folder_path, ext.upper())))
            
        if not self.image_paths:
            messagebox.showerror("Erro", "Nenhuma imagem encontrada na pasta.")
            return
            
        print(f"[DEBUG] Total de imagens encontradas: {len(self.image_paths)}")
        self.load_image()

    def load_image(self):
        if self.current_idx >= len(self.image_paths):
            print("[DEBUG] Fim da lista de imagens. Processo concluído.")
            messagebox.showinfo("Fim", f"Concluído! CSV em:\n{self.csv_path}")
            self.root.quit()
            return
            
        path = self.image_paths[self.current_idx]
        print(f"\n[DEBUG] --- Carregando imagem {self.current_idx + 1}: {os.path.basename(path)} ---")
        self.original_img = cv2.imread(path)
        
        h, w = self.original_img.shape[:2]
        max_height = 700
        if h > max_height:
            self.scale_factor = max_height / h
            new_w = int(w * self.scale_factor)
            self.display_img = cv2.resize(self.original_img, (new_w, max_height))
        else:
            self.scale_factor = 1.0
            self.display_img = self.original_img.copy()

        # Verifica se o usuário pediu para travar o círculo
        if not self.lock_circle.get():
            print("[DEBUG] Posicionando círculo no centro padrão.")
            self.cx = self.display_img.shape[1] // 2
            self.cy = self.display_img.shape[0] // 2
            self.radius = int(100 * self.scale_factor) if self.scale_factor < 1 else 150
        else:
            print("[DEBUG] Círculo travado! Mantendo coordenadas anteriores.")

        self.sync_real_values_to_ui()
        
        # Limpa a borracha para a nova foto
        self.eraser_mask = np.ones(self.display_img.shape[:2], dtype=np.uint8) * 255
        
        self.update_view()

    def sync_real_values_to_ui(self):
        real_cx = int(self.cx / self.scale_factor)
        real_cy = int(self.cy / self.scale_factor)
        real_r = int(self.radius / self.scale_factor)
        
        self.var_cx.set(str(real_cx))
        self.var_cy.set(str(real_cy))
        self.var_r.set(str(real_r))

    def apply_manual_circle(self):
        print("[DEBUG] Botão Atualizar Círculo pressionado.")
        try:
            real_cx = int(self.var_cx.get())
            real_cy = int(self.var_cy.get())
            real_r = int(self.var_r.get())
            
            print(f"[DEBUG] Coordenadas Reais Digitadas - CX: {real_cx}, CY: {real_cy}, R: {real_r}")
            
            self.cx = int(real_cx * self.scale_factor)
            self.cy = int(real_cy * self.scale_factor)
            self.radius = int(real_r * self.scale_factor)
            
            self.update_view()
        except ValueError:
            print("[DEBUG] Erro: O usuário digitou texto em vez de números nas caixas.")
            messagebox.showerror("Erro", "Digite apenas números inteiros válidos nos campos.")

    def erase_pixels(self, event):
        cv2.circle(self.eraser_mask, (event.x, event.y), self.var_eraser.get(), 0, -1)
        self.update_view()

    def restore_pixels(self, event):
        cv2.circle(self.eraser_mask, (event.x, event.y), self.var_eraser.get(), 255, -1)
        self.update_view()

    def calculate_math(self):
        circle_mask = np.zeros(self.display_img.shape[:2], dtype=np.uint8)
        cv2.circle(circle_mask, (self.cx, self.cy), self.radius, 255, -1)
        
        # Tira a linha verde fixa
        x_inicio = self.cx - 1
        x_fim = self.cx + 1
        y_inicio = max(0, self.cy - self.radius)
        y_fim = self.cy
        cv2.rectangle(circle_mask, (x_inicio, y_inicio), (x_fim, y_fim), 0, -1)
        
        final_mask = cv2.bitwise_and(circle_mask, self.eraser_mask)
        
        hsv_img = cv2.cvtColor(self.display_img, cv2.COLOR_BGR2HSV)
        valid_pixels = hsv_img[final_mask == 255]
        
        if len(valid_pixels) == 0:
            print("[DEBUG] Cuidado! Nenhum pixel válido no círculo atual.")
            return 0.0, final_mask
            
        hues = valid_pixels[:, 0] * 2.0 
        rads = hues * np.pi / 180.0
        sum_sin = np.sum(np.sin(rads))
        sum_cos = np.sum(np.cos(rads))
        
        return math.atan2(sum_sin, sum_cos), final_mask

    def update_view(self):
        mean_angle_rad, final_mask = self.calculate_math()
        img_show = self.display_img.copy()
        
        erased = (self.eraser_mask == 0)
        img_show[erased] = [0, 0, 255]
        
        x_inicio = self.cx - 1
        x_fim = self.cx + 1
        y_inicio = max(0, self.cy - self.radius)
        y_fim = self.cy
        cv2.rectangle(img_show, (x_inicio, y_inicio), (x_fim, y_fim), (255, 150, 0), -1)
        
        cv2.circle(img_show, (self.cx, self.cy), self.radius, (0, 255, 0), 2)
        
        file_name = os.path.basename(self.image_paths[self.current_idx])
        progress = f"[{self.current_idx + 1}/{len(self.image_paths)}]"
        self.info_label.config(text=f"{progress} {file_name}   |   RADIANO: {mean_angle_rad:.4f}")
        
        img_rgb = cv2.cvtColor(img_show, cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(img_rgb)
        self.tk_image = ImageTk.PhotoImage(img_pil)
        
        self.canvas.config(width=img_show.shape[1], height=img_show.shape[0])
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)
        self.current_mean_rad = mean_angle_rad

    def save_and_next(self):
        file_name = os.path.basename(self.image_paths[self.current_idx])
        print(f"[DEBUG] Salvando foto {file_name} com Radiano {self.current_mean_rad:.4f}")
        
        df = pd.DataFrame([[file_name, self.current_mean_rad]], columns=["Nome_Arquivo", "Angulo_Rad"])
        if not os.path.isfile(self.csv_path):
            df.to_csv(self.csv_path, index=False)
        else:
            df.to_csv(self.csv_path, mode='a', header=False, index=False)
            
        self.current_idx += 1
        self.load_image()

if __name__ == "__main__":
    root = tk.Tk()
    app = AlizarolQCApp(root)
    root.mainloop()