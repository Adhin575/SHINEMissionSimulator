🛰️ SHINE Mission Complete Simulator
A Python-based desktop GUI application that simulates the full mission timeline of the SHINE spacecraft — from Earth launch through lunar science operations to controlled deorbit. Built with Tkinter and Matplotlib, the simulator steps through each mission phase in real time, tracking orbital mechanics, propellant consumption, delta-V budget, and science observations.

Mission Overview
The SHINE mission is a small satellite (CubeSat-class) designed to study the Moon's permanently shadowed regions (PSRs) at the lunar south pole. The spacecraft uses an iodine-propellant electric propulsion system (Busek BIT-3) and follows a multi-phase trajectory from Earth to a circular 300 km polar lunar orbit.
Mission Timeline:
PhaseDateDurationLaunch / ICPS DeploymentMar 1, 2029—CommissioningMar 1, 2029~10 hoursTrans-Lunar Injection (TLI)Mar 1, 2029~2 hoursTranslunar CruiseMar 1–6, 20295 daysLunar Gravity Assist FlybyMar 6, 2029~12 hoursSun-Earth TransferMar 6 – Aug 17, 2029163 daysNRHO CaptureAug 17–24, 2029~6.5 daysNRHO StagingAug 24 – Sep 13, 202920 daysSpiral Down (1450 km → 300 km)Sep 13 – Oct 25, 202942 daysScience OperationsOct 25, 2029 – Sep 29, 2030339 daysDeorbitSep 30, 20301 day
Total Mission Duration: ~515 days

Features

Full phase-by-phase simulation of all mission segments with accurate durations derived from the mission Gantt chart
Real-time orbital parameter tracking — semi-major axis, eccentricity, periapsis, apoapsis, inclination, orbital period, and revolutions per day
Propellant budgeting — tracks iodine propellant consumed and remaining against the 1.5 kg tank capacity, with a 685 g margin above the 815 g mission requirement
Delta-V accounting — monitors ΔV used and remaining against the 2,483 m/s total capacity, with a 1,385 m/s planned mission budget
Thruster system telemetry — firing status, cumulative burn time, duty cycle, and thruster specifications for the Busek BIT-3 ion thruster (1.25 mN thrust, 85 W)
Science operations tracking — PSR observation pass count, target coverage progress (1,000+ passes), and latitude coverage (80–90°S)
6 live-updating plots:

Distance from Moon
Orbital altitudes (periapsis & apoapsis)
Propellant status (remaining vs. used)
Delta-V budget
Spacecraft velocity
Science coverage (PSR observations)


Adjustable simulation speed (1× to 100×)
Dark-themed UI styled for an operations-center aesthetic


The GUI window will open at 1600×950 pixels. Click ▶ Start Mission to begin the simulation. Use the speed slider to accelerate through longer phases such as the Sun-Earth transfer and science operations.

GUI Layout
┌──────────────────────────────────────────────────────┐
│              SHINE Mission Complete Simulator         │
│  Launch Date | Science Start | Science End | End Date │
├──────────────────────────────────────────────────────┤
│  [▶ Start]  [↻ Reset]  [Speed: ──────]  ● Status     │
│  Progress Bar + Phase Timeline                        │
├────────────┬────────────┬─────────────┬──────────────┤
│ Spacecraft │ Trajectory │ ΔV &        │ Thruster  │ Science │
│ State      │ & Orbit    │ Propulsion  │ System    │ Ops     │
├────────────┴────────────┴─────────────┴──────────────┤
│  [Moon Dist] [Altitudes] [Propellant]                 │
│  [Delta-V]   [Velocity]  [Coverage]                   │
└──────────────────────────────────────────────────────┘

Orbital Mechanics Notes
The simulator uses simplified but physically-grounded models:

Orbital period is computed from Kepler's third law: T = 2π √(a³/μ)
ΔV expenditure follows the rocket equation: ΔV = Isp × g₀ × ln(m₀/m_f)
Lunar gravitational parameter: μ = 4,902.8 × 10⁹ m³/s²
Lunar radius: 1,737.4 km
The NRHO (Near Rectilinear Halo Orbit) is modeled at 1,450 km periapsis × 69,500 km apoapsis, 90° inclination, 6.56-hour period

Spacecraft Specifications
Parameter              Value
Dry Mass               12 kg
Propellant Mass        1.5 kg (iodine, I₂)
Propulsion System      Busek BIT-3 ion thruster
Thrust                 1.25 mN
Specific Impulse (Isp) 2,500 s
Power (firing)         85 W
Max ΔV Capacity        2,483 m/s
Mission ΔV Budget      1,385 m/s
Science Orbit          300 km circular, 90° inclination
