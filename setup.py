from setuptools import setup, find_packages
setup(
    name = "flexbot",
    version = "0.1",
    packages = find_packages(),

    install_requires = [
        'slacker>=0.8.6',
        'psycopg2>=2.6.1',
        'cherrypy>=4.0.0',
        'pyyaml>=3.11',
        'pystache>=0.5.4'
    ],

    author = "Brandon Shin, Miles Yucht",
    author_email = "mgyucht@gmail.com",
    description = "A fun framework for incorporating more exercise into your life at work through Slack.",
    license = "MIT",
    keywords = "slack slackbot exercise"
)
