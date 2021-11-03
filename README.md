# WAGMI is an execution framework for systematic strategies.

It is very much a work in progress, IT CURRENTLY DOES NOT WORK!!

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

1. clone the repo
2. create a virtualenv (I recommend pyenv-virtualenv)
3. install the requirements 'pip install -r requirements.txt'
4. make a .env file (based on .env-example)
5. setup a database (connection string and password in the env file) - if you like, you can get a postgres running locally in docker using 'make runpg' then 'make createdb'
6. check everything is working: ./manage.py migrate (if not - fix any errors)
7. load the exchanges: ./manage.py loaddata exchanges.yaml
8. load the strategies: ./manage.py loaddata strategies.yaml
9. make a user: ./manage.py createsuperuser

## Either run it locally...

1. run it: ./manage.py runserver
2. go to: https://localhost:8000/wagmi/ and login.

## Or, run with docker-compose

1. Make sure you have docker and docker-compose is installed
2. run 
    2.1 docker-compose -f trading-server.yml up -d
    2.2 docker-compose -f trading-server.yml exec django python manage.py createsuperuser

3. go to: https://localhost:8000/wagmi/ and login.

## Contributing

Please ping me if you want to help!

The plan is:

1. Get this working for RW "yolo" on ftx.
2. Make sure the blotting is accurate (fills and fees)
3. Consider optimising execution (it currently just tries to place an aggressive order inthe order book)
4. Serve as a framework for other strategies.

## Coding guidelines

1. PEP8 - please use the code formatter, black: https://github.com/psf/black
2. docstrings - please use Google style docstrings: https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings
3. For all other style matters, please follow the google styleguide ofr python.
4. Tests - Please use pytest
5. Dependencies - please try to minimise them.
6. Simplicity - please don't try to be too clever; code should be as simple as possible to understand it's purpose.

## BSD License

Copyright (c) 2021, Rich Atkinson

Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE
