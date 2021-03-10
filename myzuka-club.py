#!/usr/bin/env python3
# -*- coding: utf-8 -*- 

# This work is free. You can redistribute it and/or modify it under the
# terms of the Do What The Fuck You Want To Public License, Version 2,
# as published by Sam Hocevar.  See the COPYING file for more details.

# requires installation of the following additional modules: PySocks and Beautifulsoup4

# Changelog:
# 5.6: better support for Tor socks proxy, and support for "requests" module instead of "urllib.request", because
# cloudflare seems to block more "urllib.request" than "requests", even with the same headers...

import re
import sys
import os
import signal
import time
import random
import socks
import socket
import html
import argparse
import traceback
from multiprocessing import Pool
from bs4 import BeautifulSoup

site = "http://myzuka.club"
userequests = 1
version = 5.6
useragent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.122 Safari/537.36"
covers_name = "cover.jpg"

def script_help(version, script_name):
    description = "Python script to download albums from %s, version %s." % (site, version)
    help_string = description + """

------------------------------------------------------------------------------------------------------------------
################## To download an album, give it an url with '/Album/' in it #####################################
------------------------------------------------------------------------------------------------------------------
user@computer:/tmp$ %s [-p /path] %s/Album/630746/The-6-Cello-Suites-Cd1-1994
** We will try to use 3 simultaneous downloads, progress will be shown **
** after each completed file but not necessarily in album's order. **

Artist: Johann Sebastian Bach
Album: The 6 Cello Suites (CD1)
Year: 1994
cover.jpg                                                 00.01 of 00.01 MB [100%%]
05_johann_sebastian_bach_maurice_gendron_bwv1007_menuets_myzuka.mp3        07.04 of 07.04 MB [100%%]
01_johann_sebastian_bach_maurice_gendron_bwv1007_prelude_myzuka.mp3        05.57 of 05.57 MB [100%%]
03_johann_sebastian_bach_maurice_gendron_bwv1007_courante_myzuka.mp3        05.92 of 05.92 MB [100%%]
06_johann_sebastian_bach_maurice_gendron_bwv1007_gigue_myzuka.mp3        04.68 of 04.68 MB [100%%]
04_johann_sebastian_bach_maurice_gendron_bwv1007_sarabande_myzuka.mp3        07.06 of 07.06 MB [100%%]
[...]

It will create an "Artist - Album" directory in the path given as argument (or else in current
 directory if not given), and download all songs and covers available on that page.


------------------------------------------------------------------------------------------------------------------
################## To download all albums from an artist, give it an url with '/Artist/' in it ###################
------------------------------------------------------------------------------------------------------------------

user@computer:/tmp$ %s [-p /path] %s/Artist/7110/Johann-Sebastian-Bach/Albums
** We will try to use 3 simultaneous downloads, progress will be shown **
** after each completed file but not necessarily in album's order. **
** Warning: we are going to download all albums from this artist! **

Artist: Johann Sebastian Bach
Album: The 6 Cello Suites (CD1)
Year: 1994
cover.jpg                                                 00.01 of 00.01 MB [100%%]
05_johann_sebastian_bach_maurice_gendron_bwv1007_menuets_myzuka.mp3        07.04 of 07.04 MB [100%%]
01_johann_sebastian_bach_maurice_gendron_bwv1007_prelude_myzuka.mp3        05.57 of 05.57 MB [100%%]
03_johann_sebastian_bach_maurice_gendron_bwv1007_courante_myzuka.mp3        05.92 of 05.92 MB [100%%]
[...]

Artist: Johann Sebastian Bach
Album: Prelude and Fugue in E Minor, BWV 548
Year: 1964
cover.jpg                                                 00.01 of 00.01 MB [100%%]
01_johann_sebastian_bach_praeludium_myzuka.mp3            09.51 of 09.51 MB [100%%]
02_johann_sebastian_bach_fuga_myzuka.mp3                  10.80 of 10.80 MB [100%%]
** ALBUM DOWNLOAD FINISHED **

[...]


It will iterate on all albums of this artist.


------------------------------------------------------------------------------------------------------------------
################# Command line help ##############################################################################
------------------------------------------------------------------------------------------------------------------

For more info, see https://github.com/damsgithub/myzuka-club.py


""" % (script_name, site, script_name, site)
    return help_string


def to_MB(a_bytes):
    return a_bytes / 1024. / 1024.


def check_os():
    if sys.platform.startswith('win'):
        return "win"
    else:
        return "unix"


def log_to_file(function, content):
        timestr = time.strftime("%Y%m%d-%H%M%S")
        mylogname = "myzukalog-" + function + "-" + timestr + ".log"
        logcontent = open(mylogname, "w", encoding='utf-8')
        logcontent.write(content)
        logcontent.close()


def color_message(msg, color):
    colors = {}
    colors['yellow']       = "\033[0;33m"
    colors['lightyellow']  = "\033[1;33m"
    colors['red']          = "\033[0;31m"
    colors['lightred']     = "\033[1;31m"
    colors['green']        = "\033[0;32m"
    colors['lightgreen']   = "\033[1;32m"
    colors['magenta']      = "\033[0;35m"
    colors['clear']        = "\033[0;39m"
    if (check_os() == "win"):
        # Check if color is supported in cmd.exe
        if(sys.getwindowsversion()[0] >= 10 and sys.getwindowsversion()[2] >= 10586):
            os.system('') # enables VT100 Escape Sequence for WINDOWS 10 Ver. 1607
        else:
            print(msg)
            return
    print(colors[color] + msg + colors['clear'])


def dl_status(file_name, dlded_size, real_size):
    status = r'%-50s        %05.2f of %05.2f MB [%3d%%]' % \
        (file_name, to_MB(dlded_size), to_MB(real_size), dlded_size * 100. / real_size)
    return status


def download_cover(page_content, url, debug, socks_proxy, socks_port, timeout):
    # download album's cover(s)
    cover_url_re = re.compile('<img alt=".+?" itemprop="image" src="(.+?)"/>')
    cover_url_match = cover_url_re.search(page_content)

    cover_url = cover_url_match.group(1)

    if debug: print ("cover: %s" % cover_url)

    if not cover_url:
        color_message("** No cover found for this album **", "lightyellow")
    else:
        download_file(cover_url, covers_name, debug, socks_proxy, socks_port, timeout)

def get_base_url(url, debug):
    # get website base address to preprend it to images, songs and albums relative urls'
    base_url = url.split('//', 1)
    base_url = base_url[0] + '//' + base_url[1].split('/', 1)[0]
    #if debug > 1: print("base_url: %s" % base_url)
    return base_url


