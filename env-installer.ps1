


"Installing Nuget packager..."
Register-PackageSource -Name Nuget -Location "http://www.nuget.org/api/v2" –ProviderName Nuget -Trusted

#--- PYTHON INSTALL AND CONFIGURATION ---#
"Find and install Python 3.10.2..."
find-package python -MaximumVersion "3.10.2" | install-package -Scope CurrentUser

# find the path of Python installation
get-package python | % source

# To get the current USER Path
[System.Environment]::GetEnvironmentVariable('Path', 'User')

# To set the current USER Path
[System.Environment]::SetEnvironmentVariable('Path', $newPathInSingleStringSeparatedByColumn, 'User')

#--- Allure configuration ---#
[Environment]::SetEnvironmentVariable("ALLURE_NO_ANALYTICS","1","User")

# https://git-scm.com/download/win
"Getting and installing Git..."
winget install --id Git.Git -e --source winget

"Create Venv for the automation..."
python -m venv venv

"Activating environment..."
.\venv\Scripts\activate

"Install requirements..."
pip install -r .\resources\requirements.txt

# Our package to RestAPI for the management
pip install --extra-index-url http://nexus.ensilo.local:8081/repository/ensilo-cloud-pypi-3.0/simple --trusted-host nexus.ensilo.local ensilo-platform-rest --upgrade

