# import os, subprocess
# import oracledb

# os.environ["TZDIR"] = r"C:\Oracle\Middleware\Oracle_Home\oracore\zoneinfo"
# os.environ["ORA_TZFILE"] = r"C:\Oracle\Middleware\Oracle_Home\oracore\zoneinfo\timezlrg.dat"

# env = os.environ.copy()

# subprocess.run([
#     r"C:\Users\Tuttagunta Sowmya\.conda\envs\mlops3.11\Scripts\dvc.exe",
#     "import-db", "--conn", "oracle", "--table", "ANOMALIES", "-o", "my_table.csv"
# ], check=True, env=env)



import oracledb
oracledb.init_oracle_client(lib_dir=r"C:\Oracle\instantclient_23_8")
print("Thick mode?", oracledb.is_thin_mode())