def open_url(url, debug, socks_proxy, socks_port, timeout, data, range_header):
    if socks_proxy and socks_port:
        socks.set_default_proxy(socks.SOCKS5, socks_proxy, socks_port, True) # 4th parameter is to do dns resolution through the socks proxy
        socket.socket = socks.socksocket

    while True:
        if not userequests:
            # some say you have to make the import after proxy definition
            import urllib.request

            if debug: print("open_url: %s" % url)

            myheaders = {'User-Agent' : useragent, 'Referer' : site}
            req = urllib.request.Request(
                url,
                data,
                headers=myheaders
            )
            if range_header: req.add_header('Range', range_header)

            try:
                u = urllib.request.urlopen(req, timeout=timeout)
                if debug: print("HTTP reponse code: %s" % u)
            except urllib.error.HTTPError as e:
                color_message("** urllib.error.HTTPError (%s), reconnecting **" % e.reason, "lightyellow")
                time.sleep(random.randint(5,15))
                continue
            except urllib.error.URLError as e:
                if re.search('timed out', str(e.reason)):
                    # on linux "timed out" is a socket.timeout exception, 
                    # on Windows it is an URLError exception....
                    color_message("** Connection timeout (%s), reconnecting **" % e.reason, "lightyellow")
                    time.sleep(random.randint(5,15))
                    continue
                else:
                    color_message("** urllib.error.URLError, aborting **" % e.reason, "lightred")
                    u = None
            except (socket.timeout, socket.error, ConnectionError) as e:
                color_message("** Connection problem 2 (%s), reconnecting **" % str(e), "lightyellow")
                time.sleep(random.randint(5,15))
                continue
            except Exception as e:
                color_message("** Exception: aborting (%s) with error: %s **" % (url, str(e)), "lightred")
                u = None

        else:
            import cfscrape
            import requests
            scraper = cfscrape.create_scraper()
            # the "h" after socks5 is to make the dns resolution through the socks proxy
            if socks_proxy and socks_port:
                proxies = {
                    'http': 'socks5h://' + socks_proxy + ':' + str(socks_port),
                    'https': 'socks5h://' + socks_proxy + ':' + str(socks_port)
                }
            else:
                proxies = {}
			
            try:
                if range_header:
                    myheaders = {'User-Agent' : useragent, 'Referer' : site, 'Range' : range_header}
                    #u = requests.get(url, proxies=proxies, headers=myheaders, timeout=timeout, stream=True)
                    u = scraper.get(url, proxies=proxies, headers=myheaders, timeout=timeout, stream=True)
                else:
                    myheaders = {'User-Agent' : useragent, 'Referer' : site}
                    #u = requests.get(url, proxies=proxies, headers=myheaders, timeout=timeout)
                    u = scraper.get(url, proxies=proxies, headers=myheaders, timeout=timeout, stream=True)

                u.raise_for_status()
                if debug: print("HTTP reponse code: %s" % u)
            except requests.exceptions.HTTPError as e:
                color_message("** requests.exceptions.HTTPError (%s), reconnecting **" % str(e), "lightyellow")
                time.sleep(random.randint(5,15))
                continue
            except requests.exceptions.ConnectionError as e:
                color_message("**  requests.exceptions.ConnectionError (%s), reconnecting **" % str(e), "lightyellow")
                time.sleep(random.randint(5,15))
                continue
            except requests.exceptions.Timeout as e:
                color_message("** Connection timeout (%s), reconnecting **" % str(e), "lightyellow")
                time.sleep(random.randint(5,15))
                continue
            except requests.exceptions.RequestException as e:
                color_message("** Exception: aborting (%s) with error: %s **" % (url, str(e)), "lightred")
                u = None
            except (socket.timeout, socket.error, ConnectionError) as e:
                color_message("** Connection problem 2 (%s), reconnecting **" % str(e), "lightyellow")
                time.sleep(random.randint(5,15))
                continue
            except Exception as e:
                color_message("** Exception: aborting (%s) with error: %s **" % (url, str(e)), "lightred")
                u = None

        return u


def get_page_soup(url, data, debug, socks_proxy, socks_port, timeout):
    page = open_url(url, debug, socks_proxy, socks_port, timeout, data=data, range_header=None)
    if not page:
        return None
    if not userequests: page_soup = BeautifulSoup(page, "html.parser", from_encoding=page.info().get_param('charset'))
    else: page_soup = BeautifulSoup(page.content, "html.parser", from_encoding=page.encoding)
    #if debug > 1: print("page_soup: %s" % page_soup)
    page.close()
    return page_soup


