pyinstaller --clean -y -n "Rover RB200 Configurator" --add-data=".\logo.png;." --add-data=".\icon.ico;." --icon=".\icon.ico" --onefile --noconsole .\main.py