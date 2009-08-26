/*
    Copyright (C) 2009  Jiri Moskovcak (jmoskovc@redhat.com)
    Copyright (C) 2009  RedHat inc.

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License along
    with this program; if not, write to the Free Software Foundation, Inc.,
    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
    */

#ifndef CRASHWATCHER_H_
#define CRASHWATCHER_H_

#include <string>
#include <sys/inotify.h>
#include <glib.h>
#include <pthread.h>
#include "MiddleWare.h"
#include "Settings.h"

#ifdef ENABLE_DBUS
    #include "CommLayerServerDBus.h"
#elif ENABLE_SOCKET
    #include "CommLayerServerSocket.h"
#endif
#include "CommLayerInner.h"

// 1024 simultaneous actions
#define INOTIFY_BUFF_SIZE ((sizeof(struct inotify_event)+FILENAME_MAX)*1024)

#define VAR_RUN_LOCK_FILE   VAR_RUN"/abrt.lock"
#define VAR_RUN_PIDFILE     VAR_RUN"/abrt.pid"


class CCrashWatcher
:  public CObserver
{
    public:
        CCrashWatcher();
        virtual ~CCrashWatcher();

    public:
        /* Observer methods */
        virtual void Status(const std::string& pMessage, const std::string& pDest="0");
        virtual void Debug(const std::string& pMessage);
        virtual void Warning(const std::string& pMessage);
};

vector_crash_infos_t GetCrashInfos(const std::string &pUID);
uint64_t CreateReport_t(const std::string &pUUID,const std::string &pUID, const std::string &pSender);
bool DeleteDebugDump(const std::string& pUUID, const std::string& pUID);
map_crash_report_t GetJobResult(uint64_t pJobID, const std::string& pSender);

/* plugins related */
vector_map_string_string_t GetPluginsInfo();
map_plugin_settings_t GetPluginSettings(const std::string& pName, const std::string& pUID);
void SetPluginSettings(const std::string& pName, const std::string& pUID, const map_plugin_settings_t& pSettings);
void RegisterPlugin(const std::string& pName);
void UnRegisterPlugin(const std::string& pName);

#endif /*CRASHWATCHER_H_*/