def prepare_album_dir(page_content, base_path, debug):
    # get album infos from html page content
    artist = ""
    title = ""
    year = ""

    if debug > 1:
        log_to_file("prepare_album_dir", page_content)

    print("")

    # find artist name
    artist_info_re = re.compile('<td>Исполнитель:</td>\r?\n?'
                                '(?:\s)*<td>\r?\n?'
                                '(?:\r?\n?)*'
                                '(?:\s)*<a (?:.+?)>\r?\n?'
                                '(?:\s)*<meta (?:.+?)itemprop="url"(?:.*?)(?:\s)*/>\r?\n?'
                                '(?:\s)*<meta (?:.+?)itemprop="name"(?:.*?)(?:\s)*/>\r?\n?'
                                '(?:\r?\n?)*'
                                '(?:\s)*(.+?)\r?\n?'
                                '(?:\r?\n?)*'
                                '(?:\s)*</a>')
    artist_info = artist_info_re.search(page_content)

    if not artist_info:
        artist = input("Unable to get ARTIST NAME. Please enter here: ")
    else:
        artist = artist_info.group(1)
    print("Artist: %s" % artist)

    # find album name
    title_info_re = re.compile('<span itemprop="title">(?:.+?)</span>\r?\n?'
                                '(?:\r?\n?)*'
                                '(?:\s)*</a>/\r?\n?'
                                '(?:\r?\n?)*'
                                '(?:\s)*<span (?:.*?)itemtype="http://data-vocabulary.org/Breadcrumb"(?:.*?)>(.+?)</span>')
    title_info = title_info_re.search(page_content)

    if not title_info:
        title = input("Unable to get ALBUM NAME. Please enter here: ")
    else:
        title = title_info.group(1)
    print("Album: %s" % title)

    # Get the year if it is available
    year_info_re = re.compile('<time datetime="(\d+).*?" itemprop="datePublished"></time>\r?\n?')

    year_info = year_info_re.search(page_content)

    if year_info and year_info.group(1):
        year = year_info.group(1)
    else:
        year = input("Unable to get ALBUM YEAR. Please enter here (may leave blank): ")
        print("Year: %s" % year)

    # prepare album's directory
    if year:
        album_dir = artist + " - " + title + " (" + year + ")"
    else:
        album_dir = artist + " - " + title

    album_dir = os.path.normpath(base_path + os.sep + sanitize_path(album_dir))
    if debug: print("Album's dir: %s" % (album_dir))

    if not os.path.exists(album_dir):
        os.mkdir(album_dir)

    return album_dir


def sanitize_path(path):
    chars_to_remove = str.maketrans('/\\?*|":><', '         ')
    return path.translate(chars_to_remove)

def get_filename_from_cd(cd):
    """
    Get filename from content-disposition
    """
    if not cd:
        return None
    fname = re.findall('filename=(.+)', cd)
    if len(fname) == 0:
        return None
    return fname[0]


def download_file(url, file_name, debug, socks_proxy, socks_port, timeout):
    process_id = os.getpid()
    try:
        real_size = -1
        partial_dl = 0
        dlded_size = 0
    
        u = open_url(url, debug, socks_proxy, socks_port, timeout, data=None, range_header=None)
        if not u:
            return -1

        if not file_name:
            if not userequests: file_name = u.info().get_filename()
            else: file_name = get_filename_from_cd(u.headers.get('content-disposition'))
        if debug > 1: print("filename: %s" % file_name)
        file_name = file_name.replace("_myzuka", "")

        if os.path.exists(file_name):
            dlded_size = os.path.getsize(file_name)
        if (dlded_size <= 8192):
            # we may have downloaded an "Exceed the download limit" (Превышение лимита скачивания) page 
            # instead of the song, restart at beginning.
            dlded_size = 0

        i = 0
        while (i < 5):
            try:
                if not userequests: real_size = int(u.info()['content-length'])
                else: real_size = int(u.headers['Content-length'])
                if debug > 1: print("length: %s" % real_size)
                if real_size <= 1024:
                   # we got served an "Exceed the download limit" (Превышение лимита скачивания) page, 
                   # retry without incrementing counter (for musicmp3spb)
                   color_message("** File size too small (<1024), might be an error, please verify manually **", "lightyellow")
                break
            except Exception as e:
                if (i == 4):
                    color_message("** Unable to get the real size of %s from the server because: %s. **" 
                                  % (file_name, str(e)), "lightyellow")
                    break # real_size == -1
                else:
                    i += 1
                    if debug: print("%s problem while getting content-length: %s, retrying" 
                                    % (process_id, str(e)), file=sys.stderr)
                    continue

        # find where to start the file download (continue or start at beginning)
        if (0 < dlded_size < real_size):
            # file incomplete, we need to resume download
            u.close()
            
            range_header = 'bytes=%s-%s' % (dlded_size, real_size)
            data = None
            u = open_url(url, debug, socks_proxy, socks_port, timeout, data, range_header)
            if not u: return -1
    
            # test if the server supports the Range header
            range_support = ""
            if not userequests: range_support = u.getcode()
            else: range_support = u.status_code

            if (range_support == 206):
                partial_dl = 1
            else:
                color_message("** Range/partial download is not supported by server, restarting download at beginning **", "lightyellow")
                dlded_size = 0
        elif (dlded_size == real_size):
            # file already completed, skipped
            color_message("%s (skipped)" % dl_status(file_name, dlded_size, real_size), "lightgreen")
            u.close()
            return
        elif (dlded_size > real_size):
            # we got a problem, restart download
            color_message("** Downloaded size (%s) bigger than the real size (%s) of %s. Either real size could not be found or an other problem occured, retrying **" % (dlded_size,real_size,file_name), "lightyellow")
            u.close()
            return -1

        # append or truncate
        if partial_dl:
            f = open(file_name, 'ab+')
        else:
            f = open(file_name, 'wb+')

        # get the file
        block_sz = 8192

        if not userequests:
            while True:
                buffer = u.read(block_sz)
                if not buffer:
                    break
                else:
                    dlded_size += len(buffer)
                    #if debug > 1: print("Downloaded size: %s" % dlded_size)
                    f.write(buffer)
                    #if debug > 1: print("Buffer written")
        else:
            for buffer in u.iter_content(chunk_size=block_sz):
                if not buffer:
                    break
                else:
                    dlded_size += len(list(buffer))
                    #if debug > 1: print("Downloaded size: %s" % dlded_size)
                    f.write(buffer)
                    #if debug > 1: print("Buffer written")
			
        if (real_size == -1): 
            real_size = dlded_size
            color_message("%s (file downloaded, but could not verify if it is complete)" 
                   % dl_status(file_name, dlded_size, real_size), "lightyellow")
        elif (real_size == dlded_size):
            color_message("%s" # file downloaded and complete
                   % dl_status(file_name, dlded_size, real_size), "lightgreen")
        elif (dlded_size < real_size):
            color_message("%s (file download incomplete, retrying)" 
                   % dl_status(file_name, dlded_size, real_size), "lightyellow")
            u.close()
            f.close()
            return -1

        #sys.stdout.write('\n')
        u.close()
        f.close()
    except KeyboardInterrupt as e:
        if debug: print("** %s : download_file: keyboard interrupt detected **" % process_id, file=sys.stderr)
        raise e
    except Exception as e:
        color_message('** Exception caught in download_file(%s,%s) with error: "%s". We will continue anyway. **' 
               % (url, file_name, str(e)), "lightyellow")
        traceback.print_stack(file=sys.stderr)
        return -1


