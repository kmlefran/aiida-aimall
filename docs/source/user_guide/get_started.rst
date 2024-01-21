===============
Getting started
===============

This guide was written for my group, but still including in docs for now - maybe you will find it useful. Near complete AiiDA setup and instructions.

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

You will be prompted in the quicksetup command, answer as suits you for profile name etc

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

    pip install aiida-aimall
    #verify that entry points are registered
    verdi plugin list aiida.calculations # should show aimall and gaussianwfx
    verdi plugin list aiida.parsers # should show aimqb.base and gaussianwfx
    verdi plugin list aiida.data # should shoul AimqbParameters
    verdi plugin list aiida.workflows # should show multifrag aimreor and g16opt

Step 8: Computer Setup
----------------------
You'll likely need to setup at least two computers: localhost(your desktop) and the remote cluster you are submitting to. To do this, it is easiest to use a .yml file.

First though, you need to ensure that you have an ssh key setup for the remote cluster. That is if you ssh username@cluster.computecanada.ca, you don't need to enter your password. Follow sshSetup_

Back to configuring the computer, here is an example yml file for the remote cluster cedar:
::

    label: "cedar"
    hostname: "cedar.computecanada.ca"
    transport: "core.ssh"
    scheduler: "core.slurm"
    work_dir: "/home/kgagnon/project/kgagnon/aiida"
    mpirun_command: "mpirun -np {tot_num_mpiprocs}"
    mpiprocs_per_machine: "4"
    description: "Cedar computer"
    default_memory_per_machine: "6553600"
    prepend_text: ""
    append_text: ""
    shebang: "#!/bin/bash"

In the directory that this cedar.yml is in, run::

    verdi computer setup --config cedar.yml

You will be prompted asking if you want to escape commands in double quotes. Type "N". This should bring you back to the command line. You then need to configure the computer. Now run::

    verdi -p your_aiida_profile computer configure core.ssh cedar4



For username, enter your DRAC username. (e.g. kgagnon)
Use the defaults for the rest as you are prompted. Defaults on Y/n options are shown in capitals. The full list here is:

::

    User name [chemlab]: kgagnon
    Port number [22]:
    Look for keys [Y/n]: Y
    SSH key file []:
    Connection timeout in s [60]:
    Allow ssh agent [Y/n]: Y
    SSH proxy jump []:
    SSH proxy command []:
    Compress file transfers [Y/n]: Y
    GSS auth [False]:
    GSS kex [False]:
    GSS deleg_creds [False]:
    GSS host [cedar.computecanada.ca]:
    Load system host keys [Y/n]: Y
    Key policy (RejectPolicy, WarningPolicy, AutoAddPolicy) [RejectPolicy]:
    Use login shell when executing command [Y/n]: Y
    Connection cooldown time (s) [30.0]:

Now, test to make sure that the computer workflows::

    verdi computer test cedar

Should return all passes

You need to do similar steps for the localhost computer. yml file. Here is the yml for localhost

::

    hostname: "localhost"
    transport: "core.local"
    scheduler: "core.direct"
    work_dir: "/Users/chemlab/.aiida_run"
    mpirun_command: "mpirun -np {tot_num_mpiprocs}"
    mpiprocs_per_machine: "4"
    description: "localhost computer"
    prepend_text: ""
    append_text: ""
    shebang: "#!/bin/bash"

Still use N for escaping command line arguments

You need to configure and test it again, similar to before but with less prompts

::

    verdi -p your_aiida_profile computer configure core.local localhosttest

    Use login shell when executing command [Y/n]: n
    Connection cooldown time (s) [0.0]:

    verdi computer test localhost

Should return passes

Step 9: Setup Code plugins
--------------------------
Again, use .yml files like those shown here:

e.g. for AIMAll:
::

    label: 'aimall'
    description: 'aimall'
    default_calc_job_plugin: 'aimall'
    filepath_executable: '/Applications/AIMAll/AIMQB.app/Contents/MacOS/aimqb'
    computer: 'localhost'
    prepend_text: ' '
    append_text: ' '

e.g. for gaussian::

    label: 'gaussian'
    description: 'gaussian'
    default_calc_job_plugin: 'gaussianwfx'
    filepath_executable: '/opt/software/gaussian/g16.c01/g16'
    computer: 'cedar'
    prepend_text: 'module load gaussian/g16.c01'
    append_text: ' '

For both, run (changing yml file name)
::

    verdi code create core.code.installed --config aimall.yml

And N for double quotes again

And with that, AiiDA should be all setup!

Usage
+++++

A quick demo of how to submit a calculation:

Write example here

.. _AiidaSetup: https://aiida.readthedocs.io/projects/aiida-core/en/latest/intro/install_conda.html#intro-get-started-conda-install
.. _PostGresSQl: https://postgresapp.com/
.. _Conda: https://docs.conda.io/en/latest/
.. _sshSetup: https://docs.alliancecan.ca/wiki/SSH_Keys
