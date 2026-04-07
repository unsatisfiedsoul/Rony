def calculate_actual_flow(normalized_flow, pressure_mbar, temp_celsius):
    """
    Calculates Actual Flow (m3/hr) from Normalized Flow (Nm3/hr).
    Standard Reference (Normal) Conditions:
    Pressure (Pn): 1013.25 mbar
    Temperature (Tn): 0°C (273.15 K)
    """
    # Reference Constants
    P_NORMAL = 1013.25  # mbar
    T_NORMAL_K = 273.15  # Kelvin
    
    # Convert Actual Temperature to Kelvin
    t_actual_k = temp_celsius + 273.15
    
    # Actual Flow Formula: Qa = Qn / ((Pa / Pn) * (Tn / Ta))
    actual_flow = normalized_flow / ((pressure_mbar / P_NORMAL) * (T_NORMAL_K / t_actual_k))
    
    return actual_flow

def main():
    print("Actual Flow Calculator")
    nm3_hr = float(input("Enter Normalized Flow (Nm3/hr): "))
    p_actual_mbar = float(input("Enter Pressure (mbar): "))
    t_actual_c = float(input("Enter Temperature (°C): "))
    
    actual_m3_hr = calculate_actual_flow(nm3_hr, p_actual_mbar, t_actual_c)
    print(f"Actual Flow: {actual_m3_hr:.2f} m3/hr")

if __name__ == "__main__":
    main()