def download_song(params):
    (num_and_url, debug, socks_proxy, socks_port, timeout) = params
    process_id = os.getpid()

    m = re.match(r"^(\d+)-(.+)", num_and_url)
    tracknum = m.group(1)
    url = m.group(2)

    while True: # continue until we have the song
        try:
            if debug: print("%s: downloading song from %s" % (process_id, url))
            file_name = ""
            file_url = ""

            page_soup = get_page_soup(url, None, debug, socks_proxy, socks_port, timeout)
            if not page_soup: 
                if debug: print("** %s: Unable to get song's page soup, retrying **" % process_id, file=sys.stderr)
                continue

            # get the filename and file url
            for link in page_soup.find_all('a', href=True, class_="no-ajaxy", itemprop="audio", limit=1):
                #song_infos_re = re.compile('<a .+?download="(.+?)" href="(.+?)" .+?><span>'
                #                           '<i class="zmdi zmdi-cloud-download zmdi-hc-4x"></i></span></a>')

                #song_infos = song_infos_re.search(str(link))
                file_url = link.get('href')
                break

            # prepend base url if necessary
            if re.match(r'^/', file_url):
                file_url = get_base_url(url, debug) + file_url

            # download song      
            ret = download_file(file_url, file_name, debug, socks_proxy, socks_port, timeout)
            if ret == -1:
                color_message("** %s: Problem detected while downloading %s, retrying **" % (process_id, file_name), "lightyellow")
                continue
            else:
                break
        except KeyboardInterrupt:
            if debug: print("** %s: keyboard interrupt detected, finishing process **" % process_id, file=sys.stderr)
            # just return, see: 
            # http://jessenoller.com/2009/01/08/multiprocessingpool-and-keyboardinterrupt/
            return
        except Exception as e:
            color_message('** %s: Exception caught in download_song(%s,%s) with error: "%s", retrying **'
                   % (process_id, url, file_name, str(e)), "lightyellow")
            traceback.print_stack(file=sys.stderr)
            pass



def download_album(url, base_path, debug, socks_proxy, socks_port, timeout, nb_conn):
    page_soup = get_page_soup(url, None, debug, socks_proxy, socks_port, timeout)
    if not page_soup:
        color_message("** Unable to get album's page soup **", "lightred")
        return
    page_content = str(page_soup)

    # Beautifulsoup converts "&" to "&amp;" so that it be valid html. We need to convert them back with html.unescape.
    page_content = html.unescape(page_content)

    album_dir = prepare_album_dir(page_content, base_path, debug)

    os.chdir(album_dir)
 
    download_cover(page_content, url, debug, socks_proxy, socks_port, timeout)

    # create list of album's songs
    songs_links = []
    tracknum = 0
    absent_track_flag = 0

    for link in page_soup.find_all('a', href=re.compile("^/Song/"), title=re.compile("^Скачать")):
        # search track number

        tracknum_infos_re = re.compile('<div class="position">\r?\n?'
                                       '(?:\r?\n?)*'
                                       '(?:\s)*(\d+)\r?\n?'
                                       '(?:\r?\n?)*'
                                       '(?:\s)*</div>\r?\n?'
                                       '(?:\s)*<div class="options">\r?\n?'
                                       '(?:\s)*<div class="top">\r?\n?'
                                       '(?:\s)*<span (?:.+?)title="Сохранить в плейлист"(?:.*?)></span>\r?\n?'
                                       '(?:\s)*<span (?:.+?)title="Добавить в плеер"(?:.*?)>(?:.*?)</span>\r?\n?'
                                       '(?:\s)*<a href="' + link['href'], re.I)

        tracknum_infos = tracknum_infos_re.search(page_content)
        if tracknum_infos:
            tracknum = tracknum_infos.group(1)
            tracknum = str(tracknum).zfill(2)
        else:
            color_message("** Unable to get track number for %s **" % link['href'], "lightyellow")
            tracknum = 0

        # prepend base url if necessary
        if re.match(r'^/', link['href']):
            link['href'] = get_base_url(url, debug) + link['href']

        # add song url and number in array
        songs_links.append(str(tracknum) + '-' + link['href'])

    if debug > 1:
        log_to_file("download_album", page_content)

    # search for absent/deleted tracks from the website.
    deleted_track_re = re.compile(r'<div class="position">\r?\n?'
                                  '(?:\r?\n?)?'
                                  '(?:\s)*(\d+)\r?\n?'
                                  '(?:\r\n?)?'
                                  '(?:\s)*</div>\r?\n?'
                                  '(?:\s)*<div class="options">\r?\n?'
                                  '(?:\s)*<div class="top">\r?\n?'
                                  '(?:\s)*<span class=".*?glyphicon-ban-circle.*?"></span>\r?\n?'
                                  '(?:\s)*</div>\r?\n?'
                                  '(?:\s)*<div class="data">(?:.+?)</div>\r?\n?'
                                  '(?:\s)*</div>\r?\n?'
                                  '(?:\s)*<div class="details">\r?\n?'
                                  '(?:\s)*<div class="time">(?:.+?)</div>\r?\n?'
                                  '(?:\s)*<a (?:.+?)\r?\n?'
                                  '(?:\s)*<meta (?:.+?)\r?\n?'
                                  '(?:\s)*<meta (?:.+?)\r?\n?'
                                  '(?:\s)*</span>\r?\n?'
                                  '(?:\s)*<p>\r?\n?'
                                  '(?:\s)*<span>(.+?)</span> <span class=(?:.+?)>\[Удален по требованию правообладателя\]</span>')

    for deleted_track in re.findall(deleted_track_re, page_content):
        tracknum = deleted_track[0]
        trackname = deleted_track[1]
        color_message("** The track number %s (%s) is absent from website **" % (tracknum, trackname), "lightyellow")
        absent_track_flag = 1

    if not songs_links:
        color_message("** Unable to detect any song links, skipping this album/url **", "lightred")
        absent_track_flag = 1
    else:
        # we launch the threads to do the downloads
        pool = Pool(processes=nb_conn)

        # pool.map accepts only one argument for the function call, so me must aggregate all in one
        params = [(num_and_url, debug, socks_proxy, socks_port, timeout) for num_and_url in songs_links]
        try:
            pool.map(download_song, params)
            pool.close()
            pool.join()
        except KeyboardInterrupt as e:
            color_message("** Program interrupted by user, exiting! **", "lightred")
            pool.terminate()
            pool.join()
            sys.exit(1)

    os.chdir('..')
    if not absent_track_flag: color_message("** ALBUM DOWNLOAD FINISHED **", "lightgreen")
    else: color_message("** ALBUM DOWNLOAD INCOMPLETE, TRACK(S) MISSING ON WEBSITE **", "lightred")

