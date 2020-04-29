# myzuka-club.py
Python 3 port of https://github.com/xor512/musicmp3spb.org (http://musicmp3spb.org/ music downloader) with some differences.

Features included:
* Cover downloading
* Windows/Linux support
* Resume incomplete songs and albums downloads
* Creation of directory with "Artist - Album (year)" name.
* Multiple simultaneous downloads to download faster
* Able to download all albums from an artist
* Socks proxy support
* Colored output

TODO:
* make some kind of progress bar (difficult because of the simultaneous downloads).
* streaming mode?

Install:
* install python 3 (tested with 3.6.2) if not already present on your distrib. For Windows, see here https://www.python.org/downloads/windows/
* install required modules: BeautifulSoup4 and Pysocks. Use your standard repo for linux, for Windows do in an administrator command prompt

```sh
python -m pip install BeautifulSoup4 Pysocks requests cfscrape
```

Usage:
* Just give it an album or artist url from http://myzuka.club/ as argument, see below:

```
Python script to download albums from http://myzuka.club, version 5.6.

------------------------------------------------------------------------------------------------------------------
################## To download an album, give it an url with '/Album/' in it #####################################
------------------------------------------------------------------------------------------------------------------
user@computer:/tmp$ myzuka-club.py [-p /path] http://myzuka.club/Album/630746/The-6-Cello-Suites-Cd1-1994
** We will try to use 3 simultaneous downloads, progress will be shown **
** after each completed file but not necessarily in album's order. **

Artist: Johann Sebastian Bach
Album: The 6 Cello Suites (CD1)
Year: 1994
cover.jpg                                                 00.01 of 00.01 MB [100%]
05_johann_sebastian_bach_maurice_gendron_bwv1007_menuets_myzuka.mp3        07.04 of 07.04 MB [100%]
01_johann_sebastian_bach_maurice_gendron_bwv1007_prelude_myzuka.mp3        05.57 of 05.57 MB [100%]
03_johann_sebastian_bach_maurice_gendron_bwv1007_courante_myzuka.mp3        05.92 of 05.92 MB [100%]
06_johann_sebastian_bach_maurice_gendron_bwv1007_gigue_myzuka.mp3        04.68 of 04.68 MB [100%]
04_johann_sebastian_bach_maurice_gendron_bwv1007_sarabande_myzuka.mp3        07.06 of 07.06 MB [100%]
[...]

It will create an "Artist - Album" directory in the path given as argument (or else in current
 directory if not given), and download all songs and covers available on that page.

------------------------------------------------------------------------------------------------------------------
################## To download all albums from an artist, give it an url with '/Artist/' in it ###################
------------------------------------------------------------------------------------------------------------------

user@computer:/tmp$ myzuka-club.py [-p /path] http://myzuka.club/Artist/7110/Johann-Sebastian-Bach/Albums
** We will try to use 3 simultaneous downloads, progress will be shown **
** after each completed file but not necessarily in album's order. **
** Warning: we are going to download all albums from this artist! **

Artist: Johann Sebastian Bach
Album: The 6 Cello Suites (CD1)
Year: 1994
cover.jpg                                                 00.01 of 00.01 MB [100%]
05_johann_sebastian_bach_maurice_gendron_bwv1007_menuets_myzuka.mp3        07.04 of 07.04 MB [100%]
01_johann_sebastian_bach_maurice_gendron_bwv1007_prelude_myzuka.mp3        05.57 of 05.57 MB [100%]
03_johann_sebastian_bach_maurice_gendron_bwv1007_courante_myzuka.mp3        05.92 of 05.92 MB [100%]
[...]

Artist: Johann Sebastian Bach
Album: Prelude and Fugue in E Minor, BWV 548
Year: 1964
cover.jpg                                                 00.01 of 00.01 MB [100%]
01_johann_sebastian_bach_praeludium_myzuka.mp3            09.51 of 09.51 MB [100%]
02_johann_sebastian_bach_fuga_myzuka.mp3                  10.80 of 10.80 MB [100%]
** ALBUM DOWNLOAD FINISHED **

[...]

It will iterate on all albums of this artist.

------------------------------------------------------------------------------------------------------------------
################# Command line help ##############################################################################
------------------------------------------------------------------------------------------------------------------

For more info, see https://github.com/damsgithub/myzuka-club.py

positional arguments:
  url                   URL of album or artist page

optional arguments:
  -h, --help            show this help message and exit
  -d {0,1,2}, --debug {0,1,2}
                        Debug verbosity: 0, 1, 2
  -s SOCKS, --socks SOCKS
                        Socks proxy: "address:port" without "http://"
  -t TIMEOUT, --timeout TIMEOUT
                        Timeout for HTTP connections in seconds
  -n NB_CONN, --nb_conn NB_CONN
                        Number of simultaneous downloads (max 3 for tempfile.ru)
  -p PATH, --path PATH  Base directory in which album(s) will be downloaded. Defaults to current directory.
  -v, --version         show program's version number and exit
  
```
