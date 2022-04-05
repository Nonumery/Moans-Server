start wsl -e bash -lic "pipenv run docker-compose up && exec wsl -li"
start wsl -e bash -lic "read -rsp $'Press enter to continue...\n' && pipenv run python3 main.py"