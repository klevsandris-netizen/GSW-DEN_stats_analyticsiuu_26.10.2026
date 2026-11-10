from datetime import datetime
import pandas as pd
import sqlite3
import os
from pathlib import Path
import logging


#from here we are taking our raw data of the Golden State Warriors boxscore from the match Golden State Warriors Denver Nuggets october 26th, using pathlib :)
SCRIPT_DIR = Path(__file__).resolve().parent

PROJECT_DIR = SCRIPT_DIR.parent

input_path = PROJECT_DIR / "csv_filesiuu" / "gsw_rawiu.csv"
clean_data_path = PROJECT_DIR / "csv_filesiuu" / "gsw_cleaniu.csv"
database_path = PROJECT_DIR / "GSWdatabaseiu" / "gswiu.db"
logs_path = PROJECT_DIR /'logsmiau'/ 'pipeline.logs'

os.makedirs(logs_path.parent, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),                            
        logging.FileHandler(logs_path, encoding='utf-8')  
    ]
)
#Making data quality check for security :)
def validate_data(df: pd.DataFrame):

    logging.info("Starting Data Quality checks! :)")
    
    if df['Player'].isnull().any() or (df['Player'] == '').any():
        raise ValueError("DQ ERROR: Found empty or null Player names!")

    if (df['PTS'] < 0).any():
        raise ValueError("DQ ERROR: Points (PTS) cannot be negative!")
        
    if (df['FG'] > df['FGA']).any():
        raise ValueError("DQ ERROR: Field Goals Made (FG) cannot exceed Field Goal Attempts (FGA)!")

    if not df['FG%'].between(0.0, 1.0).all():
        raise ValueError("DQ ERROR: FG% values must be between 0.0 and 1.0!")

    logging.info("✅ Data Quality Check passed successfully. Congrats! :)")


#here we are reading our CSV file and replacing NaN values on 0 (but it is better to check all the stats and make stats into integers and after replacing Nan on 0...) :) 

def process_boxscore(input_path: Path, clean_output_path: Path, game_date: str, team: str, opponent: str):
 df = pd.read_csv(input_path,skiprows=2) #.fillna(0)


 df = df.rename(columns={'Starters': 'Player'})

 if '-9999' in df.columns:
    df = df.drop(columns=['-9999'])

 df = df[df['Player'] != 'Team Totals'].copy()


 num_columns = ['FG', 'FGA', 'FG%', '3P', '3PA', '3P%', 'FT', 'FTA', 'FT%', 
                'ORB', 'DRB', 'TRB', 'AST', 'STL', 'BLK', 'TOV', 'PF', 'PTS', 'GmSc', '+/-']
#transforming all the stats into integers or floats and errors = 'coerce' is a defensive tools against NaN(-,. such values and so on..) also we have 'raise' and 'ignore' :) 
 for num in num_columns:
    if num in df.columns:
     df[num] = pd.to_numeric(df[num], errors = 'coerce').fillna(0)

 logging.info(" Data cleaning was made successfully! :) ")     

#creating metadata for making our database universal(we can add others stats from other matches and do not be confused!:) and making date by ISO standarts for simplifying sorting and sql requests((( sorry...
 file_time_created = datetime.now().strftime('%Y-%m-%d %H:%M:%S')


 df['game_date'] = game_date 
 df['team'] = team 
 df['opp'] = opponent 
 df['source_fileiuu'] = input_path.name 
 df['time_file_loadedmiau'] = file_time_created

 validate_data(df)

#let us make the LOAD of Files

 df.to_csv(clean_output_path, index=False)

 logging.info(f"CSV files was saved in: {clean_output_path}")

#database
 os.makedirs(database_path.parent, exist_ok=True)

 logging.info(f"Connecting to SQLite database: {database_path}")

 conn = sqlite3.connect(database_path)
 #making our database secured if we want to execute our pipeline one more time it will not duplicate the data to our database :)
 cursor = conn.cursor()
 cursor.execute(
   "DELETE FROM nba_stats WHERE game_date = ? AND team = ? AND opp = ?", 
    (game_date, team, opponent)
)
 conn.commit()

 df.to_sql('nba_stats',conn, if_exists ='append',index = False)
 conn.close()

 logging.info(f"NBA Match {team} vs {opponent} was loaded to SQL database successfully! :) ")

#running our pipeline and making addinitonal dataframes for making it easy to find each stats of the match ;)
if __name__ == "__main__":
    process_boxscore(
        input_path=input_path,
        clean_output_path=clean_data_path,
        game_date="2026-10-26",
        team="GSW",
        opponent="DEN"
    )



    logging.info(f"ETL-pipeline of the file {input_path.name} was successfully created. Congrats iuu! :) ")