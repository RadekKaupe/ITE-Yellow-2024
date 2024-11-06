User, heslo, host a název, které jsou třeba k připojení k db, budou uložené v samostatném .env file, abych na github nesdílel hesla k mojí personal datab ázi (a v budoucnu k naší školní db).

Skript db.py/db.ipynb se k db připojí a vytvoří tam prázdné tabulky Team a Sensor data.

Pro založení db na VM, bude třeba nainstalovat postgres, založit tam uživatele a poté se řídit **create_a_db.txt** . 