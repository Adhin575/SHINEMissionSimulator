import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
import time
from datetime import datetime, timedelta

class SHINEMissionGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("SHINE Mission Complete Simulator")
        self.root.geometry("1600x950")
        self.root.configure(bg='#0f172a')
        
        # Mission start date - From Gantt chart: Launch Window (Preferred Launch Date: 18 Feb 2029)
        # Launch & ICPS Deployment - Lunar Flyby & Ballistic Lunar Transfer: 1-Mar-23 to 17-Aug-29
        # Actual launch date from schedule: 1-Mar-29 (ICPS deployment start)
        self.MISSION_START_DATE = datetime(2029, 3, 1)  # Launch/ICPS Deployment on Mar 1, 2029
        
        # Physical constants
        self.MU_MOON = 4902.8e9  # m^3/s^2
        self.R_MOON = 1737.4e3   # m
        self.ISP = 2500
        self.G0 = 9.81
        self.THRUST = 1.25e-3  # kN
        self.DRY_MASS = 12  # kg (from mission documentation)
        self.FLOW_RATE = 42e-9  # kg/s (calculated from Isp)
        
        # Mission phase durations (in days) - EXACT dates from Gantt chart
        # Phase E starts: 1-Mar-29 (ICPS deployment)
        # NRHO Capture & Periapsis Lowering: 17-Aug-29 to 25-Oct-29 (69 days)
        # Science Phase: 25-Oct-29 to 29-Sep-30 (~339 days, but doc says 6-12 months)
        # De-orbit: 30-Sep-30 to 30-Sep-30 (same day)
        
        # Calculating from dates:
        # Launch to NRHO Capture: 1-Mar-29 to 17-Aug-29 = 169 days
        # NRHO to Science start: 17-Aug-29 to 25-Oct-29 = 69 days  
        # Science Phase: 25-Oct-29 to 29-Sep-30 = 339 days
        # Deorbit: 30-Sep-30 = 1 day
        
        self.PHASE_DURATIONS = {
            'launch': 0.0,  # Instantaneous - Mar 1, 2029
            'commissioning': 0.42,  # ~10 hours post-launch
            'tli': 0.08,  # B-plane maneuver period (~2 hours)
            'cruise': 5.0,  # 5-day translunar cruise (Mar 1-6)
            'lga_flyby': 0.5,  # ~12 hours lunar gravity assist (Mar 6)
            'sun_earth_transfer': 163.0,  # Sun-Earth transfer to NRHO (Mar 6 - Aug 17 = ~163 days)
            'nrho_capture': 6.56,  # NRHO capture period (Aug 17-24)
            'nrho_staging': 20.0,  # NRHO staging before spiral (Aug 24 - Sep 13 = ~20 days)
            'spiral_down': 42.0,  # Spiral down to 300 km (Sep 13 - Oct 25 = ~42 days)
            'commissioning_orbit': 0.0,  # Combined with spiral down
            'science': 339.0,  # Science Phase: Oct 25, 2029 - Sep 29, 2030 (339 days)
            'deorbit': 1.0  # De-orbit on Sep 30, 2030
        }
        
        # Propellant budgets (kg) - CORRECTED for 12 kg dry mass
        # Required propellant for full mission ΔV (1,385 m/s) ≈ 0.815 kg
        self.PROPELLANT_BUDGET = {
            'tli': 0.020,            # 40 m/s → ~0.020 kg
            'cruise': 0.007,         # 15 m/s → ~0.007 kg
            'sun_earth_transfer': 0.039,  # 80 m/s → ~0.039 kg
            'nrho_capture': 0.059,   # 120 m/s → ~0.059 kg
            'spiral_down': 0.527,    # 950 m/s → ~0.527 kg
            'science': 0.046,        # 95 m/s → ~0.046 kg
            'deorbit': 0.041         # 85 m/s → ~0.041 kg
        }
        # Total required: ~0.739 kg (with small rounding, target is 0.815 kg for 1,385 m/s)
        
        # Delta-V budgets (m/s) - Total planned ΔV
        self.DELTA_V_BUDGET = {
            'tli': 40,           # B-plane correction maneuvers
            'cruise': 15,        # TCMs during cruise
            'sun_earth_transfer': 80,  # Multi-body trajectory corrections
            'nrho_capture': 120, # NRHO insertion
            'spiral_down': 950,  # Major ΔV for orbit lowering (1450 km to 300 km)
            'science': 95,       # Station-keeping and momentum dumps
            'deorbit': 85        # Controlled deorbit from 300 km
        }
        # Total planned ΔV: 1,385 m/s
        
        # Initial conditions
        self.INITIAL_PROPELLANT = 1.5  # kg total (tank capacity)
        # With 1.5 kg propellant and 12 kg dry mass:
        # ΔV_max = 2500 * 9.81 * ln(13.5/12) = 2,483 m/s
        self.TOTAL_DELTA_V_CAPACITY = 2483  # m/s (corrected for 12 kg dry mass)
        self.REQUIRED_PROPELLANT = 0.815  # kg (for 1,385 m/s mission ΔV)
        self.PROPELLANT_MARGIN = self.INITIAL_PROPELLANT - self.REQUIRED_PROPELLANT  # 0.685 kg margin
        
        # Simulation state
        self.is_running = False
        self.current_time = 0  # days
        self.phase = "launch"
        self.propellant_remaining = self.INITIAL_PROPELLANT
        self.propellant_used = 0
        self.cumulative_burn_time = 0  # hours
        self.delta_v_used = 0  # m/s
        self.delta_v_remaining = self.TOTAL_DELTA_V_CAPACITY  # m/s
        self.is_firing = False
        self.science_passes = 0
        self.psr_observations = 0
        
        # Data storage
        self.time_data = []
        self.prop_remaining_data = []
        self.prop_used_data = []
        self.periapsis_data = []
        self.apoapsis_data = []
        self.burn_time_data = []
        self.distance_moon_data = []
        self.altitude_data = []
        self.velocity_data = []
        self.delta_v_used_data = []
        self.delta_v_remaining_data = []
        
        # Current orbital parameters
        self.current_orbit = {
            'sma': 0,
            'ecc': 0,
            'periapsis': 0,
            'apoapsis': 0,
            'period': 0,
            'inclination': 0,
            'revs_per_day': 0
        }
        
        self.current_state = {
            'altitude': 300,  # km (LEO parking)
            'distance_moon': 384400,  # km
            'velocity': 7.8,  # km/s (LEO velocity)
            'in_lunar_soi': False,
            'latitude': 0,
            'longitude': 0
        }
        
        self.setup_gui()
        
    def setup_gui(self):
        # Main container
        main_frame = tk.Frame(self.root, bg='#0f172a')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title section
        title_frame = tk.Frame(main_frame, bg='#1e293b', relief=tk.RAISED, bd=3)
        title_frame.pack(fill=tk.X, pady=(0, 10))
        
        title_label = tk.Label(title_frame, 
                              text="🛰️ SHINE Mission Complete Simulator",
                              font=('Arial', 20, 'bold'), 
                              bg='#1e293b', fg='#38bdf8')
        title_label.pack(pady=8)
        
        subtitle_label = tk.Label(title_frame, 
                                 text="Launch → TLI → Cruise → LGA → Sun-Earth Transfer → NRHO → Spiral → Science → Deorbit",
                                 font=('Arial', 9), 
                                 bg='#1e293b', fg='#94a3b8')
        subtitle_label.pack(pady=(0, 3))
        
        # Mission dates label
        mission_end = datetime(2030, 9, 30)  # Exact end date from Gantt chart
        dates_label = tk.Label(title_frame,
                              text=f"Mission Duration: {self.MISSION_START_DATE.strftime('%B %d, %Y')} - {mission_end.strftime('%B %d, %Y')} | Phase E: Operations",
                              font=('Arial', 9, 'italic'),
                              bg='#1e293b', fg='#60a5fa')
        dates_label.pack(pady=(0, 8))
        
        # Mission stats bar
        stats_frame = tk.Frame(title_frame, bg='#1e293b')
        stats_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        total_days = sum(self.PHASE_DURATIONS.values())
        self.create_stat_box(stats_frame, "Launch Date", "Mar 1, 2029", 0)
        self.create_stat_box(stats_frame, "Science Start", "Oct 25, 2029", 1)
        self.create_stat_box(stats_frame, "Science End", "Sep 29, 2030", 2)
        self.create_stat_box(stats_frame, "Mission End", "Sep 30, 2030", 3)
        
        # Control panel
        control_frame = tk.Frame(main_frame, bg='#1e293b', relief=tk.RAISED, bd=2)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        btn_frame = tk.Frame(control_frame, bg='#1e293b')
        btn_frame.pack(pady=10)
        
        self.start_btn = tk.Button(btn_frame, text="▶ Start Mission", 
                                   command=self.toggle_simulation,
                                   bg='#22c55e', fg='white', 
                                   font=('Arial', 12, 'bold'),
                                   width=12, height=2, cursor='hand2')
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.reset_btn = tk.Button(btn_frame, text="↻ Reset", 
                                   command=self.reset_simulation,
                                   bg='#ef4444', fg='white', 
                                   font=('Arial', 12, 'bold'),
                                   width=12, height=2, cursor='hand2')
        self.reset_btn.pack(side=tk.LEFT, padx=5)
        
        self.speed_label = tk.Label(btn_frame, text="Simulation Speed:", 
                                   bg='#1e293b', fg='white', 
                                   font=('Arial', 10))
        self.speed_label.pack(side=tk.LEFT, padx=(20, 5))
        
        self.speed_scale = tk.Scale(btn_frame, from_=1, to=100, 
                                   orient=tk.HORIZONTAL,
                                   bg='#334155', fg='white', 
                                   font=('Arial', 9),
                                   length=200, troughcolor='#475569')
        self.speed_scale.set(10)
        self.speed_scale.pack(side=tk.LEFT, padx=5)
        
        # Status indicator
        self.status_frame = tk.Frame(btn_frame, bg='#475569', relief=tk.RAISED, bd=2)
        self.status_frame.pack(side=tk.LEFT, padx=20)
        
        self.status_label = tk.Label(self.status_frame, text="● Pre-Launch", 
                                    bg='#475569', fg='white', 
                                    font=('Arial', 11, 'bold'),
                                    padx=20, pady=10)
        self.status_label.pack()
        
        # Progress section
        progress_frame = tk.Frame(control_frame, bg='#1e293b')
        progress_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        self.progress_label = tk.Label(progress_frame, 
                                      text="LAUNCH Phase - Day 0.0 / 515.0",
                                      bg='#1e293b', fg='#38bdf8', 
                                      font=('Arial', 11, 'bold'))
        self.progress_label.pack(pady=(5, 5))
        
        self.progress_bar = ttk.Progressbar(progress_frame, length=800, mode='determinate')
        self.progress_bar.pack(pady=5)
        
        # Phase timeline
        timeline_frame = tk.Frame(progress_frame, bg='#1e293b')
        timeline_frame.pack(fill=tk.X, pady=5)
        
        phase_colors = {
            'Launch': '#22c55e', 'TLI': '#3b82f6', 'Cruise': '#8b5cf6',
            'Transfer': '#f59e0b', 'NRHO': '#ec4899', 'Spiral': '#06b6d4',
            'Science': '#10b981', 'Deorbit': '#ef4444'
        }
        
        for i, (phase, color) in enumerate(phase_colors.items()):
            label = tk.Label(timeline_frame, text=phase, 
                           bg=color, fg='white',
                           font=('Arial', 8, 'bold'), 
                           padx=8, pady=3)
            label.pack(side=tk.LEFT, padx=2)
        
        # Info panels container
        info_container = tk.Frame(main_frame, bg='#0f172a')
        info_container.pack(fill=tk.X, pady=(0, 10))
        
        # Left panel - Spacecraft State
        left_panel = self.create_info_panel(info_container, "Spacecraft State", '#3b82f6')
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 3))
        self.spacecraft_text = self.create_text_widget(left_panel, height=9)
        
        # Middle-left panel - Trajectory/Orbit
        ml_panel = self.create_info_panel(info_container, "Trajectory & Orbit", '#8b5cf6')
        ml_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=3)
        self.orbit_text = self.create_text_widget(ml_panel, height=9)
        
        # Middle panel - Delta-V & Propulsion
        m_panel = self.create_info_panel(info_container, "ΔV & Propulsion", '#10b981')
        m_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=3)
        self.deltav_text = self.create_text_widget(m_panel, height=9)
        
        # Middle-right panel - Thruster Status
        mr_panel = self.create_info_panel(info_container, "Thruster System", '#f59e0b')
        mr_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=3)
        self.prop_text = self.create_text_widget(mr_panel, height=9)
        
        # Right panel - Science Operations
        right_panel = self.create_info_panel(info_container, "Science Operations", '#ec4899')
        right_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(3, 0))
        self.science_text = self.create_text_widget(right_panel, height=9)
        
        # Plots section
        plot_frame = tk.Frame(main_frame, bg='#0f172a')
        plot_frame.pack(fill=tk.BOTH, expand=True)
        
        self.fig = Figure(figsize=(16, 7), facecolor='#0f172a')
        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Create 6 subplots
        gs = self.fig.add_gridspec(2, 3, hspace=0.3, wspace=0.3)
        self.ax1 = self.fig.add_subplot(gs[0, 0], facecolor='#1e293b')
        self.ax2 = self.fig.add_subplot(gs[0, 1], facecolor='#1e293b')
        self.ax3 = self.fig.add_subplot(gs[0, 2], facecolor='#1e293b')
        self.ax4 = self.fig.add_subplot(gs[1, 0], facecolor='#1e293b')
        self.ax5 = self.fig.add_subplot(gs[1, 1], facecolor='#1e293b')
        self.ax6 = self.fig.add_subplot(gs[1, 2], facecolor='#1e293b')
        
        self.setup_plots()
        self.update_display()
        
    def create_stat_box(self, parent, label, value, col):
        frame = tk.Frame(parent, bg='#334155', relief=tk.RAISED, bd=1)
        frame.grid(row=0, column=col, padx=5, pady=5, sticky='ew')
        parent.grid_columnconfigure(col, weight=1)
        
        tk.Label(frame, text=label, bg='#334155', fg='#94a3b8',
                font=('Arial', 8)).pack(pady=(3, 0))
        tk.Label(frame, text=value, bg='#334155', fg='white',
                font=('Arial', 10, 'bold')).pack(pady=(0, 3))
        
    def create_info_panel(self, parent, title, color):
        panel = tk.Frame(parent, bg='#1e293b', relief=tk.RAISED, bd=2)
        tk.Label(panel, text=title, font=('Arial', 11, 'bold'),
                bg='#1e293b', fg=color, pady=5).pack()
        return panel
        
    def create_text_widget(self, parent, height):
        text = tk.Text(parent, height=height, width=30, 
                      bg='#0f172a', fg='#e2e8f0',
                      font=('Courier', 9), relief=tk.FLAT,
                      padx=10, pady=5)
        text.pack(padx=5, pady=5, fill=tk.BOTH, expand=True)
        return text
    
    def setup_plots(self):
        axes = [self.ax1, self.ax2, self.ax3, self.ax4, self.ax5, self.ax6]
        titles = ['Distance from Moon', 'Orbital Altitudes', 'Propellant Status',
                 'Delta-V Budget', 'Spacecraft Velocity', 'Science Coverage']
        
        for ax, title in zip(axes, titles):
            ax.set_title(title, fontsize=10, color='white', pad=10)
            ax.tick_params(colors='white', labelsize=8)
            for spine in ax.spines.values():
                spine.set_color('#475569')
            ax.grid(True, alpha=0.15, color='#475569', linestyle='--')
            ax.set_facecolor('#1e293b')
        
        self.ax1.set_xlabel('Day', color='white', fontsize=8)
        self.ax1.set_ylabel('Distance (km)', color='white', fontsize=8)
        
        self.ax2.set_xlabel('Day', color='white', fontsize=8)
        self.ax2.set_ylabel('Altitude (km)', color='white', fontsize=8)
        
        self.ax3.set_xlabel('Day', color='white', fontsize=8)
        self.ax3.set_ylabel('Mass (kg)', color='white', fontsize=8)
        
        self.ax4.set_xlabel('Day', color='white', fontsize=8)
        self.ax4.set_ylabel('ΔV (m/s)', color='white', fontsize=8)
        
        self.ax5.set_xlabel('Day', color='white', fontsize=8)
        self.ax5.set_ylabel('Velocity (km/s)', color='white', fontsize=8)
        
        self.ax6.set_xlabel('Day', color='white', fontsize=8)
        self.ax6.set_ylabel('PSR Observations', color='white', fontsize=8)
        
    def get_current_date(self):
        """Get the current mission date based on elapsed time"""
        return self.MISSION_START_DATE + timedelta(days=self.current_time)
    
    def get_phase_end_date(self, phase):
        """Get the end date for a given phase"""
        phase_end_day = self.get_phase_start_day(phase) + self.PHASE_DURATIONS.get(phase, 0)
        return self.MISSION_START_DATE + timedelta(days=phase_end_day)
    
    def get_phase_start_day(self, phase):
        """Calculate the start day for a given phase"""
        phases_order = ['launch', 'commissioning', 'tli', 'cruise', 'lga_flyby',
                       'sun_earth_transfer', 'nrho_capture', 'nrho_staging',
                       'spiral_down', 'commissioning_orbit', 'science', 'deorbit']
        
        start_day = 0
        for p in phases_order:
            if p == phase:
                return start_day
            start_day += self.PHASE_DURATIONS[p]
        return start_day
    
    def get_current_phase(self):
        """Determine current mission phase based on elapsed time"""
        t = self.current_time
        cumulative = 0
        
        for phase, duration in self.PHASE_DURATIONS.items():
            cumulative += duration
            if t <= cumulative:
                return phase
        return "complete"
    
    def calculate_orbital_period(self, sma_km):
        """Calculate orbital period in hours"""
        sma_m = sma_km * 1000
        period_s = 2 * np.pi * np.sqrt(sma_m**3 / self.MU_MOON)
        return period_s / 3600
    
    def update_spacecraft_state(self):
        """Update spacecraft position, velocity, and orbital parameters"""
        phase = self.phase
        
        # Handle completion phase
        if phase == 'complete':
            self.current_orbit['periapsis'] = 0
            self.current_orbit['apoapsis'] = 0
            self.current_state['altitude'] = 0
            self.current_state['velocity'] = 2.4  # Impact velocity
            return
        
        t = self.current_time
        phase_start = self.get_phase_start_day(phase)
        phase_time = t - phase_start
        
        if phase == 'launch':
            self.current_state['altitude'] = 300
            self.current_state['velocity'] = 7.8
            self.current_state['distance_moon'] = 384400
            
        elif phase == 'commissioning':
            self.current_state['altitude'] = 300
            self.current_state['velocity'] = 7.8
            self.current_state['distance_moon'] = 384400
            
        elif phase == 'tli':
            progress = phase_time / self.PHASE_DURATIONS['tli']
            self.current_state['altitude'] = 300 + progress * 1000
            self.current_state['velocity'] = 7.8 + progress * 3.2  # TLI burn to ~11 km/s
            self.current_state['distance_moon'] = 384400
            
        elif phase == 'cruise':
            progress = phase_time / self.PHASE_DURATIONS['cruise']
            self.current_state['altitude'] = 1300 + progress * 50000
            self.current_state['velocity'] = 11.0 - progress * 0.5
            self.current_state['distance_moon'] = 384400 * (1 - progress * 0.87)
            
        elif phase == 'lga_flyby':
            progress = phase_time / self.PHASE_DURATIONS['lga_flyby']
            min_distance = 50000  # 50,000 km closest approach
            self.current_state['distance_moon'] = 50000 + abs(0.5 - progress) * 10000
            self.current_state['velocity'] = 1.0 + progress * 0.2
            self.current_state['in_lunar_soi'] = True
            
        elif phase == 'sun_earth_transfer':
            progress = phase_time / self.PHASE_DURATIONS['sun_earth_transfer']
            # Large elliptical trajectory through Earth-Moon system
            self.current_state['distance_moon'] = 50000 + progress * 300000
            self.current_state['velocity'] = 1.2 - progress * 0.3
            
        elif phase == 'nrho_capture':
            progress = phase_time / self.PHASE_DURATIONS['nrho_capture']
            self.current_state['distance_moon'] = 350000 - progress * 280000
            self.current_orbit['periapsis'] = 1450
            self.current_orbit['apoapsis'] = 69500
            self.current_orbit['sma'] = (1450 + 69500) / 2 + self.R_MOON / 1000
            self.current_orbit['period'] = 6.56
            self.current_orbit['inclination'] = 90
            
        elif phase == 'nrho_staging':
            self.current_orbit['periapsis'] = 1450
            self.current_orbit['apoapsis'] = 69500
            self.current_orbit['sma'] = 37212.4
            self.current_orbit['period'] = 6.56
            self.current_orbit['inclination'] = 90
            self.current_orbit['revs_per_day'] = 24 / 6.56
            
        elif phase == 'spiral_down':
            progress = phase_time / self.PHASE_DURATIONS['spiral_down']
            initial_apo = 69500
            final_apo = 300
            current_apo = initial_apo - (initial_apo - final_apo) * progress
            current_peri = 1450 - (1450 - 300) * progress
            
            self.current_orbit['periapsis'] = current_peri
            self.current_orbit['apoapsis'] = current_apo
            self.current_orbit['sma'] = (current_peri + current_apo) / 2 + self.R_MOON / 1000
            self.current_orbit['ecc'] = (current_apo - current_peri) / (current_apo + current_peri)
            self.current_orbit['period'] = self.calculate_orbital_period(self.current_orbit['sma'])
            self.current_orbit['inclination'] = 90
            
        elif phase == 'commissioning_orbit':
            self.current_orbit['periapsis'] = 300
            self.current_orbit['apoapsis'] = 300
            self.current_orbit['sma'] = 2037.4
            self.current_orbit['ecc'] = 0.025
            self.current_orbit['period'] = 2.37
            self.current_orbit['inclination'] = 90
            self.current_orbit['revs_per_day'] = 10.1
            
        elif phase == 'science':
            self.current_orbit['periapsis'] = 300
            self.current_orbit['apoapsis'] = 300
            self.current_orbit['sma'] = 2037.4
            self.current_orbit['ecc'] = 0.02
            self.current_orbit['period'] = 2.37
            self.current_orbit['inclination'] = 90
            self.current_orbit['revs_per_day'] = 10.1
            
            # Update science passes - 9 months of science operations
            if phase_time > 0:
                self.science_passes = int(phase_time * 10.1)
                # PSR observations occur when latitude > 80°S
                self.psr_observations = int(self.science_passes * 0.67)  # ~67% of passes over PSRs
            
        elif phase == 'deorbit':
            progress = phase_time / self.PHASE_DURATIONS['deorbit']
            self.current_orbit['periapsis'] = 300 - 300 * progress
            self.current_orbit['apoapsis'] = 300
            self.current_orbit['sma'] = 2037.4 - 37.4 * progress
            self.current_orbit['period'] = self.calculate_orbital_period(self.current_orbit['sma'])
            self.current_orbit['inclination'] = 90
    
    def determine_firing_status(self):
        """Determine if thruster should be firing based on phase"""
        phase = self.phase
        
        # Handle completion phase
        if phase == 'complete':
            return False
        
        t = self.current_time
        phase_start = self.get_phase_start_day(phase)
        phase_time = t - phase_start
        duration = self.PHASE_DURATIONS.get(phase, 0)
        
        if phase in ['launch', 'commissioning', 'lga_flyby', 'commissioning_orbit']:
            return False
            
        elif phase == 'tli':
            return True  # Continuous burn during TLI
            
        elif phase == 'cruise':
            # Occasional TCMs
            return np.random.random() < 0.05
            
        elif phase == 'sun_earth_transfer':
            # Burns near apses
            progress = phase_time / duration
            # Higher burn probability near key points
            if progress < 0.15 or (0.45 < progress < 0.55) or progress > 0.85:
                return np.random.random() < 0.3
            return np.random.random() < 0.05
            
        elif phase == 'nrho_capture':
            return True  # Continuous burn during capture
            
        elif phase == 'nrho_staging':
            # Periodic station-keeping
            return np.random.random() < 0.1
            
        elif phase == 'spiral_down':
            # Heavy burn activity
            return np.random.random() < 0.85
            
        elif phase == 'science':
            # Station-keeping and momentum dumps
            hours_into_day = (phase_time % 1) * 24
            # Burns occur outside science windows
            if 2 <= hours_into_day < 2.5 or 14 <= hours_into_day < 14.5:
                return True
            return False
            
        elif phase == 'deorbit':
            return np.random.random() < 0.95  # Heavy deorbit burns
            
        return False
    
    def simulation_step(self):
        """Execute one simulation time step"""
        if not self.is_running:
            return
        
        # Time step based on simulation speed
        speed = self.speed_scale.get()
        time_step = 0.1 * (speed / 10)  # days
        
        self.current_time += time_step
        
        # Update phase
        old_phase = self.phase
        self.phase = self.get_current_phase()
        
        # Log phase transitions
        if old_phase != self.phase and self.phase != 'complete':
            print(f"Phase transition: {old_phase} -> {self.phase} at day {self.current_time:.1f}")
        
        # Update spacecraft state
        self.update_spacecraft_state()
        
        # Determine firing status
        self.is_firing = self.determine_firing_status()
        
        # Update propellant
        if self.is_firing and self.propellant_remaining > 0:
            prop_consumed = self.FLOW_RATE * (time_step * 24 * 3600)
            self.propellant_remaining = max(0, self.propellant_remaining - prop_consumed)
            self.propellant_used += prop_consumed
            self.cumulative_burn_time += time_step * 24
            
            # Calculate delta-V used (Tsiolkovsky equation)
            # ΔV = Isp * g0 * ln(m_before / m_after)
            m_before = self.DRY_MASS + self.propellant_remaining + prop_consumed
            m_after = self.DRY_MASS + self.propellant_remaining
            if m_after > 0 and m_before > m_after:
                delta_v_increment = self.ISP * self.G0 * np.log(m_before / m_after)
                self.delta_v_used += delta_v_increment
                self.delta_v_remaining = self.TOTAL_DELTA_V_CAPACITY - self.delta_v_used
        
        # Store data for plotting (every ~1 day)
        if len(self.time_data) == 0 or self.current_time - self.time_data[-1] >= 1.0:
            self.time_data.append(self.current_time)
            self.prop_remaining_data.append(self.propellant_remaining)
            self.prop_used_data.append(self.propellant_used)
            self.periapsis_data.append(self.current_orbit.get('periapsis', 0))
            self.apoapsis_data.append(self.current_orbit.get('apoapsis', 0))
            self.burn_time_data.append(self.cumulative_burn_time)
            self.distance_moon_data.append(self.current_state.get('distance_moon', 0))
            self.altitude_data.append(self.current_state.get('altitude', 0))
            self.velocity_data.append(self.current_state.get('velocity', 0))
            self.delta_v_used_data.append(self.delta_v_used)
            self.delta_v_remaining_data.append(self.delta_v_remaining)
        
        # Check if mission complete
        total_duration = sum(self.PHASE_DURATIONS.values())
        if self.current_time >= total_duration:
            self.is_running = False
            self.phase = "complete"
            self.start_btn.config(text="▶ Start Mission", bg='#22c55e')
            print(f"Mission complete at day {self.current_time:.1f}")
        
        # Update display
        self.update_display()
        
        # Schedule next step
        if self.is_running:
            delay = max(1, int(50 / speed))  # Faster updates at higher speeds
            self.root.after(delay, self.simulation_step)
    
    def toggle_simulation(self):
        """Start or pause the simulation"""
        self.is_running = not self.is_running
        if self.is_running:
            self.start_btn.config(text="⏸ Pause", bg='#f59e0b')
            self.simulation_step()
        else:
            self.start_btn.config(text="▶ Resume", bg='#22c55e')
    
    def reset_simulation(self):
        """Reset simulation to initial state"""
        self.is_running = False
        self.current_time = 0
        self.phase = "launch"
        self.propellant_remaining = self.INITIAL_PROPELLANT
        self.propellant_used = 0
        self.cumulative_burn_time = 0
        self.delta_v_used = 0
        self.delta_v_remaining = self.TOTAL_DELTA_V_CAPACITY
        self.is_firing = False
        self.science_passes = 0
        self.psr_observations = 0
        
        # Clear data
        self.time_data = []
        self.prop_remaining_data = []
        self.prop_used_data = []
        self.periapsis_data = []
        self.apoapsis_data = []
        self.burn_time_data = []
        self.distance_moon_data = []
        self.altitude_data = []
        self.velocity_data = []
        self.delta_v_used_data = []
        self.delta_v_remaining_data = []
        
        # Reset state
        self.current_orbit = {
            'sma': 0, 'ecc': 0, 'periapsis': 0,
            'apoapsis': 0, 'period': 0, 'inclination': 0, 'revs_per_day': 0
        }
        
        self.current_state = {
            'altitude': 300, 'distance_moon': 384400,
            'velocity': 7.8, 'in_lunar_soi': False,
            'latitude': 0, 'longitude': 0
        }
        
        self.start_btn.config(text="▶ Start Mission", bg='#22c55e')
        self.update_display()
        print("Simulation reset")
    
    def update_display(self):
        """Update all GUI elements with current simulation state"""
        # Update progress bar
        total_duration = sum(self.PHASE_DURATIONS.values())
        progress = (self.current_time / total_duration) * 100
        self.progress_bar['value'] = min(progress, 100)
        
        # Update progress label
        phase_name = self.phase.upper().replace('_', ' ')
        current_date = self.get_current_date()
        phase_end_date = self.get_phase_end_date(self.phase) if self.phase != 'complete' else current_date
        
        self.progress_label.config(
            text=f"{phase_name} Phase - Day {self.current_time:.2f} / {total_duration:.1f} | {current_date.strftime('%b %d, %Y')}"
        )
        
        # Update status indicator
        if self.is_firing:
            self.status_label.config(text="🔥 THRUSTER FIRING", bg='#f97316')
            self.status_frame.config(bg='#f97316')
        else:
            self.status_label.config(text="💨 Coasting", bg='#475569')
            self.status_frame.config(bg='#475569')
        
        # Update spacecraft state text
        self.spacecraft_text.delete(1.0, tk.END)
        current_date = self.get_current_date()
        spacecraft_info = f"""
Phase:           {phase_name}
Day:             {self.current_time:.2f}
Date:            {current_date.strftime('%b %d, %Y')}
Time (UTC):      {current_date.strftime('%H:%M:%S')}
Altitude:        {self.current_state['altitude']:.1f} km
Velocity:        {self.current_state['velocity']:.2f} km/s
Dist to Moon:    {self.current_state['distance_moon']:.0f} km
In Lunar SOI:    {'Yes' if self.current_state.get('in_lunar_soi', False) else 'No'}
Mass:            {self.DRY_MASS + self.propellant_remaining:.2f} kg
"""
        self.spacecraft_text.insert(1.0, spacecraft_info)
        
        # Update orbit text
        self.orbit_text.delete(1.0, tk.END)
        if self.phase in ['nrho_capture', 'nrho_staging', 'spiral_down', 
                         'commissioning_orbit', 'science', 'deorbit']:
            orbit_info = f"""
Semi-major Axis: {self.current_orbit['sma']:.1f} km
Eccentricity:    {self.current_orbit['ecc']:.4f}
Periapsis:       {self.current_orbit['periapsis']:.1f} km
Apoapsis:        {self.current_orbit['apoapsis']:.1f} km
Period:          {self.current_orbit['period']:.2f} h
Inclination:     {self.current_orbit['inclination']:.1f}°
Revs/Day:        {self.current_orbit.get('revs_per_day', 0):.2f}
"""
        else:
            orbit_info = f"""
Status:          Transfer Trajectory
Type:            {'TLI' if self.phase == 'tli' else 'Cruise' if self.phase == 'cruise' else 'Sun-Earth Transfer'}
Target:          {'Lunar SOI' if self.phase in ['tli', 'cruise'] else 'NRHO Capture'}


(Orbital parameters available
after NRHO capture)
"""
        self.orbit_text.insert(1.0, orbit_info)
        
        # Update Delta-V & Propulsion text
        self.deltav_text.delete(1.0, tk.END)
        deltav_percent_used = (self.delta_v_used / self.TOTAL_DELTA_V_CAPACITY) * 100
        deltav_percent_remaining = (self.delta_v_remaining / self.TOTAL_DELTA_V_CAPACITY) * 100
        
        # Get phase-specific delta-V budget
        phase_budget = self.DELTA_V_BUDGET.get(self.phase, 0)
        
        deltav_info = f"""
ΔV Capacity:     {self.TOTAL_DELTA_V_CAPACITY:.0f} m/s
ΔV Used:         {self.delta_v_used:.1f} m/s ({deltav_percent_used:.1f}%)
ΔV Remaining:    {self.delta_v_remaining:.1f} m/s ({deltav_percent_remaining:.1f}%)
Phase Budget:    {phase_budget} m/s
Planned Total:   1,385 m/s
Propellant Used: {self.propellant_used * 1000:.1f} g
Propellant Left: {self.propellant_remaining * 1000:.1f} g
Required Mass:   {self.REQUIRED_PROPELLANT * 1000:.0f} g (for mission)
Margin:          {self.PROPELLANT_MARGIN * 1000:.0f} g
"""
        self.deltav_text.insert(1.0, deltav_info)
        
        # Update thruster status text
        self.prop_text.delete(1.0, tk.END)
        duty_cycle = (self.cumulative_burn_time / (self.current_time * 24) * 100) if self.current_time > 0 else 0
        total_orbits = self.current_time * self.current_orbit.get('revs_per_day', 0)
        thruster_info = f"""
Status:           {'🔥 FIRING' if self.is_firing else '❄️  OFF'}
Thrust:           1.25 mN
Power:            85 W (firing)
Cumulative Time:  {self.cumulative_burn_time:.1f} h
Duty Cycle:       {duty_cycle:.1f}%
Total Orbits:     {total_orbits:.0f}
Propellant Type:  Iodine (I₂)
System:           Busek BIT-3
"""
        self.prop_text.insert(1.0, thruster_info)
        
        # Update science text
        self.science_text.delete(1.0, tk.END)
        if self.phase == 'science':
            coverage = (self.psr_observations / 1000) * 100  # Target: 1000+ passes
            # Science phase: Oct 25, 2029 - Sep 29, 2030
            science_start = datetime(2029, 10, 25)
            science_end = datetime(2030, 9, 29)
            science_info = f"""
Status:          ACTIVE
Science Start:   {science_start.strftime('%b %d, %Y')}
Science End:     {science_end.strftime('%b %d, %Y')}
Total Passes:    {self.science_passes}
PSR Observations: {self.psr_observations}
Target Coverage: 1000+ passes
Current:         {coverage:.1f}%
Latitude Range:  80-90°S
Data Rate:       10.5 Mbps
"""
        elif self.phase in ['commissioning_orbit', 'spiral_down']:
            # Orbit commissioning happens during spiral down
            science_start = datetime(2029, 10, 25)
            science_info = f"""
Status:          CHECKOUT
Phase:           Orbit Circularization
Target Alt:      300 km circular
Science Ready:   {science_start.strftime('%b %d, %Y')}




"""
        else:
            next_phase = 'NRHO Capture' if self.phase in ['launch', 'tli', 'cruise', 'lga_flyby'] else 'Science Orbit'
            science_info = f"""
Status:          STANDBY
Science Phase:   Not Yet Started
Awaiting:        {next_phase}




"""
        self.science_text.insert(1.0, science_info)
        
        # Update plots
        self.update_plots()
    
    def update_plots(self):
        """Update all matplotlib plots"""
        if len(self.time_data) < 2:
            return
        
        # Clear all axes
        for ax in [self.ax1, self.ax2, self.ax3, self.ax4, self.ax5, self.ax6]:
            ax.clear()
        
        # Plot 1: Distance from Moon
        self.ax1.plot(self.time_data, self.distance_moon_data, '#8b5cf6', linewidth=2)
        self.ax1.set_title('Distance from Moon', fontsize=10, color='white', pad=10)
        self.ax1.set_xlabel('Day', color='white', fontsize=8)
        self.ax1.set_ylabel('Distance (km)', color='white', fontsize=8)
        self.ax1.set_xlim([0, max(self.time_data[-1], 10)])
        
        # Plot 2: Orbital Altitudes
        self.ax2.plot(self.time_data, self.periapsis_data, '#06b6d4', linewidth=2, label='Periapsis')
        self.ax2.plot(self.time_data, self.apoapsis_data, '#f43f5e', linewidth=2, label='Apoapsis')
        self.ax2.set_title('Orbital Altitudes', fontsize=10, color='white', pad=10)
        self.ax2.set_xlabel('Day', color='white', fontsize=8)
        self.ax2.set_ylabel('Altitude (km)', color='white', fontsize=8)
        self.ax2.legend(facecolor='#1e293b', edgecolor='#475569', labelcolor='white', fontsize=8)
        
        # Plot 3: Propellant Status
        self.ax3.plot(self.time_data, self.prop_remaining_data, '#22c55e', linewidth=2, label='Remaining')
        self.ax3.plot(self.time_data, self.prop_used_data, '#f59e0b', linewidth=2, label='Used')
        self.ax3.axhline(y=0.5, color='#ef4444', linestyle='--', linewidth=1, alpha=0.5, label='Reserve')
        self.ax3.set_title('Propellant Status', fontsize=10, color='white', pad=10)
        self.ax3.set_xlabel('Day', color='white', fontsize=8)
        self.ax3.set_ylabel('Mass (kg)', color='white', fontsize=8)
        self.ax3.legend(facecolor='#1e293b', edgecolor='#475569', labelcolor='white', fontsize=8)
        
        # Plot 4: Delta-V Budget
        self.ax4.plot(self.time_data, self.delta_v_used_data, '#f59e0b', linewidth=2, label='ΔV Used')
        self.ax4.plot(self.time_data, self.delta_v_remaining_data, '#22c55e', linewidth=2, label='ΔV Remaining')
        self.ax4.axhline(y=self.TOTAL_DELTA_V_CAPACITY, color='#3b82f6', linestyle='--', 
                        linewidth=1, alpha=0.5, label=f'Capacity ({self.TOTAL_DELTA_V_CAPACITY} m/s)')
        self.ax4.axhline(y=1385, color='#ef4444', linestyle='--', 
                        linewidth=1, alpha=0.5, label='Planned (1,385 m/s)')
        self.ax4.set_title('Delta-V Budget', fontsize=10, color='white', pad=10)
        self.ax4.set_xlabel('Day', color='white', fontsize=8)
        self.ax4.set_ylabel('ΔV (m/s)', color='white', fontsize=8)
        self.ax4.legend(facecolor='#1e293b', edgecolor='#475569', labelcolor='white', fontsize=7)
        
        # Plot 5: Spacecraft Velocity
        self.ax5.plot(self.time_data, self.velocity_data, '#a855f7', linewidth=2)
        self.ax5.set_title('Spacecraft Velocity', fontsize=10, color='white', pad=10)
        self.ax5.set_xlabel('Day', color='white', fontsize=8)
        self.ax5.set_ylabel('Velocity (km/s)', color='white', fontsize=8)
        
        # Plot 6: Science Coverage
        if self.phase == 'science' and self.science_passes > 0:
            science_days = [d - self.get_phase_start_day('science') 
                          for d in self.time_data if d >= self.get_phase_start_day('science')]
            science_obs = [self.psr_observations * (i+1) / len(science_days) 
                          for i in range(len(science_days))]
            if science_days:
                self.ax6.plot(science_days, science_obs, '#10b981', linewidth=2, label='Observations')
                self.ax6.axhline(y=1000, color='#22c55e', linestyle='--', linewidth=1, 
                               alpha=0.5, label='Target (1000)')
                self.ax6.legend(facecolor='#1e293b', edgecolor='#475569', labelcolor='white', fontsize=8)
        self.ax6.set_title('Science Coverage', fontsize=10, color='white', pad=10)
        self.ax6.set_xlabel('Days in Science Phase', color='white', fontsize=8)
        self.ax6.set_ylabel('PSR Observations', color='white', fontsize=8)
        
        # Apply styling to all axes
        for ax in [self.ax1, self.ax2, self.ax3, self.ax4, self.ax5, self.ax6]:
            ax.tick_params(colors='white', labelsize=8)
            for spine in ax.spines.values():
                spine.set_color('#475569')
            ax.grid(True, alpha=0.15, color='#475569', linestyle='--')
            ax.set_facecolor('#1e293b')
        
        self.canvas.draw()


if __name__ == "__main__":
    root = tk.Tk()
    app = SHINEMissionGUI(root)
    root.mainloop()
