# WAGMI is an execution framework for systematic strategies.

It is very much a work in progress, please don't expect it to work!

## Architecture

The Django framework ties this project together and so a basic knowledge of Django is very useful if you want to work on this.

This has no dependencies on GCP or AWS, a DockerFile is provided as a deployment option. There is also a Makefile with some handy commands to get up and running.

Scheduling of tasks uses apscheduler, wrapped in django_apscheduler.

There are two key apps, "sizing" and "execution". Other apps can be added as strategies. The only strategy app included is "yolo", which is a RobotWealth strategy and requires a Robot Wealth API key. See https://robotwealth.com/.

The Sizing app collects Strategy Position Requests from each strategy, and then sizes the resultant trades based on the capital allocated to each strategy. The Sizing app then resolves the combined aggregate Target Positions for each Security.

The Execution app compares the actual account positions on the Exchange to the Target Positions, calculates the delta, and places an order for each Security to bring the actual account positions in line with the Target Positions.

All of this is logged, including fees, arrtival prices and fill prices.

## Status

Some of the above works, some is incomplete. I ripped this code out of another project with the view of creatign a combined execution framework that can be used with a number of strategies on a number of different exchanges. For the purpose of simplicity, I have ripped out all of the IB execution code and other strategies (that aren't really for the public domain).

## Getting Started

clone the repo
create a virtualenv (I recommend pyenv-virtualenv)
install the requirements 'pip install -r requirements.txt'
make a .env file (based on .env-example)
setup a database (connection string and password in the env file) - if you like, you can get a postgres running locally in docker using 'make runpg' then 'make createdb'

check everything is working: ./manage.py migrate (if not - fix any errors)
load the fixtures: ./manage.py loaddata exchanges.yaml
make a user: ./manage.py createsuperuser
run it: ./manage.py runserver
go to: https://localhost:8000/wagmi/ and login.

## Run with docker-compose

1. Make sure you have docker and docker-compose is installed
2. run 
    2.1 docker-compose -f trading-server.yml up -d
    2.2 docker-compose -f trading-server.yml exec django python manage.py createsuperuser

3. go to: https://localhost:8000/wagmi/ and login.

## Contributing

Please use create a fork and submit pull requests!

The plan is:

1. Get this working for RW "yolo" on ftx.
2. Make sure the blotting is accurate (fills and fees)
3. Consider optimising execution (it currently just tries to place an aggressive order inthe order book)
4. Serve as a framework for other strategies.

## BSD License

Copyright (c) 2021, Rich Atkinson

Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE
