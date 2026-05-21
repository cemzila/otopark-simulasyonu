import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
import numpy as np
import skfuzzy as fuzz
import skfuzzy.control as ctrl
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Tema
CTK_LAVENDER_MAIN = "#927bb1"       # Buton ve aktif elementlerin ana rengi
CTK_LAVENDER_HOVER = "#79619b"      # Üzerine gelindiğinde tetiklenen koyu lavanta
CTK_LAVENDER_LIGHT_BG = "#f2f0f5"   # Light mod arka planı
CTK_LAVENDER_DARK_BG = "#1a1620"    # Dark mod ana pencere arka planı
CTK_LAVENDER_DARK_SUB = "#25202e"   # İç panellerin (Frame) koyu lavanta tonu
CTK_LAVENDER_TEXT = "#e1dde6"       # Yazıların okunabilir kalması için açık gri-lavanta

# CustomTkinter görünüm modu ayarı
ctk.set_appearance_mode("dark") 

class FuzzyParkApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Park Yeri Bulma İhtimali Bulucu")
        self.root.geometry("1240x980") 
        self.root.configure(fg_color=CTK_LAVENDER_DARK_BG)
        
        try:
            icon = tk.PhotoImage(file='araba.png')
            root.iconphoto(False, icon)
        except Exception:
            pass 

        # Bulanık Mantık Parametreleri 
        self.bounds = {
            'saat_sakin': [0, 0, 7, 9],
            'saat_normal': [8, 10, 16, 24],
            'saat_yogun': [16, 18, 20],
            'yer_az': [0, 0, 20],
            'yer_orta': [15, 50, 70],
            'yer_cok': [60, 80, 100, 100]
        }

        # Kurallar
        self.kurallar = {
            0: "K1: HAFTA İÇİ + SAKİN saat + BOL yer -> YÜKSEK",
            1: "K2: HAFTA İÇİ + SAKİN saat + ORTA yer -> YÜKSEK",
            2: "K3: HAFTA İÇİ + NORMAL saat + ORTA yer -> ORTA",
            3: "K4: HAFTA İÇİ + NORMAL saat + AZ yer -> DÜŞÜK",
            4: "K5: HAFTA İÇİ + YOĞUN saat + AZ yer -> DÜŞÜK",
            5: "K6: HAFTA İÇİ + YOĞUN saat + ORTA yer -> DÜŞÜK",
            6: "K7: HAFTA SONU + SAKİN saat + BOL yer -> YÜKSEK",
            7: "K8: HAFTA SONU + SAKİN saat + ORTA yer -> ORTA",
            8: "K9: HAFTA SONU + NORMAL saat + BOL yer -> YÜKSEK",
            9: "K10: HAFTA SONU + NORMAL saat + ORTA yer -> DÜŞÜK",
            10: "K11: HAFTA SONU + NORMAL saat + AZ yer -> DÜŞÜK",
            11: "K12: HAFTA SONU + YOĞUN saat + AZ yer -> DÜŞÜK",
            12: "K13: SAKİN saatte yer AZ bile olsa sirkülasyon -> ORTA",
            13: "K14: Her durumda otoparkta ÇOK yer varsa -> YÜKSEK",
            14: "K15: YOĞUN saatte yer AZ ise kesinlikle -> DÜŞÜK"
        }

        self.create_widgets()
        self.hesapla_ve_ciz()

    def create_widgets(self):
        # Sol Panel
        self.control_frame = ctk.CTkFrame(self.root, width=450, height=940, fg_color=CTK_LAVENDER_DARK_SUB, corner_radius=15)
        self.control_frame.place(x=20, y=20)

        # Başlık 
        title_lbl = ctk.CTkLabel(self.control_frame, text="PARK SİMÜLASYONU", font=("Helvetica", 18, "bold"), text_color=CTK_LAVENDER_MAIN)
        title_lbl.pack(pady=15)

        # Giriş Sürgüleri
        input_group = ctk.CTkFrame(self.control_frame, fg_color="transparent")
        input_group.pack(fill="x", padx=20, pady=5)

        # Gün Sürgüsü
        self.day_title = ctk.CTkLabel(input_group, text="Haftanın Günü: Pazartesi (0)", font=("Helvetica", 12), text_color=CTK_LAVENDER_TEXT)
        self.day_title.pack(anchor="w", pady=(5,0))
        self.slider_day = ctk.CTkSlider(input_group, from_=0, to=6, number_of_steps=6, button_color=CTK_LAVENDER_MAIN, button_hover_color=CTK_LAVENDER_HOVER, progress_color=CTK_LAVENDER_MAIN, command=self.update_labels)
        self.slider_day.set(0)
        self.slider_day.pack(fill="x", pady=(0,10))

        # Saat Sürgüsü
        self.time_title = ctk.CTkLabel(input_group, text="Saat: 12.0", font=("Helvetica", 12), text_color=CTK_LAVENDER_TEXT)
        self.time_title.pack(anchor="w")
        self.slider_time = ctk.CTkSlider(input_group, from_=0, to=24, button_color=CTK_LAVENDER_MAIN, button_hover_color=CTK_LAVENDER_HOVER, progress_color=CTK_LAVENDER_MAIN, command=self.update_labels)
        self.slider_time.set(12.0)
        self.slider_time.pack(fill="x", pady=(0,10))

        # Boş Yer Sürgüsü
        self.space_title = ctk.CTkLabel(input_group, text="Otoparktaki Boş Yer Sayısı: 50", font=("Helvetica", 12), text_color=CTK_LAVENDER_TEXT)
        self.space_title.pack(anchor="w")
        self.slider_space = ctk.CTkSlider(input_group, from_=0, to=100, number_of_steps=100, button_color=CTK_LAVENDER_MAIN, button_hover_color=CTK_LAVENDER_HOVER, progress_color=CTK_LAVENDER_MAIN, command=self.update_labels)
        self.slider_space.set(50)
        self.slider_space.pack(fill="x", pady=(0,10))

        # Sınır Ayarları
        settings_group = ctk.CTkFrame(self.control_frame, fg_color="#2f293b", corner_radius=10)
        settings_group.pack(fill="x", padx=20, pady=5)

        ctk.CTkLabel(settings_group, text="Yoğun Saat Merkez Değeri:", font=("Helvetica", 11), text_color=CTK_LAVENDER_TEXT).grid(row=0, column=0, sticky="w", pady=(8, 2), padx=(10, 5))
        self.entry_yogun_saat = ctk.CTkEntry(settings_group, width=65, height=22, fg_color=CTK_LAVENDER_DARK_BG, border_color=CTK_LAVENDER_MAIN, text_color=CTK_LAVENDER_TEXT)
        self.entry_yogun_saat.insert(0, "18")
        self.entry_yogun_saat.grid(row=0, column=1, pady=(8, 2), padx=(5, 10))

        ctk.CTkLabel(settings_group, text="Maks. 'AZ' Yer Sınırı:", font=("Helvetica", 11), text_color=CTK_LAVENDER_TEXT).grid(row=1, column=0, sticky="w", pady=2, padx=(10, 5))
        self.entry_yer_az = ctk.CTkEntry(settings_group, width=65, height=22, fg_color=CTK_LAVENDER_DARK_BG, border_color=CTK_LAVENDER_MAIN, text_color=CTK_LAVENDER_TEXT)
        self.entry_yer_az.insert(0, "20")
        self.entry_yer_az.grid(row=1, column=1, pady=2, padx=(5, 10))

        btn_update = ctk.CTkButton(settings_group, text="Sınırları Güncelle", font=("Helvetica", 10, "bold"), fg_color=CTK_LAVENDER_MAIN, hover_color=CTK_LAVENDER_HOVER, text_color=CTK_LAVENDER_DARK_BG, height=24, command=self.ayarlari_guncelle)
        btn_update.grid(row=2, column=0, columnspan=2, pady=(8, 8), padx=10, sticky="ew")

        # Sonuç Ekranı ve Dinamik Kurallar
        self.result_frame = ctk.CTkFrame(self.control_frame, fg_color=CTK_LAVENDER_DARK_BG, corner_radius=10)
        self.result_frame.pack(fill="both", expand=True, padx=20, pady=(5,15))

        self.lbl_result = ctk.CTkLabel(self.result_frame, text="Mekanizma Tetikleniyor...", font=("Helvetica", 13, "bold"), text_color=CTK_LAVENDER_MAIN)
        self.lbl_result.pack(pady=(8, 2))

        # Aktif Kurallar Başlığı
        ctk.CTkLabel(self.result_frame, text="Aktif Kurallar", font=("Helvetica", 11), text_color="#a8dadc").pack()

        # Kurallar için Canlı Liste Kutusu
        self.rules_listbox = tk.Listbox(self.result_frame, font=("Helvetica", 9), bg=CTK_LAVENDER_DARK_SUB, fg=CTK_LAVENDER_TEXT, bd=0, highlightthickness=0, selectbackground=CTK_LAVENDER_MAIN, selectforeground=CTK_LAVENDER_DARK_BG)
        self.rules_listbox.pack(fill="both", expand=True, padx=10, pady=(5, 5))
        
        # Diğer sekmeyi açacak olan buton
        btn_all_rules = ctk.CTkButton(self.result_frame, text="Tüm Kural Listesi", font=("Helvetica", 10, "bold"), fg_color="#3d354b", hover_color=CTK_LAVENDER_HOVER, text_color=CTK_LAVENDER_TEXT, height=28, command=self.tum_kurallari_ac)
        btn_all_rules.pack(fill="x", padx=10, pady=(0, 10))


        # Grafiklerin Paneli
        self.chart_frame = ctk.CTkFrame(self.root, width=730, height=940, fg_color=CTK_LAVENDER_DARK_SUB, corner_radius=15)
        self.chart_frame.place(x=490, y=20)

        plt.style.use('dark_background')
        self.fig, (self.ax_day, self.ax1, self.ax2, self.ax3) = plt.subplots(4, 1, figsize=(6.8, 9.0))
        self.fig.patch.set_facecolor(CTK_LAVENDER_DARK_SUB) 
        
        for ax in [self.ax_day, self.ax1, self.ax2, self.ax3]:
            ax.set_facecolor(CTK_LAVENDER_DARK_BG) 
            ax.tick_params(colors=CTK_LAVENDER_TEXT, labelsize=8)
            ax.grid(True, color='#342c3e', linestyle='--', alpha=0.6)

        self.fig.tight_layout(pad=2.5)
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.chart_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=15, pady=15)

    def tum_kurallari_ac(self):
        """ Tüm kuralları listeleyen yeni bir bağımsız sekme açar. """
        rules_window = ctk.CTkToplevel(self.root)
        rules_window.title("Sistemdeki Tüm Bulanık Kurallar Matrisi")
        rules_window.geometry("500x420")
        rules_window.configure(fg_color=CTK_LAVENDER_DARK_BG)
        rules_window.attributes("-topmost", True) 

        title = ctk.CTkLabel(rules_window, text="KURAL MATRİSİ", font=("Helvetica", 14, "bold"), text_color=CTK_LAVENDER_MAIN)
        title.pack(pady=15)

        frame = ctk.CTkFrame(rules_window, fg_color=CTK_LAVENDER_DARK_SUB, corner_radius=10)
        frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        full_listbox = tk.Listbox(frame, font=("Consolas", 9), bg=CTK_LAVENDER_DARK_BG, fg=CTK_LAVENDER_TEXT, bd=0, highlightthickness=0)
        full_listbox.pack(fill="both", expand=True, padx=10, pady=10)

        for km in self.kurallar.values():
            full_listbox.insert(tk.END, f" {km}")

    def update_labels(self, value=None):
        gunler = ["Pazartesi (0)", "Salı (1)", "Çarşamba (2)", "Perşembe (3)", "Cuma (4)", "Cumartesi (5)", "Pazar (6)"]
        tam_gun = int(round(self.slider_day.get()))
        
        self.day_title.configure(text=f"Haftanın Günü: {gunler[tam_gun]}")
        self.time_title.configure(text=f"Saat: {self.slider_time.get():.1f}")
        self.space_title.configure(text=f"Otoparktaki Boş Yer Sayısı: {int(self.slider_space.get())}")
        
        self.hesapla_ve_ciz()

    def ayarlari_guncelle(self):
        try:
            yogun_saat = float(self.entry_yogun_saat.get())
            yer_az_sinir = int(self.entry_yer_az.get())
            if not (0 <= yogun_saat <= 24) or not (0 < yer_az_sinir <= 100): raise ValueError
            
            self.bounds['saat_yogun'] = [yogun_saat - 2, yogun_saat, yogun_saat + 2]
            self.bounds['yer_az'] = [0, 0, yer_az_sinir]
            self.bounds['yer_orta'] = [yer_az_sinir - 5, 50, 75]
            
            messagebox.showinfo("Başarılı", "Sınırlar Güncellendi !")
            self.hesapla_ve_ciz()
        except ValueError:
            messagebox.showerror("Hata", "Lütfen sınır değerlerini düzgün biçimde girin.")

    def hesapla_ve_ciz(self):
        try:
            # Bulanık Mantık Evrenleri
            saat_ekseni = np.arange(0, 25, 1)
            yer_ekseni = np.arange(0, 101, 1)
            ihtimal_ekseni = np.arange(0, 101, 1)
            gun_ekseni = np.arange(0, 7, 1)

            saat = ctrl.Antecedent(saat_ekseni, 'saat')
            bos_yer = ctrl.Antecedent(yer_ekseni, 'bos_yer')
            gun = ctrl.Antecedent(gun_ekseni, 'gun')
            ihtimal = ctrl.Consequent(ihtimal_ekseni, 'ihtimal')

            # Fonksiyon Tanımlamaları
            saat['sakin'] = fuzz.trapmf(saat.universe, self.bounds['saat_sakin'])
            saat['normal'] = fuzz.trapmf(saat.universe, self.bounds['saat_normal'])
            saat['yogun'] = fuzz.trimf(saat.universe, self.bounds['saat_yogun'])

            bos_yer['az'] = fuzz.trimf(bos_yer.universe, self.bounds['yer_az'])
            bos_yer['orta'] = fuzz.trimf(bos_yer.universe, self.bounds['yer_orta'])
            bos_yer['cok'] = fuzz.trapmf(bos_yer.universe, self.bounds['yer_cok'])

            gun['hafta_ici'] = fuzz.trapmf(gun.universe, [0, 0, 3, 5])
            gun['hafta_sonu'] = fuzz.trapmf(gun.universe, [3, 5, 6, 6])

            ihtimal['dusuk'] = fuzz.trimf(ihtimal.universe, [0, 0, 40])
            ihtimal['orta'] = fuzz.trimf(ihtimal.universe, [30, 50, 70])
            ihtimal['yuksek'] = fuzz.trimf(ihtimal.universe, [60, 100, 100])

            # Kural Kümesi
            kural_listesi = [
                ctrl.Rule(gun['hafta_ici'] & saat['sakin'] & bos_yer['cok'], ihtimal['yuksek']),
                ctrl.Rule(gun['hafta_ici'] & saat['sakin'] & bos_yer['orta'], ihtimal['yuksek']),
                ctrl.Rule(gun['hafta_ici'] & saat['normal'] & bos_yer['orta'], ihtimal['orta']),
                ctrl.Rule(gun['hafta_ici'] & saat['normal'] & bos_yer['az'], ihtimal['dusuk']),
                ctrl.Rule(gun['hafta_ici'] & saat['yogun'] & bos_yer['az'], ihtimal['dusuk']),
                ctrl.Rule(gun['hafta_ici'] & saat['yogun'] & bos_yer['orta'], ihtimal['dusuk']),
                ctrl.Rule(gun['hafta_sonu'] & saat['sakin'] & bos_yer['cok'], ihtimal['yuksek']),
                ctrl.Rule(gun['hafta_sonu'] & saat['sakin'] & bos_yer['orta'], ihtimal['orta']),
                ctrl.Rule(gun['hafta_sonu'] & saat['normal'] & bos_yer['cok'], ihtimal['yuksek']),
                ctrl.Rule(gun['hafta_sonu'] & saat['normal'] & bos_yer['orta'], ihtimal['dusuk']),
                ctrl.Rule(gun['hafta_sonu'] & saat['normal'] & bos_yer['az'], ihtimal['dusuk']),
                ctrl.Rule(gun['hafta_sonu'] & saat['yogun'] & bos_yer['az'], ihtimal['dusuk']),
                ctrl.Rule(bos_yer['az'] & saat['sakin'], ihtimal['orta']),
                ctrl.Rule(bos_yer['cok'], ihtimal['yuksek']),
                ctrl.Rule(bos_yer['az'] & saat['yogun'], ihtimal['dusuk'])
            ]

            park_kontrol = ctrl.ControlSystem(kural_listesi)
            park_sim = ctrl.ControlSystemSimulation(park_kontrol)

            # Giriş Sürgülerinin Yakalanması
            g_val = int(round(self.slider_day.get()))
            s_val = self.slider_time.get()
            y_val = self.slider_space.get()

            park_sim.input['gun'] = g_val
            park_sim.input['saat'] = s_val
            park_sim.input['bos_yer'] = y_val

            park_sim.compute()
            sonuc = park_sim.output['ihtimal']
            
            if y_val == 0: sonuc = 0.0 # Tam doluluk emniyet kilidi

            self.lbl_result.configure(text=f"Tahmini Park İhtimali: %{sonuc:.1f}", text_color=CTK_LAVENDER_MAIN)

            # Kural Aktivasyon Seviyelerini Hesaplama 
            mu_hi = fuzz.interp_membership(gun_ekseni, gun['hafta_ici'].mf, g_val)
            mu_hs = fuzz.interp_membership(gun_ekseni, gun['hafta_sonu'].mf, g_val)
            
            mu_skn = fuzz.interp_membership(saat_ekseni, saat['sakin'].mf, s_val)
            mu_nrm = fuzz.interp_membership(saat_ekseni, saat['normal'].mf, s_val)
            mu_ygn = fuzz.interp_membership(saat_ekseni, saat['yogun'].mf, s_val)
            
            mu_az = fuzz.interp_membership(yer_ekseni, bos_yer['az'].mf, y_val)
            mu_ort = fuzz.interp_membership(yer_ekseni, bos_yer['orta'].mf, y_val)
            mu_cok = fuzz.interp_membership(yer_ekseni, bos_yer['cok'].mf, y_val)

            aktivasyonlar = [
                min(mu_hi, mu_skn, mu_cok),  # K1
                min(mu_hi, mu_skn, mu_ort),  # K2
                min(mu_hi, mu_nrm, mu_ort),  # K3
                min(mu_hi, mu_nrm, mu_az),   # K4
                min(mu_hi, mu_ygn, mu_az),   # K5
                min(mu_hi, mu_ygn, mu_ort),  # K6
                min(mu_hs, mu_skn, mu_cok),  # K7
                min(mu_hs, mu_skn, mu_ort),  # K8
                min(mu_hs, mu_nrm, mu_cok),  # K9
                min(mu_hs, mu_nrm, mu_ort),  # K10
                min(mu_hs, mu_nrm, mu_az),   # K11
                min(mu_hs, mu_ygn, mu_az),   # K12
                min(mu_az, mu_skn),          # K13
                mu_cok,                      # K14
                min(mu_az, mu_ygn)           # K15
            ]

            self.rules_listbox.delete(0, tk.END)
            aktif_kural_sayisi = 0

            for idx, akt_seviye in enumerate(aktivasyonlar):
                if akt_seviye > 0:
                    yuzde_etki = akt_seviye * 100
                    kural_metni = self.kurallar[idx]
                    self.rules_listbox.insert(tk.END, f" (%{int(yuzde_etki)} etki) {kural_metni}")
                    aktif_kural_sayisi += 1

            if aktif_kural_sayisi == 0:
                self.rules_listbox.insert(tk.END, " Şuan aktif bir kural tetiklenmedi.")

            # Eksenleri temizle
            for ax in [self.ax_day, self.ax1, self.ax2, self.ax3]: ax.clear()

            # Haftanın Günü Grafiği
            self.ax_day.plot(gun_ekseni, fuzz.trapmf(gun_ekseni, [0, 0, 3, 5]), '#4fa3a5', label='Hafta İçi', linewidth=2)
            self.ax_day.plot(gun_ekseni, fuzz.trapmf(gun_ekseni, [3, 5, 6, 6]), '#d96b43', label='Hafta Sonu', linewidth=2)
            self.ax_day.axvline(x=g_val, color='#ffffff', linestyle=':', alpha=0.8)
            self.ax_day.set_title(f"Haftanın Günü", fontsize=10, color=CTK_LAVENDER_TEXT)
            self.ax_day.set_xticks(range(7))
            self.ax_day.set_xticklabels(['Pzt', 'Sal', 'Çar', 'Per', 'Cum', 'Cmt', 'Paz'], fontsize=8)
            self.ax_day.legend(loc='upper right', fontsize=8)

            # Saat Grafiği
            self.ax1.plot(saat_ekseni, fuzz.trapmf(saat_ekseni, self.bounds['saat_sakin']), '#bcaaa4', label='Sakin')
            self.ax1.plot(saat_ekseni, fuzz.trapmf(saat_ekseni, self.bounds['saat_normal']), CTK_LAVENDER_MAIN, label='Normal', linewidth=2)
            self.ax1.plot(saat_ekseni, fuzz.trimf(saat_ekseni, self.bounds['saat_yogun']), '#b39ddb', label='Yoğun')
            self.ax1.axvline(x=s_val, color='#ffffff', linestyle=':', alpha=0.8)
            self.ax1.set_title(f"Saat Üyelik Fonksiyonları (Seçili: {s_val:.1f})", fontsize=10, color=CTK_LAVENDER_TEXT)
            self.ax1.legend(loc='upper right', fontsize=8)

            # Boş Yer Grafiği
            self.ax2.plot(yer_ekseni, fuzz.trimf(yer_ekseni, self.bounds['yer_az']), '#e5989b', label='Az')
            self.ax2.plot(yer_ekseni, fuzz.trimf(yer_ekseni, self.bounds['yer_orta']), CTK_LAVENDER_MAIN, label='Orta')
            self.ax2.plot(yer_ekseni, fuzz.trapmf(yer_ekseni, self.bounds['yer_cok']), '#a8dadc', label='Çok')
            self.ax2.axvline(x=y_val, color='#ffffff', linestyle=':', alpha=0.8)
            self.ax2.set_title(f"Boş Yer Dağılımı (Mevcut Boş: {int(y_val)})", fontsize=10, color=CTK_LAVENDER_TEXT)
            self.ax2.legend(loc='upper right', fontsize=8)

            # Sonuç Alanı Grafiği
            self.ax3.plot(ihtimal_ekseni, fuzz.trimf(ihtimal_ekseni, [0, 0, 40]), '#d94e5c', alpha=0.3)
            self.ax3.plot(ihtimal_ekseni, fuzz.trimf(ihtimal_ekseni, [30, 50, 70]), '#8067a3', alpha=0.4)
            self.ax3.plot(ihtimal_ekseni, fuzz.trimf(ihtimal_ekseni, [60, 100, 100]), '#4f9a74', alpha=0.3)
            self.ax3.axvline(x=sonuc, color=CTK_LAVENDER_MAIN, linestyle='-', linewidth=4, label=f'Ağırlık Merkezi (%{sonuc:.1f})')
            self.ax3.set_title("Defuzzification (Durulaştırma) Karar Alanı", fontsize=10, color=CTK_LAVENDER_TEXT)
            self.ax3.legend(loc='upper right', fontsize=8)

            for ax in [self.ax_day, self.ax1, self.ax2, self.ax3]:
                ax.grid(True, color='#342c3e', linestyle='--', alpha=0.5)

            self.canvas.draw()

        except Exception as e:
            self.lbl_result.configure(text="Hesaplanamıyor (Belirsiz Bölge)", text_color="#d94e5c")

if __name__ == "__main__":
    root = ctk.CTk()
    app = FuzzyParkApp(root)
    root.mainloop()