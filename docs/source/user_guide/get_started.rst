===============
Getting started
===============

This page should contain a short guide on what the plugin does and
a short example on how to use the plugin.

Installation
++++++++++++

These steps will guide you through the complete setup of AiiDA on Apple M1, OS Ventura 13.5.1. The steps are adapted from AiidaSetup_

Step 1: Install Brew
--------------------
Run the following in terminal to install homebrew::

    cd /opt/
    mkdir homebrew && curl -L https://github.com/Homebrew/brew/tarball/master | tar xz --strip 1 -C homebrew
    eval "$(homebrew/bin/brew shellenv)"
    brew update --force --quiet
    chmod -R go-w "$(brew --prefix)/share/zsh"

Step 2: Install Docker
----------------------
Using brew, install Docker::

    brew install --cask docker

Run the app and do first time setup. Ensure it is running by seeing the whale in the top right. Make sure to launch this again on reboots

Step 3: Install RabbitMQ with AiiDA compatible version
------------------------------------------------------
Run the following to setup rabbitmq with an AiiDA compatible version::

    brew install rabbitmq git python
    docker run --detach --hostname aiida-rabbitmq --name aiida-rabbitmq-server --restart=unless-stopped --publish=127.0.0.1:5671:5671 --publish=127.0.0.1:5672:5672 --mount=type=volume,src=rabbitmq-volume,dst=/var/lib/rabbitmq rabbitmq:3.7.28
    brew services start rabbitmq

This should now start at launch.

Step 4: Download and setup PostGresSQL
--------------------------------------
Download PostGresSQL_

Launch the app and click initialize

In Terminal::

    sudo mkdir -p /etc/paths.d && echo /Applications/Postgres.app/Contents/Versions/latest/bin | sudo tee /etc/paths.d/postgresapp

Should now be set up and running in the background. Note the elephant in the top right. Note that on reboots you should make sure you start this back up for AiiDA

Step 5: install AiiDA
---------------------
This assumes that conda is installed already. Conda_::

    conda create -yn aiida-env -c conda-forge aiida-core
    conda activate aiida-env

Step 6: Setup profile
---------------------
::

    verdi quicksetup
    verdi profile setdefault <PROFILE>

Note that in the second line, <PROFILE> should be whatever you set in the prompts for verdi quicksetup.

Step 7: Launch Daemons and Verify
---------------------------------
::

    verdi daemon start 2 #rerun every reboot
    verdi status

Should result in all processes working

Step 8: Install aiida-aimall
----------------------------
::

    git clone https://github.com/kmlefran/aiida-aimall .
    cd aiida-aimall
    pip install -e .  # also installs aiida, if missing (but not postgres)
    #verify that entry points are registered
    verdi plugin list aiida.calculations # should show aimall and gaussianwfx
    verdi plugin list aiida.parsers # should show aimqb.base and gaussianwfx
    verdi plugin list aiida.data # should shoul AimqbParameters
    verdi plugin list aiida.workflows # should show multifrag aimreor and g16opt

Step 9: Setup Code plugins
--------------------------
Write more info here

Usage
+++++

A quick demo of how to submit a calculation:

Write example here

.. _AiidaSetup: https://aiida.readthedocs.io/projects/aiida-core/en/latest/intro/install_conda.html#intro-get-started-conda-install
.. _PostGresSQl: https://postgresapp.com/
.. _Conda: https://docs.conda.io/en/latest/