def download_artist(url, base_path, debug, socks_proxy, socks_port, timeout, nb_conn):
    page_soup = get_page_soup(url, str.encode(''), debug, socks_proxy, socks_port, timeout)
    if not page_soup:
        if debug: print("** Unable to get artist's page soup **", file=sys.stderr)
        return 

    color_message("** Warning: we are going to download all albums from this artist! **", "lightyellow")

    albums_links = []
    for link in page_soup.find_all('a', href=True):
        if re.search(r'/Album/.*', link['href']):
            # albums' links may appear multiple times, we need to de-duplicate.
            if link['href'] not in albums_links:
                albums_links.append(link['href'])

    for album_link in albums_links:
            download_album(get_base_url(url, debug) + album_link, base_path, 
                           debug, socks_proxy, socks_port, timeout, nb_conn)
    print("")
    print("ARTIST DOWNLOAD FINISHED")


def main():
    global version
    debug = 0
    socks_proxy = ""
    socks_port = ""
    timeout = 10
    nb_conn = 3
    script_name = os.path.basename(sys.argv[0])

    parser = argparse.ArgumentParser(description=script_help(version, script_name), add_help=True, 
                                     formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument(
        "-d", "--debug", type=int, choices=range(0,3), default=0, help="Debug verbosity: 0, 1, 2" )
    parser.add_argument(
        "-s", "--socks", type=str, default=None, help='Socks proxy: "address:port" without "http://"')
    parser.add_argument(
        "-t", "--timeout", type=int, default=10, help='Timeout for HTTP connections in seconds')
    parser.add_argument(
        "-n", "--nb_conn", type=int, default=3, help='Number of simultaneous downloads (max 3 for tempfile.ru)')
    parser.add_argument(
        "-p", "--path", type=str, default=".", help="Base directory in which album(s) will be"
                                                    " downloaded. Defaults to current directory.")
    parser.add_argument(
        "-v", "--version", action='version', version='%(prog)s, version: '+str(version))

    parser.add_argument("url", action='store', help="URL of album or artist page")
    args = parser.parse_args()

    debug = int(args.debug)
    if debug: print("Debug level: %s" % debug)

    nb_conn = int(args.nb_conn)
    timeout = int(args.timeout)

    if (args.socks):
        (socks_proxy, socks_port) = args.socks.split(':')
        if debug: print("proxy socks: %s %s" % (socks_proxy, socks_port))
        if not socks_port.isdigit():
            color_message("** Error in your socks proxy definition, exiting. **", "lightred")
            sys.exit(1)
        socks_port = int(socks_port)

    try:
        print("** We will try to use %s simultaneous downloads, progress will be shown" % nb_conn)
        print("   after each completed file but not necessarily in album's order. **")

        # modification of global variables do not work correctly under windows with multiprocessing,
        # so I have to pass all these parameters to these functions...
        if re.search(r'/Artist/.*', args.url, re.IGNORECASE):
            download_artist(args.url, args.path, debug, socks_proxy, socks_port, timeout, nb_conn)
        elif re.search(r'/Album/.*', args.url, re.IGNORECASE):
            download_album(args.url, args.path, debug, socks_proxy, socks_port, timeout, nb_conn)
        else:
            color_message("** Error: unable to recognize url, it should contain '/Artist/' or '/Album/'! **", "lightred")

    except Exception as e:
        color_message("** Error: Cannot download URL: %s, reason: %s **" % (args.url, str(e)), "lightred")
        traceback.print_stack(file=sys.stderr)

if __name__ == "__main__":
    main()

