import os
import pandas as pd
from datetime import date, timedelta, datetime
from pydexcom import Dexcom
import garminconnect

# ─── INSTÄLLNINGAR ───────────────────────────────────
DEXCOM_USER     = " "
DEXCOM_PASS     = " "
DEXCOM_REGION   = "ous"

GARMIN_EMAIL    = " "
GARMIN_PASSWORD = " "

OUTPUT_FILE     = " "
# ─────────────────────────────────────────────────────

def hamta_dexcom_5min():
    print("Hämtar Dexcom-data...")
    try:
        dex = Dexcom(username=DEXCOM_USER, password=DEXCOM_PASS, region=DEXCOM_REGION)
        historik = dex.get_glucose_readings(minutes=1440, max_count=288)
        
        rader = []
        for v in historik:
            dt = pd.to_datetime(v.datetime).round("5min")
            rader.append({
                "timestamp": dt.strftime("%Y-%m-%d %H:%M"),
                "glukos": round(v.value / 18.0, 1)
            })
        
        df = pd.DataFrame(rader)
        if not df.empty:
            df = df.drop_duplicates(subset="timestamp")
        return df
    except Exception as e:
        print(f"Kunde inte hämta Dexcom-data: {e}")
        return pd.DataFrame(columns=["timestamp", "glukos"])


def hamta_garmin_5min():
    print("Hämtar Garmin-data (rullande 24 timmar)...")
    try:
        client = garminconnect.Garmin(GARMIN_EMAIL, GARMIN_PASSWORD)
        client.login()
        
        # LÖSNING: Hämta data för både igår och idag så att vi täcker hela Dexcom-fönstret
        idag_str = date.today().isoformat()
        igar_str = (date.today() - timedelta(days=1)).isoformat()
        
        stress_rader = []
        steg_rader = []
        puls_rader = []
        
        # Loopa igenom båda dagarna och samla all data i samma listor
        for dag in [igar_str, idag_str]:
            # 1. Stress
            try:
                stress_data = client.get_stress_data(dag)
                if stress_data and "stressValuesArray" in stress_data:
                    for punkt in stress_data["stressValuesArray"]:
                        if punkt[1] is not None and punkt[1] >= 0: # Rensa samtidigt bort -1 och -2 felkoder
                            dt = pd.to_datetime(punkt[0], unit="ms").round("5min")
                            stress_rader.append({"timestamp": dt.strftime("%Y-%m-%d %H:%M"), "stress": punkt[1]})
            except Exception: pass

            # 2. Steg
            try:
                steps_data = client.get_steps_data(dag)
                if steps_data:
                    for punkt in steps_data:
                        tid = punkt.get("startGMT") or punkt.get("startLocal")
                        antal_steg = punkt.get("steps", 0)
                        if tid and antal_steg > 0:
                            dt = pd.to_datetime(tid).round("5min")
                            steg_rader.append({"timestamp": dt.strftime("%Y-%m-%d %H:%M"), "steg": antal_steg})
            except Exception: pass

            # 3. Puls
            try:
                puls_data = client.get_heart_rates(dag)
                if puls_data and "heartRateValues" in puls_data:
                    for punkt in puls_data["heartRateValues"]:
                        if punkt[1] is not None:
                            dt = pd.to_datetime(punkt[0], unit="ms").round("5min")
                            puls_rader.append({"timestamp": dt.strftime("%Y-%m-%d %H:%M"), "puls": punkt[1]})
            except Exception: pass

        # Skapa DataFrames och rensa dubbletter
        df_stress = pd.DataFrame(stress_rader).drop_duplicates(subset="timestamp") if stress_rader else pd.DataFrame(columns=["timestamp", "stress"])
        df_puls = pd.DataFrame(puls_rader).drop_duplicates(subset="timestamp") if puls_rader else pd.DataFrame(columns=["timestamp", "puls"])
        
        if steg_rader:
            df_steg = pd.DataFrame(steg_rader).groupby("timestamp", as_index=False)["steg"].sum()
        else:
            df_steg = pd.DataFrame(columns=["timestamp", "steg"])

        # Slå ihop Garmin-datan
        garmin_kombinerad = pd.merge(df_stress, df_steg, on="timestamp", how="outer")
        garmin_kombinerad = pd.merge(garmin_kombinerad, df_puls, on="timestamp", how="outer")
        
        return garmin_kombinerad

    except Exception as e:
        print(f"Kunde inte hämta Garmin-data: {e}")
        return pd.DataFrame(columns=["timestamp", "stress", "steg", "puls"])


def main():
    # 1. Hämta från båda källorna
    dexcom_df = hamta_dexcom_5min()
    garmin_df = hamta_garmin_5min()
    
    if dexcom_df.empty and garmin_df.empty:
        print("Ingen data kunde hämtas från någon av källorna.")
        return

    # 2. Slå ihop dem baserat på tidstämpeln
    ny_data = pd.merge(dexcom_df, garmin_df, on="timestamp", how="outer")
    ny_data = ny_data.sort_values("timestamp").reset_index(drop=True)
    
    # 3. Hantera historisk fil om den finns
    if os.path.exists(OUTPUT_FILE):
        print(f"Hittade befintlig fil '{OUTPUT_FILE}'. Kombinerar historik...")
        gammal_data = pd.read_csv(OUTPUT_FILE)
        gammal_data = gammal_data.replace('-', pd.NA)
        
        # RÄTTNING: Om den gamla filen är helt tom på rader, strunta i concat och ta bara ny_data
        if gammal_data.dropna(how='all').empty:
            kombinerad = ny_data
        else:
            kombinerad = pd.concat([gammal_data, ny_data], ignore_index=True)
            kombinerad = kombinerad.groupby("timestamp", as_index=False).first()
    else:
        kombinerad = ny_data

    # 4. Snygga till ordningen på kolumnerna
    kolumner = ["timestamp", "glukos", "stress", "steg", "puls"]
    for kol in kolumner:
        if kol not in kombinerad.columns:
            kombinerad[kol] = None
            
    kombinerad = kombinerad[kolumner]
    kombinerad = kombinerad.sort_values("timestamp").reset_index(drop=True)
    
    # 5. Ersätt alla tomma rutor med '-'
    slutgiltig_df = kombinerad.fillna('-')
    
    # Spara till CSV
    slutgiltig_df.to_csv(OUTPUT_FILE, index=False)
    print(f"\nKlart! Sparade i formatet till '{OUTPUT_FILE}'.")
    print(f"Totalt antal rader i filen: {len(slutgiltig_df)}")

if __name__ == "__main__":
    main()