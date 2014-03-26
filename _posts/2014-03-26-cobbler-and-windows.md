---
layout: post
title: "Installing Windows with cobbler"
description: ""
category: ""
tags: []
---
{% include JB/setup %}
When you run a dynamic data center enviroment, there are many tools that you use to ensure that everything runs smooth.  One of the most important tools you'll use is your provisioning system.  In a dynamic environment, systems are spun up and down frenquently, and having a proper set of tools to manage provisioning tasks keeps workloads low.

There are many provisioning tools floating around out there.  From comercial products, like [SCCM](http://www.microsoft.com/en-us/server-cloud/products/system-center-2012-r2/default.aspx) and [IBM's Tivolli Suite](http://www.ibm.com/software/tivoli/), to various open source and free solutions.  One of my favorites is [Cobbler](http://www.cobblerd.org/).  Cobbler works great for Linux and (most0 other unix like systems, but doesn't handle Windows so well.

Fortunatly, there is a way to use cobbler with windows, and even, integrate configuration management.  In this post, I'llexplor the steps required to provision Windows virtual and physical machines using cobbler.  Before we get to far, there's a few things you'll need:

*   A Technition machine

    This is the term that Microsoft uses to refer to a Windows system that is used to run the tools and other operations.  This machine can be any version of Windows, so long as the WAIK tools can run.

*   [The Windows Automated Installication Kit](http://www.microsoft.com/en-us/download/details.aspx?id=5753)

    The Windows AIK is a set of tools for generating custom install CDs, manipulating [Windows Image Format](http://en.wikipedia.org/wiki/Windows_Imaging_Format), or WIM, files, and creating Windows instalilation answer files.

*   A Windows install CD or ISO image.

    I used a Windows 7 Enterprise Edition (AMD64) ISO.  Since the installitation files will still come from this CD, you'll need the proper media for each Windows version you want to support.

*   Curl for windows

    To my knowledge, WinPE doesn't have any good way to get data via HTTP.  Curl is an easy way to add that functionality.  Note, be sure to use the version of curl that mached your architecture.  This example targets AMD64, but the 32 compat layer will be be installed (to reduce image size).  

*   A working Cobbler instance.

    Obviously, you'll need cobbler.  I highly recommend that you get cobbler working for Linux installs prior to attempting Windows.

Once all of your tools are installed and working, we should be ready to start.  The majority of the begining steps will need to be performed on your technition computer.  It should be noted that, even in a Windows environment, I tend to rely on a command prompt (powershell) for the majority of my work.  As such, most of the examples will be given as commands to be executed in a command intrepter.  Be sure that your path is set up properly before begining (beyond the scope of this tutorial).

---

Getting Started

There are several way to get a Windows installitation started.  The method I chose integrates well with cobbler, and is easy to generate and manipulate.  Were are going to build a custom [WindowsPE](http://en.wikipedia.org/wiki/Windows_Preinstallation_Environment) CD image that can be booted over the network, and use to start the install process.

First we'll need a working environment.  This is created with the copype utility from AIK.

    copype amd64 c:\winpe

This will create the directories and files we'll use to create our image, including a base Winpe.wim, which we'll modify to get our install working.  Let's go ahead and mount that WinPE image...  Again, AIK gives us the tool for the job:

    imagex /mountrw c:\winpe\winpe.wim 1 c:\winpe\mount

You could also use the dism tool.  Dism is a new utility that integrates many of the the AIK tools into a single application.  You'll actually need to use dism if you need to add drivers or packages to your WinPE image.  I'm more familiar with imagex, so that's what my examples will use.

We want to maximize the amount of work that cobbler does, but there's a few pre-install tasks that we'll need in order to work around the limitations of the windows install system.  To make things easyier when we need to make changes in the future, we'll modularize as much as we can.  To start things off, we need to create a configuration file for [winpeshl](http://technet.microsoft.com/en-us/library/cc766156.aspx).  The config file (in the example environment) will be c:\winpe\mount\windows\system32\winpeshl.ini.

    [LaunchApps]
    wpeinit
    %SYSTEMDRIVE%\local\init.cmd

This is a simple set of commands that winpeshl will execute to startup the windows shell.  In this case, we're calling wpeinit, then a script, which will get our install started.  Wpeinit is a WinPE utility that initializes the WindowsPE environment, including, loading any drivers that have been added to your WinPE image.  Now we'll need a couple of scripts to finish setting up our environment.  

Unfortunatly, I do not know of a way to pass commandline options into WinPE, so this is the one place that we'll need to hard code the host name of our cobbler server.  There are a couple of peices of information that will be needed to get our install going properly.  These will each be performed in init.cmd.  To keep things seperated, lets put everyting in %SYSTEMDRIVE%\local.  %SYSTEMDRIVE% is a windows environment variable that store the drive letter of the  partition that the windows system is on.  In WinPE, this is almost always X:, but to be safe, we'll use the env var.  So let's create a local scripts directory:

    mkdir c:\winpe\mount\local

and start creatng our scripts.  We'll start with setsysname.cmd (c:\winpe\mount\local\setsysname.cmd):

    @echo off
    
    set COBBLER_SERV=cobbler.example.net
    set COBBLER_MAC=

    for /f "tokens=1 delims= " %%H in ('nbtstat -n ^| find "UNIQUE"') do set COBBLER_HNAME=%%H
    for /f "tokens=4 delims= " %%M in ('nbtstat -a %COBBLER_HNAME% ^| find "MAC Address"') do set COBBLER_MAC=%%M
    for /f "tokens=1-6 delims=- " %%a in ('echo %COBBLER_MAC%') do set COBBLER_MAC=%%a:%%b:%%c:%%d:%%e:%%f

    for /f "delims= " %%S in ('curl -s http://%COBBLER_SERV%/cblr/svc/op/autodetect/HTTP_X_RHN_PROVISIONING_MAC_0/eth0%%20%COBBLER_MAC%') do set COBBLER_SYSNAME=%%S


Setsysname will create an environment variable (COBBLER_SYSNAME) with the system name based on the systems MAC address.  Note, this uses an unsupported feature of cobbler that could be removed in the future.  Again, we need to hard code the cobbler server hostname here.  With that done, let's create our init.cmd in c:\winpe\mount\local\init.cmd

    @echo off

    rem set COBBLER_SYSTEMNAME and COBBLER_SERV
    %SYSTEMDRIVE%\local\setsysname.cmd

    rem get the remainder of the init scripts
    curl -s -o %TEMP%/mountmedia.cmd http://%COBBLER_SERV%/cblr/svc/op/script/system/%COBBLER_SYSNAME%/?script=mountmedia.cmd
    curl -s -o %TEMP%/getks.cmd http://%COBBLER_SERV%/cblr/svc/op/script/system/%COBBLER_SYSNAME%/?script=getks.cmd
    curl -s -o %TEMP%/runsetup.cmd http://%COBBLER_SERV%/cblr/svc/op/script/system/%COBBLER_SYSNAME%/?script=runsetup.cmd

    rem run 'em
    call %TEMP%\mountmedia.cmd
    call %TEMP%\getks.cmd
    call %TEMP%\runsetup.cmd

Make sure you've added curl to your wim.  From the curl binary zipfile, copy dlls\*.* and bin\*.* to c:\winpe\mount\windows\system32.

That should conclude our WIM modifications.  Unmount it:

    imagex /unmount c:\winpe\mount /commit

and copy it into the ISO diretory:

    cp c:\winpe\winpe.wim c:\winpe\ISO\sources\boot.wim

Now, let's create a CD image.  This is done with the oscdimg tool:

    oscdimg -n -bc:\winpe\etfsboot.com c:\winpe\ISO c:\winpe\winpe_cobbler_amd64.iso

We have one file task that we'll need the technition computer for.  Fire up the Windows System Image Manager and create an answer file for your windows install.  How to do this is beyond the scope of this discussion, but [tutorials](http://technet.microsoft.com/en-us/library/cc749317.aspx) should be easy enough to find.

Now that we're done with the windows side, copy your custom WinPE ISO, your Windows 7 ISO, and answer file to your cobbler server, and store them in appropriate locations.  On my system (Ubuntu 13.10), I places my answer file in /var/lib/cobbler/kickstarts, my WinPE ISO in /var/lib/cobbler/isos, and left my Win7 ISO in my homedir (we actually need to extract it).

Mount the Windows 7 ISO someplace, and copy the contents to a location that you can share via samba.  If you do not plan to use the pxe_just_once feature of cobbbler, then there's no need to extract the contents of the ISO.  Just mount it, and share the directory.  If it's not already installed, install samba on your cobbler server, and add a share:

    [global]
    security = user
    guest account = nobody
    map to guest = Bad User

    [REMINST]
    browsable = true
    read only = no
    guest only = yes
    path = /var/windowsmedia
    public = yes
    available = yes

Adjust as is appropriate for your environment.  Our server is joined to an AD domain (security=ads), so we ran into a few problems getting things wokring just right.  The above should work for most cases, though.  Restart samba, and test that your share is working.  Since we use this method for several different versions of Windows, /var/windowsmedia has a sub-directory for each version of Windows we deploy via cobbler.  Now, add a new distro to cobbler, using syslinux's memdisk as the kernel:

    cobbler distro add --name=windows7-x86_64 --kernel=/usr/lib/syslinux/memdisk --initrd=/var/lib/cobbler/isos/winpe_amd64.iso --kopts="raw iso"

and a profile

    cobbler profile add --name=windows7-x86_64 --distro=windows7-x86_64 --kickstart=/var/lib/cobbler/kickstarts/win7-amd64-unattend.xml

Edit your answer file, and replace any bits (such as ComputerName with $system_name) with appropriate template variables.  Remember, the windows answer file will be passed through the same template engine used for kickstart and preseeds.  This means that you can use ksmeta vars, builtins, and  expressions (including snippets) like any other kickstart.  

We'll also need a couple of supporting scripts.  These will go in your scripts directory (/var/lib/cobbler/scripts on my system).  The first is mountmedia.cmd.  This script will mount your samba share, on the booted WinPE instance (it's run by init.cmd above)

    @echo off

    #set smb_srv = '\\\\%s' % ($http_server)

    echo Mounting Network Drive...
    net use Q: $smb_srv\REMINST "" /user:$http_server\nobody
    set COBBLER_MEDIA=Q:

Again, these are passed through cobbler's template engine, so feel free to get creative.  Be aware, WinPE's net use command expects a domain and username.  In my case, I used my cobbler server as my domain and nobody and the user, with no password.  Due to the "map to guest = Bad User" setting in our samba config, this will cause the share to be mounted as guest.  Of course, you can use real user names and passwords if you want.

getks.cmd

    @echo off

    echo Retreiving unattend.xml
    curl -s -o %TEMP%\unattended.xml http://%COBBLER_SERV%/cblr/svc/op/ks/system/%COBBLER_SYSNAME%

runsetup.cmd

    @echo off

    echo Starting setup...
    call %COBBLER_MEDIA%\win7\setup.exe /unattend:%TEMP%\unattended.xml

Now you're ready to add a system as you normally would.  If you are not using pxe_just_one, then you're done.  There's one final step that needs to be completed if you are using pxe_just_once.  You need a post install script to disables PXE.  In the directory where you extracted your Windows7 ISO, create sources/$oem$/$$/Setup and source/$oem$/$$/system32. Into Setup, place a copy of setsysname.cmd and rename it to setupcomplete.cmd.  Into system32 copy your curl dlls and executables.  Edit setupcomplete.cmd to look like

    @echo off
    
    set COBBLER_SERV=cobbler.example.net
    set COBBLER_MAC=

    for /f "tokens=1 delims= " %%H in ('nbtstat -n ^| find "UNIQUE"') do set COBBLER_HNAME=%%H
    for /f "tokens=4 delims= " %%M in ('nbtstat -a %COBBLER_HNAME% ^| find "MAC Address"') do set COBBLER_MAC=%%M
    for /f "tokens=1-6 delims=- " %%a in ('echo %COBBLER_MAC%') do set COBBLER_MAC=%%a:%%b:%%c:%%d:%%e:%%f

    for /f "delims= " %%S in ('curl -s http://%COBBLER_SERV%/cblr/svc/op/autodetect/HTTP_X_RHN_PROVISIONING_MAC_0/eth0%%20%COBBLER_MAC%') do set COBBLER_SYSNAME=%%S

    %SYSTEMROOT%/system32/curl -s http://%COBBLER_SERV%/cblr/svc/op/trig/mode/post/system/$COBBLER_SYSNAME%
    %SYSTEMROOT%/system32/curl -s http://%COBBLER_SERV%/cblr/svc/op/nopxe/system/$COBBLER_SYSNAME%

----

Conclusions

There's still a few details that I'd like to work out.  First is how to pass command line options (aka kopts) to WinPE on boot.  Being able to do that would eliminate the need for hard coding the name of the cobbler server into setsysname.cmd.  I'm not as familiar with WindowsPE and the windows installer as I'd like to be, but there doesn't seem to be a way to do it.  One possibility is creating a BCD for each profile/distro, and snagging that via TFTP during bootup (there seems to be a mechinism for using multiple BCDs during boot, but I'm not familiar with how to do it).  Using such a mechinism, I could retreive everything else without doing a discovery step.

There's also a small catch with bootfix.bin in the WinPE iso image.  This service looks for a botable partition on the hard drive, and presents the "press a key to boot DVD" message.  The windows install process involves several reboots, and all but the first must be from the hard drive.  If this is removed, then cobbler will retsrat the installer on each boot.  Obviously not what we want.  I could disable PXE earlier in the install, but that risks a bad install never restarting, again not a great option.  Of course, this only become a problem when the hard drive is already bootable (previous OS install).  In that instance, someone would have to be at the console to press a key on the first boot (starting the install for the first time).

As always, if you have suggestions or comments (especially if you understand the Windows install preocess better than I), shoot me an email.
