from setuptools import setup, find_packages
setup(
    name = "slackbot-workout",
    version = "0.3",
    packages = find_packages(),

    install_requires = [
        'slacker>=0.8.6',
        'psycopg2>=2.6.1',
        'cherrypy>=4.0.0',
        'pyyaml>=3.11'
    ],

    author = "Brandon Shin, Miles Yucht",
    author_email = "mgyucht@gmail.com",
    description = "A fun framework for incorporating more exercise into your life at work through Slack.",
    license = "MIT",
    keywords = "slack slackbot exercise"
)
