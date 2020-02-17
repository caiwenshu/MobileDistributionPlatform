# -*- coding: utf-8 -*-
# This file is part of Androguard.
#
# Copyright (C) 2010, Anthony Desnos <desnos at t0t0.fr>
# All rights reserved.
#
# Androguard is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Androguard is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Androguard.  If not, see <http://www.gnu.org/licenses/>.

# import bytecode


from xml.dom import minidom
import commands
import os
# import the logging library
import logging

import shutil

# Get an instance of a logger
logger = logging.getLogger("django")

def parse(filePath):
    f = filePath

    dirname = os.path.dirname(f)
    basename = os.path.basename(f)
    base = basename.split('.')[0]

    unzipDir = dirname + "/" + base

    comm = 'apktool d -f ' + f + ' -o ' + unzipDir
    status, output = commands.getstatusoutput(comm)

    # status = 0
    logger.info("&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&")
    logger.info(f)
    logger.info(status)
    logger.info(output)
    package = ""
    versionCode = ""
    versionName = ""
    label = ""
    appName = ""

    if status == 0:

        logger.info(unzipDir)
        logger.info(os.path.exists(unzipDir))
        if os.path.exists(unzipDir):

            manifest = "/AndroidManifest.xml"
            strings = "/res/values/strings.xml"
            yml = "/apktool.yml"

            apktoolYml = open(unzipDir + yml)

            for line in apktoolYml.readlines():

                if line.find("versionCode:") >= 0:

                    code = line.split(":")[1].replace( "'", "").replace( " ", "").replace( "\n", "")
                    versionCode = code
                    logger.info(code)

                if line.find("versionName") >= 0:

                    name = line.split(":")[1].replace( " ", "").replace( "\n", "")
                    versionName = name
                    logger.info(name)

            manifestDom = minidom.parse(unzipDir + manifest)
            stringsDom = minidom.parse(unzipDir + strings)

            package = manifestDom.documentElement.getAttribute("package")

            for item in manifestDom.getElementsByTagName("application"):
                label = item.getAttribute("android:label").replace("@string/", "")
                icon = item.getAttribute("android:icon").replace("@mipmap/", "")

            for item in stringsDom.getElementsByTagName("string"):
                name = item.getAttribute("name")

                # print name
                if name == label:
                    appName = item.childNodes[0].nodeValue.strip()

            icon_path_v4 = os.path.join(unzipDir, "res/mipmap-xxhdpi-v4/%s.png" % icon)
            icon_path_xxh = os.path.join(unzipDir, "res/mipmap-xxhdpi/%s.png" % icon)
            icon_path_xh = os.path.join(unzipDir, "res/mipmap-xhdpi/%s.png" % icon)

            icon_path = ""
            if os.path.isfile(icon_path_v4):
                icon_path = icon_path_v4
            elif os.path.isfile(icon_path_xxh):
                icon_path = icon_path_xxh
            elif os.path.isfile(icon_path_xh):
                icon_path = icon_path_xh

            logger.info("**************")
            logger.info(package)
            logger.info(versionCode)
            logger.info(versionName)
            logger.info(label)
            logger.info(appName)
            logger.info("icon path: %s" % icon_path)
            logger.info("unzip dir: %s" % unzipDir)


        # if os.path.exists(unzipDir):
        #     shutil.rmtree(unzipDir)

    return (status, package, versionCode, versionName, appName, icon_path ,unzipDir)


def rm_unzip_dir(unzip_dir):
    if os.path.exists(unzip_dir):
        shutil.rmtree(unzip_dir)